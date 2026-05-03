"""删除 29 条误通过的记录"""
import json, time, urllib.request
from pathlib import Path

APP_TOKEN = "MtpRbyHq9aOP3csA3jVc6CYenuc"
TABLE_ID = "tblvxlFAqO5hP4fD"

# 29 条待删除（来自 re-review 结果）
TO_DELETE = [
    ("recvi7hytlrEdU", "69ef5cd2000000003601b90d", "下周就要出发去汕尾啦", "纯分享帖无问句"),
    ("recvibXz2j10Vx", "69efa240000000002003b965", "五一假期去汕尾咋样", "纯分享帖无问句"),
    ("recvic3WiXreZg", "69f1ebee000000001e00dbd8", "汕尾包车，7座商务车", "商家账号推广包车"),
    ("recvifUFdukY70", "69f2ebae000000002202b96a", "远离城市喧嚣汕尾藏着温柔晚风", "纯分享帖"),
    ("recvigurWkfWAZ", "69f0eb760000000023014e51", "土著带路盘点汕尾城区老牌美食", "纯分享帖"),
    ("recvigRpLilD9g", "69f333680000000038035df0", "一万种旅行howto", "纯分享帖"),
    ("recvihX41zvtBO", "69f05bf30000000036003af6", "4.28汕尾红海湾玻璃海实时天气", "商家账号推广约拍"),
    ("recvihX4oM7mbi", "69f035480000000035027914", "4.28汕尾红海湾海上古堡实时天气", "商家账号推广约拍"),
    ("recviimyidGpNW", "69f38972000000002202b3a9", "汕尾五一酒店太惊人太鲜明的对比了", "纯分享帖"),
    ("recviip55s03fj", "69f226db0000000035021105", "SeasideDiary海边日记", "纯分享帖"),
    ("recviipa8dWYTW", "69ee100d000000003502e9fa", "如果在汕尾只有一天时间很推荐这些", "纯分享帖"),
    ("recviqgukuhTl9", "69f2c4c4000000001a034dac", "汕尾的朋友们帮忙看一下这个行程", "筛选原因为空+无问句"),
    ("recvisyJO60HPR", "69f5a8990000000038023132", "捷胜潼山甘露寺", "纯分享帖"),
    ("recviszaJI3Fzr", "69f19fca0000000035031efb", "汕尾我来了", "找搭子/结伴"),
    ("recvitomWKfBbA", "69f1e921000000001e00cd16", "只知汕头不知汕尾", "纯分享帖"),
    ("recvitonjSfj11", "69f1e58b0000000023016c92", "莲塘口岸最新消息", "非相关地域"),
    ("recvitqyUmRg7j", "69f5e94f000000003503a697", "5.2汕尾红海湾海上古堡现状", "纯分享帖"),
    ("recvitqzgO3swS", "69f5c0da000000003601fa4f", "5月2号的汕尾玻璃海", "纯分享帖"),
    ("recvitqzFQHYFR", "69f4b927000000002301e4be", "汕尾住宿价格太惊人太鲜明的对比了", "纯分享帖"),
    ("recvitu3untJtQ", "69f4c85f0000000035025cb4", "好想快点洗澡睡觉", "内容与关键词无关"),
    ("recvitw2jUOFA1", "69f5ba55000000003701e220", "想避开51人流那就来鲘门吧", "纯分享帖"),
    ("recvitzGhbD9Op", "69f1fcf9000000003502b97e", "幼儿园美食", "非相关地域"),
    ("recvitAQxWTyp7", "69f5eac8000000003502d2e5", "不是三亚去不起而是金町湾更有性价比", "纯分享帖"),
    ("recviuiRoFyzrv", "69f2043e0000000023014e47", "汕尾金町湾把海景搬进房间里的宝藏房源", "纯分享帖"),
    ("recviulziF1gp6", "69f60774000000003601947c", "汕尾到底算不算是潮汕呀", "纯分享帖"),
    ("recviulzNg2QaX", "69f601310000000035024859", "这个位置看古堡独家了", "纯分享帖"),
    ("recviunoDSGPBX", "69f232e500000000380366f5", "汕尾-深圳-东莞", "内容与关键词无关"),
    ("recviuoMMBhaG6", "69f6066a000000003502b3b1", "5.1汕尾逃", "纯分享帖"),
    ("recviurroTQwm5", "69f5f708000000003701d03e", "值得二刷的小镇妥妥的玻璃海", "纯分享帖"),
]

def get_token():
    import os
    app_id = os.environ.get("FEISHU_APP_ID", "")
    app_secret = os.environ.get("FEISHU_APP_SECRET", "")
    if not app_id:
        sf = Path("E:/translate/claw/xhs-auto-traffic-v2/secrets.json")
        if sf.exists():
            d = json.loads(sf.read_text(encoding="utf-8"))
            app_id = app_id or d.get("feishu_app_id", "")
            app_secret = app_secret or d.get("feishu_app_secret", "")
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp).get("tenant_access_token", "")

def delete_record(token, rec_id):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/{rec_id}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"}, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.load(resp)
            return result.get("code") == 0
    except Exception as e:
        print(f"    Error: {e}")
        return False

print("Getting token...")
token = get_token()
print(f"Token: {token[:20]}...")

print(f"\nDeleting {len(TO_DELETE)} records...")
deleted = 0
failed = []
for rec_id, note_id, title, reason in TO_DELETE:
    ok = delete_record(token, rec_id)
    status = "OK" if ok else "FAIL"
    print(f"[{status}] {rec_id} | {title[:30]} | {reason}")
    if ok:
        deleted += 1
    else:
        failed.append((rec_id, note_id, title))
    time.sleep(0.3)

print(f"\n=== Done: {deleted}/{len(TO_DELETE)} deleted ===")
if failed:
    print(f"Failed ({len(failed)}):")
    for rec_id, note_id, title in failed:
        print(f"  {rec_id} | {note_id} | {title}")