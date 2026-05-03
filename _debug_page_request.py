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

    print("=== Testing page.request for note API ===")

    # Go to explore page first
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    # Get first note info
    first_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("1. First note href:", first_href[:80])

    # Try page.request.get for the note URL
    note_url = "https://www.xiaohongshu.com" + first_href
    print(f"\n2. page.request.get: {note_url[:80]}...")
    resp = page.request.get(note_url)
    print(f"   Status: {resp.status}")
    print(f"   Final URL: {resp.url}")

    if resp.status == 200:
        try:
            data = resp.json()
            print(f"   JSON response: {str(data)[:200]}")
        except:
            text = resp.text()
            print(f"   Text: {text[:200]}")
    else:
        print(f"   Response: {resp.text()[:100]}")

    # Try with a different API format
    note_id = first_href.split('/explore/')[1].split('?')[0]
    api_url = f"https://edith.xiaohongshu.com/api/sns/web/v1/note/{note_id}"
    print(f"\n3. Try note detail API: {api_url}...")
    
    resp2 = page.request.get(api_url)
    print(f"   Status: {resp2.status}")
    print(f"   URL: {resp2.url}")
    if resp2.status == 200:
        try:
            data2 = resp2.json()
            print(f"   JSON: {str(data2)[:300]}")
        except:
            print(f"   Text: {resp2.text()[:200]}")
    else:
        print(f"   Response: {resp2.text()[:100]}")

    browser.close()
    print("\nDone")