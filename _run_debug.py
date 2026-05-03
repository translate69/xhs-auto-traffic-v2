"""
Debug runner: python main.py --keyword 汕尾美食 --limit 5 --debug
"""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "main.py", "--keyword", "汕尾美食", "--limit", "5", "--debug"],
    capture_output=False,
    text=True
)
print("stdout:", result.stdout)
print("stderr:", result.stderr)
print("returncode:", result.returncode)