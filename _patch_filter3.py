"""Patch filter_service.py by precise position"""
with open(r'E:\translate\claw\xhs-auto-traffic-v2\filter\filter_service.py', encoding='utf-8') as f:
    content = f.read()

import re

# ── Replace has_signal (at end of file) ──
# Find it precisely
hs_sig = 'def has_signal(text: str, kw_list: list[str]) -> bool:'
hs_start = content.find(hs_sig)
if hs_start == -1:
    print("ERROR: has_signal not found")
    import sys; sys.exit(1)

# Find the end: "return False\n    return False" at end of module
# We want everything from hs_start to the last "return False" at module level
hs_body = content[hs_start:]
# Remove the last "return False\n" (last line of function)
# The file ends with "...return False\n" - so trailing newline
lines = content[hs_start:].split('\n')
# Find the last line that's "    return False" (4 spaces indent = end of function)
func_lines = []
for l in lines:
    func_lines.append(l)
    if l.strip() == 'return False':
        break
hs_end = hs_start + len('\n'.join(func_lines)) + (1 if func_lines else 0)
print(f"has_signal: {hs_start} - {hs_end}")
print(f"Original tail ({len(content[hs_start:hs_end])} chars):")
print(repr(content[hs_start:hs_end][:200]))

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
                continue

        return True
    return False'''

# ── Replace _has_unnegated_intent ──
ui_sig = '    def _has_unnegated_intent(self, text: str) -> bool:'
ui_start = content.find(ui_sig)
if ui_start == -1:
    print("ERROR: _has_unnegated_intent not found")
    import sys; sys.exit(1)

# Find end of this function - next "    def " at same indent level
ui_body_start = content.find('\n', ui_start) + 1
ui_rest = content[ui_body_start:]
m = re.search(r'\n    def ', ui_rest)
if m:
    ui_end = ui_body_start + m.start()
else:
    ui_end = len(content)
print(f"_has_unnegated_intent: {ui_start} - {ui_end}")
print(f"Original ({len(content[ui_start:ui_end])} chars):")
print(repr(content[ui_start:ui_end][:300]))

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

# Apply replacements
new_content = content[:ui_start] + NEW_INTENT + content[ui_end:hs_start] + NEW_HAS_SIGNAL
print(f"\nOld content len: {len(content)}, New: {len(new_content)}")

with open(r'E:\translate\claw\xhs-auto-traffic-v2\filter\filter_service.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
print("Written OK")