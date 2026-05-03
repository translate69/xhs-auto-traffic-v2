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

    # Monitor requests and responses
    all_requests = []
    def on_request(req):
        all_requests.append({"url": req.url[:100], "method": req.method})

    page.on("request", on_request)

    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    print("Homepage URL:", page.url)

    search_input = page.wait_for_selector("#search-input", timeout=10000)
    search_input.fill("汕尾美食")
    time.sleep(1)

    # Check the sug-box structure - what happens when sug-item is clicked
    sug_html = page.evaluate("""() => {
        const sugBox = document.querySelector('.sug-box');
        if (!sugBox) return 'no sug-box';
        const firstItem = sugBox.querySelector('.sug-item');
        if (!firstItem) return 'no sug-item';
        return {
            html: sugBox.innerHTML.slice(0, 800),
            firstItemClass: firstItem.className,
            firstItemTag: firstItem.tagName,
            firstItemHTML: firstItem.innerHTML.slice(0, 200)
        };
    }""")
    print("\nSug-box HTML:")
    print(sug_html)

    # Check if the sug-item has a data attribute or link
    sug_attr = page.evaluate("""() => {
        const items = document.querySelectorAll('.sug-item');
        if (!items.length) return 'no items';
        const first = items[0];
        const allAttrs = {};
        for (const attr of first.attributes) {
            allAttrs[attr.name] = attr.value;
        }
        return {
            tag: first.tagName,
            class: first.className,
            href: first.getAttribute('href'),
            onclick: first.getAttribute('onclick'),
            dataHref: first.getAttribute('data-href'),
            dataUrl: first.getAttribute('data-url'),
            innerHTML: first.innerHTML.slice(0, 300)
        };
    }""")
    print("\nSug-item attributes:", sug_attr)

    # Now check: when we press Enter on the search input, does the page navigate via JS?
    # Let's check the current page URL after entering keyword
    print("\nCurrent URL before Enter:", page.url)

    # Try using ArrowDown to select a sug-item, then Enter to confirm
    print("\nTrying ArrowDown + Enter...")
    search_input.press("ArrowDown")
    time.sleep(0.5)

    # Check which element is focused/active
    focused = page.evaluate("() => document.activeElement ? document.activeElement.className : 'none'")
    print("Focused element class:", focused)

    search_input.press("Enter")
    time.sleep(5)
    print("\nURL after ArrowDown+Enter:", page.url)
    notes = page.query_selector_all("section.note-item")
    print("Notes:", len(notes))

    # Try navigating via URL with xsec_token from existing explore page
    print("\n\n=== Now testing search_result URL format ===")
    page2 = context.new_page()
    page2.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)

    # Check what the search API returns when called directly
    api_url = "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes?keyword=%E6%B1%95%E5%B0%BE%E7%BE%8E%E9%A3%9F&offset=0&limit=20&sort=0&note_type=0&ext_flags=&image_formats=jpg,webp,avif"
    resp = page2.request.get(api_url)
    print("API status:", resp.status)
    print("API url:", resp.url)
    if resp.status == 200:
        try:
            data = resp.json()
            print("API response:", str(data)[:500])
        except:
            print("Not JSON:", resp.text()[:200])
    else:
        print("API failed:", resp.status)
        print("Response headers:", dict(resp.headers))

    browser.close()
    print("\nDone")