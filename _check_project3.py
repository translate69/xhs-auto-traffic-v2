"""Check key merchant/share rules in review_service"""
import os

proj = r'E:\translate\claw\xhs-auto-traffic-v2'

with open(os.path.join(proj, 'filter/review_service.py'), encoding='utf-8') as f:
    content = f.read()

print('=== MERCHANT_AUTHOR_KEYWORDS ===')
start = content.find('MERCHANT_AUTHOR_KEYWORDS')
print(content[start:start+500])

print('\n=== SHARE_POST_KEYWORDS ===')
start2 = content.find('SHARE_POST_KEYWORDS')
print(content[start2:start2+500])