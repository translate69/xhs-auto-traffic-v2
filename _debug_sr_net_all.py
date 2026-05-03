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
    page.set_default_timeout(20000)

    # Capture ALL network requests
    requests = []
    responses = []
    
    def handle_request(request):
        url = request.url
        if any(k in url.lower() for k in ['xhs', 'xiaohongshu', 'edith']):
            requests.append({
                'url': url[:100],
                'method': request.method,
                'post_data': request.post_data[:200] if request.post_data else None
            })
    
    def handle_response(response):
        url = response.url
        if any(k in url.lower() for k in ['xhs', 'xiaohongshu', 'edith']):
            try:
                body = response.body()
                preview = body[:300] if len(body) > 300 else body.decode('utf-8', errors='replace')
                responses.append({
                    'url': url[:100],
                    'status': response.status,
                    'body_preview': preview
                })
            except:
                responses.append({
                    'url': url[:100],
                    'status': response.status,
                    'body_preview': 'could not read'
                })
    
    page.on("request", handle_request)
    page.on("response", handle_response)

    # Test: search_result page - what requests does it make?
    print("1. Going to search_result...")
    page.goto("https://www.xiaohongshu.com/search_result?keyword=%E6%B1%95%E5%B0%BE%E7%BE%8E%E9%A3%9F", wait_until="networkidle", timeout=30000)
    time.sleep(3)
    print("   URL:", page.url)
    print("   section.note-item:", len(page.query_selector_all("section.note-item")))
    print("\n   Requests made:", len(requests))
    for r in requests[-10:]:
        print(f"   [{r['method']}] {r['url']}")
    
    print("\n   Responses with data:", len([r for r in responses if 'note' in r['url'].lower() or 'feed' in r['url'].lower()]))
    for r in responses:
        if 'feed' in r['url'].lower() or 'note' in r['url'].lower():
            print(f"   [{r['status']}] {r['url'][:80]}")
            print(f"        body: {r['body_preview'][:150]}")

    requests.clear()
    responses.clear()

    # Test: explore page - what requests does it make?
    print("\n2. Going to explore page...")
    page2 = context.new_page()
    page2.on("request", handle_request)
    page2.on("response", handle_response)
    
    page2.goto("https://www.xiaohongshu.com/explore", wait_until="networkidle", timeout=30000)
    time.sleep(3)
    print("   URL:", page2.url)
    print("   section.note-item:", len(page2.query_selector_all("section.note-item")))
    print("\n   Requests made:", len(requests))
    for r in requests[-10:]:
        print(f"   [{r['method']}] {r['url']}")
    
    print("\n   Responses with note/feed data:")
    for r in responses:
        if 'feed' in r['url'].lower() or 'note' in r['url'].lower():
            print(f"   [{r['status']}] {r['url'][:80]}")
            print(f"        body: {r['body_preview'][:150]}")

    page2.close()
    browser.close()
    print("\nDone")