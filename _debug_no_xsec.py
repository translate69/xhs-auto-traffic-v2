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
    page.set_default_timeout(15000)

    # Test: navigate to note WITHOUT xsec_token
    print("1. Test: /explore/69d0e269 (no xsec_token)...")
    page.goto("https://www.xiaohongshu.com/explore/69d0e2690000000023021313", wait_until="domcontentloaded")
    time.sleep(5)
    print("   URL:", page.url)
    print("   Title:", page.title()[:60])

    detail_exists = page.evaluate("() => !!document.querySelector('#detail-desc')")
    print("   Has #detail-desc:", detail_exists)

    # Check if this requires login
    if "/login" in page.url:
        print("   -> Login page!")
    else:
        body = page.text_content("body") or ""
        print("   Body text:", body[:100])

    browser.close()
    print("\nDone")