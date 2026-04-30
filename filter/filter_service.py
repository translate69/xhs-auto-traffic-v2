"""
filter_service.py - 两段式过滤服务

来自原 filter.py，逻辑 1:1 迁移。
enrichment 后执行，包含地域/商家/广告/分享贴/交通/搭子/弱意向/求助信号过滤 + 分类。
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import config
from core.note_detail import NoteDetail
from filter.classifier import classify_types, classify_type
from utils.parse import parse_published_at

# ─── 过滤常量 ────────────────────────────────────────────

REGION_KEYWORDS = ["汕尾", "红海湾", "金町湾", "海丰", "陆丰", "二马路", "三马路"]
REGION_KEYWORDS_SZ = ["深圳", "天文台", "南武当", "梧桐山", "大鹏", "较场尾", "东门", "世界之窗", "深圳湾", "东部华侨城", "中英街", "莲花山"]

ASK_SIGNALS = [
    "求", "求推荐", "求带", "求问", "求攻略", "求美食",
    "求助", "哪里好", "哪家好", "怎么玩", "住哪",
    "有没有推荐", "怎么选", "怎么安排", "求住", "想问", "问一下",
    "蹲蹲", "求指教",
    "帮我", "帮帮我",
    "有什么", "哪家好", "哪里好",
    "去哪吃", "去哪儿吃", "去哪玩", "去哪儿玩",
    "知道", "想问下", "请问",
]

STRONG_REJECT_KEYWORDS = [
    "旅游搭子", "找旅游搭子", "找搭子", "求搭子", "旅行搭子",
    "包车", "带车司机", "配司机", "驾驶员", "地陪",
]

QUESTION_SIGNALS = ["?", "？", "吗", "么", "呢"]
TRIP_QUESTION_SIGNALS = [
    "够吗", "合适吗", "可以吗", "方便吗", "行吗", "适合吗",
    "怎么安排", "来得及吗", "来得及么",
]
URGENT_SIGNALS = ["明天出发", "今天出发", "马上出发", "急", "在线等", "急急"]

REJECT_PATTERNS = [
    r"旗舰店", r"专卖店", r"限时", r"福利", r"广告", r"开业",
    r"秒杀", r"抢购", r"真的绝了", r"太宝藏了", r"封神",
    r"保姆级", r"附超全", r"不踩坑", r"不踩雷",
    r"车型[：:]", r"随停随走", r"人数1-7", r"全程[一三两五八]小时",
]

# 纯酒店/民宿夸赞广告淘汰关键词（无求助信号 → 淘汰）
HOTEL_PRAISE_KEYWORDS = [
    "有温度的酒店", "不舍得离开", "服务周到", "强烈推荐",
    "必住", "太好住了", "推荐这家民宿", "这家酒店超赞",
]

# 纯团建广告淘汰关键词（无求助信号 → 淘汰）
TEAM_BUILD_KEYWORDS = [
    "团建", "HR", "10人起接", "别墅", "篝火",
    "团建攻略", "公司团建", "团队游",
]

MERCHANT_AUTHOR_KEYWORDS = [
    "民宿", "酒店", "餐厅", "大排档", "包车", "陪拍",
    "导游", "旅行社", "工作室", "客栈", "度假村",
    "别墅", "小院", "公寓", "海景房", "度假",
    "小姐姐", "小哥哥", "管家", "趣墅记",
]

SHARE_POST_KEYWORDS = [
    "攻略", "分享", "推荐", "打卡", "避雷", "合集",
    "探店", "测评", "我的", "我去", "我吃",
    "不踩坑", "不踩雷", "保姆级", "超全",
    "没有攻略", "无攻略", "没攻略",  # 否定语气，非求助
]

TRANSPORT_KEYWORDS = [
    "打车", "公交", "地铁", "停车", "交通", "高铁",
    "大巴", "车站", "自驾", "路线",
]

NEGATIONS = ["不想", "不要", "不是", "不含", "没兴趣", "不考虑", "不去", "不知道", "不知", "没吃过", "没尝过"]


# ─── FilterResult ────────────────────────────────────────


@dataclass
class FilterResult:
    passed: bool
    reasons: str  # 逗号分隔，通过原因或淘汰原因
    note_type: str = ""  # 分类类型


# ─── FilterService ───────────────────────────────────────


class FilterService:
    """
    两段式过滤服务（enrichment 后执行）。

    流程：
      1. 基础过滤：时间二次校验、空内容过滤
      2. 业务强过滤：地域/商家/广告/分享贴/交通/搭子/弱意向/正向信号
      3. 分类：美食推荐/住宿推荐/行程规划/景点推荐
    """

    def filter_all(self, details: list[NoteDetail], keyword: str = "") -> list[NoteDetail]:
        """
        对所有笔记执行过滤，返回通过筛选的 NoteDetail 列表。
        同时写入 data/filtered_for_feishu.jsonl。
        同时更新每条 detail 的 filter_* 字段（供保存时写入中间文件）。
        """
        passed = []

        for detail in details:
            result = self.filter_one(detail, keyword=keyword)
            detail.filter_result = result
            detail.filter_passed = result.passed
            detail.filter_reasons = result.reasons
            detail.filter_type = result.note_type

            if result.passed:
                passed.append(detail)

        # 写文件
        self._write_output(passed, keyword=keyword)
        return passed

    def filter_one(self, detail: NoteDetail, keyword: str = "") -> FilterResult:
        """对单条笔记执行完整过滤逻辑"""
        title = detail.title or ""
        content = detail.content or ""
        combined = f"{title} {content}"

        # ── 1. 基础过滤 ────────────────────────────────

        # 时间二次校验
        if detail.published_at:
            try:
                pub_dt = datetime.strptime(detail.published_at[:10], "%Y-%m-%d")
                age = (datetime.now() - pub_dt).days
                if age > config.TIME_THRESHOLD_DAYS:
                    return FilterResult(passed=False, reasons=f"时间过久({age}天)")
            except ValueError:
                pass

        # ── 2. 地域检查 ────────────────────────────────
        # 根据关键词确定检查哪组地域词
        kw = keyword or getattr(detail, "keyword", "") or ""
        if "深圳" in kw:
            region_kws = REGION_KEYWORDS_SZ
        else:
            region_kws = REGION_KEYWORDS
        has_region = any(kw in combined for kw in region_kws)
        if not has_region:
            return FilterResult(passed=False, reasons=f"非目标地域")

        # ── 3. 强拒绝关键词 ────────────────────────────
        if any(kw in combined for kw in STRONG_REJECT_KEYWORDS):
            return FilterResult(passed=False, reasons="找搭子/旅游同伴")

        # ── 4. 商家账号 ────────────────────────────────
        if detail.author and self._is_merchant_author(detail.author):
            return FilterResult(passed=False, reasons="商家账号")

        # ── 5. 纯攻略/分享贴 ───────────────────────────
        # 去掉标签，避免标签里的关键词干扰信号判断和分类
        content_no_tags = re.sub(r'#.+?(?=\s|#|$)', '', content)

        # 先计算 ask 信号（供多个规则共用）
        title_has_explicit_ask = has_signal(title, ASK_SIGNALS)
        # 推荐格式标题（「xxx推荐xxx」）中的「推荐」不算 ASK 信号
        if self._is_recommendation_format(title):
            title_has_explicit_ask = False
        content_has_ask = has_signal(content_no_tags, ["求", "想问", "请问", "求指教", "帮我", "帮帮我", "推荐"])
        title_has_bang = "帮我" in title or "帮帮我" in title or "帮忙" in title
        has_any_ask = title_has_explicit_ask or content_has_ask or title_has_bang

        # 用去掉标签的内容做分享贴检查
        if self._is_share_post_only(title, content_no_tags):
            return FilterResult(passed=False, reasons="纯分享攻略贴")

        # ── 6. 纯交通类 ───────────────────────────────
        note_types = classify_types(title, content_no_tags)  # 分类时不依赖标签
        combined = f"{title} {content_no_tags}"
        if self._is_transport_only(combined, note_types):
            return FilterResult(passed=False, reasons="纯交通问题")

        # ── 7. 广告文案 ───────────────────────────────
        ad_reason = self._has_reject_pattern(combined)
        if ad_reason:
            return FilterResult(passed=False, reasons=f"广告:{ad_reason}")

        # ── 8. 正向信号通过 ────────────────────────────
        passed_reasons = self._get_pass_reasons(title, content, note_types)

        if not passed_reasons:
            return FilterResult(passed=False, reasons="无明确需求")

        # ── 9. 分类 ────────────────────────────────────
        # note_types 已在上层计算，直接复用
        return FilterResult(
            passed=True,
            reasons=",".join(passed_reasons),
            note_type=note_types[0] if note_types else "",
        )

    # ─── 辅助方法 ───────────────────────────────────────

    def _is_merchant_author(self, author: str) -> bool:
        author_lower = author.lower()
        return any(kw in author_lower for kw in MERCHANT_AUTHOR_KEYWORDS)

    def _is_recommendation_format(self, title: str) -> bool:
        """
        检查标题是否为「分享推荐」格式：xxx推荐xxx
        例如：「汕尾必玩景点推荐住宿」「美食推荐」
        这种格式中的「推荐」不应触发 ask 信号（是分享语气，不是求助）

        排除格式：
        - 「求推荐xxx」- 求助格式
        - 「有什么推荐吗」- 问句格式
        - 「推荐xxx吗」- 问句格式
        """
        if not title:
            return False
        # 排除以「求」开头的求助格式
        if title.startswith("求") or "求推荐" in title:
            return False
        # 排除问句格式（推荐后面有问号或「吗」「么」「呢」）
        if re.search(r"推荐[吗么呢？]", title):
            return False
        # 匹配 "xxx推荐xxx" 格式（推荐前后都有内容）
        return bool(re.search(r".{0,10}推荐.{0,15}", title))

    def _is_share_post_only(self, title: str, content: str) -> str | None:
        """检查是否为纯分享/攻略贴。返回淘汰原因或 None"""
        # 去掉标签，避免标签里的关键词干扰信号判断
        content_no_tags = re.sub(r'#.+?(?=\s|#|$)', '', content)
        combined = title + " " + content_no_tags

        # 标题否定语气：没有攻略/无攻略/没攻略 → 纯分享，非求助
        title_negation_patterns = ["没有攻略", "无攻略", "没攻略", "不用攻略", "不必攻略"]
        if any(title.startswith(p) for p in title_negation_patterns):
            return "纯分享攻略贴"

        title_has_explicit_ask = has_signal(title, ASK_SIGNALS)
        # 推荐格式（「xxx推荐xxx」）不算求助信号
        if self._is_recommendation_format(title):
            title_has_explicit_ask = False
        # 用去掉标签的内容检查，避免标签里的「推荐」等词误判
        content_has_ask = has_signal(content_no_tags, ["求", "想问", "请问", "求指教", "帮我", "帮帮我", "推荐"])
        title_has_bang = "帮我" in title or "帮帮我" in title or "帮忙" in title
        has_any_ask = title_has_explicit_ask or content_has_ask or title_has_bang

        if has_any_ask:
            return None  # 有求助信号，不淘汰

        if any(kw in combined for kw in HOTEL_PRAISE_KEYWORDS):
            return "纯酒店夸赞广告"
        if any(kw in combined for kw in TEAM_BUILD_KEYWORDS):
            return "纯团建广告"

        # 「xxx推荐xxx」格式标题 → 纯分享推荐，不算求助
        if self._is_recommendation_format(title):
            return "纯分享攻略贴"

        if any(kw in combined for kw in SHARE_POST_KEYWORDS):
            return "纯分享攻略贴"

        # 强化：纯分享风格（用去掉标签的内容）
        share_style = (
            content_no_tags.count("#") >= 2 or
            "打卡" in combined or
            "合集" in combined or
            (title.startswith(("我的", "我在", "我吃", "这次", "终于", "终于打卡"))) or
            (re.search(r"^[在我]\s*\S+", combined.lstrip()) and "推荐" in combined) or
            "没踩雷" in combined or "没踩坑" in combined
        )
        if share_style and not has_any_ask:
            return "纯分享攻略贴"

        return None

    def _has_unnegated_intent(self, text: str) -> bool:
        """检测是否有未是否定修饰的意图词（想/计划/打算/准备/行程）"""
        INTENT_WORDS = ["想", "计划", "打算", "准备", "行程"]
        # 否定前缀列表（按长度降序排列，避免短前缀干扰）
        NEG_PREFIXES_SORTED = sorted(
            ["不想", "不想去", "不打算", "不计划", "不要", "不用", "不会", "不能", "没想", "没打算", "没计划", "不", "没", "别"],
            key=len, reverse=True
        )
        text_lower = text.lower()

        for kw in INTENT_WORDS:
            idx = text_lower.find(kw)
            if idx == -1:
                continue
            # 检查「想」前1字、「计划」前2字等是否是否定
            # 从长到短检查：先检查2字否定，再检查单字否定
            max_prefix_len = max(len(p) for p in NEG_PREFIXES_SORTED)
            start = max(0, idx - max_prefix_len)
            pre_text = text_lower[start:idx]
            negated = False
            for prefix in NEG_PREFIXES_SORTED:
                if pre_text.endswith(prefix):
                    negated = True
                    break
            if not negated:
                return True
        return False

    def _is_transport_only(self, combined: str, note_types: list[str]) -> bool:
        if not any(kw in combined for kw in TRANSPORT_KEYWORDS):
            return False
        return not note_types

    def _has_reject_pattern(self, combined: str) -> str | None:
        for pattern in REJECT_PATTERNS:
            if re.search(pattern, combined, re.IGNORECASE):
                return pattern
        return None

    def _get_pass_reasons(self, title: str, content: str, note_types: list[str]) -> list[str]:
        """判断通过原因。宽松规则：有地域+有note_types+无强拒绝=通过"""
        reasons = []
        # 去掉标签，避免标签里的关键词干扰信号判断
        content_no_tags = re.sub(r'#.+?(?=\s|#|$)', '', content)
        combined_no_tags = f"{title} {content_no_tags}"

        # 求助信号（高优先级）
        if has_signal(content_no_tags, ASK_SIGNALS):
            reasons.append("ask")
        if has_signal(content_no_tags, TRIP_QUESTION_SIGNALS):
            reasons.append("trip_question")
        if has_signal(content_no_tags, URGENT_SIGNALS):
            reasons.append("urgent")

        if reasons:
            return reasons

        # 弱意向（次优先级）
        weak_desire = any(p in content_no_tags for p in ["想去", "好想去", "打算"])
        if weak_desire:
            content_has_consult = any(kw in content_no_tags for kw in ["求推荐", "求带", "有没有人", "求问"])
            if content_has_consult:
                reasons.append("weak_desire")

        if reasons:
            return reasons

        # 宽松规则：有 note_types + 有地域（已在上层验证）= 通过
        # 收紧：必须有内容质量信号，纯分享/广告语气不允许
        if note_types:
            # 纯分享/广告语气 → 淘汰（家宝藏/封神/种草语气）
            if re.search(r"宝藏|绝了|封神|太好吃|种草", content_no_tags):
                return reasons  # 不添加 type_match，走淘汰
            # 有问句/意图信号 → 通过（真实需求）
            # 避免「哪」单独匹配「去哪玩不重要」这类陈述句
            if any(kw in content_no_tags for kw in ["吗", "怎么", "哪里", "求", "想问", "请问"]) or "哪儿" in content_no_tags:
                reasons.append("type_match")
            # 内容较长 + 有意图词（排除被否定修饰的） → 通过
            elif len(content_no_tags) > 30 and self._has_unnegated_intent(content_no_tags):
                reasons.append("type_match")

        return reasons

    def _write_output(self, passed: list[NoteDetail], keyword: str = ""):
        """写入 filtered_for_feishu.jsonl"""
        config.FEISHU_DIR.mkdir(parents=True, exist_ok=True)
        output_path = config.FEISHU_DIR / "filtered_for_feishu.jsonl"

        rows = []
        for detail in passed:
            # 构建 note_url
            note_url = self._build_note_url(detail)
            fr = detail.filter_result

            rows.append({
                "title": detail.content[:50] if detail.title else detail.content[:50],
                "note_url": note_url,
                "note_id": detail.note_id,  # property，直接访问
                "type": fr.note_type if fr else "",
                "content": detail.content[:500],
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

        with open(output_path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _build_note_url(self, detail: NoteDetail) -> str:
        import re
        if not detail.url:
            return ""

        if "/explore/" in detail.url:
            if "xsec_token=" in detail.url:
                return detail.url
            if detail.xsec_token:
                sep = "&" if "?" in detail.url else "?"
                return f"{detail.url}{sep}xsec_token={detail.xsec_token}"
            return detail.url

        m = re.search(r"search_result/([a-f0-9]+)", detail.url)
        if m:
            note_id = m.group(1)
            base = f"https://www.xiaohongshu.com/explore/{note_id}"
            if detail.xsec_token:
                return f"{base}?xsec_token={detail.xsec_token}&xsec_source=pc_search"
            return base

        return detail.url


# ─── has_signal（内部用）────────────────────────────────


def has_signal(text: str, kw_list: list[str]) -> bool:
    """检查文本是否含信号词，且不在否定前缀后"""
    text_lower = text.lower()
    for kw in kw_list:
        idx = text_lower.find(kw.lower())
        if idx == -1:
            continue

        # ── 否定词检查（向前看2字，否定词最长2字）────────────────
        # 单字否定 + 完整否定短语
        NEGATIONS_SINGLE = ["不", "没", "别", "莫", "勿", "未", "否", "休", "甭"]
        NEGATIONS_PHRASE = ["不想", "不要", "不是", "不含", "没兴趣", "不考虑", "不去", "不知道", "不了解", "不清楚", "不确定", "没吃过", "没尝过"]
        # 关键词后紧跟的否定词（.signal不/没/无 + 后续字）
        POST_SIGNAL_NEG = ["不", "没", "无"]

        if idx >= 2:
            pre = text_lower[idx - 2:idx]
            last_char = pre[-1] if pre else ''
            if last_char in NEGATIONS_SINGLE:
                continue  # 有否定词前缀，跳过
            if any(n in pre for n in NEGATIONS_PHRASE):
                continue  # 有完整否定短语，跳过

        # ── 信号后否定检查（如「去哪玩不重要」）───────────────────
        after_pos = idx + len(kw)
        if after_pos < len(text_lower):
            after_char = text_lower[after_pos]
            if after_char in POST_SIGNAL_NEG:
                # 紧跟的否定字，跳过
                continue

        # 无否定词，命中
        return True
    return False
