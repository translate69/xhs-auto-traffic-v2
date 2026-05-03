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

    # 1. Go to explore
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    # 2. Get note href and click
    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("1. Note href:", note_href[:80])

    # Click via JS (simulates real click behavior)
    page.evaluate("""() => {
        document.querySelector('section.note-item a.cover.mask').click();
    }""")
    time.sleep(5)
    print("2. URL:", page.url)

    # 3. Get the note ID from the URL
    note_id_match = re.search(r'/explore/([a-f0-9]+)', page.url)
    note_id = note_id_match.group(1) if note_id_match else None
    print("3. Note ID:", note_id)

    # 4. Try to call note detail API directly using page.request
    if note_id:
        print("\n4. Calling note detail API...")
        api_url = f"https://edith.xiaohongshu.com/api/sns/web/v1/note/{note_id}"
        resp = page.request.get(api_url)
        print(f"   API status: {resp.status}")
        print(f"   API URL: {resp.url}")
        if resp.status == 200:
            try:
                data = resp.json()
                print(f"   API response keys: {list(data.keys())}")
                print(f"   API data: {json.dumps(data, ensure_ascii=False)[:300]}")
            except:
                print(f"   Not JSON: {resp.text()[:100]}")
        else:
            print(f"   Response: {resp.text()[:200]}")

    # 5. Check what __INITIAL_STATE__ has for note data
    note_state = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state) return 'no state';
        
        const keys = Object.keys(state).filter(k => !k.startsWith('__'));
        const result = { stateKeys: keys };
        
        // Check note-related keys
        for (const key of ['note', 'feed', 'article', 'currentNote', 'noteDetail']) {
            if (state[key]) {
                const val = state[key];
                result[key + '_keys'] = Object.keys(val).slice(0, 10);
                
                // Special handling for noteDetailMap
                if (val.noteDetailMap) {
                    const mapKeys = Object.keys(val.noteDetailMap);
                    result['noteDetailMap_count'] = mapKeys.length;
                    
                    // Get first entry's actual content
                    if (mapKeys.length > 0) {
                        const firstEntry = val.noteDetailMap[mapKeys[0]];
                        result['firstEntry_keys'] = Object.keys(firstEntry).slice(0, 10);
                        result['firstEntry_noteType'] = firstEntry.note ? firstEntry.note.type : 'no note';
                    }
                }
            }
        }
        
        return result;
    }""")
    print("\n5. Note state:", json.dumps(note_state, ensure_ascii=False, indent=2))

    # 6. Check for note content in page DOM (non-login elements)
    dom_note_content = page.evaluate("""() => {
        // Check all elements for note-like content
        const body = document.body;
        
        // Look for elements that are NOT login-related
        const loginElements = document.querySelectorAll('[class*="login"], [id*="login"], .login-modal, .login-container');
        const loginTexts = new Set(['登录', 'login', '登陆', '登录查看']);
        
        // Check for note detail elements
        const detailSelectors = [
            '#detail-desc', '.detail-desc', '[class*="detail-desc"]',
            '.note-content', '[class*="note-content"]',
            '.title-container', '[class*="title-container"]',
            '.author-info', '[class*="author"]'
        ];
        
        const results = {};
        for (const sel of detailSelectors) {
            const el = document.querySelector(sel);
            if (el) {
                const text = el.textContent || '';
                const isLogin = loginTexts.has(text.trim()) || text.trim().length < 5;
                results[sel] = {
                    found: true,
                    text: text.trim().slice(0, 80),
                    isLikelyLogin: isLogin
                };
            } else {
                results[sel] = { found: false };
            }
        }
        
        return results;
    }""")
    print("\n6. DOM note content:", json.dumps(dom_note_content, ensure_ascii=False, indent=2))

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_full_note.png", full_page=True)
    browser.close()
    print("\nDone")