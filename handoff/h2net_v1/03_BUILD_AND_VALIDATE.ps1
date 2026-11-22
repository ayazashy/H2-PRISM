# 03 - V2 targets -> decided build spec -> build H2Net v1 copies -> validation simulations -> evaluation.
# Stops at the first closed gate or failure. Needs the owner decision record and EXECUTOR_DESIGNATION.yaml.
. (Join-Path $PSScriptRoot '_common.ps1')
if ((Invoke-Py @('tools\simulation\h2net_v1_gates.py', 'check', 'targets')) -ne 0) { Fail 'decision record incomplete (see above)' }
if ((Invoke-Py @('tools\simulation\h2net_v1_v2_targets.py', '--out', 'h2net_v1_run\targets\V2_TARGETS.json')) -ne 0) { Fail 'V2 targets refused' }
if ((Invoke-Py @('tools\simulation\h2net_v1_build_spec_decided.py')) -ne 0) { Fail 'decided build spec refused' }
if ((Invoke-Matlab "h2prism_build_h2net_v1('h2net_v1_run','foundation.enum.gas_spec.real_gas')" 'build') -ne 0) { Fail 'model build failed (h2net_v1_run\build\BUILD_REPORT.json names the failing operation)' }
if ((Invoke-Matlab "h2prism_validate_h2net_v1('h2net_v1_run', 3600)" 'validation') -ne 0) { Fail 'validation simulations failed (see the log)' }
if ((Invoke-Py @('tools\simulation\h2net_v1_validation.py')) -ne 0) { Fail 'physical validation NOT PASSED (h2net_v1_run\validation\VALIDATION_REPORT.json)' }
Ok 'H2Net v1 built and validated (V2, V3, V4, V5, V6, V8, D1 PASS)'
