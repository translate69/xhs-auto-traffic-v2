import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
import time
import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    cookies = json.load(open(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json"))
    context.add_cookies(cookies)

    page = context.new_page()
    page.set_default_timeout(15000)

    # Capture ALL requests/responses from homepage to search
    all_requests = []
    all_responses = []
    
    def on_request(request):
        url = request.url
        if any(k in url for k in ['search', 'feed', 'note', 'recommend', 'cluster', 'xhs']):
            all_requests.append(f"[{request.method}] {url.replace('https://edith.xiaohongshu.com','').replace('https://www.xiaohongshu.com','')}")
    
    def on_response(response):
        url = response.url
        if any(k in url for k in ['search', 'feed', 'note', 'recommend', 'cluster']):
            try:
                body = response.body()
                preview = body[:100].decode('utf-8', errors='replace')
            except:
                preview = 'N/A'
            all_responses.append(f"[{response.status}] {url.replace('https://edith.xiaohongshu.com','')}: {preview}")

    page.on("request", on_request)
    page.on("response", on_response)

    # Step 1: Go to homepage
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    print("1. Homepage URL:", page.url)

    # Clear lists
    all_requests.clear()
    all_responses.clear()

    # Step 2: Fill search and press Enter
    page.fill("#search-input", "汕尾美食")
    time.sleep(0.3)
    page.keyboard.press("Enter")
    time.sleep(5)
    print("2. After search URL:", page.url)
    print("   Notes:", len(page.query_selector_all("section.note-item")))

    print(f"\n3. Requests made ({len(all_requests)}):")
    for r in all_requests:
        print(f"   {r}")

    print(f"\n4. Responses received ({len(all_responses)}):")
    for r in all_responses:
        print(f"   {r}")

    browser.close()
    print("\nDone")