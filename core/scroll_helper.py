"""
ScrollHelper - 滚动加载辅助

职责：
  · 滚动页面触发 XHS 懒加载
  · 智能判断是否已到底
  · 支持指定目标数量或最大滚动次数
"""
from __future__ import annotations

import time
import random

import config


class ScrollHelper:
    """
    滚动助手。

    使用：
        helper = ScrollHelper(page)
        helper.scroll_to_count(target_count=30, max_scrolls=8)
    """

    def __init__(self, page):
        self.page = page

    def scroll_to_count(self, target_count: int, max_scrolls: int = 8):
        """
        滚动直到拿到 target_count 条笔记，或达到 max_scrolls 次上限。

        策略：
          · 每次滚动 600px
          · 每次滚动后等 1 秒让内容加载
          · 每 2 次滚动检查一次笔记数量
        """
        for i in range(max_scrolls):
            # 执行滚动
            self.page.evaluate("window.scrollBy(0, 600)")
            time.sleep(1.0)

            # 每 2 次滚动检查一次数量
            if (i + 1) % 2 == 0:
                count = self._note_count()
                print(f"[ScrollHelper] 滚动 {i+1}/{max_scrolls}: 当前 {count} 条")
                if count >= target_count:
                    print(f"[ScrollHelper] 已达目标 {target_count} 条，提前结束")
                    break

    def scroll_until_stable(self, max_scrolls: int = 5, stable_threshold: int = 3):
        """
        滚动直到笔记数量连续 stable_threshold 次不增长（已到底）。
        用于不知道目标数量时的自然滚动。
        """
        last_counts = []
        for i in range(max_scrolls):
            self.page.evaluate("window.scrollBy(0, 600)")
            time.sleep(1.0)

            count = self._note_count()
            last_counts.append(count)

            # 保持窗口大小
            if len(last_counts) > stable_threshold:
                last_counts.pop(0)

            # 连续 N 次不增长
            if len(last_counts) == stable_threshold:
                if len(set(last_counts)) == 1:
                    print(f"[ScrollHelper] 已触底，连续 {stable_threshold} 次 {count} 条不变")
                    break

            print(f"[ScrollHelper] 滚动 {i+1}/{max_scrolls}: {count} 条")

    def _note_count(self) -> int:
        """返回当前页面 note-item 数量"""
        try:
            return self.page.evaluate("""
                document.querySelectorAll('section.note-item').length
            """)
        except Exception:
            return 0
