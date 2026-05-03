import sys
sys.path.insert(0, "E:/translate/claw/xhs-auto-traffic-v2")
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    import json
    cookies = json.load(open(r'E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json'))
    context.add_cookies(cookies)

    page = context.new_page()

    # Go to explore first (notes render there)
    print("1. Explore page (baseline)...")
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(5)
    print(f"   Notes: {len(page.query_selector_all('section.note-item'))}")

    # Now navigate to search_result and try a LONGER wait + scrolling
    print("\n2. Search_result with extended wait...")
    page.goto("https://www.xiaohongshu.com/search_result?keyword=汕尾美食&type=51", wait_until="domcontentloaded")
    time.sleep(15)  # Wait 15s for JS to render

    # Force scroll to trigger lazy loading
    for i in range(5):
        page.evaluate(f"window.scrollTo(0, {i*500})")
        time.sleep(2)
        print(f"   After scroll {i+1}: {len(page.query_selector_all('section.note-item'))} notes")

    # Check if notes exist in Vue state but not DOM
    vue_state_check = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.feed || !state.feed.feeds) return 'no feeds';
        
        // Get all notes from all feed objects
        const allNotes = [];
        Object.values(state.feed.feeds).forEach(feed => {
            if (feed && feed.items) {
                allNotes.push(...feed.items);
            }
        });
        
        return {
            totalInState: allNotes.length,
            firstNoteId: allNotes[0] ? allNotes[0].id : 'none',
            noteIds: allNotes.slice(0, 3).map(n => n.id)
        };
    }""")
    print(f"\n3. Vue state notes: {vue_state_check}")

    # Check for __NUXT__ or other hydration data
    nuxt_check = page.evaluate("""() => {
        if (typeof window.__NUXT__ !== 'undefined') {
            return { hasNuxt: true, keys: Object.keys(window.__NUXT__).slice(0, 5) };
        }
        return { hasNuxt: false };
    }""")
    print(f"4. Nuxt state: {nuxt_check}")

    # Try clicking in the page area to trigger any lazy render
    print("\n5. Try clicking body to trigger render...")
    page.click("body", timeout=5000)
    time.sleep(3)
    print(f"   After click: {len(page.query_selector_all('section.note-item'))} notes")

    # Check if the search result container has any child elements at all
    container_check = page.evaluate("""() => {
        // Look for any element that might contain note items
        const selectors = [
            '.feeds-container',
            '.note-list',
            '[class*="feeds"]',
            '[class*="note-list"]',
            'main'
        ];
        
        const results = {};
        selectors.forEach(sel => {
            const el = document.querySelector(sel);
            if (el) {
                results[sel] = {
                    class: el.className.slice(0, 40),
                    childCount: el.children.length,
                    innerHTML: el.innerHTML.slice(0, 200)
                };
            }
        });
        return results;
    }""")
    print(f"\n6. Container check: {container_check}")

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_sr_extended.png")
    browser.close()
    print("\nDone")