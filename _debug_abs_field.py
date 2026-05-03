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

    # Go to explore via homepage search
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    page.fill("#search-input", "汕尾美食")
    time.sleep(0.3)
    page.keyboard.press("Enter")
    time.sleep(5)

    print("1. URL:", page.url)

    # Get ALL data from __INITIAL_STATE__ feed items
    feed_items = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.feed || !state.feed.feeds) return null;
        
        const feeds = state.feed.feeds;
        const keys = Object.keys(feeds);
        if (!keys.length) return null;
        
        const firstFeed = feeds[keys[0]];
        if (!firstFeed || !firstFeed.items) return null;
        
        return firstFeed.items.slice(0, 5).map(item => {
            // Return all keys so we can see what's available
            return {
                keys: Object.keys(item),
                id: item.id || item.noteId,
                title: item.title || item.displayTitle || '',
                abs: item.abs || '',
                desc: item.desc || item.description || '',
                displayTitle: item.displayTitle || '',
                type: item.type || '',
                cover: item.cover || '',
                time: item.time || '',
                liked: item.liked,
                likecount: item.likecount,
                commentcount: item.commentcount,
                user: item.user ? {
                    nickname: item.user.nickname || '',
                    id: item.user.id || ''
                } : null
            };
        });
    }""")

    print(f"\n2. Feed items from __INITIAL_STATE__:")
    if feed_items:
        for i, item in enumerate(feed_items):
            print(f"\n   Item {i}:")
            print(f"      keys: {item['keys']}")
            print(f"      id: {item['id']}")
            print(f"      title: {item['title'][:50] if item['title'] else 'EMPTY'}")
            print(f"      abs: {item['abs'][:80] if item['abs'] else 'EMPTY'}")
            print(f"      desc: {item['desc'][:80] if item['desc'] else 'EMPTY'}")
            print(f"      displayTitle: {item['displayTitle'][:50] if item['displayTitle'] else 'EMPTY'}")
            print(f"      user: {item['user']}")
    else:
        print("   No feed items found!")

    # Also check: what about search state?
    search_feed = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.search) return null;
        
        const sfeeds = state.search.searchFeedsWrapper;
        if (!sfeeds) return null;
        
        const feeds = sfeeds.feeds || sfeeds.items || [];
        return feeds.slice(0, 3).map(item => {
            return {
                keys: Object.keys(item),
                title: item.title || item.displayTitle || '',
                abs: item.abs || '',
                desc: item.desc || ''
            };
        });
    }""")
    print(f"\n3. Search feed items:")
    if search_feed:
        for i, item in enumerate(search_feed):
            print(f"   Item {i}: title={item['title'][:40]}, abs={item['abs'][:60]}")
    else:
        print("   No search feed found!")

    browser.close()
    print("\nDone")