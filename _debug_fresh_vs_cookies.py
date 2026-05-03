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

    print("=== Test: Fresh browser vs loaded cookies ===")

    # Test 1: Fresh context (no cookies)
    print("1. Fresh context (no cookies)...")
    ctx_fresh = browser.new_context()
    page_fresh = ctx_fresh.new_page()
    page_fresh.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    print("   URL:", page_fresh.url)
    print("   Notes:", len(page_fresh.query_selector_all("section.note-item")))
    ctx_fresh.close()
    page_fresh.close()

    # Test 2: With cookies
    print("\n2. With cookies...")
    page2 = context.new_page()
    page2.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    print("   URL:", page2.url)
    print("   Notes:", len(page2.query_selector_all("section.note-item")))
    
    # Check login status
    login_status = page2.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state) return 'no state';
        const user = state.user;
        if (!user) return 'no user in state';
        return {
            loggedIn: user.loggedIn,
            activated: user.activated,
            userId: user.userInfo ? user.userInfo.id : null
        };
    }""")
    print("   User state:", json.dumps(login_status, ensure_ascii=False))

    # Test 3: From explore page, go to search_result
    print("\n3. From explore to search_result...")
    page2.goto("https://www.xiaohongshu.com/search_result?keyword=%E6%B1%95%E5%B0%BE%E7%BE%8E%E9%A3%9F", wait_until="domcontentloaded")
    time.sleep(5)
    print("   URL:", page2.url)
    print("   Notes:", len(page2.query_selector_all("section.note-item")))
    
    login_status2 = page2.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state) return 'no state';
        const user = state.user;
        if (!user) return 'no user in state';
        return {
            loggedIn: user.loggedIn,
            activated: user.activated,
            userId: user.userInfo ? user.userInfo.id : null
        };
    }""")
    print("   User state:", json.dumps(login_status2, ensure_ascii=False))

    # Check the cookies on search_result page
    print("\n4. Cookies on search_result...")
    sr_cookies = page2.context.cookies()
    print("   Total:", len(sr_cookies))
    ws = [c for c in sr_cookies if c['name'] == 'web_session']
    print("   web_session:", ws[0]['value'][:40] if ws else "NOT FOUND")

    page2.close()
    browser.close()
    print("\nDone")