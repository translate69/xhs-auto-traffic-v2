import sys
sys.path.insert(0, r'E:\translate\claw\xhs-auto-traffic-v2')
import importlib
import filter.filter_service
importlib.reload(filter.filter_service)
from filter.filter_service import FilterService, STRONG_REJECT_KEYWORDS
from core.note_detail import NoteDetail

svc = FilterService()
print("Keywords:", STRONG_REJECT_KEYWORDS)

content1 = '红海湾约拍日常\n红海湾bao🚗，随叫随到！\n大学生好说话有耐心，会规划'
note1 = NoteDetail(url='', title='4.28汕尾红海湾玻璃海实时天气', author='test', content=content1, published_at='')
note1.keyword = '汕尾红海湾攻略'
r1 = svc.filter_one(note1)
print("Test 1 (with emoji):", r1.passed, r1.reasons)

content2 = '红海湾约拍日常\n红海湾bao，随叫随到！\n大学生好说话有耐心，会规划'
note2 = NoteDetail(url='', title='4.28汕尾红海湾玻璃海实时天气', author='test', content=content2, published_at='')
note2.keyword = '汕尾红海湾攻略'
r2 = svc.filter_one(note2)
print("Test 2 (no emoji):", r2.passed, r2.reasons)