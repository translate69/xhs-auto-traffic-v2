import sys, json, urllib.request, urllib.error, time

sys.path.insert(0, '.')

cookies = json.load(open('xhs_cookies.json'))
cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

# 从 Playwright 抓到的真实 header
x_s_common = "2UQAPsHC+aIjqArjwjHjNsQhPsHCH0rjNsQhPaHCH0c1PUhMHjIj2eHjwjQgynEDJ74AHjIj2ePjwjQhyoPTqBPT49pjHjIj2ecjwjH9N0q1+jHVHdWMH0ijP/SD8e4S+9GEPnz6GnI7wBTS80chJ0zD+eZI2nkxJ/WEJep7JBRhynLMPeZIPeG7P/q7+jHVHdW9H0ijHjIj2eqjwjHjNsQhwsHCJdpVJsIj2eDjwjFEPArE+/chPAPVHdWlPsHCPsIj2erlH0ijJfRUJnbVHjIj2erUH0ijJdpVJeVl+Aq9P0Z7+0LMP0rFHdF="
x_s = "XYS_2UQhPsHCH0c1PUhMHjIj2erjwjQhyoPTqBPT49pjHjIj2eHjwjQgynEDJ74AHjIj2ePjwjQTJdPIP/ZlgMqELnLF/rQI4e++Ggp9arMfagqhPL+Tp94E8LED+rMazf4+2/D7aSWE4pYt/fI62fG6yMZlz9MyyF4Y+rYMLL4i874z+MzC+pqMJBMS8ebrt9EEPLz3+/LAL98Qy98iGFM/cSiFJ9lePfi9zoYMt78HzeQL/e86z0SGzn4z/LHAzUuMPF8ky9lb8dqhLgpezSYx+MY0zaTPGF8o+pbD/pmynnh6wep+2dcIydmdwBY6P/QGa/mxqrk6PnTy+rlLz9pFL04aHjIj2ecjwjHjKc=="
x_t = str(int(time.time() * 1000))

url = "https://edith.xiaohongshu.com/api/sns/web/v2/user/me"

headers = {
    "Cookie": cookie_str,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://www.xiaohongshu.com/",
    "x-s-common": x_s_common,
    "x-s": x_s,
    "x-t": x_t,
    "x-b3-traceid": "4de4b0783d9e51ac",
    "x-xray-traceid": "ceebf3fd39e44b66290b9fccc0a313fa",
    "sec-ch-ua": '"Chromium";v="127", "Not)A;Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "accept": "application/json, text/plain, */*",
}

print("Testing with x-s-common header (from Playwright)...")
req = urllib.request.Request(url, headers=headers)
try:
    resp = urllib.request.urlopen(req, timeout=10)
    body = json.loads(resp.read())
    data = body.get('data', {})
    code = body.get('code')
    print(f"HTTP {resp.status} | code={code} | guest={data.get('guest')}")
    if not data.get('guest'):
        print(f"REAL USER: {data.get('nickname')} ({data.get('red_id')})")
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode()[:200]}")
except Exception as e:
    print(f"Error: {e}")

print("\nTesting WITHOUT x-s-common header...")
headers2 = {k: v for k, v in headers.items() if k not in ('x-s-common', 'x-s')}
req2 = urllib.request.Request(url, headers=headers2)
try:
    resp2 = urllib.request.urlopen(req2, timeout=10)
    body2 = json.loads(resp2.read())
    data2 = body2.get('data', {})
    code2 = body2.get('code')
    print(f"HTTP {resp2.status} | code={code2} | guest={data2.get('guest')}")
    if not data2.get('guest'):
        print(f"REAL USER: {data2.get('nickname')} ({data2.get('red_id')})")
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode()[:200]}")
except Exception as e:
    print(f"Error: {e}")
