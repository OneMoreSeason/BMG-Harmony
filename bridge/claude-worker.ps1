<#
  Compatibility entry point for explicit, bounded Harmony tasks.
  Default: review only. No Bash, permission bypass, or app control.
  Use -TaskFile for the formal task contract; -Prompt creates a one-off review.
#>
[CmdletBinding(DefaultParameterSetName = 'Prompt')]
param(
  [Parameter(Mandatory = $true, ParameterSetName = 'Task')][string]$TaskFile,
  [Parameter(Mandatory = $true, ParameterSetName = 'Prompt')][string]$Prompt,
  [Parameter(Mandatory = $true, ParameterSetName = 'PromptFile')][string]$PromptFile,
  [string]$WorkDir = (Join-Path $env:TEMP 'harmony-worker'),
  [ValidateSet('review','implement')][string]$Mode = 'review',
  [string[]]$AllowedFiles = @(),
  [string]$Model,
  [string]$ClaudePath,
  [ValidateSet('text','json')][string]$OutputFormat = 'json',
  [ValidateRange(1,3600)][int]$TimeoutSeconds = 600,
  [switch]$AllowBash,
  [string[]]$AllowedTools
)
$ErrorActionPreference = 'Stop'
if ($AllowBash -or $AllowedTools) {
  throw 'Arbitrary tool grants are retired. Use a scoped task; the supervisor runs build/test commands.'
}
$python = if ($env:HARMONY_PYTHON) { $env:HARMONY_PYTHON } else {
  Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'
}
if (-not (Test-Path -LiteralPath $python)) { throw 'Set HARMONY_PYTHON to the Python executable.' }
$temporaryTask = $null
try {
  if (-not $TaskFile) {
    if ($PromptFile) { $Prompt = Get-Content -Raw -LiteralPath $PromptFile -Encoding UTF8 }
    New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
    $packet = @{
      version = 1; task_id = ('manual-' + [guid]::NewGuid().ToString('N'))
      objective = $Prompt; workdir = (Resolve-Path -LiteralPath $WorkDir).Path
      mode = $Mode; allowed_files = @($AllowedFiles)
      acceptance_criteria = @('Return findings, evidence, and remaining risks within the assigned scope.')
      timeout_seconds = $TimeoutSeconds
    }
    if ($Model) { $packet.model = $Model }
    $temporaryTask = Join-Path $env:TEMP ($packet.task_id + '.json')
    [System.IO.File]::WriteAllText($temporaryTask, ($packet | ConvertTo-Json -Depth 6),
      [System.Text.UTF8Encoding]::new($false))
    $TaskFile = $temporaryTask
  }
  $workerArgs = @((Join-Path $PSScriptRoot 'delegate.py'))
  if ($ClaudePath) { $workerArgs += @('--claude', $ClaudePath) }
  $workerArgs += @('run', $TaskFile)
  $output = & $python @workerArgs
  $workerExit = $LASTEXITCODE
  if ($OutputFormat -eq 'text') {
    $receipt = ($output -join [Environment]::NewLine) | ConvertFrom-Json
    if ($receipt.result) { Write-Output $receipt.result } else { Write-Output ($output -join [Environment]::NewLine) }
  } else {
    Write-Output $output
  }
  exit $workerExit
}
finally {
  if ($temporaryTask -and (Test-Path -LiteralPath $temporaryTask)) {
    Remove-Item -LiteralPath $temporaryTask
  }
}
