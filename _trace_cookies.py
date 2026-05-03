import sys, json, time
sys.path.insert(0, '.')
from core.browser_manager import BrowserManager

def trace_cookies():
    cookies = json.load(open('xhs_cookies.json'))
    ws = next((c for c in cookies if c['name'] == 'web_session'), None)
    print(f"[FILE] web_session: {ws['value']}")
    print(f"[FILE] domain: {ws.get('domain')}")
    print(f"[FILE] path: {ws.get('path')}")
    print(f"[FILE] size: {len(cookies)} cookies\n")

    with BrowserManager(headless=False) as (browser, context):
        # 添加 cookies
        for c in cookies:
            context.add_cookies([c])
        print(f"[ADDED] {len(cookies)} cookies to context\n")

        # 检查 context 里 cookies
        after_add = context.cookies()
        ws_after = next((c for c in after_add if c['name'] == 'web_session'), None)
        print(f"[CONTEXT] web_session after add: {ws_after['value'] if ws_after else 'NOT FOUND'}")
        print(f"[CONTEXT] all cookies in context ({len(after_add)}):")
        for c in after_add:
            print(f"  {c['name']} | domain={c['domain']} | value={c['value'][:30]}...")
        print()

        # 打开小红书
        page = context.new_page()
        print("[NAVIGATE] to https://www.xiaohongshu.com ...")
        page.goto("https://www.xiaohongshu.com", timeout=60000)
        page.wait_for_timeout(5000)
        print(f"[URL] after navigate: {page.url}\n")

        # 导航后检查 cookies（看服务端有没有修改）
        after_nav = context.cookies()
        ws_nav = next((c for c in after_nav if c['name'] == 'web_session'), None)
        print(f"[AFTER_NAV] web_session: {ws_nav['value'] if ws_nav else 'NOT FOUND'}")
        print(f"[AFTER_NAV] all cookies ({len(after_nav)}):")
        for c in after_nav:
            print(f"  {c['name']} | domain={c['domain']} | value={c['value'][:30]}...")

        # 检查 localStorage / sessionStorage
        print("\n[STORAGE] localStorage:")
        try:
            ls = page.evaluate("() => JSON.stringify(localStorage)")
            print(f"  {ls[:300]}")
        except:
            print("  (empty or error)")

        print("\n[STORAGE] sessionStorage:")
        try:
            ss = page.evaluate("() => JSON.stringify(sessionStorage)")
            print(f"  {ss[:300]}")
        except:
            print("  (empty or error)")

        page.close()

if __name__ == "__main__":
    trace_cookies()
