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
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    print("URL:", page.url)

    search_input = page.wait_for_selector("#search-input", timeout=10000)

    # Test approach: use JavaScript to trigger the Vue router/navigation
    # Maybe the search box is connected to Vue and needs input event + keydown
    print("\n1. Fill + JS InputEvent + Enter...")
    search_input.fill("汕尾美食")
    
    # Trigger Vue's input handler via InputEvent
    page.evaluate("""() => {
        const inp = document.querySelector('#search-input');
        // Fire input event (Vue listens for this)
        const inputEvent = new Event('input', { bubbles: true, composed: true });
        inp.dispatchEvent(inputEvent);
        // Fire keydown for Enter key
        const kbEvent = new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true });
        inp.dispatchEvent(kbEvent);
    }""")
    time.sleep(5)
    print("URL after JS events:", page.url)
    notes = page.query_selector_all("section.note-item")
    print("Notes:", len(notes))

    # If still on explore, try triggering via URL change
    if "search_result" not in page.url:
        print("\n2. Check page for search-related Vue router...")
        router_info = page.evaluate("""() => {
            // Check if Vue router is available
            if (typeof window.__vue_router__ !== 'undefined') {
                return '__vue_router__ found';
            }
            if (typeof window.Vue !== 'undefined') {
                return 'Vue available: ' + window.Vue.version;
            }
            // Check for app-specific router
            const app = document.querySelector('#app');
            if (app && app.__vue_app__) {
                return '__vue_app__ found';
            }
            return 'No Vue router found';
        }""")
        print("Router info:", router_info)

        # Try pressing key through keyboard modal
        print("\n3. Try Enter via different keyboard config...")
        search_input.fill("")
        search_input.fill("汕尾美食")
        time.sleep(0.5)
        
        # Check what happens when we press Escape (might close sug-box and then navigation happens)
        search_input.press("Escape")
        time.sleep(1)
        search_input.press("Enter")
        time.sleep(5)
        print("URL after Escape+Enter:", page.url)
        notes2 = page.query_selector_all("section.note-item")
        print("Notes:", len(notes2))

    # Final check - check if there's a search icon that does navigation
    print("\n4. Look for search icon button with data-hp-kind...")
    icon_btn = page.query_selector("[data-hp-kind='.close-icon']")
    print("close-icon:", icon_btn)
    if icon_btn:
        parent = page.evaluate("""() => {
            const icon = document.querySelector("[data-hp-kind='.close-icon']");
            if (!icon) return null;
            let el = icon.parentElement;
            for (let i = 0; i < 5; i++) {
                if (!el) break;
                console.log('Parent', i, el.tagName, el.className.slice(0,50));
                el = el.parentElement;
            }
            return null;
        }""")

    browser.close()
    print("\nDone")