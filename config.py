"""
全局配置 - config.py
所有常量集中管理，方便一处修改全局生效。
"""
from pathlib import Path

# ─── 项目路径 ──────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
COOKIE_FILE = PROJECT_ROOT / "xhs_cookies.json"

# ─── 浏览器配置 ────────────────────────────────────────────

# 生产环境 headless，调试环境 headed
HEADLESS = False  # 调试模式，浏览器窗口可见

# Playwright Chromium 启动参数（反检测）
BROWSER_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",  # 去掉 webdriver 特征
    "--disable-blink-features=IsolateOrigins,AutomationReloaded",  # 额外防护
    "--no-first-run",
    "--no-default-browser-check",
]

# 伪装真实浏览器 UA（XHS 会检测 UA）
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# 视口
VIEWPORT = {"width": 1280, "height": 900}

# 页面加载超时（秒）
PAGE_LOAD_TIMEOUT = 30000

# ─── 采集配置 ──────────────────────────────────────────────

# 默认每关键词采集数量
DEFAULT_LIMIT = 30

# 滚动次数（8 次滚动约 35 条笔记）
DEFAULT_SCROLL_COUNT = 8

# 滚动间隔（秒）
SCROLL_PAUSE = 1.0

# ─── 时间过滤 ──────────────────────────────────────────────

# 采集层时间过滤阈值（天）
TIME_THRESHOLD_DAYS = 5

# 去重时间窗口（天）
RECENT_DAYS = 7

# ─── 重试配置 ──────────────────────────────────────────────

# enrichment 单条最大重试次数
ENRICHMENT_MAX_RETRIES = 3

# enrichment 网络错误重试间隔（秒）
ENRICHMENT_RETRY_DELAY = 15

# enrichment 安全风控重试间隔（秒）
ENRICHMENT_SECURITY_DELAY = 20

# 采集节奏
PAUSE_BETWEEN_NOTES = (3, 5)
PAUSE_DURATION = 15  # 每 N 条暂停风控保护

# ─── 输出配置 ──────────────────────────────────────────────

# JSONL 数据输出目录
JSONL_DIR = DATA_DIR

# ─── 飞书 Bitable 配置（v2 专用表）───────────────────────────
# App Token: MtpRbyHq9aOP3csA3jVc6CYenuc
# Table ID: tblvxlFAqO5hP4fD（从飞书 URL 解析）
# 凭证: secrets.json 或环境变量 FEISHU_APP_ID / FEISHU_APP_SECRET
FEISHU_APP_TOKEN = "MtpRbyHq9aOP3csA3jVc6CYenuc"
FEISHU_TABLE_ID = "tbl3cmXBcrQfXa2D"  # 生产环境

# 飞书输出目录（JSONL 文件）
FEISHU_DIR = DATA_DIR / "feishu"

# ─── 日志配置 ──────────────────────────────────────────────

LOG_DIR = PROJECT_ROOT / "logs"
LOG_LEVEL = "INFO"