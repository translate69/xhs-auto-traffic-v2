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

    print("=== Test: Use page.route to see actual network requests ===")

    # Capture all requests and responses
    requests = []
    responses = []
    
    def on_request(request):
        url = request.url
        requests.append(f"[{request.method}] {url[:100]}")
    
    def on_response(response):
        url = response.url
        status = response.status
        if status in [302, 303, 307, 308] or 'login' in url.lower():
            responses.append(f"[{status}] {url[:100]}")
    
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

    # Clear recording
    requests.clear()
    responses.clear()

    print("\n2. Click note and capture requests...")
    page.evaluate("""() => {
        document.querySelector('section.note-item a.cover.mask').click();
    }""")
    time.sleep(5)
    print("   URL:", page.url)

    print("\n3. Requests made during click:")
    for r in requests[-20:]:
        print("   ", r)
    
    print("\n4. Redirect/Auth responses:")
    for r in responses:
        print("   ", r)

    # Also check if there are any requests to the note URL itself
    note_requests = [r for r in requests if note_href[:20] in r or '/note/' in r or '/explore/' in r]
    print("\n5. Note-related requests:")
    for r in note_requests:
        print("   ", r)

    browser.close()
    print("\nDone")