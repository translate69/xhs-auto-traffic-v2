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

    # Test /explore/ format with valid recent note
    print("1. Test with a note ID from recent logs (69d0e269)...")
    url = "https://www.xiaohongshu.com/explore/69d0e2690000000023021313"
    page.goto(url, wait_until="domcontentloaded")
    time.sleep(5)
    print(f"   URL: {page.url}")
    print(f"   Title: {page.title()[:60]}")

    # Check for note content
    note_content = page.evaluate("""() => {
        const el = document.querySelector('#detail-desc');
        return el ? 'found: ' + el.textContent.slice(0,50) : 'NOT FOUND';
    }""")
    print(f"   detail-desc: {note_content}")

    # Check the 404 error details
    if "/404" in page.url:
        error_info = page.evaluate("""() => {
            const url = window.location.href;
            const params = new URLSearchParams(url.split('?')[1] || '');
            return {
                error_code: params.get('error_code'),
                error_msg: params.get('error_msg'),
                source: params.get('source')
            };
        }""")
        print(f"   404 error info: {error_info}")

    # Check cookies on this page
    print("\n2. Checking cookies for note page...")
    note_cookies = page.context.cookies()
    print(f"   Total cookies: {len(note_cookies)}")
    for c in note_cookies:
        if c['name'] in ['web_session', 'access-token', 'a1']:
            print(f"   {c['name']}={c['value'][:30]}...")

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_note_404.png")

    # Test: what if we go to explore page first, then click a note?
    print("\n3. Test navigating from explore to note...")
    page2 = context.new_page()
    page2.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    # Click the first note link
    first_note_link = page2.query_selector("section.note-item a.cover.mask")
    if first_note_link:
        href = first_note_link.get_attribute('href')
        print(f"   First note href: {href}")
        page2.goto(f"https://www.xiaohongshu.com{href}", wait_until="domcontentloaded")
        time.sleep(5)
        print(f"   After click URL: {page2.url}")
        print(f"   Title: {page2.title()[:60]}")
    else:
        print("   No note link found")

    browser.close()
    print("\nDone")