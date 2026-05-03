import sys
sys.path.insert(0, "E:/translate/claw/xhs-auto-traffic-v2")
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    import json
    cookies = json.load(open(r'E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json'))
    context.add_cookies(cookies)

    page = context.new_page()

    # Monitor ALL navigation requests
    nav_requests = []
    def on_request(req):
        url = req.url
        if "/search" in url or "/explore" in url or "keyword" in url:
            nav_requests.append({"url": url, "method": req.method, "type": req.resource_type})

    page.on("request", on_request)

    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    print("Homepage URL:", page.url)

    # Fill and check network requests
    search_input = page.wait_for_selector("#search-input", timeout=10000)
    search_input.fill("汕尾美食")
    time.sleep(1)

    print("\nRequests after fill:")
    for r in nav_requests[-10:]:
        print(f"  {r['method']}: {r['url'][:100]}")

    nav_requests.clear()

    # Press Enter and capture all requests
    print("\nPressing Enter...")
    page.keyboard.press("Enter")
    time.sleep(3)

    print("\nRequests after Enter:")
    for r in nav_requests:
        print(f"  {r['method']}: {r['url'][:120]}")

    print("\nFinal URL:", page.url)
    notes = page.query_selector_all("section.note-item")
    print("Notes on page:", len(notes))

    browser.close()
    print("Done")