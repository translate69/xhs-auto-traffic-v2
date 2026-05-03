import sys, time
sys.path.insert(0, '.')
from core.browser_manager import BrowserManager

def trace_request_headers():
    with BrowserManager(headless=False) as (browser, context):
        page = context.new_page()

        # 拦截 user/me 请求，打印所有请求头
        target_url = "user/me"

        def print_requestHeaders(request):
            if target_url in request.url:
                print(f"\n=== REQUEST HEADERS for {request.url} ===")
                for k, v in request.headers.items():
                    print(f"  {k}: {v}")

        def print_responseBody(response):
            if target_url in response.url:
                try:
                    body = response.text()
                    print(f"\n=== RESPONSE for {response.url} ===")
                    print(f"  Status: {response.status}")
                    import json
                    data = json.loads(body)
                    print(f"  code: {data.get('code')}, guest: {data.get('data',{}).get('guest')}")
                except:
                    pass

        page.on('request', print_requestHeaders)
        page.on('response', print_responseBody)

        page.goto("https://www.xiaohongshu.com", timeout=60000)
        page.wait_for_timeout(5000)

        print("\nDone.")
        page.close()

if __name__ == "__main__":
    trace_request_headers()
