import subprocess, sys, os

env = dict(os.environ)
env['PYTHONIOENCODING'] = 'utf-8'
env['PYTHONPATH'] = r'E:\translate\claw\xhs-auto-traffic-v2'

result = subprocess.run(
    [sys.executable, r'E:\translate\claw\xhs-auto-traffic-v2\run_all.py',
     '--keyword', '汕尾海边民宿推荐',
     '--limit', '10',
     '--debug'],
    env=env,
    text=True,
    encoding='utf-8',
    errors='replace',
    cwd=r'E:\translate\claw\xhs-auto-traffic-v2'
)
print(result.stdout[:3000] if result.stdout else '')
print(result.stderr[:1000] if result.stderr else '')
print('RC:', result.returncode)