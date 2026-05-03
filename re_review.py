"""
re-review: 删除 5/2-5/3 误写入飞书的笔记
"""
import json, os, urllib.request

APP_TOKEN = "MtpRbyHq9aOP3csA3jVc6CYenuc"
TABLE_ID = "tblvxlFAqO5hP4fD"

# 待删除清单：(record_id, note_id, title, 删除原因)
TO_DELETE = [
    # 商家账号推广包车/约拍服务
    ("recvic3WiXreZg", "69f1ebee", "汕尾包车，7座商务车", "商家账号推广包车"),
    ("recvihX41zvtBO", "69f05bf3", "4.28汕尾红海湾玻璃海实时天气", "商家账号（汕尾文文bao🚗）"),
    ("recvihX4oM7mbi", "69f03548", "4.28汕尾红海湾海上古堡实时天气", "商家账号（汕尾文文bao🚗）"),
    # 纯分享帖（无任何问句/求助信号）
    ("recvic3VVxKWOO", "69f1fe1a", "记录二人一狗在汕尾没有攻略的10天", "纯分享帖无求助"),
    ("recvisyJO60HPR", "69f5a899", "捷胜潼山甘露寺", "纯分享帖无求助"),
    ("recvisyJqpkEKV", "69ef8e5d", "今天吃了好多好多东西…评价一下", "纯个人记录无求助"),
    ("recvisyIWQE8wo", "69f36cae", "汕尾美食记录📝边走边吃没踩雷", "纯分享帖（标题含'记录'）"),
    ("recvigurWkfWAZ", "69f0eb76", "土著带路｜盘点汕尾城区老牌美食", "纯攻略帖无求助"),
    ("recviihC3kdgdu", "69ec7de1", "珠三角周末逃离计划｜汕尾一日游很值得", "纯分享帖无问句"),
    ("recviitKtCGP91", "69f1bb09", "刚从汕尾回来真的比我想象中舒服", "纯分享帖无问句"),
    ("recviihccpsQ7b", "69f088d1", "晚云集大床房没有泡池的夜晚反而更治愈了", "民宿推广帖"),
    # 招募/找搭子
    ("recviqfjkdAB60", "69f2f7f1", "两头大肥猪即将到汕尾求安利", "找搭子"),
    # 筛选原因为空（filter未运行就写入）
    ("recviotfGzM34q", "69f3b4a8", "求推荐汕尾各种美食", "筛选原因为空"),
    ("recviqgukuhTl9", "69f2c4c4", "汕尾的朋友们帮忙看一下这个行程怎么样", "筛选原因为空"),
    ("recviqqmU0itqV", "69f07da5", "五一自驾去汕尾求推荐本地人才去的海鲜大排档", "筛选原因为空"),
    # 推广帖
    ("recvigip5pEL8A", "69f31154", "汕尾城区Get首家泰式瓦罐小火锅", "商家推广"),
    ("recvigioCWQQy3", "69ee0c7c", "金町湾美食推荐", "商家账号发布纯推荐"),
]

print(f"共 {len(TO_DELETE)} 条待删除")

# 获取 token
def get_token():
    app_id = os.environ.get("FEISHU_APP_ID", "")
    app_secret = os.environ.get("FEISHU_APP_SECRET", "")
    if not app_id or not app_secret:
        from pathlib import Path
        sf = Path(__file__).parent / "secrets.json"
        if sf.exists():
            d = json.loads(sf.read_text(encoding="utf-8"))
            app_id = app_id or d.get("feishu_app_id", "")
            app_secret = app_secret or d.get("feishu_app_secret", "")
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp).get("tenant_access_token", "")

token = get_token()
print(f"Token: {token[:20]}...")

def delete_record(record_id: str) -> bool:
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/{record_id}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
        method="DELETE"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.load(resp)
            return result.get("code") == 0
    except Exception as e:
        print(f"    删除失败: {e}")
        return False

print("\n开始删除...")
deleted = 0
failed = []
for rec_id, note_id, title, reason in TO_DELETE:
    ok = delete_record(rec_id)
    status = "✅" if ok else "❌"
    print(f"{status} [{rec_id}] {title[:25]}... | {reason}")
    if ok:
        deleted += 1
    else:
        failed.append((rec_id, note_id, title))
    import time; time.sleep(0.3)

print(f"\n删除完成: 成功 {deleted}/{len(TO_DELETE)}")
if failed:
    print(f"失败 ({len(failed)}): {[x[1] for x in failed]}")