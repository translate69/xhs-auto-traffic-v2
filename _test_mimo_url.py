import urllib.request, json

api_key = "tp-c8fsp0ek3jmpy1a19bfuognrwzs3gsn32pku1rlydehqxbga"

# Test 1: models list
print("=== Test 1: GET /v1/models ===")
try:
    req = urllib.request.Request(
        "https://token-plan-cn.xiaomimimo.com/v1/models",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read())
    models = [m["id"] for m in data.get("data", [])]
    print(f"OK: {len(models)} models")
    for m in models:
        print(f"  {m}")
except Exception as e:
    print(f"FAIL: {type(e).__name__}: {e}")

# Test 2: chat completions (simple test)
print("\n=== Test 2: POST /v1/messages (chat) ===")
try:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError
    payload = json.dumps({
        "model": "MiMo-V2.5-Pro",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "say hi"}]
    }).encode()
    req = Request(
        "https://token-plan-cn.xiaomimimo.com/v1/messages",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        },
        method="POST"
    )
    resp = urlopen(req, timeout=10)
    result = json.loads(resp.read())
    print(f"OK: {result}")
except HTTPError as e:
    body = e.read().decode("utf-8", errors="replace")
    print(f"HTTP {e.code}: {body[:500]}")
except Exception as e:
    print(f"FAIL: {type(e).__name__}: {e}")
