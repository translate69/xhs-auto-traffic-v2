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
    page.set_default_timeout(20000)

    # Test: Get notes from homepage search flow and check their content
    print("=== Homepage search flow test ===")
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    print("Homepage URL:", page.url)

    # Find and fill search
    search_input = page.wait_for_selector("#search-input", timeout=10000)
    search_input.fill("汕尾美食")
    time.sleep(0.5)
    page.keyboard.press("Enter")
    time.sleep(5)
    print("After Enter URL:", page.url)
    print("Notes:", len(page.query_selector_all("section.note-item")))

    # Get note titles and see what content we have
    notes_info = page.evaluate("""() => {
        const notes = document.querySelectorAll('section.note-item');
        return Array.from(notes).slice(0, 5).map((note, i) => {
            const title = note.querySelector('.title span');
            const author = note.querySelector('.name-time-wrapper .name');
            const time = note.querySelector('.name-time-wrapper .time');
            const link = note.querySelector('a.cover.mask');
            return {
                index: i,
                title: title ? title.textContent.trim().slice(0, 50) : '',
                author: author ? author.textContent.trim() : '',
                time: time ? time.textContent.trim() : '',
                href: link ? link.getAttribute('href') : ''
            };
        });
    }""")
    print("\nNotes from homepage search:")
    for n in notes_info:
        print(f"  [{n['index']}] title={n['title'][:40]} author={n['author']} time={n['time']}")
        print(f"       href={n['href'][:80]}")

    # Check the note item HTML structure
    first_note_html = page.evaluate("""() => {
        const note = document.querySelector('section.note-item');
        return note ? note.outerHTML.slice(0, 800) : 'not found';
    }""")
    print("\nFirst note HTML:")
    print(first_note_html[:500])

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/debug_homepage_search.png")
    browser.close()
    print("\nDone")