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

# 新 commit，读取详情
$commitFull = git -C $RepoRoot log --oneline -1 "$latestHash"
$changedFiles = git -C $RepoRoot diff --name-only "${latestHash}^..${latestHash}"
$filterStats = ""
if ($changedFiles -match "filter/filter_service.py") {
    $filterStats = git -C $RepoRoot diff --stat "${latestHash}^..${latestHash}" -- filter/filter_service.py
}

$newNotes = @()
if ($changedFiles -match "test/corpus/problem_notes.json") {
    $diff = git -C $RepoRoot diff "${latestHash}^..${latestHash}" -- test/corpus/problem_notes.json
    $newIds = [regex]::Matches($diff, '\+"note_id":\s*"([^"]+)"') | ForEach-Object { $_.Groups[1].Value }
    $newNotes = $newIds
}

$msg = "🛡️ **Filter 变更自动汇报**`n`n"
$msg += "**Commit:** $commitFull`n"
$msg += "**变更文件:** $changedFiles"
if ($filterStats) { $msg += "`n**Filter 改动:** $filterStats" }
if ($newNotes.Count -gt 0) {
    $msg += "`n`n**新增 Problem Notes ($($newNotes.Count) 条):**`n"
    foreach ($id in $newNotes) {
        $msg += "• `$id`n"
    }
}
$msg += "`n— 自动监控"

# 写入消息文件，触发通知
@{
    message = $msg
    commitHash = $latestHash
} | ConvertTo-Json -Compress | Set-Content (Join-Path $RepoRoot ".filter_notify_pending.json") -NoNewline

$latestHash | Set-Content $stateFile -NoNewline
Write-Host "PENDING_NOTIFICATION: $($newNotes.Count) notes from $commitFull"
exit 0
