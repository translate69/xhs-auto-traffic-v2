[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONPATH = "E:\translate\claw\xhs-auto-traffic-v2"
Set-Location "E:\translate\claw\xhs-auto-traffic-v2"
Write-Host "=== Checking keyword loading ===" -ForegroundColor Cyan
$output = python -c "
import sys
sys.path.insert(0, '.')
from load_keywords import load_keywords
kw = load_keywords()
for k in kw:
    print(k['keyword'])
" 2>&1
Write-Host $output -ForegroundColor Gray
Write-Host "`n=== Matching ===" -ForegroundColor Cyan
$match_out = python -c "
import sys
sys.path.insert(0, '.')
from load_keywords import load_keywords
all_kw = load_keywords()
kw_target = '\u6c53\u5c3e\u6d77\u8fb9\u6c民宿\u63a8\u8386'
print('Target:', kw_target)
filtered = [kw for kw in all_kw if kw['keyword'] == kw_target]
print('Filtered:', filtered)
" 2>&1
Write-Host $match_out -ForegroundColor Gray