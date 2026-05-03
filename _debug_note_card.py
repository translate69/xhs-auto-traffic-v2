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

    # Explore noteCard structure
    note_card = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        const feeds = state.feed.feeds;
        const depFeed = feeds['dep'];
        const subRef = depFeed.subs.sub;
        const arr = subRef._value;
        
        // Get first item's noteCard
        const firstItem = arr['0'];
        const nc = firstItem.noteCard;
        
        return {
            noteCardKeys: nc ? Object.keys(nc) : [],
            title: nc ? (nc.title || nc.displayTitle || '') : '',
            abs: nc ? (nc.abs || nc.description || '') : '',
            desc: nc ? (nc.desc || '') : '',
            type: nc ? (nc.type || '') : '',
            cover: nc ? (nc.cover || '') : '',
            user: nc && nc.user ? {
                nickname: nc.user.nickname || '',
                id: nc.user.id || ''
            } : null
        };
    }""")
    
    print("Note card structure:", json.dumps(note_card, ensure_ascii=False, indent=2))

    # Get all notes with full noteCard data
    all_notes = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        const feeds = state.feed.feeds;
        const depFeed = feeds['dep'];
        const subRef = depFeed.subs.sub;
        const arr = subRef._value;
        
        const notes = [];
        for (const key of Object.keys(arr)) {
            const el = arr[key];
            const nc = el.noteCard;
            if (nc) {
                notes.push({
                    id: el.id,
                    noteCardKeys: Object.keys(nc),
                    title: nc.title || nc.displayTitle || '',
                    abs: nc.abs || '',
                    desc: nc.desc || nc.description || '',
                    type: nc.type || ''
                });
            }
        }
        return notes;
    }""")
    
    print(f"\nAll notes ({len(all_notes)}):")
    for n in all_notes[:10]:
        print(f"  id={n['id']}, title={n['title'][:40]}, abs={n['abs'][:50]}, desc={n['desc'][:30]}")

    browser.close()
    print("\nDone")