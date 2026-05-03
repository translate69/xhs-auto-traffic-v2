"""查 Bitable 表实际字段"""
import sys
import json
import urllib.request

sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout.reconfigure(encoding="utf-8")

import config
from utils.feishu_client import _get_tenant_token

token = _get_tenant_token()

url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{config.FEISHU_APP_TOKEN}/tables/{config.FEISHU_TABLE_ID}/fields"

req = urllib.request.Request(
    url,
    headers={"Authorization": f"Bearer {token}"},
    method="GET",
)

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.load(resp)
        items = result.get("data", {}).get("items", [])
        print(f"表里共有 {len(items)} 个字段:\n")
        for f in items:
            print(f"  [{f['field_id']}] {f['field_name']} (type={f.get('type')})")
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8")
    print(f"HTTP {e.code}: {body}")
