import sys, json, urllib.request
sys.path.insert(0, '.')

def test_via_playwright_but_http():
    cookies = json.load(open('xhs_cookies.json'))
    ws = next((c for c in cookies if c['name'] == 'web_session'), None)
    print(f"web_session: {ws['value']}")

    # 直接用 urllib，不走 Playwright 浏览器
    url = "https://edith.xiaohongshu.com/api/sns/web/v2/user/me"
    cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
    headers = {
        "Cookie": cookie_str,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Referer": "https://www.xiaohongshu.com/",
    }

    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        body = json.loads(resp.read())
        data = body.get('data', {})
        print(f"HTTP 200 - guest={data.get('guest')}")
        if not data.get('guest'):
            print(f"REAL USER: red_id={data.get('red_id')}, nick={data.get('nickname')}")
        else:
            print(f"GUEST user")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_via_playwright_but_http()
