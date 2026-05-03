"""Find the exact bytes of '信号后否定检查' and replace them"""
with open(r'E:\translate\claw\xhs-auto-traffic-v2\filter\filter_service.py', 'rb') as f:
    raw = f.read()

# Find the signal check comment
keyword = '信号后否定检查'.encode('utf-8')
pos = raw.find(keyword)
print(f"Found at byte {pos}")
if pos >= 0:
    print("Context (hex):", raw[pos-5:pos+50].hex())
    print("Context (utf8):", raw[pos-5:pos+50].decode('utf-8', errors='replace'))
    
# Find the "无否定词，命中" comment
keyword2 = '无否定词'.encode('utf-8')
pos2 = raw.find(keyword2)
print(f"'无否定词' at byte {pos2}")

# Find the full block from signal check to return True
# We want to find "return True\n    return False" at end of file
keyword3 = b'return True\r\n    return False'
pos3 = raw.rfind(keyword3)
print(f"'return True...return False' at byte {pos3}")
print("Context:", raw[pos3-50:pos3+30].hex())
print("Decoded:", raw[pos3-50:pos3+30].decode('utf-8', errors='replace'))