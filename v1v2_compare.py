"""v1 vs v2 规则对比"""
import sys
sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout.reconfigure(encoding='utf-8')

from core.note_detail import NoteDetail
from filter.filter_service import FilterService, classify_types, has_signal
from filter.filter_service import ASK_SIGNALS

content = "📍广东 汕尾 红海湾～\n周末出差有1天半的自由活动时间\n小红书看了看，还是不知道怎么安排..."

svc = FilterService()
note_types = classify_types("", content)

print(f"笔记内容：{content}")
print(f"note_types：{note_types}")
print()

print("=== 过滤路径 ===")
print(f"地域 ✅ → 强拒绝 ❌ → 商家账号 ❌ → 纯分享贴 → has_any_ask=False → 不淘汰")
print(f"→ 纯交通：交通关键词=[] → 不过")
print(f"→ 广告：[] → 不过")
print()

print("=== v1 严格模式 _get_pass_reasons ===")
print(f"输入: title='', content, note_types={note_types}")
print(f"  ASK信号: {has_signal(content, ASK_SIGNALS)}")
print(f"  trip_question: False")
print(f"  urgent: False")
print(f"  weak_desire(想去/好想去/打算): False")
print(f"  type_match (v1无此分支): False")
print(f"v1 返回: [] → 淘汰原因='无明确需求'")
print(f"v1 最终结果: ❌ 淘汰")
print()

print("=== v2 宽松模式 _get_pass_reasons ===")
print(f"输入: title='', content, note_types={note_types}")
print(f"  ASK/trip/urgent/weak 均为 False → 继续")
print(f"  note_types=景点推荐 → type_match ✅")
print(f"v2 返回: ['type_match']")
print(f"v2 最终结果: ✅ 通过，reasons=type_match")
print()

print("=== 结论 ===")
print(f"  v1 严格：❌ 淘汰（无ASK关键词）")
print(f"  v2 宽松：✅ 通过（有note_types=景点推荐）")