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

    # Create SearchCollector and run a mini pipeline
    from core.search_collector import SearchCollector
    from core.note_detail import NoteDetailCollector
    from filter.filter_service import FilterService

    page = context.new_page()
    collector = SearchCollector(browser, context)
    page.close()

    # Collect feeds
    print("Collecting feeds for '汕尾美食'...")
    feeds = collector.collect("汕尾美食", limit=5)
    print(f"Feeds collected: {len(feeds)}")

    # Enrich first 3 only
    detail_collector = NoteDetailCollector(browser, context)
    notes = detail_collector.enrich_all(feeds[:3])
    print(f"Enriched notes: {len(notes)}")

    # Show content for each note
    for i, note in enumerate(notes):
        print(f"\nNote {i+1}: {note.note_id}")
        print(f"  Title: {note.title[:50] if note.title else 'none'}")
        print(f"  Content: {note.content[:80] if note.content else 'EMPTY'}")
        print(f"  Likes: {note.likes}, Collects: {note.collects}")

    # Now filter
    print("\nFiltering...")
    svc = FilterService()
    for note in notes:
        r = svc.filter_one(note, keyword="汕尾美食")
        print(f"  {note.title[:40]}: passed={r.passed}, reasons={r.reasons}, type={r.note_type}")

    browser.close()
    print("\nDone")