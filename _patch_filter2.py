"""Write new has_signal and _has_unnegated_intent functions to filter_service.py"""
with open(r'E:\translate\claw\xhs-auto-traffic-v2\filter\filter_service.py', encoding='utf-8') as f:
    content = f.read()

# ── New has_signal ──
NEW_HAS_SIGNAL = '''def has_signal(text: str, kw_list: list[str]) -> bool:
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
        # 关键词后紧跟的否定词（如「去哪玩不重要」）
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
    return False'''

# ── New _has_unnegated_intent ──
NEW_INTENT = '''    def _has_unnegated_intent(self, text: str) -> bool:
        """检测是否有未是否定修饰的意图词（想/计划/打算/准备/行程）
        注意：「想」后接 CJK 字符（想想/想要/想去）复合词不算独立意图"""
        CJK_RANGE = range(0x4E00, 0x9FFF + 1) | range(0x3400, 0x4DBF + 1)
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
        return False'''

# ── Locate and replace has_signal ──
import re
hs_match = re.search(r'(def has_signal\(text: str, kw_list: list\[str\]\) -> bool:.*?return False\n    return False)', content, re.DOTALL)
if hs_match:
    content = content[:hs_match.start()] + NEW_HAS_SIGNAL + '\n' + content[hs_match.end():]
    print("has_signal replaced")
else:
    print("has_signal NOT found, showing search...")
    idx = content.find('def has_signal(')
    print(content[idx:idx+500])

# ── Locate and replace _has_unnegated_intent ──
ui_match = re.search(r'(    def _has_unnegated_intent\(self, text: str\) -> bool:.*?return False\n        return False)', content, re.DOTALL)
if ui_match:
    content = content[:ui_match.start()] + NEW_INTENT + '\n' + content[ui_match.end():]
    print("_has_unnegated_intent replaced")
else:
    print("_has_unnegated_intent NOT found")

with open(r'E:\translate\claw\xhs-auto-traffic-v2\filter\filter_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("File written")