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

    print("=== Check __INITIAL_STATE__ on explore page (BEFORE clicking note) ===")

    # Go to explore
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    print("1. Explore URL:", page.url)

    # Check __INITIAL_STATE__ for note feed data
    explore_state = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state) return 'no state';
        
        const feed = state.feed;
        if (!feed) return 'no feed in state';
        
        const feeds = feed.feeds;
        if (!feeds) return 'no feeds in feed';
        
        const keys = Object.keys(feeds);
        if (!keys.length) return 'no feed keys';
        
        const firstKey = keys[0];
        const firstFeed = feeds[firstKey];
        
        if (!firstFeed) return 'no firstFeed';
        
        return {
            feedKey: firstKey,
            hasItems: !!firstFeed.items,
            itemCount: firstFeed.items ? firstFeed.items.length : 0,
            firstItem: firstFeed.items && firstFeed.items[0] ? {
                id: firstFeed.items[0].id || firstFeed.items[0].noteId,
                title: firstFeed.items[0].title || firstFeed.items[0].displayTitle || '',
                type: firstFeed.items[0].type || ''
            } : null
        };
    }""")
    print("2. Explore feed state:", json.dumps(explore_state, ensure_ascii=False))

    # Get a note href
    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("3. First note href:", note_href[:80])

    # Click the note
    page.evaluate("""() => {
        document.querySelector('section.note-item a.cover.mask').click();
    }""")
    time.sleep(5)
    print("4. After click URL:", page.url)

    # Check __INITIAL_STATE__ again (on note page)
    note_state = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state) return 'no state';
        
        const noteState = state.note;
        if (!noteState) return 'no note state - keys: ' + Object.keys(state).slice(0, 10).join(',');
        
        const noteDetailMap = noteState.noteDetailMap;
        if (!noteDetailMap) return 'no noteDetailMap - keys: ' + Object.keys(noteState).join(',');
        
        const keys = Object.keys(noteDetailMap);
        if (!keys.length) return 'empty noteDetailMap';
        
        const firstEntry = noteDetailMap[keys[0]];
        
        return {
            mapKeyCount: keys.length,
            firstKey: keys[0],
            firstKeyType: typeof keys[0],
            firstValueKeys: Object.keys(firstEntry),
            hasNote: !!firstEntry.note,
            noteType: typeof firstEntry.note,
            noteContent: firstEntry.note ? JSON.stringify(firstEntry.note) : 'null'
        };
    }""")
    print("5. Note page state:", json.dumps(note_state, ensure_ascii=False, indent=2))

    # Check user state on note page
    user_state = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state) return 'no state';
        
        const user = state.user;
        if (!user) return 'no user in state - keys: ' + Object.keys(state).join(',');
        
        return {
            loggedIn: user.loggedIn,
            activated: user.activated,
            hasUserInfo: !!user.userInfo,
            userId: user.userInfo ? user.userInfo.id : null
        };
    }""")
    print("6. User state:", json.dumps(user_state, ensure_ascii=False))

    # Try to get note detail from __INITIAL_STATE__ using the note ID from URL
    note_id_from_url = page.url.split('/explore/')[1].split('?')[0] if '/explore/' in page.url else None
    print("\n7. Note ID from URL:", note_id_from_url)

    # Look for this specific note in the state
    note_in_state = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state) return 'no state';
        
        // Search for the note ID in the entire state
        const noteIdFromUrl = window.location.pathname.split('/explore/')[1]?.split('?')[0];
        
        // Check noteDetailMap
        const noteDetailMap = state.note?.noteDetailMap;
        if (noteDetailMap) {
            const mapKeys = Object.keys(noteDetailMap);
            if (mapKeys.length > 0) {
                const firstEntry = noteDetailMap[mapKeys[0]];
                return {
                    found: true,
                    location: 'noteDetailMap',
                    key: mapKeys[0],
                    valueKeys: Object.keys(firstEntry)
                };
            }
        }
        
        return { found: false };
    }""")
    print("7. Note in state:", json.dumps(note_in_state, ensure_ascii=False))

    browser.close()
    print("\nDone")