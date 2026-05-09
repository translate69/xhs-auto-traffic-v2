# Filter 开发流程

> 上次更新：2026-05-06

## 核心原则

**每一条因为特定笔记问题而修改 filter 逻辑的改动，必须同时把该笔记加入 `test/corpus/problem_notes.json`。**

这是强制要求，不是可选项。没有 `problem_notes` 记录的 filter 修改不允许 commit。

---

## 标准流程

### Step 0 - 发现问题
在日志、回归测试或人工审查中发现某条笔记的过滤结果不符合预期。

### Step 1 - 记录到 problem_notes（先于任何代码修改）
在 `test/corpus/problem_notes.json` 中添加一条记录：

```json
{
  "note_id": "笔记ID",
  "title": "标题",
  "content": "正文内容",
  "author": "作者（如果有）",
  "keyword": "触发该笔记的搜索关键词（如果有）",
  "expected": true 或 false,
  "reason": "问题描述，清晰说明为什么错误、哪个逻辑导致的",
  "found_at": "YYYY-MM-DD"
}
```

`expected` 含义：
- `true` = 该笔记应该通过 filter 但被误杀
- `false` = 该笔记应该被 filter 拒绝但误通过

### Step 2 - 分析根因
阅读 `filter/filter_service.py` 的相关逻辑，确认是哪个函数、哪行代码出了问题。

### Step 3 - 修改代码
修复对应逻辑。修改完后必须确保：
1. `problem_notes` 中该笔记的 `expected` 判定能被满足
2. 不破坏已有测试（运行 `python test_filter_rules.py`）

### Step 4 - 验证
运行回归测试：
```bash
cd E:\translate\claw\xhs-auto-traffic-v2
python test_filter_rules.py
```

### Step 5 - 标注 fixed_at
在 `problem_notes.json` 中补上 `fixed_at` 字段（commit hash 或修复文件名）：
```json
"fixed_at": "filter_service.py has_signal否定词检测"
```

---

## problem_notes.json 字段说明

| 字段 | 必须 | 说明 |
|------|------|------|
| `note_id` | ✅ | 笔记 ID（从 XHS URL 或 JSONL 中获取）|
| `title` | ✅ | 标题（可为空） |
| `content` | ✅ | 正文内容 |
| `author` | 推荐 | 作者名 |
| `keyword` | 推荐 | 触发该笔记的搜索关键词 |
| `expected` | ✅ | `true` = 应通过，`false` = 应拒绝 |
| `reason` | ✅ | 问题描述，包含具体哪个逻辑导致误判 |
| `found_at` | ✅ | 发现日期 `YYYY-MM-DD` |
| `fixed_at` | 推荐 | 修复日期/commit/修复方式 |

---

## 常见错误类型

| 问题类型 | 示例 | 修复方向 |
|---------|------|---------|
| 误通过（应拒绝） | 纯分享帖被放行 | 补充 EXPERIENCE_SHARE_KEYWORDS 或 REJECT_PATTERNS |
| 误杀（应通过） | 真实求助被拒绝 | 补充 ASK_SIGNALS 或修复信号检测逻辑 |
| 商家帖漏过 | 包车/陪拍广告 | 补充 STRONG_REJECT_KEYWORDS 或 MERCHANT_ACCOM_KEYWORDS |
| 否定词干扰 | "不想挤网红"被误判 | `_has_unnegated_intent()` 否定前缀检测 |

---

## 反例（违规操作）

❌ **只改代码，不加 problem_notes**
→ 禁止。后续无法回归验证。

❌ **加了好几条才想起补 problem_notes**
→ 禁止。应该先加 problem_notes，再改代码。

❌ **problem_notes 里 expected 写反**
→ 禁止。这会导致测试套件给出错误的通过/失败信号。