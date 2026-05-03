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

    # Go to explore
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    # Get note href
    first_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("1. First href:", first_href[:80])

    # Test: what does page.title() show RIGHT after we navigate?
    # Try a different approach - use page.goto with the full URL
    print("\n2. Using page.goto with full URL...")
    page2 = context.new_page()
    full_url = "https://www.xiaohongshu.com" + first_href
    page2.goto(full_url, wait_until="domcontentloaded")
    time.sleep(3)
    print("   page2.url:", page2.url)
    print("   page2.title:", page2.title()[:60])

    # Now try fresh context with same cookies
    print("\n3. Fresh context, same cookies...")
    context2 = browser.new_context()
    context2.add_cookies(cookies)
    page3 = context2.new_page()
    page3.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    
    first_href3 = page3.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    
    page3.goto("https://www.xiaohongshu.com" + first_href3, wait_until="domcontentloaded")
    time.sleep(3)
    print("   page3.url:", page3.url)
    print("   page3.title:", page3.title()[:60])
    
    page3.close()
    page2.close()

    # Try: check if it's a redirect issue
    print("\n4. Monitoring console messages...")
    console_messages = []
    page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text[:100]}"))
    
    page4 = context.new_page()
    page4.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(2)
    
    page4.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        if (link) link.click();
    }""")
    time.sleep(5)
    
    print("   URL:", page4.url)
    print("   Title:", page4.title()[:60])
    print("   Console messages:", console_messages[:10])
    
    page4.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_console_click.png")
    page4.close()

    browser.close()
    print("\nDone")