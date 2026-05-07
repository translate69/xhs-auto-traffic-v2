# FILTER_LOGIC.md - 过滤逻辑文档

> 上次更新：2026-05-06

## 整体流程（11步）

```
Step 1  时间过滤        → 早于 cutoff_date → 拒绝（时间过久）
Step 2  地域过滤        → 不含目标地域词 → 拒绝（非目标地域）
Step 2.5 跨城市蹭流量   → OTHER_CITY ≥3次且≥target×2 → 拒绝（跨城市蹭流量）
Step 3  商家账号检测    → 商家关键词命中 → 拒绝（商家账号）
Step 4  强拒绝词        → STRONG_REJECT 命中 → 拒绝（广告/推广/...)
Step 5  广告语气检测    → REJECT_PATTERNS 命中 → 拒绝（限时/开业/福利/...）
Step 6  民宿商家自推广  → MERCHANT_ACCOM 命中 → 拒绝（民宿商家推广）
Step 7  交通/搭子检测   → trip_question/找搭子信号 → 拒绝（纯交通问题/找搭子）
Step 8  弱意向过滤      → _is_weak_intent() → 拒绝（无明确需求）
Step 9  分类匹配       → type_match && _get_pass_reasons → 通过/拒绝
Step 10 结果输出
```

## 详细规则

### Step 2 - 地域过滤
- `REGION_KEYWORDS`：`汕尾`、`红海湾`、`金町湾`、`海丰`、`陆丰`、`二马路`、`三马路`
- 判断：标题+正文含关键词 → 通过；不含 → 拒绝（非目标地域）

### Step 2.5 - 跨城市蹭流量检测
- `OTHER_CITY_KEYWORDS`：90+个广东及全国旅游城市名
- 触发条件：正文+标签中命中其他城市词 ≥3次 **且** 命中次数 ≥ 目标城市出现次数×2
- 目的：过滤「顺便提一句隔壁城市」蹭流量的笔记

### Step 4 - 强拒绝词（STRONG_REJECT_KEYWORDS）
- 商家推广类：`自家果园`、`自家荔枝`、`我家荔枝`、`包邮`、`特价`、`秒杀`
- 房地产类：`房价`、`首付`、`月供`、`购房`、`业主急售`、`红本在手`
- 移民/留学：`移民`、`留学`、`签证`
- 虚假景点：`人造景点`、`人造沙滩`、`排队超长`

### Step 5 - 广告语气检测（REJECT_PATTERNS）
- `限时`/`开业`/`福利`/`广告`/`不踩雷`/`手慢无`/`真的绝了`/`封神`/`业主急售`/`建面约\d+㎡`

### Step 6 - 民宿商家自推广（_is_merchant_accommodation）
- 关键词：`自家民宿`、`四房一厅`、`麻将`、`加微信`、`欢迎预`
- 正则：`麻将.{0,6}(房|室|厅)`、`(专业|团队).{0,6}(接|接待)`
- 触发后直接拒绝

### Step 7 - 交通/搭子过滤
- `TRIP_QUESTION_SIGNALS`：`怎么去`、`怎么走`、`几点去`、`几点出发`、`怎么安排`
- 命中且无强 ask 信号 → 拒绝（纯交通问题）
- `找搭子/旅游同伴` 信号：`捞人`、`找伴`、`组队`、`求捡`、`一起玩`、`搭子`
- 命中 → 拒绝（找搭子/旅游同伴）

### Step 8 - 弱意向过滤（_is_weak_intent）
- 自语检测：`_is_self_talk()` 含「有什么」+ 前有「我想/我在/我想想」→ 拒绝
- 无明确需求：无一票通杀规则，依赖 Step 9 的 `_get_pass_reasons`

