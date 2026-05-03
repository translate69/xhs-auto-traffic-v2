"""在 collect() 流程里加诊断：在 _extract_feeds() 前检查状态"""
import sys, time, json, re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config
config.HEADLESS = False

from core.browser_manager import BrowserManager

with BrowserManager() as (browser, context):
    page = context.new_page()

    # 走 pipeline collect 的前几步
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    page.fill("#search-input", "汕尾美食")
    time.sleep(1)
    page.keyboard.press("Enter")
    time.sleep(5)

    print(f"搜索后URL: {page.url}")

    # hover + filter
    page.hover(".filter")
    time.sleep(0.5)

    latest = page.evaluate("""
(function() {
    var all = document.querySelectorAll('.filter *');
    for (var i = 0; i < all.length; i++) {
        var txt = (all[i].textContent || '').trim();
        var rect = all[i].getBoundingClientRect();
        if (txt === '最新' && rect.width > 5 && rect.height > 5 && rect.top >= 0)
            return {x: Math.round(rect.x+rect.width/2), y: Math.round(rect.top+rect.height/2)};
    }
    return null;
})()
    """)
    week = page.evaluate("""
(function() {
    var all = document.querySelectorAll('.filter *');
    for (var i = 0; i < all.length; i++) {
        var txt = (all[i].textContent || '').trim();
        var rect = all[i].getBoundingClientRect();
        if (txt === '一周内' && rect.width > 5 && rect.height > 5 && rect.top >= 0)
            return {x: Math.round(rect.x+rect.width/2), y: Math.round(rect.top+rect.height/2)};
    }
    return null;
})()
    """)
    if latest:
        page.mouse.click(latest['x'], latest['y'])
        time.sleep(2)
    if week:
        page.mouse.click(week['x'], week['y'])
        time.sleep(3)

    print(f"筛选后URL: {page.url}")

    # 模拟滚动
    for _ in range(3):
        page.mouse.wheel(0, 300)
        time.sleep(0.5)

    # 提取前的诊断
    print(f"\n=== 提取前诊断 ===")
    print(f"当前URL: {page.url}")

    # 关键：检查当前 page 的 main frame 是否还在
    frame_info = page.evaluate("""
(function() {
    return {
        url: document.URL,
        readyState: document.readyState,
        bodyLen: document.body.innerHTML.length,
        sections: document.querySelectorAll('section.note-item').length
    };
})()
    """)
    print(f"document.URL: {frame_info['url']}")
    print(f"document.readyState: {frame_info['readyState']}")
    print(f"section.note-item: {frame_info['sections']}")

    # 提取 a.cover.mask 的 href
    link_sample = page.evaluate("""
(function() {
    var links = document.querySelectorAll('a.cover.mask');
    var result = [];
    for (var i = 0; i < Math.min(links.length, 3); i++) {
        result.push(links[i].getAttribute('href') || '');
    }
    return result;
})()
    """)
    print(f"a.cover.mask href 前3条: {link_sample}")

    # 完整模拟 _extract_feeds 的逻辑
    raw_data = page.evaluate("""
(function() {
    var notes = document.querySelectorAll('section.note-item');
    var result = [];
    for (var i = 0; i < notes.length; i++) {
        var note = notes[i];
        var link = note.querySelector('a.cover.mask');
        result.push({
            url: link ? (link.getAttribute('href') || '') : '',
            author: (note.querySelector('.name-time-wrapper .name') || {textContent: ''}).textContent.trim(),
            time_text: (note.querySelector('.name-time-wrapper .time') || {textContent: ''}).textContent.trim()
        });
    }
    return result;
})()
    """)
    print(f"JS 提取的 raw data 条数: {len(raw_data)}")
    if raw_data:
        print(f"第1条 url: '{raw_data[0]['url']}'")

    # 用 pipeline 的过滤条件验证
    feeds = []
    for item in raw_data:
        raw_url = item["url"]
        if not raw_url or ("/note/" not in raw_url and "/explore/" not in raw_url):
            print(f"  跳过: {raw_url[:60]}")
            continue
        m = re.search(r"/(note|explore)/([a-f0-9]+)", raw_url)
        if m:
            feeds.append({"note_id": m.group(2), "url": raw_url[:80]})

    print(f"过滤后 feeds: {len(feeds)}")
    for f in feeds[:3]:
        print(f"  {f}")

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/test_page.png", full_page=True)
    print("截图已保存")

print("完成")