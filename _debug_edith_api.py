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

    # Get note IDs from subs.sub._value
    note_ids = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        const feeds = state.feed.feeds;
        const depFeed = feeds['dep'];
        const subRef = depFeed.subs.sub;
        const arr = subRef._value;
        
        return Object.keys(arr).slice(0, 5).map(k => ({
            id: arr[k].id,
            xsecToken: arr[k].xsecToken
        }));
    }""")
    
    print("Note IDs:", note_ids)

    # Try the edith API for each note
    for ni in note_ids:
        api_url = f"https://edith.xiaohongshu.com/api/sns/web/v1/note/{ni['id']}"
        print(f"\nAPI: {api_url}")
        resp = page.request.get(api_url)
        print(f"   Status: {resp.status}")
        print(f"   URL: {resp.url}")
        
        if resp.status == 200:
            data = resp.json()
            print(f"   Keys: {list(data.keys())}")
            if 'data' in data:
                d = data['data']
                print(f"   data keys: {list(d.keys()) if isinstance(d, dict) else type(d)}")
                if isinstance(d, dict):
                    print(f"   note keys: {list(d.get('note', {}).keys()) if 'note' in d else 'no note'}")
                    print(f"   title: {d.get('note', {}).get('title', '')}")
                    print(f"   desc: {str(d.get('note', {}).get('desc', ''))[:100]}")
        else:
            print(f"   Response: {resp.text()[:100]}")

    browser.close()
    print("\nDone")