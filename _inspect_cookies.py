import json

c = json.load(open('xhs_cookies.json'))
print(f'总数: {len(c)}')
for x in c:
    print(f"  {x['name']}: domain={x.get('domain','?')} secure={x.get('secure','?')} httpOnly={x.get('httpOnly','?')} sameSite={x.get('sameSite','?')}")
