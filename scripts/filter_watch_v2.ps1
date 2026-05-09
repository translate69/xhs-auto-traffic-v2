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

$commitMsg = $latest
$changedFiles = git -C $RepoRoot diff --name-only "${latestHash}^..${latestHash}"

$msg = "🛡️ **Filter 变更自动汇报**`n`n"
$msg += "**Commit:** $commitMsg`n"
$msg += "**变更文件:** $changedFiles"

if ($changedFiles -match "test/corpus/problem_notes.json") {
    $diff = git -C $RepoRoot diff "${latestHash}^..${latestHash}" -- test/corpus/problem_notes.json
    $newIds = [regex]::Matches($diff, '\+"note_id":\s*"([^"]+)"') | ForEach-Object { $_.Groups[1].Value }
    if ($newIds) {
        $msg += "`n`n**新增 Problem Notes ($($newIds.Count) 条):**`n"
        foreach ($id in $newIds) {
            $title = git -C $RepoRoot show "${latestHash}:test/corpus/problem_notes.json" | Select-String -Pattern """note_id""\s*:\s*""$id""" -Context 0,1 | ForEach-Object { ($_ -split 'title"":""')[1] -replace '",.*','' -replace '"}','' }
            $shortTitle = if ($title -and $title.Length -gt 25) { $title.Substring(0,25) + "..." } else { $title }
            $msg += "• `$id $shortTitle`n"
        }
    }
}

$msg += "`n— 自动监控"

# 写入消息文件
$msg | Set-Content (Join-Path $RepoRoot ".filter_notify_msg.txt") -NoNewline
$latestHash | Set-Content $stateFile -NoNewline

Write-Host "NEW_COMMIT: $commitMsg"
exit 0
