# -*- coding: utf-8 -*-
"""
从用户已登录的 Chrome 浏览器通过 CDP 导出 cookie，
绕过 Playwright 扫码后 auth token 不完整的问题。
"""
import sys, os, io
sys.path.insert(0, ".")
os.chdir(r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import json
from pathlib import Path
import subprocess

cookie_dst = Path(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json")

# 用 Chrome CDP 导出 cookie
# 关闭 Chrome 实例才能导出，否则被锁定
print("请确保 Chrome 已关闭（所有标签页）")
print("按 Enter 继续，或 Ctrl+C 退出...")

input()

# 找到 Chrome 用户数据目录
chrome_user_data = Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data"

# 使用 chrome-cookies-extractor 或直接用 psutil 读内存
# 这里用简化的方式：复制 Local State 再用 Python 解析
local_state_file = chrome_user_data / "Local State"
if not local_state_file.exists():
    print(f"Local State 不存在: {local_state_file}")
    sys.exit(1)

# 尝试直接用 chrome 插件方式
# 最简单：启动带 remote-debugging-port 的 chrome，手动访问小红书，等用户刷新，再导出
print(f"\n启动 Chrome 并开启调试端口 9222...")
print("请在浏览器中访问 https://www.xiaohongshu.com 并确保已登录")
print("然后按 Enter...")

proc = subprocess.Popen([
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "--remote-debugging-port=9222",
    "--user-data-dir=" + str(chrome_user_data),
    "--no-first-run",
    "--no-default-browser-check",
], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

try:
    input()
finally:
    proc.terminate()
    proc.wait()

# 从 CDP 获取 cookie
import urllib.request
try:
    with urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=5) as r:
        version_info = json.loads(r.read())
        print(f"CDP WebSocket URL: {version_info.get('webSocketDebuggerUrl')}")
except Exception as e:
    print(f"无法连接 CDP: {e}")
    sys.exit(1)
