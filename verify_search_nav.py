"""
verify_search_nav.py - 验证首页搜索回车是否生效
"""
import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config
from core.browser_manager import BrowserManager

def main():
    with BrowserManager() as (browser, context):
        page = context.new_page()
        
        print("1. 访问首页...")
        page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
        time.sleep(3)
        print(f"   当前URL: {page.url}")
        
        print("2. 找搜索框...")
        try:
            inp = page.wait_for_selector("#search-input", timeout=10000)
            print(f"   找到输入框: {inp}")
        except Exception as e:
            print(f"   ❌ 找不到 #search-input: {e}")
            page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/verify_no_input.png")
            print("   已截图: verify_no_input.png")
            return
        
        print("3. 点击输入框...")
        inp.click(timeout=3000)
        time.sleep(0.5)
        
        print("4. 输入关键词...")
        inp.fill("汕尾美食")
        
        print("5. 按回车...")
        inp.press("Enter")
        
        print("6. 等待3秒后检查URL...")
        time.sleep(3)
        print(f"   当前URL: {page.url}")
        
        print("7. 检查页面内容...")
        note_items = page.query_selector_all("section.note-item")
        print(f"   section.note-item 数量: {len(note_items)}")
        
        explore_items = page.query_selector_all("[class*='explore'] [class*='note-item']")
        print(f"   explore下的note-item: {len(explore_items)}")
        
        # 检查搜索结果相关元素
        search_result = page.query_selector(".search-result")
        print(f"   .search-result: {search_result}")
        
        # 打印当前页面 title
        print(f"   page.title: {page.title}")
        
        page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/verify_after_enter.png")
        print("   已截图: verify_after_enter.png")
        
        page.close()

if __name__ == "__main__":
    main()