### Step 9 - 分类匹配 + _get_pass_reasons
```
输入：title, content, note_types

has_ask_signal   = has_signal(content_no_tags, ASK_SIGNALS) or has_signal(title, ASK_SIGNALS)
content_has_ask   = has_signal(content_no_tags, ASK_SIGNALS)
title_has_ask     = has_signal(title, ASK_SIGNALS)

reasons = []

# 1. 有 ask 信号
if has_ask_signal:
    if _is_self_talk(content_no_tags): pass  # 自语不append ask
    else: reasons.append("ask")

# 2. 目的地意图不匹配检测（_check_destination_mismatch）
if _check_destination_mismatch(): reasons.clear()  # 强制拦截

# 3. 分享帖检测（EXPERIENCE_SHARE_KEYWORDS 命中）
share_hit = [kw for kw in EXPERIENCE_SHARE_KEYWORDS if kw in content_no_tags or kw in title]
if share_hit:
    if content_has_ask: reasons.remove("ask")  # 降级为非ask
    elif title_has_ask: reasons.remove("ask")
    # 不append任何reason，保持后续trip_question/urgent通道

# 4. trip_question / urgent 信号
if has_signal(content_no_tags, TRIP_QUESTION_SIGNALS): reasons.append("trip_question")
if has_signal(content_no_tags, URGENT_SIGNALS):        reasons.append("urgent")

# 5. type_match 兜底
if note_types and not reasons: reasons.append("type_match")

# 6. 正文<MIN_CONTENT_LEN且无正文ask时，标题ask不可靠
if len(content_no_tags) < MIN_CONTENT_LEN_FOR_TAG_ASK:
    if "ask" in reasons and not content_has_ask: reasons.remove("ask")

返回 reasons（空[]=拒绝，非空=通过）
```

### ASK_SIGNALS（求助信号）
```
"求" "求推荐" "求带" "求问" "求攻略" "求美食" "求助"
"哪里好" "哪家好" "怎么玩" "住哪" "有没有推荐" "怎么选" "怎么安排"
"求住" "想问" "问一下" "蹲蹲" "求指教" "帮我" "帮帮我"
"有什么" "哪家好" "哪里好" "去哪吃" "去哪儿吃" "去哪玩" "去哪儿玩"
"知道" "想问下" "请问"
```

### EXPERIENCE_SHARE_KEYWORDS（分享/种草/陪伴/记录帖）
```
# 体验感叹
"太幸福了" "绝了" "太好吃" "种草" "宝藏" "封神" "封神了"
"今天也" "居然" "竟然" "太棒了" "太好吃了" "太美了"
"我爱了" "也太" "真的绝" "名不虚传" "来实现"

# 到达/出发完成时态
"终于来了" "第一次来汕尾" "回来了"

# 陪伴/家庭/宠物出行
"带爸妈" "陪爸妈" "带着" "一家人" "带上小狗" "带狗" "小狗知道"

# 旅行记录/完成时态
"24年想看" "26年看了" "朋友开车" "这趟旅行" "这次来"

# 体验发现类表达
"来汕尾才知道" "也是喝上" "也是吃上" "才知道汕尾" "原来汕尾"

# 负面/吐槽/避雷表达
"避雷" "吐槽" "崩溃" "踩雷" "差了点意思"
"还没去就" "没去成" "不值" "太坑了" "太烂了"
"被坑了" "后悔来" "后悔去" "再也不来" "太不值得"

# 感叹句式
"也太幸福" "太好吃了" "太治愈" "太绝了" "真的好"

# 网络分享语气
"家人们谁懂啊" "谁懂啊" "家人们谁懂"
"我来啦" "冲鸭" "绝了绝了" "太爱了" "太可了"
"真的哭死" "哭死" "太治愈了" "太浪漫了"
```

### URGENT_SIGNALS（紧急信号）
```
"急急" "急死了" "在线等" "马上到" "救命" "救命啊" "紧急"
```

### MIN_CONTENT_LEN_FOR_TAG_ASK = 30
正文不足30字时，只有标题的 ask 信号不可靠（正文需要有 ask 才能放行）

