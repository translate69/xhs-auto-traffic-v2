import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests
import json

# Read secrets
secrets = json.load(open("secrets.json", encoding="utf-8"))
app_id = secrets["feishu_app_id"]
app_secret = secrets["feishu_app_secret"]

# Get app access token
resp = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal",
    json={"app_id": app_id, "app_secret": app_secret},
    timeout=10
)
print(f"Token response: {resp.status_code} {resp.text[:200]}")

if resp.status_code == 200:
    token_data = resp.json()
    app_token = token_data.get("app_access_token")
    
    # Try to list records
    bitable_token = "MtpRbyHq9aOP3csA3jVc6CYenuc"
    table_id = "tblvxlFAqO5hP4fD"
    
    headers = {"Authorization": f"Bearer {app_token}"}
    resp2 = requests.get(
        f"https://open.feishu.cn/open-apis/bitable/v1/apps/{bitable_token}/tables/{table_id}/records?page_size=10",
        headers=headers, timeout=10
    )
    print(f"\nList records: {resp2.status_code}")
    if resp2.status_code == 200:
        data = resp2.json()
        items = data.get("data", {}).get("items", [])
        print(f"Total records: {len(items)}")
        for item in items:
            fields = item.get("fields", {})
            title = str(fields.get("标题", ""))[:40]
            nid = fields.get("note_id", "")
            print(f"  [{item['record_id']}] note_id={nid} title={title}")
    else:
        print(f"Error: {resp2.text[:300]}")
