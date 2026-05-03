"""Fix CJK_RANGE in _has_unnegated_intent: use frozenset instead of range union"""
with open(r'E:\translate\claw\xhs-auto-traffic-v2\filter\filter_service.py', encoding='utf-8') as f:
    content = f.read()

old = '        CJK_RANGE = range(0x4E00, 0x9FFF + 1) | range(0x3400, 0x4DBF + 1)'
new = '        CJK_RANGE = frozenset(range(0x4E00, 0x9FFF + 1)) | frozenset(range(0x3400, 0x4DBF + 1))'

if old in content:
    content = content.replace(old, new, 1)
    with open(r'E:\translate\claw\xhs-auto-traffic-v2\filter\filter_service.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed CJK_RANGE OK")
else:
    print("NOT FOUND:", repr(old))
    # Show what's actually there
    idx = content.find('CJK_RANGE')
    if idx >= 0:
        print("Found at:", idx, repr(content[idx:idx+80]))