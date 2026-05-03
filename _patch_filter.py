"""Patch filter_service.py: fix has_signal and _has_unnegated_intent"""
with open(r'E:\translate\claw\xhs-auto-traffic-v2\filter\filter_service.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    # ── Patch 1: Fix has_signal - remove the "求" special case block ──
    if 'def has_signal(' in lines[i] and i == 0 or \
       (i > 0 and 'def has_signal(' in lines[i] and not lines[i].startswith('    ')):
        # Copy original has_signal until we hit the "求" special case block
        j = i
        while j < len(lines):
            if '        # ── 单字「求」后缀检查' in lines[j]:
                # Skip this block (7 lines)
                j += 9  # skip the comment (1) + if block (8)
                break
            new_lines.append(lines[j])
            j += 1
        i = j
        continue

    # ── Patch 2: Fix _has_unnegated_intent - add CJK check after 想想/想要/想去 ──
    if 'def _has_unnegated_intent' in lines[i]:
        new_lines.append(lines[i])  # def line
        i += 1
        new_lines.append(lines[i])  # docstring
        i += 1
        new_lines.append(lines[i])  # INTENT_WORDS line
        i += 1
        new_lines.append(lines[i])  # NEG_PREFIXES_SORTED start
        i += 1
        new_lines.append(lines[i])  # NEG_PREFIXES_SORTED content
        i += 1
        new_lines.append(lines[i])  # NEG_PREFIXES_SORTED end
        i += 1
        new_lines.append(lines[i])  # text_lower = ...
        i += 1
        # Now the for loop - copy as-is until after "if not negated: return True"
        while i < len(lines):
            if '            if not negated:' in lines[i]:
                new_lines.append(lines[i])  # if not negated:
                i += 1
                new_lines.append(lines[i])  # return True
                i += 1
                # Add CJK check before return False
                new_lines.append('            # 「想」后接 CJK 字符（想想/想要/想去）→ 复合词，非独立意图\n')
                new_lines.append('            if kw == "想" and idx + 1 < len(text_lower):\n')
                new_lines.append('                after_char = text_lower[idx + 1]\n')
                new_lines.append('                if ord(after_char) in range(0x4E00, 0x9FFF + 1) | range(0x3400, 0x4DBF + 1):\n')
                new_lines.append('                    continue\n')
                break
            new_lines.append(lines[i])
            i += 1
        # Replace the remaining loop with the cleaned version
        # Copy remaining lines until end of function
        funcIndent = '    '
        while i < len(lines):
            l = lines[i]
            # Stop at next top-level def
            if l.startswith('    def ') or (l.startswith('class ') or l.startswith('async def ') or (l.startswith('def ') and not l.startswith('        '))):
                # Next function starts - back up
                break
            i += 1
        new_lines.append('        return False\n')
        continue

    new_lines.append(lines[i])
    i += 1

with open(r'E:\translate\claw\xhs-auto-traffic-v2\filter\filter_service.py', 'w', encoding='utf-8', newline='\n') as f:
    f.writelines(new_lines)

print("Done. Lines:", len(new_lines))