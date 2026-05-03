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

    print("=== Test: From explore page, can we click note and extract content via __INITIAL_STATE__? ===")

    # Go to explore (from homepage search)
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    page.fill("#search-input", "汕尾美食")
    time.sleep(0.3)
    page.keyboard.press("Enter")
    time.sleep(5)
    
    print("1. After search URL:", page.url)
    print("   Notes:", len(page.query_selector_all("section.note-item")))

    # Get note href from DOM
    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : '';
    }""")
    print("2. Note href:", note_href[:80])

    # Click the note (via JS to bypass reds-mask)
    page.evaluate("""() => {
        document.querySelector('section.note-item a.cover.mask').click();
    }""")
    time.sleep(5)
    print("3. After click URL:", page.url)

    # Now check __INITIAL_STATE__ on the note page
    note_state = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state) return 'no state';
        
        // Check if note data is in state.note.noteDetailMap
        const noteDetailMap = state.note?.noteDetailMap;
        if (!noteDetailMap) return 'no noteDetailMap - keys: ' + Object.keys(state).join(', ');
        
        const keys = Object.keys(noteDetailMap);
        if (!keys.length) return 'empty noteDetailMap';
        
        // Get first entry
        const firstKey = keys[0];
        const firstVal = noteDetailMap[firstKey];
        
        return {
            mapKeyCount: keys.length,
            firstKey: firstKey,
            firstValueKeys: Object.keys(firstVal),
            hasNote: !!firstVal.note,
            noteKeys: firstVal.note ? Object.keys(firstVal.note) : [],
            noteType: firstVal.note ? firstVal.note.type : null,
            noteDisplayTitle: firstVal.note ? firstVal.note.displayTitle : null,
            noteDesc: firstVal.note ? (firstVal.note.desc || firstVal.note.description || '') : null,
            noteAbs: firstVal.note ? (firstVal.note.abs || '') : null
        };
    }""")
    print("4. Note state:", json.dumps(note_state, ensure_ascii=False, indent=2))

    # If note has content in __INITIAL_STATE__, we can extract it without waiting for DOM
    if note_state.get('noteDesc'):
        print("5. Note desc from __INITIAL_STATE__:", note_state['noteDesc'][:100])

    # Try to extract note content via page.evaluate on the loaded note page
    page_content = page.evaluate("""() => {
        // Try to get content from #detail-desc
        const detailDesc = document.querySelector('#detail-desc');
        const titleEl = document.querySelector('.title-container .title span, h1.title');
        const authorEl = document.querySelector('.author-info .name');
        
        return {
            hasDetailDesc: !!detailDesc,
            detailDescText: detailDesc ? detailDesc.textContent.slice(0, 200) : null,
            titleText: titleEl ? titleEl.textContent.trim() : null,
            authorText: authorEl ? authorEl.textContent.trim() : null,
            bodyTextLength: document.body.textContent.length
        };
    }""")
    print("6. Page content:", json.dumps(page_content, ensure_ascii=False))

    browser.close()
    print("\nDone")