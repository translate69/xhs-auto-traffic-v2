import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests, json

secrets = json.load(open("secrets.json", encoding="utf-8"))
app_id = secrets["feishu_app_id"]
app_secret = secrets["feishu_app_secret"]

# Get token
resp = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": app_id, "app_secret": app_secret}, timeout=15
)
token = resp.json()["tenant_access_token"]
headers = {"Authorization": f"Bearer {token}"}

bitable_token = "MtpRbyHq9aOP3csA3jVc6CYenuc"
table_id = "tblvxlFAqO5hP4fD"

# Get all records
resp = requests.get(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{bitable_token}/tables/{table_id}/records?page_size=500",
    headers=headers, timeout=15
)
items = resp.json()["data"]["items"]
print(f"Total records: {len(items)}")

# Delete test record + 深圳 records
delete_ids = []
for item in items:
    fields = item.get("fields", {})
    title = str(fields.get("标题", ""))
    nid = str(fields.get("note_id", ""))
    if nid == "test999999999" or "深圳" in title:
        delete_ids.append(item["record_id"])
        print(f"Delete: [{item['record_id']}] {title[:40]}")

print(f"\nDeleting {len(delete_ids)} records...")
for rid in delete_ids:
    r = requests.delete(
        f"https://open.feishu.cn/open-apis/bitable/v1/apps/{bitable_token}/tables/{table_id}/records/{rid}",
        headers=headers, timeout=15
    )
    print(f"  {rid}: {r.json().get('msg', r.text[:50])}")
