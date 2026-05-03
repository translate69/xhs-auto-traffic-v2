# -*- coding: utf-8 -*-
import sys, os, io, subprocess, json, shutil
sys.path.insert(0, ".")
os.chdir(r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from pathlib import Path

cookie_dst = Path(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json")
chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
user_data_dir = os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data")

print("=== 小红书 Cookie 获取器 ===")
print()
print("启动 Chrome 并打开小红书...")
proc = subprocess.Popen([
    chrome_path,
    "--new-window",
    "https://www.xiaohongshu.com",
    f"--user-data-dir={user_data_dir}",
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("Chrome 已启动，请在浏览器中扫码登录")
print("登录完成后在此窗口输入 'ok' 回车保存 cookie")
print()

# 等待用户输入
while True:
    try:
        line = input().strip()
        if line == "ok":
            break
        print("请输入 'ok' 回车以保存 cookie")
    except EOFError:
        print("stdin closed, assuming auto-save")
        break

# 关闭 Chrome
print("关闭 Chrome 以读取 cookie...")
proc.terminate()
proc.wait(timeout=10)

# 读 Chrome Cookies 数据库
cookie_db = Path(user_data_dir) / "Default" / "Cookies"
temp_db = Path("temp_cookies.db")

if not cookie_db.exists():
    print("❌ Chrome Cookie 数据库不存在")
else:
    print("读取 Cookie 数据库...")
    shutil.copy2(cookie_db, temp_db)
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT host, name, value, path, expires_utc, is_secure FROM cookies "
        "WHERE host LIKE '%xiaohongshu%' OR host LIKE '%xhs%' OR host LIKE '%.com'"
    )
    rows = cursor.fetchall()
    conn.close()
    temp_db.unlink()

    cookies = []
    for host, name, value, path, expires, secure in rows:
        cookies.append({
            "domain": host,
            "name": name,
            "value": value,
            "path": path or "/",
            "secure": bool(secure),
            "expires": -1,
            "httpOnly": False
        })

    with open(cookie_dst, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)

    print(f"✅ 已保存到: {cookie_dst}")
    print(f"   共 {len(cookies)} 条 cookie")