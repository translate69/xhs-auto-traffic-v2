# -*- coding: utf-8 -*-
from load_keywords import load_keywords
all_kw = load_keywords()
print(f"共 {len(all_kw)} 个关键词:")
for kw in all_kw:
    print(f"  [{kw['group']}] {kw['keyword']}")