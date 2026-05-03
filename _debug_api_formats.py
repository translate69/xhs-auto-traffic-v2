import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
import time
import json
from playwright.sync_api import sync_playwright

result = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    cookies = json.load(open(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json"))
    context.add_cookies(cookies)

    page = context.new_page()
    page.set_default_timeout(15000)

    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    feed_items = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        const feeds = state.feed.feeds;
        const depFeed = feeds['dep'];
        const subRef = depFeed.subs.sub;
        const arr = subRef._value;
        
        return Object.keys(arr).slice(0, 3).map(k => ({
            cardId: arr[k].id,
            xsecToken: arr[k].xsecToken,
            noteCardTitle: arr[k].noteCard?.displayTitle || ''
        }));
    }""")
    
    result["feed_items"] = feed_items

    first = feed_items[0]
    result["first_id"] = first["cardId"]
    
    # Try different API formats
    apis = [
        f"https://edith.xiaohongshu.com/api/sns/web/v1/note/{first['cardId']}",
        f"https://edith.xiaohongshu.com/api/sns/web/v2/note/{first['cardId']}",
        f"https://edith.xiaohongshu.com/api/sns/web/v1/note/{first['cardId']}?xsec_token={first['xsecToken']}",
        "https://edith.xiaohongshu.com/api/sns/web/v1/homefeed",
        "https://edith.xiaohongshu.com/api/sns/web/v1/explore/feed"
    ]
    
    result["api_results"] = []
    for api_url in apis:
        resp = page.request.get(api_url)
        result["api_results"].append({
            "url": api_url,
            "status": resp.status,
            "body_preview": resp.text()[:100] if resp.status != 200 else ""
        })

    browser.close()

with open(r"E:\translate\claw\xhs-auto-traffic-v2\_debug_api_results.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("Done - written to _debug_api_results.json")