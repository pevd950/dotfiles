# Copy shared agent guidance and its referenced skills; preview unless -Apply is set.
[CmdletBinding()]
param([string]$TargetHome = $env:USERPROFILE, [switch]$Apply)
$ErrorActionPreference = 'Stop'
$sourceRoot = Split-Path $PSScriptRoot -Parent
$TargetHome = [IO.Path]::GetFullPath($TargetHome)
$codexPath = Join-Path $TargetHome '.codex'
if (-not $PSBoundParameters.ContainsKey('TargetHome') -and $env:CODEX_HOME -and
    [IO.Path]::GetFullPath($env:CODEX_HOME) -ne $codexPath) {
    throw 'Custom CODEX_HOME is not supported by this minimal setup.'
}
function Assert-Unlinked([string]$Path) {
    for ($cursor = $Path; $cursor; $cursor = Split-Path $cursor -Parent) {
        $item = Get-Item -LiteralPath $cursor -Force -ErrorAction SilentlyContinue
        if ($item -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw "Review linked path manually: $cursor"
        }
    }
}
$override = Join-Path $codexPath 'AGENTS.override.md'
if (Test-Path -LiteralPath $override) { throw 'Review AGENTS.override.md before deploying global guidance.' }
$selected = @(
    '.codex/AGENTS.md',
    '.agents/skills/productivity/craft',
    '.agents/skills/productivity/task-management',
    '.agents/skills/ops/cross-host-context',
    '.agents/skills/development/babysit-pr'
)
$paths = @(git -C $sourceRoot ls-files -- @selected)
if ($LASTEXITCODE -ne 0 -or $paths.Count -eq 0) { throw 'Run from a Git checkout with Git available.' }
$changes = @()
$conflicts = @()
foreach ($path in $paths) {
    $source = Join-Path $sourceRoot $path
    $target = Join-Path $TargetHome $path
    Assert-Unlinked $source
    Assert-Unlinked $target
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing source: $path" }
    if (Test-Path -LiteralPath $target -PathType Container) { throw "File target is a directory: $target" }
    if (Test-Path -LiteralPath $target) {
        if ((Get-FileHash -LiteralPath $source).Hash -eq (Get-FileHash -LiteralPath $target).Hash) { continue }
        $conflicts += $target
        "CONFLICT: $target"
    } else {
        $changes += @{ Source = $source; Target = $target }
        "CREATE: $target"
    }
}
if (-not $Apply) { 'Preview only. Use -Apply after reviewing the paths.'; return }
if ($conflicts.Count) { throw 'No files changed. Move conflicting files aside after reviewing them, then rerun.' }
foreach ($file in $changes) {
    New-Item -ItemType Directory -Path (Split-Path $file.Target -Parent) -Force | Out-Null
    Copy-Item -LiteralPath $file.Source -Destination $file.Target
}
"Copied $($changes.Count) files. No packages installed. Start a fresh Codex chat to load the guidance."
