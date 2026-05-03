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

    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    # Get feed from __INITIAL_STATE__.feed.feeds (not .search)
    feed_data = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.feed || !state.feed.feeds) return null;
        
        const feeds = state.feed.feeds;
        const keys = Object.keys(feeds);
        if (!keys.length) return null;
        
        const firstFeed = feeds[keys[0]];
        if (!firstFeed) return null;
        
        return {
            key: keys[0],
            hasItems: !!firstFeed.items,
            itemCount: firstFeed.items ? firstFeed.items.length : 0,
            firstItem: firstFeed.items && firstFeed.items[0] ? {
                id: firstFeed.items[0].id,
                title: firstFeed.items[0].title,
                abs: firstFeed.items[0].abs || '',
                desc: firstFeed.items[0].desc || '',
                displayTitle: firstFeed.items[0].displayTitle || '',
                type: firstFeed.items[0].type
            } : null,
            allKeys: Object.keys(firstFeed)
        };
    }""")

    print("1. Feed data:", json.dumps(feed_data, ensure_ascii=False, indent=2))

    # Check if abs is in the first item
    if feed_data and feed_data.get('firstItem'):
        item = feed_data['firstItem']
        print(f"\n2. First item:")
        print(f"   id: {item['id']}")
        print(f"   title: {item['title']}")
        print(f"   abs: '{item['abs']}'")
        print(f"   desc: '{item['desc']}'")
        print(f"   displayTitle: '{item['displayTitle']}'")

    # Get note href from DOM
    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : '';
    }""")
    print(f"\n3. First note DOM href: {note_href[:80]}")

    # Try to get note detail via API using the id from __INITIAL_STATE__
    if feed_data and feed_data.get('firstItem') and feed_data['firstItem']['id']:
        note_id = feed_data['firstItem']['id']
        print(f"\n4. Calling note detail API for {note_id}...")
        
        api_url = f"https://edith.xiaohongshu.com/api/sns/web/v1/note/{note_id}"
        resp = page.request.get(api_url)
        print(f"   Status: {resp.status}")
        print(f"   URL: {resp.url}")
        
        if resp.status == 200:
            data = resp.json()
            print(f"   Data: {json.dumps(data, ensure_ascii=False)[:400]}")
        else:
            print(f"   Response: {resp.text()[:200]}")

    browser.close()
    print("\nDone")