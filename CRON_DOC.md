# Cron 运行文档

> 本文档记录 xhs-auto-traffic-v2 的定时任务配置、运行情况及已知问题。

---

## 1. 定时任务配置

### 1.1 Cron 配置

```json
{
  "schedule": { "kind": "cron", "expr": "0 6,12,18 * * *", "tz": "Asia/Shanghai" },
  "payload": { "kind": "agentTurn", "message": "..." },
  "sessionTarget": "isolated"
}
```

含义：每天 **6:00 / 12:00 / 18:00**（上海时区）各跑一次

### 1.2 触发命令

```bash
python run_batch.py --limit 50 --timeout 600 --restart-browser-every 3
```

- `--limit 50`：每个关键词采集 50 条
- `--timeout 600`：单个关键词超时 600 秒
- `--restart-browser-every 3`：**每 3 个关键词重启一次浏览器**（见 3.2 节）

### 1.3 关键词列表

| 关键词 | 分组 | 说明 |
|---|---|---|
| 汕尾美食 | core | 主词 |
| 汕尾住宿推荐 | core | 主词 |
| 汕尾美食推荐 | core | 主词 |
| 汕尾游玩 | core | 主词 |
| 汕尾酒店 | core | 主词 |
| 汕尾攻略 | core | 主词 |
| 汕尾美食 | core | 主词 |
| 深圳到汕尾自驾住哪 | longtail | 长尾 |
| 深圳到汕尾旅游攻略 | longtail | 长尾 |
| ...（共 17 个关键词） | | |

---

## 2. Pipeline 流程

```
run_batch.py
  └── BrowserManager（启动 Playwright Chromium，headless）
        │
        ├── SearchCollector.collect(keyword, limit)
        │     └── 输出：list[FeedCard]（搜索结果列表）
        │
        ├── NoteDetailCollector.enrich_all(feeds)
        │     └── 输出：list[NoteDetail]（含 content/content）
        │
        ├── FilterService.filter_one()  × N
        │     ├── 地域过滤（汕尾关键词）
        │     ├── 商家账号过滤
        │     ├── 纯分享/攻略贴过滤
        │     ├── 弱意向 + ask信号过滤
        │     ├── _get_pass_reasons（严格路径）
        │     └── 输出：通过的 NoteDetail 列表
        │
        ├── ReviewService.review()  × N（强制 gate）
        │     ├── 规则1：reasons 为空 → 拒绝
        │     ├── 规则2：商家账号 → 拒绝
        │     ├── 规则3：纯分享帖 → 拒绝
        │     └── 输出：通过的 NoteDetail 列表
        │
        └── FeishuOutputService.write()
              ├── reviewed_for_feishu.jsonl（中间文件）
              └── Feishu Bitable（最终写入）
```

**双层 Gate 保障**：FilterService + ReviewService，任何一层拒绝都不会写入飞书。

---

## 3. 已知问题与解决方案

### 3.1 SIGKILL（浏览器进程被 kill）

**现象**：
- enrichment 阶段浏览器进程被系统强制终止
- 日志：`Exec failed (session xxx, signal SIGKILL)`

**根因**：
1. 内存累积：每条笔记新建 `page`（context 不关闭），内存峰值持续上升
2. 页面加载超时（`detail-desc` 15s 内无法访问）→ 重试3次仍失败 → 系统 OOM

**解决方案**：方案 A — 每 N 个关键词重启浏览器（已实现）

```bash
python run_batch.py --restart-browser-every 3
# 每跑完 3 个关键词后自动重启浏览器（context + browser 全部关闭）
# 用户打开的浏览器不受影响（见 3.3 节）
```

### 3.2 浏览器重启是否影响用户浏览器？

**不影响。** 原因：

```
BrowserManager.__enter__() 启动流程：
  1. _get_chrome_pids() 记录「当前所有 chrome.exe PIDs」
  2. launch() 启动 Playwright Chromium（独立的 chrome.exe 进程）
  3. _playwright_pids = after_pids - before_pids
     → 只有 Playwright 启动的新 PIDs 被记录
  4. __exit__ 时，只杀 _playwright_pids（不碰用户浏览器 PIDs）
```

**用户浏览器**：通过 Chrome 官方 UI 打开，父进程是 `chrome.exe`，**不在 `_playwright_pids` 集合中**。
**Playwright 浏览器**：由 `playwright.chromium.launch()` 启动，**在 `_playwright_pids` 集合中**。

两者进程隔离，`taskkill /F /PID <playwright_pid>` 不会影响用户浏览器。

### 3.3 日志堆积

`logs/` 目录每次运行产生一个日志文件（目前已 153 个）。

**建议**：每月 1 日凌晨手动清理，或加一个 cron 任务：

```python
# 清理 30 天前的日志
from pathlib import Path
import time
log_dir = Path("logs/")
cutoff = time.time() - 30 * 86400
for f in log_dir.glob("*.log"):
    if f.stat().st_mtime < cutoff:
        f.unlink()
```

---

## 4. 观察记录

| 日期 | 运行情况 | 通过数 | 问题 |
|---|---|---|---|
| 2026-05-03 | 首次 cron 跑 pipeline 测试 | — | SIGKILL（内存） |
| 2026-05-03 | 修复 run_batch.py + 添加 restart-browser-every | 待观察 | — |

---

## 5. 安全机制

| 机制 | 说明 |
|---|---|
| **幂等写入** | `batch_write` 先查 `load_existing_note_ids()`，已存在的 note_id 跳过 |
| **双层 Gate** | FilterService + ReviewService，任何一层拒绝则不写入 |
| **超时保护** | 每个关键词 600s timer，超时后 `context.close()` 继续下一个 |
| **浏览器进程隔离** | `_playwright_pids` 只记录 Playwright 自己的进程，不杀用户浏览器 |
| **时间过滤** | `TIME_THRESHOLD_DAYS = 5`，超过 5 天的笔记直接淘汰 |
| **自动重启** | `--restart-browser-every 3` 定期释放内存，避免 OOM |

---

## 6. cron 设置命令

```python
cron(action="add", job={
  "name": "xhs-auto-traffic-v2 采集",
  "schedule": {"kind": "cron", "expr": "0 6,12,18 * * *", "tz": "Asia/Shanghai"},
  "payload": {
    "kind": "agentTurn",
    "message": "python run_batch.py --limit 50 --timeout 600 --restart-browser-every 3 --group core && python run_batch.py --limit 50 --timeout 600 --restart-browser-every 3 --group longtail",
    "timeoutSeconds": 3600
  },
  "sessionTarget": "isolated",
  "delivery": {"mode": "announce"}
})
```

> 注意：`--group core` 和 `--group longtail` 分两次跑，避免单次超时。`--restart-browser-every 3` 每 3 个关键词重启一次，建议值 3-5。
