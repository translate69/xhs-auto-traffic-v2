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

    # Step 1: Go to explore page (already logged in)
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    print("1. Explore page URL:", page.url)
    print("   Notes:", len(page.query_selector_all("section.note-item")))

    # Step 2: Click on the first note
    print("\n2. Clicking first note...")
    first_note = page.query_selector("section.note-item")
    if first_note:
        # Find the link within the note
        note_link = first_note.query_selector("a.cover.mask")
        if note_link:
            href = note_link.get_attribute('href')
            title = note_link.get_attribute('title') or ''
            print(f"   href: {href[:80]}")
            print(f"   title: {title[:40]}")

            # Use page.click to navigate (instead of page.goto)
            # This should preserve the session context
            note_link.click()
            time.sleep(5)

            print(f"   URL after click: {page.url}")
            print(f"   Title: {page.title()[:60]}")

            # Check if note loaded
            detail_desc = page.query_selector("#detail-desc")
            print(f"   #detail-desc found: {detail_desc is not None}")

            if detail_desc:
                content = page.evaluate("document.querySelector('#detail-desc').textContent || ''")
                print(f"   Content (first 100): {content[:100]}")

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_click_note.png")
    browser.close()
    print("\nDone")