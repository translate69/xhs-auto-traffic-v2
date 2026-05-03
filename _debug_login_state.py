import sys
sys.path.insert(0, "E:/translate/claw/xhs-auto-traffic-v2")
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    import json
    cookies = json.load(open(r'E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json'))
    context.add_cookies(cookies)

    page = context.new_page()

    print("1. Check explore page...")
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    print(f"   URL: {page.url}")

    login_state_explore = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state) return 'no state';
        return {
            hasLogin: 'login' in state,
            loginType: typeof state.login,
            loginKeys: state.login ? Object.keys(state.login).slice(0, 5) : 'no login'
        };
    }""")
    print(f"   Explore login state: {login_state_explore}")

    print("\n2. Check search_result page...")
    page2 = context.new_page()
    page2.goto("https://www.xiaohongshu.com/search_result?keyword=汕尾美食&type=51", wait_until="domcontentloaded")
    time.sleep(5)
    print(f"   URL: {page2.url}")

    login_state_sr = page2.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state) return 'no state';
        return {
            hasLogin: 'login' in state,
            loginType: typeof state.login,
        };
    }""")
    print(f"   search_result login state: {login_state_sr}")

    # Check if the page shows login-only content (no actual search results)
    page_text = page2.text_content("body") or ""
    print(f"\n3. Page text preview: {page_text[:300]}")

    # Check cookies on search_result context
    print("\n4. Cookies on search_result page...")
    page2_cookies = page2.context.cookies()
    print(f"   Total cookies: {len(page2_cookies)}")
    for c in page2_cookies:
        if c['name'] in ['web_session', 'access-token', 'a1', 'webId']:
            print(f"   {c['name']}={c['value'][:30]}...")

    page2.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_sr_check.png")
    browser.close()
    print("\nDone")