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

    print("1. Go to explore page...")
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    print("   URL:", page.url)
    notes_count = len(page.query_selector_all("section.note-item"))
    print("   Notes:", notes_count)

    # Get first note href
    first_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("   First href:", first_href[:80] if first_href else None)

    if first_href:
        # Use JavaScript click (bypasses playwright's click interception check)
        print("\n2. Click via JS evaluate...")
        page.evaluate("""() => {
            const link = document.querySelector('section.note-item a.cover.mask');
            if (link) link.click();
        }""")
        time.sleep(5)

        print("   URL after JS click:", page.url)
        print("   Title:", page.title()[:60])

        if "/login" in page.url:
            print("   -> LOGIN PAGE!")
        elif "/404" in page.url:
            print("   -> 404 PAGE!")
        else:
            detail = page.query_selector("#detail-desc")
            print("   #detail-desc:", detail is not None)
            
            if detail:
                content = page.evaluate("document.querySelector('#detail-desc').textContent || ''")
                print("   Content (first 100):", content[:100])

        page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_js_click.png")

    browser.close()
    print("\nDone")