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

    print("=== Test: Use new context (no cookies) - see if we can at least get notes ===")

    # Use a fresh context with no cookies
    context2 = browser.new_context()
    page2 = context2.new_page()
    page2.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    print("1. Fresh context, no cookies:")
    print("   URL:", page2.url)
    print("   Notes:", len(page2.query_selector_all("section.note-item")))
    page2.close()

    # Now use the SAME context but intercept the note detail URL
    print("\n2. Test with same context, intercept note URL...")
    page3 = context.new_page()

    # First go to explore
    page3.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    print("   Explore URL:", page3.url)

    # Get first note href
    note_href = page3.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("   Note href:", note_href[:80] if note_href else None)

    # Instead of goto, simulate the in-page navigation
    # By calling window.history.pushState and then waiting for the page to update
    print("\n3. Try using page.route to intercept and handle...")
    
    # Route the note URL and see what happens
    def handle_route(route):
        url = route.request.url
        print(f"   Route: {url[:80]}")
        
        # Check if this is a note detail request
        if '/explore/' in url or '/note/' in url:
            # Try to continue normally
            route.continue()
        else:
            route.continue()
    
    page3.route("**/explore/**", handle_route)
    
    page3.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        if (link) link.click();
    }""")
    time.sleep(5)
    print("   After click URL:", page3.url)
    print("   After click title:", page3.title()[:60])

    page3.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_route_click.png")

    # Now test: what if we use context.new_page() and navigate to explore, then click note?
    print("\n4. Fresh page in same context, click note...")
    page4 = context.new_page()
    page4.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    
    note_href4 = page4.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("   href:", note_href4[:80])
    
    # Instead of page.goto, try clicking with a specific approach
    note_element = page4.query_selector('section.note-item a.cover.mask')
    if note_element:
        print("   Found note element, clicking via JS...")
        page4.evaluate("""() => {
            document.querySelector('section.note-item a.cover.mask').click();
        }""")
        time.sleep(5)
        print("   URL:", page4.url)
        print("   Title:", page4.title()[:60])
        
        if "/login" in page4.url:
            print("   -> LOGIN")
        else:
            desc = page4.query_selector("#detail-desc")
            print("   Has #detail-desc:", desc is not None)
    
    page4.close()
    page3.close()
    browser.close()
    print("\nDone")