### DEST_MISMATCH_KEYWORDS（目的地意图不匹配）
```
"广州南" "广州站" "广州东" "广州市区" "广州能" "广州有" "广州哪"
"去广州" "回广州" "到广州"
"深圳北" "深圳站" "深圳能" "深圳有" "去深圳" "回深圳"
```
命中≥2个 + 有问句语气 → 目的地不匹配，强制拦截

---

## 问题笔记处理记录

| note_id   | 问题描述 | 处理结果 |
|-----------|---------|---------|
| 69ef1538  | 宝藏语气，纯分享种草，误通过 type_match 宽松规则 | ✅ 已修复：感叹语气 → 广告语气拒绝 |
| 69ef89c2  | 真实求助，content_has_ask漏识别「推荐」，被误判为纯分享攻略 | ✅ 已修复：移除泛化分享词，去掉"请" |
| 69f1ebee  | 商家广告，bao（包车缩写）和随叫随到未被覆盖 | ✅ 已修复：STRONG_REJECT加包车/地陪关键词 |
| 69f1fe1a  | 纯分享贴，标题「没有攻略」否定语气被漏检 | ✅ 已修复：否定词前缀检测 |
| 69f2ebae  | 纯分享贴，标签里「推荐/攻略」导致content_has_ask误判 | ✅ 已修复：标签ask不参与content_has_ask |
| 69f2e808  | 纯分享攻略贴，含「攻略」但无求助信号；「绝了」触发广告语气 | ✅ 已修复：感叹语气拒绝 |
| 69f31154  | 纯分享种草，「不知道」前3字含否定词「不」但has_signal误判为ASK | ✅ 已修复：否定前缀「不」检测 |
| 69f0eb76  | 纯分享攻略，意图词「想」被否定前缀「不」修饰，type_match误判 | ✅ 已修复：否定前缀「不」检测 |
| 69f05bf3  | 商家包车广告，bao未被STRONG_REJECT_KEYWORDS覆盖 | ✅ 已修复：STRONG_REJECT加bao/随叫随到 |
| 69f03548  | 商家包车广告，同上 | ✅ 已修复：同上 |
| 69f0a7af  | 自言自语，「有什么可以打包」是内心独白而非求助 | ✅ 已修复：_is_self_talk检测 |
| 69f9ce66  | 深圳房地产广告，REJECT_PATTERNS新增房地产广告格式后过滤 | ✅ 已修复：地域检查用笔记实际内容 |

---

## 通过率统计（2026-05-06 凌晨·最终）

- 总笔记：2029条（data/collected/runs 历史数据）
- 通过：37条（1.8%）
- 回归测试：17/17 ✅（含本次修复的5条）

### 通过的笔记类型
- `ask`：真实汕尾求助（住宿/美食/出行/票务等明确需求）
- `ask,urgent`：紧急求助（马上到/急急急）
- `urgent`：踩雷后紧急求助

### 本次拦截的5条（已加入 problem_notes）
| note_id | 问题 | 修复方式 |
|---------|------|---------|
| 69f07a33 | 攻略帖含完整住宿推荐结构，标签ask误判 | EXPERIENCE_SHARE_KEYWORDS 加"住宿推荐"结构词 |
| 69f0c9f4 | 民宿商家推广"三房五床"未被检测 | MERCHANT_ACCOM_KEYWORDS 加"三房""五床" |
| 69f2ae98 | 找音乐同好（河图），与旅游无关 | STRONG_REJECT_KEYWORDS 加"河图" |
| 69f1f867 | 攻略指南帖，周边景点推荐结构 | EXPERIENCE_SHARE_KEYWORDS 加"周边景点""打卡地" |
| 69f31292 | 旅行回忆帖，share_hit后被type_match兜底误放 | type_match兜底加 `not share_hit` 条件 |

### 关键Bug修复（本次）
1. 标题标签被计入 ASK_SIGNALS → 清理标题标签后再匹配
2. type_match 兜底未排除 share_hit → 加 `not share_hit` 条件
