import sys, os, json, time
sys.path.insert(0, '.')

print("Attempting to get cookies via Chrome DevTools Protocol...")
print("Make sure Chrome is running with remote debugging enabled.")
print("To start Chrome with debugging: chrome.exe --remote-debugging-port=9222")
print()

import urllib.request, urllib.error

DEBUG_URL = "http://localhost:9222/json"

try:
    # Get list of targets
    req = urllib.request.Request(DEBUG_URL)
    resp = urllib.request.urlopen(req, timeout=5)
    targets = json.loads(resp.read())
    print(f"Found {len(targets)} Chrome targets:")
    for t in targets:
        print(f"  {t.get('type')} - {t.get('title', 'no title')[:50]} | url={t.get('url', 'no url')[:80]}")
except Exception as e:
    print(f"Cannot connect to Chrome DevTools: {e}")
    print()
    print("Chrome is NOT running with remote debugging.")
    print("Please start Chrome manually with:")
    print('  chrome.exe --remote-debugging-port=9222')
    sys.exit(1)
