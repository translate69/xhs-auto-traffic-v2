"""
get_chrome_cookies.py - 通过 Chrome CDP 获取已登录的 cookie
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from playwright.sync_api import sync_playwright

def main():
    print("连接 Chrome CDP...")
    try:
        pw = sync_playwright().start()
        # 尝试连接到已运行的 Chrome
        browser = pw.chromium.connect_over_cdp("http://localhost:9222")
    except Exception as e:
        print(f"连接失败: {e}")
        print("请确认 Chrome 已开启调试模式:")
        print('  右键 Chrome 快捷方式 -> 目标末尾加 " --remote-debugging-port=9222"')
        sys.exit(1)

    print("获取上下文...")
    context = browser.contexts[0] if browser.contexts else browser.new_context()

    print("获取 cookies...")
    cookies = context.cookies()
    print(f"共 {len(cookies)} 个 cookies")

    # 检查关键 cookie
    web_sessions = [c for c in cookies if c["name"] == "web_session"]
    if web_sessions:
        print(f"web_session: {web_sessions[0]['value'][:20]}...")
    else:
        print("警告: 未找到 web_session")

    # 保存
    out_path = Path("E:/translate/claw/xhs-auto-traffic-v2/xhs_cookies.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)
    print(f"已保存到: {out_path}")

    browser.close()
    pw.stop()

if __name__ == "__main__":
    main()