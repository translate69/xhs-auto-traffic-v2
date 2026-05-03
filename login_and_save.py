"""
login_and_save.py - 扫码登录小红书并保存 Cookie

用法：python login_and_save.py
1. 弹出手动浏览器窗口
2. 你手动扫码登录
3. 完成后按 Enter 保存 cookie
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config
from playwright.sync_api import sync_playwright

def main():
    print("[1] 启动手动浏览器...")
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=False, args=config.BROWSER_ARGS)
    context = browser.new_context(
        viewport=config.VIEWPORT,
        user_agent=config.USER_AGENT,
    )

    page = context.new_page()
    print("[2] 打开登录页...")
    page.goto("https://www.xiaohongshu.com/login", wait_until="domcontentloaded")
    time.sleep(2)

    print("")
    print("=" * 50)
    print("  请在浏览器中扫码登录小红书")
    print("  登录完成后回到此窗口按 Enter 保存 cookie")
    print("  按 Ctrl+C 取消")
    print("=" * 50)
    print("")

    # 等待用户按 Enter
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        print("取消")
        page.close()
        context.close()
        browser.close()
        pw.stop()
        sys.exit(0)

    print("[3] 保存 cookie...")

    # 验证登录态
    cookies = context.cookies()
    web_sessions = [c for c in cookies if c["name"] == "web_session"]
    if web_sessions:
        print(f"     web_session: {web_sessions[0]['value'][:20]}...")
        print(f"     共 {len(cookies)} 个 cookie")
    else:
        print("     警告: 未找到 web_session")

    out_path = Path(config.COOKIE_FILE)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)

    print(f"[OK] Cookie 已保存到: {out_path}")

    print("[4] 关闭浏览器...")
    time.sleep(2)
    page.close()
    context.close()
    browser.close()
    pw.stop()
    print("[完成]")

if __name__ == "__main__":
    main()