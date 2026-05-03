# -*- coding: utf-8 -*-
import sys, os, io
sys.path.insert(0, ".")
os.chdir(r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.browser_manager import BrowserManager
from pathlib import Path
import json

cookie_dst = Path(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json")

print("打开小红书浏览器...")
print("请在浏览器中扫码登录小红书，登录完成后在此界面回复我")

with BrowserManager(headless=False) as (browser, context):
    page = context.new_page()
    page.goto("https://www.xiaohongshu.com", wait_until="domcontentloaded")
    print("浏览器已打开，等待扫码登录...")
    print("登录完成后回复我任何消息即可，我会继续保存 Cookie")
