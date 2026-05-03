import sys, os, json, time, subprocess, urllib.request, urllib.error

# Step 1: Close Chrome
print("[1] Closing Chrome...")
result = subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True, text=True)
print(f"   Result: {result.returncode}")
time.sleep(2)

# Step 2: Start Chrome with remote debugging
print("[2] Starting Chrome with remote debugging on port 9222...")
chrome_cmd = [
    os.path.join(os.environ['PROGRAMFILES'], 'Google', 'Chrome', 'Application', 'chrome.exe'),
    '--remote-debugging-port=9222',
    '--user-data-dir=' + os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data'),
]
print(f"   Command: {' '.join(chrome_cmd)}")
proc = subprocess.Popen(chrome_cmd)
print(f"   PID: {proc.pid}")

print("\n[3] Waiting 5s for Chrome to start...")
time.sleep(5)

print("\n[4] Connecting to Chrome DevTools...")
try:
    req = urllib.request.Request("http://localhost:9222/json")
    resp = urllib.request.urlopen(req, timeout=5)
    targets = json.loads(resp.read())
    print(f"   Found {len(targets)} targets:")
    for t in targets:
        print(f"   - {t.get('type','?")} | {t.get('title","?")[:50]}")
except Exception as e:
    print(f"   ERROR: {e}")
    print("   Chrome may have closed or blocked the port.")

print("\n[5] If Chrome opened, please:")
print("   1. Log in to Xiaohongshu in Chrome")
print("   2. Navigate to any Xiaohongshu page")
print("   3. Press Enter here (we'll reconnect)")
input("Press Enter to try connecting again...")

print("\n[6] Trying to get cookies from Chrome...")
try:
    req = urllib.request.Request("http://localhost:9222/json")
    resp = urllib.request.urlopen(req, timeout=5)
    targets = json.loads(resp.read())
    ws_target = None
    for t in targets:
        if 'xiaohongshu' in t.get('url', '').lower() or 'Chrome' in t.get('title', ''):
            ws_target = t
            break
    if ws_target:
        print(f"   Target: {ws_target}")
        ws_url = ws_target.get('webSocketDebuggerUrl', '')
        print(f"   WS URL: {ws_url[:80]}...")
except Exception as e:
    print(f"   ERROR: {e}")

print("\nDone.")
