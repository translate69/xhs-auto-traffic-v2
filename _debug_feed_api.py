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

    print("=== Test: Get note data from FEED API instead of detail page ===")

    # Go to explore
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    # Try to call the feed API directly
    print("1. Calling feed API...")
    
    # Try the edith API for feed
    feed_api_urls = [
        "https://edith.xiaohongshu.com/api/sns/web/v1/feed",
        "https://edith.xiaohongshu.com/api/sns/web/v1/homefeed",
        "https://edith.xiaohongshu.com/api/sns/web/v1/explore/feed"
    ]
    
    for api_url in feed_api_urls:
        try:
            resp = page.request.get(api_url)
            print(f"   [{resp.status}] {api_url}")
            if resp.status == 200:
                data = resp.json()
                print(f"       data keys: {list(data.keys())}")
                print(f"       data: {json.dumps(data, ensure_ascii=False)[:200]}")
        except Exception as e:
            print(f"   ERROR: {e}")

    # Now check if the explore page has more note data in __INITIAL_STATE__
    print("\n2. Check __INITIAL_STATE__ for explore feed...")
    
    # Go to homepage and search
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    
    page.fill("#search-input", "汕尾美食")
    time.sleep(0.3)
    page.keyboard.press("Enter")
    time.sleep(5)
    
    print("   URL:", page.url)
    
    # Check the state
    feed_state = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state) return 'no state';
        
        // Check search state
        const search = state.search;
        const feed = state.feed;
        
        return {
            hasSearch: !!search,
            hasFeed: !!feed,
            searchKeys: search ? Object.keys(search).slice(0, 10) : [],
            feedKeys: feed ? Object.keys(feed).slice(0, 10) : []
        };
    }""")
    print("   State:", json.dumps(feed_state, ensure_ascii=False))

    # Check if search state has note items
    search_notes = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.search) return 'no search state';
        
        const searchState = state.search;
        const feedsWrapper = searchState.searchFeedsWrapper;
        
        if (!feedsWrapper) return 'no searchFeedsWrapper';
        
        // Check for notes/items
        const feeds = feedsWrapper.feeds || feedsWrapper.items || feedsWrapper.notes;
        
        return {
            hasFeeds: !!feeds,
            count: feeds ? feeds.length : 0,
            firstNote: feeds && feeds[0] ? {
                id: feeds[0].id || feeds[0].noteId,
                title: feeds[0].title || feeds[0].displayTitle,
                type: feeds[0].type
            } : null
        };
    }""")
    print("   Search notes:", json.dumps(search_notes, ensure_ascii=False))

    browser.close()
    print("\nDone")