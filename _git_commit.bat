@echo off
cd /d E:\translate\claw\xhs-auto-traffic-v2
git add -A
git commit -m "fix: 修复筛选逻辑，移除 type_match 的 len>30 后门"