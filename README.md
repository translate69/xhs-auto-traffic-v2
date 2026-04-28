# xhs-auto-traffic-v2

小红书截流工具 v2，全量重构版本。

## 架构概述

```
┌─────────────────────────────────────────────────────────┐
│                     main.py                              │
│              (唯一入口，调度全流程)                        │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────┐
│              BrowserManager                               │
│  · 初始化 Chromium (headless/headed)                    │
│  · Cookie 加载 / 保存                                    │
│  · is_logged_in() 登录态检测                            │
│  · 进程清理（只杀 Playwright 自己的进程）                │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────┐
│            SearchCollector                               │
│  · goto 搜索结果页                                       │
│  · FilterHelper: hover .filter → 面板内文字匹配 → 坐标点击│
│  · ScrollHelper: 滚动加载笔记列表                        │
│  · 提取: url, xsec_token, author, time_text            │
│  · 采集层轻过滤: 时间门槛 + 去重                         │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────┐
│          NoteDetailCollector                             │
│  · 打开笔记详情页                                        │
│  · 提取: 正文, 图片列表, 标签, 点赞/收藏/评论数, 时间     │
│  · 降级策略: 失败 → 保留搜索页已有数据，不丢弃           │
│  · 重试: 最多 3 次                                       │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────┐
│            FilterService                                 │
│  · enrichment 后二次处理                                 │
│  · 基础过滤: 时间校验, 空内容过滤                        │
│  · 业务过滤:                                            │
│    - 地域过滤 (汕尾/红海湾/金町湾/海丰/陆丰)             │
│    - 商家账号淘汰 (民宿/酒店/餐厅/导游/旅行社)            │
│    - 分享/攻略/探店贴淘汰                               │
│    - 交通意图淘汰                                       │
│    - 广告文案淘汰                                       │
│    - 搭子淘汰                                          │
│    - 弱意向淘汰 (仅有想去/好想去)                        │
│    - 正向信号通过 (求/推荐/哪里好/怎么玩/帮我/问句)      │
│  · classify_type: 美食推荐/住宿推荐/行程规划/景点推荐    │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────┐
│           FeishuOutputService                            │
│  · 封装 write_feishu.py 底层逻辑                        │
│  · 标准化笔记结构体 → Bitable 字段映射                   │
│  · 批量写入 + 异常重试                                   │
└──────────────────────────────────────────────────────────┘
```

## 两段式过滤（核心设计）

```
搜索列表页
    ↓
[采集层] 时间过滤 (≥5天跳过) + 去重 (7天内已采过跳过)
    ↓ enrichment (Playwright 访问详情页)
[FilterService] 地域/商家/广告/分享贴/交通/搭子/弱意向/求助信号/分类
    ↓
飞书 Bitable
```

**为什么这样设计：**
- 采集层在 enrichment 前过滤掉 60~80% 无效内容，节省网络请求和解析时间
- FilterService 依赖 enrichment 后的正文内容做语义判断，无法前置

## FilterHelper 选择器策略（最稳定方案）

XHS 过滤面板默认隐藏，只有 hover `.filter` 后才显示，无法用 Playwright locator 直接点击隐藏元素。

**最终方案（不改）：**
```python
page.hover(".filter")           # 触发面板显示
time.sleep(0.5)

# 在 .filter .filter-panel 内扫描所有子元素
targets = page.evaluate("""
var panel = document.querySelector('.filter .filter-panel');
var all = panel.querySelectorAll('*');
for (el in all) {
    if (el.textContent.trim() === '最新') {
        return { x, y };  // getBoundingClientRect 中心坐标
    }
}
""")

page.mouse.click(x, y)           # 模拟鼠标点击
```

这是目前对抗 XHS 最稳的方案，比 locator/JS evaluate/CDP 都更可靠。

## 目录结构

```
xhs-auto-traffic-v2/
├── main.py                    # 唯一入口
├── config.py                  # 全局配置
├── ARCHITECTURE.md             # 本文档
├── /core
│   ├── browser_manager.py     # 浏览器生命周期
│   ├── search_collector.py    # 搜索采集
│   ├── note_detail.py         # 笔记详情采集
│   └── scroll_helper.py       # 滚动辅助
├── /filter
│   ├── filter_service.py      # 两段式过滤
│   └── classifier.py          # 类型分类
├── /output
│   └── feishu_service.py      # 飞书写入
└── /utils
    ├── parse.py               # 时间解析
    ├── text.py                # 文本工具
    └── storage.py             # 去重存储
```

## 使用方式

```bash
# 完整流程
python main.py --keyword 汕尾美食 --limit 50

# 分阶段
python main.py --stage collect --keyword 汕尾美食 --limit 30
python main.py --stage filter
python main.py --stage feishu
```

## 关键常量

| 常量 | 值 | 说明 |
|------|----|------|
| `TIME_THRESHOLD_DAYS` | 5 | 采集层时间过滤阈值 |
| `RECENT_DAYS` | 7 | 去重时间窗口 |
| `ENRICHMENT_MAX_RETRIES` | 3 | 单条笔记 enrichment 重试次数 |
| `SCROLL_COUNT` | 8 | 默认滚动次数（约 35+ 条） |
| `COOKIE_FILE` | `xhs_cookies.json` | Cookie 存储路径 |

## 开发规范

- 分支: `main` / `dev` / `feature/xxx` / `bugfix/xxx`
- 提交: `feat:` / `fix:` / `refactor:` / `docs:` / `test:`
- 迭代: 1 天 1 个可运行版本，不允许半成品合并
- 所有功能必须能独立运行，不影响其他模块
- 有异常捕获，可回滚

## 遗留兼容

- `parse_published_at()` 来自原 `collect.py`，逻辑不变
- `filter_note()` / `classify_type()` 来自原 `filter.py`，1:1 迁移
- `write_feishu.py` 底层逻辑不动，只做封装
- `RecentCollector` 来自原 `recent_collector.py`，复用存储文件格式
