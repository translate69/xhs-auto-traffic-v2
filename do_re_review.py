"""
re-review 所有 5/2-5/3 飞书记录
基于 filter_service.py 规则，对每条笔记重新判断，输出应删除的 record_id 清单
"""
import json, re, urllib.request
from pathlib import Path

APP_TOKEN = "MtpRbyHq9aOP3csA3jVc6CYenuc"
TABLE_ID = "tblvxlFAqO5hP4fD"

REGION_KEYWORDS = ["汕尾", "红海湾", "金町湾", "海丰", "陆丰", "二马路", "三马路"]
ASK_SIGNALS = ["求", "求推荐", "求带", "求问", "求攻略", "求美食", "求助", "哪里好",
               "哪家好", "怎么玩", "住哪", "有没有推荐", "怎么选", "怎么安排",
               "求住", "想问", "问一下", "蹲蹲", "求指教", "帮我", "帮帮我",
               "有什么", "去哪吃", "去哪儿吃", "去哪玩", "去哪儿玩", "知道", "想问下", "请问"]
STRONG_REJECT = ["旅游搭子", "找旅游搭子", "找搭子", "求搭子", "旅行搭子", "包车", "bao",
                 "带车司机", "配司机", "驾驶员", "地陪", "约拍"]
MERCHANT_KEYWORDS = ["民宿", "酒店", "餐厅", "大排档", "包车", "陪拍", "导游", "旅行社",
                     "工作室", "客栈", "度假村", "别墅", "小院", "公寓", "海景房", "度假",
                     "小姐姐", "小哥哥", "管家", "趣墅记"]
SHARE_POST_KEYWORDS = ["攻略", "分享", "推荐", "打卡", "避雷", "合集", "探店", "测评",
                       "我的", "我去", "我吃", "不踩坑", "不踩雷", "保姆级", "超全",
                       "没有攻略", "无攻略", "没攻略"]
HOTEL_PRAISE = ["有温度的酒店", "不舍得离开", "服务周到", "强烈推荐", "必住", "太好住了", "推荐这家民宿", "这家酒店超赞"]

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

def has_signal(text, signals):
    return any(s in text for s in signals)

def is_recommendation_format(title):
    if not title: return False
    if title.startswith("求") or "求推荐" in title: return False
    if re.search(r"推荐[吗么呢？]", title): return False
    return bool(re.search(r".{0,10}推荐.{0,15}", title))

def should_reject(record):
    fields = record.get("fields", {})
    title = fields.get("标题", "") or ""
    content = fields.get("正文摘要", "") or ""
    author = fields.get("作者", "") or ""
    combined = title + " " + content

    has_region = any(kw in combined for kw in REGION_KEYWORDS)
    if not has_region:
        return False

    if any(kw in combined for kw in STRONG_REJECT):
        return True

    author_lower = author.lower()
    if any(kw in author_lower for kw in MERCHANT_KEYWORDS):
        if any(kw in author for kw in ["包车", "约拍", "导游", "旅行社", "民宿", "酒店"]):
            return True

    content_no_tags = re.sub(r'#.+?(?=\s|#|$)', '', content)
    title_has_ask = has_signal(title, ASK_SIGNALS)
    if is_recommendation_format(title):
        title_has_ask = False
    content_has_ask = has_signal(content_no_tags, ["求", "想问", "请问", "求指教", "帮我", "帮帮我", "推荐"])
    has_any_ask = title_has_ask or content_has_ask or ("帮我" in title) or ("帮帮我" in title)

    if not has_any_ask:
        if any(kw in combined for kw in HOTEL_PRAISE):
            return True
        if is_recommendation_format(title):
            return True
        if any(kw in combined for kw in SHARE_POST_KEYWORDS):
            if "记录" in title:
                return True
            tag_count = content.count("#")
            if tag_count >= 3 and not any(kw in title for kw in ["求", "请问", "帮", "问"]):
                return True

    reasons = fields.get("筛选原因", "")
    if not reasons or reasons.strip() == "":
        if not has_any_ask:
            return True

    return False

print("Fetching all Feishu records...")
records = get_all_records()
print(f"Total records: {len(records)}")

to_delete = []
for rec in records:
    fields = rec.get("fields", {})
    note_id = fields.get("笔记ID", "")
    title = (fields.get("标题", "") or "")[:40]
    author = fields.get("作者", "") or ""
    reasons = fields.get("筛选原因", "") or ""
    rec_id = rec.get("record_id", "")
    collected_keyword = fields.get("采集关键词", "") or ""
    content_preview = (fields.get("正文摘要", "") or "")[:50]

    reject = should_reject(rec)
    if reject:
        to_delete.append({
            "rec_id": rec_id,
            "note_id": note_id,
            "title": title,
            "author": author,
            "reasons": reasons,
            "keyword": collected_keyword,
            "content_preview": content_preview
        })
        print(f"[REJECT] rec_id={rec_id} note_id={note_id} author={author} reasons='{reasons}' title={title}")

print(f"\nTotal to delete: {len(to_delete)}")

# Save result
with open("E:/translate/claw/xhs-auto-traffic-v2/review_result.json", "w", encoding="utf-8") as f:
    json.dump(to_delete, f, ensure_ascii=False, indent=2)
print("Saved to review_result.json")

# Also output the delete script
delete_cmds = []
for item in to_delete:
    delete_cmds.append(f"curl -X DELETE 'https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/{item['rec_id']}' -H 'Authorization: Bearer <TOKEN>'")

with open("E:/translate/claw/xhs-auto-traffic-v2/do_delete.sh", "w", encoding="utf-8") as f:
    for item in to_delete:
        f.write(f"{item['rec_id']}|{item['note_id']}|{item['title']}\n")

print(f"Delete commands saved to do_delete.sh")
print("\nDelete list:")
for item in to_delete:
    print(f"  {item['rec_id']} | {item['note_id']} | {item['title']} | reasons={item['reasons']}")