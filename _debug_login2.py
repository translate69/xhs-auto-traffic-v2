# -*- coding: utf-8 -*-
import sys, os, io
sys.path.insert(0, ".")
os.chdir(r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.browser_manager import BrowserManager
from core.search_collector import SearchCollector
import time, urllib.parse

keyword = "汕尾海边民宿推荐"

with BrowserManager(headless=False) as (browser, context):
    page = context.new_page()
    url = f"https://www.xiaohongshu.com/search_result?keyword={urllib.parse.quote(keyword)}&type=51"
    print(f"访问: {url}")
    page.goto(url, wait_until="domcontentloaded")
    time.sleep(3)

    print(f"当前URL: {page.url}")

    # 测试 _check_login 的选择器
    selectors_to_test = [
        ".user-author", ".user-info", "[class*='user-author']", "[class*='avatar']",
        ".login-btn", ".login-modal",
        "[class*='avatar']", "[class*='user']", "[class*='nickname']"
    ]

    print("\n页面元素检测:")
    for sel in selectors_to_test:
        try:
            el = page.wait_for_selector(sel, timeout=2000)
            if el:
                cls = el.get_attribute('class') or ''
                txt = (el.inner_text() or '')[:30].replace('\n', ' ')
                print(f"  ✅ {sel} → class={cls!r} text={txt!r}")
        except Exception as e:
            print(f"  ❌ {sel}: {str(e)[:50]}")

    # 截图
    page.screenshot(path="logged_in_check.png")
    print("\n截图: logged_in_check.png")
