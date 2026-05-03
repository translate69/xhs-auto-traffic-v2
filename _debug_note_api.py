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

    print("1. Go to explore page...")
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    print("   URL:", page.url)
    print("   Notes:", len(page.query_selector_all("section.note-item")))

    # Get first note's href
    first_note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("   First note href:", first_note_href[:80] if first_note_href else None)

    # Check __INITIAL_STATE__ for notes
    note_state = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.feed) return 'no feed state';
        
        const feeds = state.feed.feeds;
        if (!feeds) return 'no feeds';
        
        const firstFeedKey = Object.keys(feeds)[0];
        const firstFeed = feeds[firstFeedKey];
        if (!firstFeed || !firstFeed.items || !firstFeed.items.length) return 'no items';
        
        const firstNote = firstFeed.items[0];
        return {
            noteId: firstNote.id || firstNote.noteId,
            title: firstNote.title || firstNote.displayTitle || '',
            type: firstNote.type || '',
            displayTitle: firstNote.displayTitle || ''
        };
    }""")
    print(f"\n2. Note state from __INITIAL_STATE__: {note_state}")

    # Direct navigation to note with xsec_token
    if first_note_href:
        print(f"\n3. Direct navigation: https://www.xiaohongshu.com{first_note_href[:100]}...")
        page2 = context.new_page()
        page2.goto("https://www.xiaohongshu.com" + first_note_href, wait_until="domcontentloaded", timeout=15000)
        time.sleep(3)
        print("   URL:", page2.url)
        print("   Title:", page2.title()[:60])
        if "/login" in page2.url:
            print("   -> Login page!")
        elif "/404" in page2.url:
            print("   -> 404 page!")
        else:
            detail = page2.query_selector("#detail-desc")
            print("   #detail-desc:", detail is not None)
        page2.close()

    browser.close()
    print("\nDone")