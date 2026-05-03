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

    print("=== Test: Compare click methods ===")

    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("1. Note href:", note_href[:80])

    # Test JS click
    print("\n2. JS click test...")
    page.evaluate("""() => {
        document.querySelector('section.note-item a.cover.mask').click();
    }""")
    time.sleep(5)
    print("   URL:", page.url)
    print("   Title:", page.title()[:60])
    
    js_click_result = "/explore/" in page.url and "xsec_token" in page.url
    print("   JS click navigated to note:", js_click_result)

    # Now go back to explore
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    # Test locator.click with force
    print("\n3. Locator click(force=True) test...")
    page.locator("section.note-item a.cover.mask").first.click(force=True)
    time.sleep(5)
    print("   URL:", page.url)
    print("   Title:", page.title()[:60])
    
    locator_result = "/explore/" in page.url and "xsec_token" in page.url
    print("   locator click navigated to note:", locator_result)

    # Go back to explore again
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    # Test locator.click WITHOUT force
    print("\n4. Locator click without force (normal)...")
    try:
        page.locator("section.note-item a.cover.mask").first.click(timeout=5000)
        time.sleep(5)
        print("   URL:", page.url)
        print("   Title:", page.title()[:60])
    except Exception as e:
        print("   Error:", e)

    browser.close()
    print("\nDone")