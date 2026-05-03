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

    # Direct to search_result with long wait
    print("1. Go to search_result with 8s wait...")
    page.goto("https://www.xiaohongshu.com/search_result?keyword=%E6%B1%95%E5%B0%BE%E7%BE%8E%E9%A3%9F", wait_until="domcontentloaded")
    time.sleep(8)
    print("   URL:", page.url)
    print("   Notes (section.note-item):", len(page.query_selector_all("section.note-item")))

    # Check all possible note selectors
    selectors = [
        "section.note-item",
        ".note-item",
        "[class*='note-item']",
        ".feeds .note",
        ".note-list .note",
        "[class*='feeds'] [class*='note']"
    ]
    print("\n   Selector checks:")
    for sel in selectors:
        count = len(page.query_selector_all(sel))
        if count > 0:
            print(f"   {sel}: {count}")

    # Check __INITIAL_STATE__ for note data
    state_data = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.feed || !state.feed.feeds) return 'no state.feed.feeds';
        
        const feeds = state.feed.feeds;
        const keys = Object.keys(feeds);
        if (!keys.length) return 'no feed keys';
        
        const firstKey = keys[0];
        const firstFeed = feeds[firstKey];
        
        return {
            feedKey: firstKey,
            hasItems: !!firstFeed.items,
            itemCount: firstFeed.items ? firstFeed.items.length : 0,
            firstItem: firstFeed.items && firstFeed.items[0] ? {
                id: firstFeed.items[0].id || firstFeed.items[0].noteId,
                title: firstFeed.items[0].title || firstFeed.items[0].displayTitle || '',
                type: firstFeed.items[0].type || ''
            } : null
        };
    }""")
    print("\n   __INITIAL_STATE__ feed:", json.dumps(state_data, ensure_ascii=False))

    # Wait more and check again
    print("\n2. Waiting 5 more seconds...")
    time.sleep(5)
    print("   Notes:", len(page.query_selector_all("section.note-item")))
    
    # Try waiting for notes with timeout
    try:
        page.wait_for_selector("section.note-item", timeout=10000)
        print("   wait_for_selector found notes!")
    except Exception as e:
        print(f"   wait_for_selector timeout: {e}")

    # Check the HTML content near where notes should be
    html_preview = page.evaluate("""() => {
        // Check what's in the main content area
        const main = document.querySelector('#main, .main, [class*="feeds"], [class*="search"]');
        if (!main) return document.body.innerHTML.slice(0, 500);
        return main.innerHTML.slice(0, 500);
    }""")
    print("\n   HTML preview:", html_preview[:300])

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_sr_long.png")
    browser.close()
    print("\nDone")