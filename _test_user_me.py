import sys, json, urllib.request

sys.path.insert(0, '.')

cookies = json.load(open('xhs_cookies.json'))
ws = next((c for c in cookies if c['name'] == 'web_session'), None)
print(f"web_session: {ws['value']}")

# 直接发 HTTP 请求到 user/me
url = "https://edith.xiaohongshu.com/api/sns/web/v2/user/me"

cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
headers = {
    "Cookie": cookie_str,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://www.xiaohongshu.com/",
    "x-s": "test",
    "x-t": "test",
}

req = urllib.request.Request(url, headers=headers)
try:
    resp = urllib.request.urlopen(req, timeout=10)
    body = json.loads(resp.read())
    print(f"\nHTTP {resp.status}")
    print(f"code: {body.get('code')}")
    print(f"msg: {body.get('msg')}")
    print(f"data: {json.dumps(body.get('data', {}), ensure_ascii=False)[:300]}")
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8', errors='replace')
    print(f"\nHTTP Error {e.code}: {body[:300]}")
except Exception as e:
    print(f"\nError: {e}")
