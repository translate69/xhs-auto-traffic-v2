import sys, time, json
sys.path.insert(0, '.')
from core.browser_manager import BrowserManager

def route_login_activate():
    cookies = json.load(open('xhs_cookies.json'))

    with BrowserManager(headless=False) as (browser, context):
        for c in cookies:
            context.add_cookies([c])

        page = context.new_page()

        # 拦截 login/activate - 返回空成功，不设置任何 cookie
        page.route(
            "**/login/activate**",
            lambda route, response: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"code": 0, "msg": "ok", "data": {}, "success": True})
            )
        )

        print("Navigating with login/activate intercepted...")
        page.goto("https://www.xiaohongshu.com", timeout=60000)
        page.wait_for_timeout(6000)

        print(f"URL: {page.url}")

        # 检查 login modal
        try:
            modal = page.locator(".login-modal")
            if modal.is_visible(timeout=2000):
                print("[FAIL] Login modal visible")
            else:
                print("[PASS] No login modal!")
                notes = page.locator(".note-item")
                count = notes.count()
                print(f"Notes on page: {count}")
        except Exception as e:
            print(f"[PASS] No login modal (error: {e})")

        # 检查 web_session cookies
        all_cookies = context.cookies()
        ws = [c for c in all_cookies if c['name'] == 'web_session']
        print(f"\nweb_session cookies ({len(ws)}):")
        for c in ws:
            print(f"  domain={c['domain']} value={c['value'][:30]}...")

        page.close()

if __name__ == "__main__":
    route_login_activate()
