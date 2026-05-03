import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
import time
from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    cookies = json.load(open(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json"))
    context.add_cookies(cookies)

    page = context.new_page()

    # Capture ALL requests to find search/feed API endpoints
    api_calls = []

    def on_response(resp):
        url = resp.url
        if any(x in url for x in ['api/', '/feed', '/search', '/note', '/explore']):
            api_calls.append({
                'url': url[:120],
                'status': resp.status,
                'type': resp.request.resource_type
            })

    page.on("response", on_response)

    print("1. Go to explore page and capture API calls...")
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(5)
    print(f"   URL: {page.url}")
    print(f"   Notes: {len(page.query_selector_all('section.note-item'))}")

    print(f"\n   API calls captured: {len(api_calls)}")
    for call in api_calls[:20]:
        print(f"     [{call['status']}] {call['type']}: {call['url']}")

    # Now try search_result and capture API calls
    print("\n2. Go to search_result and capture API calls...")
    api_calls.clear()
    page2 = context.new_page()
    page2.on("response", on_response)
    page2.goto("https://www.xiaohongshu.com/search_result?keyword=汕尾美食&type=51", wait_until="domcontentloaded")
    time.sleep(5)
    print(f"   URL: {page2.url}")
    print(f"   Notes: {len(page2.query_selector_all('section.note-item'))}")

    print(f"\n   API calls captured: {len(api_calls)}")
    for call in api_calls[:20]:
        print(f"     [{call['status']}] {call['type']}: {call['url']}")

    browser.close()
    print("\nDone")