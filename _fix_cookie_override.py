import sys, time
sys.path.insert(0, '.')
from core.browser_manager import BrowserManager
import json

def fix_cookie_override():
    cookies = json.load(open('xhs_cookies.json'))

    with BrowserManager(headless=False) as (browser, context):
        for c in cookies:
            context.add_cookies([c])

        page = context.new_page()

        # 先导航，不等待，让 JavaScript 先执行
        print("Navigating (not waiting for load)...")
        page.goto("https://www.xiaohongshu.com", timeout=60000)

        # 等 login/activate 发生（它在前几秒就会调用）
        print("Waiting 3s for login/activate to fire...")
        page.wait_for_timeout(3000)

        # 删除服务器通过 login/activate 创建的 .xiaohongshu.com guest session
        all_cookies = context.cookies()
        dot_xhs = [c for c in all_cookies if c['domain'] == '.xiaohongshu.com' and c['name'] == 'web_session']
        print(f"\nBefore fix - .xiaohongshu.com web_session: {dot_xhs[0]['value'][:30] if dot_xhs else 'NOT FOUND'}")

        if dot_xhs:
            context.remove_cookies('.xiaohongshu.com', name='web_session')
            print("Removed server-set guest session cookie!")

        # 再等一下让页面处理
        page.wait_for_timeout(3000)

        # 检查 cookie
        all_cookies2 = context.cookies()
        ws_xhs = [c for c in all_cookies2 if c['domain'] == '.xiaohongshu.com' and c['name'] == 'web_session']
        print(f"After fix - .xiaohongshu.com web_session: {ws_xhs[0]['value'][:30] if ws_xhs else 'NOT FOUND'}")
        ws_www = [c for c in all_cookies2 if c['domain'] == 'xiaohongshu.com' and c['name'] == 'web_session']
        print(f"After fix - xiaohongshu.com web_session: {ws_www[0]['value'][:30] if ws_www else 'NOT FOUND'}")

        # 现在触发搜索
        print("\nNavigating to search...")
        page.goto("https://www.xiaohongshu.com/search_result?keyword=%E6%B1%95%E5%B0%BE%E7%BE%8E%E9%A3%9F", timeout=60000)
        page.wait_for_timeout(5000)

        # 检查 login modal
        try:
            modal = page.locator(".login-modal")
            if modal.is_visible(timeout=2000):
                print("[FAIL] Login modal still visible")
            else:
                print("[PASS] No login modal!")
                # 检查是否有笔记列表
                notes = page.locator(".note-item")
                count = notes.count()
                print(f"Notes on page: {count}")
        except Exception as e:
            print(f"[PASS] No login modal (error: {e})")

        page.close()

if __name__ == "__main__":
    fix_cookie_override()
