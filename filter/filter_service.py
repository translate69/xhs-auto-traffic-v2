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

# 跨城市蹭流量关键词：内容中出现这些词说明不是目标城市（汕尾）
# 只加城市名/行政区划名，不加景点/街道名（避免误杀）
OTHER_CITY_KEYWORDS = [
    # 广东热门旅游城市
    "阳朔", "桂林", "湛江", "汕头", "潮州", "揭阳",
    "珠海", "中山", "佛山", "东莞", "惠州", "江门", "肇庆", "清远", "韶关",
    # 福建
    "厦门", "福州", "泉州", "武夷山", "漳州", "龙岩", "莆田", "三明", "南平",
    # 浙江
    "杭州", "乌镇", "苏州", "南京", "宁波", "温州", "绍兴", "嘉兴", "湖州", "金华", "台州", "丽水", "衢州",
    # 四川/重庆
    "成都", "九寨沟", "稻城", "色达", "重庆", "洪崖洞", "解放碑",
    # 陕西
    "西安", "兵马俑", "华山", "延安", "咸阳",
    # 北京
    "北京", "故宫", "长城", "天安门", "颐和园", "圆明园",
    # 上海
    "上海", "外滩", "浦东", "豫园",
    # 云南
    "丽江", "大理", "香格里拉", "泸沽湖", "昆明", "石林", "西双版纳", "腾冲",
    # 山东
    "青岛", "威海", "烟台", "济南", "泰安", "曲阜", "蓬莱",
    # 湖南
    "长沙", "张家界", "衡山", "岳阳", "凤凰",
    # 江西
    "南昌", "滕王阁", "庐山", "婺源", "景德镇", "三清山",
    # 湖北
    "武汉", "黄鹤楼", "三峡", "宜昌", "恩施",
    # 贵州
    "贵阳", "黄果树", "西江千户", "镇远", "遵义",
    # 广西（不含桂林/阳朔已列）
    "南宁", "北海", "涠洲岛", "德天瀑布",
    # 海南
    "海口", "三亚", "博鳌", "万宁",
    # 天津/河北
    "天津", "古文化街", "石家庄", "承德", "秦皇岛",
    # 东北
    "哈尔滨", "冰雪大世界", "雪乡", "长春", "长白山", "沈阳", "大连", "鞍山",
    # 西北
    "兰州", "敦煌", "张掖", "青海湖", "茶卡盐湖", "西宁", "塔尔寺",
    "乌鲁木齐", "天山", "喀纳斯", "伊犁", "吐鲁番",
    "拉萨", "布达拉宫", "纳木错", "林芝", "羊卓雍错",
    "西安", "华山", "延安",
    # 港澳台
    "香港", "澳门", "台北", "高雄", "垦丁", "花莲", "台中",
    # 河南/山西
    "郑州", "开封", "洛阳", "少林寺", "云台山",
    "太原", "平遥古城", "大同", "五台山",
    # 安徽
    "黄山", "宏村", "西递", "合肥", "徽州",
    # 内蒙古/宁夏/甘肃
    "呼和浩特", "呼伦贝尔", "阿尔山", "满洲里",
    "银川", "中卫", "沙湖",
    "兰州", "敦煌", "张掖", "嘉峪关", "酒泉",
]

ASK_SIGNALS = [
    "求", "求推荐", "求带", "求问", "求攻略", "求美食",
    "求助", "哪里好", "哪家好", "怎么玩", "住哪",
    "有没有推荐", "有推荐", "有推荐的吗", "有本地人推荐", "怎么选", "怎么安排", "求住", "想问", "问一下",
    "蹲蹲", "求指教",
    "帮帮我",
    "有什么", "哪家好", "哪里好",
    "去哪吃", "去哪儿吃", "想问下", "请问",
]

STRONG_REJECT_KEYWORDS = [
    "旅游搭子", "找旅游搭子", "找搭子", "求搭子", "旅行搭子",
    "包车", "bao", "带车司机", "配司机", "驾驶员", "地陪", "约拍",
    "河图",
]

