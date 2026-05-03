import sys, time
sys.path.insert(0, '.')
from core.browser_manager import BrowserManager
import urllib.parse

def find_search_api():
    with BrowserManager(headless=False) as (browser, context):
        page = context.new_page()

        # 拦截所有 API 请求
        api_calls = []
        def on_request(request):
            url = request.url
            if 'xiaohongshu.com' in url and ('api' in url or 'search' in url):
                api_calls.append({'url': url, 'method': request.method})

        page.on('request', on_request)

        print("Navigating to search page...")
        page.goto(f"https://www.xiaohongshu.com/search_result?keyword={urllib.parse.quote('汕尾美食')}", timeout=60000)
        page.wait_for_timeout(5000)

        print(f"\nCaptured {len(api_calls)} API calls:")
        for call in api_calls:
            print(f"  {call['method']} {call['url'][:150]}")

        page.close()

if __name__ == "__main__":
    find_search_api()
