# 02 - MATLAB readiness (R0): environment, six-model smoke test, hydrogen integration, then the independent validator.
# Close other applications first. Memory limits are enforced by the MATLAB tooling and are never relaxed here.
. (Join-Path $PSScriptRoot '_common.ps1')
$dir = 'h2net_v1_run/readiness'
$code = Invoke-Matlab "ok = h2prism_run_readiness('$dir'); if ~ok, error('h2prism:readiness','readiness FAIL'); end" 'readiness'
if ((Invoke-Py @('tools\matlab\check_matlab_reports.py', $dir)) -ne 0) { Fail "R0 readiness NOT_READY (reports in $dir; RUN_LOG.json gives the stopping point)" }
if ($code -ne 0) { Fail 'MATLAB readiness run returned an error (see the log)' }
Ok 'R0 readiness verified by the independent validator'
