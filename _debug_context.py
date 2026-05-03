"""Deep debug: understand the exact text context around 求 in 69ef3f8f"""
import sys, re
sys.path.insert(0, r'E:\translate\claw\xhs-auto-traffic-v2')

content = (
    '如果你想51带娃去海边，又不想人挤人，那我推荐广东汕尾这个小众城市！不用做攻略，直接🐎住着这里！\n'
    '🚗DAY1金町湾沙滩🏖️➡️Day2沙舍尾➕凤山旅游度假区➡️Day3红海湾一日游🏖️\n\n'
    '之前出去旅行每次都要手动搜索🔍景点之间的位置，用了百度地图的小度想想行程助手，输入想去的目的地和要求，它一键出路线攻略，对宝妈来说真的太节省时间了！\n'
    '✅添加专属喜好、一键规划路线\n'
    '✅随时mark修改行程\n'
    '✅贴心提醒：海边防晒&退潮时间\n\n'
    'Day1️⃣金町湾沙滩\n'
    '海上香格里拉：拥有7公里长的原生沙滩，沙子很细！\n'
    '✔️风帆礼堂：白色建筑+椰林，双层轨道巴士🚌\n'
    '✔️鲸湾小镇：坐海上小火车（🎫抖🎵便宜）\n'
    '✔️'
)
content_no_tags = re.sub(r'#.+?(?=\s|#|$)', '', content)
text_lower = content_no_tags.lower()

# Find all occurrences of single-char "求" (not part of multi-char signal)
print("Text around '求' (pos 143):")
for i, ch in enumerate(text_lower[130:160]):
    print(f"  {130+i}: {repr(ch)}")

# Check: what multi-char words contain 求 in the text?
print()
print("Multi-char words containing '求':")
import re
for m in re.finditer(r'.{0,2}求.{0,2}', text_lower):
    start = m.start()
    end = m.end()
    word = m.group()
    # Check if it's preceded by a CJK char (meaning 求 is NOT first char of word)
    preceded_by_cjk = start > 0 and ord(text_lower[start-1]) > 0x2E7F
    print(f"  pos {start}: {repr(word)} (preceded_by_cjk={preceded_by_cjk})")

print()
# The real fix: when single-char "求" is found, check if it's preceded by a CJK char
# If yes → it's part of a compound word (要求/请求/力求), NOT an ask signal
print("Proposed fix validation:")
for m in re.finditer(r'求', text_lower):
    idx = m.start()
    preceded_by_cjk = idx > 0 and ord(text_lower[idx-1]) > 0x2E7F
    print(f"  '求' at {idx}: preceded_by_cjk={preceded_by_cjk}, pre_char={repr(text_lower[idx-1])}, context={repr(text_lower[max(0,idx-2):idx+4])}")
    if preceded_by_cjk:
        print("    → would skip (compound word)")