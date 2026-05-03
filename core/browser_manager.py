"""
BrowserManager - 浏览器生命周期管理

职责：
  · 初始化 Chromium (headless / headed)
  · Cookie 加载 / 保存
  · is_logged_in() 登录态检测
  · 进程清理（只杀 Playwright 自己的进程，不影响用户浏览器）

使用方式：
  with BrowserManager() as browser:
      page = browser.new_page()
      ...
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import config
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Playwright

# ─── 辅助函数 ──────────────────────────────────────────────


def _get_chrome_pids() -> set[int]:
    """返回当前所有 chrome.exe PIDs"""
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq chrome.exe", "/FO", "CSV", "/NH"],
            text=True, encoding="gbk",
        )
        pids = set()
        for line in out.strip().split("\n"):
            parts = line.split(",")
            if len(parts) >= 2:
                try:
                    pids.add(int(parts[1].strip().strip('"')))
                except ValueError:
                    pass
        return pids
    except Exception:
        return set()


# ─── BrowserManager ─────────────────────────────────────────


class BrowserManager:
    """
    浏览器生命周期管理器。

    使用 with 语法：
        with BrowserManager() as (browser, context):
            page = context.new_page()
            ...

    自动管理：
      · Playwright 启动 / 关闭
      · Cookie 加载
      · Playwright 进程清理（只清自己，不影响用户浏览器）
    """

    def __init__(
        self,
        cookie_file: str | Path | None = None,
        headless: bool | None = None,
        viewport: dict | None = None,
    ):
        self.cookie_file = Path(cookie_file or config.COOKIE_FILE)
        self.headless = headless if headless is not None else config.HEADLESS
        self.viewport = viewport or config.VIEWPORT
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self._playwright_pids: set[int] = set()  # 仅 Playwright 的进程 PIDs

    def __enter__(self) -> tuple[Browser, BrowserContext]:
        # 记录启动前的 PIDs
        before_pids = _get_chrome_pids()

        # 启动 Playwright Chromium
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=config.BROWSER_ARGS,
        )

        # 等待子进程启动
        time.sleep(0.5)

        # 启动后新增的 PIDs = Playwright 的进程
        after_pids = _get_chrome_pids()
        self._playwright_pids = after_pids - before_pids

        # 新建 Context（隔离 cookie + 伪装 UA）
        self.context = self.browser.new_context(
            viewport=self.viewport,
            user_agent=config.USER_AGENT,
        )

        # 注入反检测脚本（每个新页面加载前执行）
        self.context.add_init_script(
            """Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
                configurable: true
            });"""
        )

        # 加载 Cookie
        self._load_cookies()

        return self.browser, self.context

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 关闭 context / browser
        if self.context:
            try:
                self.context.close()
            except Exception:
                pass
            self.context = None

        if self.browser:
            try:
                self.browser.close()
            except Exception:
                pass
            self.browser = None

        if self.playwright:
            try:
                self.playwright.stop()
            except Exception:
                pass
            self.playwright = None

        # 兜底清理：只杀 Playwright 启动的进程
        time.sleep(0.5)
        for pid in self._playwright_pids:
            try:
                subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                               capture_output=True)
            except Exception:
                pass

        return False  # 不吞异常

    def _load_cookies(self):
        """加载 xhs_cookies.json 到当前 Context"""
        if not self.cookie_file.exists():
            raise FileNotFoundError(f"Cookie 文件不存在: {self.cookie_file}")

        with open(self.cookie_file, encoding="utf-8") as f:
            cookies = json.load(f)

        self.context.add_cookies(cookies)

    def _load_cookies_to_context(self, target_context):
        """加载 xhs_cookies.json 到指定的 Context（用于串行模式）"""
        if not self.cookie_file.exists():
            raise FileNotFoundError(f"Cookie 文件不存在: {self.cookie_file}")

        with open(self.cookie_file, encoding="utf-8") as f:
            cookies = json.load(f)

        target_context.add_cookies(cookies)

    def is_logged_in(self) -> bool:
        """
        检测登录态。
        访问个人主页，能进入 → 已登录；被重定向 → 未登录。
        """
        if not self.context:
            raise RuntimeError("Context 未初始化，请先 __enter__")

        page = self.context.new_page()
        try:
            page.goto("https://www.xiaohongshu.com/user/profile", wait_until="domcontentloaded")
            time.sleep(2)

            # 检查是否跳转到登录页
            url = page.url
            page.close()

            if "login" in url or "redict" in url:
                return False
            return True
        except Exception:
            try:
                page.close()
            except Exception:
                pass
            return False

    def save_cookies(self):
        """保存当前 Context 的 Cookie 到文件"""
        if not self.context:
            raise RuntimeError("Context 未初始化")

        cookies = self.context.cookies()
        with open(self.cookie_file, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
