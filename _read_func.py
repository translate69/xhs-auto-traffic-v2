"""Read the full _get_pass_reasons function"""
with open(r'E:\translate\claw\xhs-auto-traffic-v2\filter\filter_service.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_func = False
func_lines = []
for i, l in enumerate(lines):
    if 'def _get_pass_reasons' in l:
        in_func = True
    if in_func:
        func_lines.append((i+1, l))
        if len(func_lines) > 1 and l.startswith('    def ') and 'def _get_pass_reasons' not in l:
            break

for i, l in func_lines:
    print(f"{i:3d}: {l}", end='')