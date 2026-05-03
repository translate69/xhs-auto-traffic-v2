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

    # Check if going to "/" redirects somewhere
    print("1. Go to /")
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    print("   URL after /:", page.url)
    
    # Check if there's a search input on whatever page we're on
    search_input = page.query_selector("#search-input")
    print("   Has #search-input:", search_input is not None)

    # Now try the search_result page directly
    print("\n2. Go directly to search_result page...")
    page2 = context.new_page()
    page2.goto("https://www.xiaohongshu.com/search_result?keyword=%E6%B1%95%E5%B0%BE%E7%BE%8E%E9%A3%9F", wait_until="domcontentloaded")
    time.sleep(3)
    print("   URL:", page2.url)
    print("   Notes:", len(page2.query_selector_all("section.note-item")))
    has_filter = page2.query_selector(".filter")
    print("   Has .filter:", has_filter is not None)

    # Check __INITIAL_STATE__
    init_state = page2.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state) return 'no state';
        return {
            hasSearch: !!state.search,
            hasFeed: !!state.feed,
            searchKeys: state.search ? Object.keys(state.search) : [],
            feedKeys: state.feed ? Object.keys(state.feed) : []
        };
    }""")
    print("   __INITIAL_STATE__:", init_state)
    
    page2.close()

    # Now try the old search page
    print("\n3. Try /search page...")
    page3 = context.new_page()
    page3.goto("https://www.xiaohongshu.com/search?keyword=%E6%B1%95%E5%B0%BE%E7%BE%8E%E9%A3%9F", wait_until="domcontentloaded")
    time.sleep(3)
    print("   URL:", page3.url)
    print("   Notes:", len(page3.query_selector_all("section.note-item")))
    has_filter3 = page3.query_selector(".filter")
    print("   Has .filter:", has_filter3 is not None)
    page3.close()

    browser.close()
    print("\nDone")