"""Fix _get_pass_reasons: tighten type_match path"""
with open(r'E:\translate\claw\xhs-auto-traffic-v2\filter\filter_service.py', 'rb') as f:
    raw = f.read()

# Find _get_pass_reasons function
func_marker = 'def _get_pass_reasons'.encode('utf-8')
pos = raw.find(func_marker)
print(f"_get_pass_reasons at byte {pos}")

# Find the end of the function - next top-level "    def " after this
rest = raw[pos+5:]
next_func = rest.find(b'    def ')
func_end = pos + 5 + next_func if next_func > 0 else len(raw)
print(f"Function ends at byte {func_end}")

# Show the current type_match block
import re
func_bytes = raw[pos:func_end].decode('utf-8', errors='replace')
print("Current type_match block:")
# Find "type_match" in the function
tm_idx = func_bytes.find('type_match')
if tm_idx >= 0:
    print(func_bytes[tm_idx-100:tm_idx+400])