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

    print("=== 新登录测试 ===")

    # Step 1: Go to Xiaohongshu and manually trigger login flow via QR code
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    print(f"1. On: {page.url}")

    # Step 2: Try to trigger the QR code login modal
    # Look for a login button and click it
    login_btn = page.query_selector('a[href*="login"], .login-btn, [class*="login"]')
    print(f"2. Login buttons: {login_btn}")

    # Look at the page to find login options
    page_info = page.evaluate("""() => {
        const btns = document.querySelectorAll('button, a, [class*="login"], [class*="sign"]');
        const relevant = [];
        for (const btn of btns) {
            const text = (btn.textContent || '').trim();
            if (text.includes('登录') || text.includes('login') || text.includes('登录')) {
                relevant.push({
                    text: text.slice(0, 30),
                    class: btn.className,
                    tag: btn.tagName,
                    href: btn.getAttribute('href') || ''
                });
            }
        }
        return {
            url: window.location.href,
            relevantBtns: relevant.slice(0, 5),
            hasQR: !!document.querySelector('[class*="qr"], [class*="qrcode"], canvas'),
            bodyText: document.body.textContent.replace(/\s+/g, ' ').trim().slice(0, 300)
        };
    }""")
    print(f"3. Page info:", json.dumps(page_info, ensure_ascii=False, indent=2))

    # Step 3: Check if we can access user info
    user_state = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.user) return 'no user state';
        
        const user = state.user;
        const isLoggedIn = user.loggedIn || user.activated;
        const userInfo = user.userInfo;
        
        return {
            loggedIn: isLoggedIn,
            activated: user.activated,
            hasUserInfo: !!userInfo,
            userId: userInfo ? (userInfo.id || userInfo.userId) : null,
            nickname: userInfo ? userInfo.nickname : null,
            avatar: userInfo ? (userInfo.avatar || userInfo.avatarUrl) : null
        };
    }""")
    print(f"\n4. User state: {json.dumps(user_state, ensure_ascii=False, indent=2)}")

    # Step 4: Check the current web_session
    current_cookies = page.context.cookies()
    ws = [c for c in current_cookies if c['name'] == 'web_session']
    print(f"\n5. Current web_session: {ws[0]['value'][:50] if ws else 'NOT FOUND'}")
    print(f"   Cookie count: {len(current_cookies)}")

    # Step 5: Try going to a note directly
    print("\n6. Try direct note access...")
    page2 = context.new_page()
    page2.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    
    note_href = page2.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    
    if note_href:
        # Direct navigation
        note_url = "https://www.xiaohongshu.com" + note_href
        page3 = context.new_page()
        page3.goto(note_url, wait_until="domcontentloaded")
        time.sleep(3)
        print(f"   Direct URL: {note_url[:80]}")
        print(f"   Direct result: {page3.url}")
        if "/login" in page3.url:
            print("   -> LOGIN PAGE")
        page3.close()
    
    page2.close()

    # Step 6: Update cookies with fresh session
    print("\n7. Current cookies:")
    for c in current_cookies:
        if c['name'] in ['web_session', 'a1', 'galaxy_creator_session_id']:
            print(f"   {c['name']}: {c['value'][:50]}... (domain={c['domain']})")

    browser.close()
    print("\nDone")