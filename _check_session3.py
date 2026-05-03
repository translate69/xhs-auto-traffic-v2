import sys, json, time, re
sys.path.insert(0, '.')
from core.browser_manager import BrowserManager

def check_session():
    cookies = json.load(open('xhs_cookies.json'))
    ws = next((c for c in cookies if c['name'] == 'web_session'), None)
    print(f"web_session: {ws['value'][:40]}..." if ws else "No web_session!")

    with BrowserManager(headless=False) as (browser, context):
        for c in cookies:
            context.add_cookies([c])

        page = context.new_page()

        # Try to intercept API calls that indicate login status
        login_status = {}

        def handle_response(response):
            url = response.url
            if 'user_self' in url or 'user/info' in url or 'self' in url:
                try:
                    body = response.text()
                    login_status[url] = body[:200]
                except:
                    pass

        page.on("response", handle_response)

        page.goto("https://www.xiaohongshu.com", timeout=60000)
        page.wait_for_timeout(5000)

        url = page.url
        print(f"Final URL: {url}")
        print(f"Login status API responses:")
        for k, v in login_status.items():
            print(f"  {k}: {v}")

        # Check for login modal
        try:
            modal = page.locator(".login-modal")
            if modal.is_visible(timeout=3000):
                print("LOGIN MODAL: present -> NOT logged in")
            else:
                print("LOGIN MODAL: not visible -> likely logged in")
        except:
            print("LOGIN MODAL: check failed (not found)")

        page.close()

if __name__ == "__main__":
    check_session()
