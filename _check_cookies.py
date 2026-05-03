import json, sys, time
sys.path.insert(0, 'E:/translate/claw/xhs-auto-traffic-v2')

with open('E:/translate/claw/xhs-auto-traffic-v2/xhs_cookies.json', encoding='utf-8') as f:
    cookies = json.load(f)

print(f'Total: {len(cookies)} cookies')
for c in cookies[:8]:
    exp = c.get('expirationDate', 0)
    exp_str = time.strftime('%Y-%m-%d', time.localtime(exp)) if exp else 'session'
    print(f'  {c["name"]} | domain={c["domain"]} | expires={exp_str}')

now = time.time()
expired = [c for c in cookies if c.get('expirationDate') and c['expirationDate'] < now]
print(f'Expired: {len(expired)}, Valid: {len(cookies)-len(expired)}')