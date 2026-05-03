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

    # Explore subs.sub._value array structure
    array_data = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        const feeds = state.feed.feeds;
        const depFeed = feeds['dep'];
        const subRef = depFeed.subs.sub;
        const arr = subRef._value;
        
        // Check what the array elements look like
        const firstEl = arr['0'];
        const secondEl = arr['1'];
        
        return {
            arrayLength: arr.length || Object.keys(arr).length,
            firstElKeys: firstEl ? Object.keys(firstEl) : [],
            firstElType: typeof firstEl,
            firstElHasId: firstEl && (firstEl.id || firstEl.noteId),
            firstElId: firstEl ? (firstEl.id || firstEl.noteId) : null,
            firstElTitle: firstEl ? (firstEl.title || firstEl.displayTitle || firstEl.abs || '') : '',
            firstElAbs: firstEl ? (firstEl.abs || '') : '',
            firstElDesc: firstEl ? (firstEl.desc || '') : '',
            secondElKeys: secondEl ? Object.keys(secondEl) : [],
            secondElId: secondEl ? (secondEl.id || secondEl.noteId) : null
        };
    }""")
    
    print("Array data:", json.dumps(array_data, ensure_ascii=False, indent=2))

    # Get all items from the array (the subs.sub._value array)
    all_items = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        const feeds = state.feed.feeds;
        const depFeed = feeds['dep'];
        const subRef = depFeed.subs.sub;
        const arr = subRef._value;
        
        // It's an array-like object with numeric keys
        const items = [];
        for (const key of Object.keys(arr)) {
            const el = arr[key];
            if (el && typeof el === 'object' && (el.id || el.noteId)) {
                items.push({
                    key: key,
                    id: el.id || el.noteId,
                    title: el.title || el.displayTitle || el.abs || '',
                    abs: el.abs || '',
                    desc: el.desc || ''
                });
            }
        }
        return items;
    }""")
    
    print(f"\nAll items ({len(all_items)}):")
    for n in all_items[:10]:
        print(f"  [{n['key']}] id={n['id']}, title={n['title'][:40]}, abs={n['abs'][:40]}")

    browser.close()
    print("\nDone")