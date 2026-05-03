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
    page.set_default_timeout(10000)  # 10s timeout for everything

    # Go to explore page first
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    print("URL:", page.url)

    # Get the first note's href
    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("First note href:", note_href[:80] if note_href else None)

    if note_href:
        # Navigate to the note via goto (not click)
        note_url = "https://www.xiaohongshu.com" + note_href
        print("\nNavigating to note via goto:", note_url[:80])
        
        page.goto(note_url, wait_until="domcontentloaded", timeout=15000)
        time.sleep(3)
        
        print("URL after goto:", page.url)
        print("Title:", page.title()[:60])
        
        # Quick check for detail-desc without waiting
        detail_exists = page.evaluate("""() => !!document.querySelector('#detail-desc')""")
        print("Has #detail-desc:", detail_exists)
        
        # Check page body text
        body_text = page.text_content("body") or ""
        print("Body text (first 150):", body_text[:150])
        
        # If we're on a note page, get the content
        if "/note/" in page.url or "/explore/" in page.url:
            # Try to extract note content via JS
            content = page.evaluate("""() => {
                const desc = document.querySelector('#detail-desc');
                const title = document.querySelector('.title-container .title span') || document.querySelector('h1');
                return {
                    detail_desc: desc ? desc.textContent.slice(0, 100) : 'not found',
                    title: title ? title.textContent.slice(0, 50) : 'not found'
                };
            }""")
            print("Note content:", content)

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_goto_note.png")
    browser.close()
    print("\nDone")