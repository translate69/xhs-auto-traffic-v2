# -*- coding: utf-8 -*-
import sys, os, io
sys.path.insert(0, ".")
os.chdir(r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import time
import urllib.parse

from core.browser_manager import BrowserManager
from core.search_collector import SearchCollector

keyword = "汕尾海边民宿推荐"
limit = 30

print(f"关键词: {keyword}")

with BrowserManager(headless=False) as (browser, context):
    page = context.new_page()
    url = f"https://www.xiaohongshu.com/search_result?keyword={urllib.parse.quote(keyword)}&type=51"
    print(f"访问: {url}")

    page.goto(url, wait_until="domcontentloaded")
    print("domcontentloaded 完成")
    page.screenshot(path="1_domcontentloaded.png")
    print(f"截图1: 1_domcontentloaded.png (url={page.url})")

    time.sleep(5)
    print("sleep(5) 结束")
    page.screenshot(path="2_after_sleep.png")
    print(f"截图2: 2_after_sleep.png (url={page.url})")

    t0 = time.time()
    try:
        page.wait_for_selector("section.note-item", timeout=20000)
        elapsed = time.time() - t0
        print(f"wait_for_selector 成功，耗时: {elapsed:.1f}s")
        page.screenshot(path="3_notes_visible.png")
        print(f"截图3: 3_notes_visible.png")
    except Exception as e:
        elapsed = time.time() - t0
        print(f"wait_for_selector 失败 ({elapsed:.1f}s): {e}")
        page.screenshot(path="3_notes_timeout.png")
        print(f"截图3: 3_notes_timeout.png")
