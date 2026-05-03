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

    print("=== Capture ALL API responses during note click ===")

    all_responses = []
    
    def on_response(response):
        url = response.url
        status = response.status
        try:
            body = response.body()
            all_responses.append({
                'url': url,
                'status': status,
                'body_len': len(body),
                'body_preview': body[:100]
            })
        except:
            all_responses.append({
                'url': url,
                'status': status,
                'body_len': 0,
                'body_preview': 'could not read'
            })
    
    page.on("response", on_response)

    # Go to explore
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("1. Note href:", note_href[:80])

    # Clear responses
    all_responses.clear()

    # Click note
    page.evaluate("""() => {
        document.querySelector('section.note-item a.cover.mask').click();
    }""")
    time.sleep(5)
    print("2. URL:", page.url)

    # Show all API responses
    print(f"\n3. All API responses ({len(all_responses)}):")
    for r in all_responses:
        url_short = r['url'].replace('https://edith.xiaohongshu.com', '').replace('https://www.xiaohongshu.com', '')
        print(f"   [{r['status']}] {url_short[:80]}")
        if r['body_preview'] and r['body_preview'] != 'could not read':
            print(f"        {r['body_preview'][:80]}")

    # Now check: which responses are related to note detail data?
    note_apis = [r for r in all_responses if any(k in r['url'] for k in ['note', 'detail', 'feed', 'article', 'explore'])]
    print(f"\n4. Note-related APIs ({len(note_apis)}):")
    for r in note_apis:
        url_short = r['url'].replace('https://edith.xiaohongshu.com', '').replace('https://www.xiaohongshu.com', '')
        print(f"   [{r['status']}] {url_short[:80]}")
        print(f"        body_len={r['body_len']}, preview={r['body_preview'][:60]}")

    browser.close()
    print("\nDone")