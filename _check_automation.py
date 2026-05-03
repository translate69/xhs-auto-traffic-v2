import sys, json, time
sys.path.insert(0, '.')
from core.browser_manager import BrowserManager

def check_automation():
    with BrowserManager(headless=False) as (browser, context):
        page = context.new_page()
        page.goto("https://www.xiaohongshu.com", timeout=60000)
        page.wait_for_timeout(3000)

        # 检查 webdriver 属性
        webdriver = page.evaluate("() => navigator.webdriver")
        print(f"navigator.webdriver: {webdriver}")

        # 检查 Chrome runtime
        plugins = page.evaluate("() => navigator.plugins.length")
        print(f"navigator.plugins.length: {plugins}")

        # 检查 language
        languages = page.evaluate("() => navigator.languages")
        print(f"navigator.languages: {languages}")

        # 检查 platform
        platform = page.evaluate("() => navigator.platform")
        print(f"navigator.platform: {platform}")

        # 检查是否 headless
        user_agent = page.evaluate("() => navigator.userAgent")
        print(f"User-Agent: {user_agent}")

        # 检查 webdriver 是否被修改
        result = page.evaluate("() => window.webdriver")
        print(f"window.webdriver: {result}")

        # Try to detect automation
        chrome = page.evaluate("() => chrome.runtime")
        print(f"chrome.runtime: {chrome}")

        # Check cookie with full domain
        all_cookies = context.cookies()
        print(f"\nTotal cookies: {len(all_cookies)}")
        for c in all_cookies:
            print(f"  {c['domain']}: {c['name']} = {c['value'][:30]}...")

        page.close()

if __name__ == "__main__":
    check_automation()
