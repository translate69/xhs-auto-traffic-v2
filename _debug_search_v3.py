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
    time.sleep(0.5)

    # Try page.keyboard.press instead of element press
    print("Pressing Enter via page.keyboard...")
    page.keyboard.press("Enter")
    time.sleep(5)
    print("URL after Enter:", page.url)
    notes = page.query_selector_all("section.note-item")
    print("Notes:", len(notes))

    # If still on explore, check sug-container
    if "search_result" not in page.url:
        sug_items = page.evaluate("""() => {
            const sugBox = document.querySelector('.sug-box');
            if (!sugBox) return 'no sug-box';
            const items = sugBox.querySelectorAll('li, [class*="item"]');
            return Array.from(items).map(function(i) {
                return i.className.slice(0,40) + ' txt=' + (i.textContent||'').slice(0,30);
            });
        }""")
        print("Sug items:", sug_items)

        # Check input-button
        btn_info = page.evaluate("""() => {
            const btn = document.querySelector('.input-button');
            if (!btn) return 'no input-button';
            return {
                onclick: btn.getAttribute('onclick'),
                dataHref: btn.getAttribute('data-href'),
                html: btn.innerHTML.slice(0, 300)
            };
        }""")
        print("Input button:", btn_info)

        # Try clicking the close-icon inside input-button
        close_icon = page.query_selector(".close-icon")
        print("Close icon:", close_icon)
        if close_icon:
            # Fill the search input again since clicking may have cleared it
            search_input.fill("汕尾美食")
            time.sleep(0.5)
            # Try clicking the close icon to dismiss any overlay, then press enter
            try:
                close_icon.click(timeout=2000)
            except:
                pass
            time.sleep(0.5)
            page.keyboard.press("Enter")
            time.sleep(5)
            print("URL after close-icon:", page.url)
            notes2 = page.query_selector_all("section.note-item")
            print("Notes after:", len(notes2))

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_search_v3.png")
    browser.close()
    print("Done")