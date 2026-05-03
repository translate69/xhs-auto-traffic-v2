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

    # Capture network requests on explore page to understand how it loads notes
    note_requests = []
    feed_requests = []

    def on_request(req):
        url = req.url
        if "/feed/" in url or "/note/" in url or "search" in url.lower():
            note_requests.append(url[:100])

    page.on("request", on_request)

    print("1. Go to explore and capture note loading requests...")
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    
    # Wait a bit for notes to load
    time.sleep(5)
    
    print(f"   Notes captured during explore load:")
    for r in note_requests[:15]:
        print(f"     {r}")

    print(f"\n2. Now try going to search_result from same context...")
    
    # Open a new page in same context
    page2 = context.new_page()
    feed_requests.clear()
    
    def on_request2(req):
        url = req.url
        if "/feed/" in url or "/note/" in url or "search" in url.lower():
            feed_requests.append(url[:100])
    
    page2.on("request", on_request2)
    
    page2.goto("https://www.xiaohongshu.com/search_result?keyword=汕尾美食&type=51", wait_until="domcontentloaded")
    time.sleep(10)  # Wait for potential API calls
    
    print(f"   Requests on search_result page:")
    for r in feed_requests[:15]:
        print(f"     {r}")

    # Check the note data from explore page's __INITIAL_STATE__
    print("\n3. Explore page note data in __INITIAL_STATE__...")
    explore_note_data = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.feed) return 'no feed';
        const feedKeys = Object.keys(state.feed);
        // Get a note item if possible
        const firstFeed = state.feed[feedKeys[0]];
        if (firstFeed && firstFeed.items) {
            return { key: feedKeys[0], count: firstFeed.items.length };
        }
        return { keys: feedKeys };
    }""")
    print(f"   Explore note data: {explore_note_data}")

    page2.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_sr_notes_check.png")
    browser.close()
    print("\nDone")