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

    # Go to explore
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("1. Note href:", note_href[:80])

    page.evaluate("""() => {
        document.querySelector('section.note-item a.cover.mask').click();
    }""")
    time.sleep(5)
    print("2. URL:", page.url)

    # Check user state
    user_state = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state) return 'no state';
        
        const user = state.user;
        if (!user) return 'no user in state';
        
        return {
            loggedIn: user.loggedIn,
            activated: user.activated,
            hasUserInfo: !!user.userInfo,
            userId: user.userInfo ? user.userInfo.id : null,
            userKeys: Object.keys(user).slice(0, 10)
        };
    }""")
    print("3. User state:", user_state)

    # Check what keys exist in state
    state_keys = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state) return [];
        return Object.keys(state).filter(k => !k.startsWith('__'));
    }""")
    print("4. State keys:", state_keys)

    # Check note state more carefully
    note_detail = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.note) return 'no note state';
        
        const ndm = state.note.noteDetailMap;
        if (!ndm) return 'no noteDetailMap';
        
        const keys = Object.keys(ndm);
        if (!keys.length) return 'empty map';
        
        const firstKey = keys[0];
        const firstVal = ndm[firstKey];
        
        return {
            mapKeyCount: keys.length,
            firstKeyRepr: JSON.stringify(firstKey),
            firstValKeys: Object.keys(firstVal),
            noteObj: firstVal.note ? {
                noteKeys: Object.keys(firstVal.note),
                noteTitle: firstVal.note.title || firstVal.note.displayTitle || '',
                noteType: firstVal.note.type || ''
            } : { error: 'note is empty object' }
        };
    }""")
    print("5. Note detail:", note_detail)

    browser.close()
    print("\nDone")