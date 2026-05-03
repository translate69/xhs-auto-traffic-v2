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
    page.set_default_timeout(20000)

    # Go to explore
    page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
    time.sleep(3)

    # Get first note href
    note_href = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        return link ? link.getAttribute('href') : '';
    }""")
    print("Note href:", note_href[:80])

    # Analyze what clicking the note actually does
    click_analysis = page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        if (!link) return 'no link';
        
        return {
            href: link.getAttribute('href'),
            onclick: link.getAttribute('onclick'),
            target: link.getAttribute('target'),
            class: link.className,
            dataHref: link.getAttribute('data-href'),
            // Check if it's a regular anchor or has custom click handler
            tagName: link.tagName,
            outerHTML: link.outerHTML.slice(0, 300)
        };
    }""")
    print("\nClick analysis:", json.dumps(click_analysis, ensure_ascii=False, indent=2))

    # Try: click with page.click (which intercepts reds-mask)
    # and see what network requests are made
    print("\n--- Monitoring network requests during click ---")
    
    # Set up route interception to see what's happening
    def handle_response(response):
        url = response.url
        if 'note' in url or 'feed' in url or 'sns' in url:
            print(f"  RESP: {response.status} {url[:80]}")
    
    page.on("response", handle_response)
    
    # Now click via JS and capture what happens
    page.evaluate("""() => {
        const link = document.querySelector('section.note-item a.cover.mask');
        if (link) link.click();
    }""")
    time.sleep(5)
    
    print("\nURL after JS click:", page.url)
    print("Title:", page.title()[:60])

    browser.close()
    print("\nDone")