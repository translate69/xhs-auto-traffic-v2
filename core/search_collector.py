"""
SearchCollector - 搜索采集层

职责：
  · 访问搜索结果页
  · FilterHelper: hover .filter → 面板内文字匹配 → 坐标点击（最新 + 一周内）
  · ScrollHelper: 滚动加载笔记列表
  · 提取: url, xsec_token, author, time_text
  · 采集层轻过滤: 时间门槛 + 去重
"""
from __future__ import annotations

import re
import time
import urllib.parse
from dataclasses import dataclass, field

import config
from core.scroll_helper import ScrollHelper
from utils.parse import parse_published_at
from utils.storage import RecentStorage


@dataclass
class FeedNote:
    """搜索列表页提取的最小笔记结构"""
    url: str = ""
    xsec_token: str = ""
    author: str = ""
    time_text: str = ""
    title: str = ""

    @property
    def note_id(self) -> str:
        """从 url 提取 note_id"""
        import re
        m = re.search(r"search_result/([a-zA-Z0-9]+)", self.url, re.IGNORECASE)
        return m.group(1) if m else ""


# ─── FilterHelper ───────────────────────────────────────────


class FilterHelper:
    """
    过滤面板点击助手。

    XHS 过滤面板默认隐藏，hover .filter 后才显示。
    方案：在 .filter .filter-panel 内扫描子元素 → 文字精确匹配 → 坐标点击。

    使用：
        helper = FilterHelper(page)
        helper.click_filter(["最新", "一周内"])
    """

    def __init__(self, page):
        self.page = page

    def click_filter(self, *labels: str):
        """
        依次点击过滤面板中的指定标签。
        例如：click_filter("最新", "一周内")

        只需 hover 一次，panel 保持开启。
        """
        self.page.hover(".filter")
        time.sleep(0.5)

        for label in labels:
            coord = self._find_coord(label)
            if coord:
                self.page.mouse.click(coord["x"], coord["y"])
                time.sleep(1.5)
            else:
                raise RuntimeError(f"找不到过滤选项: {label}")

    def _find_coord(self, label: str) -> dict | None:
        """在 .filter .filter-panel 内找文字精确匹配的坐标"""
        return self.page.evaluate(f"""
(function() {{
    var panel = document.querySelector('.filter .filter-panel');
    if (!panel) return null;
    var all = panel.querySelectorAll('*');
    for (var i = 0; i < all.length; i++) {{
        var el = all[i];
        var txt = (el.textContent||'').trim();
        var rect = el.getBoundingClientRect();
        if (rect.width < 5 || rect.height < 5 || rect.top < 0) continue;
        if (txt === '{label}') {{
            return {{
                x: Math.round(rect.x + rect.width / 2),
                y: Math.round(rect.top + rect.height / 2)
            }};
        }}
    }}
    return null;
}})()
        """)


# ─── SearchCollector ────────────────────────────────────────


class SearchCollector:
    """
    搜索采集器。

    流程：
      1. 访问搜索结果页
      2. 点击筛选（最新 + 一周内）
      3. 滚动加载笔记
      4. 提取列表数据
      5. 采集层轻过滤（时间门槛 + 去重）
    """

    SEARCH_URL = "https://www.xiaohongshu.com/search_result?keyword={keyword}&type=51"

    def __init__(self, browser, context):
        self.browser = browser
        self.context = context
        self.page = context.new_page()
        self.scroll_helper = ScrollHelper(self.page)
        self.storage = RecentStorage()

    def collect(self, keyword: str, limit: int = 30) -> list[FeedNote]:
        """
        执行完整采集流程。
        返回满足时间门槛且去重后的 FeedNote 列表。
        """
        if not self.page:
            raise RuntimeError("Page 未初始化")

        # 1. 访问搜索页
        url = self.SEARCH_URL.format(keyword=keyword)
        self.page.goto(url, wait_until="domcontentloaded")
        time.sleep(5)
        try:
            self.page.wait_for_selector("section.note-item", timeout=20000)
        except Exception as e:
            print(f"[SearchCollector] WARN: 等待笔记列表超时: {e}")
            self.page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_search_timeout.png")
            print(f"[SearchCollector] DEBUG: 已保存截图到 debug_search_timeout.png")

        # 2. 点击筛选
        filter_helper = FilterHelper(self.page)
        try:
            filter_helper.click_filter("最新", "一周内")
            print(f"[SearchCollector] 筛选完成: 最新 + 一周内")
        except RuntimeError as e:
            print(f"[SearchCollector] 筛选异常: {e}，继续使用默认排序")

        time.sleep(2)

        # 3. 滚动加载
        self.scroll_helper.scroll_to_count(
            target_count=limit,
            max_scrolls=config.DEFAULT_SCROLL_COUNT,
        )

        # 4. 提取数据
        feeds = self._extract_feeds()

        # 5. 采集层轻过滤
        filtered = self._apply_light_filter(feeds)

        print(f"[SearchCollector] 采集完成: {len(filtered)}/{len(feeds)} 条（时间+去重后）")
        return filtered

    def _extract_feeds(self) -> list[FeedNote]:
        """从当前 DOM 提取所有笔记数据"""
        data = self.page.evaluate("""
(function() {
    var notes = document.querySelectorAll('section.note-item');
    var result = [];
    for (var i = 0; i < notes.length; i++) {
        var note = notes[i];
        var item = {};

        // URL + xsec_token
        var link = note.querySelector('a.cover.mask');
        item.url = link ? (link.getAttribute('href') || '') : '';

        // 作者
        var nameEl = note.querySelector('.name-time-wrapper .name');
        item.author = nameEl ? (nameEl.textContent || '').trim() : '';

        // 时间
        var timeEl = note.querySelector('.name-time-wrapper .time');
        item.time_text = timeEl ? (timeEl.textContent || '').trim() : '';

        // 标题（可能为空）
        var titleEl = note.querySelector('.title span');
        item.title = titleEl ? (titleEl.textContent || '').trim() : '';

        result.push(item);
    }
    return result;
})()
        """)

        feeds = []
        import re
        for item in data:
            raw_url = item["url"]
            # 跳过无效 URL
            if not raw_url or "search_result" not in raw_url:
                continue
            m = re.search(r"xsec_token=([^&\s]+)", raw_url)
            xsec_token = urllib.parse.unquote(m.group(1)) if m else ""
            feeds.append(FeedNote(
                url=raw_url,
                xsec_token=xsec_token,
                author=item["author"],
                time_text=item["time_text"],
                title=item["title"],
            ))

        return feeds

    def _apply_light_filter(self, feeds: list[FeedNote]) -> list[FeedNote]:
        """
        采集层轻过滤：
          1. 时间过滤：超过 TIME_THRESHOLD_DAYS 天跳过
          2. 去重：note_id 在最近 7 天已采过跳过
        """
        from datetime import datetime

        now = datetime.now()
        result = []

        for feed in feeds:
            # 时间过滤
            if feed.time_text:
                pub_dt = parse_published_at(feed.time_text)
                if pub_dt is not None:
                    age_days = (now - pub_dt).days
                    if age_days > config.TIME_THRESHOLD_DAYS:
                        continue  # 时间过久，跳过

            # 去重
            note_id = feed.note_id
            if note_id and self.storage.is_recent(note_id):
                continue  # 已采过，跳过

            result.append(feed)

            # 记录
            if note_id:
                self.storage.mark_seen(note_id)

        return result
