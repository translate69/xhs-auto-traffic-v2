import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
import time
import json
from playwright.sync_api import sync_playwright

result = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    cookies = json.load(open(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json"))
    context.add_cookies(cookies)

    page = context.new_page()
    page.set_default_timeout(20000)

    # Go to explore via homepage
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    page.fill("#search-input", "汕尾美食")
    time.sleep(0.3)
    page.keyboard.press("Enter")
    time.sleep(5)

    # Now we're on /explore - click a note and wait for navigation
    print("1. On explore, click note and wait for navigation...")
    first_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("   First href:", first_href[:80] if first_href else None)

    # Use page.click with wait_for_navigation instead of JS click
    # First, set up network monitoring
    def handle_response(response):
        url = response.url
        if 'detail' in url.lower() or 'note' in url.lower():
            print(f"   [NET] {response.status} {url[:80]}")

    page.on("response", handle_response)

    # Click and wait for URL change
    print("\n2. Click note with waitForNavigation...")
    
    # Start waiting for navigation BEFORE clicking
    # We want to detect when URL changes to a note detail page
    promise = page.wait_for_url("**/explore/**", timeout=10000)
    
    # Do the click via JS (to bypass reds-mask)
    page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        if (link) link.click();
    }""")
    
    # Wait for the URL to match
    try:
        result_url = promise.result()
        print("   Navigated to:", result_url)
        print("   Title:", page.title()[:60])
        
        # Check if we're on the note detail page
        if "/explore/" in page.url and "xsec_token" in page.url:
            print("   -> URL has xsec_token, checking content...")
            # Wait for content to load
            time.sleep(3)
            
            content_check = page.evaluate("""() => {
                const desc = document.querySelector('#detail-desc');
                const interact = document.querySelector('.interact-container');
                const title = document.querySelector('.title-container');
                return {
                    hasDetailDesc: !!desc,
                    detailText: desc ? desc.textContent.slice(0, 100) : null,
                    hasInteract: !!interact,
                    hasTitle: !!title,
                    bodyText: document.body.textContent.slice(0, 200)
                };
            }""")
            print("   Content check:", json.dumps(content_check, ensure_ascii=False))
    except Exception as e:
        print("   waitForURL error:", e)
        print("   Current URL:", page.url)

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_click_nav.png")
    browser.close()
    print("\nDone")