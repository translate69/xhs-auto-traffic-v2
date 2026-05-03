# -*- coding: utf-8 -*-
import sys, os, io
sys.path.insert(0, ".")
os.chdir(r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import time
import urllib.parse

from core.browser_manager import BrowserManager
from core.search_collector import SearchCollector, LoginRequiredError

keyword = "汕尾海边民宿推荐"
limit = 30

print(f"关键词: {keyword}")
print(f"模式: debug (有界面)")

with BrowserManager(headless=False) as (browser, context):
    page = context.new_page()
    url = f"https://www.xiaohongshu.com/search_result?keyword={urllib.parse.quote(keyword)}&type=51"
    print(f"\n访问: {url}")
    page.goto(url, wait_until="domcontentloaded")
    print(f"当前URL: {page.url}")
    page.screenshot(path="debug_A.png")

    # 检测登录态
    try:
        from core.search_collector import SearchCollector
        sc = SearchCollector(browser, context)
        sc._check_login()
        print("_check_login: 通过")
    except LoginRequiredError as e:
        print(f"_check_login: 抛出 LoginRequiredError → {e}")
    except Exception as e:
        print(f"_check_login: 其他异常 → {e}")

    page.screenshot(path="debug_B.png")

    # 等笔记列表
    t0 = time.time()
    try:
        page.wait_for_selector("section.note-item", timeout=15000)
        elapsed = time.time() - t0
        print(f"\nwait_for_selector 成功，耗时: {elapsed:.1f}s")
        page.screenshot(path="debug_C.png")
    except Exception as e:
        elapsed = time.time() - t0
        print(f"\nwait_for_selector 失败 ({elapsed:.1f}s)")
        page.screenshot(path="debug_C.png")
        print(f"当前URL: {page.url}")

    # 等弹窗遮罩
    time.sleep(3)
    page.screenshot(path="debug_D.png")
    print("\n截图已保存: debug_A/B/C/D.png")
