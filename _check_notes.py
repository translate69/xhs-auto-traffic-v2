import sys, json
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from core.note_detail import NoteDetail
from filter.filter_service import FilterService

filter_svc = FilterService()

test_cases = [
    # corpus 已有
    {"title": "沉浸式做汕尾这款宝藏美食！", "content": "沉浸式做汕尾这款宝藏美食！#芋头饺 #汕尾茶点供应 #手工芋", "author": "某用户", "keyword": "汕尾美食", "expected": False, "note_id": "69ef1538"},
    {"title": "（无标题）", "content": "五月二去从深圳去汕尾玩，凌晨五点的动车，有什么汕尾推荐游玩的住宿的地方吗#五一出行问活人 #汕尾", "author": "某用户", "keyword": "汕尾旅游", "expected": True, "note_id": "69ef89c2"},
    # 新发现的问题笔记
    {"title": "汕尾包车，7座商务车", "content": "汕尾红海湾包车一日游\n🕙出发时间：自由选择\n📍出发地点：汕尾站或汕尾市区或金町湾\n🚗车型：5 座 或7座 人数1-7人随停随走😜\n⏰时限：全程一天 8 小时", "author": "跟着阳光游汕尾🚗📷", "keyword": "汕尾旅游攻略", "expected": False, "note_id": "69f1ebee"},
    {"title": "记录二人一狗在汕尾没有攻略的10天", "content": "吃喝篇：很庆幸这一次吃到很多本地人的店，特别是城内路，早餐很多摆摊的...\n住宿篇：金町湾二刷的民宿：浪花朵朵", "author": "肥肥", "keyword": "汕尾旅游攻略", "expected": False, "note_id": "69f1fe1a"},
]

all_pass = True
for tc in test_cases:
    nd = NoteDetail(title=tc["title"], content=tc["content"], author=tc["author"], url="")
    nd.keyword = tc["keyword"]
    result = filter_svc.filter_one(nd, keyword=tc["keyword"])

    ok = (result.passed == tc["expected"])
    status = "✅" if ok else "❌"
    if not ok:
        all_pass = False

    print(f"{status} [{tc['note_id']}] expected={tc['expected']} got={result.passed} | {result.reasons}")

print()
if all_pass:
    print("All passed ✅")
else:
    print("Some failed ❌")