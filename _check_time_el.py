import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from core.search_collector import SearchCollector
from core.browser_manager import BrowserManager

keyword = "汕尾美食"
limit = 5

with BrowserManager(headless=False) as (browser, context):
    collector = SearchCollector(browser, context)
    page = context.new_page()
    
    page.goto(f"https://www.xiaohongshu.com/search_result?keyword=%E6%B1%95%E5%B0%BE%E7%BE%8E%E9%A3%9F", timeout=60000)
    page.wait_for_timeout(3000)
    
    # 等筛选
    try:
        page.locator(".filter").click(timeout=5000)
        page.wait_for_timeout(1000)
        page.locator("text=最新").click(timeout=3000)
        page.wait_for_timeout(1000)
        page.locator("text=一周内").click(timeout=3000)
        page.wait_for_timeout(2000)
    except Exception as e:
        print(f"Filter click: {e}")
    
    # 检查 .name-time-wrapper .time 的实际文本
    times = page.evaluate("""
        () => {
            const els = document.querySelectorAll('.name-time-wrapper .time');
            return Array.from(els).slice(0, 5).map(el => ({
                text: JSON.stringify(el.textContent),
                parent: el.parentElement ? el.parentElement.innerText.slice(0, 30) : ''
            }));
        }
    """)
    print("Time elements:")
    for t in times:
        print(f"  textContent={t['text']}, parent={t['parent']}")
    
    page.close()