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

    print("=== Test: Use SAME page for entire flow (no page.close between steps) ===")

    # Step 1: Go to Xiaohongshu homepage and look at the current cookies
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    print("1. Homepage URL:", page.url)

    # Get all cookies BEFORE searching
    ctx_cookies_before = page.context.cookies()
    ws_before = [c for c in ctx_cookies_before if c['name'] == 'web_session']
    print("   web_session (before):", ws_before[0]['value'][:40] if ws_before else "NOT FOUND")
    print("   Total cookies:", len(ctx_cookies_before))

    # Step 2: Fill search and click
    page.fill("#search-input", "汕尾美食")
    time.sleep(0.3)
    page.keyboard.press("Enter")
    time.sleep(5)
    print("\n2. After search URL:", page.url)

    # Check cookies AFTER search navigation
    ctx_cookies_after = page.context.cookies()
    ws_after = [c for c in ctx_cookies_after if c['name'] == 'web_session']
    print("   web_session (after):", ws_after[0]['value'][:40] if ws_after else "NOT FOUND")
    print("   Total cookies:", len(ctx_cookies_after))
    print("   Same session:", ws_before[0]['value'] == ws_after[0]['value'] if ws_before and ws_after else False)

    # Check note count
    notes = page.query_selector_all("section.note-item")
    print("   Notes:", len(notes))

    # Step 3: Get note href
    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("\n3. Note href:", note_href[:80])

    # Step 4: Click note - use page.locator and click with force
    print("\n4. Clicking note via locator...")
    
    # Use locator to click (more reliable than JS for Playwright)
    locator = page.locator("section.note-item a.cover.mask").first
    locator.click(force=True, timeout=10000)
    
    time.sleep(5)
    print("   URL after click:", page.url)
    print("   Title:", page.title()[:60])

    # Check if we're on a note page or login
    if "/login" in page.url:
        print("   -> LOGIN PAGE")
    elif "/explore/" in page.url:
        print("   -> EXPLORE NOTE PAGE")
        # Check for note content
        desc = page.query_selector("#detail-desc")
        print("   Has #detail-desc:", desc is not None)
    else:
        print("   -> OTHER PAGE")

    # Check cookies again
    ctx_cookies_final = page.context.cookies()
    ws_final = [c for c in ctx_cookies_final if c['name'] == 'web_session']
    print("\n5. web_session (final):", ws_final[0]['value'][:40] if ws_final else "NOT FOUND")

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_same_page.png")
    browser.close()
    print("\nDone")