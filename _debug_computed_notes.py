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

    # Check the actual full state of feed.feeds["dep"]
    full_feed = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.feed || !state.feed.feeds) return null;
        
        const feeds = state.feed.feeds;
        const depFeed = feeds['dep'];
        if (!depFeed) return 'no dep feed';
        
        // Get computed
        const computed = depFeed.computed;
        if (!computed) return 'no computed in dep';
        
        return {
            computedKeys: Object.keys(computed),
            noteCount: computed.noteCount || 0,
            noteListExists: !!computed.noteList,
            noteListLen: computed.noteList ? computed.noteList.length : 0,
            firstNote: computed.noteList && computed.noteList[0] ? {
                id: computed.noteList[0].id,
                title: computed.noteList[0].title,
                abs: computed.noteList[0].abs || '',
                desc: computed.noteList[0].desc || '',
                type: computed.noteList[0].type
            } : null,
            // Also check subs.dep
            subsDep: depFeed.subs && depFeed.subs.dep ? {
                keys: Object.keys(depFeed.subs.dep),
                hasValue: depFeed.subs.dep._value !== undefined
            } : null
        };
    }""")

    print("Full feed data:", json.dumps(full_feed, ensure_ascii=False, indent=2))

    # If computed has noteList, get all notes from it
    if full_feed and full_feed.get('noteListExists'):
        all_notes = page.evaluate("""() => {
            const state = window.__INITIAL_STATE__;
            const feeds = state.feed.feeds;
            const depFeed = feeds['dep'];
            const computed = depFeed.computed;
            
            return computed.noteList.slice(0, 10).map(n => ({
                id: n.id,
                title: n.title || n.displayTitle || '',
                abs: n.abs || '',
                desc: n.desc || '',
                type: n.type || '',
                cover: n.cover || ''
            }));
        }""")
        print(f"\nAll notes from computed.noteList: {len(all_notes)}")
        for n in all_notes:
            print(f"  id={n['id']}, title={n['title'][:40]}, abs={n['abs'][:40]}")

    browser.close()
    print("\nDone")