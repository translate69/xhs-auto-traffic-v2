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

    # Try search_result with extra headers that might be needed
    print("1. Direct to search_result (no extra setup)...")
    page.goto("https://www.xiaohongshu.com/search_result?keyword=汕尾美食&type=51", wait_until="domcontentloaded")
    time.sleep(2)
    print(f"   URL: {page.url}")
    body = page.text_content("body") or ""
    print(f"   Body snippet: {body[:300]}")
    notes = page.query_selector_all("section.note-item")
    print(f"   Notes: {len(notes)}")
    
    # Check what section elements exist
    sections = page.query_selector_all("section")
    print(f"   All sections: {len(sections)}")
    for s in sections[:5]:
        try:
            print(f"     class={s.get_attribute('class')}")
        except:
            pass

    # Check if there's a content area
    content = page.query_selector(".search-result, .note-list, .content, main, [class*='list']")
    if content:
        print(f"   Content area class: {content.get_attribute('class')}")

    # Check for any div with note in class
    note_divs = page.query_selector_all("[class*='note']")
    print(f"   divs with 'note' in class: {len(note_divs)}")
    for d in note_divs[:3]:
        try:
            print(f"     {d.get_attribute('class')}")
        except:
            pass

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_sr_inspect.png")

    # Now try with additional anti-detection headers
    print("\n2. Try with extra headers...")
    page2 = context.new_page()
    
    # Set extra HTTP headers that might help
    page2.set_extra_http_headers({
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    })
    
    page2.goto("https://www.xiaohongshu.com/search_result?keyword=汕尾美食&type=51", wait_until="domcontentloaded")
    time.sleep(5)
    print(f"   URL: {page2.url}")
    body2 = page2.text_content("body") or ""
    print(f"   Body snippet: {body2[:300]}")
    notes2 = page2.query_selector_all("section.note-item")
    print(f"   Notes: {len(notes2)}")
    page2.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_sr_headers.png")

    browser.close()
    print("\nDone")