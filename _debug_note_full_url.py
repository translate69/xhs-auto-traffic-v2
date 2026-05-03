import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
import time
import json
from playwright.sync_api import sync_playwright

result_data = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    cookies = json.load(open(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json"))
    context.add_cookies(cookies)

    page = context.new_page()
    page.set_default_timeout(20000)

    # Test: From explore, click note with full absolute URL
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    print("Explore URL:", page.url)

    # Get note href and construct full URL
    note_info = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        const href = link ? link.getAttribute('href') : null;
        return {
            href: href,
            fullUrl: href ? 'https://www.xiaohongshu.com' + href : null
        };
    }""")
    print("Note href:", note_info['href'][:80] if note_info['href'] else None)
    print("Full URL:", note_info['fullUrl'][:80] if note_info['fullUrl'] else None)

    if note_info['fullUrl']:
        # Navigate using full URL (like _go_to_detail does)
        print("\nNavigating to note detail:...")
        page.goto(note_info['fullUrl'], wait_until="domcontentloaded")
        time.sleep(5)
        print("URL:", page.url)
        print("Title:", page.title()[:60])

        # Check for note content
        detail_found = page.evaluate("""() => {
            const desc = document.querySelector('#detail-desc');
            return {
                hasDetailDesc: !!desc,
                detailText: desc ? desc.textContent.slice(0, 100) : null,
                bodyText: document.body.textContent.slice(0, 200)
            };
        }""")
        print("Detail check:", detail_found)

        if "/login" in page.url:
            print("RESULT: LOGIN PAGE")
        elif "/404" in page.url:
            print("RESULT: 404 PAGE")
        else:
            print("RESULT: NOTE PAGE - content available!")

    browser.close()
    print("\nDone")