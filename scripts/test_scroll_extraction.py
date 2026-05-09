"""
测试脚本：验证滚动增量提取是否能获取更多笔记

目标：对比两种提取策略
  A. 滚动全部完成后一次性提取（当前逻辑）
  B. 每滚动一次就提取一次，累加 note_id 去重

用法：python scripts/test_scroll_extraction.py --keyword 汕尾美食 --scrolls 8
"""
import argparse
import re
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(PROJECT_ROOT))

import config
from core.browser_manager import BrowserManager


def extract_note_ids(page) -> set[str]:
    """从当前 DOM 提取所有 note_id（去重）"""
    data = page.evaluate("""
        (function() {
            var notes = document.querySelectorAll('section.note-item');
            var ids = [];
            for (var i = 0; i < notes.length; i++) {
                var link = notes[i].querySelector('a.cover.mask');
                if (!link) continue;
                var href = link.getAttribute('href') || '';
                var m = href.match(/search_result\\/([a-f0-9]+)|explore\\/([a-f0-9]+)/i);
                if (m) ids.push((m[1] || m[2]).toLowerCase());
            }
            return ids;
        })()
    """)
    return set(data)


def get_note_count(page) -> int:
    """当前页面 note-item 总数"""
    try:
        return page.evaluate("document.querySelectorAll('section.note-item').length")
    except Exception:
        return 0


def test_incremental_extraction(keyword: str, max_scrolls: int = 8):
    """增量提取测试"""

    results = {
        "strategy_a": {"total_collected": 0, "unique_ids": set()},
        "strategy_b": {"by_scroll": [], "cumulative_unique": set()},
    }

    with BrowserManager(headless=False) as (browser, context):
        page = context.new_page()

        # ── 访问搜索页 ──────────────────────────────
        print(f"\n{'='*60}")
        print(f"测试关键词: {keyword}")
        print(f"最大滚动次数: {max_scrolls}")
        print(f"{'='*60}\n")

        page.goto(
            "https://www.xiaohongshu.com/search_result?keyword="
            + keyword + "&type=51",
            wait_until="domcontentloaded"
        )
        time.sleep(5)

        # 等待笔记列表出现
        try:
            page.wait_for_selector("section.note-item", timeout=30000)
        except Exception as e:
            print(f"等待笔记列表超时: {e}")
            page.screenshot(path=str(PROJECT_ROOT / "debug_test_timeout.png"))
            return results

        print(f"[初始] DOM 中 note-item: {get_note_count(page)}")

        # ── 策略 A：滚动全部完成后一次性提取 ─────────
        print(f"\n{'─'*40}")
        print("策略 A：滚动全部完成后一次性提取（当前逻辑）")
        print(f"{'─'*40}")

        # 重新加载页面（干净状态）
        page.goto(
            "https://www.xiaohongshu.com/search_result?keyword="
            + keyword + "&type=51",
            wait_until="domcontentloaded"
        )
        time.sleep(5)
        page.wait_for_selector("section.note-item", timeout=30000)

        for i in range(max_scrolls):
            page.evaluate("window.scrollBy(0, 600)")
            time.sleep(1.0)
            count = get_note_count(page)
            print(f"  滚动 {i+1}/{max_scrolls}: DOM note-item = {count}")

        # 全部滚动完后提取
        ids_a = extract_note_ids(page)
        results["strategy_a"]["unique_ids"] = ids_a
        results["strategy_a"]["total_collected"] = len(ids_a)
        print(f"  → 策略 A 最终提取: {len(ids_a)} 条唯一笔记")

        # ── 策略 B：每滚动一次提取一次，累加去重 ───
        print(f"\n{'─'*40}")
        print("策略 B：每滚动一次提取一次，累加去重（增量提取）")
        print(f"{'─'*40}")

        # 重新加载页面（干净状态）
        page.goto(
            "https://www.xiaohongshu.com/search_result?keyword="
            + keyword + "&type=51",
            wait_until="domcontentloaded"
        )
        time.sleep(5)
        page.wait_for_selector("section.note-item", timeout=30000)

        cumulative_ids: set[str] = set()

        for i in range(max_scrolls):
            before = len(cumulative_ids)
            page.evaluate("window.scrollBy(0, 600)")
            time.sleep(1.0)
            count = get_note_count(page)
            new_ids = extract_note_ids(page)
            cumulative_ids.update(new_ids)
            delta = len(cumulative_ids) - before
            results["strategy_b"]["by_scroll"].append({
                "scroll": i + 1,
                "dom_count": count,
                "cumulative_unique": len(cumulative_ids),
                "delta_this_scroll": delta,
            })
            print(f"  滚动 {i+1}/{max_scrolls}: DOM={count}, 累计唯一={len(cumulative_ids)}, 本次新增={delta}")

        results["strategy_b"]["cumulative_unique"] = cumulative_ids

        # ── 对比结果 ─────────────────────────────
        print(f"\n{'='*60}")
        print("对比结果")
        print(f"{'='*60}")
        a_count = results["strategy_a"]["total_collected"]
        b_count = len(results["strategy_b"]["cumulative_unique"])
        diff = b_count - a_count
        print(f"  策略 A（一次性提取）: {a_count} 条")
        print(f"  策略 B（增量累加）:  {b_count} 条")
        print(f"  差异: {'+' if diff > 0 else ''}{diff} 条 ({diff/a_count*100:+.1f}%)")

        if diff > 0:
            print(f"\n  ✅ 增量提取更优！策略 B 多获取了 {diff} 条笔记")
            print(f"  建议：改用策略 B，每滚动 N 次提取一次（减少 DOM 回收损失）")
        elif diff < 0:
            print(f"\n  ⚠️ 策略 A 更优，DOM 有回收机制，增量提取反而重复多")
        else:
            print(f"\n  ≈ 两种策略效果相同，XHS 没有回收机制")

        # 找出策略 B 中增量最大的滚动次数
        if results["strategy_b"]["by_scroll"]:
            best = max(results["strategy_b"]["by_scroll"], key=lambda x: x["delta_this_scroll"])
            print(f"\n  最大增量出现在滚动 {best['scroll']}: +{best['delta_this_scroll']} 条")

    return results


def main():
    parser = argparse.ArgumentParser(description="滚动增量提取测试")
    parser.add_argument("--keyword", "-k", type=str, default="汕尾美食")
    parser.add_argument("--scrolls", "-s", type=int, default=8)
    args = parser.parse_args()

    results = test_incremental_extraction(args.keyword, args.scrolls)


if __name__ == "__main__":
    main()
