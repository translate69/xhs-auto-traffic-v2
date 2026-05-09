import json, time
from playwright.sync_api import sync_playwright

with open(r'E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json', 'r') as f:
    cookies = json.load(f)
print(f'加载了 {len(cookies)} 个 cookie')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
    ctx = browser.new_context()
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto('https://www.xiaohongshu.com', timeout=15000)
    time.sleep(3)
    title = page.title()
    print(f'页面标题: {title}')
    mask = page.query_selector('.login-mask, .login-popup, [class*=login]')
    status = '无' if not mask else '有'
    print(f'登录遮罩: {status}')
    browser.close()
print('done')