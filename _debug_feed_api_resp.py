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
    page.set_default_timeout(20000)

    # Capture all feed-related API responses
    feed_responses = []
    
    def on_response(response):
        url = response.url
        if any(k in url for k in ['feed', 'explore', 'recommend', 'subscribe']):
            try:
                body = response.body()
                if b'"items"' in body or b'"notes"' in body or b'"note"' in body:
                    feed_responses.append({
                        'url': url.replace('https://edith.xiaohongshu.com', ''),
                        'status': response.status,
                        'body_len': len(body),
                        'has_items': b'"items"' in body,
                        'body_preview': body[:200].decode('utf-8', errors='replace')
                    })
            except:
                pass

    page.on("response", on_response)

    # Go to explore
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(5)  # Wait for API calls to complete
    print("1. URL:", page.url)
    print("   Notes:", len(page.query_selector_all("section.note-item")))

    print(f"\n2. Feed API responses captured: {len(feed_responses)}")
    for r in feed_responses:
        print(f"\n   [{r['status']}] {r['url']}")
        print(f"        body_len={r['body_len']}, has_items={r['has_items']}")
        print(f"        preview: {r['body_preview'][:150]}")

    # Now check the DOM note items
    notes_check = page.evaluate("""() => {
        const notes = document.querySelectorAll('section.note-item');
        return {
            count: notes.length,
            firstTitle: notes[0] ? notes[0].querySelector('.title span')?.textContent?.trim() : '',
            firstHref: notes[0] ? notes[0].querySelector('a.cover.mask')?.getAttribute('href')?.slice(0, 80) : ''
        };
    }""")
    print(f"\n3. DOM notes: {notes_check}")

    browser.close()
    print("\nDone")