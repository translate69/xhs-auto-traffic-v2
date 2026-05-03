import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
import time
import json
from playwright.sync_api import sync_playwright

result = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    cookies = json.load(open(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json"))
    context.add_cookies(cookies)

    page = context.new_page()
    page.set_default_timeout(15000)

    # From homepage search to explore
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    page.fill("#search-input", "汕尾美食")
    time.sleep(0.3)
    page.keyboard.press("Enter")
    time.sleep(5)

    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : '';
    }""")
    print("Note href:", note_href[:80])

    page.evaluate("""() => {
        document.querySelector('section.note-item a.cover.mask').click();
    }""")
    time.sleep(5)
    print("URL:", page.url)

    # Get body text
    body_text = page.evaluate("document.body.textContent.replace(/\\s+/g, ' ').trim()")
    result["body_text"] = body_text[:500]
    result["body_length"] = len(body_text)

    # Check HTML
    html = page.content()
    # Check if there's any note-related content
    result["has_detail_desc"] = 'detail-desc' in html or 'detail-desc' in html.lower()
    result["has_note_content"] = 'note-content' in html or 'note-content' in html.lower()
    result["has_login"] = 'login' in html.lower() or '登录' in html

    # Try to find the actual content
    content_check = page.evaluate("""() => {
        // Get all visible text elements
        const body = document.body;
        
        // Look for non-empty text content that looks like note content
        const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT);
        const textNodes = [];
        let node;
        while (node = walker.nextNode()) {
            const text = node.textContent.trim();
            if (text.length > 20) {
                textNodes.push({
                    tag: node.parentElement?.tagName,
                    class: node.parentElement?.className?.slice(0, 50),
                    text: text.slice(0, 100)
                });
            }
        }
        
        return textNodes.slice(0, 20);
    }""")
    result["text_nodes"] = content_check

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_clicked_note.png")
    browser.close()

with open(r"E:\translate\claw\xhs-auto-traffic-v2\_debug_clicked_body.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("Done")