import urllib.request, json

api_key = "tp-c8fsp0ek3jmpy1a19bfuognrwzs3gsn32pku1rlydehqxbga"
url = "https://token-plan-cn.xiaomimimo.com/v1/models"

req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
try:
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read())
    models = [m["id"] for m in data.get("data", [])]
    print(f"✅ API Key 正常，共 {len(models)} 个模型:")
    for m in models:
        print(f"  {m}")
except Exception as e:
    print(f"❌ API Key 测试失败: {e}")
