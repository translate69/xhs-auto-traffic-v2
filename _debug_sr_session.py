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

    # Test if search_result works when coming from same-session explore page
    print("1. Go to explore (session established)...")
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    print(f"   URL: {page.url}")

    # Now navigate to search_result using page.goto (not same-page navigation)
    print("\n2. Now goto search_result...")
    page.goto("https://www.xiaohongshu.com/search_result?keyword=汕尾美食&type=51", wait_until="domcontentloaded")
    time.sleep(5)
    print(f"   URL: {page.url}")
    body = page.text_content("body") or ""
    print(f"   Body snippet: {body[:200]}")
    
    notes = page.query_selector_all("section.note-item")
    print(f"   Notes: {len(notes)}")

    # Try via click on search result link
    print("\n3. Test page.evaluate JS routing...")
    page2 = context.new_page()
    page2.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(2)

    result = page2.evaluate("""() => {
        // Try to programmatically trigger search navigation
        // Check if there's a search API we can call
        return {
            url: window.location.href,
            search_available: typeof window.__INITIAL_STATE__ !== 'undefined' || typeof window.__NUXT__ !== 'undefined'
        };
    }""")
    print(f"   Explore state: {result}")

    # Check cookies on current context
    print("\n4. Cookie check on context...")
    ctx_cookies = context.cookies()
    print(f"   Total cookies: {len(ctx_cookies)}")
    for c in ctx_cookies[:5]:
        print(f"   {c['name']}={c['value'][:30]}...")

    browser.close()
    print("\nDone")