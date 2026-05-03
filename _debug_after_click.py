import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
import time
from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    cookies = json.load(open(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json"))
    context.add_cookies(cookies)

    page = context.new_page()
    page.set_default_timeout(15000)

    print("1. Go to explore page...")
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    print("   URL:", page.url)
    print("   Notes:", len(page.query_selector_all("section.note-item")))

    # Get a note href
    first_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("   First href:", first_href[:80] if first_href else None)

    # Click the note via JS
    print("\n2. Click note via JS...")
    page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        if (link) link.click();
    }""")
    time.sleep(5)
    print("   URL:", page.url)
    print("   Title:", page.title()[:60])

    if "/note/" in page.url or "/explore/" in page.url:
        print("   -> On note page!")
        # Get the note detail content
        content = page.evaluate("""() => {
            const desc = document.querySelector('#detail-desc');
            const title = document.querySelector('.title-container .title span') || document.querySelector('h1');
            return {
                detail_desc: desc ? desc.textContent.slice(0, 100) : 'NOT FOUND',
                title: title ? title.textContent.slice(0, 50) : 'NOT FOUND',
                full_html: document.body.innerHTML.slice(0, 500)
            };
        }""")
        print("   Content:", content)

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_after_click.png")
    browser.close()
    print("\nDone")