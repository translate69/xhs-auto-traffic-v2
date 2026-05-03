import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
import time
import json
import re
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    cookies = json.load(open(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json"))
    context.add_cookies(cookies)

    page = context.new_page()
    page.set_default_timeout(15000)

    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("1. Note href:", note_href[:80])

    page.evaluate("""() => {
        document.querySelector('section.note-item a.cover.mask').click();
    }""")
    time.sleep(5)
    print("2. After click URL:", page.url)

    content_elements = page.evaluate("""() => {
        const selectors = ['#detail-desc', '.note-detail', '.note-content', '[class*="detail"]', '[class*="content"]'];
        const result = {};
        for (const sel of selectors) {
            const el = document.querySelector(sel);
            result[sel] = el ? el.textContent.slice(0, 100) : null;
        }
        return result;
    }""")
    print("3. Content elements:", json.dumps(content_elements, ensure_ascii=False))

    title = page.title()
    print("4. Page title:", title)

    body_text = page.evaluate("document.body.textContent || ''")
    cleaned = re.sub(r'\s+', ' ', body_text).strip()
    print("5. Body text preview:", cleaned[:200])

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_explore_note_page.png")
    browser.close()
    print("\nDone")