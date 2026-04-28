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
import random
from dataclasses import dataclass, field

sys.stdout.reconfigure(encoding="utf-8")

import config
from core.search_collector import FeedNote


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

    @property
    def note_id(self) -> str:
        """从 url 提取 note_id"""
        import re
        m = re.search(r"search_result/([a-fA-F0-9]+)", self.url, re.IGNORECASE)
        if m:
            return m.group(1)
        m2 = re.search(r"/explore/([a-fA-F0-9]+)", self.url, re.IGNORECASE)
        if m2:
            return m2.group(1)
        return ""


# ─── NoteDetailCollector ─────────────────────────────────


class NoteDetailCollector:
    """
    笔记详情采集器。

    流程：
      1. 逐条打开笔记（带重试）
      2. 提取详情（正文/图片/标签/互动数/时间）
      3. 失败 → 降级保留搜索页数据
    """

    def __init__(self, browser, context):
        self.browser = browser
        self.context = context
        self.page = context.new_page()

    def enrich_all(self, feeds: list[FeedNote]) -> list[NoteDetail]:
        """
        对 feeds 列表逐条做 enrichment。
        返回 NoteDetail 列表（失败条目降级保留搜索页数据）。
        """
        results = []

        for i, feed in enumerate(feeds):
            print(f"[Detail] [{i+1}/{len(feeds)}] {feed.url[:60]}...")

            detail = self._enrich_single(feed)
            results.append(detail)

            # 采集节奏
            pause = random.uniform(*config.PAUSE_BETWEEN_NOTES)
            time.sleep(pause)

            # 每 5 条暂停（风控保护）
            if (i + 1) % 5 == 0:
                print(f"[Detail] 已采集 {i+1} 条，暂停 {config.PAUSE_DURATION}s")
                time.sleep(config.PAUSE_DURATION)

        return results

    def _enrich_single(self, feed: FeedNote, max_retries: int = 3) -> NoteDetail:
        """单条笔记 enrichment，支持重试"""

        detail_url = self._build_detail_url(feed)
        if not detail_url:
            print(f"[Detail] WARN: URL 为空，降级保留搜索页数据")
            detail = NoteDetail()
            detail.merge_from_feed(feed)
            return detail

        last_error = ""

        for attempt in range(1, max_retries + 1):
            try:
                if not self.page:
                    raise RuntimeError("Page 未初始化")

                self.page.goto(detail_url, wait_until="domcontentloaded")
                self.page.wait_for_selector("#detail-desc", timeout=15000)
                time.sleep(2)  # 等待异步数据加载

                detail = self._extract_detail()
                detail.merge_from_feed(feed)

                if not detail.has_content():
                    # 正文为空，降级：保留搜索页 title 作为 content 兜底
                    print(f"[Detail] WARN: 正文为空，用搜索页标题降级")
                    if detail.title:
                        detail.content = f"[标题] {detail.title}"
                    else:
                        detail.content = ""

                # 检测正文是否仅为 hashtag（笔记无法访问的降级态）
                if self._is_hashtag_only(detail.content):
                    print(f"[Detail] WARN: 正文仅为 hashtag（笔记可能无法访问），用搜索页标题降级")
                    # 搜索标题也可能是 hashtag，进一步降级为标记
                    if self._is_hashtag_only(feed.title):
                        # 搜索标题也是 hashtag → 正文记为无法访问标记，交由过滤器判断
                        detail.content = "[内容无法获取]"
                    else:
                        detail.content = feed.title

                print(f"[Detail] OK: {detail.content[:30] if detail.content else '(无正文)'}...")
                return detail

            except Exception as e:
                last_error = str(e)
                print(f"[Detail] FAIL {attempt}/3: {last_error}")

                if attempt < max_retries:
                    time.sleep(config.ENRICHMENT_RETRY_DELAY)

        # 所有重试耗尽 → 降级保留搜索页数据
        print(f"[Detail] WARN: enrichment 全部失败，降级: {last_error}")
        detail = NoteDetail()
        detail.merge_from_feed(feed)
        return detail

    def _build_detail_url(self, feed: FeedNote) -> str:
        """从搜索结果 URL 构建 explore 详情页 URL"""
        import re

        if "/explore/" in feed.url:
            if "xsec_token=" in feed.url:
                return feed.url
            if feed.xsec_token:
                sep = "&" if "?" in feed.url else "?"
                return f"{feed.url}{sep}xsec_token={feed.xsec_token}"
            return feed.url

        m = re.search(r"search_result/([a-fA-F0-9]+)", feed.url, re.IGNORECASE)
        if not m:
            return feed.url  # 兜底

        note_id = m.group(1)
        base = f"https://www.xiaohongshu.com/explore/{note_id}"

        if feed.xsec_token:
            return f"{base}?xsec_token={feed.xsec_token}&xsec_source=pc_search"
        return base

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

    def _extract_detail(self) -> NoteDetail:
        """从当前页面 DOM 提取详情（带 fallback）"""
        try:
            data = self._extract_detail_raw()
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

        return NoteDetail(
            content=data.get("content", ""),
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

    def _extract_detail_raw(self) -> dict:
        """实际执行 DOM 提取（所有选择器均加异常保护）"""
        return self.page.evaluate("""
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