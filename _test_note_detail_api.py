import sys, json, time, urllib.request, urllib.parse
sys.path.insert(0, '.')

# 笔记详情 API
note_id = "69f1020c000000001a02e734"

cookies = json.load(open('xhs_cookies.json'))
cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

headers = {
    "Cookie": cookie_str,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Referer": f"https://www.xiaohongshu.com/explore/{note_id}",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

# 笔记详情 API - 尝试不同版本
for path in [
    f"/api/sns/web/v1/feed?note_id={note_id}&source=search_notes&extra_params=%7B%7D",
    f"/api/sns/web/v1/note/{note_id}",
]:
    url = f"https://edith.xiaohongshu.com{path}"
    print(f"\nTrying: {url[:100]}...")
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        body = json.loads(resp.read())
        print(f"  code={body.get('code')} msg={body.get('msg')}")
        data = body.get('data', {})
        if data:
            print(f"  SUCCESS! title={str(data.get('title', data.get('note_card', {}).get('title', '?')))[:50]}")
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.read().decode()[:200]}")
    except Exception as e:
        print(f"  Error: {e}")