QUESTION_SIGNALS = ["?", "？", "吗", "么", "呢"]
TRIP_QUESTION_SIGNALS = [
    "够吗", "合适吗", "可以吗", "方便吗", "行吗", "适合吗",
    "怎么安排", "来得及吗", "来得及么",
]
URGENT_SIGNALS = ["明天出发", "今天出发", "马上出发", "急什么", "在线等", "急急"]

REJECT_PATTERNS = [
    r"旗舰店", r"专卖店", r"限时", r"福利", r"广告", r"开业",
    r"秒杀", r"抢购", r"真的绝了", r"太宝藏了", r"封神",
    r"保姆级", r"附超全", r"不踩坑", r"不踩雷",
    r"车型[：:]", r"随停随走", r"随叫随到", r"人数1-7", r"全程[一三两五八]小时",
    # 房地产/商业广告特有
    r"业主急售", r"业主急卖", r"急售捡漏", r"急卖捡漏",
    r"降价急售", r"降价急卖", r"血亏急售", r"亏本急售",
    r"套内[0-9]+㎡", r"套内约[0-9]+㎡", r"建面[0-9]+㎡", r"建面约[0-9]+㎡",
    r"满五", r"红本在手", r"税费低", r"交易快",
    r"顶豪", r"豪宅", r"抄底价", r"底价可谈", r"手慢无",
    # 食品/产品广告特有（产品功效/成分/选购指南类内容，非真实用户求助）
    r"配料表", r"添加剂", r"增味剂", r"防腐剂", r"科技与狠活",
    r"荣获", r"力荐", r"推荐产品", r"厂家", r"专业只生产", r"正规厂家",
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
        return self.filter_one_impl(detail, skip_time_check=False)


    def filter_one_for_feishu(self, detail: NoteDetail) -> FilterResult:
        """
        飞书表格专用过滤：核心逻辑与 filter_one 完全一致，
        仅跳过时间检查（飞书表格是永久存储，不以采集时间为过滤条件）。
        """
        return self.filter_one_impl(detail, skip_time_check=True)


    def filter_one_impl(self, detail: NoteDetail, skip_time_check: bool = False) -> FilterResult:
        """filter_one 通用实现，skip_time_check=True 时跳过时间校验"""
        title = detail.title or ""
        content = detail.content or ""
        combined = f"{title} {content}"

        # ── 1. 基础过滤 ────────────────────────────────
        if not skip_time_check and detail.published_at:
            try:
                pub_dt = datetime.strptime(detail.published_at[:10], "%Y-%m-%d")
                age = (datetime.now() - pub_dt).days
                if age > config.TIME_THRESHOLD_DAYS:
                    return FilterResult(passed=False, reasons=f"时间过久({age}天)")
            except ValueError:
                pass

        # ── 2. 地域检查 ────────────────────────────────
        region_kws = REGION_KEYWORDS
        has_region = any(kw in combined for kw in region_kws)
        if not has_region:
            return FilterResult(passed=False, reasons=f"非目标地域")

        # ── 2.5 跨城市蹭流量检测 ───────────────────────
        # 用去掉标签的内容检测其他城市词（正文里的外地地名更可靠）
        content_no_tags = re.sub(r'#.+?(?=\s|#|$)', '', content)
        # 同时传入原始内容（含标签），标签里的外地城市名也要统计
        other_city = self._detect_other_city(content_no_tags, content, region_kws)
        if other_city:
            return FilterResult(passed=False, reasons=f"跨城市蹭流量({other_city})")

        # ── 3. 强拒绝关键词 ────────────────────────────
        if any(kw in combined for kw in STRONG_REJECT_KEYWORDS):
            return FilterResult(passed=False, reasons="找搭子/旅游同伴")

        # ── 4. 商家账号 ────────────────────────────────
        if detail.author and self._is_merchant_author(detail.author):
            return FilterResult(passed=False, reasons="商家账号")

        # ── 5. 纯攻略/分享贴 ───────────────────────────

        # 先计算 ask 信号（供多个规则共用）
        title_has_explicit_ask = has_signal(title, ASK_SIGNALS)
        # 推荐格式标题（「xxx推荐xxx」）中的「推荐」不算 ASK 信号
        if self._is_recommendation_format(title):
            title_has_explicit_ask = False
        # 「推荐」已移出 content_has_ask：正文里的「好吃推荐/炒鸡推荐」是分享语气，不是求助信号
        # 求助信号中「推荐」的角色由 EXPERIENCE_SHARE_KEYWORDS 中的结构化推荐词覆盖
        content_has_ask = has_signal(content_no_tags, ASK_SIGNALS)
        title_has_bang = "帮帮我" in title or "帮忙" in title
        has_any_ask = title_has_explicit_ask or content_has_ask or title_has_bang

        # （无标题拦截已移除：无标题+有 ask 可能是正常求助（如 69ef89c2），
        #   爬虫生成帖会被自语检测、跨城市检测、民宿检测等覆盖，这里不需要额外拦截）

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

        # ── 7.5 民宿商家自推广 ───────────────────────
        # 有 ask 信号但内容含民宿自推广特征 → 商家广告，不是求助
        if self._is_merchant_accommodation(combined):
            return FilterResult(passed=False, reasons="民宿商家推广")

        # ── 8. 正向信号通过 ────────────────────────────
        passed_reasons = self._get_pass_reasons(title, content, note_types)

        # ── 8. 正文极短时放宽 ─────────────────────────
        # 正文<30字时，若标题有求助信号，说明内容可能在图片里，放行
        # 注意：不要覆盖 passed_reasons 中的 "ask" 信号 —— review 要靠 "ask" 判断是否信任 filter
        if len(content_no_tags.strip()) < 30 and title_has_explicit_ask:
            if "ask" not in passed_reasons:
                passed_reasons.append("正文内容可能在图片中")

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

    def _detect_other_city(
        self, content: str, full_content: str, target_region_kws: list[str] | None = None
    ) -> str | None:
        """
        检测内容是否蹭其他热门旅游城市（非目标城市）。

        判断逻辑：OTHER_CITY 出现次数（正文+标签合计）>= 目标城市出现次数*2 且 >=3次
        → 说明大量篇幅在说其他城市，不是目标城市。
        正文+标签里都有外地城市名 → 蹭流量。

        返回检测到的城市名，无则返回 None。
        """
        if target_region_kws is None:
            target_region_kws = REGION_KEYWORDS

        # 统计目标城市词出现次数（正文，去掉标签）
        target_count = sum(content.count(kw) for kw in target_region_kws)

        # 统计 OTHER_CITY 词出现次数（正文 + 标签合计）
        city_scores: dict[str, int] = {}
        for city in OTHER_CITY_KEYWORDS:
            cnt = full_content.count(city)  # 含标签
            if cnt > 0:
                city_scores[city] = cnt

        if not city_scores:
            return None

        # 找出现最多的那个城市
        top_city, top_count = max(city_scores.items(), key=lambda x: x[1])

        # 阈值：other_city 出现 >= 目标城市出现*2 且 >= 3次
        if top_count >= 3 and top_count >= target_count * 2:
            return top_city
        return None

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
        # 排除以「求」开头的求助格式（最优先，避免漏掉「救命，求...」这类紧急求助）
        if title.startswith("求") or "求推荐" in title:
            return False
        # 排除问句格式（推荐后面有问号或「吗」「么」「呢」）
        if re.search(r"推荐[吗么呢？]", title):
            return False
        # 排除包含「求/求问/请问」的求助标题（「汕尾美食求推荐」类）
        # 优先级高于「推荐」检测，避免「美食推荐」被误判为推荐格式
        if re.search(r"求|求问|请问", title):
            return False
        # 排除「有没有/有无/在线蹲/求推荐」等求助前缀 + 「推荐」的结构（真实求助，不是分享）
        # 例如：「有没有本地人推荐一下」「在线蹲汕尾本地人推荐点私藏美食」
        if re.search(r"有没有|有无|在线蹲", title):
            return False
        # 匹配 "xxx推荐xxx" 格式（推荐前后都有内容）
        # 但「不推荐」「被推荐」「说推荐」等是否定上下文，不是分享推荐
        neg_before = re.search(r"[不没被都说也还就才]\s*推荐", title)
        if neg_before:
            return False
        return bool(re.search(r".{0,10}推荐.{0,15}", title))

    def _is_topic_description_format(self, title: str) -> bool:
        """
        检查标题是否为话题描述格式（topic-description）。
        这种格式的特征是：以「xxx怎么选xxx」结构呈现一个话题，不是真求助。
        例如：「广东沙滩怎么选」「汕尾民宿怎么选」

        排除：后面有问号/吗/么（真问句），或以「求/请问」开头（求助格式）。
        """
        if not title:
            return False
        if title.startswith("求") or title.startswith("请问"):
            return False
        if re.search(r".{2,10}怎么选", title) and not re.search(r"怎么选[么吗?？]", title):
            return True
        return False

    def _is_share_post_only(self, title: str, content: str) -> str | None:
        """检查是否为纯分享/攻略贴。返回淘汰原因或 None"""
        content_no_tags = re.sub(r'#.+?(?=\s|#|$)', '', content)
        combined = title + " " + content_no_tags

        # 标题否定语气
        title_negation_patterns = ["没有攻略", "无攻略", "没攻略", "不用攻略", "不必攻略"]
        if any(title.startswith(p) for p in title_negation_patterns):
            return "纯分享攻略贴"

        # ── 格式拦截（在 has_any_ask 之前，防止 topic-description 逃逸）───
        # _is_recommendation_format 处理「xxx推荐xxx」
        if self._is_recommendation_format(title):
            return "纯分享攻略贴"
        # _is_topic_description_format 处理「xxx怎么选xxx」
        if self._is_topic_description_format(title):
            return "纯分享攻略贴"

        title_has_explicit_ask = has_signal(title, ASK_SIGNALS)
        content_has_ask = has_signal(content_no_tags, ASK_SIGNALS)
        title_has_bang = "帮帮我" in title or "帮忙" in title
        has_any_ask = title_has_explicit_ask or content_has_ask or title_has_bang

        if has_any_ask:
            return None

        if any(kw in combined for kw in HOTEL_PRAISE_KEYWORDS):
            return "纯酒店夸赞广告"
        if any(kw in combined for kw in TEAM_BUILD_KEYWORDS):
            return "纯团建广告"
        if any(kw in combined for kw in SHARE_POST_KEYWORDS):
            return "纯分享攻略贴"

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
        """检测是否有未是否定修饰的意图词（想/计划/打算/准备/行程）
        注意：「想」后接 CJK 字符（想想/想要/想去）复合词不算独立意图"""
        CJK_RANGE = frozenset(range(0x4E00, 0x9FFF + 1)) | frozenset(range(0x3400, 0x4DBF + 1))
        INTENT_WORDS = ["想", "计划", "打算", "准备", "行程"]
        NEG_PREFIXES_SORTED = sorted(
            ["不想", "不想去", "不打算", "不计划", "不要", "不用", "不会", "不能", "没想", "没打算", "没计划", "不", "没", "别"],
            key=len, reverse=True
        )
        text_lower = text.lower()
        for kw in INTENT_WORDS:
            idx = text_lower.find(kw)
            if idx == -1:
                continue
            max_prefix_len = max(len(p) for p in NEG_PREFIXES_SORTED)
            start = max(0, idx - max_prefix_len)
            pre_text = text_lower[start:idx]
            negated = any(pre_text.endswith(prefix) for prefix in NEG_PREFIXES_SORTED)
            if negated:
                continue
            # 「想」后接 CJK → 复合词（想想/想要/想去），跳过
            if kw == "想" and idx + 1 < len(text_lower):
                after_char = text_lower[idx + 1]
                if ord(after_char) in CJK_RANGE:
                    continue
            return True
        return False

    def _is_self_talk(self, content: str) -> bool:
        """
        检测自语帖（内心独白，而非向他人求助）。

        典型自语：「我要想一下有什么可以打包的」
        典型求助：「有什么汕尾住宿推荐吗」「请问有什么好吃的」「有朋友能说说吗」

        逻辑：含「有什么/有啥」+ 前方有「想/我在/我在想/我想/自己」+ 不含外向求助信号
        """
        idx = content.find("有什么")
        if idx == -1:
            idx = content.find("有啥")
        if idx == -1:
            return False

        # 前方最多20字符窗口（用于检查思考标记和排除外向求助）
        pre_window = content[max(0, idx - 20):idx]

        # 排除明确外向求助信号（「请问/想问」本身就是 ask；「有朋友/有没人/大家来」等是外向）
        EXTERNAL_ASK = [
            "请问", "想问", "有朋友", "有没人", "大家来",
            "来说说", "说说看", "指导下", "请大家", "想请教", "想知道",
        ]
        for sig in EXTERNAL_ASK:
            if sig in content:
                return False

        # 排除强求助前缀「求」
        if "求" in pre_window:
            return False

        # 自语特征：第一人称思考（「想/我在/我想/自己」在「有什么」之前）
        SELF_TALK_MARKERS = ["想", "我在", "我想", "自己"]
        for marker in SELF_TALK_MARKERS:
            if marker in pre_window:
                return True

        # Pattern: 「有什么〦勃定」 = 个人隂性心态描这\uff0c不是真求助
        # 例：「有什么公交车来就勃定去哪里吃」 = 描这自己的旅�%A1�方式\uff0c不是问别人推荐
        if re.search(r'有什么.{0,20}(就决定|就看|就跟|就根据|就去|就走|就算|就当|就算它|就当是)', content):
            return True
        # Pattern: 明显随机/随性心态描述（无「有什么」前缀）
        if re.search(r'(走到哪|走到哪算哪|随便|随意|随性)', content):
            return True

        return False

    def _is_soft_ad_question(self, content: str) -> bool:
        """
        检测以问句开场的软广推广帖。

        典型结构：正文前几句以「有什么/有啥/请问」等问句词开场，
        紧跟宝藏店铺/品牌/特产推荐，是探店软广，不是真求助。

        判断逻辑：
          - 正文前几句含以问句词开头的句子
          - 且后面内容含软广特征词（宝藏店铺/一站式搞定/超级方便等）>= 2 个
          → 软广，拒绝
          - 仅有问句开场但无软广词 → 可能是真求助，不拦截
        """
        if not content or len(content.strip()) < 10:
            return False

        # 先检查软广特征词（正文里）
        ad_phrases = [
            "宝藏店铺", "一站式搞定", "超级方便", "太全了",
            "海味干货", "包装精美", "送礼都超有面儿",
            "来一站式", "特产真的太全",
            "精选", "天然", "品质", "专业只生产",
            "厂家", "力荐", "推荐产品", "荣获",
        ]
        ad_count = sum(1 for phrase in ad_phrases if phrase in content)
        if ad_count < 2:
            return False

        # 检查前几句是否有以问句词开头的句子
        opening_patterns = ["有什么", "有啥", "请问", "想问", "问问", "求推荐", "求问"]
        for line in content[:200].split("\n")[:4]:
            for sep in ["。", "？", "！"]:
                first_part = line.split(sep)[0].strip()
                # 用 `in` 检查（有些句子前面有地名/主语前缀，如「汕尾有什么特产」）
                if any(p in first_part[:15] for p in opening_patterns):
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

    # 纯体验分享/种草关键词（正文含这些说明不是真求助，是分享/陪伴/记录帖）
    # 注意：「去汕尾/来汕尾」不加入——真实求助帖也常说「去汕尾有什么推荐」
    EXPERIENCE_SHARE_KEYWORDS = [
        # 体验感叹（感叹语气是分享帖特征）
        "太幸福了", "绝了", "太好吃", "种草", "宝藏", "封神", "封神了",
        "今天也", "居然", "竟然", "太棒了", "太好吃了", "太美了",
        "我爱了", "也太", "真的绝", "名不虚传", "来实现",
        # 到达/出发完成时态（分享帖特征：已经去了，不是计划去）
        "终于来了", "第一次来汕尾", "回来了",
        # 陪伴/家庭/宠物出行
        "带爸妈", "陪爸妈", "带着", "一家人", "带上小狗", "带狗", "小狗知道",
        # 旅行记录/完成时态
        "24年想看", "26年看了", "朋友开车", "这趟旅行", "这次来",
        "两年前", "翻到了",
        # 体验发现类表达（发现+感叹=分享帖）
        "来汕尾才知道", "也是喝上", "也是吃上", "才知道汕尾", "原来汕尾",
        # 负面/吐槽/避雷表达（本质是分享帖，不是真求助）
        "避雷", "吐槽", "崩溃", "踩雷", "差了点意思",
        "还没去就", "没去成", "不值", "太坑了", "太烂了",
        "被坑了", "后悔来", "后悔去", "再也不来", "太不值得",
        # 感叹句式
        "也太幸福", "太好吃了", "太治愈", "太绝了", "真的好",
        # 攻略指南/种草结构（分享帖典型句式）
        "住宿推荐", "推荐玩", "可以瞅瞅周边", "打卡地", "周边景点",
        # 分享帖典型推荐结构（「好吃推荐」「炒鸡推荐」「必吃」等是第一人称种草，非求助）
        "好吃推荐", "炒鸡推荐", "必吃", "值得吃", "强力推荐",
        "推荐必吃", "推荐这家", "一定要吃", "良心推荐",
        # 网络分享语气（强烈分享/种草信号）
        "家人们谁懂啊", "谁懂啊", "家人们谁懂",
        "我来啦", "冲鸭", "绝了绝了", "太爱了", "太可了",
        "真的哭死", "哭死", "太治愈了", "太浪漫了",
    ]
    # 正文太短时的 ask 依赖阈值（正文不足30字 + 只有标题/标签 ask = 不可靠）
    MIN_CONTENT_LEN_FOR_TAG_ASK = 30

    # 目的地不匹配检测：正文大量提其他城市名，但问的是那个城市能做什么
    # 常见：「去汕尾→回广州→问广州能干啥」
    DEST_MISMATCH_KEYWORDS = [
        "广州南", "广州站", "广州东", "广州市区", "广州能", "广州有", "广州哪", "去广州", "回广州", "到广州",
        "深圳北", "深圳站", "深圳能", "深圳有", "去深圳", "回深圳",
    ]

    def _check_destination_mismatch(self, content: str, title: str) -> bool:
        """
        检测目的地意图不匹配：问的是中转城市（如「广州南」），不是目标城市。
        典型：「五一去汕尾→回广州→问广州南附近能干啥」
        正文提「广州南/广州能/去广州」且有「问/能/哪」等问句格式 → 目的地不匹配。
        """
        combined = content + title
        hit_count = sum(1 for kw in self.DEST_MISMATCH_KEYWORDS if kw in combined)
        # 命中 ≥2 个目的地不匹配词 + 正文有问句 → 不是问汕尾
        if hit_count >= 2 and any(kw in combined for kw in ["问", "能", "哪", "什么", "怎么"]):
            return True
        # 命中「广州南」或「广州能/有/哪」+ 有关键问句 → 不匹配
        if ("广州南" in combined or "广州能" in combined or "广州有" in combined or "广州哪" in combined):
            if any(kw in combined for kw in ["问", "能", "哪", "什么", "怎么", "做", "吃", "玩"]):
                return True
        return False

    # ── 民宿/商家自推广检测 ───────────────────────────────────────
    MERCHANT_ACCOM_KEYWORDS = [
        "自家民宿", "自营民宿", "自营酒店",
        "联系我", "加我微信", "加微信", "私信我", "电话咨询",
        "预订请", "订房请", "入住请", "预约请", "联系掌柜",
        "欢迎预", "欢迎来住", "欢迎入住",
        "四房一厅", "三房", "三房两厅", "两房一厅", "六房", "五房", "五床",
        "整栋出", "整栋租", "整层出",
        "专业接待", "团队接待", "可接团",
    ]
    MERCHANT_ACCOM_REJECT_PATTERNS = [
        r"自家民宿", r"自营民宿", r"自营酒店",
        r"(联系|加|私信).{0,6}(微|微信|我|)[^\u4e00-\u9fa5]*[1-9]",
        r"(欢迎|需要).{0,10}(预|订|入)",
        r"四房一厅", r"三房两厅", r"两房一厅",
        r"整栋.{0,4}(出|租|售)",
        r"麻将.{0,6}(房|室|厅)", r"(KTV|棋牌).{0,6}(房|室|厅)",
        r"(专业|团队).{0,6}(接|接待)",
    ]

    def _is_merchant_accommodation(self, combined: str) -> bool:
        """
        检测是否为民宿/酒店商家的自推广帖。
        典型特征：含「自家民宿」「四房一厅」「麻将」「加微信预订」等
        这类内容有 ask 信号（问推荐），但本质是商家打广告，不应通过。
        """
        for kw in self.MERCHANT_ACCOM_KEYWORDS:
            if kw in combined:
                return True
        for pat in self.MERCHANT_ACCOM_REJECT_PATTERNS:
            if re.search(pat, combined):
                return True
        return False

    def _get_pass_reasons(self, title: str, content: str, note_types: list[str]) -> list[str]:
        """判断通过原因。宽松规则：有地域+有note_types+无强拒绝=通过"""
        reasons = []
        # 去掉标签，避免标签里的关键词干扰信号判断
        content_no_tags = re.sub(r'#.+?(?=\s|#|$)', '', content)
        # 标题也要去掉标签（如「#求推荐 #出招」是标签，不是正文 ask 信号）
        title_clean = re.sub(r'#.+?(?=\s|#|$)', '', title)

        # 求助信号（高优先级）：正文（去标签） + 标题（去标签）都要看
        has_ask_signal = has_signal(content_no_tags, ASK_SIGNALS) or has_signal(title_clean, ASK_SIGNALS)
        content_has_ask = has_signal(content_no_tags, ASK_SIGNALS)
        title_has_ask = has_signal(title_clean, ASK_SIGNALS)

        if has_ask_signal:
            # 自语帖
            if self._is_self_talk(content_no_tags):
                pass
            # 软广问句开场：正文第一句含「有什么/有啥」+ 紧跟店铺/品牌/特产推荐
            elif self._is_soft_ad_question(content_no_tags):
                pass  # 软广，不append ask
            else:
                reasons.append("ask")

        # 正文含体验分享/种草词 → 拦截（即使有 ask 信号也不放行）
        # 这些帖子：有 ask 信号但本质是分享/种草/陪伴记录，不算真求助
        # 检测范围：正文 + 标题（因为「避雷」/「吐槽」可能只出现在标题）
        share_hit = [kw for kw in self.EXPERIENCE_SHARE_KEYWORDS if kw in content_no_tags or kw in title]

        # 目的地意图不匹配：正文大量提其他城市（如「广州」），但询问的是那个城市能做什么
        # 而非在问「汕尾能做什么」。常见于「去汕尾→回广州→问广州能干啥」
        dest_mismatch = self._check_destination_mismatch(content_no_tags, title)
        if dest_mismatch:
            reasons.clear()  # 清除任何 ask 信号，强制拦截

        if share_hit:
            if not content_has_ask and not title_has_ask:
                pass  # 不可能有 ask，share_hit 已证明
            elif not content_has_ask and title_has_ask:
                # 只有标题有 ask → 正文太短不可靠，拦截
                if reasons and "ask" in reasons:
                    reasons.remove("ask")
            elif content_has_ask and share_hit:
                # 正文有 ask 但含分享词 → 判断 ask 信号的强度
                # strong_ask: 想问/求/求助/有什么/有没有（有明确需求意向词）
                # 补充强信号：有具体推荐问句结构（「有啥好吃推荐/有没有XX推荐」）
                # 反问语气检测：「还有什么烦恼」「有什么...不/没」→ 字面是问句，实际是满足/感叹语气，不算真求助
                is_rhetorical_what = bool(re.search(
                    r'还有什么[^\u4e00-\u9fa5]*?(烦恼|忧愁|不爽|难过)|有什么.?.?(不|没|么)\w',
                    content_no_tags
                ))
                if is_rhetorical_what:
                    # 反问语气：有 "有什么" 但上下文是「还有什么烦恼/不爽」→ 降级，不算 strong_ask
                    strong_ask = False
                else:
                    strong_ask = has_signal(content_no_tags, ["想问", "求", "求助", "有什么", "有没有"])
                has_recommend_ask = bool(re.search(r"有.{0,6}推荐", content_no_tags))
                if not strong_ask and not has_recommend_ask:
                    if reasons and "ask" in reasons:
                        reasons.remove("ask")
            elif title_has_ask and share_hit:
                # 标题有 ask 但标题本身含分享词（避雷/吐槽）→ 降级
                if reasons and "ask" in reasons:
                    reasons.remove("ask")
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
        # 注意：share_hit 非空时（已被识别为分享帖）禁止 type_match 兜底
        if note_types and not share_hit:
            # 纯分享/广告语气 → 淘汰（家宝藏/封神/种草语气）
            if re.search(r"宝藏|绝了|封神|太好吃|种草", content_no_tags):
                return reasons  # 不添加 type_match，走淘汰
            # 有问句/意图信号 → 通过（真实需求）
            # 限制：只用特定的行程咨询信号，不使用泛化的「吗/么/呢」问号
            # 因为「你们见过吗」是描述性问句，不等于求助
            if any(kw in content_no_tags for kw in ["怎么安排", "来得及吗", "来得及么", "够吗", "合适吗", "可以吗", "方便吗", "行吗", "适合吗"]) or "哪儿" in content_no_tags:
                reasons.append("type_match")
            # 内容较长 + 有意图词（排除被否定修饰的） → 通过
            # Removed: len>30 fallback too loose for type_match; require genuine ask signal
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
    CJK_RANGE = frozenset(range(0x4E00, 0x9FFF + 1)) | frozenset(range(0x3400, 0x4DBF + 1))
    for kw in kw_list:
        idx = text_lower.find(kw.lower())
        if idx == -1:
            continue

        # ── 否定词检查（向前看2字，否定词最长2字）────────────────
        NEGATIONS_SINGLE = ["不", "没", "别", "莫", "勿", "未", "否", "休", "甭"]
        NEGATIONS_PHRASE = ["不想", "不要", "不是", "不含", "没兴趣", "不考虑", "不去", "不知道", "不了解", "不清楚", "不确定", "没吃过", "没尝过"]
        POST_SIGNAL_NEG = ["不", "没", "无"]

        if idx >= 2:
            pre = text_lower[idx - 2:idx]
            last_char = pre[-1] if pre else ''
            if last_char in NEGATIONS_SINGLE:
                continue
            if any(n in pre for n in NEGATIONS_PHRASE):
                continue

        # ── 单字「求」被 CJK 前缀：复合词（X求）→ 跳过 ───────────
        # 例：「要求」(demand) ≠ 求帮，求助
        if kw == "求" and len(kw) == 1 and idx > 0:
            pre_char = text_lower[idx - 1]
            if ord(pre_char) in CJK_RANGE:
                continue

        # ── 信号后否定检查（如「去哪玩不重要」）───────────────────
        after_pos = idx + len(kw)
        if after_pos < len(text_lower):
            after_char = text_lower[after_pos]
            if after_char in POST_SIGNAL_NEG:
                continue

        return True
    return False
