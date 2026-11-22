# H2-PRISM Web Operating & Release Guide

## Local Development & Verification
```powershell
# 1. Rebuild audited public replay bundles (from repo root)
python tools/data_pipeline/build_web_bundle.py
python -m pytest tools/data_pipeline/test_bundle.py -v

# 2. Typecheck, unit test, and build the web app
cd apps/web
npm ci
npm run typecheck
npm run test
npm run build
npm run dev
```

## GitHub Pages Deployment
- Workflow: `.github/workflows/deploy-pages.yml`
- Builds `apps/web/` with `VITE_BASE_PATH=/H2-PRISM/` on push to `main`.
- Target URL: `https://ayazashy.github.io/H2-PRISM/`

## Rollback
To roll back the live site without modifying research artifacts:
1. Identify the last known-good commit on `main`.
2. `git revert <bad_commit>` (or re-run `.github/workflows/deploy-pages.yml` from the tagged commit) and push `main`.
