<#
  claude-worker.ps1 — Safe headless Claude worker for the BMG-Harmony reverse bridge.

  Purpose: let a SUPERVISOR (e.g. Codex) delegate a task to Claude non-interactively
  and read the result. This is the mirror image of Claude driving `codex exec`.

  Safety posture (safe + sustainable by design):
    * --strict-mcp-config + minimal harmony.mcp.json  => ONLY the shared board is exposed.
      None of Claude's other MCP organelles (desktop-ops, blender, godot, yantrikdb) are loaded.
    * --allowedTools whitelist                         => explicit allow-list, NOT a blanket
      permission bypass. Dangerous tools are simply unavailable.
    * Isolated working directory                        => file work stays in a scratch dir,
      not the caller's repo, unless the caller overrides -WorkDir.

  Usage:
    powershell -ExecutionPolicy Bypass -File claude-worker.ps1 -Prompt "your task here"
    powershell -ExecutionPolicy Bypass -File claude-worker.ps1 -Prompt "..." -WorkDir "C:\path\to\repo" -AllowBash

  Returns: Claude's final response on stdout (text by default).
#>
[CmdletBinding()]
param(
  # Either -Prompt (inline string, fine for short prompts) or -PromptFile (path to a
  # UTF-8 text file containing the prompt — required for long/multi-line prompts passed
  # from Python subprocess to avoid list2cmdline quoting corruption).
  [string]$Prompt,
  [string]$PromptFile,

  # Where the worker is allowed to do file work. Defaults to an out-of-repo scratch dir.
  [string]$WorkDir = (Join-Path $env:TEMP "harmony-worker"),

  # Tool allow-list. Board tools + read/write/edit by default. Bash is opt-in via -AllowBash.
  [string[]]$AllowedTools = @(
    "mcp__bmg-harmony__post_message",
    "mcp__bmg-harmony__read_thread",
    "mcp__bmg-harmony__list_threads",
    "mcp__bmg-harmony__ack_message",
    "mcp__bmg-harmony__reply_message",
    "mcp__bmg-harmony__get_battle_card",
    "mcp__bmg-harmony__append_proving_envelope",
    "Read", "Write", "Edit"
  ),

  # Add Bash to the allow-list (needed for build/test tasks; off by default for safety).
  [switch]$AllowBash,

  [ValidateSet("text", "json", "stream-json")]
  [string]$OutputFormat = "text",

  [string]$Model
)

$ErrorActionPreference = "Stop"

$claude = Join-Path $env:APPDATA "npm\claude.cmd"
if (-not (Test-Path $claude)) { throw "claude CLI not found at $claude (run: npm install -g @anthropic-ai/claude-code)" }

$mcp = Join-Path $PSScriptRoot "harmony.mcp.json"
if (-not (Test-Path $mcp)) { throw "harmony.mcp.json not found next to this script at $mcp" }

if ($AllowBash) { $AllowedTools += "Bash" }
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null

$claudeArgs = @(
  "-p", $Prompt,
  "--output-format", $OutputFormat,
  "--mcp-config", $mcp,
  "--strict-mcp-config",
  "--add-dir", $WorkDir,
  "--allowedTools"
) + $AllowedTools
if ($Model) { $claudeArgs += @("--model", $Model) }

Push-Location $WorkDir
try {
  if ($PromptFile) {
    # Long/multi-line prompt delivered via file → pipe to claude stdin.
    # Avoids subprocess.list2cmdline quoting corruption for special characters.
    Get-Content -Raw -Path $PromptFile -Encoding UTF8 | & $claude @claudeArgs
  } elseif ($Prompt) {
    $Prompt | & $claude @claudeArgs
  } else {
    throw "Provide either -Prompt or -PromptFile."
  }
  exit $LASTEXITCODE
}
finally {
  Pop-Location
}
