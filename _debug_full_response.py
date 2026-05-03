import sys, json, time
sys.path.insert(0, '.')
from core.browser_manager import BrowserManager

def debug_login_flow():
    cookies = json.load(open('xhs_cookies.json'))
    ws = next((c for c in cookies if c['name'] == 'web_session'), None)
    print(f"web_session: {ws['value'][:40]}...")

    with BrowserManager(headless=False) as (browser, context):
        # 手动设置 cookies
        for c in cookies:
            context.add_cookies([c])

        page = context.new_page()

        # 拦截所有小红书 API 响应
        api_responses = []
        def handle_response(response):
            url = response.url
            if 'xiaohongshu.com' in url and ('api' in url or 'sns' in url):
                try:
                    api_responses.append({
                        'url': url,
                        'status': response.status,
                        'headers': dict(response.headers),
                    })
                except:
                    pass

        page.on('response', handle_response)

        print("Navigating to xiaohongshu.com...")
        page.goto("https://www.xiaohongshu.com", timeout=60000)
        page.wait_for_timeout(8000)

        print(f"\nFinal URL: {page.url}")

        # 打印所有 API 响应
        print(f"\nCaptured {len(api_responses)} API responses:")
        for r in api_responses:
            print(f"  [{r['status']}] {r['url'][:100]}")

        # 检查 login modal
        try:
            modal = page.locator(".login-modal")
            if modal.is_visible(timeout=2000):
                print("\n❌ Login modal VISIBLE")
                # 获取 modal 内容
                modal_html = modal.inner_html().catch(False)
                if modal_html:
                    print(f"Modal content (first 200): {modal_html[:200]}")
            else:
                print("\n✅ No login modal")
        except Exception as e:
            print(f"\nModal check: {e}")

        # 检查页面标题
        print(f"\nPage title: {page.title()}")
        print(f"Page URL: {page.url}")

        page.close()

if __name__ == "__main__":
    debug_login_flow()
