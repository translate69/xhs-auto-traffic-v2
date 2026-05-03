import sys
sys.path.insert(0, "E:/translate/claw/xhs-auto-traffic-v2")
import time
from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    with open("E:/translate/claw/xhs-auto-traffic-v2/xhs_cookies.json", encoding="utf-8") as f:
        cookies = json.load(f)
    context.add_cookies(cookies)

    page = context.new_page()

    # Monitor network requests
    requests = []
    page.on("request", lambda r: requests.append({"url": r.url, "type": r.resource_type}) if "/search" in r.url or "/explore" in r.url else None)

    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)

    print(f"Homepage URL: {page.url}")

    # Find the real search input (not HP injected one)
    # The real XHS input has data-v-57548470 attribute
    search_input = page.query_selector("#search-input")
    print(f"Found #search-input: {search_input is not None}")
    if search_input:
        rect = search_input.bounding_box()
        print(f"Rect: {rect}")

    # Fill it
    search_input.fill("汕尾去哪吃")
    print("Filled search input")
    time.sleep(0.5)

    # Check what happens on enter
    search_input.press("Enter")
    print("Pressed Enter")
    time.sleep(2)
    print(f"URL after Enter: {page.url}")

    # Also check network requests
    print(f"\nNetwork requests captured: {len(requests)}")
    for r in requests[:10]:
        print(f"  {r['type']}: {r['url'][:100]}")

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/screenshot_after_search.png")
    print("Screenshot saved")
    page.wait_for_timeout(5000)
    print(f"Final URL: {page.url}")
    browser.close()