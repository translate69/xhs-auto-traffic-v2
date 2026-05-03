[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Set-Location "E:\translate\claw\xhs-auto-traffic-v2"
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONPATH = "E:\translate\claw\xhs-auto-traffic-v2"
python -c "
import sys
sys.path.insert(0, '.')
from core.browser_manager import BrowserManager

print('启动 Playwright 浏览器...')
with BrowserManager(headless=False) as (browser, context):
    page = context.new_page()
    print('打开小红书搜索页...')
    page.goto('https://www.xiaohongshu.com/search_result?keyword=汕尾旅游&type=51', wait_until='domcontentloaded', timeout=30000)
    print('页面标题:', page.title())
    print('当前 URL:', page.url)
    print('是否含 search_result:', 'search_result' in page.url)
" 2>&1