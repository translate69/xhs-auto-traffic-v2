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
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)

    # Get the search input
    search_input = page.wait_for_selector("#search-input", timeout=10000)

    # Check nearby buttons/elements
    print("=== 搜索框附近元素 ===")
    # Get bounding box
    box = search_input.bounding_box()
    print(f"搜索框位置: {box}")

    # Search for nearby clickable elements
    # The search form might have a submit button
    submit_btn = page.query_selector("button[type='submit']")
    print(f"button[type=submit]: {submit_btn}")

    # Look at parent form
    parent = page.evaluate("""() => {
        const inp = document.querySelector('#search-input');
        if (!inp) return 'no input';
        const form = inp.closest('form');
        if (!form) return 'no form, parent=' + inp.parentElement.tagName;
        return {
            tag: form.tagName,
            action: form.action || 'no-action',
            children: Array.from(form.querySelectorAll('*')).map(el => el.tagName + '.' + el.className.slice(0,30))
        };
    }""")
    print(f"Form info: {submit_btn}")

    # Check the search dropdown suggestions div
    print("\n=== 所有 input 元素 ===")
    inputs = page.query_selector_all("input")
    for inp in inputs:
        try:
            print(f"  {inp.get_attribute('name') or 'unnamed'}: type={inp.get_attribute('type')} id={inp.get_attribute('id')} class={inp.get_attribute('class')}")
        except:
            pass

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_homepage_search.png")
    print("\n截图已保存")
    browser.close()