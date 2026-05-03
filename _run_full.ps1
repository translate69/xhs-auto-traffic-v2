[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
Set-Location "E:\translate\claw\xhs-auto-traffic-v2"
python main.py --keyword "汕尾亲子游" --limit 8 --debug 2>&1