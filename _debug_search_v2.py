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
    print(f"URL: {page.url}")

    # Test: Try multiple approaches to trigger search navigation
    search_input = page.wait_for_selector("#search-input", timeout=10000)

    # Approach 1: Click input → wait → type slowly → wait → press Enter
    print("\n1. Click → type slowly → Enter...")
    search_input.click(timeout=5000)
    time.sleep(1)
    search_input.type("汕尾美食", delay=200)
    time.sleep(1)
    search_input.press("Enter")
    time.sleep(5)
    print(f"   URL: {page.url}")
    notes1 = page.query_selector_all("section.note-item")
    print(f"   Notes: {len(notes1)}")

    # If not on search_result, try approach 2: evaluate JavaScript to trigger navigation
    if "search_result" not in page.url:
        print("\n2. Try JS navigation...")
        page.evaluate("""() => {
            const inp = document.querySelector('#search-input');
            // Check if there's a Vue/jQuery event we can trigger
            const event = new Event('input', { bubbles: true });
            inp.dispatchEvent(event);
        }""")
        time.sleep(1)
        search_input.press("Enter")
        time.sleep(5)
        print(f"   URL after JS: {page.url}")
        notes2 = page.query_selector_all("section.note-item")
        print(f"   Notes: {len(notes2)}")

    # Approach 3: Try navigating via URL with proper session handling
    if "search_result" not in page.url:
        print("\n3. Check if maybe search_result just has 0 results for this keyword...")
        # Check what keyword is being searched
        current_kw = page.evaluate("() => { const inp = document.querySelector('#search-input'); return inp ? inp.value : 'no input'; }")
        print(f"   Current input value: {current_kw}")
        
        # Check if maybe we need to use different URL format
        page2 = context.new_page()
        page2.goto("https://www.xiaohongshu.com/search_result?keyword=%E6%B1%95%E5%B0%BE%E7%BE%8E%E9%A3%9F&type=51&source=web_explore_feed", wait_until="domcontentloaded")
        time.sleep(5)
        print(f"   Alternative URL: {page2.url}")
        notes3 = page2.query_selector_all("section.note-item")
        print(f"   Notes with alt URL: {len(notes3)}")
        page2.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_sr_alt_url.png")
        page2.close()

    # Check the sug-container for search suggestions
    print("\n4. Check sug-container content...")
    sug_html = page.evaluate("""() => {
        const sug = document.querySelector('.sug-container-wrapper');
        return sug ? sug.innerHTML.slice(0, 500) : 'not found';
    }""")
    print(f"   sug-container HTML: {sug_html}")

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_search_result.png")
    browser.close()
    print("\nDone")