# Filter 逻辑文档

> 本文件是 filter_service.py 过滤规则的说明文档。每次修改 filter 逻辑请同步更新本文件。

---

## 过滤流程（9步）

```
filter_one(detail, keyword)
│
├─ 1. 时间校验
│     published_at > 5天 → 淘汰
│
├─ 2. 地域检查
│     深圳关键词 → 用 REGION_KEYWORDS_SZ
│     汕尾关键词 → 用 REGION_KEYWORDS
│     无地域词 → 淘汰
│
├─ 3. 强拒绝关键词（STRONG_REJECT_KEYWORDS）
│     命中的任意一个 → 直接淘汰
│     当前列表：旅游搭子/找搭子/包车/地陪/带车司机/配司机/驾驶员
│
├─ 4. 商家账号检测（MERCHANT_AUTHOR_KEYWORDS）
│     author 名含商家词 → 淘汰
│     当前列表：民宿/酒店/餐厅/包车/导游/旅行社/工作室/...
│
├─ 5. 纯攻略/分享贴检测（_is_share_post_only）
│     a. 标题以「没有攻略」「无攻略」「没攻略」开头 → 淘汰
│     b. 有求助信号（ask/帮我/求） → 不淘汰
│     c. HOTEL_PRAISE_KEYWORDS / TEAM_BUILD_KEYWORDS → 淘汰
│     d. _is_recommendation_format 标题格式 → 淘汰
│     e. SHARE_POST_KEYWORDS 命中 ≥2 → 淘汰（无求助信号时）
│
├─ 6. 纯交通类检测（_is_transport_only）
│     只含交通关键词且无游玩/餐饮信号 → 淘汰
│
├─ 7. 广告文案（REJECT_PATTERNS 正则）
│     匹配任意正则 → 淘汰
│     当前：旗舰店/专卖店/限时/秒杀/保姆级/不踩坑 + 包车格式
│     包车格式：车型[：:]/随停随走/人数1-7/全程[一三两五八]小时
│
├─ 8. 正向信号通过（_get_pass_reasons）
│     无正向信号 → 淘汰
│     有正向信号 → 通过，记录原因
│
└─ 9. 分类（classify_types）
      通过的笔记归类：美食推荐/住宿推荐/行程规划/景点推荐
```

---

## 通过条件

笔记必须同时满足：
1. 时间在 5 天内
2. 地域含汕尾（或深圳）关键词
3. 无强拒绝词/商家账号/纯分享/交通/广告
4. 有正向信号（ask / type_match）

---

## 问题笔记记录（problem_notes.json）

| note_id | 标题/摘要 | expected | 原因 | 修复版本 |
|---------|---------|----------|------|---------|
| 69ef1538 | 沉浸式做汕尾这款家宝藏美食 | false |家宝藏语气纯分享 | 已修复 |
| 69ef89c2 | 五月二去汕尾有什么推荐住宿 | true | content_has_ask漏识别 | a3702d9 |
| 69f1ebee | 汕尾包车，7座商务车 | false | 商家广告STRONG_REJECT加包车 | filter_service.py |
| 69f1fe1a | 记录二人一狗在汕尾没有攻略 | false | 标题否定语气漏检 | SHARE_POST_KEYWORDS |

---

## 地域词配置

**REGION_KEYWORDS（汕尾）**：
`汕尾`、`红海湾`、`金町湾`、`海丰`、`陆丰`、`遮浪`、`马宫`、`长沙湾`、`捷胜`、`陶河`、`赤坑`、`公平`、`可塘`、`平东`、`河口`、`新田`、`甲西`、`湖东`、`甲子`、`碣石`、`南塘`、`湖东`、`大安`、`八万`、`陂洋`、`博美`、`城东`、`东海`、`河西`、`潭西`、`星都`、`上英`、`潭西`...

**REGION_KEYWORDS_SZ（深圳）**：
`深圳`、`天文台`、`南武当`、`梧桐山`、`大鹏`、`较场尾`、`东门`、`世界之窗`、`深圳湾`、`东部华侨城`、`中英街`、`莲花山`

---

## 测试脚本

```bash
python _check_notes.py
```

测试用例：`test/corpus/problem_notes.json`

每次修改 filter 逻辑后：
1. 运行 `_check_notes.py` 确认全部通过
2. 确认新发现问题已追加到 `problem_notes.json`
3. 同步更新本文件的「问题笔记记录」表格