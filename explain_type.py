"""解释 note_type = 美食推荐 是什么意思"""
import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout.reconfigure(encoding='utf-8')

from filter import classifier
import re

print("=== 美食推荐 的匹配规则 ===")
for pat in classifier.TYPE_SIGNALS_REGEX.get("美食推荐", []):
    print(f"  pattern: {pat}")

print()
content1 = "汕尾2天1夜，吃的都没踩雷 #汕尾美食 #五一"
text1 = content1.lower()
print(f"原文：{content1}")
print()
print("逐一匹配美食推荐规则：")
matched1 = []
for pat in classifier.TYPE_SIGNALS_REGEX.get("美食推荐", []):
    m = re.search(pat, text1)
    if m:
        matched1.append(m.group())
        print(f"  MATCH: pattern={pat} matched={m.group()}")
if not matched1:
    print("  (无匹配)")

print()
print("=== 红海湾笔记 的匹配 ===")
content2 = "📍广东 汕尾 红海湾～\n周末出差有1天半的自由活动时间"
text2 = content2.lower()
print(f"原文：{content2}")
matched2 = []
for pat in classifier.TYPE_SIGNALS_REGEX.get("景点推荐", []):
    m = re.search(pat, text2)
    if m:
        matched2.append(m.group())
        print(f"  MATCH: pattern={pat} matched={m.group()}")
if not matched2:
    print("  (无匹配)")

print()
print("=== 所以 note_type 是什么 ===")
print()
print("美食推荐：classifier 根据内容中的关键词判断这篇笔记属于哪种类型")
print("  - '美食' 出现在 '#汕尾美食' 里 → 触发美食推荐规则")
print("  - 注意：这里的触发是因为包含'美食'字样，不是说作者在求推荐")
print()
print("景点推荐：classifier 判断这篇是游玩类需求")
print("  - '红海湾' 是景区名 → 触发景点推荐")
print()
print("note_type 的设计意图：识别用户是来找美食、找住宿、找景点、找购物")
print("但它只能识别'用户在聊什么主题'，不能识别'用户有没有需求'")
print()
print("所以：")
print("  '汕尾2天1夜，吃的都没踩雷 #汕尾美食 #五一'")
print("  → note_type = 美食推荐 （只是说明内容涉及美食主题）")
print("  → 但这可能是一篇打卡/分享笔记，不是有需求的人在求推荐")