import sys
sys.path.insert(0, "E:/translate/claw/xhs-auto-traffic-v2")
from filter.filter_service import FilterService
from core.note_detail import NoteDetail
from output.feishu_service import FeishuOutputService

note = NoteDetail()
note.url = "/explore/69d0e2690000000023021313"
note.title = "手残党必入！5款氛围感发饰提升精致感✨"
note.author = "某用户"
note.content = "手残党必入！5款氛围感发饰提升精致感✨ #发饰 #氛围感 #好物推荐"
note.keyword = "汕尾去哪吃"

svc = FilterService()
r = svc.filter_one(note, keyword="汕尾去哪吃")

print(f"r.passed = {r.passed}")
print(f"r.reasons = {r.reasons!r}")
print(f"type(r.reasons) = {type(r.reasons)}")
print(f"r.note_type = {r.note_type!r}")

note.filter_passed = r.passed
note.filter_reasons = r.reasons
note.filter_result = r

print(f"note.filter_reasons type: {type(note.filter_reasons)}")
print(f"note.filter_reasons value: {note.filter_reasons!r}")

# Test FeishuOutputService._note_detail_to_row
feishu = FeishuOutputService()
row = feishu._note_detail_to_row(note)
print(f"\nFeishu row: {row}")
print(f"reasons in row: {row.get('reasons', 'KEY NOT FOUND')!r}")