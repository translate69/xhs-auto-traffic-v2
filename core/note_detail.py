"""
NoteDetailCollector - 笔记详情采集

职责：
  · 打开笔记详情页
  · 提取: 正文, 图片列表, 标签, 点赞/收藏/评论数, 时间
  · 降级策略: enrichment 失败 → 保留搜索页已有数据，不丢弃
  · 重试: 最多 3 次
"""
from __future__ import annotations

import sys
import time
import json
import random
from dataclasses import dataclass, field
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# ─── SIGKILL 定位日志 ───────────────────────────────────
try:
    import os as _os
    _debug_log_path = _os.path.join(_os.path.dirname(__file__), "..", "_pipeline_debug.log")
    _debug_log_enabled = True

    def _log_stage(stage: str, flush: bool = True):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        line = f"[{ts}] [NoteDetail] {stage}\n"
        print(line, end="", flush=True)
        if _debug_log_enabled:
            try:
                with open(_debug_log_path, "a", encoding="utf-8", buffering=1) as _f:
                    _f.write(line)
                    if flush:
                        _f.flush()
                        _os.fsync(_f.fileno())
            except Exception:
                pass
except ImportError:
    def _log_stage(stage: str, flush: bool = True):
        pass

import config
from core.search_collector import FeedNote


# ─── 登录失效异常 ───────────────────────────────


class RateLimitError(Exception):
    """enrichment 检测到 300013 访问频繁时抛出，触发 URL 格式切换"""
    pass


class LoginRequiredError(Exception):
    """enrichment 检测到登录弹窗或 cookie 失效时抛出"""
    pass


# ─── NoteDetail ───────────────────────────────────────────


@dataclass
class NoteDetail:
    """单条笔记详情（enrichment 结果）"""
    # 来自搜索页
    url: str = ""
    xsec_token: str = ""
    author: str = ""
    time_text: str = ""
    title: str = ""          # 标题（来自详情页或搜索页）

    # 来自详情页（enrichment）
    content: str = ""
    images: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    likes: int = 0
    collects: int = 0
    comments: int = 0
    published_at: str = ""       # YYYY-MM-DD 格式
    author_id: str = ""

    # 内部
    _filter_result: 'filter_service.FilterResult | None' = field(default_factory=lambda: None)  # 筛选结果
    filter_passed: bool | None = None       # 筛选是否通过（filter_all 后填充）
    filter_reasons: str = ""                # 筛选通过/拒绝原因
    filter_type: str = ""                   # 笔记分类类型
    is_hashtag_fallback: bool = False       # 正文是否因 hashtag 降级而使用了搜索页标题

    def has_content(self) -> bool:
        """是否有正文（判断降级是否生效）"""
        return bool(self.content)

    @property
    def filter_result(self) -> "filter_service.FilterResult | None":
        """外部访问筛选结果的属性（映射到内部 _filter_result）"""
        return self._filter_result

    @filter_result.setter
    def filter_result(self, value: "filter_service.FilterResult | None"):
        """允许外部赋值（FilterService.filter_all 用）"""
        self._filter_result = value

    def merge_from_feed(self, feed: FeedNote):
        """用搜索页已有数据填充（降级时使用）"""
        self.url = feed.url or self.url
        self.xsec_token = feed.xsec_token or self.xsec_token
        self.author = feed.author or self.author
        self.time_text = feed.time_text or self.time_text
        self.title = feed.title or self.title
        self.note_id = feed.note_id or self.note_id

    # note_id 专用 backing（避免与 @property 冲突）
    _note_id: str = ""

    @property
    def note_id(self) -> str:
        """从 url 提取 note_id（优先用实例 _note_id，其次从 url 解析）"""
        import re
        # 优先返回显式设置的值（来自 feed.note_id）
        if self._note_id:
            return self._note_id
        m = re.search(r"search_result/([a-fA-F0-9]+)", self.url, re.IGNORECASE)
        if m:
            return m.group(1)
        m2 = re.search(r"/explore/([a-fA-F0-9]+)", self.url, re.IGNORECASE)
        if m2:
            return m2.group(1)
        return ""

    @note_id.setter
    def note_id(self, value: str):
        """允许外部赋值 instance attribute"""
        self._note_id = value


# ─── NoteDetailCollector ─────────────────────────────────


