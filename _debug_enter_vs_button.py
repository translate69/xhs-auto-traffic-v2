import sys
sys.path.insert(0, "E:/translate/claw/xhs-auto-traffic-v2")
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    import json
    with open("E:/translate/claw/xhs-auto-traffic-v2/xhs_cookies.json", encoding="utf-8") as f:
        cookies = json.load(f)
    context.add_cookies(cookies)

    page = context.new_page()

    # Strategy: When on explore page with search input, what triggers navigation to search_result?
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    print(f"1. Home URL: {page.url}")

    search_input = page.wait_for_selector("#search-input", timeout=10000)
    search_input.fill("汕尾美食")
    print("2. Filled")

    # Check: after filling, does an autocomplete/suggestion appear?
    time.sleep(1)
    suggestion_box = page.query_selector(".search-suggest, [class*='suggest-list'], [class*='search-results'], ul[class*='search']")
    print(f"   Suggestion box: {suggestion_box}")

    # Check all elements with "search" in class within the nav area
    search_area = page.evaluate("""() => {
        const inp = document.querySelector('#search-input');
        const parent = inp ? inp.closest('div[class*="search"], nav, .nav-header') : null;
        if (!parent) return 'no parent found';
        const allEls = parent.querySelectorAll('[class*="search"], button, a');
        return Array.from(allEls).map(el => el.tagName + ' class=' + el.className.slice(0,40) + ' href=' + (el.href || '').slice(0,50));
    }""")
    print(f"   Search area elements: {search_area[:5]}")

    # Now press Enter - but let's first try to find the search icon button
    search_icon = page.query_selector("[class*='search-icon'], [class*='magnifier'], i[class*='search']")
    print(f"\n3. Search icon elements: {search_icon}")

    # Get all buttons in the search area
    buttons = page.evaluate("""() => {
        const inp = document.querySelector('#search-input');
        const form = inp ? inp.closest('.search-bar, .search-wrapper, [class*=\"search-bar\"]') : null;
        if (!form) return 'no form found';
        return Array.from(form.querySelectorAll('button, a, [class*=\"icon\"]')).map(el => el.tagName + ' cls=' + el.className.slice(0,30) + ' txt=' + (el.textContent||'').slice(0,20));
    }""")
    print(f"   Buttons in search bar: {buttons}")

    # Try clicking the search icon if found
    if search_icon:
        try:
            search_icon.click(timeout=3000)
            print("   Clicked search icon!")
            time.sleep(5)
            print(f"   URL after icon click: {page.url}")
        except Exception as e:
            print(f"   Icon click failed: {e}")

    # Now press Enter
    search_input.press("Enter")
    time.sleep(5)
    print(f"\n4. After Enter URL: {page.url}")
    notes = page.query_selector_all("section.note-item")
    print(f"   section.note-item count: {len(notes)}")

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_explore_search.png")

    # Try direct navigation to search_result for comparison
    page2 = context.new_page()
    page2.goto("https://www.xiaohongshu.com/search_result?keyword=汕尾美食&type=51", wait_until="domcontentloaded")
    time.sleep(8)
    print(f"\n5. Direct search_result URL: {page2.url}")
    notes2 = page2.query_selector_all("section.note-item")
    print(f"   section.note-item count: {len(notes2)}")

    # Check for filter element
    filter_el = page2.query_selector(".filter")
    print(f"   .filter element: {filter_el}")
    page2.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_direct_sr.png")

    browser.close()
    print("\nDone")