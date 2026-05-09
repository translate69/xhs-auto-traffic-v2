$ErrorActionPreference = 'SilentlyContinue'
$RepoRoot = "E:\translate\claw\xhs-auto-traffic-v2"
$stateFile = Join-Path $RepoRoot ".filter_notify_last"

$latest = git -C $RepoRoot log --oneline -1 -- filter/filter_service.py test/corpus/problem_notes.json
if (-not $latest) { exit 0 }

$latestHash = ($latest -split ' ')[0]

if (Test-Path $stateFile) {
    $lastHash = Get-Content $stateFile -Raw
    if ($lastHash -and $lastHash.Trim() -eq $latestHash) { exit 0 }
}

$commitFull = git -C $RepoRoot log --oneline -1 "$latestHash"
$body = git -C $RepoRoot log --oneline -3 -- filter/filter_service.py test/corpus/problem_notes.json
$changedFiles = git -C $RepoRoot diff --name-only "${latestHash}^..${latestHash}"

$noteCount = 0
if ($changedFiles -match "test/corpus/problem_notes.json") {
    $diff = git -C $RepoRoot diff "${latestHash}^..${latestHash}" -- test/corpus/problem_notes.json
    $noteCount = ([regex]::Matches($diff, 'note_id')).Count
}

$msg = "Filter 变更自动汇报 | Commit: $commitFull | 变更: $changedFiles"
if ($noteCount -gt 0) { $msg = $msg + " | 新增 Problem Notes: $noteCount 条" }

$pendingFile = Join-Path $RepoRoot ".filter_notify_pending.json"
$pendingHash = Join-Path $RepoRoot ".filter_notify_last"

$msgEscaped = $msg -replace '"', '\"'
$json = "{""msg"":""$msgEscaped"",""commitHash"":""$latestHash""}"
$json | Out-File -FilePath $pendingFile -NoNewline -Encoding UTF8
$latestHash | Out-File -FilePath $pendingHash -NoNewline -Encoding UTF8

Write-Host "PENDING: $commitFull"
exit 0
