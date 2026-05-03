# -*- coding: utf-8 -*-
"""
保持浏览器开启的脚本，等待用户扫码后手动保存 cookie
"""
import sys, os, io, json
sys.path.insert(0, ".")
os.chdir(r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.browser_manager import BrowserManager
from pathlib import Path

cookie_dst = Path(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json")

print("=== 小红书 Cookie 获取器 ===")
print()

with BrowserManager(headless=False) as (browser, context):
    page = context.new_page()
    page.goto("https://www.xiaohongshu.com", wait_until="domcontentloaded")
    print("✅ 浏览器已打开，请扫码登录小红书")
    print()

    # 等待用户按 Enter（表示已登录完成）
    print("登录完成后在下面输入 'ok' 并回车:")
    user_input = input("> ").strip()

    if user_input.lower() == "ok":
        print("\n保存 Cookie...")
        cookies = context.cookies()
        with open(cookie_dst, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print(f"✅ 已保存到: {cookie_dst}")
        print(f"   共 {len(cookies)} 条 cookie")
        page.screenshot(path="login_done.png")
        print("   截图: login_done.png")
    else:
        print("未确认，Cookie 未保存")