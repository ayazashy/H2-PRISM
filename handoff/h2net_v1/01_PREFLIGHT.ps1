# 01 - Preflight: repository, Python, MATLAB, RAM, disk, hashes. Writes h2net_v1_run\preflight\PREFLIGHT.json
. (Join-Path $PSScriptRoot '_common.ps1')
$checks = [ordered]@{}
$py = Get-Python
$checks.python = (& $py -c "import sys,numpy,scipy,pandas,yaml; print(sys.version.split()[0])" | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { Fail "Python dependencies missing: run .venv\Scripts\pip install -r requirements-lock.txt" }
$m = Get-Matlab
$checks.matlab = $m
$os = Get-CimInstance Win32_OperatingSystem
$checks.windows = "$($os.Caption) $($os.Version)"
$checks.ram_total_mb = [int]($os.TotalVisibleMemorySize / 1KB)
$checks.ram_free_mb = [int]($os.FreePhysicalMemory / 1KB)
$checks.disk_free_gb = [math]::Round((Get-Item $Repo).PSDrive.Free / 1GB, 1)
$problems = @()
if ($checks.ram_total_mb -lt 15000) { $problems += "physical RAM $($checks.ram_total_mb) MB < 15000 MB (a 16 GB machine is expected)" }
if ($checks.disk_free_gb -lt 20) { $problems += "free disk $($checks.disk_free_gb) GB < 20 GB" }
if ((Invoke-Py @('tools\governance\verify_frozen_hashes.py')) -ne 0) { $problems += 'frozen research hashes do not verify' }
if ((Invoke-Py @('tools\matlab\build_matlab_expectations.py', '--check')) -ne 0) { $problems += 'MATLAB expectations stale against the repository records' }
if ((Invoke-Py @('tools\simulation\extract_released_network.py', '--check')) -ne 0) { $problems += 'released models differ from the recorded extraction (check data\raw model hashes)' }
$checks.problems = $problems
$checks.overall = if ($problems.Count -eq 0) { 'PASS' } else { 'FAIL' }
New-Item -ItemType Directory -Force -Path (Join-Path $Run 'preflight') | Out-Null
$checks | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $Run 'preflight\PREFLIGHT.json')
if ($problems.Count) { $problems | ForEach-Object { Write-Host " - $_" }; Fail 'preflight (fix the items above and rerun)' }
Ok "preflight PASS (RAM $($checks.ram_total_mb) MB, disk $($checks.disk_free_gb) GB, MATLAB $m)"
