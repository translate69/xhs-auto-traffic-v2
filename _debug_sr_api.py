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

    # Capture all API responses
    api_data = []
    
    def handle_response(response):
        url = response.url
        if any(k in url for k in ['feed', 'note', 'explore', 'search']):
            try:
                body = response.body()
                if b'"items"' in body or b'"notes"' in body or b'"id"' in body:
                    api_data.append({
                        'url': url[:100],
                        'status': response.status,
                        'body_preview': body[:200]
                    })
            except:
                pass
    
    page.on("response", handle_response)

    # Test 1: Go to search_result directly
    print("1. Direct to search_result...")
    page.goto("https://www.xiaohongshu.com/search_result?keyword=%E6%B1%95%E5%B0%BE%E7%BE%8E%E9%A3%9F", wait_until="domcontentloaded")
    time.sleep(5)
    print("   URL:", page.url)
    print("   section.note-item:", len(page.query_selector_all("section.note-item")))
    print("   API calls captured:", len(api_data))
    
    # Test 2: From explore page, go to search_result
    print("\n2. From explore page to search_result...")
    page2 = context.new_page()
    page2.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    
    api_data2 = []
    def handle_response2(response):
        url = response.url
        if any(k in url for k in ['feed', 'note', 'search']):
            try:
                body = response.body()
                if b'"items"' in body or b'"notes"' in body:
                    api_data2.append({
                        'url': url[:100],
                        'status': response.status
                    })
            except:
                pass
    page2.on("response", handle_response2)
    
    page2.goto("https://www.xiaohongshu.com/search_result?keyword=%E6%B1%95%E5%B0%BE%E7%BE%8E%E9%A3%9F", wait_until="domcontentloaded")
    time.sleep(5)
    print("   URL:", page2.url)
    print("   section.note-item:", len(page2.query_selector_all("section.note-item")))
    print("   API calls captured:", len(api_data2))
    for d in api_data2:
        print("   ", d)

    page2.close()
    browser.close()
    print("\nDone")