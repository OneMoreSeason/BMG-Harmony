<#
  codex-conductor.ps1 — Persistent multi-turn autonomous Codex runner for BMG-Harmony.

  This is the "not a one-off" host. A single `codex exec` is one bounded session;
  this conductor chains FRESH Codex passes over durable state (board + .planning/STATE.md
  + last after-packet) so Codex can run a long mission across many turns — restrained
  by UAE closeout and safety guards, exactly per BMG-Brain doctrine.

  Why fresh passes (not `resume`): BMG doctrine regains context from coarse live surfaces
  and the after-packet, not from a single fragile session. Fresh passes can't overflow
  context and match the coarse/fine packet model.

  STOP CONDITIONS (the loop is "restrained by UAE or other"):
    * UAE-CLOSEOUT  — Codex signals the mission is achieved + committed/pushed (or INCOMPLETE) + after-packet written.
    * UAE-HALT      — failure-loop hard stop (2 strikes) or a hard block; a human is needed.
    * MaxTurns      — safety guard.
    * Kill-switch   — operator drops the kill file; immediate halt.

  SAFETY: default sandbox is --full-auto (workspace-write), with the harmony store added
  as a writable root so board posts work. Real network pushes may need -FullAccess
  (--dangerously-bypass-approvals-and-sandbox); under the safe default, a blocked push is
  recorded as INCOMPLETE per UAE doctrine, which is the correct behavior, not a failure.

  Example:
    powershell -ExecutionPolicy Bypass -File codex-conductor.ps1 `
      -Objective "Add harmony-awareness to the Codex Boot Route in AGENTS.md and README, per the brief on harmony-inbox-codex." `
      -WorkDir "C:\Users\thepo\OneDrive\Documents\GitHub\BMG-Brain" -MaxTurns 6
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$Objective,
  [string]$WorkDir       = (Get-Location).Path,
  [string]$StatusThread  = "harmony-codex-autonomous",
  [int]$MaxTurns         = 8,
  [string]$KillSwitch    = (Join-Path $env:TEMP "STOP-CODEX"),
  [ValidateSet("low","medium","high","xhigh")][string]$Reasoning = "medium",
  [switch]$FullAccess
)

# NOTE: not "Stop" — codex is a native exe that prints its banner/progress to stderr.
# Under Stop, PS 5.1 turns the first stderr line into a terminating NativeCommandError.
# Our own precondition `throw`s below still abort regardless of this setting.
$ErrorActionPreference = "Continue"
$codex = Join-Path $env:APPDATA "npm\codex.cmd"
if (-not (Test-Path $codex)) { throw "codex CLI not found at $codex (npm install -g @openai/codex)" }
if (-not (Test-Path $WorkDir)) { throw "WorkDir not found: $WorkDir" }

