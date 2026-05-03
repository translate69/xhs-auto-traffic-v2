import sys, json, time
sys.path.insert(0, '.')
from core.browser_manager import BrowserManager
from playwright.sync_api import expect

def check_session():
    cookies = json.load(open('xhs_cookies.json'))
    ws = next((c for c in cookies if c['name'] == 'web_session'), None)
    print(f"web_session value: {ws['value'][:30]}..." if ws and ws.get('value') else "No web_session found!")

    with BrowserManager(headless=False) as (browser, context):
        # load cookies
        for c in cookies:
            context.add_cookies([c])

        page = context.new_page()
        page.goto("https://www.xiaohongshu.com", wait_until="networkidle", timeout=30000)
        time.sleep(2)

        url = page.url
        print(f"Current URL: {url}")

        # Check for login modal
        modal = page.locator(".login-modal").first
        modal_visible = modal.is_visible().catch(False)
        print(f"Login modal visible: {modal_visible}")

        if modal_visible:
            print("Login modal IS present -> session invalid or revoked")
        else:
            print("No login modal -> session appears valid")

        # Check for avatar (logged in indicator)
        avatar = page.locator(".user-author").first
        avatar_visible = avatar.is_visible().catch(False)
        print(f"Avatar visible: {avatar_visible}")

        page.close()

if __name__ == "__main__":
    check_session()
