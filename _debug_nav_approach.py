import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
import time
import json
import re
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    cookies = json.load(open(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json"))
    context.add_cookies(cookies)

    page = context.new_page()
    page.set_default_timeout(15000)

    print("=== Test: Navigate via window.location instead of page.goto ===")

    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("1. Note href:", note_href[:80])

    # Navigate using window.location (SPA navigation, not full page reload)
    print("\n2. Navigate via window.location...")
    page.evaluate("""(href) => {
        window.location.href = 'https://www.xiaohongshu.com' + href;
    }""", note_href)
    
    time.sleep(5)
    print("   URL:", page.url)
    print("   Title:", page.title()[:60])

    if "/login" in page.url:
        print("   -> LOGIN (expected for direct nav)")
    else:
        desc = page.query_selector("#detail-desc")
        print("   Has #detail-desc:", desc is not None)
        
        # Also check __INITIAL_STATE__ for note data
        note_data = page.evaluate("""() => {
            const state = window.__INITIAL_STATE__;
            if (!state || !state.note || !state.note.noteDetailMap) return 'no map';
            
            const map = state.note.noteDetailMap;
            const keys = Object.keys(map);
            if (!keys.length) return 'empty map';
            
            const firstVal = map[keys[0]];
            return {
                hasNote: !!firstVal.note,
                noteKeys: firstVal.note ? Object.keys(firstVal.note) : [],
                noteContent: firstVal.note ? JSON.stringify(firstVal.note).slice(0, 100) : 'null'
            };
        }""")
        print("   Note data:", note_data)

    # Now try the JS click approach and wait longer
    print("\n3. Go back to explore, click note, wait 10s...")
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    note_href2 = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("   New href:", note_href2[:80])

    page.evaluate("""() => {
        document.querySelector('section.note-item a.cover.mask').click();
    }""")
    
    # Poll every second for 10 seconds
    for i in range(10):
        time.sleep(1)
        url = page.url
        has_desc = page.query_selector("#detail-desc") is not None
        title = page.title()
        print(f"   {i+1}s: url={url[:60]}, has_detail={has_desc}")

        if has_desc:
            print("   -> Content loaded!")
            break
        if "/login" in url:
            print("   -> Login page")
            break

    browser.close()
    print("\nDone")