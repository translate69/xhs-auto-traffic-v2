"""测 Feishu API 字段修复"""
import sys
import json
import urllib.request
import urllib.error

sys.path.insert(0, r"E:\translate\claw\xhs-auto-traffic-v2")
sys.stdout.reconfigure(encoding="utf-8")

import config
from utils.feishu_client import _get_tenant_token, _build_fields, write_single_record

token = _get_tenant_token()
print(f"Token: {token[:30]}...")

test_row = {
    "title": "测试字段修复",
    "note_url": "https://www.xiaohongshu.com/explore/test5555555555?xsec_token=TEST",
    "content": "验证时间字段是否正确",
    "author": "测试作者",
    "likes": 200,
    "collects": 100,
    "comments": 20,
    "published_at": "2026-04-28",
    "time_text": "3天前",
    "type": "美食推荐",
    "reasons": "ask",
    "keyword": "汕尾美食",
}

fields = _build_fields("test5555555555", test_row)
print(f"\n构建的 fields:\n{json.dumps(fields, ensure_ascii=False, indent=2)}")

print("\n=== 写入响应 ===")
ok = write_single_record("test5555555555", test_row)
print(f"写入结果: {'✅ 成功' if ok else '❌ 失败'}")
