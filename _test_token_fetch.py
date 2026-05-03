import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json, urllib.request, os

# Test _get_tenant_token directly
app_id = os.environ.get("FEISHU_APP_ID", "")
app_secret = os.environ.get("FEISHU_APP_SECRET", "")

if not app_id or not app_secret:
    secrets = json.load(open("secrets.json", encoding="utf-8"))
    app_id = app_id or secrets.get("feishu_app_id", "")
    app_secret = app_secret or secrets.get("feishu_app_secret", "")

print(f"app_id: {app_id}")
print(f"app_secret: {app_secret[:10]}...")

payload = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode("utf-8")
headers = {"Content-Type": "application/json"}
req = urllib.request.Request(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    data=payload, headers=headers, method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.load(resp)
        token = result.get("tenant_access_token", "")
        print(f"Token: {token[:30]}...")
        print(f"Success! code={result.get('code')}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

# Now test load_existing_note_ids
print("\nTesting load_existing_note_ids...")
sys.path.insert(0, '.')
from utils.feishu_client import load_existing_note_ids
ids = load_existing_note_ids()
print(f"Existing note_ids count: {len(ids)}")
print(f"First 3: {list(ids)[:3]}")
