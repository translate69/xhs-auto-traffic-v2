import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
import time
import json
import re
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    cookies = json.load(open(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json"))
    context.add_cookies(cookies)

    page = context.new_page()
    page.set_default_timeout(15000)

    print("=== Test: Fresh page.goto to note detail ===")

    # First, go to explore to get a note URL
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("1. Got note href:", note_href[:80])

    # Now close that page and open a NEW page
    page.close()

    # Open new page and go directly to note URL
    page2 = context.new_page()
    print("2. New page, going directly to note...")
    full_url = "https://www.xiaohongshu.com" + note_href
    page2.goto(full_url, wait_until="domcontentloaded")
    time.sleep(3)
    print("   URL:", page2.url)
    print("   Title:", page2.title()[:60])

    if "/login" in page2.url:
        print("   -> LOGIN PAGE (expected)")
    else:
        desc = page2.query_selector("#detail-desc")
        print("   Has #detail-desc:", desc is not None)
        if desc:
            text = page2.evaluate("document.querySelector('#detail-desc').textContent || ''")
            print("   Content:", text[:100])

    # But: what if we open a NEW page and click from explore in that context?
    print("\n3. Fresh page in same context, navigate to explore then click...")

    page3 = context.new_page()
    page3.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    note_href3 = page3.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("   Got href:", note_href3[:80])

    # Click using page.click on the element (not JS)
    # First get the element handle
    note_element = page3.query_selector('section.note-item a.cover.mask')
    if note_element:
        # Use page.click on the selector (not JS)
        print("   Clicking using page.click...")
        page3.click('section.note-item a.cover.mask')
        time.sleep(5)
        print("   URL after page.click:", page3.url)
        print("   Title after page.click:", page3.title()[:60])
        
        if "/login" in page3.url:
            print("   -> LOGIN")
        else:
            desc3 = page3.query_selector("#detail-desc")
            print("   Has #detail-desc:", desc3 is not None)
    else:
        print("   No note element found!")

    page3.close()
    page2.close()
    browser.close()
    print("\nDone")