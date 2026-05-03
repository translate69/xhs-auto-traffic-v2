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

    # Go to explore first
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    # Get note href
    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : '';
    }""")
    print("1. Note href:", note_href[:80])

    # Try page.request.get (should use same as context cookies)
    note_url = "https://www.xiaohongshu.com" + note_href
    print(f"\n2. page.request.get: {note_url[:80]}...")
    resp = page.request.get(note_url)
    print(f"   Status: {resp.status}")
    print(f"   Final URL: {resp.url}")

    body = resp.body()
    body_str = body.decode('utf-8', errors='replace')
    print(f"   Body length: {len(body_str)}")
    print(f"   Has 'note' or 'detail': {'note' in body_str.lower() and 'detail' in body_str.lower()}")
    print(f"   Has login text: {'login' in body_str or '登录' in body_str}")

    # Check what we got
    if 'login' in body_str.lower() or '登录查看' in body_str:
        print("   -> Login content")
    elif 'detail-desc' in body_str or 'note-content' in body_str:
        print("   -> Note content!")
    else:
        print("   -> Other content")
        print("   Preview:", body_str[:300])

    # Now try clicking the note and THEN using page.request.get
    print("\n3. Click note and try page.request.get...")
    page.evaluate("""() => {
        document.querySelector('section.note-item a.cover.mask').click();
    }""")
    time.sleep(5)
    print("   Clicked URL:", page.url)

    # Now try page.request.get to the same URL
    resp2 = page.request.get(page.url)
    print(f"   Status: {resp2.status}")
    body2 = resp2.body()
    body2_str = body2.decode('utf-8', errors='replace')
    print(f"   Body length: {len(body2_str)}")
    print(f"   Has detail-desc: {'detail-desc' in body2_str}")
    print(f"   Has login: {'login' in body2_str.lower()}")

    browser.close()
    print("\nDone")