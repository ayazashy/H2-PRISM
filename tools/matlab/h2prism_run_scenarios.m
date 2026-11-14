function summary = h2prism_run_scenarios(runDir, maxRuns)
%H2PRISM_RUN_SCENARIOS  Dataset generation from SCENARIO_PLAN.json (gate 'dataset': separate scoped authorization).
%   summary = h2prism_run_scenarios('h2net_v1_run')            from the repository root; maxRuns optional (resume-safe)
%   ONE simulation at a time, memory-guarded. Each run writes <runDir>/dataset/raw/<run_id>.csv (time + logged channels,
%   resampled to the decided sample period) and a manifest line; a failed run is recorded as FAILED and the next run
%   continues. Existing outputs are never overwritten (resume). Class labels are NOT written here (LABELS.csv is kept
%   separately by the planner). Status: IMPLEMENTED, UNVERIFIED IN MATLAB.
    if nargin < 2, maxRuns = inf; end
    root = pwd;
    py = getenv('H2PRISM_PYTHON'); if isempty(py), py = fullfile(root, '.venv', 'Scripts', 'python.exe'); end
    [st, txt] = system(sprintf('"%s" "%s" check dataset', py, fullfile(root, 'tools', 'simulation', 'h2net_v1_gates.py')));
    assert(st == 0, 'h2prism:gate', 'dataset gate closed:\n%s', txt);
    E = h2prism_load_expectations();
    P = jsondecode(fileread(fullfile(runDir, 'scenarios', 'SCENARIO_PLAN.json')));
    runs = P.runs; if ~iscell(runs), runs = num2cell(runs); end
    rawDir = fullfile(runDir, 'dataset', 'raw'); if ~exist(rawDir, 'dir'), mkdir(rawDir); end
    man = fullfile(runDir, 'dataset', 'RUN_MANIFEST.jsonl');
    loaded = ''; done = 0; failed = 0;
    for k = 1:numel(runs)
        if done >= maxRuns, break, end
        r = runs{k};
        out = fullfile(rawDir, [r.run_id '.csv']);
        if isfile(out), continue, end
        [ok, m] = h2prism_memory_guard(E.memory_mb.minimum_available_between_models);
        if ~ok, appendJson(man, struct('run_id', r.run_id, 'status', 'STOPPED_MEMORY', 'available_mb', m.available_mb)); break, end
        if ~strcmp(loaded, r.model)
            if ~isempty(loaded), close_system(loaded, 0); end
            load_system(fullfile(runDir, 'build', 'models', [r.model '.slx'])); loaded = r.model;
        end
        t0 = tic;
        try
            sig = fieldnames(r.signals);
            for j = 1:numel(sig)
                pts = r.signals.(sig{j}); if iscell(pts), pts = cell2mat(cellfun(@(c) c(:)', pts, 'UniformOutput', false)); end
                assignin('base', sig{j}, timeseries(pts(:, 2), pts(:, 1)));
            end
            o = sim(r.model, 'StopTime', num2str(r.stop_time_s));
            writeCsv(out, o, r.sample_period_s, r.stop_time_s);
            appendJson(man, struct('run_id', r.run_id, 'status', 'COMPLETED', 'model', r.model, 'seconds', toc(t0), ...
                'solver', get_param(r.model, 'Solver'), 'reltol', get_param(r.model, 'RelTol'), 'matlab', version, ...
                'csv_sha256', h2prism_sha256file(out)));
            done = done + 1;
        catch err
            appendJson(man, struct('run_id', r.run_id, 'status', 'FAILED', 'error', err.message, 'seconds', toc(t0)));
            failed = failed + 1;
        end
    end
    if ~isempty(loaded), close_system(loaded, 0); end
    summary = struct('completed_now', done, 'failed_now', failed, 'planned', numel(runs));
    disp(summary);
end

function writeCsv(path, o, dt, T)
    t = (0:dt:T)'; vars = sort(o.who); M = t; head = {'time_s'};
    for k = 1:numel(vars)
        ts = o.get(vars{k});
        if ~isa(ts, 'timeseries'), continue, end
        M = [M, interp1(ts.Time, double(ts.Data(:)), t, 'linear', 'extrap')]; %#ok<AGROW>
        head{end + 1} = vars{k}; %#ok<AGROW>
    end
    fid = fopen(path, 'w'); c = onCleanup(@() fclose(fid));
    fprintf(fid, '%s\n', strjoin(head, ','));
    fprintf(fid, [repmat('%.9g,', 1, size(M, 2) - 1) '%.9g\n'], M');
end

function appendJson(path, s)
    fid = fopen(path, 'a', 'n', 'UTF-8'); c = onCleanup(@() fclose(fid));
    fprintf(fid, '%s\n', jsonencode(s));
end
