import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from core.search_collector import SearchCollector
from core.browser_manager import BrowserManager

keyword = "汕尾美食"
limit = 5

print(f"Keyword: {keyword}, Limit: {limit}")
with BrowserManager(headless=False) as (browser, context):
    collector = SearchCollector(browser, context)
    feeds = collector.collect(keyword, limit=limit)
    print(f"\nCollected {len(feeds)} feeds:")
    for f in feeds:
        print(f"  - [{f.note_id}] {f.title[:30] if f.title else 'NO TITLE'} | {f.time_text}")
        print(f"    url: {f.url[:80]}")
