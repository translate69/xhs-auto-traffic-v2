"""v1 vs v2 has_signal CJK 逻辑差异"""
import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout.reconfigure(encoding='utf-8')

# v1 has_signal 逻辑（简版）
NEGATIONS_V1 = ["不想", "不要", "不是", "不含", "没兴趣", "不考虑", "不去"]

def has_signal_v1(text: str, kw_list: list[str]) -> bool:
    """v1 版本：CJK 前缀直接跳过，不检查否定词"""
    text_lower = text.lower()
    for kw in kw_list:
        idx = text_lower.find(kw.lower())
        if idx == -1:
            continue
        if idx > 0:
            pre_char = text_lower[idx - 1]
            if 0x4E00 <= ord(pre_char) <= 0x9FFF:
                continue  # v1 逻辑：CJK 前缀直接跳过
        for window in range(4, 0, -1):
            if idx >= window:
                pre = text_lower[idx - window:idx]
                if any(n in pre for n in NEGATIONS_V1):
                    break
        else:
            return True
    return False

# v2 has_signal 逻辑（当前）
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

NEGATIONS_V2 = ["不想", "不要", "不是", "不含", "没兴趣", "不考虑", "不去"]

def has_signal_v2(text: str, kw_list: list[str]) -> bool:
    """v2 版本：CJK 前缀时只有有否定词才跳过，否则保留匹配"""
    text_lower = text.lower()
    for kw in kw_list:
        idx = text_lower.find(kw.lower())
        if idx == -1:
            continue
        if idx > 0:
            pre_char = text_lower[idx - 1]
            if 0x4E00 <= ord(pre_char) <= 0x9FFF:
                has_negation = any(
                    n in text_lower[idx - w:idx]
                    for w in range(4, 0, -1)
                    for n in NEGATIONS_V2
                    if idx >= w
                )
                if not has_negation:
                    pass  # 无否定词，保留匹配
                else:
                    continue  # 有否定词，跳过
        for window in range(4, 0, -1):
            if idx >= window:
                pre = text_lower[idx - window:idx]
                if any(n in pre for n in NEGATIONS_V2):
                    break
        else:
            return True
    return False

print("=== has_signal v1 vs v2 对比 ===\n")
test_cases = [
    ("汕尾美食求推荐", True, "标准ASK"),
    ("有没有人知道汕尾", False, "v1:CJK跳过→不过, v2:知道→通过"),
    ("追求推荐汕尾", False, "求被CJK前缀跳过"),
    ("帮我推荐汕尾", True, "帮我在ASK"),
    ("请问汕尾怎么玩", True, "请问在ASK"),
    ("美食有何推荐", False, "有字在求前面"),
    ("汕尾哪里好", True, "哪里好在ASK"),
]

for text, v1_expected, note in test_cases:
    v1_result = has_signal_v1(text, ASK_SIGNALS)
    v2_result = has_signal_v2(text, ASK_SIGNALS)
    v1_ok = "✅" if v1_result == v1_expected else "❌"
    v2_ok = "✅" if v2_result else "✅"
    diff = "←差异" if v1_result != v2_result else ""
    print(f"[{v1_ok}] v1={v1_result} [{v2_ok}] v2={v2_result} | {text!r} {note} {diff}")