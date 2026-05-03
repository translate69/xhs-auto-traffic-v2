import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests
import json

secrets = json.load(open("secrets.json", encoding="utf-8"))
app_id = secrets["feishu_app_id"]
app_secret = secrets["feishu_app_secret"]

# Get token
resp = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal",
    json={"app_id": app_id, "app_secret": app_secret},
    timeout=10
)
token = resp.json()["app_access_token"]
headers = {"Authorization": f"Bearer {token}"}

bitable_token = "MtpRbyHq9aOP3csA3jVc6CYenuc"
table_id = "tblvxlFAqO5hP4fD"

# 先看全部记录
resp = requests.get(
    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{bitable_token}/tables/{table_id}/records?page_size=500",
    headers=headers, timeout=10
)
items = resp.json()["data"]["items"]
print(f"总记录数: {len(items)}")

# 找到深圳相关的 record_ids
delete_ids = []
for item in items:
    fields = item.get("fields", {})
    title = str(fields.get("标题", ""))[:50]
    if "深圳" in title or "五一出游散心女搭子" in title:
        delete_ids.append(item["record_id"])
        print(f"将删除: [{item['record_id']}] {title}")

print(f"\n共 {len(delete_ids)} 条待删除")

# 逐条删除
for rid in delete_ids:
    r = requests.delete(
        f"https://open.feishu.cn/open-apis/bitable/v1/apps/{bitable_token}/tables/{table_id}/records/{rid}",
        headers=headers, timeout=10
    )
    print(f"删除 {rid}: {r.status_code} {r.json().get('msg', '')}")
