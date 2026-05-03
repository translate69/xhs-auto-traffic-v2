"""Fix _has_unnegated_intent to skip CJK-compound 想想/想要/想去"""
with open(r'E:\translate\claw\xhs-auto-traffic-v2\filter\filter_service.py', encoding='utf-8') as f:
    content = f.read()

old = """    def _has_unnegated_intent(self, text: str) -> bool:
        \"\"\"检测是否有未是否定修饰的意图词（想/计划/打算/准备/行程）\"\"\"
        INTENT_WORDS = [\"想\", \"计划\", \"打算\", \"准备\", \"行程\"]
        # 否定前缀列表（按长度降序排列，避免短前缀干扰）
        NEG_PREFIXES_SORTED = sorted(
            [\"不想\", \"不想去\", \"不打算\", \"不计划\", \"不要\", \"不用\", \"不会\", \"不能\", \"没想\", \"没打算\", \"没计划\", \"不\", \"没\", \"别\"],
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
        return False"""

new = """    def _has_unnegated_intent(self, text: str) -> bool:
        \"\"\"检测是否有未是否定修饰的意图词（想/计划/打算/准备/行程）\"\"\"
        CJK_RANGE = range(0x4E00, 0x9FFF + 1) | range(0x3400, 0x4DBF + 1)
        INTENT_WORDS = [\"想\", \"计划\", \"打算\", \"准备\", \"行程\"]
        NEG_PREFIXES_SORTED = sorted(
            [\"不想\", \"不想去\", \"不打算\", \"不计划\", \"不要\", \"不用\", \"不会\", \"不能\", \"没想\", \"没打算\", \"没计划\", \"不\", \"没\", \"别\"],
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
            if kw == \"想\" and idx + 1 < len(text_lower):
                after_char = text_lower[idx + 1]
                if ord(after_char) in CJK_RANGE:
                    continue
            return True
        return False"""

if old in content:
    content = content.replace(old, new)
    with open(r'E:\translate\claw\xhs-auto-traffic-v2\filter\filter_service.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('REPLACED OK')
else:
    print('NOT FOUND - searching...')
    idx = content.find('def _has_unnegated_intent')
    if idx >= 0:
        print('Found at pos', idx)
        print(content[idx:idx+500])
    else:
        print('Function not found in file')
