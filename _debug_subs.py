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

    # Explore subs structure
    subs_info = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.feed || !state.feed.feeds) return null;
        
        const feeds = state.feed.feeds;
        const depFeed = feeds['dep'];
        if (!depFeed || !depFeed.subs) return 'no subs';
        
        const subs = depFeed.subs;
        const subRef = subs.sub;
        const depRef = subs.dep;
        
        return {
            subHasValue: !!subRef && subRef._value !== undefined,
            subValueType: subRef ? typeof subRef._value : 'N/A',
            subValueKeys: subRef && subRef._value && typeof subRef._value === 'object' ? Object.keys(subRef._value) : [],
            subValueHasItems: subRef && subRef._value && subRef._value.items ? !!subRef._value.items : false,
            subValueItemCount: subRef && subRef._value && subRef._value.items ? subRef._value.items.length : 0,
            
            depHasValue: !!depRef && depRef._value !== undefined,
            depValueType: depRef ? typeof depRef._value : 'N/A',
            depValueKeys: depRef && depRef._value && typeof depRef._value === 'object' ? Object.keys(depRef._value) : []
        };
    }""")
    
    print("Subs info:", json.dumps(subs_info, ensure_ascii=False, indent=2))

    # Check if sub._value.items has note data
    if subs_info.get('subHasValue') and subs_info.get('subValueItemCount', 0) > 0:
        notes_from_sub = page.evaluate("""() => {
            const state = window.__INITIAL_STATE__;
            const feeds = state.feed.feeds;
            const depFeed = feeds['dep'];
            const subRef = depFeed.subs.sub;
            const items = subRef._value.items;
            
            return items.slice(0, 5).map(item => ({
                id: item.id,
                title: item.title || item.displayTitle || '',
                abs: item.abs || '',
                desc: item.desc || '',
                type: item.type
            }));
        }""")
        
        print(f"\nNotes from sub._value.items:")
        for n in notes_from_sub:
            print(f"  id={n['id']}, title={n['title'][:40]}, abs={n['abs'][:40]}")

    browser.close()
    print("\nDone")