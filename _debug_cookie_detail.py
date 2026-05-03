import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
import time
from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    cookies = json.load(open(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json"))
    context.add_cookies(cookies)

    page = context.new_page()
    page.set_default_timeout(15000)

    print("=== Cookie Debug ===")
    
    # Check cookies on explore page
    print("\n1. On explore page...")
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    print("   URL:", page.url)
    
    ctx_cookies = page.context.cookies()
    print(f"   Context cookies: {len(ctx_cookies)}")
    for c in ctx_cookies:
        print(f"   {c['name']}: {c['value'][:30]}... (domain={c['domain']}, secure={c['secure']})")
    
    # Check if there's a web_session cookie
    ws = [c for c in ctx_cookies if c['name'] == 'web_session']
    print(f"   web_session cookie: {ws[0]['value'][:40] if ws else 'NOT FOUND'}")
    print(f"   web_session domain: {ws[0]['domain'] if ws else 'N/A'}")
    print(f"   web_session secure: {ws[0]['secure'] if ws else 'N/A'}")

    # Now check cookies when trying to access a note
    print("\n2. Navigate to note and check cookies...")
    first_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    
    # Open new page (same context)
    page2 = context.new_page()
    note_url = "https://www.xiaohongshu.com" + first_href
    print(f"   Going to: {note_url[:80]}")
    page2.goto(note_url, wait_until="domcontentloaded", timeout=15000)
    time.sleep(3)
    print(f"   URL: {page2.url}")
    
    ctx_cookies2 = page2.context.cookies()
    ws2 = [c for c in ctx_cookies2 if c['name'] == 'web_session']
    print(f"   web_session on note page: {ws2[0]['value'][:40] if ws2 else 'NOT FOUND'}")
    
    # Check what cookies the page actually has at note URL
    note_cookies = page2.evaluate("""() => {
        // Check document.cookies
        return document.cookie;
    }""")
    print(f"   document.cookie on note page: {note_cookies[:100] if note_cookies else 'EMPTY'}")

    page2.close()
    browser.close()
    print("\nDone")