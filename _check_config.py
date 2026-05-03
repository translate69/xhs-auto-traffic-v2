import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import config
print(f"HEADLESS: {config.HEADLESS}")
print(f"BROWSER_ARGS: {config.BROWSER_ARGS}")
print(f"VIEWPORT: {config.VIEWPORT}")
