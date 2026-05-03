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

    # Add init script like run_batch.py does
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false, configurable: true
        });
    """)

    print("=== Test: Cookie loading + detail page ===")

    # Go to explore
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    # Get note href
    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : '';
    }""")
    print(f"Note href: {note_href[:80]}")

    # Go to detail page
    detail_url = "https://www.xiaohongshu.com" + note_href
    page.goto(detail_url, wait_until="domcontentloaded")
    time.sleep(5)
    print(f"Detail URL: {page.url}")
    print(f"Title: {page.title()[:60]}")

    # Check for content
    has_detail = page.query_selector("#detail-desc") is not None
    print(f"Has #detail-desc: {has_detail}")

    if has_detail:
        # Get content
        content = page.evaluate("""() => {
            const desc = document.querySelector('#detail-desc');
            return desc ? desc.textContent.slice(0, 200) : '';
        }""")
        print(f"Content: {content[:100]}")

    # Now test with SearchCollector flow
    print("\n=== Test with SearchCollector flow ===")
    page2 = context.new_page()
    from core.search_collector import SearchCollector
    
    class FakeBrowserManager:
        browser = browser
    
    sc = SearchCollector(FakeBrowserManager(), context)
    feeds = sc.collect("汕尾美食", limit=3)
    print(f"Collected {len(feeds)} feeds")
    
    if feeds:
        print(f"First feed: {feeds[0].url[:60]}, author={feeds[0].author}")

    browser.close()
    print("\nDone")