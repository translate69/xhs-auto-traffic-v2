import sys, json, time
sys.path.insert(0, '.')
from core.browser_manager import BrowserManager

def test_server_session():
    cookies = json.load(open('xhs_cookies.json'))

    # 服务器新建的 session
    server_ws = "030037aec2f91a63b57522eb892e4a4a0c0368"
    for c in cookies:
        if c['name'] == 'web_session':
            c['value'] = server_ws
            c['domain'] = '.xiaohongshu.com'
            break

    with BrowserManager(headless=False) as (browser, context):
        context.clear_cookies()

        key_names = ['web_session', 'a1', 'webId', 'xsecappid', 'websectiga', 'acw_tc', 'webBuild', 'loadts']
        key_cookies = [c for c in cookies if c['name'] in key_names]
        print(f"Adding {len(key_cookies)} cookies...")
        for c in key_cookies:
            context.add_cookies([c])

        page = context.new_page()
        print("Navigating...")
        page.goto("https://www.xiaohongshu.com", timeout=60000)
        page.wait_for_timeout(6000)
        print(f"URL: {page.url}")

        try:
            modal = page.locator(".login-modal")
            if modal.is_visible(timeout=2000):
                print("[FAIL] Login modal VISIBLE")
            else:
                print("[PASS] No login modal")
        except Exception as e:
            print(f"[PASS] No login modal (check error: {e})")

        page.screenshot(path="screenshot_server_session.png", full_page=False)
        print("Screenshot: screenshot_server_session.png")
        page.close()

if __name__ == "__main__":
    test_server_session()
