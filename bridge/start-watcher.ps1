<# No service is installed. Omit -Enable to inspect the disabled default. #>
param(
  [switch]$Enable,
  [string[]]$AllowedRoot = @(),
  [switch]$AllowImplement,
  [ValidateRange(1,86400)][int]$Poll = 30,
  [ValidateRange(1,86400)][int]$Cooldown = 60,
  [ValidateRange(1,1000)][int]$MaxDaily = 20,
  [ValidateRange(1,100)][int]$MaxFail = 3,
  [switch]$Once
)
$ErrorActionPreference = 'Stop'
$python = if ($env:HARMONY_PYTHON) { $env:HARMONY_PYTHON } else {
  Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'
}
$watcherArgs = @((Join-Path $PSScriptRoot 'harmony-inbox-watcher.py'),
  '--poll', $Poll, '--cooldown', $Cooldown, '--max-daily', $MaxDaily, '--max-fail', $MaxFail)
if ($Enable) { $watcherArgs += '--enable' }
if ($AllowImplement) { $watcherArgs += '--allow-implement' }
foreach ($root in $AllowedRoot) { $watcherArgs += @('--allowed-root', $root) }
if ($Once) { $watcherArgs += '--once' }
& $python @watcherArgs
exit $LASTEXITCODE
