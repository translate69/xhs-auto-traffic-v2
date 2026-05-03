import sys, json, time, re, urllib.request, urllib.error
sys.path.insert(0, '.')

# 测试直接用 requests 调用搜索 API
cookies = json.load(open('xhs_cookies.json'))
cookie_str = "; ".join([f"{c['name']}={urllib.parse.quote(c['value'], safe='')}" for c in cookies])

import urllib.parse

# 用原始值，不用 quote
cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

headers = {
    "Cookie": cookie_str,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://www.xiaohongshu.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 搜索 API
keyword = "汕尾美食"
url = f"https://edith.xiaohongshu.com/api/sns/web/v1/search/notes?keyword={urllib.parse.quote(keyword)}&page=1&page_size=20&search_id=&sort=general&note_type=0"

print(f"URL: {url}")
print(f"Cookies (first 100): {cookie_str[:100]}...")

req = urllib.request.Request(url, headers=headers)
try:
    resp = urllib.request.urlopen(req, timeout=10)
    body = json.loads(resp.read())
    code = body.get('code')
    msg = body.get('msg')
    print(f"\nHTTP {resp.status} | code={code} | msg={msg}")
    data = body.get('data', {})
    items = data.get('items', [])
    print(f"Items count: {len(items)}")
    if items:
        for item in items[:3]:
            print(f"  - {item.get('title', 'no title')[:30]} | {item.get('user', {}).get('nickname', '')}")
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8', errors='replace')
    print(f"HTTP Error {e.code}: {body[:500]}")
except Exception as e:
    print(f"Error: {e}")
