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

    print("1. Test note IDs from explore page...")
    # Get some note IDs from explore page
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    note_ids = page.evaluate("""() => {
        const notes = document.querySelectorAll('section.note-item a.cover.mask');
        const result = [];
        for (const note of notes) {
            const href = note.getAttribute('href') || '';
            const match = href.match(/\\/note\\/([a-f0-9]+)/) || href.match(/\\/explore\\/([a-f0-9]+)/);
            if (match) result.push(match[1]);
        }
        return result.slice(0, 10);
    }""")
    print(f"   Found note IDs: {note_ids[:5]}")

    # Check full URLs from explore page
    note_urls = page.evaluate("""() => {
        const notes = document.querySelectorAll('section.note-item a.cover.mask');
        const result = [];
        for (const note of notes) {
            result.push(note.getAttribute('href') || '');
        }
        return result.slice(0, 5);
    }""")
    print(f"   Note URLs: {note_urls[:3]}")

    # Now try each note ID with different URL formats
    for note_id in note_ids[:3]:
        print(f"\n2. Testing note_id: {note_id}")

        # Try /note/ format
        url1 = f"https://www.xiaohongshu.com/note/{note_id}"
        page2 = context.new_page()
        page2.goto(url1, wait_until="domcontentloaded", timeout=15000)
        time.sleep(3)
        print(f"   /note/ URL: {page2.url}")
        print(f"   Page title: {page2.title()[:40]}")
        note_item = page2.query_selector("section.note-item, .note-item, [class*='note-detail']")
        print(f"   Note item found: {note_item}")
        page2.close()

    browser.close()
    print("\nDone")