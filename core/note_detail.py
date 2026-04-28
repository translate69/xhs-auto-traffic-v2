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

sys.stdout.reconfigure(encoding='utf-8')

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
    _filter_result: dict | None = field(default_factory=lambda: None)  # 筛选结果

    def has_content(self) -> bool:
        """是否有正文（判断降级是否生效）"""
        return bool(self.content)

    def merge_from_feed(self, feed: FeedNote):
        """用搜索页已有数据填充（降级时使用）"""
        self.url = feed.url or self.url
        self.xsec_token = feed.xsec_token or self.xsec_token
        self.author = feed.author or self.author
        self.time_text = feed.time_text or self.time_text


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
                    print(f"[Detail] WARN: 正文为空，降级保留搜索页数据")

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

    def _extract_detail(self) -> NoteDetail:
        """从当前页面 DOM 提取详情"""
        data = self.page.evaluate("""
(function() {
    var r = {};

    // 正文
    var desc = document.querySelector('#detail-desc');
    r.content = desc ? (desc.textContent || '').trim() : '';

    // 标签
    var tagEls = desc ? desc.querySelectorAll('a.tag') : [];
    r.tags = [];
    for (var i = 0; i < tagEls.length; i++) {
        var txt = (tagEls[i].textContent || '').trim();
        if (txt) r.tags.push(txt);
    }

    // 作者
    var nameEl = document.querySelector('.author .info .name, .author-wrapper .name');
    r.author = nameEl ? (nameEl.textContent || '').trim() : '';

    // 作者 ID
    var authorLink = document.querySelector('.author a, .author-wrapper a');
    var href = authorLink ? (authorLink.getAttribute('href') || '') : '';
    var m = href.match(/profile\\/([^?]+)/);
    r.author_id = m ? m[1] : '';

    // 点赞/收藏/评论
    var countEls = document.querySelectorAll('[class*="count"]');
    var counts = [];
    for (var i = 0; i < countEls.length; i++) {
        var txt = (countEls[i].textContent || '').trim();
        if (txt && !isNaN(parseInt(txt))) counts.push(parseInt(txt));
    }
    r.likes = counts[0] || 0;
    r.collects = counts[1] || 0;
    r.comments = counts[2] || 0;

    // 时间
    var dateEl = document.querySelector('.date, [class*="date"]');
    r.time_text = dateEl ? (dateEl.textContent || '').trim() : '';

    // 正文图片
    var imgs = desc ? desc.querySelectorAll('img') : [];
    r.images = [];
    for (var i = 0; i < imgs.length; i++) {
        var src = imgs[i].getAttribute('src') || imgs[i].getAttribute('data-src') || '';
        if (src && !src.includes('avatar')) r.images.push(src);
    }

    return r;
})()
        """)

        # 解析时间（去掉地名后缀）
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
