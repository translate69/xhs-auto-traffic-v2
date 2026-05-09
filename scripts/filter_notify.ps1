# filter_notify.ps1 - filter + problem_notes 变更自动汇报脚本
# 由 cronjob 每5分钟调用一次

param(
    [string]$RepoRoot = "E:\translate\claw\xhs-auto-traffic-v2"
)

$stateFile = Join-Path $RepoRoot ".filter_notify_last"
$feishuScript = Join-Path $RepoRoot "scripts\send_feishu.py"

# 1. 获取当前最新涉及 filter_service.py 或 problem_notes.json 的 commit
$latestCommit = git -C $RepoRoot log --oneline -1 -- filter/filter_service.py test/corpus/problem_notes.json 2>$null
if (-not $latestCommit) { exit 0 }

$latestHash = ($latestCommit -split ' ')[0]
if (-not $latestHash) { exit 0 }

# 2. 对比上次记录，无新commit则退出
if (Test-Path $stateFile) {
    $lastHash = Get-Content $stateFile -Raw | ForEach-Object { $_.Trim() }
    if ($lastHash -eq $latestHash) { exit 0 }
}

# 3. 有新commit，生成汇报内容
$commitHash = $latestHash
$commitMsg = git -C $RepoRoot log --oneline -1 $commitHash

# 获取涉及的 diff 文件列表
$changedFiles = git -C $RepoRoot diff --name-only "${commitHash}^..$commitHash" 2>$null

# 获取 problem_notes 新增的条目（只取新增的 diff hunk）
$newProblemNotes = @()
if ($changedFiles -match "test/corpus/problem_notes.json") {
    $diffOutput = git -C $RepoRoot diff "${commitHash}^..$commitHash" -- test/corpus/problem_notes.json 2>$null
    # 提取新加的 note_id（简单做法：取 +"note_id": 那行）
    $lines = $diffOutput -split "`n"
    $capturing = $false
    $newEntry = @{}
    foreach ($line in $lines) {
        if ($line -match '^\+\s*\{$') { $capturing = $true; $newEntry = @{} }
        elseif ($capturing -and $line -match '^\+\s*\}') { $capturing = $false; if ($newEntry.note_id) { $newProblemNotes += $newEntry } }
        elseif ($capturing) {
            if ($line -match '^\+\s*"note_id":\s*"([^"]+)"') { $newEntry.note_id = $Matches[1] }
            if ($line -match '^\+\s*"title":\s*"([^"]*)"') { $newEntry.title = $Matches[1] }
            if ($line -match '^\+\s*"reason":\s*"([^"]*)"') { $newEntry.reason = $Matches[1] }
            if ($line -match '^\+\s*"expected":\s*(true|false)') { $newEntry.expected = $Matches[1] }
        }
    }
}

# 获取 filter_service.py 的改动行数
$filterChanged = $changedFiles -match "filter/filter_service.py"
$filterStats = ""
if ($filterChanged) {
    $filterStats = git -C $RepoRoot diff --stat "${commitHash}^..$commitHash" -- filter/filter_service.py 2>$null
}

# 4. 发送飞书消息
$msgLines = @()
$msgLines += "🛡️ **Filter 变更自动汇报**"
$msgLines += ""
$msgLines += "**Commit:** `$commitMsg"
$msgLines += "**变更文件:** `$changedFiles"
if ($filterChanged) { $msgLines += "**Filter 改动:** `$filterStats" }
if ($newProblemNotes.Count -gt 0) {
    $msgLines += ""
    $msgLines += "**新增 Problem Notes (`$(newProblemNotes.Count) 条):**"
    foreach ($entry in $newProblemNotes) {
        $title = if ($entry.title) { $entry.title.Substring(0, [Math]::Min(30, $entry.title.Length)) } else { "(无标题)" }
        $expected = if ($entry.expected -eq "true") { "✅ 通过" } else { "❌ 过滤" }
        $msgLines += "• [$($entry.note_id)](http://xgic.openclaw.ai/search_result/$($entry.note_id)) | $($title) | $($expected)"
        if ($entry.reason) { $msgLines += "  原因: $($entry.reason)" }
    }
}

$feishuMsg = $msgLines -join "`n"

# 调用飞书脚本
if (Test-Path $feishuScript) {
    python $feishuScript $feishuMsg 2>$null
}

# 5. 更新记录
$latestHash | Set-Content $stateFile -NoNewline

Write-Host "NOTIFIED: $commitMsg"
exit 0
