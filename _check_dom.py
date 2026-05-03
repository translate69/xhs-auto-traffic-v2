import sys, re
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from core.search_collector import SearchCollector, FeedNote
from core.browser_manager import BrowserManager

keyword = "汕尾美食"
limit = 5

print(f"Keyword: {keyword}")
with BrowserManager(headless=False) as (browser, context):
    collector = SearchCollector(browser, context)
    # 直接读 raw feeds，不走 filter
    from core.search_collector import SearchCollector
    page = context.new_page()
    page.goto(f"https://www.xiaohongshu.com/search_result?keyword=%E6%B1%95%E5%B0%BE%E7%BE%8E%E9%A3%9F", timeout=60000)
    page.wait_for_timeout(3000)
    
    # 直接提取几个 feed 看看 URL 格式
    import json
    data = page.evaluate("""
        () => {
            const notes = document.querySelectorAll('.note-item');
            return Array.from(notes).slice(0, 5).map(n => {
                const link = n.querySelector('a[href*="search_result"]') || n.querySelector('a[href*="explore"]');
                return {
                    href: link ? link.href : '',
                    title: n.innerText.slice(0, 50)
                };
            });
        }
    """)
    print(f"\nFound {len(data)} note items in DOM:")
    for item in data:
        print(f"  href: {item['href'][:100]}")
        print(f"  title: {item['title'][:50]}")
        print()
    page.close()
