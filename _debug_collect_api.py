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

    print("=== Test: Capture ALL requests during note click, especially collect ===")

    # Capture all requests with their post data
    all_requests = []
    
    def on_request(request):
        url = request.url
        method = request.method
        post_data = request.post_data
        
        all_requests.append({
            'method': method,
            'url': url,
            'post_data': post_data
        })
    
    def on_response(response):
        url = response.url
        status = response.status
        
        # Only care about collect or auth-related
        if 'collect' in url or 'auth' in url or 'login' in url.lower():
            print(f"   [{status}] {url[:80]}")
    
    page.on("request", on_request)
    page.on("response", on_response)

    # Go to explore
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("1. Note href:", note_href[:80])

    all_requests.clear()
    print("\n2. Click note...")
    page.evaluate("""() => {
        document.querySelector('section.note-item a.cover.mask').click();
    }""")
    time.sleep(5)
    print("   URL:", page.url)

    # Show the collect requests
    collect_requests = [r for r in all_requests if 'collect' in r['url']]
    print(f"\n3. collect requests: {len(collect_requests)}")
    for r in collect_requests:
        print(f"   [{r['method']}] {r['url']}")
        print(f"      post_data: {r['post_data']}")

    # Also check the collect response
    def on_collect_response(response):
        if 'collect' in response.url:
            try:
                body = response.body()
                print(f"\n4. collect response: {response.status}")
                print(f"   body: {body[:200]}")
            except:
                pass
    
    page.on("response", on_collect_response)

    # Now do the click again in a new page to capture collect response
    page2 = context.new_page()
    page2.on("response", on_collect_response)
    page2.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    
    note_href2 = page2.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    
    print("\n5. Click on page2...")
    page2.evaluate("""() => {
        document.querySelector('section.note-item a.cover.mask').click();
    }""")
    time.sleep(5)
    print("   URL:", page2.url)

    page2.close()
    browser.close()
    print("\nDone")