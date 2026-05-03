import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from core.search_collector import SearchCollector
from core.browser_manager import BrowserManager
from utils.parse import parse_published_at
from datetime import datetime

keyword = "汕尾美食"
limit = 5

with BrowserManager(headless=False) as (browser, context):
    collector = SearchCollector(browser, context)
    page = context.new_page()
    
    # 直接访问搜索页
    page.goto(f"https://www.xiaohongshu.com/search_result?keyword=%E6%B1%95%E5%B0%BE%E7%BE%8E%E9%A3%9F", timeout=60000)
    page.wait_for_timeout(3000)
    
    # 等筛选面板出现并操作
    try:
        page.locator(".filter").click(timeout=5000)
        page.wait_for_timeout(1000)
        # 点最新
        page.locator("text=最新").click(timeout=3000)
        page.wait_for_timeout(1000)
        # 点一周内
        page.locator("text=一周内").click(timeout=3000)
        page.wait_for_timeout(2000)
    except Exception as e:
        print(f"Filter click error: {e}")
    
    # 直接用 JS 提取所有 note item 的数据
    import json
    notes = page.evaluate("""
        () => {
            const items = document.querySelectorAll('.note-item');
            return Array.from(items).map(n => {
                const timeEl = n.querySelector('[class*="time"]') || n.querySelector('[class*="date"]') || n.querySelector('span');
                const timeText = timeEl ? timeEl.innerText.trim() : '';
                const link = n.querySelector('a[href*="search_result"]') || n.querySelector('a[href*="explore"]');
                return {
                    href: link ? link.href : '',
                    timeText: timeText
                };
            });
        }
    """)
    
    now = datetime.now()
    print(f"Found {len(notes)} notes after filter:")
    for n in notes:
        dt = parse_published_at(n['timeText'])
        if dt:
            age = (now - dt).days
            print(f"  '{n['timeText']}' -> dt={dt}, age={age} days {'PASS' if age <= 5 else 'FAIL'}")
        else:
            print(f"  '{n['timeText']}' -> dt=None")
        print(f"    href: {n['href'][:100]}")
    
    page.close()
