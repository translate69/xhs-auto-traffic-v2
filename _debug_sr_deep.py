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

    print("=== Inspect search_result page in depth ===")

    # Use the exact SEARCH_URL from search_collector.py
    search_url = "https://www.xiaohongshu.com/search_result?keyword=%E6%B1%95%E5%B0%BE%E7%BE%8E%E9%A3%9F&type=51"
    page.goto(search_url, wait_until="domcontentloaded")
    time.sleep(8)
    print("1. URL:", page.url)

    # Check for notes with various selectors
    selectors = [
        "section.note-item",
        ".note-item",
        "[class*='note-item']",
        ".feeds .item",
        ".search-result .note",
        "[class*='feeds'] [class*='note']",
        ".content-wrapper section"
    ]
    print("\n2. Selector checks:")
    for sel in selectors:
        count = len(page.query_selector_all(sel))
        if count > 0:
            print(f"   {sel}: {count}")

    # Check __INITIAL_STATE__
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
    print("\n3. __INITIAL_STATE__:", json.dumps(state_data, ensure_ascii=False))

    # Check the body text to see what's visible
    body_text = page.evaluate("document.body.textContent.replace(/\\s+/g, ' ').trim().slice(0, 300)")
    print("\n4. Body text preview:", body_text[:200])

    # Check for any error or loading states
    loading = page.evaluate("""() => {
        const loaders = document.querySelectorAll('[class*="loading"], [class*="skeleton"], [class*="placeholder"]');
        return {
            hasLoader: loaders.length > 0,
            loaderCount: loaders.length,
            hasError: !!document.querySelector('[class*="error"]'),
            hasEmpty: !!document.querySelector('[class*="empty"], [class*="no-result"]')
        };
    }""")
    print("\n5. Loading states:", json.dumps(loading, ensure_ascii=False))

    # Check the FEEDS wrapper element
    feeds_info = page.evaluate("""() => {
        const feedsWrapper = document.querySelector('.feeds-wrapper, [class*="feeds-wrapper"], .search-feeds');
        if (!feedsWrapper) return 'no feeds wrapper found';
        
        return {
            found: true,
            class: feedsWrapper.className,
            childCount: feedsWrapper.children.length,
            innerHTML: feedsWrapper.innerHTML.slice(0, 300)
        };
    }""")
    print("\n6. Feeds wrapper:", json.dumps(feeds_info, ensure_ascii=False))

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_sr_deep.png", full_page=True)
    browser.close()
    print("\nDone")