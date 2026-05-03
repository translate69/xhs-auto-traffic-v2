import sys
sys.path.insert(0, "E:/translate/claw/xhs-auto-traffic-v2")
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    import json
    with open("E:/translate/claw/xhs-auto-traffic-v2/xhs_cookies.json", encoding="utf-8") as f:
        cookies = json.load(f)
    context.add_cookies(cookies)

    page = context.new_page()

    # Test: Does search_result URL show captcha even with valid cookies?
    print("1. Testing direct search_result access with cookies...")
    page.goto("https://www.xiaohongshu.com/search_result?keyword=汕尾美食&type=51", wait_until="domcontentloaded")
    time.sleep(3)
    print(f"   URL: {page.url}")
    print(f"   Title: {page.title()[:50]}")

    # Check for captcha
    if "captcha" in page.url or "website-login" in page.url:
        print("   -> Captcha detected!")
    else:
        notes = page.query_selector_all("section.note-item")
        print(f"   -> section.note-item count: {len(notes)}")
        filter_el = page.query_selector(".filter")
        print(f"   -> .filter element: {filter_el is not None}")

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_sr_attempt1.png")

    # Now try going to homepage first then to search_result
    print("\n2. Testing: Homepage first, then search_result...")
    page2 = context.new_page()
    page2.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(2)
    print(f"   Homepage URL: {page2.url}")

    # Now go to search_result
    page2.goto("https://www.xiaohongshu.com/search_result?keyword=汕尾美食&type=51", wait_until="domcontentloaded")
    time.sleep(3)
    print(f"   search_result URL: {page2.url}")
    if "captcha" in page2.url or "website-login" in page2.url:
        print("   -> Captcha detected!")
    else:
        notes2 = page2.query_selector_all("section.note-item")
        print(f"   -> section.note-item count: {len(notes2)}")
        filter_el2 = page2.query_selector(".filter")
        print(f"   -> .filter element: {filter_el2 is not None}")

    page2.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_sr_attempt2.png")

    # Try a 3rd approach: use search API or smarter navigation
    print("\n3. Testing: Search via URL with longer wait...")
    page3 = context.new_page()
    page3.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(2)

    # Try navigating to search_result with networkidle
    page3.goto("https://www.xiaohongshu.com/search_result?keyword=汕尾美食&type=51", wait_until="networkidle", timeout=30000)
    time.sleep(2)
    print(f"   URL: {page3.url}")
    if "captcha" in page3.url or "website-login" in page3.url:
        print("   -> Captcha!")
    else:
        notes3 = page3.query_selector_all("section.note-item")
        print(f"   -> section.note-item count: {len(notes3)}")
        filter_el3 = page3.query_selector(".filter")
        print(f"   -> .filter: {filter_el3 is not None}")
    page3.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_sr_attempt3.png")

    browser.close()
    print("\nDone")