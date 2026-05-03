import subprocess, sys
result = subprocess.run([sys.executable, "-c", "print('hello from subprocess')"],
    capture_output=True, text=True, timeout=10)
print("stdout:", result.stdout)
print("stderr:", result.stderr[:200] if result.stderr else "")