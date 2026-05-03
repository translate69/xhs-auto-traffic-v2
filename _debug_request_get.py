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

    print("=== Final test: page.request.get for note detail ===")

    # Go to explore and get a note URL
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("1. Note href:", note_href[:80])

    # Use page.request.get (inherits page cookies) to fetch the note URL
    note_url = "https://www.xiaohongshu.com" + note_href
    print(f"\n2. page.request.get: {note_url[:80]}...")
    
    resp = page.request.get(note_url)
    print(f"   Status: {resp.status}")
    print(f"   Final URL: {resp.url}")
    
    if resp.status == 200:
        text = resp.text()
        print(f"   Response length: {len(text)}")
        print(f"   Contains detail-desc: {'detail-desc' in text or 'detail-desc' in text}")
        print(f"   Contains login: {'login' in text.lower() and '登录' in text}")
        print(f"   Preview: {text[:300]}")
    else:
        print(f"   Response: {resp.text()[:200]}")

    # Try the edith API for note detail
    note_id = note_href.split('/explore/')[1].split('?')[0]
    print(f"\n3. Try note detail API: /api/sns/web/v1/note/{note_id}...")
    
    detail_api = f"https://edith.xiaohongshu.com/api/sns/web/v1/note/{note_id}"
    resp2 = page.request.get(detail_api)
    print(f"   Status: {resp2.status}")
    print(f"   URL: {resp2.url}")
    
    if resp2.status == 200:
        data = resp2.json()
        print(f"   Data: {json.dumps(data, ensure_ascii=False)[:300]}")
    else:
        print(f"   Response: {resp2.text()[:200]}")

    # Try page.request.get with the full URL including xsec_source
    print(f"\n4. page.request.get with xsec_source query param...")
    full_note_url = note_url + "&xsec_source=pc_feed"
    resp3 = page.request.get(full_note_url)
    print(f"   Status: {resp3.status}")
    print(f"   Final URL: {resp3.url}")
    if resp3.status == 200:
        text3 = resp3.text()
        print(f"   Length: {len(text3)}")
        print(f"   Preview: {text3[:200]}")

    browser.close()
    print("\nDone")