class NoteDetailCollector:
    """
    笔记详情采集器。

    流程：
      1. 逐条打开笔记（带重试）
      2. 提取详情（正文/图片/标签/互动数/时间）
      3. 失败 → 降级保留搜索页数据
    """

    # 每 N 条重启 context，释放主进程堆内存，防止 Windows 内存压缩发 SIGKILL
    RESTART_EVERY = 10

    def __init__(self, browser, context, cookie_file: Path | None = None):
        self.browser = browser
        self.context = context
        # Cookie 文件路径（传入而非硬编码，保持与 BrowserManager 一致）
        self._cookie_file = cookie_file or (Path(__file__).parent.parent / "xhs_cookies.json")
        # 全局 URL 格式状态：初始 search_result（explore 格式稳定触发 300011，优先用 search_result）
        # 触发 300013 后降级为 explore
        self._url_format = "search_result"
        # Batch 级别 300013 统计（用于检测 token 过期）
        self._batch_300013_count = 0
        self._batch_total = 0
        _log_stage("创建 NoteDetailCollector")


    def _restart_context(self):
        """关闭旧 context 并重建（cookie 重新写入）"""
        old = self.context
        self.context = self.browser.new_context()
        old.close()
        with open(self._cookie_file, encoding="utf-8") as f:
            cookies = json.load(f)
        self.context.add_cookies(cookies)
        _log_stage(f"  [Context 重启完成]")

    def enrich_all(self, feeds: list[FeedNote]) -> list[NoteDetail]:
        """
        对 feeds 列表逐条做 enrichment。
        每条笔记单独开一个 page，用完立即 close，避免 DOM 数据积累导致 OOM。
        返回 NoteDetail 列表（失败条目降级保留搜索页数据）。
        """
        results = []
        from utils.storage import RecentStorage
        recent_storage = RecentStorage()
        self._batch_total = 0
        self._batch_300013_count = 0
        _log_stage(f"enrich_all 开始，共 {len(feeds)} 条")

        for i, feed in enumerate(feeds):
            # ── 每 RESTART_EVERY 条重启 context，释放堆内存 ──
            if i > 0 and i % self.RESTART_EVERY == 0:
                print(f"[Detail] 已处理 {i} 条，重启 context 释放内存...")
                self._restart_context()

            # ── 每条笔记独立 page，用完即关 ──
            page = None
            try:
                page = self.context.new_page()
            except Exception as e:
                if "Target page, context or browser has been closed" in str(e) or "Protocol error" in str(e):
                    _log_stage(f"  [WARN] Browser 已关闭，尝试重建 context...", flush=True)
                    self._restart_context()
                    try:
                        page = self.context.new_page()
                    except Exception:
                        _log_stage(f"  [ERROR] 重建 context 失败，跳过笔记", flush=True)
                        self._batch_total += 1
                        results.append(NoteDetail())
                        results[-1].merge_from_feed(feed)
                        continue
                else:
                    raise

            try:
                _log_stage(f"处理笔记 {i+1}/{len(feeds)}: {feed.note_id}", flush=False)
                print(f"[Detail] [{i+1}/{len(feeds)}] {feed.url}")

                detail = self._enrich_single(feed, page)

                # ── enrichment 成功，写入 recent storage ──
                if feed.note_id:
                    recent_storage.mark_seen(feed.note_id)

                self._batch_total += 1

                # ── 暂停节奏 ──
                pause = random.uniform(*config.PAUSE_BETWEEN_NOTES)
                time.sleep(pause)

                # 每 5 条暂停（风控保护）
                if (i + 1) % 5 == 0:
                    print(f"[Detail] 已采集 {i+1} 条，暂停 {config.PAUSE_DURATION}s")
                    time.sleep(config.PAUSE_DURATION)

            except Exception as e:
                _log_stage(f"  例外: {e}", flush=True)
                self._batch_total += 1
                detail = NoteDetail()
                detail.merge_from_feed(feed)

            finally:
                if page:
                    try:
                        page.close()
                    except Exception:
                        pass  # 页面已关闭，忽略
                _log_stage(f"  Page 已关闭")

            results.append(detail)

        _log_stage(f"enrich_all 完成，返回 {len(results)} 条")

        # ── Token 过期 / 会话级风控警告 ──
        if self._batch_total > 0 and self._batch_300013_count == self._batch_total:
            print(f"\n🚨 [CRITICAL] Batch 内全部 {self._batch_total} 条笔记均触发 300013！")
            print(f"   原因可能是 xsec_token 已过期或会话级风控，建议重新采集搜索页以刷新 token。")
            print(f"   当前 cookie 文件: {self._cookie_file}")

        return results

    def _switch_url_format_on_300013(self, switch_count: int) -> str:
        """
        内部封装：遇到 300013 后切换 URL 格式。
        switch_count=0 → search_result 触发 300013 → 切换到 explore
        switch_count=1 → explore 也触发 300013 → 切换回 search_result
        switch_count=2 → 两种格式都失败了，放弃切格式
        """
        if switch_count == 0:
            self._url_format = "explore"
            print(f"[Detail] 300013 detected，全局切换 → explore 格式")
        elif switch_count == 1:
            self._url_format = "search_result"
            print(f"[Detail] 300013 on explore，切回 search_result 重试")
        # switch_count >= 2 不再切换，用当前格式硬撑

    def _enrich_single(self, feed: FeedNote, page, max_retries: int = 3) -> NoteDetail:
        """单条笔记 enrichment，支持重试 + URL 格式自动切换"""

        last_error = ""
        format_switch_count = 0  # 记录本次笔记内切换了几次 URL 格式

        for attempt in range(1, max_retries + 1):
            try:
                if not page:
                    raise RuntimeError("Page 未初始化")

                # ── 根据当前格式构建 URL ────────────────────────────
                if self._url_format == "search_result":
                    detail_url = self._build_detail_url_search_result(feed)
                else:
                    detail_url = self._build_detail_url_fallback(feed)

                _log_stage(f"  [{self._url_format}] goto: {detail_url[:80]}", flush=False)
                page.goto(detail_url, wait_until="networkidle")
                _log_stage(f"  page.goto 完成", flush=False)

                # ── 登录态检测（与 SearchCollector 一致）─────────────────────
                try:
                    page.wait_for_selector(
                        "[class*='login'], [class*='login-modal'], .login-container",
                        timeout=3000
                    )
                    raise LoginRequiredError(
                        "详情页检测到登录弹窗，cookie 可能已失效，需重新扫码"
                    )
                except Exception:
                    pass  # 正常，无弹窗

                # ── 300013 检测（优先于通用登录检测）─────────────────
                final_url = page.url
                if "error_code=300013" in final_url:
                    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_detail_300013.png")
                    raise RateLimitError(
                        f"详情页触发 300013 访问频繁（{final_url[:80]}），需切换 URL 格式重试"
                    )

                # 检测是否跳转登录/安全限制页
                if any(kw in final_url.lower() for kw in ["login", "/w/user/login", "/w/login", "website-login/error"]):
                    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_detail_login.png")
                    raise LoginRequiredError(
                        f"详情页 URL 异常（{final_url[:60]}），cookie 可能已失效"
                    )

                # 网络空闲后正文元素应该已经渲染，额外等一小段时间确保渲染完成
                time.sleep(1)
                page.wait_for_selector("#detail-desc", timeout=20000)
                _log_stage(f"  wait_for_selector 完成", flush=False)

                # ── 检测帖子是否不可见（删/私/限）──────────────────────
                # 在提取正文前先检查页面是否有"不可见"提示
                is_unavailable = page.evaluate(
                    """() => {
                    var body = document.body.textContent || '';
                    // 小红书不可见帖子的常见提示文本
                    var unavailable_phrases = [
                        '内容不可见', '该内容不可见', '此内容不可见',
                        '笔记已删除', '该笔记已删除', '此笔记已删除',
                        '已被删除', '已删除',
                        '私密笔记', '该笔记为私密笔记',
                        '该笔记仅对', '内容仅对',
                        '账号异常', '该账号异常',
                    ];
                    for (var i = 0; i < unavailable_phrases.length; i++) {
                        if (body.includes(unavailable_phrases[i])) {
                            return true;
                        }
                    }
                    return false;
                    }"""
                )
                if is_unavailable:
                    print(f"[Detail] WARN: 帖子不可访问（删/私/限），标记为[内容无法获取]")
                    detail = NoteDetail()
                    detail.merge_from_feed(feed)
                    detail.content = "[内容无法获取]"
                    return detail

                _log_stage(f"  开始提取详情", flush=False)
                detail = self._extract_detail(page)
                detail.merge_from_feed(feed)
                _log_stage(f"  提取完成 content_len={len(detail.content)}", flush=True)

                # hashtag 内容笔记正常保留，让 filter 自然判断
                print(f"[Detail] OK: {detail.content[:30] if detail.content else '(无正文)'}...")
                return detail

            except Exception as e:
                last_error = str(e)
                print(f"[Detail] FAIL {attempt}/3: {last_error}")

                # ── 300013：切换 URL 格式后重试（每张笔记最多切换 2 次）──────
                if "300013" in last_error or "error_code=300013" in last_error:
                    self._batch_300013_count += 1
                    if format_switch_count < 2:
                        self._switch_url_format_on_300013(format_switch_count)
                        format_switch_count += 1
                        continue  # 用新格式重试
                    else:
                        print(f"[Detail] 两种格式均触发 300013，放弃重试")
                        break  # 跳出 retry 循环，降级保留搜索页数据

                if attempt < max_retries:
                    time.sleep(config.ENRICHMENT_RETRY_DELAY)

        # 所有重试耗尽 → 降级保留搜索页数据
        print(f"[Detail] WARN: enrichment 全部失败，降级: {last_error}")
        detail = NoteDetail()
        detail.merge_from_feed(feed)
        return detail

    def _build_detail_url(self, feed: FeedNote) -> str:
        """从搜索结果 URL 构建详情页 URL
        优先用 search_result URL 保持 xsec_token 上下文，减少风控触发。"""
        import re

        # 处理相对 URL（以 / 开头）
        if feed.url.startswith("/"):
            base = "https://www.xiaohongshu.com"
            full_url = base + feed.url
        else:
            full_url = feed.url

        # 如果 URL 已经有 xsec_token，直接返回
        if "/explore/" in full_url or "/search_result/" in full_url:
            if "xsec_token=" in full_url:
                return full_url
            if feed.xsec_token:
                sep = "&" if "?" in full_url else "?"
                return f"{full_url}{sep}xsec_token={feed.xsec_token}"
            return full_url

        # 从 search_result URL 提取 note_id，保持 search_result 格式
        m = re.search(r"search_result/([a-fA-F0-9]+)", full_url, re.IGNORECASE)
        if m:
            note_id = m.group(1)
            if feed.xsec_token:
                # 保持 search_result URL + xsec_token，保持搜索上下文
                return (f"https://www.xiaohongshu.com/search_result/{note_id}"
                        f"?xsec_token={feed.xsec_token}&xsec_source=pc_search")
            return f"https://www.xiaohongshu.com/search_result/{note_id}"

        return full_url  # 兜底

    def _build_detail_url_fallback(self, feed: FeedNote) -> str:
        """降级 URL：当 search_result 触发 300013 时，切为 explore 格式访问"""
        import re
        # 优先从 feed.url 提取 note_id
        m = re.search(r"search_result/([a-fA-F0-9]+)", feed.url, re.IGNORECASE)
        if not m:
            m = re.search(r"/explore/([a-fA-F0-9]+)", feed.url, re.IGNORECASE)
        if not m and feed.url:
            m = re.search(r"([a-fA-F0-9]){16}", feed.url)

        if m:
            note_id = m.group(1)
            if feed.xsec_token:
                return (f"https://www.xiaohongshu.com/explore/{note_id}"
                        f"?xsec_token={feed.xsec_token}&xsec_source=pc_search")
            return f"https://www.xiaohongshu.com/explore/{note_id}"

        # 兜底：直接返回原 URL（去掉 search_result 格式）
        return feed.url.replace("/search_result/", "/explore/") if "/search_result/" in feed.url else feed.url

    def _build_detail_url_search_result(self, feed: FeedNote) -> str:
        """降级 URL：当 explore 触发 300013 时，切为 search_result 格式"""
        import re
        m = re.search(r"search_result/([a-fA-F0-9]+)", feed.url, re.IGNORECASE)
        if not m:
            m = re.search(r"/explore/([a-fA-F0-9]+)", feed.url, re.IGNORECASE)
        if not m and feed.url:
            m = re.search(r"([a-fA-F0-9]){16}", feed.url)

        if m:
            note_id = m.group(1)
            if feed.xsec_token:
                return (f"https://www.xiaohongshu.com/search_result/{note_id}"
                        f"?xsec_token={feed.xsec_token}&xsec_source=pc_search")
            return f"https://www.xiaohongshu.com/search_result/{note_id}"

        return feed.url.replace("/explore/", "/search_result/") if "/explore/" in feed.url else feed.url

    def _is_hashtag_only(self, content: str) -> bool:
        """
        判断正文是否仅为 hashtag（无实质内容）。
        典型场景：笔记无法访问时，DOM 可能只渲染出 hashtag 形式的标题。
        """
        if not content:
            return False
        import re
        # 去掉 #xxx 形式 tag 后，看还剩多少实质文字
        stripped = re.sub(r'#[^\s#]+', '', content).strip()
        # 如果剩余字符 < 5，认为是纯 hashtag 正文
        return len(stripped) < 5

    def _extract_detail(self, page) -> NoteDetail:
        """从 page DOM 提取详情（带 fallback）"""
        try:
            data = self._extract_detail_raw(page)
        except Exception as e:
            print(f"[Detail] DOM 提取异常，降级: {e}")
            return NoteDetail()

        if not data.get("content"):
            print(f"[Detail] WARN: 正文 DOM 为空")

        # 解析时间
        time_text = data.get("time_text", "")
        time_clean = time_text.split(" ")[0] if time_text else ""

        from utils.parse import parse_published_at
        pub_dt = parse_published_at(time_clean)
        published_at = pub_dt.strftime("%Y-%m-%d") if pub_dt else ""

        # 清洗正文：从 content 中移除 #标签 文本（因为标签已有独立 tags 字段）
        raw_content = data.get("content", "")
        import re
        content = re.sub(r'#[^\s#]+', '', raw_content).strip()

        return NoteDetail(
            content=content,
            tags=data.get("tags", []),
            images=data.get("images", []),
            likes=data.get("likes", 0),
            collects=data.get("collects", 0),
            comments=data.get("comments", 0),
            time_text=time_text,
            published_at=published_at,
            author=data.get("author", ""),
            author_id=data.get("author_id", ""),
        )

    def _extract_detail_raw(self, page) -> dict:
        """实际执行 DOM 提取（所有选择器均加异常保护）"""
        return page.evaluate(
            """
(function() {
    var r = {};

    // ── 正文 ────────────────────────────────────────────
    var desc = document.querySelector('#detail-desc');
    r.content = desc ? (desc.textContent || '').trim() : '';

    // ── 标签 ───────────────────────────────────────────
    r.tags = [];
    if (desc) {
        var tagEls = desc.querySelectorAll('a.tag');
        for (var i = 0; i < tagEls.length; i++) {
            var txt = (tagEls[i].textContent || '').trim();
            if (txt) r.tags.push(txt);
        }
    }

    // ── 作者（多选择器兜底）────────────────────────────
    var nameEl = (
        document.querySelector('.author .info .name') ||
        document.querySelector('.author-wrapper .name') ||
        document.querySelector('[class*="author"] [class*="name"]') ||
        document.querySelector('.name')
    );
    r.author = nameEl ? (nameEl.textContent || '').trim() : '';

    // ── 作者 ID ────────────────────────────────────────
    r.author_id = '';
    var authorLink = (
        document.querySelector('.author a') ||
        document.querySelector('.author-wrapper a') ||
        document.querySelector('[class*="author"] a')
    );
    if (authorLink) {
        var href = authorLink.getAttribute('href') || '';
        var m = href.match(/profile\\/([^?]+)/);
        if (m) r.author_id = m[1];
    }

    // ── 点赞/收藏/评论（多选择器兜底）────────────────
    var countEls = (
        document.querySelectorAll('[class*="count"]') ||
        document.querySelectorAll('[class*="Count"]')
    );
    var counts = [];
    for (var i = 0; i < countEls.length; i++) {
        var txt = (countEls[i].textContent || '').trim();
        var num = parseInt(txt);
        if (txt && !isNaN(num)) counts.push(num);
    }
    r.likes = counts[0] || 0;
    r.collects = counts[1] || 0;
    r.comments = counts[2] || 0;

    // ── 时间（详情页）─────────────────────────────────────
    // 在正文附近找时间元素，兼容各种 class 命名
    var dateEl = (
        document.querySelector('.date') ||
        document.querySelector('[class*="date"]') ||
        document.querySelector('[class*="time"]') ||
        document.querySelector('.posted') ||
        document.querySelector('[class*="publish"]') ||
        (desc ? desc.parentElement.querySelector('[class*="time"]') : null)
    );
    r.time_text = dateEl ? (dateEl.textContent || '').trim() : '';

    // ── 正文图片（封面图，不是正文字节内的 emoji）─────────
    // 策略：在 #detail-desc 外部找第一张真实图片（排除 emoji 规格 <100px）
    r.images = [];
    var allImgs = document.querySelectorAll('img');
    for (var i = 0; i < allImgs.length; i++) {
        var img = allImgs[i];
        var src = img.getAttribute('src') || img.getAttribute('data-src') || '';
        if (!src || !src.startsWith('http')) continue;
        if (src.includes('avatar') || src.includes('emotion') || src.includes('emoji')) continue;
        // 排除 desc 内部的小图（emoji）
        if (desc && desc.contains(img)) {
            var rect = img.getBoundingClientRect();
            if (rect.width < 100 || rect.height < 100) continue;
        }
        r.images.push(src);
        break;  // 只取第一张（封面图）
    }

    return r;
})()
        """)