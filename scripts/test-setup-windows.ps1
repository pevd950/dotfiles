$ErrorActionPreference = 'Stop'
$installer = Join-Path $PSScriptRoot 'setup-windows.ps1'
$testRoot = Join-Path ([IO.Path]::GetTempPath()) ('dotfiles-agents-' + [guid]::NewGuid())
$target = Join-Path $testRoot 'profile with spaces'
$untracked = Join-Path (Split-Path $PSScriptRoot -Parent) ('.agents/skills/productivity/craft/untracked-' + [guid]::NewGuid() + '.tmp')
function Assert($Condition, $Message) { if (-not $Condition) { throw $Message } }
try {
    & $installer -TargetHome $target
    Assert (-not (Test-Path $target)) 'Preview wrote files'
    New-Item -ItemType Directory -Path (Join-Path $target '.codex') -Force | Out-Null
    $instructions = Join-Path $target '.codex/AGENTS.md'
    [IO.File]::WriteAllText($instructions, '')
    $failed = $false
    try { & $installer -TargetHome $target -Apply } catch { $failed = $true }
    Assert $failed 'Existing empty file was overwritten'
    Assert ((Get-Item $instructions).Length -eq 0) 'Conflict changed'
    Assert (-not (Test-Path (Join-Path $target '.agents'))) 'Partial deployment before conflict rejection'
    Remove-Item -LiteralPath $instructions
    $unrelated = Join-Path $target '.codex/config.toml'
    Set-Content $unrelated 'preserve me'
    Set-Content $untracked 'not part of the shared skill'
    & $installer -TargetHome $target -Apply
    Assert ((Get-Content $instructions -Raw) -match 'Craft is my knowledge base') 'Instructions missing'
    Assert (Test-Path (Join-Path $target '.agents/skills/productivity/craft/references/formatting.md')) 'Supporting references missing'
    Assert (-not (Test-Path (Join-Path $target '.agents/skills/design'))) 'Unselected skills deployed'
    Assert (-not (Test-Path (Join-Path $target ('.agents/skills/productivity/craft/' + (Split-Path $untracked -Leaf))))) 'Untracked source file copied'
    Assert ((Get-Content $unrelated -Raw).Trim() -eq 'preserve me') 'Unrelated configuration changed'
    & $installer -TargetHome $target -Apply
    Assert (-not (Test-Path (Join-Path $target '.local'))) 'Unnecessary deployment state created'
    Set-Content (Join-Path $target '.codex/AGENTS.override.md') 'override'
    $failed = $false
    try { & $installer -TargetHome $target -Apply } catch { $failed = $true }
    Assert $failed 'Shadowing override ignored'
    $linked = Join-Path $testRoot 'linked'
    $outside = Join-Path $testRoot 'outside'
    New-Item -ItemType Directory -Path $linked,$outside | Out-Null
    New-Item -ItemType Junction -Path (Join-Path $linked '.agents') -Target $outside | Out-Null
    $failed = $false
    try { & $installer -TargetHome $linked -Apply } catch { $failed = $true }
    Assert $failed 'Linked target accepted'
    Assert (@(Get-ChildItem $outside -Force).Count -eq 0) 'Wrote through target link'
    'PASS: Windows agent setup tests'
} finally {
    if (Test-Path $untracked) { Remove-Item -LiteralPath $untracked }
    $resolved = [IO.Path]::GetFullPath($testRoot)
    $tempBase = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if (-not $resolved.StartsWith($tempBase, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe test cleanup' }
    if (Test-Path $resolved) { Remove-Item -LiteralPath $resolved -Recurse -Force }
}
