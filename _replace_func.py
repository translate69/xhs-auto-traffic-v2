"""Byte-level replacement of has_signal function"""
with open(r'E:\translate\claw\xhs-auto-traffic-v2\filter\filter_service.py', 'rb') as f:
    raw = f.read()

# Find has_signal start - look for the UTF-8 string "def has_signal"
func_start_marker = 'def has_signal'.encode('utf-8')
hs_start = raw.find(func_start_marker)
if hs_start == -1:
    print("ERROR: def has_signal not found")
    exit(1)
print(f"has_signal starts at byte {hs_start}")

# Find the end: look for "return False\n    return False" at module level (8 spaces indent = 8 bytes)
# This is the last function in the file
# We find the second-to-last "return False" that's indented with 4 spaces
return_false = b'    return False'
# Find all occurrences
positions = []
start_search = hs_start
while True:
    pos = raw.find(return_false, start_search)
    if pos == -1:
        break
    positions.append(pos)
    start_search = pos + 1
print(f"Found {len(positions)} '    return False' occurrences at: {positions}")

# The last one is at the end of has_signal
# But actually there might be only 1 (at end of file)
# The function ends with "return False\n" (4-space indent = the function body)
# And then another "return False" at column 0 isn't possible
# Actually the file ends with: "return False\n" then nothing
# The issue is there's no second "return False" at end of file

# Let me find the actual end: look for the pattern "return True\n    return False"
# at the end of the file (has_signal's final lines)
pattern = b'return True\r\n    return False'
pos_end = raw.rfind(pattern)
print(f"'return True\\r\\n    return False' at byte {pos_end}")
if pos_end > hs_start:
    # This is the end of has_signal (the function's final return)
    func_end = pos_end + len(b'return True\r\n    return False')
    print(f"has_signal ends at byte {func_end}")
else:
    # Try without \r
    pattern2 = b'return True\n    return False'
    pos_end2 = raw.rfind(pattern2)
    print(f"'return True\\n    return False' at byte {pos_end2}")
    func_end = pos_end2 + len(b'return True\n    return False')
    print(f"has_signal ends at byte {func_end}")

# New has_signal function bytes (UTF-8 encoded)
NEW_FUNC = '''def has_signal(text: str, kw_list: list[str]) -> bool:
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
'''.encode('utf-8')

print(f"\nNew function length: {len(NEW_FUNC)} bytes")
print(f"Old function range: {hs_start} - {func_end} ({func_end - hs_start} bytes)")

# Replace
new_raw = raw[:hs_start] + NEW_FUNC + raw[func_end:]
print(f"New file length: {len(new_raw)} (was {len(raw)})")

with open(r'E:\translate\claw\xhs-auto-traffic-v2\filter\filter_service.py', 'wb') as f:
    f.write(new_raw)
print("Written OK")