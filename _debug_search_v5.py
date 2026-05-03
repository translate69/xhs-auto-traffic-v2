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
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    print("URL:", page.url)

    search_input = page.wait_for_selector("#search-input", timeout=10000)
    search_input.fill("汕尾美食")
    time.sleep(1)

    # Try clicking sug-item with force (bypass intercepts)
    first_sug = page.query_selector(".sug-item")
    if first_sug:
        print("Clicking sug-item with force...")
        first_sug.click(force=True, timeout=5000)
        time.sleep(5)
        print("URL:", page.url)
        notes = page.query_selector_all("section.note-item")
        print("Notes:", len(notes))
        filter_el = page.query_selector(".filter")
        print("Has filter:", filter_el is not None)
    else:
        print("No sug-item found!")

    browser.close()
    print("Done")