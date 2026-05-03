import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import config
print(f"FEISHU_APP_ID: {config.FEISHU_APP_ID}")
print(f"FEISHU_APP_SECRET: {config.FEISHU_APP_SECRET}")
print(f"FEISHU_DIR: {config.FEISHU_DIR}")
import os
secrets = open("secrets.json", encoding="utf-8").read()
print(f"secrets.json: {secrets}")
