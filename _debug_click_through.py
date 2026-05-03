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

    # Test: can we use page.request to access note detail?
    # page.request inherits cookies and might handle xsec_token differently
    print("1. Test page.request for note detail...")
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    # Get first note info
    note_info = page.evaluate("""() => {
        const note = document.querySelector('section.note-item a.cover.mask');
        if (!note) return null;
        return {
            href: note.getAttribute('href'),
            title: note.closest('.note-item')?.querySelector('.title span')?.textContent || ''
        };
    }""")
    print(f"   Note info: {note_info}")

    if note_info:
        # Try page.request to access the note
        full_url = f"https://www.xiaohongshu.com{note_info['href']}"
        print(f"\n2. page.request.get for: {full_url[:80]}...")
        resp = page.request.get(full_url)
        print(f"   Status: {resp.status}")
        print(f"   URL: {resp.url}")
        if resp.status == 200:
            try:
                data = resp.json()
                print(f"   JSON: {str(data)[:200]}")
            except:
                text = resp.text()
                print(f"   Text: {text[:200]}")
        else:
            print(f"   Response: {resp.text()[:100]}")

    # Check if explore page has any note detail links that work
    print("\n3. Click-through from explore...")
    page2 = context.new_page()
    page2.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    # Check what the note item looks like when loaded
    note_html = page2.evaluate("""() => {
        const note = document.querySelector('section.note-item');
        return note ? note.outerHTML.slice(0, 500) : 'not found';
    }""")
    print(f"   Note HTML: {note_html}")

    # Get the note link
    note_link = page2.query_selector("section.note-item a.cover.mask")
    if note_link:
        href = note_link.get_attribute('href')
        title = note_link.get_attribute('title') or ''
        print(f"\n   Note link href: {href[:80]}")
        print(f"   Note link title: {title[:40]}")

        # Click it
        page2.click("section.note-item a.cover.mask")
        time.sleep(5)
        print(f"   After click URL: {page2.url}")
        print(f"   Title: {page2.title()[:60]}")

        # Check if detail-desc is present
        detail_desc = page2.query_selector("#detail-desc")
        print(f"   #detail-desc: {detail_desc}")

        # If detail-desc exists, get the content
        if detail_desc:
            content = page2.evaluate("document.querySelector('#detail-desc').textContent")
            print(f"   Content: {content[:100]}")

    page2.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_click_note.png")
    browser.close()
    print("\nDone")