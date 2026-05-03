"""诊断9条问题笔记的详情"""
import json, os, urllib.request
from pathlib import Path

APP_TOKEN = 'MtpRbyHq9aOP3csA3jVc6CYenuc'
TABLE_ID = 'tblvxlFAqO5hP4fD'

def get_token():
    app_id = os.environ.get('FEISHU_APP_ID', '')
    app_secret = os.environ.get('FEISHU_APP_SECRET', '')
    if not app_id:
        sf = Path(r'E:\translate\claw\xhs-auto-traffic-v2\secrets.json')
        if sf.exists():
            d = json.loads(sf.read_text(encoding='utf-8'))
            app_id = app_id or d.get('feishu_app_id', '')
            app_secret = app_secret or d.get('feishu_app_secret', '')
    url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
    payload = json.dumps({'app_id': app_id, 'app_secret': app_secret}).encode()
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp).get('tenant_access_token', '')

def get_all_records():
    token = get_token()
    all_records = []
    page_token = ""
    while True:
        url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records?page_size=100'
        if page_token:
            url += f"&page_token={page_token}"
        req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.load(resp)
            items = result.get('data', {}).get('items', [])
            all_records.extend(items)
            if not result.get('data', {}).get('has_more'):
                break
            page_token = result.get('data', {}).get('page_token', '')
    return all_records

target_ids = ['69f5c8d900000000360196f9', '69f1d781000000003503bd1f', 'test9876543210', 'test5555555555', '69ef3f8f0000000035026b3d', '69ee1e4d0000000036019efd', '69ee2bd1000000002003b231', '69edd4ab000000003502bdde', '69ece2e4000000003601fb4e']

records = get_all_records()
target_set = set(target_ids)

# Filter to just the target ones
matches = []
for rec in records:
    nid = rec.get('fields', {}).get('笔记ID', '')
    if nid in target_set:
        matches.append(rec)

output = []
for rec in matches:
    f = rec.get('fields', {})
    nid = f.get('笔记ID', '')
    output.append({
        'record_id': rec.get('record_id', ''),
        'note_id': nid,
        'title': f.get('标题', ''),
        'author': f.get('作者', ''),
        'reasons': f.get('筛选原因', ''),
        'content': f.get('正文摘要', ''),
    })

with open(r'E:\translate\claw\xhs-auto-traffic-v2\_probe_9_notes.json', 'w', encoding='utf-8') as out:
    json.dump(output, out, ensure_ascii=False, indent=2)

print(f'Found {len(output)}/{len(target_ids)} notes')
for item in output:
    print(f"  {item['note_id']} | reasons='{item['reasons']}' | title={item['title'][:40]}")
