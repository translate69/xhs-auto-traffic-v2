$ErrorActionPreference = 'SilentlyContinue'
$RepoRoot = "E:\translate\claw\xhs-auto-traffic-v2"
$stateFile = Join-Path $RepoRoot ".filter_notify_last"

$latest = git -C $RepoRoot log --oneline -1 -- filter/filter_service.py test/corpus/problem_notes.json
if (-not $latest) { exit 0 }

$latestHash = ($latest -split ' ')[0]

if (Test-Path $stateFile) {
    $lastHash = Get-Content $stateFile -Raw | ForEach-Object { $_.Trim() }
    if ($lastHash -eq $latestHash) { exit 0 }
}

# 有新 commit，生成汇报
$commitMsg = $latest
$changedFiles = git -C $RepoRoot diff --name-only "${latestHash}^..${latestHash}"

$msg = "🛡️ **Filter 变更自动汇报**`n`n"
$msg += "**Commit:** $commitMsg`n"
$msg += "**变更文件:** $changedFiles"

# 检查 problem_notes 新增条目
if ($changedFiles -match "test/corpus/problem_notes.json") {
    $diff = git -C $RepoRoot diff "${latestHash}^..${latestHash}" -- test/corpus/problem_notes.json
    $newIds = [regex]::Matches($diff, '\+"note_id":\s*"([^"]+)"') | ForEach-Object { $_.Groups[1].Value }
    if ($newIds) {
        $msg += "`n`n**新增 Problem Notes:**`n"
        foreach ($id in $newIds) {
            $titleLine = git -C $RepoRoot show "${latestHash}:test/corpus/problem_notes.json" | Select-String -Pattern $id -Context 0,3 | ForEach-Object { $_.Line }
            $msg += "• `$id`n"
        }
    }
}

$msg += "`n`n— 自动汇报脚本"

# 写入临时文件供后续处理
$msg | Set-Content (Join-Path $RepoRoot ".filter_notify_msg.txt") -NoNewline
$latestHash | Set-Content $stateFile -NoNewline

Write-Host "NEW_COMMIT_DETECTED: $commitMsg"
exit 0
