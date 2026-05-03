import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
import time
import json
from playwright.sync_api import sync_playwright

result = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    cookies = json.load(open(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json"))
    context.add_cookies(cookies)

    page = context.new_page()
    page.set_default_timeout(20000)

    # Go to explore
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    # Check if search_result has notes if we go through homepage first
    print("1. Homepage search to /explore...")
    page.fill("#search-input", "汕尾美食")
    time.sleep(0.3)
    page.keyboard.press("Enter")
    time.sleep(5)
    print("   URL:", page.url)
    print("   Notes:", len(page.query_selector_all("section.note-item")))

    # Now manually navigate to search_result
    print("\n2. Navigate to search_result...")
    page2 = context.new_page()
    page2.goto("https://www.xiaohongshu.com/search_result?keyword=%E6%B1%95%E5%B0%BE%E7%BE%8E%E9%A3%9F", wait_until="domcontentloaded")
    time.sleep(3)
    print("   URL:", page2.url)
    print("   Notes:", len(page2.query_selector_all("section.note-item")))
    
    # Get note content
    note_info = page2.evaluate("""() => {
        const notes = document.querySelectorAll('section.note-item');
        if (!notes.length) return 'no notes';
        
        const note = notes[0];
        const link = note.querySelector('a.cover.mask');
        const title = note.querySelector('.title span');
        const name = note.querySelector('.name');
        const time = note.querySelector('.time');
        
        return {
            noteCount: notes.length,
            firstTitle: title ? title.textContent.trim().slice(0, 50) : '',
            firstAuthor: name ? name.textContent.trim() : '',
            firstTime: time ? time.textContent.trim() : '',
            firstHref: link ? link.getAttribute('href') : ''
        };
    }""")
    print("   Note info:", json.dumps(note_info, ensure_ascii=False))
    
    page2.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_search_result.png")
    page2.close()

    # Check if the search_result page has notes when coming from an existing page context
    print("\n3. From explore page, navigate via JS to search_result...")
    page.evaluate("""() => {
        // Try using history API or location to trigger search_result
        window.location.href = 'https://www.xiaohongshu.com/search_result?keyword=汕尾美食';
    }""")
    time.sleep(5)
    print("   URL:", page.url)
    print("   Notes:", len(page.query_selector_all("section.note-item")))

    browser.close()
    print("\nDone")