import sys
sys.path.insert(0, '.')
import config
for attr in dir(config):
    if "FEISHU" in attr.upper() or "BITABLE" in attr.upper() or "APP" in attr.upper():
        print(f"{attr} = {getattr(config, attr)}")
