import sys, time
sys.path.insert(0, '.')
from core.browser_manager import BrowserManager
import json

def block_login_activate():
    cookies = json.load(open('xhs_cookies.json'))

    with BrowserManager(headless=False) as (browser, context):
        for c in cookies:
            context.add_cookies([c])

        page = context.new_page()

        # 在请求发出前拦截 login/activate，如果是设置 cookie 的响应就取消
        intercepted_responses = []

        def handle_response(response):
            url = response.url
            if 'login/activate' in url or 'login/qrcode' in url:
                try:
                    body = response.text()
                    print(f"[INTERCEPTED] {url}")
                    print(f"  Status: {response.status}")
                    print(f"  Body: {body[:200]}")
                    intercepted_responses.append(response.url)
                except:
                    pass

        page.on('response', handle_response)

        print("Navigating...")
        page.goto("https://www.xiaohongshu.com", timeout=60000)
        page.wait_for_timeout(6000)

        print(f"\nURL: {page.url}")
        print(f"Intercepted: {len(intercepted_responses)} calls")

        # 检查 cookies 现在的状态
        all_cookies = context.cookies()
        ws_cookies = [c for c in all_cookies if c['name'] == 'web_session']
        print(f"\nweb_session cookies ({len(ws_cookies)}):")
        for c in ws_cookies:
            print(f"  domain={c['domain']} value={c['value'][:30]}...")

        # 检查 login modal
        try:
            modal = page.locator(".login-modal")
            if modal.is_visible(timeout=2000):
                print("\n[FAIL] Login modal visible")
            else:
                print("\n[PASS] No login modal!")
        except:
            print("\n[PASS] No login modal")

        page.close()

if __name__ == "__main__":
    block_login_activate()
