import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    import json
    cookies = json.load(open(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json"))
    context.add_cookies(cookies)

    page = context.new_page()

    # Test note detail page on /explore/ URL
    note_url = "https://www.xiaohongshu.com/explore/69d0e2690000000023021313"
    print(f"1. Going to: {note_url}")
    page.goto(note_url, wait_until="domcontentloaded")
    time.sleep(5)
    print(f"   URL: {page.url}")

    detail_desc = page.query_selector("#detail-desc")
    print(f"   #detail-desc: {detail_desc}")

    body_text = page.text_content("body") or ""
    print(f"   Body text (first 200): {body_text[:200]}")

    note_content = page.evaluate("""() => {
        const el = document.querySelector('#detail-desc');
        if (!el) return 'NOT FOUND';
        return el.textContent || '';
    }""")
    print(f"   detail-desc text: {note_content[:100]}")

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_note_detail.png")

    print("\n2. Retrying with networkidle...")
    page2 = context.new_page()
    page2.goto(note_url, wait_until="networkidle", timeout=30000)
    time.sleep(3)
    print(f"   URL: {page2.url}")
    detail_desc2 = page2.query_selector("#detail-desc")
    print(f"   #detail-desc: {detail_desc2}")
    page2.close()

    browser.close()
    print("\nDone")