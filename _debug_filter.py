import sys
sys.path.insert(0, "E:/translate/claw/xhs-auto-traffic-v2")
import config
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport=config.VIEWPORT)

    import json
    with open("E:/translate/claw/xhs-auto-traffic-v2/xhs_cookies.json", encoding="utf-8") as f:
        cookies = json.load(f)
    context.add_cookies(cookies)

    page = context.new_page()

    # Homepage search via fill+enter
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    search_input = page.wait_for_selector("#search-input", timeout=10000)
    search_input.fill("汕尾去哪吃")
    search_input.press("Enter")

    # Wait for navigation or note items
    page.wait_for_timeout(8000)
    print(f"URL after search: {page.url}")
    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/screenshot_homepage_search.png")

    # Check what elements exist
    for sel in ["section.note-item", "[class*='note-item']", ".filter", ".filter-panel"]:
        count = page.locator(sel).count()
        if count > 0:
            print(f"Found {sel}: {count} elements")
            # Try to get first element text
            try:
                el = page.locator(sel).first
                print(f"  Text: {el.inner_text()[:100]}")
            except:
                pass
        else:
            print(f"Not found: {sel}")

    # Check if page has any content at all
    body_text = page.locator("body").inner_text()
    print(f"Body text (first 200): {body_text[:200]}")

    page.wait_for_timeout(5000)
    browser.close()