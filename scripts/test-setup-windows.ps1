$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $PSScriptRoot 'setup-windows.ps1'
$testRoot = Join-Path ([IO.Path]::GetTempPath()) ('dotfiles-agents-' + [guid]::NewGuid())
$targetRoot = Join-Path $testRoot 'profile with spaces'
function Assert-True($Condition, $Message) { if (-not $Condition) { throw $Message } }
try {
    & $scriptPath -TargetHome $targetRoot
    Assert-True (-not (Test-Path $targetRoot)) 'Preview changed target home'
    New-Item -ItemType Directory -Path (Join-Path $targetRoot '.codex') -Force | Out-Null
    $instructionsPath = Join-Path $targetRoot '.codex/AGENTS.md'
    Set-Content $instructionsPath 'host-local instructions'
    $failed = $false
    try { & $scriptPath -TargetHome $targetRoot -Apply } catch { $failed = $true }
    Assert-True $failed 'Conflicting instructions were silently replaced'
    Assert-True ((Get-Content $instructionsPath -Raw).Trim() -eq 'host-local instructions') 'Conflict changed'
    $unrelatedPath = Join-Path $targetRoot '.codex/config.toml'
    Set-Content $unrelatedPath 'keep me'
    & $scriptPath -TargetHome $targetRoot -Apply -BackupConflicts
    Assert-True ((Get-Content $instructionsPath -Raw) -match 'Craft is my knowledge base') 'Instructions missing'
    Assert-True (Test-Path (Join-Path $targetRoot '.agents/skills/productivity/craft/references/formatting.md')) 'Craft references missing'
    Assert-True (-not (Test-Path (Join-Path $targetRoot '.agents/skills/design'))) 'Unselected skills copied'
    Assert-True ((Get-Content $unrelatedPath -Raw).Trim() -eq 'keep me') 'Unrelated config changed'
    $backupFiles = @(Get-ChildItem (Join-Path $targetRoot '.local/state/dotfiles-agents/backups') -Recurse -File)
    Assert-True (@($backupFiles | Where-Object Name -eq 'AGENTS.md').Count -eq 1) 'Conflict backup missing'
    $backupCount = $backupFiles.Count
    & $scriptPath -TargetHome $targetRoot -Apply
    Assert-True (@(Get-ChildItem (Join-Path $targetRoot '.local/state/dotfiles-agents/backups') -Recurse -File).Count -eq $backupCount) 'Rerun created backups'
    Set-Content (Join-Path $targetRoot '.codex/AGENTS.override.md') 'override'
    $failed = $false
    try { & $scriptPath -TargetHome $targetRoot -Apply } catch { $failed = $true }
    Assert-True $failed 'Shadowing override not rejected'
    Remove-Item -LiteralPath (Join-Path $targetRoot '.codex/AGENTS.override.md')
    $customCodex = Join-Path $targetRoot 'custom codex'
    & $scriptPath -TargetHome $targetRoot -CodexHome $customCodex -Apply
    Assert-True (Test-Path (Join-Path $customCodex 'AGENTS.md')) 'Custom Codex home ignored'
    $outside = Join-Path $testRoot 'outside'
    New-Item -ItemType Directory -Path $outside | Out-Null
    $linkedHome = Join-Path $testRoot 'linked profile'
    New-Item -ItemType Directory -Path $linkedHome | Out-Null
    if ($IsWindows) { New-Item -ItemType Junction -Path (Join-Path $linkedHome '.agents') -Target $outside | Out-Null }
    else { New-Item -ItemType SymbolicLink -Path (Join-Path $linkedHome '.agents') -Target $outside | Out-Null }
    $failed = $false
    try { & $scriptPath -TargetHome $linkedHome -Apply } catch { $failed = $true }
    Assert-True $failed 'Linked target directory accepted'
    Assert-True (@(Get-ChildItem $outside -Force).Count -eq 0) 'Wrote outside target through link'
    'PASS: Windows agent deployment safety tests'
} finally {
    # Delete only the verified disposable test root, never a live profile.
    $resolvedRoot = [IO.Path]::GetFullPath($testRoot)
    $tempBase = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if (-not $resolvedRoot.StartsWith($tempBase, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe cleanup target' }
    if (Test-Path $resolvedRoot) { Remove-Item -LiteralPath $resolvedRoot -Recurse -Force }
}
