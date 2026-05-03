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

    print("=== Test: Wait LONGER for note content to load ===")

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

    # Wait for 15 seconds and check periodically
    for i in range(15):
        time.sleep(1)
        url = page.url
        has_detail = page.query_selector("#detail-desc")
        print(f"2.{i+1}s: url={url[:60]}, has_detail={has_detail is not None}")

        if has_detail:
            print("   Found #detail-desc!")
            break

        if "/login" in url:
            print("   -> Login page, stopping")
            break

    # Final state
    print("\n3. Final URL:", page.url)
    print("   Title:", page.title()[:60])

    # Check note state
    note_state = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.note || !state.note.noteDetailMap) return 'no map';
        
        const map = state.note.noteDetailMap;
        const keys = Object.keys(map);
        
        if (!keys.length) return 'empty map';
        
        const firstKey = keys[0];
        const firstVal = map[firstKey];
        
        return {
            key: firstKey,
            hasNote: !!firstVal.note,
            noteEmpty: firstVal.note ? JSON.stringify(firstVal.note) === '{}' : 'no note',
            noteKeys: firstVal.note ? Object.keys(firstVal.note) : []
        };
    }""")
    print("4. Note state:", json.dumps(note_state, ensure_ascii=False))

    # Check if the page has any content at all
    body_elements = page.evaluate("""() => {
        const body = document.body;
        const children = Array.from(body.children).map(c => c.tagName + '.' + c.className.slice(0,30));
        return {
            childCount: body.children.length,
            children: children.slice(0, 10),
            text: body.textContent.replace(/\\s+/g, ' ').trim().slice(0, 100)
        };
    }""")
    print("5. Body elements:", json.dumps(body_elements, ensure_ascii=False))

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_long_wait.png", full_page=True)
    browser.close()
    print("\nDone")