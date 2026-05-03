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

    nc_full = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        const feeds = state.feed.feeds;
        const depFeed = feeds['dep'];
        const subRef = depFeed.subs.sub;
        const arr = subRef._value;
        
        const firstItem = arr['0'];
        const nc = firstItem.noteCard;
        
        return {
            ncKeys: Object.keys(nc),
            displayTitle: nc.displayTitle || '',
            type: nc.type || '',
            user: nc.user ? nc.user.nickname : '',
            interactInfo: nc.interactInfo ? {
                likedCount: nc.interactInfo.likedCount,
                commentCount: nc.interactInfo.commentCount
            } : null,
            coverUrls: nc.cover ? nc.cover.infoList?.map(i => i.url) || [] : [],
            hasDesc: !!nc.desc,
            hasAbstract: !!nc.abs,
            hasTitle: !!nc.title
        };
    }""")
    
    result["nc_full"] = nc_full

    # Get all notes
    all_notes = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        const feeds = state.feed.feeds;
        const depFeed = feeds['dep'];
        const subRef = depFeed.subs.sub;
        const arr = subRef._value;
        
        const notes = [];
        for (const key of Object.keys(arr)) {
            const el = arr[key];
            const nc = el.noteCard;
            if (nc) {
                notes.push({
                    id: el.id,
                    xsecToken: el.xsecToken,
                    displayTitle: nc.displayTitle || '',
                    type: nc.type || '',
                    userNickname: nc.user ? nc.user.nickname : '',
                    interactInfo: nc.interactInfo ? {
                        likedCount: nc.interactInfo.likedCount,
                        commentCount: nc.interactInfo.commentCount
                    } : null
                });
            }
        }
        return notes;
    }""")
    
    result["all_notes"] = all_notes

    browser.close()

with open(r"E:\translate\claw\xhs-auto-traffic-v2\_debug_nc_result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("Done - written to _debug_nc_result.json")