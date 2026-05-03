# -*- coding: utf-8 -*-
import sys, os, io
sys.path.insert(0, ".")
os.chdir(r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import time
import urllib.parse

from core.browser_manager import BrowserManager

keyword = "汕尾海边民宿推荐"
print(f"关键词: {keyword}")
print(f"浏览器: 有界面（可见）")
print(f"等待笔记列表加载...\n")

with BrowserManager(headless=False) as (browser, context):
    page = context.new_page()
    url = f"https://www.xiaohongshu.com/search_result?keyword={urllib.parse.quote(keyword)}&type=51"
    print(f"访问: {url}")

    page.goto(url, wait_until="domcontentloaded")
    print("页面加载完成，等待笔记列表...")

    t0 = time.time()
    try:
        page.wait_for_selector("section.note-item", timeout=60000)
        elapsed = time.time() - t0
        print(f"笔记列表加载完成，耗时: {elapsed:.1f}s")
    except Exception as e:
        elapsed = time.time() - t0
        print(f"等待失败 ({elapsed:.1f}s): {e}")
        page.screenshot(path="debug_search_timeout.png")
        print("截图已保存: debug_search_timeout.png")
