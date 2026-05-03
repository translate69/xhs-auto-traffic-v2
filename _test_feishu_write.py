import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from utils.feishu_client import batch_write, load_existing_note_ids

# Test token fetch
print("=== Token test ===")
ids = load_existing_note_ids()
print(f"load_existing_note_ids: {len(ids)} records")
print(f"Token OK: {len(ids) > 0}")

# Try writing a dummy record
print("\n=== Write test ===")
test_row = {
    "title": "测试写入",
    "note_url": "https://www.xiaohongshu.com/explore/test123",
    "note_id": "test999999999",
    "content": "这是测试内容",
    "author": "测试作者",
}
ok = batch_write(test_row)
print(f"Write result: {ok}")
