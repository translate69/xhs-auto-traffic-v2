[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Set-Location "E:\translate\claw\xhs-auto-traffic-v2"
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONPATH = "E:\translate\claw\xhs-auto-traffic-v2"
python find_note.py 2>&1