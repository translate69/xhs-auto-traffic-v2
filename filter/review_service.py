"""
review_service.py - 强制复查阶段

在 FilterService 之后、FeishuOutputService 之前执行，作为不可跳过的 gate。

复查规则（任意一条触发拒绝）：
  1. reasons 为空  → filter 未运行/失败，不写入
  2. 商家账号      → 作者含商家关键词，拒绝
  3. 纯分享帖      → 无求助信号 + 含分享关键词，拒绝

支持两种模式：
  - auto: 全自动，符合即通过
  - manual: 输出通过列表供人工确认后才写文件
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import config
from core.note_detail import NoteDetail


# ─── 复查常量 ────────────────────────────────────────────

MERCHANT_AUTHOR_KEYWORDS = [
    "民宿", "酒店", "餐厅", "大排档", "包车", "陪拍",
    "导游", "旅行社", "工作室", "客栈", "度假村",
    "别墅", "小院", "公寓", "海景房", "度假",
    "小姐姐", "小哥哥", "管家", "趣墅记",
    # 商家常用标识
    "bao", "bao🚗", "🚗", "约拍", "跟拍", "旅拍",
    "趣墅", "趣墅记", "趣墅海景",
]

SHARE_POST_KEYWORDS = [
    "攻略", "分享", "推荐", "打卡", "避雷", "合集",
    "探店", "测评", "我的", "我去", "我吃",
    "不踩坑", "不踩雷", "保姆级", "超全",
    "没有攻略", "无攻略", "没攻略",
]

ASK_SIGNALS_REVIEW = ["求", "想问", "请问", "求指教", "帮我", "帮帮我"]


# ─── 复查结果 ────────────────────────────────────────────

@dataclass
class ReviewResult:
    passed: bool
    reason: str = ""  # 拒绝原因


# ─── ReviewService ──────────────────────────────────────

class ReviewService:
    """
    强制复查 gate。

    用法：
        review = ReviewService()
        passed = review.review(filtered_notes)          # auto 模式
        passed = review.review(filtered_notes, mode="manual")  # manual 模式
    """

    def __init__(self):
        self._output_path = config.FEISHU_DIR / "reviewed_for_feishu.jsonl"

    def review(
        self,
        notes: list[NoteDetail],
        mode: str = "auto",
        keyword: str = "",
    ) -> list[NoteDetail]:
        """
        对 FilterService 通过的笔记执行复查，返回最终通过列表。

        Args:
            notes:    FilterService 返回的通过列表
            mode:     "auto" | "manual"
            keyword:  采集关键词（供记录）

        Returns:
            最终通过可写入飞书的 NoteDetail 列表
        """
        print(f"\n[review] === 复查阶段开始 ({len(notes)} 条待查) ===")

        passed = []
        rejected_count = 0

        for note in notes:
            result = self._review_one(note)
            if result.passed:
                passed.append(note)
            else:
                rejected_count += 1
                print(
                    f"[review] ❌ 拒绝 {note.note_id[:12]} | "
                    f"{note.title[:30] if note.title else note.content[:30]} | "
                    f"原因: {result.reason}"
                )

        print(f"[review] === 复查完成: {len(notes)} 条初审通过 → {len(passed)} 条终审通过 (拒绝 {rejected_count} 条) ===")

        if not passed:
            print("[review] ⚠️ 复查后无通过记录，不写入飞书")
            return []

        # 写入供 FeishuOutputService 读取的 JSONL
        self._write_output(passed, keyword=keyword)

        return passed

    def _review_one(self, note: NoteDetail) -> ReviewResult:
        """对单条笔记执行复查规则"""
        # ── 规则 1：reasons 为空 → 跳过 ─────────────────
        fr = note.filter_result
        if not fr or not fr.reasons or fr.reasons.strip() == "":
            return ReviewResult(passed=False, reason="reasons为空(filter未运行)")

        # ── 规则 2：商家账号 ──────────────────────────────
        if note.author and self._is_merchant_author(note.author):
            return ReviewResult(passed=False, reason=f"商家账号({note.author})")

        # ── 规则 3：纯分享帖 ─────────────────────────────
        title = note.title or ""
        content = note.content or ""
        content_no_tags = re.sub(r'#.+?(?=\s|#|$)', '', content)
        combined = f"{title} {content_no_tags}"

        title_has_explicit_ask = any(kw in title for kw in ASK_SIGNALS_REVIEW)
        content_has_ask = any(kw in content_no_tags for kw in ASK_SIGNALS_REVIEW)
        title_has_bang = "帮我" in title or "帮帮我" in title or "帮忙" in title
        has_any_ask = title_has_explicit_ask or content_has_ask or title_has_bang

        if not has_any_ask:
            # 纯分享关键词检查
            if any(kw in combined for kw in SHARE_POST_KEYWORDS):
                return ReviewResult(passed=False, reason="纯分享攻略贴")
            # 标题推荐格式检查（「xxx推荐xxx」）
            if self._is_recommendation_format(title):
                return ReviewResult(passed=False, reason="纯分享推荐格式")

        return ReviewResult(passed=True)

    def _is_merchant_author(self, author: str) -> bool:
        author_lower = author.lower()
        return any(kw in author_lower for kw in MERCHANT_AUTHOR_KEYWORDS)

    def _is_recommendation_format(self, title: str) -> bool:
        if not title:
            return False
        if title.startswith("求") or "求推荐" in title:
            return False
        if re.search(r"推荐[吗么呢？]", title):
            return False
        return bool(re.search(r".{0,10}推荐.{0,15}", title))

    def _write_output(self, passed: list[NoteDetail], keyword: str = ""):
        """写入 reviewed_for_feishu.jsonl（供 FeishuOutputService 读取）"""
        config.FEISHU_DIR.mkdir(parents=True, exist_ok=True)

        rows = []
        for detail in passed:
            fr = detail.filter_result

            # 构建 note_url
            note_url = detail.url or ""
            if note_url and "xsec_token=" not in note_url and "search_result/" in note_url:
                import re
                m = re.search(r"search_result/([a-fA-F0-9]+)", note_url)
                if m and detail.xsec_token:
                    note_url = (
                        f"https://www.xiaohongshu.com/explore/{m.group(1)}"
                        f"?xsec_token={detail.xsec_token}&xsec_source=pc_search"
                    )

            rows.append({
                "title": (detail.title or detail.content or "")[:50],
                "note_url": note_url,
                "note_id": detail.note_id,
                "type": fr.note_type if fr else "",
                "content": (detail.content or "")[:500],
                "author": detail.author or "",
                "likes": detail.likes or 0,
                "collects": detail.collects or 0,
                "comments": detail.comments or 0,
                "published_at": detail.published_at or "",
                "cover_image": detail.images[0] if detail.images else "",
                "tags": ",".join(detail.tags) if detail.tags else "",
                "keyword": keyword,
                "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "passed": True,
                "reasons": fr.reasons if fr else "",
            })

        with open(self._output_path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

        print(f"[review] 已写入 {self._output_path} ({len(rows)} 条)")

    @property
    def output_path(self) -> Path:
        return self._output_path
