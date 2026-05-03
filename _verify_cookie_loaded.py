import sys, json, time
sys.path.insert(0, '.')
from core.browser_manager import BrowserManager

print("=== Step 1: Check xhs_cookies.json ===")
file_cookies = json.load(open('xhs_cookies.json'))
ws = next((c for c in file_cookies if c['name'] == 'web_session'), None)
print(f"web_session in file: {ws['value'][:40]}..." if ws else "NOT FOUND")
print(f"Total cookies in file: {len(file_cookies)}")

print("\n=== Step 2: Launch BrowserManager ===")
with BrowserManager(headless=False) as (browser, context):
    print("BrowserManager entered.")

    # Step 3: Check cookies in context after _load_cookies()
    ctx_cookies = context.cookies()
    ws_ctx = next((c for c in ctx_cookies if c['name'] == 'web_session'), None)
    print(f"\nweb_session in context after load: {ws_ctx['value'][:40]}..." if ws_ctx else "NOT FOUND")
    print(f"Total cookies in context: {len(ctx_cookies)}")

    # Step 4: Intercept all requests and log cookie header
    print("\n=== Step 3: Navigate to xiaohongshu.com ===")

    def on_request(request):
        if 'xiaohongshu.com' in request.url and ('user/me' in request.url or 'login/activate' in request.url):
            cookie_header = request.headers.get('cookie', '')
            ws_in_req = next((v for k, v in request.headers.items() if k.lower() == 'cookie' and 'web_session' in k), 'NOT FOUND')
            print(f"\n[REQUEST] {request.method} {request.url[:100]}")
            # extract just web_session from cookie header
            if 'web_session=' in cookie_header:
                start = cookie_header.find('web_session=')
                snippet = cookie_header[start:start+60]
                print(f"  Cookie: ...{snippet}...")

    def on_response(response):
        if 'user/me' in response.url and response.status == 200:
            try:
                body = json.loads(response.text())
                data = body.get('data', {})
                print(f"\n[RESPONSE] user/me -> code={body.get('code')} guest={data.get('guest')} red_id={data.get('red_id')}")
            except:
                pass
        if 'login/activate' in response.url and response.status == 200:
            try:
                body = json.loads(response.text())
                print(f"\n[RESPONSE] login/activate -> {body.get('msg')} session={body.get('data',{}).get('session','?')[:30]}")
            except:
                pass

    context.on('request', on_request)
    context.on('response', on_response)

    page = context.new_page()
    print("Navigating...")
    page.goto("https://www.xiaohongshu.com", timeout=60000)
    page.wait_for_timeout(5000)
    print(f"\nFinal URL: {page.url}")
    page.close()