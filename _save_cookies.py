# -*- coding: utf-8 -*-
import sys, os, io
sys.path.insert(0, ".")
os.chdir(r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.browser_manager import BrowserManager
from pathlib import Path
import json

cookie_dst = Path(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json")

print("打开小红书浏览器（等待扫码登录）...")
print("请在浏览器中扫码登录小红书")
print("登录成功后会自动保存 Cookie...")

with BrowserManager(headless=False) as (browser, context):
    page = context.new_page()
    page.goto("https://www.xiaohongshu.com", wait_until="domcontentloaded")
    print("等待扫码...")

    # 等登录弹窗消失 = 登录成功
    page.wait_for_selector(".login-modal", state="hidden", timeout=120000)
    print(f"登录成功！URL: {page.url}")

    # 保存 cookie
    cookies = context.cookies()
    with open(cookie_dst, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)

    print(f"Cookie 已保存: {cookie_dst} ({len(cookies)} 条)")
    page.screenshot(path="login_success.png")
