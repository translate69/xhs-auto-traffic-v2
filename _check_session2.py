import sys, json, time
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
        page.goto("https://edith.xiaohongshu.com/api/sns/web/v1/user_self", timeout=30000)
        time.sleep(3)
        content = page.content()
        print(f"Response (first 500 chars): {content[:500]}")
        page.close()

if __name__ == "__main__":
    check_session()
