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

# ─── SIGKILL 定位日志 ───────────────────────────────────
try:
    import os as _os
    _debug_log_path = _os.path.join(_os.path.dirname(__file__), "..", "_pipeline_debug.log")
    _debug_log_enabled = True

    def _log_stage(stage: str, flush: bool = True):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        line = f"[{ts}] [SearchColl] {stage}\n"
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


class LoginRequiredError(Exception):
    """"Cookie 失效，需扫码登录"""
    pass


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
        """从 url 提取 note_id（支持 /search_result/ 和 /explore/ 格式）"""
        import re
        m = re.search(r"/(?:search_result|explore)/([a-f0-9]+)", self.url, re.IGNORECASE)
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
        """
        self.page.hover(".filter")
        time.sleep(0.5)

        for label in labels:
            # 用 JS 找元素坐标，用 Playwright mouse.click 点击
            coord = self.page.evaluate(f"""
(function() {{
    var filter = document.querySelector('.filter');
    if (!filter) return null;
    var all = filter.querySelectorAll('*');
    for (var i = 0; i < all.length; i++) {{
        var el = all[i];
        var txt = (el.textContent || '').trim();
        var rect = el.getBoundingClientRect();
        if (txt === '{label}' && rect.width > 5 && rect.height > 5 && rect.top >= 0) {{
            return {{ x: Math.round(rect.x + rect.width/2), y: Math.round(rect.top + rect.height/2) }};
        }}
    }}
    return null;
}})()
            """)
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
    HOME_URL = "https://www.xiaohongshu.com/"
    SEARCH_INPUT_SELECTOR = "input[type='search'], input[placeholder*='搜索'], [class*='search-input'], [class*='search-input-inner'] input"
    SEARCH_BTN_SELECTOR = "button[type='submit'], [class*='search-btn'], [class*='search-button']"

    def __init__(self, browser, context):
        self.browser = browser
        self.context = context
        self.page = context.new_page()
        self.scroll_helper = ScrollHelper(self.page)
        self.storage = RecentStorage()

    # ── 登录态检测 ───────────────────────────────────────

    def _check_login(self):
        """
        检测当前页面是否需要登录。
        小红书 cookie 失效时不总是 URL 重定向，
        也可能在原 URL 显示未登录遮罩（reds-mask）。
        用内容检测：检查是否有登录相关元素，或者缺少已登录用户元素。
        抛出 LoginRequiredError， callers 负责向上传递给 UI 层提示用户扫码。
        """
        current_url = self.page.url

        # 1. URL 重定向检测（传统方式）
        if any(kw in current_url.lower() for kw in ["login", "/w/user/login", "/w/login"]):
            import os
            screenshot_path = "E:/translate/claw/xhs-auto-traffic-v2/debug_login_url.png"
            self.page.screenshot(path=screenshot_path)
            with open("E:/translate/claw/xhs-auto-traffic-v2/debug_login_url.txt", "w", encoding="utf-8") as f:
                f.write(f"URL={current_url}\n")
            raise LoginRequiredError(
                "小红书登录态失效（URL 重定向），需重新扫码登录。"
            )

        # 2. 登录弹窗特征元素检测
        try:
            self.page.wait_for_selector(
                "[class*='login'], [class*='login-modal'], .login-container",
                timeout=3000
            )
            raise LoginRequiredError(
                "检测到登录弹窗，请在浏览器中重新扫码登录小红书后保存 cookie。"
            )
        except Exception:
            pass  # 正常页面，无弹窗

        # 3. 内容级检测：已登录用户的头像/昵称应在页头
        #    未登录时页头是「登录/注册」按钮
        try:
            self.page.wait_for_selector(
                ".user-author, .user-info, [class*='user-author'], [class*='avatar']",
                timeout=5000
            )
        except Exception:
            # 未找到已登录用户特征元素，可能未登录
            # 截图留证（包含 reds-mask 等遮罩情况）
            self.page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_login_required.png")
            raise LoginRequiredError(
                "小红书登录态失效（未检测到登录用户信息），请扫码登录后重试。"
            )



    def _go_to_search_via_homepage(self, keyword: str):
        """
        从首页输入关键词搜索，绕过直接访问 search_result 的风控。
        流程：首页 → 填搜索框 → 点搜索 → 等待结果页
        """
        # Step 1: 访问首页
        _log_stage("goto: 小红书首页", flush=False)
        self.page.goto(self.HOME_URL, wait_until="domcontentloaded")
        time.sleep(3)

        # Step 2: 用页面级 fill 找到真实可见的 input
        try:
            self.page.fill("#search-input", keyword)
            _log_stage(f"搜索框已fill: {keyword}", flush=False)
        except Exception as e:
            _log_stage(f"fill 失败: {e}", flush=False)
            self.page.goto(self.SEARCH_URL.format(keyword=keyword),
                           wait_until="domcontentloaded")
            return

        time.sleep(1)

        # Step 3: 用页面级 keyboard.press 确保在正确元素上触发
        _log_stage("按回车触发搜索", flush=False)
        self.page.keyboard.press("Enter")

        # Step 4: 等待搜索结果页加载
        time.sleep(5)
        try:
            self.page.wait_for_selector("section.note-item", timeout=30000)
            _log_stage("搜索结果页面加载完成", flush=False)
        except Exception:
            _log_stage("等待笔记列表超时，继续", flush=False)

    def collect(self, keyword: str, limit: int = 30) -> list[FeedNote]:
        """
        执行完整采集流程。
        返回满足时间门槛且去重后的 FeedNote 列表。
        """
        if not self.page:
            raise RuntimeError("Page 未初始化")

        # 通过首页搜索方式访问（绕过风控）
        self._go_to_search_via_homepage(keyword)

        # 检测登录态（cookie 失效时小红书会重定向到登录页）
        self._check_login()
        _log_stage("登录检测通过", flush=False)

        time.sleep(5)
        try:
            self.page.wait_for_selector("section.note-item", timeout=60000)
            _log_stage("笔记列表出现", flush=False)
        except Exception as e:
            print(f"[SearchCollector] WARN: 等待笔记列表超时: {e}")
            self.page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_search_timeout.png")
            print(f"[SearchCollector] DEBUG: 已保存截图到 debug_search_timeout.png")

        # 2. 点击筛选（仅 search_result 页面有 filter）
        # /explore 页面（首页搜索跳转）没有筛选功能，跳过
        _log_stage("点击筛选: 最新 + 一周内", flush=False)
        filter_helper = FilterHelper(self.page)
        try:
            filter_helper.click_filter("最新", "一周内")
            print(f"[SearchCollector] 筛选完成: 最新 + 一周内")
        except Exception as e:
            # /explore 页面没有 .filter 元素，使用默认排序
            print(f"[SearchCollector] 筛选跳过（无 filter 面板或超时），使用默认排序: {e}")

        time.sleep(2)

        # 3. 滚动加载
        _log_stage("开始滚动加载", flush=False)
        self.scroll_helper.scroll_to_count(
            target_count=limit,
            max_scrolls=config.DEFAULT_SCROLL_COUNT,
        )
        _log_stage("滚动加载完成", flush=False)

        # 4. 提取数据
        _log_stage("开始提取Feeds", flush=False)
        feeds = self._extract_feeds()
        _log_stage(f"提取完成，返回 {len(feeds)} 条Feeds", flush=True)

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
            # 跳过无效 URL（支持 /search_result/, /explore/, /note/ 格式）
            if not raw_url or ("/note/" not in raw_url and "/explore/" not in raw_url and "/search_result/" not in raw_url):
                continue
            # 提取 note_id
            m = re.search(r"/(?:search_result|note|explore)/([a-f0-9]+)", raw_url)
            if not m:
                continue
            note_id = m.group(1)
            xsec_m = re.search(r"xsec_token=([^&\s]+)", raw_url)
            xsec_token = urllib.parse.unquote(xsec_m.group(1)) if xsec_m else ""
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
