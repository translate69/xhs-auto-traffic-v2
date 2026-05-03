import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
import time
import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=['--disable-blink-features=AutomationControlled']
    )
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )
    
    # Inject script to avoid webdriver detection
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => false});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
        Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
    """)

    page = context.new_page()
    page.set_default_timeout(60000)

    print("=== Login to Xiaohongshu ===")
    
    # Go to login page
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    print(f"1. URL: {page.url}")
    
    # Check if already logged in
    if "/login" in page.url:
        print("2. Not logged in, need to login...")
        
        # Look for QR code login option
        qr_login = page.query_selector('img[src*="qr"], .qrcode, [class*="qr"]')
        print(f"   QR login element: {qr_login}")
        
        # Try to find QR code image
        qr_info = page.evaluate("""() => {
            // Look for any image that might be a QR code
            const imgs = document.querySelectorAll('img');
            const qrImgs = [];
            for (const img of imgs) {
                const src = img.src || '';
                if (src.includes('qr') || src.includes('code') || src.includes('login')) {
                    qrImgs.push({
                        src: src.slice(0, 100),
                        class: img.className,
                        width: img.width,
                        height: img.height
                    });
                }
            }
            
            // Also check for login form elements
            const hasPhoneLogin = !!document.querySelector('[class*="phone"], [class*="mobile"]');
            const hasQRLogin = !!document.querySelector('[class*="qr"], [class*="scan"]');
            
            return { qrImgs, hasPhoneLogin, hasQRLogin };
        }""")
        print(f"   QR info: {qr_info}")
        
        print("\n3. Please scan QR code or login manually...")
        print("   Waiting 120 seconds for login...")
        
        # Wait for login to complete (user scans QR or enters credentials)
        try:
            page.wait_for_url(lambda url: "/explore" in url and "/login" not in url, timeout=120000)
            print(f"   Logged in! URL: {page.url}")
        except Exception as e:
            print(f"   Wait timeout: {e}")
            page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_login_state.png")
            print("   Screenshot saved")
    
    # Get cookies
    cookies = context.cookies()
    print(f"\n4. Cookies: {len(cookies)}")
    ws = [c for c in cookies if c['name'] == 'web_session']
    print(f"   web_session: {ws[0]['value'][:50] if ws else 'NOT FOUND'}...")
    print(f"   web_session domain: {ws[0]['domain'] if ws else 'N/A'}")
    
    # Test: can we access a note detail page?
    print("\n5. Test note detail access...")
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    
    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    
    if note_href:
        page2 = context.new_page()
        note_url = "https://www.xiaohongshu.com" + note_href
        page2.goto(note_url, wait_until="domcontentloaded")
        time.sleep(3)
        print(f"   Note URL: {note_url[:80]}")
        print(f"   Result URL: {page2.url}")
        
        if "/login" in page2.url:
            print("   -> LOGIN PAGE (cookie still not working)")
        else:
            print("   -> NOTE PAGE (cookie works!)")
            desc = page2.query_selector("#detail-desc")
            print(f"   Has detail-desc: {desc is not None}")
        
        page2.close()
    
    # Save cookies
    with open(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies_new.json", "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)
    print(f"\n6. Saved {len(cookies)} cookies to xhs_cookies_new.json")

    browser.close()
    print("\nDone")