$harmonyStore = "C:/Users/thepo/OneDrive/Documents/GitHub/BMG-Harmony/.harmony/store"
$logDir = Join-Path $env:TEMP ("codex-conductor-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
if (Test-Path $KillSwitch) { Remove-Item $KillSwitch -Force }  # clear stale kill file

# Sandbox posture
if ($FullAccess) {
  $sandboxArgs = @("--dangerously-bypass-approvals-and-sandbox")
} else {
  # TOML literal (single-quoted) string so the value carries no double-quotes that would
  # break native argument passing on PowerShell.
  $sandboxArgs = @("--full-auto", "-c", "sandbox_workspace_write.writable_roots=['$harmonyStore']")
}

function New-TurnPrompt([int]$Turn) {
@"
You are Codex operating under the BMG-Brain Agentic Operating Doctrine as a LONG AUTONOMOUS
multi-turn agent. A conductor re-invokes you each turn until you signal closeout. This is
turn $Turn of at most $MaxTurns.

LEAD WITH BRAIN (required first move):
- Recall durable memory (yantrikdb) relevant to this objective.
- Re-read the coarse live surfaces to regain context: the harmony board thread
  "$StatusThread" (via the bmg-harmony read_thread tool), this repo's .planning/STATE.md if
  present, and your most recent after-packet. Continuity lives in those durable surfaces,
  not in this session.
- Synthesize the invariant ledger: BMG-Brain coordinates; this repo owns implementation
  truth; memory/tools are context only; UAE governs evidence, receipt, commit, push, closeout.

OBJECTIVE:
$Objective

THIS TURN:
1. Declare ONE pass action and ONE proving intent. Do not mix lanes.
2. Do the next single coherent unit of work toward the objective (smallest meaningful change).
3. UAE closeout discipline: commit meaningful state with a real message; for a completed safe
   pass, run git status, commit, git pull --ff-only, git push, then git status -sb and capture
   the push receipt. If push is blocked, record INCOMPLETE with the explicit reason — never a
   silent third state.
4. FLYWHEEL: write durable learnings to memory if the pass produced durable decisions,
   corrections, procedures, or failure patterns. Green summaries are weak evidence; record
   friction/repairs.
5. Post a one-line pass status to the harmony board thread "$StatusThread" using the
   bmg-harmony post_message tool (agent_id=codex) so the team sees the pass action + result.

UAE HARD STOP: If you fail the same user-visible outcome twice, STOP. Do not retry louder.
Switch to diagnostic-only and signal halt.

SENTINEL — REQUIRED. End your final message with EXACTLY ONE line, starting at column 0:
  UAE-CLOSEOUT: <one-line summary>   (objective achieved AND committed/pushed-or-INCOMPLETE AND after-packet written)
  UAE-HALT: <reason>                 (failure-loop hard stop or hard block; human needed)
  UAE-CONTINUE: <the next single step>  (more work remains; you will be re-invoked)
"@
}

Write-Host "== codex-conductor =="
Write-Host "WorkDir   : $WorkDir"
Write-Host "Mission   : $Objective"
Write-Host "Status    : board thread '$StatusThread'"
Write-Host "Guards    : MaxTurns=$MaxTurns  KillSwitch=$KillSwitch  Sandbox=$(if($FullAccess){'full-access'}else{'full-auto+board-writable'})"
Write-Host "Logs      : $logDir"
Write-Host ""

$final = "MAXTURNS"
Push-Location $WorkDir
try {
  for ($turn = 1; $turn -le $MaxTurns; $turn++) {
    if (Test-Path $KillSwitch) { Write-Host "[turn $turn] KILL SWITCH present -> halting."; $final = "KILLED"; break }

    Write-Host "----- turn $turn / $MaxTurns -----"
    $prompt  = New-TurnPrompt $turn
    $turnLog = Join-Path $logDir ("turn-{0:00}.log" -f $turn)
    $outFile = Join-Path $logDir ("turn-{0:00}.out" -f $turn)
    $errFile = Join-Path $logDir ("turn-{0:00}.err" -f $turn)
    $cArgs   = @("exec","--skip-git-repo-check") + $sandboxArgs + @("-c","model_reasoning_effort=$Reasoning","-")

    # Redirect stdout/stderr to SEPARATE files (never 2>&1 — that wraps native stderr in
    # ErrorRecords on PS 5.1). stdin carries the prompt via the trailing `-` arg.
    $prompt | & $codex @cArgs 1> $outFile 2> $errFile
    Get-Content -Path $outFile, $errFile -ErrorAction SilentlyContinue | Set-Content -Path $turnLog
    $stdoutText = Get-Content -Path $outFile -Raw -ErrorAction SilentlyContinue
    if ($stdoutText) { Write-Host $stdoutText }

    # Detect the last sentinel line. Codex puts its final message on stdout; scan stderr as fallback.
    $sentinel = Select-String -Path $outFile -Pattern '^\s*(UAE-CLOSEOUT|UAE-HALT|UAE-CONTINUE):' -ErrorAction SilentlyContinue | Select-Object -Last 1
    if (-not $sentinel) {
      $sentinel = Select-String -Path $errFile -Pattern '^\s*(UAE-CLOSEOUT|UAE-HALT|UAE-CONTINUE):' -ErrorAction SilentlyContinue | Select-Object -Last 1
    }
    if (-not $sentinel) {
      Write-Host "[turn $turn] no sentinel emitted; treating as CONTINUE."
      continue
    }
    $line = $sentinel.Line.Trim()
    Write-Host "[turn $turn] sentinel: $line"
    if ($line -like "UAE-CLOSEOUT:*") { $final = "CLOSEOUT: $line"; break }
    if ($line -like "UAE-HALT:*")     { $final = "HALT: $line";     break }
    # UAE-CONTINUE -> next turn
  }
}
finally {
  Pop-Location
}

Write-Host ""
Write-Host "== conductor finished: $final =="
Write-Host "Logs: $logDir"
