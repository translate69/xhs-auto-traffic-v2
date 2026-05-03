# -*- coding: utf-8 -*-
import sys, os, io
sys.path.insert(0, ".")
os.chdir(r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.browser_manager import BrowserManager
import time, urllib.parse

keyword = "汕尾海边民宿推荐"

with BrowserManager(headless=False) as (browser, context):
    page = context.new_page()
    url = f"https://www.xiaohongshu.com/search_result?keyword={urllib.parse.quote(keyword)}&type=51"
    page.goto(url, wait_until="domcontentloaded")
    time.sleep(10)

    print(f"当前URL: {page.url}")
    page.screenshot(path="login_debug.png")

    # 尝试找用户相关元素
    selectors = [
        ".user-author", ".user-info", "[class*='user-author']", "[class*='avatar']",
        ".login-btn", "[class*='login']", ".header-user", ".user-nickname",
        "[class*='header']", "[class*='nav']"
    ]
    print("页面DOM关键元素:")
    for sel in selectors:
        try:
            el = page.wait_for_selector(sel, timeout=2000)
            if el:
                print(f"  ✅ {sel}: {el.get_attribute('class')}")
        except Exception:
            print(f"  ❌ {sel}: 未找到")
