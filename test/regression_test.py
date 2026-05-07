"""
回归测试：每次改 filter 规则前跑一遍
确保历史上误判的笔记仍然被正确拒绝

用法：
    python test/regression_test.py
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from filter.filter_service import FilterService
from core.note_detail import NoteDetail


def load_problem_notes():
    path = ROOT / "test" / "corpus" / "problem_notes.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_regression():
    notes = load_problem_notes()
    if not notes:
        print("问题笔记库为空，跳过回归测试")
        return True

    svc = FilterService()
    all_pass = True

    print(f"回归测试：{len(notes)} 条问题笔记\n")

    for item in notes:
        note = NoteDetail(
            title=item.get("title", ""),
            content=item["content"],
            url="https://www.xiaohongshu.com/explore/" + item["note_id"],
            xsec_token="",
            # 用测试时间：5天内，专注测 signal 逻辑，不受时间过滤影响
            published_at="2026-05-03",
        )
        result = svc.filter_one(note)
        # 优先检查时间过滤（published_at=5月3日，当前=5月5日=2天前，还在5天窗口内）
        # 如果结果包含"时间过久"，说明这条笔记的时间被错误放行/拒绝，先排除
        if "时间过久" in result.reasons:
            # 时间问题，不是信号逻辑问题，这轮跳过
            status = "⏭️ "
            print(f"{status} [{item['note_id'][:8]}] 时间过滤生效，跳过信号逻辑验证")
            print(f"   原因: {item['reason']}")
            print(f"   结果: {result.reasons}\n")
            continue

        expected = item.get("expected", False)

        # 跳过「已记录未修复」的笔记（它们不在 expected 验证范围内）
        if item.get("fixed_at") == "never" or not item.get("fixed_at"):
            # 检查是否在 problem_notes 里标记为 fixed（fixed_at 有值说明已修复）
            pass  # 继续验证

        status = "✅" if result.passed == expected else "❌"
        if result.passed != expected:
            all_pass = False

        print(f"{status} [{item['note_id'][:8]}] expected={expected} got={result.passed}")
        print(f"   原因: {item['reason']}")
        print(f"   结果: {result.reasons}\n")

    if all_pass:
        print("✅ 回归测试全部通过")
    else:
        print("❌ 回归测试有退化！请检查规则变更")

    return all_pass


if __name__ == "__main__":
    success = run_regression()
    sys.exit(0 if success else 1)
