# Shared helpers for the H2Net v1 handoff entrypoints (Windows PowerShell 5.1+). Dot-sourced; not run directly.
$ErrorActionPreference = 'Stop'
$Repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Run = Join-Path $Repo 'h2net_v1_run'
Set-Location $Repo

function Fail([string]$msg) { Write-Host "FAILED: $msg" -ForegroundColor Red; exit 2 }
function Ok([string]$msg) { Write-Host "OK: $msg" -ForegroundColor Green }

function Get-Python {
    if ($env:H2PRISM_PYTHON -and (Test-Path $env:H2PRISM_PYTHON)) { return $env:H2PRISM_PYTHON }
    $p = Join-Path $Repo '.venv\Scripts\python.exe'
    if (Test-Path $p) { return $p }
    Fail "Python environment not found. Create it once: py -3.12 -m venv .venv ; .venv\Scripts\pip install -r requirements-lock.txt (or set H2PRISM_PYTHON)"
}

function Get-Matlab {
    if ($env:H2PRISM_MATLAB -and (Test-Path $env:H2PRISM_MATLAB)) { return $env:H2PRISM_MATLAB }
    $c = Get-Command matlab.exe -ErrorAction SilentlyContinue
    if ($c) { return $c.Source }
    $cands = Get-ChildItem 'C:\Program Files\MATLAB\R20*\bin\matlab.exe' -ErrorAction SilentlyContinue | Sort-Object FullName -Descending
    if ($cands) { return $cands[0].FullName }
    Fail "MATLAB not found. Install R2025a or later with Simulink and Simscape, or set H2PRISM_MATLAB to the full path of matlab.exe"
}

function Invoke-Py([string[]]$ArgList) {
    $py = Get-Python
    & $py @ArgList | Out-Host
    return $LASTEXITCODE
}

function Invoke-Matlab([string]$Statement, [string]$LogName) {
    # one MATLAB process, sequential; returns 0 only if the statement completed without error
    $m = Get-Matlab
    $log = Join-Path $Run "logs\$LogName.log"
    New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
    $env:H2PRISM_PYTHON = Get-Python
    $cmd = "addpath(fullfile(pwd,'tools','matlab')); try, $Statement; catch e, disp(getReport(e)); exit(1); end; exit(0)"
    & $m -logfile $log -batch $cmd | Out-Host
    $code = $LASTEXITCODE
    Write-Host "MATLAB log: $log"
    return $code
}
