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

    print("=== Cookie 有效性测试 ===")

    # Step 1: Check web_session cookie
    ctx_cookies = page.context.cookies()
    ws = [c for c in ctx_cookies if c['name'] == 'web_session']
    print(f"\nweb_session: {ws[0]['value'][:40] if ws else 'NOT FOUND'}")
    print(f"domain: {ws[0]['domain'] if ws else 'N/A'}")
    print(f"secure: {ws[0]['secure'] if ws else 'N/A'}")

    # Step 2: Go to explore and get a note URL
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    print(f"\nExplore URL: {page.url}")
    print(f"section.note-item: {len(page.query_selector_all('section.note-item'))}")

    # Get first note href
    first_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print(f"First href: {first_href[:80] if first_href else None}")

    # Step 3: Get user info from __INITIAL_STATE__
    user_info = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state) return 'no state';
        // Check user section
        const user = state.user || state.currentUser || state.auth;
        const keys = state ? Object.keys(state).filter(k => !k.startsWith('__')) : [];
        return { 
            stateKeys: keys.slice(0, 20),
            userKeys: user ? Object.keys(user) : []
        };
    }""")
    print(f"\n__INITIAL_STATE__ keys: {user_info}")

    # Step 4: Check if user is logged in on explore page
    login_status = page.evaluate("""() => {
        // Look for user avatar or name (indicates logged in)
        const avatar = document.querySelector('.avatar, [class*="avatar"], img[src*="avatar"]');
        const loginBtn = document.querySelector('.login-btn, [class*="login"], a[href*="login"]');
        const userName = document.querySelector('[class*="username"], [class*="nickname"]');
        
        return {
            hasAvatar: !!avatar,
            hasLoginBtn: !!loginBtn,
            hasUserName: !!userName,
            bodyText: document.body.textContent.slice(0, 100)
        };
    }""")
    print(f"Login status: {login_status}")

    # Step 5: Try accessing note directly via click-through on the same page
    print("\n5. Click note via page.evaluate (same tab)...")
    page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        if (link) link.click();
    }""")
    time.sleep(5)
    print(f"   URL after click: {page.url}")
    print(f"   Title: {page.title()[:60]}")

    # Step 6: Check cookies after navigation
    ctx_cookies_after = page.context.cookies()
    ws_after = [c for c in ctx_cookies_after if c['name'] == 'web_session']
    print(f"\nweb_session after click: {ws_after[0]['value'][:40] if ws_after else 'NOT FOUND'}")

    # Step 7: Check __INITIAL_STATE__ on the note page
    note_state = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state) return 'no state';
        
        // Try to get note data
        const noteData = state.note || state.feed || state.article;
        const keys = state ? Object.keys(state).filter(k => !k.startsWith('__')) : [];
        
        return {
            stateKeys: keys.slice(0, 15),
            hasNoteData: !!noteData,
            noteKeys: noteData ? Object.keys(noteData).slice(0, 10) : []
        };
    }""")
    print(f"Note page state: {note_state}")

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_cookie_test.png")
    browser.close()
    print("\nDone")