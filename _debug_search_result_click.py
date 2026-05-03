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

    # Step 1: Go to search_result directly 
    print("1. Go to search_result page...")
    page.goto("https://www.xiaohongshu.com/search_result?keyword=%E6%B1%95%E5%B0%BE%E7%BE%8E%E9%A3%9F", wait_until="domcontentloaded")
    time.sleep(3)
    print("   URL:", page.url)
    print("   Notes:", len(page.query_selector_all("section.note-item")))
    
    # Get first note's URL from search_result
    first_note_info = page.evaluate("""() => {
        const note = document.querySelector('section.note-item');
        if (!note) return null;
        const link = note.querySelector('a.cover.mask');
        return {
            href: link ? link.getAttribute('href') : null,
            title: note.querySelector('.title span') ? note.querySelector('.title span').textContent.trim() : ''
        };
    }""")
    print("   First note:", json.dumps(first_note_info, ensure_ascii=False))

    if first_note_info and first_note_info['href']:
        print("\n2. Click first note from search_result...")
        
        # Click via JS
        page.evaluate("""() => {
            const note = document.querySelector('section.note-item');
            const link = note ? note.querySelector('a.cover.mask') : null;
            if (link) link.click();
        }""")
        time.sleep(5)
        
        print("   URL after click:", page.url)
        print("   Title:", page.title()[:60])
        
        if "/note/" in page.url:
            print("   -> ON NOTE PAGE (/note/)!")
            # Get note content
            desc = page.query_selector("#detail-desc")
            print("   #detail-desc:", desc is not None)
        elif "/explore/" in page.url:
            print("   -> ON EXPLORE PAGE (/explore/)!")
            desc = page.query_selector("#detail-desc")
            print("   #detail-desc:", desc is not None)
        elif "/login" in page.url:
            print("   -> LOGIN PAGE!")
        else:
            print("   -> OTHER PAGE!")

    # Step 3: Compare - from explore page, click note
    print("\n3. Now from explore page...")
    page2 = context.new_page()
    page2.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    
    explore_note = page2.evaluate("""() => {
        const note = document.querySelector('section.note-item');
        if (!note) return null;
        const link = note.querySelector('a.cover.mask');
        return {
            href: link ? link.getAttribute('href') : null,
            title: note.querySelector('.title span') ? note.querySelector('.title span').textContent.trim() : ''
        };
    }""")
    print("   Explore first note:", json.dumps(explore_note, ensure_ascii=False))
    
    if explore_note and explore_note['href']:
        page2.evaluate("""() => {
            const note = document.querySelector('section.note-item');
            const link = note ? note.querySelector('a.cover.mask') : null;
            if (link) link.click();
        }""")
        time.sleep(5)
        print("   URL after click:", page2.url)
        print("   Title:", page2.title()[:60])
    
    browser.close()
    print("\nDone")