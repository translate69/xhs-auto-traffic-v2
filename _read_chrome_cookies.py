# -*- coding: utf-8 -*-
import sys, os, io, subprocess
sys.path.insert(0, ".")
os.chdir(r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from pathlib import Path
import sqlite3, shutil, json

user_data_dir = os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data")
cookie_db = Path(user_data_dir) / "Default" / "Cookies"
cookie_dst = Path(r"E:\translate\claw\xhs-auto-traffic-v2\xhs_cookies.json")

print(f"Cookie DB: {cookie_db}")
print(f"存在: {cookie_db.exists()}")

if cookie_db.exists():
    temp_db = Path("temp_cookies.db")
    shutil.copy2(str(cookie_db), str(temp_db))
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT host, name, value, path, expires_utc, is_secure FROM cookies "
        "WHERE host LIKE '%xiaohongshu%' OR host LIKE '%xhs%'"
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
    print(f"✅ 保存到: {cookie_dst} ({len(cookies)} 条)")
else:
    print("❌ 数据库不存在")
