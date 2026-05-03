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

    # Step 1: Homepage
    print("1. Go to homepage...")
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    print(f"   URL: {page.url}")

    # Step 2: Find and interact with search
    search_input = page.wait_for_selector("#search-input", timeout=10000)
    
    # Check all elements in the search bar area
    search_bar = page.evaluate("""() => {
        const inp = document.querySelector('#search-input');
        if (!inp) return 'no input';
        // Find the parent that contains the search-related elements
        let el = inp.parentElement;
        for (let i = 0; i < 5; i++) {
            if (!el) break;
            const tag = el.tagName;
            const cls = el.className;
            const children = el.querySelectorAll('*');
            console.log(`Parent ${i}: ${tag} class=${cls.slice(0,50)} children=${children.length}`);
            el = el.parentElement;
        }
        
        // Find the form or search container
        const container = inp.closest('.search-container, .search-wrapper, .search-box, .header-search, [class*=\"search\"]');
        if (container) {
            const allChildren = container.querySelectorAll('*');
            return {
                tag: container.tagName,
                class: container.className.slice(0,60),
                children_count: allChildren.length,
                direct_children: Array.from(container.children).map(c => c.tagName + '.' + c.className.slice(0,30))
            };
        }
        return 'no container found';
    }""")
    print(f"\n2. Search bar structure: {search_bar}")

    # Try fill + wait for dropdown + click a suggestion
    print("\n3. Fill keyword...")
    search_input.fill("汕尾美食")
    time.sleep(1)

    # Check for any dropdown/suggestion that appeared
    popup_info = page.evaluate("""() => {
        // Look for any overlay/popup that might contain search suggestions
        const selectors = [
            '.search-suggest-popup', 
            '[class*=\"suggest\"]', 
            '[class*=\"search-result\"]',
            '.auto-complete',
            'ul[class*=\"search\"]',
            '[class*=\"dropdown\"]',
            '.xhs-dropdown'
        ];
        const results = {};
        selectors.forEach(sel => {
            const els = document.querySelectorAll(sel);
            if (els.length > 0) {
                results[sel] = Array.from(els).map(el => el.tagName + ' cls=' + el.className.slice(0,40) + ' txt=' + (el.textContent||'').slice(0,30));
            }
        });
        return results;
    }""")
    print(f"   Popup/dropdown elements: {popup_info}")

    # Check if Enter key has different behavior when input has value
    print("\n4. Check form action on enter...")
    form_info = page.evaluate("""() => {
        const inp = document.querySelector('#search-input');
        if (!inp) return 'no input';
        
        // Get all event listeners on this input
        const data = {
            tag: inp.tagName,
            type: inp.type,
            id: inp.id,
            name: inp.name,
            form: inp.form ? inp.form.tagName : 'no form',
            action: inp.form ? (inp.form.action || 'inline') : 'no form'
        };
        
        // Check if there's an onclick or keydown handler
        const handlers = [];
        const inlineOnkeydown = inp.getAttribute('onkeydown');
        const inlineOnclick = inp.getAttribute('onclick');
        const dataHref = inp.getAttribute('data-href');
        const dataUrl = inp.getAttribute('data-url');
        
        return {
            ...data,
            inlineOnkeydown: inlineOnkeydown ? 'yes: ' + inlineOnkeydown.slice(0,50) : 'no',
            inlineOnclick: inlineOnclick ? 'yes: ' + inlineOnclick.slice(0,50) : 'no',
            dataHref: dataHref,
            dataUrl: dataUrl
        };
    }""")
    print(f"   Form info: {form_info}")

    # Now look at the search icon - maybe there's a specific button
    icon_info = page.evaluate("""() => {
        const inp = document.querySelector('#search-input');
        if (!inp) return 'no input';
        
        // Look at the sibling elements of the input
        const parent = inp.parentElement;
        if (!parent) return 'no parent';
        
        const siblings = Array.from(parent.children).map(c => ({
            tag: c.tagName,
            cls: c.className.slice(0,40),
            html: c.innerHTML.slice(0,100)
        }));
        
        return { siblings };
    }""")
    print(f"\n5. Input siblings: {icon_info}")

    # Try using page.keyboard to type and enter
    print("\n6. Try type + enter (vs fill)...")
    search_input.fill("")  # clear first
    search_input.type("汕尾美食", delay=100)
    time.sleep(0.5)
    search_input.press("Enter")
    time.sleep(5)
    print(f"   After type+Enter: {page.url}")

    browser.close()
    print("\nDone")