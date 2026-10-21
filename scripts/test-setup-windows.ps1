$ErrorActionPreference = 'Stop'
$installer = Join-Path $PSScriptRoot 'setup-windows.ps1'
$sourceInstructions = Join-Path (Split-Path $PSScriptRoot -Parent) '.codex/AGENTS.md'
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
    Assert ((Get-FileHash -LiteralPath $instructions).Hash -eq (Get-FileHash -LiteralPath $sourceInstructions).Hash) 'Installed instructions differ from source'
    $installedInstructions = Get-Content -LiteralPath $instructions -Raw
    Assert (-not [string]::IsNullOrWhiteSpace($installedInstructions)) 'Installed instructions are empty'
    Assert ($installedInstructions -match '(?m)^## Authority and scope\r?$') 'Installed instructions are missing the authority heading'
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
    Assert (-not (Test-Path (Join-Path $target '.agents/skills/development/babysit-pr/SKILL.md'))) 'Unneeded babysitter deployed'
    Assert (Test-Path (Join-Path $target '.agents/skills/development/babysit-pr/references/github-media-evidence.md')) 'Linked media reference missing'
    $blocked = Join-Path $testRoot 'blocked'
    New-Item -ItemType Directory -Path (Join-Path $blocked '.agents/skills') -Force | Out-Null
    Set-Content (Join-Path $blocked '.agents/skills/productivity') 'keep'
    $failed = $false
    try { & $installer -TargetHome $blocked -Apply } catch { $failed = $true }
    Assert $failed 'File ancestor accepted'
    Assert (-not (Test-Path (Join-Path $blocked '.codex'))) 'Partial deployment before ancestor rejection'
    $savedIndex = $env:GIT_INDEX_FILE
    try {
        $env:GIT_INDEX_FILE = Join-Path $testRoot 'index'
        git -C $PSScriptRoot read-tree HEAD
        if ($LASTEXITCODE) { throw 'Could not create test index' }
        git -C (Split-Path $PSScriptRoot -Parent) update-index --force-remove -- .agents/skills/productivity/craft/SKILL.md
        if ($LASTEXITCODE) { throw 'Could not remove test index entry' }
        $incomplete = Join-Path $testRoot 'incomplete'
        $failed = $false
        try { & $installer -TargetHome $incomplete -Apply } catch { $failed = $true }
        Assert $failed 'Incomplete tracked selection accepted'
        Assert (-not (Test-Path $incomplete)) 'Partial deployment from incomplete selection'
    } finally { $env:GIT_INDEX_FILE = $savedIndex }
    'PASS: Windows agent setup tests'
} finally {
    if (Test-Path $untracked) { Remove-Item -LiteralPath $untracked }
    $resolved = [IO.Path]::GetFullPath($testRoot)
    $tempBase = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if (-not $resolved.StartsWith($tempBase, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe test cleanup' }
    if (Test-Path $resolved) { Remove-Item -LiteralPath $resolved -Recurse -Force }
}
