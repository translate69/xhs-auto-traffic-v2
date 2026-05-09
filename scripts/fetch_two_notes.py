# -*- coding: utf-8 -*-
"""直接抓取两篇笔记详情页，分析内容"""
import sys, time, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')

from core.browser_manager import BrowserManager

def fetch_detail(note_id: str, xsec_token: str = ""):
    url = f"https://www.xiaohongshu.com/search_result/{note_id}?xsec_token={xsec_token}&xsec_source=pc_search"
    print(f"Fetching: {note_id}")
    print(f"  URL: {url}")

    with BrowserManager(headless=False) as (browser, context):
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(3)

        title = page.title()
        content = page.evaluate(
            "document.querySelector('#detail-desc')?.textContent?.slice(0, 500) || ''"
        )
        author = page.evaluate(
            "document.querySelector('.author .name, .author-wrapper .name, [class*=\"author\"] [class*=\"name\"]')?.textContent || ''"
        )

        print(f"  title: {title}")
        print(f"  author: {author}")
        print(f"  content:\n{content[:500]}")
        page.close()

print("=" * 60)
print("笔记1: 69f76a0d000000002202b546")
print("=" * 60)
fetch_detail("69f76a0d000000002202b546")

print()
print("=" * 60)
print("笔记2: 69fe050a000000002003b0c8")
print("=" * 60)
fetch_detail("69fe050a000000002003b0c8")