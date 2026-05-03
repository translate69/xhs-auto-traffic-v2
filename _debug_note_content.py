import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
import time
import json
from playwright.sync_api import sync_playwright

result_data = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    cookies = json.load(open(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json"))
    context.add_cookies(cookies)

    page = context.new_page()
    page.set_default_timeout(20000)

    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    result_data["url"] = page.url

    note_info = page.evaluate("""() => {
        const notes = document.querySelectorAll('section.note-item');
        const results = [];
        for (let i = 0; i < Math.min(3, notes.length); i++) {
            const note = notes[i];
            const result = {
                index: i,
                title: (note.querySelector('.title span') || {}).textContent || '',
                href: (note.querySelector('a.cover.mask') || {}).getAttribute('href') || ''
            };
            // Try desc selectors
            const descSelectors = ['.desc', '.content', '[class*="desc"]'];
            for (const sel of descSelectors) {
                const el = note.querySelector(sel);
                if (el && el.textContent && el.textContent.trim()) {
                    result.desc = el.textContent.trim().slice(0, 200);
                    break;
                }
            }
            // All text
            result.allText = (note.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 100);
            results.push(result);
        }
        return results;
    }""")

    result_data["notes"] = note_info

    note_html = page.evaluate("""() => {
        const note = document.querySelector('section.note-item');
        return note ? note.outerHTML.slice(0, 800) : 'not found';
    }""")
    result_data["html"] = note_html

    browser.close()

# Write to file instead of printing
with open(r"E:\translate\claw\xhs-auto-traffic-v2\_debug_notes_result.json", "w", encoding="utf-8") as f:
    json.dump(result_data, f, ensure_ascii=False, indent=2)

print("Data written to _debug_notes_result.json")
print("Done")