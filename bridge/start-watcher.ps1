<#
  start-watcher.ps1 — launch the harmony-inbox-watcher in this terminal.

  Usage (defaults):     .\start-watcher.ps1
  Custom poll/cap:      .\start-watcher.ps1 -Poll 15 -MaxDaily 30
  Single-shot test:     .\start-watcher.ps1 -Once

  To stop: touch C:\Users\thepo\AppData\Local\Temp\STOP-HARMONY-WATCHER
  (or just Ctrl-C; the watcher will catch the kill switch on next poll)
#>
param(
    [int]   $Poll      = 30,
    [int]   $Cooldown  = 60,
    [int]   $MaxDaily  = 20,
    [int]   $MaxFail   = 3,
    [switch]$Once
)

$py     = "C:\Users\thepo\AppData\Local\Programs\Python\Python313\python.exe"
$script = Join-Path $PSScriptRoot "harmony-inbox-watcher.py"

$args = @("--poll", $Poll, "--cooldown", $Cooldown, "--max-daily", $MaxDaily, "--max-fail", $MaxFail)
if ($Once) { $args += "--once" }

Write-Host "Starting harmony-inbox-watcher (poll=${Poll}s, daily_cap=$MaxDaily)"
Write-Host "Kill switch: $env:TEMP\STOP-HARMONY-WATCHER"
Write-Host ""

& $py $script @args
