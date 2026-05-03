"""Add CJK-preceded check for single-char 求 in has_signal"""
with open(r'E:\translate\claw\xhs-auto-traffic-v2\filter\filter_service.py', encoding='utf-8') as f:
    content = f.read()

# The exact text to find and replace
OLD = '''        # ── 信号后否定检查（如「去哪玩不重要」）───────────────────
        after_pos = idx + len(kw)
        if after_pos < len(text_lower):
            after_char = text_lower[after_pos]
            if after_char in POST_SIGNAL_NEG:
                # 紧跟的否定字，跳过
                continue

        # 无否定词，命中
        return True
    return False'''

NEW = '''        # ── 单字「求」被 CJK 字符前缀：复合词（要求/请求）→ 跳过 ───
        # 出现在「输入想去的目的地和要求」= 要求(demand)，不是求助
        if kw == "求" and len(kw) == 1 and idx > 0:
            pre_char = text_lower[idx - 1]
            # CJK 字符范围
            is_cjk = any(0x4E00 <= ord(pre_char) <= 0x9FFF,
                        0x3400 <= ord(pre_char) <= 0x4DBF)
            if is_cjk:
                continue  # 「X求」复合词，跳过

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

if OLD in content:
    content = content.replace(OLD, NEW, 1)
    with open(r'E:\translate\claw\xhs-auto-traffic-v2\filter\filter_service.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("PATCHED OK")
else:
    print("NOT FOUND - searching for partial match...")
    idx = content.find('信号后否定检查')
    if idx >= 0:
        print("Found at", idx)
        print(repr(content[idx-5:idx+200]))
    else:
        print("signal check not found")