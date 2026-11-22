# Redaction note (privacy)

On 2026-11-14 the project lead authorized a privacy redaction of branch `audit/preparation-integration` before its first push.

**What was changed:**
- In `ENVIRONMENT_REPORT.json` and `RUN_LOG.json` of this folder, every occurrence of the local Windows username was replaced by `<user>`. This applies to every historical version of both files.
- The same change was made in `../MATLAB_READINESS.md`, and its line in `../READINESS_ARTIFACT_HASHES.sha256` was recomputed.

**What was not changed:** all other content, including the check results, timestamps, memory figures, the PASS/FAIL outcome and the MATLAB version.

The pre-redaction history is kept locally in the backup branch `backup/audit-preparation-integration-pre-redaction` and is not pushed.
