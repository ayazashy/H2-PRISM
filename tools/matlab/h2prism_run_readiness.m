function ok = h2prism_run_readiness(outDir)
%H2PRISM_RUN_READINESS  Phases 1, 3 and 4 in sequence, in ONE MATLAB process, stopping at the first FAIL.
%   From the repository root:  addpath tools/matlab; h2prism_run_readiness('matlab_readiness/run1')
%   Then, from a shell:        python tools/matlab/check_matlab_reports.py matlab_readiness/run1
%   Nothing is simulated, saved or modified. Reports are released between phases.
    if nargin < 1 || isempty(outDir), error('h2prism:args', 'outDir is required'); end
    ok = false;
    r = h2prism_verify_environment(outDir);
    if ~strcmp(r.overall, 'PASS'), fprintf('STOP: environment verification failed.\n'); return, end
    clear r
    r = h2prism_smoke_test_models(outDir, true);
    if ~strcmp(r.overall, 'PASS'), fprintf('STOP: source-model smoke test failed.\n'); return, end
    clear r
    r = h2prism_check_h2_integration(outDir);
    ok = strcmp(r.overall, 'PASS');
    if ok, s = 'PASS'; else, s = 'FAIL'; end
    fprintf('READINESS (load / compile / interface only; NOT physical validation): %s\n', s);
end
