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
    print("2. URL:", page.url)

    # Deep dive into noteDetailMap
    deep_note = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.note || !state.note.noteDetailMap) return 'no noteDetailMap';
        
        const noteMap = state.note.noteDetailMap;
        const keys = Object.keys(noteMap);
        
        // Get the actual key/value for first entry
        const firstKey = keys[0];
        const firstValue = noteMap[firstKey];
        
        return {
            mapKeyCount: keys.length,
            firstKey: firstKey,
            firstKeyType: typeof firstKey,
            firstKeyRepr: JSON.stringify(firstKey),
            firstValueKeys: firstValue ? Object.keys(firstValue) : [],
            // Try to find actual note data inside
            noteInFirstValue: firstValue ? firstValue.note : null,
            noteDataKeys: firstValue && firstValue.note ? Object.keys(firstValue.note) : []
        };
    }""")
    print("3. Deep note:", json.dumps(deep_note, ensure_ascii=False, indent=2))

    # If note is inside, get it
    if deep_note.get('noteDataKeys'):
        note_full = page.evaluate("""() => {
            const state = window.__INITIAL_STATE__;
            const noteMap = state.note.noteDetailMap;
            const firstKey = Object.keys(noteMap)[0];
            const note = noteMap[firstKey].note;
            
            return {
                title: note.title || note.displayTitle || '',
                type: note.type || '',
                desc: note.desc || note.description || '',
                imageList: note.imageList ? note.imageList.length : 0,
                user: note.user ? note.user.nickname : '',
                likecount: note.interactInfo ? note.interactInfo.likedCount : 0,
                rawKeys: Object.keys(note).slice(0, 25)
            };
        }""")
        print("4. Note full data:", json.dumps(note_full, ensure_ascii=False, indent=2))

    browser.close()
    print("\nDone")