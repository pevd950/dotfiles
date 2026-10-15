<#
.SYNOPSIS
Preview or deploy shared Codex instructions and the minimal personal skill profile.
.DESCRIPTION
Installs no packages. Never invokes setup.sh, yadm bootstrap, or skill helpers.
Existing nonidentical files require -BackupConflicts; no unrelated files are removed.
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$SourceRoot = (Split-Path $PSScriptRoot -Parent),
    [string]$TargetHome = [Environment]::GetFolderPath('UserProfile'),
    [string]$CodexHome,
    [switch]$Apply,
    [switch]$BackupConflicts
)
$ErrorActionPreference = 'Stop'
$SourceRoot = [IO.Path]::GetFullPath($SourceRoot)
$TargetHome = [IO.Path]::GetFullPath($TargetHome)
if (-not $CodexHome) {
    # Custom target homes are for isolated previews/tests, not the active profile.
    if (-not $PSBoundParameters.ContainsKey('TargetHome') -and $env:CODEX_HOME) { $CodexHome = $env:CODEX_HOME }
    else { $CodexHome = Join-Path $TargetHome '.codex' }
}
$CodexHome = [IO.Path]::GetFullPath($CodexHome)
if ((Split-Path $CodexHome -Parent) -ne $TargetHome) {
    throw 'CODEX_HOME must be directly inside the target home for relative skill references.'
}
function Assert-UnlinkedPath([string]$Path) {
    $cursor = [IO.Path]::GetFullPath($Path)
    while ($cursor) {
        $item = Get-Item -LiteralPath $cursor -Force -ErrorAction SilentlyContinue
        if ($item -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw "Linked paths are not managed automatically: $cursor"
        }
        $parent = Split-Path $cursor -Parent
        if ($parent -eq $cursor) { break }
        $cursor = $parent
    }
}
Assert-UnlinkedPath $TargetHome
Assert-UnlinkedPath $CodexHome
$override = Join-Path $CodexHome 'AGENTS.override.md'
if ((Test-Path -LiteralPath $override) -and (Get-Item -LiteralPath $override).Length -gt 0) {
    throw 'AGENTS.override.md shadows global guidance; review it before deploying.'
}
$files = [Collections.Generic.List[object]]::new()
$files.Add(@{ Source = Join-Path $SourceRoot '.codex/AGENTS.md'; Target = Join-Path $CodexHome 'AGENTS.md'; Relative = '.codex/AGENTS.md' })
$skills = @(Get-Content (Join-Path $SourceRoot 'scripts/agent-skills.txt') | Where-Object { $_.Trim() -and -not $_.Trim().StartsWith('#') })
foreach ($skill in $skills) {
    if ($skill -notmatch '^[a-z0-9-]+/[a-z0-9-]+$') { throw "Invalid skill selection: $skill" }
    $relativeRoot = ".agents/skills/$skill"
    $skillRoot = Join-Path $SourceRoot $relativeRoot
    if (-not (Test-Path (Join-Path $skillRoot 'SKILL.md'))) { throw "Missing skill: $skill" }
    foreach ($item in Get-ChildItem -LiteralPath $skillRoot -Recurse -Force) {
        Assert-UnlinkedPath $item.FullName
        if (-not $item.PSIsContainer) {
            $suffix = $item.FullName.Substring($skillRoot.Length).TrimStart('\', '/')
            $relative = "$relativeRoot/$suffix"
            $files.Add(@{ Source = $item.FullName; Target = Join-Path $TargetHome $relative; Relative = $relative })
        }
    }
}
$changes = @()
foreach ($file in $files) {
    Assert-UnlinkedPath $file.Source
    Assert-UnlinkedPath $file.Target
    if (-not (Test-Path -LiteralPath $file.Source -PathType Leaf)) { throw "Missing source: $($file.Source)" }
    if (Test-Path -LiteralPath $file.Target -PathType Container) { throw "File target is a directory: $($file.Target)" }
    $hash = (Get-FileHash -LiteralPath $file.Source -Algorithm SHA256).Hash
    $exists = Test-Path -LiteralPath $file.Target
    if ($exists -and (Get-FileHash -LiteralPath $file.Target -Algorithm SHA256).Hash -eq $hash) { continue }
    $file.Hash = $hash
    $file.Conflict = $exists -and (Get-Item -LiteralPath $file.Target).Length -gt 0
    $changes += $file
}
"Packages to install: none. Selected skills: $($skills -join ', ')"
"Files requiring deployment: $($changes.Count)"
foreach ($file in $changes) { "$(if ($file.Conflict) { 'BACKUP/REPLACE' } else { 'CREATE' }): $($file.Target)" }
if (-not $Apply) { 'Preview only. Use -Apply after review; -BackupConflicts permits backed-up replacement.'; return }
if (@($changes | Where-Object Conflict).Count -gt 0 -and -not $BackupConflicts) {
    throw 'Conflicting files found. No files changed. Review and rerun with -BackupConflicts if intended.'
}
if ($changes.Count -eq 0) { 'Already current; no files changed.'; return }
$stateRoot = Join-Path $TargetHome '.local/state/dotfiles-agents'
Assert-UnlinkedPath $stateRoot
Assert-UnlinkedPath (Join-Path $stateRoot 'manifest.json')
$backupRoot = Join-Path $stateRoot ('backups/' + [guid]::NewGuid().ToString('N'))
if (-not $PSCmdlet.ShouldProcess($TargetHome, "Deploy $($changes.Count) agent files")) { return }
foreach ($file in $changes) {
    if ($file.Conflict) {
        $backup = Join-Path $backupRoot $file.Relative
        New-Item -ItemType Directory -Path (Split-Path $backup -Parent) -Force | Out-Null
        Copy-Item -LiteralPath $file.Target -Destination $backup
    }
    New-Item -ItemType Directory -Path (Split-Path $file.Target -Parent) -Force | Out-Null
    Copy-Item -LiteralPath $file.Source -Destination $file.Target -Force
}
New-Item -ItemType Directory -Path $stateRoot -Force | Out-Null
@{ source = $SourceRoot; codexHome = $CodexHome; skills = $skills; files = @($files | ForEach-Object { @{ path = $_.Target; sha256 = (Get-FileHash -LiteralPath $_.Source -Algorithm SHA256).Hash } }) } |
    ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $stateRoot 'manifest.json') -Encoding utf8
'Deployed shared instructions and selected skills. Start a fresh Codex chat to verify discovery.'
if (Test-Path $backupRoot) { "Backups: $backupRoot" }
