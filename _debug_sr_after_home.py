import sys
sys.path.insert(0, "E:/translate/claw/xhs-auto-traffic-v2")
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    import json
    with open("E:/translate/claw/xhs-auto-traffic-v2\xhs_cookies.json", encoding="utf-8") as f:
        cookies = json.load(f)

    print(f"Loaded {len(cookies)} cookies")
    for c in cookies:
        print(f"  {c['name']}: domain={c.get('domain','?')} path={c.get('path','?')} secure={c.get('secure','?')}")

    context.add_cookies(cookies)

    page = context.new_page()

    # Step 1: Go to homepage/explore to establish session
    print("\n1. Go to homepage...")
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    print(f"   URL: {page.url}")

    # Check login state
    login_els = page.query_selector_all("[class*='login'], .login-btn, [href*='login']")
    print(f"   Login elements: {len(login_els)}")

    # Step 2: Now go to search_result
    print("\n2. Now goto search_result...")
    page.goto("https://www.xiaohongshu.com/search_result?keyword=汕尾美食&type=51", wait_until="domcontentloaded")
    time.sleep(5)
    print(f"   URL: {page.url}")
    print(f"   Title: {page.title()[:80]}")

    # Check what's on the page
    body_text = page.text_content("body") or ""
    print(f"   Body preview: {body_text[:200]}")

    notes = page.query_selector_all("section.note-item")
    print(f"   section.note-item count: {len(notes)}")
    filter_el = page.query_selector(".filter")
    print(f"   .filter: {filter_el is not None}")

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_sr_after_home.png")

    browser.close()
    print("\nDone")