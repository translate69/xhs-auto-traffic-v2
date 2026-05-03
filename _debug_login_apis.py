import sys, json, time
sys.path.insert(0, '.')
from core.browser_manager import BrowserManager

def debug_login_apis():
    cookies = json.load(open('xhs_cookies.json'))

    with BrowserManager(headless=False) as (browser, context):
        for c in cookies:
            context.add_cookies([c])

        page = context.new_page()

        # 专门拦截这两个关键 API
        user_me_response = {}
        login_activate_response = {}

        def handle_response(response):
            url = response.url
            if 'user/me' in url and 'v2' in url:
                response.finished()
                body = response.text()
                user_me_response['url'] = url
                user_me_response['body'] = body
                user_me_response['status'] = response.status
            if 'login/activate' in url:
                response.finished()
                body = response.text()
                login_activate_response['url'] = url
                login_activate_response['body'] = body
                login_activate_response['status'] = response.status

        page.on('response', handle_response)

        print("Navigating...")
        page.goto("https://www.xiaohongshu.com", timeout=60000)
        page.wait_for_timeout(8000)

        print(f"URL: {page.url}")
        print()

        # Print user/me
        if user_me_response:
            print(f"[user/me] status={user_me_response['status']}")
            body = user_me_response['body']
            try:
                parsed = json.loads(body)
                print(f"  data: {json.dumps(parsed.get('data', {}), ensure_ascii=False)[:300]}")
                print(f"  code: {parsed.get('code')}")
                print(f"  msg: {parsed.get('msg')}")
            except:
                print(f"  raw: {body[:200]}")
        else:
            print("[user/me] NOT CAPTURED")

        print()

        # Print login/activate
        if login_activate_response:
            print(f"[login/activate] status={login_activate_response['status']}")
            body = login_activate_response['body']
            try:
                parsed = json.loads(body)
                print(f"  data: {json.dumps(parsed.get('data', {}), ensure_ascii=False)[:300]}")
                print(f"  code: {parsed.get('code')}")
                print(f"  msg: {parsed.get('msg')}")
            except:
                print(f"  raw: {body[:200]}")
        else:
            print("[login/activate] NOT CAPTURED")

        # Check modal
        print()
        modal_count = page.locator(".login-modal").count()
        print(f"Login modal count: {modal_count}")
        if modal_count > 0:
            vis = page.locator(".login-modal").first.is_visible()
            print(f"Login modal visible: {vis}")

        page.close()

if __name__ == "__main__":
    debug_login_apis()
