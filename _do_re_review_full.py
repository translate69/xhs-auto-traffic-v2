"""
对飞书表格所有记录执行完整复查（使用 review_service.py 规则）
输出应删除的 record_id 列表并执行删除
"""
import json, os, re, urllib.request, sys, time
from pathlib import Path

sys_path = r"E:\translate\claw\xhs-auto-traffic-v2"
sys.path.insert(0, sys_path)

APP_TOKEN = "MtpRbyHq9aOP3csA3jVc6CYenuc"
TABLE_ID = "tblvxlFAqO5hP4fD"
LOG_PATH = Path(f"{sys_path}/re_review_log.txt")

def log(msg: str):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

def get_token():
    app_id = os.environ.get("FEISHU_APP_ID", "")
    app_secret = os.environ.get("FEISHU_APP_SECRET", "")
    if not app_id:
        sf = Path(f"{sys_path}/secrets.json")
        if sf.exists():
            d = json.loads(sf.read_text(encoding="utf-8"))
            app_id = app_id or d.get("feishu_app_id", "")
            app_secret = app_secret or d.get("feishu_app_secret", "")
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp).get("tenant_access_token", "")

def get_all_records():
    token = get_token()
    all_records = []
    page_token = ""
    while True:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records?page_size=100"
        if page_token:
            url += f"&page_token={page_token}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.load(resp)
            items = result.get("data", {}).get("items", [])
            all_records.extend(items)
            if not result.get("data", {}).get("has_more"):
                break
            page_token = result.get("data", {}).get("page_token", "")
    return all_records

def delete_record(token: str, record_id: str) -> bool:
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/{record_id}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"}, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.load(resp)
            return result.get("code") == 0
    except Exception as e:
        log(f"    删除失败: {e}")
        return False

MERCHANT_AUTHOR_KEYWORDS = [
    "民宿", "酒店", "餐厅", "大排档", "包车", "陪拍",
    "导游", "旅行社", "工作室", "客栈", "度假村",
    "别墅", "小院", "公寓", "海景房", "度假",
    "小姐姐", "小哥哥", "管家", "趣墅记",
    "bao", "bao🚗", "🚗", "约拍", "跟拍", "旅拍",
    "趣墅", "趣墅记", "趣墅海景",
]

SHARE_POST_KEYWORDS = [
    "攻略", "分享", "推荐", "打卡", "避雷", "合集",
    "探店", "测评", "我的", "我去", "我吃",
    "不踩坑", "不踩雷", "保姆级", "超全",
    "没有攻略", "无攻略", "没攻略",
]

ASK_SIGNALS_REVIEW = ["求", "想问", "请问", "求指教", "帮我", "帮帮我"]

def is_merchant_author(author: str) -> bool:
    if not author:
        return False
    return any(kw in author.lower() for kw in MERCHANT_AUTHOR_KEYWORDS)

def is_recommendation_format(title: str) -> bool:
    if not title:
        return False
    if title.startswith("求") or "求推荐" in title:
        return False
    if re.search(r"推荐[吗么呢？]", title):
        return False
    return bool(re.search(r".{0,10}推荐.{0,15}", title))

def should_reject(title: str, content: str, author: str, reasons: str) -> tuple[bool, str]:
    if not reasons or reasons.strip() == "":
        content_no_tags = re.sub(r'#.+?(?=\s|#|$)', '', content)
        title_has_ask = any(kw in title for kw in ASK_SIGNALS_REVIEW)
        content_has_ask = any(kw in content_no_tags for kw in ASK_SIGNALS_REVIEW)
        has_any_ask = title_has_ask or content_has_ask or ("帮我" in title) or ("帮帮我" in title)
        if not has_any_ask:
            return True, "reasons为空且无求助信号"

    if author and is_merchant_author(author):
        return True, f"商家账号({author})"

    content_no_tags = re.sub(r'#.+?(?=\s|#|$)', '', content)
    combined = f"{title} {content_no_tags}"
    title_has_explicit_ask = any(kw in title for kw in ASK_SIGNALS_REVIEW)
    content_has_ask = any(kw in content_no_tags for kw in ASK_SIGNALS_REVIEW)
    title_has_bang = "帮我" in title or "帮帮我" in title or "帮忙" in title
    has_any_ask = title_has_explicit_ask or content_has_ask or title_has_bang

    if not has_any_ask:
        if any(kw in combined for kw in SHARE_POST_KEYWORDS):
            return True, "纯分享攻略贴"
        if is_recommendation_format(title):
            return True, "纯分享推荐格式"

    return False, ""

# ─── 主流程 ─────────────────────────────────────────────
LOG_PATH.write_text("", encoding="utf-8")
log("Fetching all Feishu records...")
records = get_all_records()
log(f"Total records: {len(records)}")

to_delete = []
for rec in records:
    fields = rec.get("fields", {})
    note_id = fields.get("笔记ID", "") or ""
    title = fields.get("标题", "") or ""
    content = fields.get("正文摘要", "") or ""
    author = fields.get("作者", "") or ""
    reasons = fields.get("筛选原因", "") or ""
    rec_id = rec.get("record_id", "")

    reject, reason = should_reject(title, content, author, reasons)
    if reject:
        to_delete.append({
            "rec_id": rec_id,
            "note_id": note_id,
            "title": title[:80],
            "author": author,
            "reasons": reasons,
            "reject_reason": reason,
        })

log(f"Total to delete: {len(to_delete)}")

if not to_delete:
    log("没有需要删除的记录")
    sys.exit(0)

# 执行删除
token = get_token()
log(f"Token obtained, starting delete...")
deleted = 0
failed = []
for item in to_delete:
    ok = delete_record(token, item["rec_id"])
    status = "OK" if ok else "FAIL"
    log(f"[{status}] {item['rec_id']} | {item['reject_reason']}")
    if ok:
        deleted += 1
    else:
        failed.append(item)
    time.sleep(0.3)

log(f"\n结果: 成功 {deleted}/{len(to_delete)}")
if failed:
    log(f"失败 ({len(failed)}): {[x['rec_id'] for x in failed]}")

# 保存结果
with open(f"{sys_path}/review_result.json", "w", encoding="utf-8") as f:
    json.dump(to_delete, f, ensure_ascii=False, indent=2)
log(f"结果已保存到 review_result.json")
