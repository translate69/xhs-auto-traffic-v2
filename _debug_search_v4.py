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
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    print("Homepage URL:", page.url)

    search_input = page.wait_for_selector("#search-input", timeout=10000)
    search_input.fill("汕尾美食")
    time.sleep(1)

    # Check sug-box suggestions
    sug_items = page.evaluate("""() => {
        const items = document.querySelectorAll('.sug-item');
        return Array.from(items).map(function(i) {
            return 'txt=' + (i.textContent||'').slice(0,40);
        });
    }""")
    print("Sug items:", sug_items)

    # Click the first sug-item and see where it navigates
    first_sug = page.query_selector(".sug-item")
    if first_sug:
        print("Clicking first sug-item...")
        first_sug.click()
        time.sleep(5)
        print("URL after clicking sug-item:", page.url)
        notes = page.query_selector_all("section.note-item")
        print("Notes:", len(notes))
        filter_el = page.query_selector(".filter")
        print("Has filter:", filter_el is not None)

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_click_sug.png")
    browser.close()
    print("Done")