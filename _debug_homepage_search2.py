import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
import time
import json
from playwright.sync_api import sync_playwright

result_data = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    cookies = json.load(open(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json"))
    context.add_cookies(cookies)

    page = context.new_page()
    page.set_default_timeout(20000)

    # Test different homepage search approaches
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    print("Homepage URL:", page.url)

    # Get search input and surrounding elements
    search_info = page.evaluate("""() => {
        const input = document.querySelector('#search-input');
        if (!input) return 'NO SEARCH INPUT';
        
        // Get form and button
        const form = input.closest('form');
        const button = form ? form.querySelector('button[type="submit"], .search-btn, [class*="search"]') : null;
        
        return {
            inputExists: true,
            inputPlaceholder: input.getAttribute('placeholder') || '',
            formExists: !!form,
            buttonText: button ? (button.textContent || button.innerText || 'no text').trim() : null,
            buttonHTML: button ? button.outerHTML.slice(0, 200) : null,
            formHTML: form ? form.outerHTML.slice(0, 300) : null
        };
    }""")
    print("\nSearch input info:", json.dumps(search_info, ensure_ascii=False, indent=2))

    # Try: fill, then click button instead of press Enter
    page.fill("#search-input", "汕尾美食")
    time.sleep(0.5)

    # Find and click submit button
    btn_info = page.evaluate("""() => {
        const input = document.querySelector('#search-input');
        const form = input ? input.closest('form') : null;
        if (!form) return 'no form';
        
        const btn = form.querySelector('button[type="submit"]');
        if (!btn) {
            // Try finding any clickable search element
            const allBtns = form.querySelectorAll('button, [class*="search"], [class*="btn"]');
            return { 
                found: allBtns.length, 
                btns: Array.from(allBtns).slice(0,3).map(b => ({
                    text: (b.textContent||'').trim().slice(0,30),
                    class: b.className,
                    type: b.type,
                    html: b.outerHTML.slice(0,100)
                }))
            };
        }
        return { 
            found: true, 
            text: (btn.textContent||'').trim().slice(0,30),
            class: btn.className,
            type: btn.type,
            html: btn.outerHTML.slice(0,200)
        };
    }""")
    print("\nButton info:", json.dumps(btn_info, ensure_ascii=False, indent=2))

    # Click the button instead of pressing Enter
    click_result = page.evaluate("""() => {
        const input = document.querySelector('#search-input');
        const form = input ? input.closest('form') : null;
        if (!form) return 'no form';
        
        const btn = form.querySelector('button[type="submit"]') || form.querySelector('[class*="search"]');
        if (btn) {
            btn.click();
            return 'clicked: ' + btn.className;
        }
        return 'no button found';
    }""")
    print("\nClick result:", click_result)
    time.sleep(5)
    print("URL after click:", page.url)
    print("Notes after click:", len(page.query_selector_all("section.note-item")))

    # Now check: is there a filter panel on this page?
    has_filter = page.query_selector(".filter")
    print("Has .filter:", has_filter is not None)

    browser.close()

print("\nDone")