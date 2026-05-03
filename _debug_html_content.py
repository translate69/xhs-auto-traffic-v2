import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
import time
import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})

    cookies = json.load(open(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json"))
    context.add_cookies(cookies)

    page = context.new_page()
    page.set_default_timeout(15000)

    # Go to explore, click note, then check raw HTML
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("1. Note href:", note_href[:80])

    page.evaluate("""() => {
        document.querySelector('section.note-item a.cover.mask').click();
    }""")
    time.sleep(5)
    print("2. URL:", page.url)

    # Check raw HTML content
    html_content = page.content()
    print("3. HTML length:", len(html_content))

    # Check for __INITIAL_STATE__ in the HTML
    import re
    m = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html_content, re.DOTALL)
    if m:
        print("3b. __INITIAL_STATE__ found in HTML, length:", len(m.group(1)))
        # Try to parse it
        try:
            state = json.loads(m.group(1))
            print("3c. Parsed successfully!")
            # Look for note data
            if 'note' in state:
                print("3d. state.note:", json.dumps(state['note'], ensure_ascii=False)[:300])
            if 'feed' in state:
                print("3e. state.feed:", json.dumps(state['feed'], ensure_ascii=False)[:300])
        except Exception as e:
            print("3c. Parse error:", e)
    else:
        print("3b. __INITIAL_STATE__ NOT in HTML")

    # Check for any note detail data in HTML
    note_patterns = ['noteDetailMap', 'noteId', 'note_id', '"title"', 'detail-desc', '#detail-desc']
    for pat in note_patterns:
        if pat in html_content:
            print(f"4. Found '{pat}' in HTML")
            idx = html_content.find(pat)
            print(f"   Context: ...{html_content[max(0,idx-20):idx+50]}...")

    browser.close()
    print("\nDone")