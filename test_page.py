import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import config
from core.browser_manager import BrowserManager

with BrowserManager() as (browser, context):
    page = context.new_page()
    page.goto("https://www.xiaohongshu.com/", wait_until="domcontentloaded")
    time.sleep(3)
    print(f"首页URL: {page.url}")

    # 找搜索框
    inp = page.wait_for_selector("#search-input", timeout=10000)
    inp.fill("汕尾美食")
    time.sleep(0.5)

    # 方法1: 点击搜索按钮
    try:
        btn = page.wait_for_selector(".search-btn", timeout=3000)
        btn.click()
        print("方法1: 点击 .search-btn")
    except Exception:
        print("方法1: .search-btn 未找到")

    time.sleep(5)
    print(f"方法1后URL: {page.url}")

    # 如果没变，改用方法2：直接访问 search_result
    if "search_result" not in page.url:
        page.goto("https://www.xiaohongshu.com/search_result?keyword=%E6%B1%95%E5%B0%BE%E7%BE%8E%E9%A3%9F", wait_until="domcontentloaded")
        time.sleep(5)
        print(f"方法2直接访问后URL: {page.url}")

    # 检查是否有 filter
    filter_el = page.query_selector(".filter")
    print(f"filter存在: {'YES' if filter_el else 'NO'}")

    # 检查笔记
    notes = page.query_selector_all("section.note-item")
    print(f"section.note-item: {len(notes)}")

    # 用 JS 点击筛选
    page.evaluate("""
(function() {
    var all = document.querySelectorAll('.filter *');
    for (var i = 0; i < all.length; i++) {
        var el = all[i];
        var txt = (el.textContent||'').trim();
        var rect = el.getBoundingClientRect();
        if (txt === '最新' && rect.width > 0 && rect.height > 0) {
            el.click();
        }
    }
})()
    """)
    time.sleep(1)
    page.evaluate("""
(function() {
    var all = document.querySelectorAll('.filter *');
    for (var i = 0; i < all.length; i++) {
        var el = all[i];
        var txt = (el.textContent||'').trim();
        var rect = el.getBoundingClientRect();
        if (txt === '一周内' && rect.width > 0 && rect.height > 0) {
            el.click();
        }
    }
})()
    """)
    time.sleep(3)

    notes_after = page.query_selector_all("section.note-item")
    print(f"筛选后 section.note-item: {len(notes_after)}")

    # 提取数据
    data = page.evaluate("""
(function() {
    var notes = document.querySelectorAll('section.note-item');
    var result = [];
    for (var i = 0; i < Math.min(notes.length, 5); i++) {
        var note = notes[i];
        var link = note.querySelector('a.cover.mask');
        var nameEl = note.querySelector('.name-time-wrapper .name');
        var timeEl = note.querySelector('.name-time-wrapper .time');
        result.push({
            url: link ? link.getAttribute('href') : '',
            author: nameEl ? nameEl.textContent.trim() : '',
            time: timeEl ? timeEl.textContent.trim() : ''
        });
    }
    return result;
})()
    """)
    print(f"提取到数据: {len(data)} 条")
    for d in data:
        print(f"  {d}")

    page.screenshot(path="E:/translate/claw/xhs-auto-traffic-v2/test_page.png", full_page=True)
    print("截图已保存")