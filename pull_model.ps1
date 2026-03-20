# pull_model.ps1
# Downloads a single Ollama model with CPU limited via .wslconfig
# Runs ollama pull directly in the terminal (no redirection) so native
# progress bar renders correctly. Window closes automatically when done.
# Called once per model by the installer.

param(
    [Parameter(Mandatory=$true)][string]$Model,
    [Parameter(Mandatory=$false)][decimal]$CpuFraction = 0.125
)

$DOCKER_CONTEXT = "default"
$CONTAINER      = "ollama"
$totalCores     = [Environment]::ProcessorCount
$limitedCores   = [Math]::Max(1, [Math]::Floor($totalCores * $CpuFraction))
$wslConfigPath  = "$env:USERPROFILE\.wslconfig"
$backupPath     = "$env:USERPROFILE\.wslconfig.ollamavoice_backup"
$startTime      = Get-Date

$host.UI.RawUI.WindowTitle = "OllamaVoice - Downloading $Model"
try { $host.UI.RawUI.WindowSize = New-Object System.Management.Automation.Host.Size(80, 32) } catch {}

function Write-Sep  { Write-Host ("=" * 64) -ForegroundColor DarkGray }
function Write-OK   ([string]$m) { Write-Host "  [OK]  $m" -ForegroundColor Green }
function Write-Info ([string]$m) { Write-Host "  [..] $m" -ForegroundColor Yellow }
function Write-Err  ([string]$m) { Write-Host "  [!!] $m" -ForegroundColor Red }

function Wait-Docker([int]$timeout = 180) {
    $elapsed = 0
    while ($elapsed -lt $timeout) {
        Start-Sleep 3; $elapsed += 3
        & docker --context default info *>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-OK "Docker ready in ${elapsed}s"
            return $true
        }
        Write-Host "`r  [..] Waiting for Docker... ${elapsed}s   " -NoNewline -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Err "Docker did not become ready after ${timeout}s"
    return $false
}

function Restore-WslConfig {
    if (Test-Path $backupPath) {
        Copy-Item $backupPath $wslConfigPath -Force
        Remove-Item $backupPath -Force -ErrorAction SilentlyContinue
        Write-OK ".wslconfig restored to original"
    } else {
        Remove-Item $wslConfigPath -Force -ErrorAction SilentlyContinue
        Write-OK "Removed temporary .wslconfig"
    }
}

# ── Header ────────────────────────────────────────────────────────
Clear-Host
Write-Sep
Write-Host "  OllamaVoice - Model Downloader" -ForegroundColor Yellow
Write-Sep
Write-Host "  Model    : $Model" -ForegroundColor Cyan
Write-Host "  CPU cap  : $limitedCores of $totalCores cores ($([Math]::Round($CpuFraction * 100))%)" -ForegroundColor Green
Write-Host "  Started  : $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor DarkGray
Write-Sep
Write-Host ""

# ── Backup .wslconfig ─────────────────────────────────────────────
Write-Info "Backing up .wslconfig..."
if (Test-Path $wslConfigPath) {
    Copy-Item $wslConfigPath $backupPath -Force
    Write-OK "Backed up existing .wslconfig"
} else {
    Write-OK "No existing .wslconfig"
}

# ── Apply CPU limit ───────────────────────────────────────────────
$cfg = "[wsl2]`r`nprocessors=$limitedCores`r`nmemory=4GB`r`n"
Set-Content $wslConfigPath $cfg -Force
Write-OK "CPU limit applied: processors=$limitedCores"

# ── Restart WSL2 ──────────────────────────────────────────────────
Write-Host ""
Write-Info "Restarting WSL2 to apply CPU limit..."
& wsl --shutdown
Start-Sleep 6

if (-not (Wait-Docker 180)) {
    Write-Err "Docker failed to restart. Aborting."
    Restore-WslConfig
    & wsl --shutdown
    Start-Sleep 3
    exit 1
}

# ── Start Ollama container ────────────────────────────────────────
Write-Host ""
Write-Info "Starting Ollama container..."
& docker --context $DOCKER_CONTEXT start $CONTAINER *>&1 | Out-Null
Start-Sleep 8
Write-OK "Ollama container running"

# ── Download ──────────────────────────────────────────────────────
Write-Host ""
Write-Sep
Write-Host "  Downloading: $Model" -ForegroundColor Yellow
Write-Host "  CPU capped at $([Math]::Round($CpuFraction * 100))% - your PC stays responsive" -ForegroundColor Green
Write-Host "  Progress is shown below. Do not close this window." -ForegroundColor DarkGray
Write-Sep
Write-Host ""

# Run directly - no redirection - ollama's native progress works in terminal
& docker --context $DOCKER_CONTEXT exec $CONTAINER ollama pull $Model
$pullExit = $LASTEXITCODE

Write-Host ""
Write-Host ""

# ── Verify ────────────────────────────────────────────────────────
$verified = $false
if ($pullExit -eq 0) {
    Write-Info "Verifying $Model is installed..."
    $list = & docker --context $DOCKER_CONTEXT exec $CONTAINER ollama list 2>&1 | Out-String
    $base = $Model.Split(":")[0]
    if ($list -match [regex]::Escape($base)) {
        Write-OK "$Model confirmed in ollama list"
        $verified = $true
    } else {
        Write-Err "$Model not found in ollama list after download"
        Write-Host ""
        Write-Host "  ollama list output:" -ForegroundColor DarkGray
        Write-Host $list -ForegroundColor DarkGray
    }
} else {
    Write-Err "docker exec returned exit code $pullExit"
}

# ── Restore .wslconfig ────────────────────────────────────────────
Write-Host ""
Write-Sep
Write-Info "Restoring full CPU access..."
Restore-WslConfig

Write-Info "Restarting WSL2 to restore all $totalCores cores..."
& wsl --shutdown
Start-Sleep 6
Wait-Docker 120 | Out-Null
& docker --context $DOCKER_CONTEXT start $CONTAINER *>&1 | Out-Null
Write-OK "Full CPU restored"

# ── Result ────────────────────────────────────────────────────────
$mins = [Math]::Round(((Get-Date) - $startTime).TotalMinutes, 1)
Write-Host ""
Write-Sep
if ($verified) {
    Write-Host "  COMPLETE: $Model installed in ${mins} minutes" -ForegroundColor Green
} else {
    Write-Host "  FAILED: $Model did not install correctly" -ForegroundColor Red
    Write-Host "  Retry manually: docker exec ollama ollama pull $Model" -ForegroundColor Yellow
}
Write-Sep
Write-Host ""
Write-Host "  Closing in 5 seconds..." -ForegroundColor DarkGray
Start-Sleep 5
# Exit cleanly - window closes, installer moves to next model
if ($verified) { exit 0 } else { exit 1 }
