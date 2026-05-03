"""Test range | union"""
import sys
print(sys.version)
try:
    r = range(0x4E00, 0x9FFF + 1) | range(0x3400, 0x4DBF + 1)
    print("OK:", type(r), r)
except Exception as e:
    print("FAIL:", e)
    # Fix
    r = set(range(0x4E00, 0x9FFF + 1)) | set(range(0x3400, 0x4DBF + 1))
    print("Fixed with set:", type(r), len(r))