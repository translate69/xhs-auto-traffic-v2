# -*- coding: utf-8 -*-
import sys, os, io
sys.path.insert(0, ".")
os.chdir(r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.browser_manager import BrowserManager
from core.search_collector import LoginRequiredError
import time, json

print("=== 登录态完整排查 ===")

with BrowserManager(headless=False) as (browser, context):
    cookies = context.cookies()
    print(f"\n1. Cookie 加载: {len(cookies)} 条")
    names = [c["name"] for c in cookies]
    print(f"   web_session 在列表: {'web_session' in names}")
    if "web_session" in names:
        ws = next(c for c in cookies if c["name"] == "web_session")
        print(f"   web_session 值: {ws['value']}")

    # 2. 访问搜索页
    page = context.new_page()
    page.goto("https://www.xiaohongshu.com/search_result?keyword=汕尾海边民宿推荐&type=51", wait_until="domcontentloaded")
    time.sleep(5)
    print(f"\n2. 搜索页 URL: {page.url}")

    # 3. 检查各层信号
    print(f"\n3. 检测信号:")
    print(f"   URL 含 login/redict/w/: {any(kw in page.url for kw in ['login','redict','/w/'])}")
    try:
        modal = page.wait_for_selector(".login-modal", timeout=3000)
        print(f"   .login-modal 弹窗: 存在 → {modal.get_attribute('class')}")
    except Exception:
        print(f"   .login-modal 弹窗: 无")

    try:
        avatar = page.wait_for_selector("[class*='avatar']", timeout=3000)
        print(f"   avatar 元素: 存在 → {avatar.get_attribute('class')}")
    except Exception:
        print(f"   avatar 元素: 无")

    # 4. 完整 DOM 快照
    try:
        notes = page.query_selector_all("section.note-item")
        print(f"   笔记列表项数: {len(notes)}")
    except Exception:
        print(f"   笔记列表: 无法查询")

    page.screenshot(path="debug_login_full.png")
    print(f"\n4. 截图已保存: debug_login_full.png")
