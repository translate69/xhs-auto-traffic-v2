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

    # Go to search_result
    page.goto("https://www.xiaohongshu.com/search_result?keyword=汕尾美食&type=51", wait_until="domcontentloaded")
    time.sleep(15)

    # Check the full feeds-page HTML
    feeds_html = page.evaluate("""() => {
        const el = document.querySelector('.feeds-page');
        return el ? el.innerHTML.slice(0, 1000) : 'not found';
    }""")
    print("feeds-page HTML:")
    print(feeds_html)

    # Check search-layout HTML
    search_layout_html = page.evaluate("""() => {
        const el = document.querySelector('.search-layout');
        return el ? el.innerHTML.slice(0, 2000) : 'not found';
    }""")
    print("\nsearch-layout HTML:")
    print(search_layout_html)

    # Check all section elements (even outside note-item)
    all_sections = page.query_selector_all("section")
    print(f"\nAll sections: {len(all_sections)}")
    for s in all_sections[:5]:
        try:
            print(f"  class={s.get_attribute('class')}")
        except:
            pass

    # Check for any note-related elements
    note_related = page.evaluate("""() => {
        const results = {
            noteItems: document.querySelectorAll('[class*="note-item"]').length,
            allDivs: document.querySelectorAll('div').length,
            bodyChildren: document.body.children.length
        };
        return results;
    }""")
    print(f"\nNote-related elements: {note_related}")

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_sr_feeds_page.png")
    browser.close()
    print("\nDone")