# 04 - Dataset generation. Requires gate 'dataset': validation PASS, Faisal's methods review with a cited noise model,
# and a separate scoped authorization AUTH_H2NET_V1_DATASET.yaml. Resume-safe; one simulation at a time.
. (Join-Path $PSScriptRoot '_common.ps1')
if ((Invoke-Py @('tools\simulation\h2net_v1_gates.py', 'check', 'dataset')) -ne 0) { Fail 'dataset generation is not authorized or not validated (see above)' }
if ((Invoke-Py @('tools\simulation\h2net_v1_scenarios.py', 'plan')) -ne 0) { Fail 'scenario plan refused or failed its independence / shortcut checks' }
if ((Invoke-Matlab "h2prism_run_scenarios('h2net_v1_run')" 'scenarios') -ne 0) { Fail 'scenario runner error (partial outputs kept; rerunning resumes)' }
if ((Invoke-Py @('tools\simulation\h2net_v1_scenarios.py', 'noise')) -ne 0) { Fail 'noise step refused' }
Ok 'authorized scenarios generated (h2net_v1_run\dataset\RUN_MANIFEST.jsonl)'
