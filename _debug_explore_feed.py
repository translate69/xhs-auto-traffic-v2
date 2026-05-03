import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
import time
from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    cookies = json.load(open(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json"))
    context.add_cookies(cookies)

    page = context.new_page()
    page.set_default_timeout(15000)

    print("1. Go to explore page...")
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    print("   URL:", page.url)

    # Check what data is in the feed items
    print("\n2. Checking __INITIAL_STATE__ feed data...")
    feed_data = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.feed) return { error: 'no state.feed' };
        
        const feeds = state.feed.feeds;
        const keys = Object.keys(feeds || {});
        if (!keys.length) return { error: 'no feeds', feedKeys: Object.keys(state.feed) };
        
        const firstKey = keys[0];
        const firstFeed = feeds[firstKey];
        
        if (!firstFeed) return { error: 'no firstFeed' };
        
        return {
            feedKey: firstKey,
            hasItems: !!firstFeed.items,
            itemCount: firstFeed.items ? firstFeed.items.length : 0,
            firstItemKeys: firstFeed.items && firstFeed.items[0] ? Object.keys(firstFeed.items[0]).slice(0, 15) : []
        };
    }""")
    print("   Feed data:", feed_data)

    # Check the note-item elements to see what content they have
    print("\n3. Check note-item structure...")
    note_items = page.evaluate("""() => {
        const notes = document.querySelectorAll('section.note-item');
        if (!notes.length) return 'no notes';
        
        const first = notes[0];
        const result = {
            noteCount: notes.length,
            firstTitle: first.querySelector('.title span')?.textContent || '',
            firstAuthor: first.querySelector('.name-time-wrapper .name')?.textContent || '',
            firstTime: first.querySelector('.name-time-wrapper .time')?.textContent || '',
            hasContent: !!first.querySelector('.desc, .content, [class*="desc"]'),
            firstClass: first.className
        };
        
        // Get all text content from first note (to see if it has full content)
        const firstText = first.textContent || '';
        result.firstTextPreview = firstText.slice(0, 100);
        
        return result;
    }""")
    print("   Note items:", note_items)

    # Try to find any note content in the explore page
    print("\n4. Check if explore page shows note descriptions...")
    descriptions = page.evaluate("""() => {
        const descs = document.querySelectorAll('[class*="desc"], .note-desc, .content');
        return Array.from(descs).slice(0, 3).map(d => d.textContent?.trim().slice(0, 50));
    }""")
    print("   Descriptions found:", descriptions)

    browser.close()
    print("\nDone")