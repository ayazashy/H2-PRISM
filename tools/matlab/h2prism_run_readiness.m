function ok = h2prism_run_readiness(outDir)
%H2PRISM_RUN_READINESS  Phases 1, 3 and 4 in sequence, in ONE MATLAB process, stopping at the first FAIL.
%   From the repository root:  addpath tools/matlab; h2prism_run_readiness('matlab_readiness/run1')
%   Then, from a shell:        python tools/matlab/check_matlab_reports.py matlab_readiness/run1
%   Nothing is simulated, saved or modified. Reports are released between phases.
%   RUN_LOG.json is written at start and updated after every phase and on any error, so an interrupted or failed
%   run always leaves evidence of how far it got (working folder, memory, phase, error identifier and message).
    if nargin < 1 || isempty(outDir), error('h2prism:args', 'outDir is required'); end
    ok = false;
    if ~exist(outDir, 'dir'), mkdir(outDir); end
    L = struct('started', stamp(), 'cwd', pwd, 'matlab_version', version, 'memory_at_start', h2prism_memory_status(), ...
               'phases', {{}}, 'stopped_at', '', 'error', struct('identifier', '', 'message', '', 'stack', ''), 'finished', '');
    writeLog(outDir, L);
    try
        r = h2prism_verify_environment(outDir);
        L = phase(L, 'ENVIRONMENT', r.overall); writeLog(outDir, L);
        if ~strcmp(r.overall, 'PASS'), fprintf('STOP: environment verification failed.\n'); L.stopped_at = 'ENVIRONMENT'; finish(outDir, L); return, end
        clear r
        r = h2prism_smoke_test_models(outDir, true);
        L = phase(L, 'SOURCE_MODEL_SMOKE_TEST', r.overall); writeLog(outDir, L);
        if ~strcmp(r.overall, 'PASS'), fprintf('STOP: source-model smoke test failed.\n'); L.stopped_at = 'SOURCE_MODEL_SMOKE_TEST'; finish(outDir, L); return, end
        clear r
        r = h2prism_check_h2_integration(outDir);
        L = phase(L, 'H2_INTEGRATION', r.overall);
        ok = strcmp(r.overall, 'PASS');
    catch err
        L.error = struct('identifier', err.identifier, 'message', err.message, 'stack', stackText(err));
        L.stopped_at = 'ERROR';
        finish(outDir, L);
        rethrow(err);
    end
    finish(outDir, L);
    if ok, s = 'PASS'; else, s = 'FAIL'; end
    fprintf('READINESS (load / compile / interface only; NOT physical validation): %s\n', s);
end

function L = phase(L, name, overall)
    m = h2prism_memory_status();
    L.phases{end + 1} = struct('phase', name, 'overall', overall, 'at', stamp(), 'available_mb', m.available_mb, ...
                               'matlab_used_mb', m.matlab_used_mb);
end

function finish(outDir, L)
    L.finished = stamp();
    writeLog(outDir, L);
end

function writeLog(outDir, L)
    fid = fopen(fullfile(outDir, 'RUN_LOG.json'), 'w', 'n', 'UTF-8');
    if fid < 0, return, end
    c = onCleanup(@() fclose(fid));
    fwrite(fid, jsonencode(L, 'PrettyPrint', true), 'char');
end

function s = stamp()
    s = char(datetime('now', 'Format', 'yyyy-MM-dd''T''HH:mm:ssXXX', 'TimeZone', 'local'));
end

function s = stackText(err)
    s = strjoin(arrayfun(@(f) sprintf('%s:%d', f.name, f.line), err.stack, 'UniformOutput', false), ' <- ');
end
