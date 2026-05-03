import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
import time
import json
import base64
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    cookies = json.load(open(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json"))
    context.add_cookies(cookies)

    page = context.new_page()
    page.set_default_timeout(15000)

    print("=== Test: Save and restore page content ===")

    # Go to explore via homepage search
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)

    page.fill("#search-input", "汕尾美食")
    time.sleep(0.3)
    page.keyboard.press("Enter")
    time.sleep(5)

    print("1. After search URL:", page.url)
    print("   Notes:", len(page.query_selector_all("section.note-item")))

    # Get note href and click
    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("2. Note href:", note_href[:80])

    # Click
    page.evaluate("""() => {
        document.querySelector('section.note-item a.cover.mask').click();
    }""")
    time.sleep(5)
    print("3. After click URL:", page.url)

    # Save the current HTML
    html_content = page.content()
    print("4. HTML length:", len(html_content))

    # Check what the note detail page HTML looks like
    has_login = "登录查看内容" in html_content or "login" in page.url.lower()
    print("   Has login content:", has_login)

    # Try: Get the full URL and check if there's content
    full_url = page.url

    # Now try: navigate away and come back
    print("\n5. Navigate away and back...")
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    # Go back
    page.go_back()
    time.sleep(5)
    print("   After go_back URL:", page.url)
    has_desc = page.query_selector("#detail-desc")
    print("   Has #detail-desc:", has_desc is not None)

    # If still no content, try one more thing: set a cookie and reload
    print("\n6. Check current cookies...")
    ctx_cookies = page.context.cookies()
    ws = [c for c in ctx_cookies if c['name'] == 'web_session']
    print("   web_session:", ws[0]['value'][:40] if ws else "NOT FOUND")
    print("   Total cookies:", len(ctx_cookies))

    # Check the note state again
    note_state = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state) return 'no state';
        
        const noteState = state.note;
        if (!noteState) return 'no note state';
        
        const noteDetailMap = noteState.noteDetailMap;
        if (!noteDetailMap) return 'no noteDetailMap';
        
        const keys = Object.keys(noteDetailMap);
        if (!keys.length) return 'empty map';
        
        const firstEntry = noteDetailMap[keys[0]];
        
        return {
            mapKeyCount: keys.length,
            firstKey: keys[0],
            firstValueKeys: Object.keys(firstEntry),
            hasNote: !!firstEntry.note,
            noteType: typeof firstEntry.note,
            noteStr: JSON.stringify(firstEntry.note)
        };
    }""")
    print("7. Note state:", json.dumps(note_state, ensure_ascii=False, indent=2))

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_final.png")
    browser.close()
    print("\nDone")