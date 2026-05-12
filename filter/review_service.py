"""
review_service.py - 强制复查阶段（镜像执行模式）

在 FilterService 之后、FeishuOutputService 之前执行，作为不可跳过的 gate。


设计原则（镜像执行）：
  review 不是重新发明判断逻辑，而是用执行模式重新跑 filter 的核心检测函数。
  对于 filter 通过的笔记，用 filter 的关键方法重新做一遍判断——
  如果 filter 的核心检测方法自己给了 ask=passed=True（说明检测了但放行），
  review 仍然要重新执行一次，确保没有漏网之鱼。

由于所有核心判断逻辑都在 filter_service.py 里，review 通过 FilterService 实例
调用的方式嵌入执行模式——确保 review 的每一步判断都有真实的 Python 执行支撑。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import config
from core.note_detail import NoteDetail
from filter.filter_service import FilterService, has_signal, ASK_SIGNALS


# ─── 复查常量（仅用于快速兜底，不参与核心判断）───────────────

MERCHANT_AUTHOR_KEYWORDS = [
    "民宿", "酒店", "餐厅", "大排档", "包车", "陪拍",
    "导游", "旅行社", "工作室", "客栈", "度假村",
    "别墅", "小院", "公寓", "海景房", "度假",
    "小姐姐", "小哥哥", "管家", "趣墅记",
    # 商家常用标识
    "bao", "bao🚗", "🚗", "约拍", "跟拍", "旅拍",
    "趣墅", "趣墅记", "趣墅海景",
]

# 避雷类分享贴检测：标题含"避雷"时，即使有 ask 信号也视为分享贴
_BLEI_KEYWORDS = ["避雷", "吐槽", "踩坑", "被骗", "好无语", "太坑了"]


# ─── 复查结果 ────────────────────────────────────────────

@dataclass
class ReviewResult:
    passed: bool
    reason: str = ""  # 拒绝原因


# ─── ReviewService ──────────────────────────────────────

class ReviewService:
    """
    强制复查 gate（镜像执行模式）。

    用法：
        review = ReviewService()
        passed = review.review(filtered_notes)          # auto 模式
        passed = review.review(filtered_notes, mode="manual")  # manual 模式
    """

    def __init__(self):
        self._filter = FilterService()  # 镜像执行：复用 filter 的所有核心检测方法
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
        """
        复查逻辑（镜像执行模式）：
          重新用 filter 的核心检测函数跑一遍，不依赖 filter 的最终结果。
          任何一步检测返回拒绝，笔记就被拒绝。

        执行步骤：
          1. 商家账号（始终检查）
          2. 避雷类标题（始终检查）
          3. _is_recommendation_format  ← 镜像 filter 的"推荐格式"判断
          4. _is_share_post_only       ← 镜像 filter 的"纯分享贴"判断
          5. _is_self_talk             ← 镜像 filter 的"自语帖"判断（正文外向提问但内容是分享语气）
          6. _is_merchant_accommodation ← 镜像 filter 的"民宿商家"判断
        """
        fr = note.filter_result
        # ── 前置：reasons 为空 → filter 未运行，直接拒绝 ───────
        if not fr or not fr.reasons or fr.reasons.strip() == "":
            return ReviewResult(passed=False, reason="reasons为空(filter未运行)")

        title = note.title or ""
        content = note.content or ""
        content_no_tags = re.sub(r'#.+?(?=\s|#|$)', '', content)
        combined = f"{title} {content_no_tags}"

        # ── 步骤1：商家账号 ─────────────────────────────
        if note.author and self._is_merchant_author(note.author):
            return ReviewResult(passed=False, reason=f"商家账号({note.author})")

        # ── 步骤2：搭子标签（正文无真实同行意图则放行，hashtag平台标签不计入）──
        user_text_for_companion = f"{title} {content_no_tags}"
        REAL_COMPANION_INTENT_REVIEW = [
            "找搭子", "求搭子", "招募同行", "约伴", "求捡",
            "拼车", "捡人同游", "一起组队", "求组队同游",
        ]
        has_real_companion = any(kw in user_text_for_companion for kw in REAL_COMPANION_INTENT_REVIEW)
        if has_real_companion:
            return ReviewResult(passed=False, reason="找搭子/旅游同伴")

        # ── 步骤3：避雷类标题（始终检查）───
        if (not title.startswith("求")
                and not any(kw in title for kw in ["求推荐", "求住", "求带"])
                and any(kw in title for kw in _BLEI_KEYWORDS)):
            return ReviewResult(passed=False, reason="避雷类分享贴")

        # ── 步骤4：推荐格式标题（镜像执行 filter._is_recommendation_format）───
        # 修复"怎么选"误判后，这里能 catch 住"xxx怎么选xxx"格式的分享贴
        if self._filter._is_recommendation_format(title):
            return ReviewResult(passed=False, reason="纯分享推荐格式")

        # ── 步骤5：纯分享攻略贴（镜像执行 filter._is_share_post_only）─────────
        # _is_share_post_only 返回 "纯分享攻略贴" 字符串时表示拒绝
        share_reject = self._filter._is_share_post_only(title, content_no_tags)
        if share_reject:
            return ReviewResult(passed=False, reason=share_reject)

        # ── 步骤4b：（镜像执行 filter._get_pass_reasons 中的 share_hit 逻辑）───
        # _is_share_post_only 在 has_any_ask=True 时直接放行（不做分享关键词检查）。
        # 但 filter 的 _get_pass_reasons 会在「有 ask + 有 EXPERIENCE_SHARE_KEYWORDS」时
        # 进一步判断 strong_ask 是否足够强——不够强则剥掉 ask 并拒绝。
        # 这里补上这个逻辑，防止分享贴借「弱问句」逃逸。
        if has_signal(content_no_tags, ASK_SIGNALS):
            share_hit = [kw for kw in self._filter.EXPERIENCE_SHARE_KEYWORDS
                         if kw in content_no_tags or kw in title]
            if share_hit:
                # 强 ask：想问/求/求助/有什么/有没有（有具体需求意向）
                strong_ask = has_signal(content_no_tags, ["想问", "求", "求助", "有什么", "有没有"])
                has_recommend_ask = bool(__import__('re').search(r"有.{0,6}推荐", content_no_tags))
                # 反问语气：有 "有什么" 但上下文是满足/感叹语气，不算真求助
                is_rhetorical_what = bool(__import__('re').search(
                    r'还有什么[^一-龥]*?(烦恼|忧愁|不爽|难过)|有什么.?.?(不|没|么)\w',
                    content_no_tags
                ))
                if is_rhetorical_what:
                    strong_ask = False
                # 博主结尾邀请提问 ≠ 真实求助（"还有什么想问的/尽管问/评论区问"）
                blogger_ask_pattern = bool(__import__('re').search(
                    r'还有什么想问的|尽管问|评论区[问們]|有问题想问',
                    content_no_tags
                ))
                if blogger_ask_pattern:
                    strong_ask = False
                if not strong_ask and not has_recommend_ask:
                    return ReviewResult(passed=False, reason=f"分享贴借弱问句逃逸({share_hit[0]})")

        # ── 步骤6：自语帖（镜像执行 filter._is_self_talk）────────────────
        # 正文含"有什么/有啥"但前方有"想/我在"等自语标记 → 不是真求助
        if self._filter._is_self_talk(content_no_tags):
            return ReviewResult(passed=False, reason="自语帖")

        # ── 步骤7：软广问句开场（镜像执行 filter._is_soft_ad_question）───
        # 正文前几句以问句开场 + 含>=2个软广特征词 → 探店软广
        if self._filter._is_soft_ad_question(content_no_tags):
            return ReviewResult(passed=False, reason="软广问句开场")

        # ── 步骤8：民宿商家自推广（镜像执行 filter._is_merchant_accommodation）───
        if self._filter._is_merchant_accommodation(combined):
            return ReviewResult(passed=False, reason="民宿商家推广")

        return ReviewResult(passed=True)

    def _is_merchant_author(self, author: str) -> bool:
        """作者是否含商家关键词（始终独立检查，不用镜像）"""
        author_lower = author.lower()
        return any(kw in author_lower for kw in MERCHANT_AUTHOR_KEYWORDS)

    def _write_output(self, passed: list[NoteDetail], keyword: str = ""):
        """写入 reviewed_for_feishu.jsonl（供 FeishuOutputService 读取）"""
        config.FEISHU_DIR.mkdir(parents=True, exist_ok=True)

        rows = []
        for detail in passed:
            fr = detail.filter_result

            # 构建 note_url
            note_url = detail.url or ""
            if note_url and "xsec_token=" not in note_url and "search_result/" in note_url:
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
                f.write(__import__('json').dumps(row, ensure_ascii=False) + "\n")

        print(f"[review] 已写入 {self._output_path} ({len(rows)} 条)")

    @property
    def output_path(self) -> Path:
        return self._output_path
