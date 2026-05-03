import sys, json, time, subprocess, os
sys.path.insert(0, '.')

# Step 1: Close Chrome
print("Closing Chrome...")
result = subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'],
                       capture_output=True, text=True)
if result.returncode == 0:
    print("Chrome closed.")
else:
    print("No Chrome process found.")
time.sleep(2)

# Step 2: Launch Playwright with user-data-dir via persistent_context
print("Launching Playwright with Chrome user-data-dir...")
from playwright.sync_api import sync_playwright

USER_DATA_DIR = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data')
print(f"User data dir: {USER_DATA_DIR}")

try:
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,
        )
        page = context.new_page()

        page.goto('https://www.xiaohongshu.com', timeout=60000)
        page.wait_for_timeout(5000)

        url = page.url
        print(f"Final URL: {url}")

        try:
            modal = page.locator(".login-modal")
            if modal.is_visible(timeout=3000):
                print("RESULT: Login modal present -> NOT logged in")
            else:
                print("RESULT: No login modal -> LOGGED IN!")
        except:
            print("RESULT: No login modal found")

        cookies = context.cookies()
        ws = next((c for c in cookies if c['name'] == 'web_session'), None)
        if ws:
            print(f"web_session: {ws['value'][:40]}...")
        else:
            print("web_session NOT in browser cookies")

        context.close()
        print("Done.")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
