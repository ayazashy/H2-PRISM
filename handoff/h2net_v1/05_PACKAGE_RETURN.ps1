# 05 - Package everything that actually exists for Ahmed (also after an early stop). Prints the ZIP path and status.
. (Join-Path $PSScriptRoot '_common.ps1')
if ((Invoke-Py @('tools\simulation\h2net_v1_package_return.py')) -ne 0) { Fail 'packaging failed' }
Ok 'send the ZIP and its .zip.sha256 file from h2net_v1_run\return\ to Ahmed'
