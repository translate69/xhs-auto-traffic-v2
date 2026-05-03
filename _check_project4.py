"""Check review_service rules - write to file"""
import os

proj = r'E:\translate\claw\xhs-auto-traffic-v2'
with open(os.path.join(proj, 'filter/review_service.py'), encoding='utf-8') as f:
    content = f.read()

with open(os.path.join(proj, '_review_check.txt'), 'w', encoding='utf-8') as f:
    f.write('=== MERCHANT_AUTHOR_KEYWORDS ===\n')
    idx = content.find('MERCHANT_AUTHOR_KEYWORDS')
    f.write(content[idx:idx+600] + '\n\n')
    f.write('=== SHARE_POST_KEYWORDS ===\n')
    idx2 = content.find('SHARE_POST_KEYWORDS')
    f.write(content[idx2:idx2+600] + '\n\n')
    f.write('=== Review flow in _review_one ===\n')
    idx3 = content.find('def _review_one')
    f.write(content[idx3:idx3+2000] + '\n\n')
    f.write('=== _is_merchant_author ===\n')
    idx4 = content.find('def _is_merchant_author')
    f.write(content[idx4:idx4+300] + '\n\n')
    f.write('=== _is_recommendation_format ===\n')
    idx5 = content.find('def _is_recommendation_format')
    f.write(content[idx5:idx5+500] + '\n')

print('Written to _review_check.txt')