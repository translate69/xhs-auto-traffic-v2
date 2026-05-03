# -*- coding: utf-8 -*-
import sys, os, io
sys.path.insert(0, ".")
os.chdir(r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.browser_manager import BrowserManager

print("打开小红书浏览器（headless=False）...")
with BrowserManager(headless=False) as (browser, context):
    page = context.new_page()
    page.goto("https://www.xiaohongshu.com", wait_until="domcontentloaded")
    print("按 Enter 关闭浏览器...")
    input()
