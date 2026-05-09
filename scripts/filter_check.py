#!/usr/bin/env python3
import subprocess
import json
import os
import sys

repo = r"E:\translate\claw\xhs-auto-traffic-v2"
state_file = os.path.join(repo, ".filter_notify_last")
pending_file = os.path.join(repo, ".filter_notify_pending.json")

def git(repo, *args):
    """Run git command and return stdout as safe string."""
    try:
        result = subprocess.run(
            ["git", "-C", repo] + list(args),
            capture_output=True, encoding="utf-8", errors="replace"
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"git error: {e}", file=sys.stderr)
        return ""

latest = git(repo, "log", "--oneline", "-1", "--",
             "filter/filter_service.py", "test/corpus/problem_notes.json")
if not latest:
    sys.exit(0)

latest_hash = latest.split()[0]

if os.path.exists(state_file):
    with open(state_file, "r", encoding="utf-8") as f:
        last_hash = f.read().strip()
    if last_hash == latest_hash:
        sys.exit(0)

commit_full = git(repo, "log", "--oneline", "-1", latest_hash)
body = git(repo, "log", "--oneline", "-3", "--",
           "filter/filter_service.py", "test/corpus/problem_notes.json")
# Only get files matching filter or problem_notes
all_changed = git(repo, "diff", "--name-only", f"{latest_hash}^..{latest_hash}")
diff_files = "\n".join([f for f in all_changed.split("\n")
                          if f in ("filter/filter_service.py", "test/corpus/problem_notes.json")])

note_count = 0
if "test/corpus/problem_notes.json" in diff_files:
    diff = git(repo, "diff", f"{latest_hash}^..{latest_hash}",
               "--", "test/corpus/problem_notes.json")
    note_count = diff.count('"note_id"')

msg = f"Filter 变更自动汇报 | Commit: {commit_full} | 变更: {diff_files}"
if note_count > 0:
    msg += f" | 新增 Problem Notes: {note_count} 条"

pending = {
    "msg": msg,
    "commitHash": latest_hash,
    "commitFull": commit_full,
    "changedFiles": diff_files,
    "noteCount": note_count,
    "recentLog": body
}
with open(pending_file, "w", encoding="utf-8") as f:
    json.dump(pending, f, ensure_ascii=False, indent=2)

with open(state_file, "w", encoding="utf-8") as f:
    f.write(latest_hash)

print(f"PENDING: {commit_full}")
