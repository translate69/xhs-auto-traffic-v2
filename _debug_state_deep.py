import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
import time
import json
from playwright.sync_api import sync_playwright

results = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    cookies = json.load(open(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json"))
    context.add_cookies(cookies)

    page = context.new_page()
    page.set_default_timeout(20000)

    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(5)
    results["url"] = page.url
    results["note_count"] = len(page.query_selector_all("section.note-item"))

    # Check feed.feeds.computed
    feed_computed = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.feed || !state.feed.feeds) return null;
        
        const feeds = state.feed.feeds;
        const keys = Object.keys(feeds);
        if (!keys.length) return null;
        
        const firstFeed = feeds[keys[0]];
        if (!firstFeed) return null;
        
        // Check computed
        const computed = firstFeed.computed;
        if (computed) {
            return {
                computedKeys: Object.keys(computed),
                noteCount: computed.noteCount || 0,
                noteList: computed.noteList ? computed.noteList.slice(0, 3).map(n => ({
                    id: n.id || n.noteId,
                    title: n.title || n.displayTitle || '',
                    abs: n.abs || n.desc || ''
                })) : null
            };
        }
        
        return { error: 'no computed', allKeys: Object.keys(firstFeed) };
    }""")
    results["feed_computed"] = feed_computed

    # Check subs
    subs_data = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.feed || !state.feed.feeds) return null;
        
        const feeds = state.feed.feeds;
        const firstFeed = feeds[Object.keys(feeds)[0]];
        const subs = firstFeed.subs;
        
        if (!subs) return 'no subs';
        
        const subsKeys = Object.keys(subs);
        return {
            subsKeys: subsKeys.slice(0, 10),
            firstSub: subs[subsKeys[0]] ? {
                keys: Object.keys(subs[subsKeys[0]]),
                hasItems: !!subs[subsKeys[0]].items,
                itemCount: subs[subsKeys[0]].items ? subs[subsKeys[0]].items.length : 0
            } : null
        };
    }""")
    results["subs_data"] = subs_data

    # Get first note href and check if we can get title from __INITIAL_STATE__ by id
    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : '';
    }""")
    results["first_href"] = note_href[:80]

    # Check map
    map_data = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.feed || !state.feed.feeds) return null;
        
        const feeds = state.feed.feeds;
        const firstFeed = feeds[Object.keys(feeds)[0]];
        const feedMap = firstFeed.map;
        
        if (!feedMap) return 'no map';
        
        const mapKeys = Object.keys(feedMap).slice(0, 5);
        return {
            mapKeyCount: Object.keys(feedMap).length,
            firstKey: mapKeys[0],
            firstValueKeys: feedMap[mapKeys[0]] ? Object.keys(feedMap[mapKeys[0]]) : []
        };
    }""")
    results["map_data"] = map_data

    browser.close()

# Write to file
with open(r"E:\translate\claw\xhs-auto-traffic-v2\_debug_state_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("Done - written to _debug_state_results.json")
print("URL:", results.get("url"))
print("Notes:", results.get("note_count"))
print("First href:", results.get("first_href"))