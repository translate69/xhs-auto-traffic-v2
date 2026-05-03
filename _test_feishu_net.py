import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json, urllib.request

# Test connectivity to Feishu
secrets = json.load(open("secrets.json", encoding="utf-8"))
app_id = secrets["feishu_app_id"]
app_secret = secrets["feishu_app_secret"]

payload = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode("utf-8")
headers = {"Content-Type": "application/json"}
req = urllib.request.Request(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    data=payload, headers=headers, method="POST"
)

print("Testing Feishu API connectivity...")
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.load(resp)
        print(f"Response: {result}")
        print(f"Token: {result.get('tenant_access_token', '')[:30]}...")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
