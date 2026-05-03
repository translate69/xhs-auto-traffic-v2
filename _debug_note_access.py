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

    print("=== Testing note access with different approaches ===")

    # Go to explore
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)
    print("1. Explore URL:", page.url)

    # Get a fresh note URL
    first_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : null;
    }""")
    print("   First note href:", first_href[:80])

    # Try WITHOUT xsec_token
    note_id = first_href.split('/explore/')[1].split('?')[0] if '/explore/' in first_href else None
    if note_id:
        print(f"\n2. Test without xsec_token: /explore/{note_id}")
        page2 = context.new_page()
        page2.goto(f"https://www.xiaohongshu.com/explore/{note_id}", wait_until="domcontentloaded")
        time.sleep(3)
        print("   URL:", page2.url)
        if "/login" in page2.url:
            print("   -> Login required")
        elif "/404" in page2.url:
            print("   -> 404")
        else:
            detail = page2.query_selector("#detail-desc")
            print("   Has #detail-desc:", detail is not None)
        page2.close()

    # Try WITH xsec_token from the href
    print(f"\n3. Test WITH xsec_token...")
    page3 = context.new_page()
    page3.goto(f"https://www.xiaohongshu.com{first_href}", wait_until="domcontentloaded")
    time.sleep(3)
    print("   URL:", page3.url)
    if "/login" in page3.url:
        print("   -> Login required")
    else:
        detail = page3.query_selector("#detail-desc")
        print("   Has #detail-desc:", detail is not None)
    page3.close()

    # Now test: does explore page itself show note descriptions (no detail click needed)?
    print("\n4. Check if explore notes have descriptions...")
    descr_in_list = page.evaluate("""() => {
        const notes = document.querySelectorAll('section.note-item');
        const results = [];
        for (let i = 0; i < Math.min(5, notes.length); i++) {
            const note = notes[i];
            // Look for description text within the note card
            const title = note.querySelector('.title span');
            const cover = note.querySelector('.cover img');
            const interactive = note.querySelector('.interactive');
            results.push({
                index: i,
                title: title ? title.textContent.trim().slice(0, 40) : '',
                hasInteractive: !!interactive,
                textContent: note.textContent.slice(0, 80).trim()
            });
        }
        return results;
    }""")
    print("   Notes in list:", descr_in_list)

    browser.close()
    print("\nDone")