"""Patch: remove len>30 fallback from type_match, require genuine ask/question signal"""
with open(r'E:\translate\claw\xhs-auto-traffic-v2\filter\filter_service.py', 'rb') as f:
    raw = f.read()

func_marker = 'def _get_pass_reasons'.encode('utf-8')
pos = raw.find(func_marker)
rest = raw[pos:]
next_func = rest.find(b'    def ')
func_end = pos + next_func

# Find the type_match block - look for the elif that uses _has_unnegated_intent
# The old block is:
#   elif len(content_no_tags) > 30 and self._has_unnegated_intent(content_no_tags):
#       reasons.append("type_match")
# We want to REMOVE this elif entirely

old_block = b'            # \xe5\x86\x85\xe5\xae\xb9\xe8\xbe\xe8\xb6\x8a\xe5\xb0\x8f\xe5\x8d\x95\xe5\x8f\x8a\xe6\x9c\x89\xe6\x84\x8f\xe5\x9b\xbe\xe8\xaf\x8d\xef\xbc\x88\xe6\x8e\x92\xe9\x99\xa4\xe8\xa2\xab\xe5\x90\xa6\xe5\xae\x9a\xe4\xbf\xae\xe9\x80\xa0\xe7\x9a\x84\xef\xbc\x89\xe3\x80\x80\xe9\x80\x9a\xe8\xbf\x87\n            elif len(content_no_tags) > 30 and self._has_unnegated_intent(content_no_tags):\n                reasons.append("type_match")'

# Try to find just the "elif len(content_no_tags) > 30" part
elif_marker = b'elif len(content_no_tags) > 30 and self._has_unnegated_intent'
pos_elif = raw.find(elif_marker)
if pos_elif > 0:
    # Find the full line
    line_start = raw.rfind(b'\n', 0, pos_elif) + 1
    line_end = raw.find(b'\n', pos_elif)
    print(f"Found elif at {pos_elif}, line {line_start}-{line_end}")
    print("Line:", raw[line_start:line_end].decode('utf-8', errors='replace'))
    
    # Replace the elif with just a comment that it's removed
    # Actually, let's just remove it (replace with pass comment)
    new_block = b'            # Removed: len>30 fallback too loose for type_match; require genuine ask signal'
    raw = raw[:line_start] + new_block + raw[line_end:]
    
    with open(r'E:\translate\claw\xhs-auto-traffic-v2\filter\filter_service.py', 'wb') as f:
        f.write(raw)
    print("Patched OK")
else:
    print("elif block NOT found")
    # Try to find "type_match" in the function
    tm_pos = raw.find(b'type_match', pos)
    print(f"type_match first mention at byte {tm_pos}")
    if tm_pos > 0:
        print("Context:", raw[tm_pos-50:tm_pos+200].decode('utf-8', errors='replace'))