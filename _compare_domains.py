import json, glob, os

v1 = glob.glob(r"E:\translate\claw\xhs-auto-traffic\*hs_cookies*.json")
v2 = glob.glob(r"E:\translate\claw\xhs-auto-traffic-v2\*hs_cookies*.json")

for f in v1 + v2:
    print(f"\n{'='*60}")
    print(f"File: {f}")
    try:
        cookies = json.load(open(f))
        print(f"Total: {len(cookies)} cookies")
        # Show domain and name for each cookie
        for c in cookies:
            print(f"  domain={c.get('domain','?'):25s} name={c['name']}")
    except Exception as e:
        print(f"Error: {e}")
