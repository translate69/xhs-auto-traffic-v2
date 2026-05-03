import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
import time
import json
import re
from playwright.sync_api import sync_playwright

result = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    cookies = json.load(open(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json"))
    context.add_cookies(cookies)

    page = context.new_page()
    page.set_default_timeout(15000)

    # Go to explore via homepage search
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    page.fill("#search-input", "汕尾美食")
    time.sleep(0.3)
    page.keyboard.press("Enter")
    time.sleep(5)

    print("1. URL:", page.url)
    print("   Notes:", len(page.query_selector_all("section.note-item")))

    # Check note items for any description text
    notes_info = page.evaluate("""() => {
        const notes = document.querySelectorAll('section.note-item');
        const result = [];
        
        for (let i = 0; i < Math.min(5, notes.length); i++) {
            const note = notes[i];
            
            // Try various text selectors
            const titleEl = note.querySelector('.title span');
            const descSelectors = ['.desc', '.abstract', '[class*="desc"]', '[class*="content"]', '.note-desc'];
            let descText = '';
            for (const sel of descSelectors) {
                const el = note.querySelector(sel);
                if (el && el.textContent && el.textContent.trim()) {
                    descText = el.textContent.trim();
                    break;
                }
            }
            
            // Get full text as fallback
            if (!descText) {
                descText = note.textContent.replace(/\\s+/g, ' ').trim();
            }
            
            const linkEl = note.querySelector('a.cover.mask');
            
            result.push({
                index: i,
                title: titleEl ? titleEl.textContent.trim() : '',
                href: linkEl ? linkEl.getAttribute('href') : '',
                desc: descText.slice(0, 200),
                html: note.outerHTML.slice(0, 500)
            });
        }
        
        return result;
    }""")
    
    # Save to file (avoid console encoding issues)
    with open(r"E:\translate\claw\xhs-auto-traffic-v2\_debug_notes_info.json", "w", encoding="utf-8") as f:
        json.dump(notes_info, f, ensure_ascii=False, indent=2)
    
    print("\n2. Saved note info to _debug_notes_info.json")
    
    # Check the HTML structure of first note item
    first_note_html = page.evaluate("""() => {
        const note = document.querySelector('section.note-item');
        return note ? note.outerHTML : 'not found';
    }""")
    
    with open(r"E:\translate\claw\xhs-auto-traffic-v2\_debug_first_note.html", "w", encoding="utf-8") as f:
        f.write(first_note_html)
    
    print("3. Saved first note HTML to _debug_first_note.html")
    
    # Check if there are any .desc elements in the explore feed
    desc_count = page.evaluate("""() => {
        const descs = document.querySelectorAll('.desc, [class*="desc"]');
        return {
            count: descs.length,
            samples: Array.from(descs).slice(0, 3).map(d => d.className + ': ' + d.textContent.trim().slice(0, 50))
        };
    }""")
    print("4. Desc elements:", desc_count)

    browser.close()
    print("\nDone")