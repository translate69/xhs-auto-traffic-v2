import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from core.search_collector import SearchCollector
from core.browser_manager import BrowserManager

keyword = "汕尾美食"
limit = 5

# Monkey-patch to add debug output
original_extract = SearchCollector._extract_feeds

def debug_extract(self):
    # Check if notes exist
    count = self.page.evaluate("document.querySelectorAll('section.note-item').length")
    print(f"DEBUG: section.note-item count = {count}")
    
    # Check URLs in DOM
    urls = self.page.evaluate("""
        () => Array.from(document.querySelectorAll('section.note-item a.cover.mask'))
            .slice(0, 5).map(a => a.href)
    """)
    print(f"DEBUG: a.cover.mask hrefs found: {len(urls)}")
    for u in urls:
        print(f"  {u[:80]}")
    
    feeds = original_extract(self)
    print(f"DEBUG: _extract_feeds returned {len(feeds)} feeds")
    return feeds

SearchCollector._extract_feeds = debug_extract

with BrowserManager(headless=False) as (browser, context):
    collector = SearchCollector(browser, context)
    feeds = collector.collect(keyword, limit=limit)
    print(f"\nFinal feeds: {len(feeds)}")
    for f in feeds:
        print(f"  [{f.note_id}] {f.title[:30] if f.title else 'no title'} | {f.time_text}")