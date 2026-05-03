# -*- coding: utf-8 -*-
import sys; sys.path.insert(0, ".")
from core.search_collector import SearchCollector
import inspect

# 检查类初始化参数
print("SearchCollector.__init__ signature:")
print(inspect.signature(SearchCollector.__init__))

# 检查 collect 方法
print("\nSearchCollector.collect signature:")
print(inspect.signature(SearchCollector.collect))
