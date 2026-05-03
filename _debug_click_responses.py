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

    # Capture ALL responses
    all_responses = []
    
    def handle_response(response):
        url = response.url
        all_responses.append({
            'url': url[:100],
            'status': response.status,
            'headers': dict(response.headers) if hasattr(response, 'headers') else {}
        })
    
    page.on("response", handle_response)

    # Go to explore
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    print("1. Explore URL:", page.url)
    print("   Responses so far:", len(all_responses))

    # Get note href
    first_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("2. First href:", first_href[:80] if first_href else None)

    # Clear responses
    all_responses.clear()
    
    # Click
    page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        if (link) link.click();
    }""")
    time.sleep(5)
    print("3. After click URL:", page.url)
    print("   New responses:", len(all_responses))
    
    # Print responses with note-related URLs
    print("\n4. Note/feed related responses:")
    for r in all_responses:
        url_lower = r['url'].lower()
        if any(k in url_lower for k in ['note', 'feed', 'explore', 'detail', 'article', 'sns']):
            print(f"   [{r['status']}] {r['url']}")
    
    print("\n5. Login-related responses:")
    for r in all_responses:
        if 'login' in r['url'].lower() or r['status'] in [302, 301, 303, 307, 308]:
            print(f"   [{r['status']}] {r['url']}")

    # Check cookies before and after
    cookies_before = page.context.cookies()
    
    # Check what the page actually has in DOM
    body_html = page.evaluate("document.body.innerHTML.slice(0, 1000)")
    print("\n6. Body HTML preview:", body_html[:500])

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_click_responses.png")
    browser.close()
    print("\nDone")