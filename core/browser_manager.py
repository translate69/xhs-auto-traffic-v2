"""
BrowserManager - 浏览器生命周期管理

职责：
  · 初始化 Chromium (headless / headed)
  · Cookie 加载 / 保存
  · is_logged_in() 登录态检测
  · 进程清理（只清 Playwright 自己的进程，不影响用户浏览器）
  · Windows Job Object 防止 Chromium 子进程残留
  · 信号处理确保 __exit__ 一定被调用

使用方式：
  with BrowserManager() as (browser, context):
      page = context.new_page()
      ...
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import config
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Playwright

# ─── 辅助函数 ──────────────────────────────────────────────

_PID_FILE = Path(config.PROJECT_ROOT or ".") / ".playwright_pids"


def _save_playwright_pids(pids: set[int]):
    try:
        with open(_PID_FILE, "w", encoding="utf-8") as f:
            json.dump(list(pids), f)
    except Exception:
        pass


def _load_playwright_pids() -> set[int]:
    if not _PID_FILE.exists():
        return set()
    try:
        with open(_PID_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def _kill_only_playwright_pids(pids: set[int]):
    if not pids:
        return
    for pid in pids:
        try:
            subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                capture_output=True, timeout=5
            )
        except Exception:
            pass
    time.sleep(0.3)


def _get_chrome_pids() -> set[int]:
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


def _kill_all_chromes():
    """仅用于异常恢复兜底（不推荐在正常流程中使用）"""
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "chrome.exe", "/T"],
            capture_output=True, timeout=10
        )
    except Exception:
        pass
    time.sleep(0.3)


# ─── 信号处理 ──────────────────────────────────────────────

# 全局 BrowserManager 实例（用于信号处理）
_g_browser_manager: "BrowserManager | None" = None


def _sigint_handler(signum, frame):
    """SIGINT (Ctrl+C) 时先关闭浏览器再退出"""
    print("\n[BrowserManager] 收到 SIGINT，正在关闭浏览器...")
    if _g_browser_manager is not None:
        try:
            _g_browser_manager._safe_exit()
        except Exception:
            pass
    sys.stdout.flush()
    sys.exit(0)


# ─── BrowserManager ─────────────────────────────────────────


class BrowserManager:
    """
    浏览器生命周期管理器。
    · 只清理 Playwright 自己的 Chromium 进程，不影响用户的 Chrome 浏览器
    · Windows Job Object 防止子进程残留
    · 信号处理确保 Ctrl+C 时正确清理
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
        self._playwright_pids: set[int] = set()
        self._job_handle: int | None = None  # Windows Job Object handle

    def _create_job_object(self):
        """创建 Windows Job Object，将 Chromium 进程关联进去，实现组级别 kill"""
        if sys.platform != "win32":
            return None
        try:
            # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
            kernel32 = __import__('ctypes').windll.kernel32
            job = kernel32.CreateJobObjectW(None, None)
            if not job:
                return None
            # 设置子进程随 Job 关闭而终止
            class _JOBOBJECT_BASIC_LIMIT_INFORMATION:
                pass
            from ctypes import wintypes
            # struct size + flags (KILL_ON_JOB_CLOSE = 0x2000)
            info = (b'\x00' * 48)  # sizeof(JOBOBJECT_BASIC_LIMIT_INFORMATION) = 48
            # 设置 JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            info_view = bytearray(info)
            # flags at offset 40 (DWORD), value = 0x2000
            import struct
            struct.pack_into('I', info_view, 40, 0x2000)
            kernel32.SetInformationJobObject(
                job, 2,  # JobObjectBasicLimitInformation
                bytes(info_view), len(bytes(info_view))
            )
            return job
        except Exception:
            return None

    def _assign_to_job(self, job_handle: int, pid: int):
        """将指定 PID 的进程 Assign 到 Job Object"""
        if sys.platform != "win32" or not job_handle:
            return
        try:
            kernel32 = __import__('ctypes').windll.kernel32
            kernel32.AssignProcessToJobObject(job_handle, pid)
        except Exception:
            pass

    def __enter__(self) -> tuple[Browser, BrowserContext]:
        global _g_browser_manager

        # 注册信号处理
        if _g_browser_manager is None:
            signal.signal(signal.SIGINT, _sigint_handler)

        # 启动前 Targeted 清理上次残留 PIDs
        prev_pids = _load_playwright_pids()
        if prev_pids:
            _kill_only_playwright_pids(prev_pids)

        # 创建 Windows Job Object
        self._job_handle = self._create_job_object()

        # 记录启动前的 PIDs
        before_pids = _get_chrome_pids()

        # 启动 Playwright Chromium
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=config.BROWSER_ARGS,
        )

        time.sleep(0.5)

        # 记录 Playwright PIDs
        after_pids = _get_chrome_pids()
        self._playwright_pids = after_pids - before_pids
        _save_playwright_pids(self._playwright_pids)

        # 将 Playwright 进程加入 Job Object
        if self._job_handle:
            for pid in self._playwright_pids:
                self._assign_to_job(self._job_handle, pid)

        # 新建 Context
        self.context = self.browser.new_context(
            viewport=self.viewport,
            user_agent=config.USER_AGENT,
        )
        self.context.add_init_script(
            """Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
                configurable: true
            });"""
        )

        self._load_cookies()

        # 注册全局引用（供信号处理器用）
        _g_browser_manager = self

        return self.browser, self.context

    def _safe_exit(self):
        """安全关闭浏览器（供信号处理器调用）"""
        self._close_browser()
        _save_playwright_pids(set())

    def _close_browser(self):
        """关闭浏览器进程（带超时保护）"""
        deadline = time.time() + 5  # 5 秒超时

        # 优先用 kill() 强制杀，不用 graceful close()
        # kill() 直接终止 Chromium 主进程，Job Object 会自动带走所有子进程
        if self.browser:
            try:
                self.browser.kill()   # <-- 强制杀，不留死角
            except Exception:
                pass
            finally:
                self.browser = None

        if self.context:
            try:
                self.context.close()
            except Exception:
                pass
            self.context = None

        if self.playwright:
            try:
                self.playwright.stop()
            except Exception:
                pass
            self.playwright = None

        # 超时则 Targeted kill 兜底
        if time.time() >= deadline:
            _kill_only_playwright_pids(self._playwright_pids)

        # 最后 Targeted 清理残留 PIDs（双重保险）
        _kill_only_playwright_pids(self._playwright_pids)
        prev_pids = _load_playwright_pids()
        if prev_pids:
            _kill_only_playwright_pids(prev_pids)

        self._playwright_pids = set()

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _g_browser_manager
        _g_browser_manager = None
        self._close_browser()
        return False  # 不吞异常

    def _load_cookies(self):
        if not self.cookie_file.exists():
            raise FileNotFoundError(f"Cookie 文件不存在: {self.cookie_file}")
        with open(self.cookie_file, encoding="utf-8") as f:
            cookies = json.load(f)
        self.context.add_cookies(cookies)

    def _load_cookies_to_context(self, target_context):
        if not self.cookie_file.exists():
            raise FileNotFoundError(f"Cookie 文件不存在: {self.cookie_file}")
        with open(self.cookie_file, encoding="utf-8") as f:
            cookies = json.load(f)
        target_context.add_cookies(cookies)

    def is_logged_in(self) -> bool:
        if not self.context:
            raise RuntimeError("Context 未初始化，请先 __enter__")
        page = self.context.new_page()
        try:
            page.goto("https://www.xiaohongshu.com/user/profile",
                      wait_until="domcontentloaded")
            time.sleep(2)
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
        if not self.context:
            raise RuntimeError("Context 未初始化")
        cookies = self.context.cookies()
        with open(self.cookie_file, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
