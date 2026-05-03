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

    print("=== Test: Extract note content from explore feed (no click needed) ===")

    # Go to explore via homepage search
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    page.fill("#search-input", "汕尾美食")
    time.sleep(0.3)
    page.keyboard.press("Enter")
    time.sleep(5)

    print("1. URL:", page.url)
    print("   Notes:", len(page.query_selector_all("section.note-item")))

    # Get all note data from the explore page
    notes_data = page.evaluate("""() => {
        const notes = document.querySelectorAll('section.note-item');
        const results = [];
        
        for (let i = 0; i < Math.min(20, notes.length); i++) {
            const note = notes[i];
            
            // Get title
            const titleEl = note.querySelector('.title span');
            const title = titleEl ? titleEl.textContent.trim() : '';
            
            // Get author
            const authorEl = note.querySelector('.name-time-wrapper .name');
            const author = authorEl ? authorEl.textContent.trim() : '';
            
            // Get time
            const timeEl = note.querySelector('.name-time-wrapper .time');
            const timeText = timeEl ? timeEl.textContent.trim() : '';
            
            // Get image
            const imgEl = note.querySelector('.cover img');
            const img = imgEl ? imgEl.getAttribute('src') || imgEl.getAttribute('data-xhs-img') : '';
            
            // Get URL
            const linkEl = note.querySelector('a.cover.mask');
            const href = linkEl ? linkEl.getAttribute('href') : '';
            
            // Get full text content (sometimes descriptions are in the note item)
            const fullText = note.textContent || '';
            
            results.push({
                index: i,
                title: title,
                author: author,
                time: timeText,
                href: href,
                fullTextPreview: fullText.replace(/\\s+/g, ' ').trim().slice(0, 80)
            });
        }
        
        return results;
    }""")
    
    print("\n2. Note data from explore page:")
    for n in notes_data:
        print(f"   [{n['index']}] title={n['title'][:40]}")
        print(f"       author={n['author']}, time={n['time']}")
        print(f"       href={n['href'][:60]}")
        print(f"       fullText={n['fullTextPreview'][:60]}")

    # Check __INITIAL_STATE__ for feed data
    feed_data = page.evaluate("""() => {
        const state = window.__INITIAL_STATE__;
        if (!state || !state.feed || !state.feed.feeds) return 'no feed data';
        
        const feeds = state.feed.feeds;
        const keys = Object.keys(feeds);
        if (!keys.length) return 'no feed keys';
        
        const firstFeed = feeds[keys[0]];
        if (!firstFeed || !firstFeed.items || !firstFeed.items.length) return 'no items';
        
        return {
            feedKey: keys[0],
            itemCount: firstFeed.items.length,
            firstItemKeys: Object.keys(firstFeed.items[0]).slice(0, 15),
            firstItemPreview: JSON.stringify(firstFeed.items[0]).slice(0, 300)
        };
    }""")
    print("\n3. __INITIAL_STATE__ feed:", json.dumps(feed_data, ensure_ascii=False, indent=2)[:500])

    browser.close()
    print("\nDone")