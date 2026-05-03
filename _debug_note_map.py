import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
import time
import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    cookies = json.load(open(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json"))
    context.add_cookies(cookies)

    page = context.new_page()
    page.set_default_timeout(15000)

    # 1. Go to explore
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    print("1. Explore URL:", page.url)
    print("   Cookies:", len(page.context.cookies()))

    # 2. Get note href
    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("2. Note href:", note_href[:80])

    # 3. CLICK and see if the SPA successfully loads note data
    page.evaluate("""() => {
        document.querySelector('section.note-item a.cover.mask').click();
    }""")
    time.sleep(5)
    print("3. After click URL:", page.url)

    # 4. Check noteDetailMap more carefully - what are the actual keys?
    note_map_keys = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.note || !state.note.noteDetailMap) return 'no map';
        
        const map = state.note.noteDetailMap;
        const entries = [];
        
        for (const [key, value] of Object.entries(map)) {
            entries.push({
                keyRepr: JSON.stringify(key),
                valueType: typeof value,
                valueKeys: value ? Object.keys(value) : [],
                hasNote: !!value.note,
                noteType: value.note ? (typeof value.note) : 'null',
                noteContent: value.note ? JSON.stringify(value.note).slice(0, 200) : 'null'
            });
        }
        
        return entries;
    }""")
    print("4. Note detail map entries:", json.dumps(note_map_keys, ensure_ascii=False, indent=2))

    # 5. Try to find note data in the raw HTML (after JavaScript runs)
    # Maybe the data is in a script tag
    raw_data = page.evaluate("""() => {
        const scripts = document.querySelectorAll('script');
        const results = [];
        
        for (const script of scripts) {
            const text = script.textContent || '';
            if (text.includes('noteDetailMap') || text.includes('note_id')) {
                results.push({
                    src: script.src || 'inline',
                    textPreview: text.slice(0, 300)
                });
            }
        }
        
        return results;
    }""")
    print("5. Scripts with note data:", json.dumps(raw_data, ensure_ascii=False, indent=2))

    browser.close()
    print("\nDone")