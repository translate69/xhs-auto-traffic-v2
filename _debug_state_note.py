import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
import time
import json
import re
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    cookies = json.load(open(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json"))
    context.add_cookies(cookies)

    page = context.new_page()
    page.set_default_timeout(15000)

    # Go to explore
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    # Get note href
    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("1. Note href:", note_href[:80])

    # Click via JS (triggers navigation)
    page.evaluate("""() => {
        document.querySelector('section.note-item a.cover.mask').click();
    }""")
    time.sleep(5)
    print("2. URL:", page.url)

    # Now extract note content from __INITIAL_STATE__
    note_data = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.note || !state.note.noteDetailMap) {
            return { error: 'no state.note.noteDetailMap', stateKeys: state ? Object.keys(state) : [] };
        }
        
        const noteMap = state.note.noteDetailMap;
        const keys = Object.keys(noteMap);
        
        if (!keys.length) return { error: 'empty noteDetailMap' };
        
        const noteId = keys[0];
        const note = noteMap[noteId];
        
        return {
            noteId: noteId,
            title: note.title || note.displayTitle || '',
            type: note.type || '',
            desc: note.desc || note.description || '',
            imageCount: note.imageList ? note.imageList.length : 0,
            user: note.user ? note.user.nickname : 'unknown',
            likecount: note.interactInfo ? note.interactInfo.likedCount : 0,
            noteKeys: Object.keys(note).slice(0, 20)
        };
    }""")
    print("3. Note data from __INITIAL_STATE__:", json.dumps(note_data, ensure_ascii=False, indent=2))

    # Also try to get note data from anywhere in the page
    all_note_data = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state) return 'no state';
        
        // Find any key that might contain note data
        const possibleKeys = ['note', 'article', 'feed', 'currentNote', 'selectedNote'];
        const results = {};
        
        for (const key of possibleKeys) {
            if (state[key]) {
                try {
                    const val = state[key];
                    if (val.noteDetailMap || val.items || val.note) {
                        results[key] = JSON.parse(JSON.stringify(val));
                    }
                } catch(e) {}
            }
        }
        
        return results;
    }""")
    print("4. All note-related state:", json.dumps(all_note_data, ensure_ascii=False, indent=2)[:500])

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_state_data.png")
    browser.close()
    print("\nDone")