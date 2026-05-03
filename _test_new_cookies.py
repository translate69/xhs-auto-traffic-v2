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

    print("=== Test: Full flow with new cookies ===")

    # Step 1: Homepage search
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    page.fill("#search-input", "汕尾美食")
    time.sleep(0.3)
    page.keyboard.press("Enter")
    time.sleep(5)

    print(f"1. After search: {page.url}")
    print(f"   Notes: {len(page.query_selector_all('section.note-item'))}")

    # Step 2: Click first note
    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print(f"2. Note href: {note_href[:80]}")

    page.evaluate("""() => {
        document.querySelector('section.note-item a.cover.mask').click();
    }""")
    time.sleep(5)

    print(f"3. After click: {page.url}")

    # Check for content
    has_detail_desc = page.query_selector("#detail-desc") is not None
    print(f"   Has #detail-desc: {has_detail_desc}")

    if has_detail_desc:
        content = page.evaluate("""() => {
            const desc = document.querySelector('#detail-desc');
            const title = document.querySelector('.title-container .title span, h1');
            return {
                desc: desc ? desc.textContent.slice(0, 200) : '',
                title: title ? title.textContent.trim() : ''
            };
        }""")
        print(f"   Content: desc={content['desc'][:80]}, title={content['title'][:50]}")
    else:
        body_text = page.evaluate("document.body.textContent.replace(/\\s+/g, ' ').trim()")
        print(f"   Body text: {body_text[:200]}")

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_new_cookies.png")
    browser.close()
    print("\nDone")