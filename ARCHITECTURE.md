# xhs-auto-traffic-v2 架构文档

## 1. 系统概述

小红书截流工具 v2，全量重构版本。采用 Playwright 替代 opencli，全流程浏览器控制，一套 cookie 统一管理。

## 2. 架构图

```
┌──────────────────────────────────────────────────────────────┐
│                          main.py                            │
│               唯一入口，按 stage 分发任务                     │
└──────────────┬─────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                  BrowserManager                             │
│  · 启动 Chromium（headless / headed）                       │
│  · 加载 xhs_cookies.json                                   │
│  · is_logged_in() 检测登录态                               │
│  · 进程清理（只杀 Playwright 进程，不影响用户浏览器）         │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                  SearchCollector                            │
│  · goto 搜索结果页（最新 + 一周内筛选）                     │
│  · ScrollHelper: 滚动加载笔记列表                           │
│  · 提取: url, xsec_token, author, time_text                │
│  · 采集层轻过滤: 时间门槛(≥5天跳过) + 去重(7天)             │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│               NoteDetailCollector                           │
│  · 逐条打开笔记详情页                                      │
│  · 提取: 正文, 图片列表, 标签, 点赞/收藏/评论, 时间          │
│  · 重试: 最多 3 次                                         │
│  · 降级: enrichment 失败 → 保留搜索页数据，不丢弃          │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                    FilterService                             │
│  · enrichment 后执行                                       │
│  · 基础过滤: 时间二次校验, 空内容过滤                       │
│  · 业务过滤:                                               │
│    - 地域 (汕尾/红海湾/金町湾/海丰/陆丰)                    │
│    - 商家账号淘汰 (民宿/酒店/餐厅/导游/旅行社)               │
│    - 分享/攻略/探店贴淘汰                                  │
│    - 交通意图淘汰                                          │
│    - 广告文案淘汰                                          │
│    - 搭子淘汰                                              │
│    - 弱意向淘汰 (仅有想去/好想去/打算)                      │
│    - 正向信号通过 (求/推荐/哪里好/怎么玩/帮我/问句)         │
│  · 分类: 美食推荐/住宿推荐/行程规划/景点推荐               │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                 FeishuOutputService                          │
│  · 封装 write_feishu.py 底层逻辑                           │
│  · NoteDetail → Bitable 字段映射                            │
│  · 批量写入 + 异常重试                                      │
│  · 输出: filtered_for_feishu.jsonl                          │
└──────────────────────────────────────────────────────────────┘
```

## 3. 两段式过滤设计

```
搜索列表页
    ↓
[采集层] 时间过滤 (>5天跳过) + 去重 (7天内已采过跳过)
    ↓ enrichment
[FilterService] 地域+商家+广告+分享贴+交通+搭子+弱意向+求助信号
    ↓
飞书 Bitable
```

**为什么这样设计：**
- 采集层在 enrichment 前过滤掉 60~80% 无效内容，节省网络请求
- FilterService 依赖 enrichment 后的正文做语义判断，无法前置

## 4. FilterHelper 选择器策略

XHS 过滤面板默认隐藏，hover `.filter` 后才出现，无法用 Playwright locator 点击隐藏元素。

**最终方案（不改）：**
```python
page.hover(".filter")
time.sleep(0.5)

targets = page.evaluate("""
var panel = document.querySelector('.filter .filter-panel');
var all = panel.querySelectorAll('*');
for (var i = 0; i < all.length; i++) {
    var el = all[i];
    if (el.textContent.trim() === '最新') {
        return { x: rect.x + rect.width/2, y: rect.top + rect.height/2 };
    }
}
""")

page.mouse.click(x, y)  # 坐标点击
```

## 5. 目录结构

```
xhs-auto-traffic-v2/
├── main.py                    # 唯一入口
├── config.py                 # 全局配置常量
├── README.md                 # 项目说明
├── ARCHITECTURE.md           # 本文档
├── /core
│   ├── __init__.py
│   ├── browser_manager.py     # 浏览器生命周期
│   ├── search_collector.py  # 搜索采集
│   ├── note_detail.py        # 笔记详情采集
│   └── scroll_helper.py      # 滚动辅助
├── /filter
│   ├── __init__.py
│   ├── filter_service.py     # 两段式过滤
│   └── classifier.py         # 类型分类
├── /output
│   ├── __init__.py
│   └── feishu_service.py     # 飞书写入
└── /utils
    ├── __init__.py
    ├── parse.py              # 时间解析
    ├── text.py              # 文本工具
    └── storage.py           # 去重存储
```

## 6. 数据结构

### FeedNote（搜索列表页提取）
```python
url: str           # 搜索结果 URL
xsec_token: str    # 从 URL 参数提取
author: str        # .name-time-wrapper .name
time_text: str     # .name-time-wrapper .time（格式："2小时前"/"昨天 23:17"）
title: str         # 可选，筛选后可能为空
```

### NoteDetail（enrichment 结果）
```python
url: str
xsec_token: str
author: str
time_text: str
content: str        # #detail-desc textContent
images: list[str]   # 正文图片 URL 列表
tags: list[str]     # a.tag 文本列表
likes: int
collects: int
comments: int
published_at: str   # YYYY-MM-DD 格式
author_id: str
```

## 7. 关键常量

| 常量 | 值 | 说明 |
|------|----|------|
| `TIME_THRESHOLD_DAYS` | 5 | 采集层时间过滤阈值（天） |
| `RECENT_DAYS` | 7 | 去重时间窗口 |
| `ENRICHMENT_MAX_RETRIES` | 3 | 单条笔记 enrichment 重试次数 |
| `DEFAULT_SCROLL_COUNT` | 8 | 默认滚动次数（约 35+ 条） |
| `COOKIE_FILE` | `xhs_cookies.json` | Cookie 存储路径 |

## 8. 开发规范

- 分支: `main` / `dev` / `feature/xxx` / `bugfix/xxx`
- 提交: `feat:` / `fix:` / `refactor:` / `docs:` / `test:`
- 迭代: 1 天 1 个可运行版本，不允许半成品合并到 main
- 所有功能必须能独立运行，不影响其他模块
- 有异常捕获，可回滚

## 9. Day 1 ~ Day 7 任务

| Day | 任务 |
|-----|------|
| Day 1 | 项目骨架 + BrowserManager + 配置 + 工具类 |
| Day 2 | SearchCollector + ScrollHelper + 采集层轻过滤 |
| Day 3 | NoteDetailCollector + 正文/图片/标签/降级 |
| Day 4 | FilterService 完整迁移（地域+商家+广告+分类） |
| Day 5 | FeishuOutputService + 全流程串联 |
| Day 6 | 全流程联调 + 稳定性（重试/超时/崩溃防护） |
| Day 7 | main 分支稳定版 + 一键运行验证 |

## 10. 遗留兼容

- `parse_published_at()`: 原 collect.py，逻辑不变
- `filter_note()` / `classify_type()`: 原 filter.py，1:1 迁移
- `write_feishu.py`: 底层逻辑不动，只做 FeishuOutputService 封装
- `RecentStorage`: 原 recent_collector.py，复用 `data/collected_note_ids.jsonl`
