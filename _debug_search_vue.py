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

    # Test: Can we use the Vue app's search functionality directly?
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    print("URL:", page.url)

    search_input = page.wait_for_selector("#search-input", timeout=10000)
    search_input.fill("汕尾美食")
    time.sleep(1)

    # Check the sug-box and try to find out what URL it would navigate to
    # by examining the Vue app's search component
    vue_info = page.evaluate("""() => {
        const app = document.querySelector('#app');
        if (!app || !app.__vue_app__) return 'no vue app';
        
        // Try to access the Vue app's global properties
        const vueApp = app.__vue_app__;
        
        // Check for router
        try {
            const router = vueApp.config.globalProperties.$router;
            if (router) {
                return {
                    hasRouter: true,
                    currentRoute: router.currentRoute ? router.currentRoute.value : 'no value'
                };
            }
        } catch(e) {
            return 'router error: ' + e.message;
        }
        
        return 'no router found';
    }""")
    print("Vue app info:", vue_info)

    # Try triggering navigation via Vue router programmatically
    print("\nTrying Vue router navigation...")
    result = page.evaluate("""() => {
        const app = document.querySelector('#app');
        if (!app || !app.__vue_app__) return 'no vue app';
        
        try {
            const vueApp = app.__vue_app__;
            const globalProps = vueApp.config.globalProperties;
            const router = globalProps.$router;
            
            if (router && router.push) {
                // Try pushing search URL
                router.push('/search_result?keyword=汕尾美食&type=51');
                return 'pushed search URL';
            }
            
            if (router && router.navigate) {
                router.navigate('/search_result?keyword=汕尾美食&type=51');
                return 'navigated to search';
            }
            
            return 'no push/navigate method found';
        } catch(e) {
            return 'error: ' + e.message;
        }
    }""")
    print("Vue router result:", result)
    time.sleep(5)
    print("URL after Vue router:", page.url)
    notes = page.query_selector_all("section.note-item")
    print("Notes:", len(notes))
    filter_el = page.query_selector(".filter")
    print("Has filter:", filter_el is not None)

    browser.close()
    print("Done")