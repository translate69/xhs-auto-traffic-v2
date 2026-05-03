[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONPATH = "E:\translate\claw\xhs-auto-traffic-v2"
Set-Location "E:\translate\claw\xhs-auto-traffic-v2"
python run_all.py --keyword "汕尾海边民宿推荐" --limit 8 --debug 2>&1