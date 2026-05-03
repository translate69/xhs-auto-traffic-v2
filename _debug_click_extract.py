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

    print("=== Test: click note from explore page, extract content ===")

    # Go to explore
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    print("1. Explore URL:", page.url)

    # Get a note href
    first_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("2. First href:", first_href[:80] if first_href else None)

    # Click via JS
    page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        if (link) link.click();
    }""")
    time.sleep(5)
    print("3. After click URL:", page.url)
    print("   Title:", page.title()[:60])

    if "/note/" in page.url or "/explore/" in page.url:
        # Wait for detail content to load
        try:
            page.wait_for_selector("#detail-desc, .note-content, [class*='detail']", timeout=10000)
            print("   Detail content appeared!")
        except:
            print("   Detail content did NOT appear")

        # Get note content
        content = page.evaluate("""() => {
            const desc = document.querySelector('#detail-desc');
            const title = document.querySelector('.title-container .title span, h1.title');
            const author = document.querySelector('.author-info .name, [class*="author"] .name');
            const bottom = document.querySelector('.bottom-container, .note-footer');
            
            return {
                hasDetailDesc: !!desc,
                detailText: desc ? desc.textContent.slice(0, 200) : null,
                titleText: title ? title.textContent.slice(0, 50) : null,
                authorText: author ? author.textContent.trim() : null,
                hasBottom: !!bottom,
                bodyLength: document.body.textContent.length
            };
        }""")
        print("4. Content:", json.dumps(content, ensure_ascii=False, indent=2))

        # Check __INITIAL_STATE__ for note data
        note_data = page.evaluate("""() => {
            const state = window.__INITIAL_STATE__;
            if (!state || !state.note) return 'no note state';
            
            const noteMap = state.note.noteDetailMap;
            if (!noteMap) return 'no noteDetailMap';
            
            const keys = Object.keys(noteMap);
            if (!keys.length) return 'no keys in noteDetailMap';
            
            const firstKey = keys[0];
            const noteItem = noteMap[firstKey];
            
            return {
                mapKeys: keys.slice(0, 3),
                firstNoteId: firstKey,
                firstNoteKeys: noteItem ? Object.keys(noteItem).slice(0, 10) : [],
                title: noteItem ? (noteItem.title || noteItem.displayTitle || 'no title') : 'no note',
                type: noteItem ? noteItem.type : null,
                imageList: noteItem ? (noteItem.imageList ? noteItem.imageList.length : 0) : 0
            };
        }""")
        print("5. __INITIAL_STATE__.note:", json.dumps(note_data, ensure_ascii=False, indent=2))

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_click_detail.png")
    browser.close()
    print("\nDone")