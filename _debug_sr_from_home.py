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

    print("=== Test: From homepage search, navigate to search_result ===")

    # Go to homepage and search
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    print("1. Homepage URL:", page.url)

    page.fill("#search-input", "汕尾美食")
    time.sleep(0.3)
    page.keyboard.press("Enter")
    time.sleep(5)
    print("2. After search URL:", page.url)
    print("   Notes:", len(page.query_selector_all("section.note-item")))
    print("   Has filter:", page.query_selector(".filter") is not None)

    # Now navigate to search_result from this page
    print("\n3. Navigate to search_result...")
    page.goto("https://www.xiaohongshu.com/search_result?keyword=%E6%B1%95%E5%B0%BE%E7%BE%8E%E9%A3%9F", wait_until="domcontentloaded")
    time.sleep(5)
    print("   URL:", page.url)
    print("   Notes:", len(page.query_selector_all("section.note-item")))
    print("   Has filter:", page.query_selector(".filter") is not None)

    # Check login status
    login_check = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.user) return 'no user state';
        return {
            loggedIn: state.user.loggedIn,
            activated: state.user.activated,
            userInfo: state.user.userInfo ? {
                id: state.user.userInfo.id,
                nickname: state.user.userInfo.nickname
            } : null
        };
    }""")
    print("   Login:", json.dumps(login_check, ensure_ascii=False))

    # Try with different wait
    page.goto("https://www.xiaohongshu.com/search_result?keyword=%E6%B1%95%E5%B0%BE%E7%BE%8E%E9%A3%9F", wait_until="networkidle", timeout=30000)
    time.sleep(5)
    print("\n4. With networkidle:")
    print("   URL:", page.url)
    print("   Notes:", len(page.query_selector_all("section.note-item")))
    print("   Has filter:", page.query_selector(".filter") is not None)

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_sr_from_home.png")
    browser.close()
    print("\nDone")