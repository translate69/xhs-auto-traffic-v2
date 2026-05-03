import sys, json
sys.path.insert(0, '.')
from core.browser_manager import BrowserManager

print("=== xhs_cookies.json 完整内容 ===")
file_cookies = json.load(open('xhs_cookies.json'))
print(f"Total: {len(file_cookies)} cookies\n")
for c in file_cookies:
    print(f"  {c['name']}={c['value'][:40]}... domain={c.get('domain','?')} secure={c.get('secure','?')} httpOnly={c.get('httpOnly','?')} sameSite={c.get('sameSite','?')}")

print("\n=== 模拟请求：生成 Cookie header ===")
cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in file_cookies])
print(f"Cookie header:\n{cookie_header[:300]}...")

print("\n=== 关键差异检测 ===")
names = {c['name'] for c in file_cookies}
critical = ['a1', 'webId', 'web_session', 'xsecappid', 'websectiga', 'acw_tc', 'ets']
for name in critical:
    status = "IN FILE" if name in names else "MISSING"
    print(f"  {name}: {status}")