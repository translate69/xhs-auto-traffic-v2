import sys
sys.path.insert(0, "E:/translate/claw/xhs-auto-traffic-v2")
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    import json
    with open("E:/translate/claw/xhs-auto-traffic-v2/xhs_cookies.json", encoding="utf-8") as f:
        cookies = json.load(f)

    print("Cookies being loaded:")
    for c in cookies[:3]:
        print(f"  {c['name']}={c['value'][:20]}...")

    context.add_cookies(cookies)

    page = context.new_page()

    # Go to search_result and wait longer for notes to load
    page.goto("https://www.xiaohongshu.com/search_result?keyword=汕尾美食&type=51", wait_until="domcontentloaded")
    print(f"\n1. Initial URL: {page.url}")

    # Wait for notes - give it 60 seconds
    try:
        page.wait_for_selector("section.note-item", timeout=60000)
        print(f"   Notes appeared! count: {len(page.query_selector_all('section.note-item'))}")
    except Exception as e:
        print(f"   Notes did NOT appear in 60s: {e}")

    # Check current state
    print(f"   Current URL: {page.url}")
    notes = page.query_selector_all("section.note-item")
    print(f"   section.note-item count: {len(notes)}")

    # Check for any loading indicators
    loading = page.query_selector(".loading, [class*='loading'], .skeleton")
    print(f"   Loading indicators: {loading}")

    # Check page text for hints
    page_text = page.text_content("body")
    if "暂无" in page_text or "没有" in page_text:
        print(f"   Page has '暂无' or '没有' text")
    if "登录" in page_text or "login" in page_text.lower():
        print(f"   Page has login text")

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_sr_60s.png")

    # Try scrolling
    page.evaluate("window.scrollTo(0, 500)")
    time.sleep(2)
    notes2 = page.query_selector_all("section.note-item")
    print(f"\n2. After scroll: {len(notes2)} notes")

    browser.close()
    print("\nDone")