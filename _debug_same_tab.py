import sys
sys.path.insert(0, "E:/translate/claw/xhs-auto-traffic-v2")
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    import json
    cookies = json.load(open(r'E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json'))
    context.add_cookies(cookies)

    page = context.new_page()

    # Go to explore first (where notes DO render)
    print("1. Go to explore...")
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(5)
    print(f"   URL: {page.url}")
    notes = page.query_selector_all("section.note-item")
    print(f"   Notes: {len(notes)}")

    # Check the feed data in __INITIAL_STATE__
    feed_info = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.feed) return 'no feed';
        const feeds = state.feed.feeds;
        const feedsWrapper = state.feed.feedsWrapper;
        return {
            feedsCount: feeds ? Object.keys(feeds).length : 0,
            feedsWrapperCount: feedsWrapper ? Object.keys(feedsWrapper).length : 0,
            isFetching: state.feed.isFetching
        };
    }""")
    print(f"   Feed data: {feed_info}")

    # Now navigate to search_result in the SAME tab using page.goto
    print("\n2. Navigate to search_result (same tab)...")
    page.goto("https://www.xiaohongshu.com/search_result?keyword=汕尾美食&type=51", wait_until="domcontentloaded")
    time.sleep(5)
    print(f"   URL: {page.url}")
    notes2 = page.query_selector_all("section.note-item")
    print(f"   Notes: {len(notes2)}")

    # Check feed data on search_result
    sr_feed_info = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.feed) return 'no feed';
        const feeds = state.feed.feeds;
        const feedsWrapper = state.feed.feedsWrapper;
        return {
            feedsCount: feeds ? Object.keys(feeds).length : 0,
            feedsWrapperCount: feedsWrapper ? Object.keys(feedsWrapper).length : 0,
            isFetching: state.feed.isFetching,
            query: state.feed.query
        };
    }""")
    print(f"   Search_result feed data: {sr_feed_info}")

    # Check DOM - what elements exist?
    dom_info = page.evaluate("""() => {
        const sections = document.querySelectorAll('section');
        const allDivs = document.querySelectorAll('div[class*="note"]');
        const searchResult = document.querySelector('.search-result, .note-list, main, [class*="search-list"]');
        return {
            sectionCount: sections.length,
            noteDivCount: allDivs.length,
            searchResultClass: searchResult ? searchResult.className : 'none'
        };
    }""")
    print(f"   DOM info: {dom_info}")

    # Check if notes are in the page but hidden
    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_sr_explore_same_tab.png")
    
    # Try scrolling
    page.evaluate("window.scrollTo(0, 500)")
    time.sleep(2)
    notes3 = page.query_selector_all("section.note-item")
    print(f"   After scroll: {len(notes3)} notes")

    browser.close()
    print("\nDone")