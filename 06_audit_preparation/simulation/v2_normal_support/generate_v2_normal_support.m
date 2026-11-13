function generate_v2_normal_support(releaseNormalDir, designCsv, outDir, mode)
% GENERATE_V2_NORMAL_SUPPORT  Scope SIMULATION_GENERATION:V2_NORMAL_SUPPORT_DEV_AND_CONFIRMATION (package v3).
%   Run from the repository root. Authorization gate: tools/simulation/v2_normal_authorization.py (Python from the
%   environment variable H2PRISM_PYTHON, default 'python').
%     'preflight' calls the gate's non-consuming status check (must not be NOT_AUTHORIZED) and never simulates.
%     'run' ATOMICALLY CLAIMS the single authorized attempt through the gate before any output folder is populated
%           or any simulation starts. The claim is never released: success, failure or interruption all consume it.
%   NORMAL operating scenarios only (DESIGN.csv: 9 operating points x 3 released models). No events, no training,
%   no evaluation. Requires MATLAB R2025a or later (the released models were saved in R2025a, 25.1.0.2943329),
%   Simulink and Simscape (libraries used: fl_lib, nesl_utility, simulink). Simscape Fluids is not needed.
%
%   releaseNormalDir  folder holding the RELEASED Normal_HNetwork_gest_{center,down,up}.slx (read only, never saved)
%   designCsv         DESIGN.csv of this package (SHA-256 pinned in DESIGN.sha256)
%   outDir            new or empty folder OUTSIDE the release, e.g. data/generated/v2_normal_support
%   mode              'preflight' (default): copy, load, set and read back every parameter, check versions and
%                                  licences, write PREFLIGHT_REPORT.json; NO simulation, NO signal output
%                     'run'      : additionally simulate and export clean signals on the solver time grid
%
%   Parameters are set by block SID (identical in all three models):
%     59  PS Step  -> 'final_value'      : Pressure Source (G)3 pressure-rise set-point after t = 25 s [MPa]
%     241 PS Ramp  -> 'slope'            : Pressure Source (G)1 differential ramp (let-down element) [MPa/s]
%     213/222/312/215 Local Restriction (G)3..(G)6 -> 'restriction_area' : withdrawals G3..G6 [m^2]
%   A failed run writes <run>_FAILED.json (error identifier and message) and the function errors at the end; no
%   partial set may be post-processed or sealed (README, failure procedure).

    if nargin < 4, mode = 'preflight'; end
    assert(any(strcmp(mode, {'preflight', 'run'})), 'mode must be preflight or run');
    assert(~isMATLABReleaseOlderThan('R2025a'), 'MATLAB R2025a or later is required (models saved in R2025a)');
    assert(license('test', 'Simulink') && license('test', 'Simscape'), 'Simulink and Simscape licences are required');
    rel = char(java.io.File(releaseNormalDir).getCanonicalPath());
    out = char(java.io.File(outDir).getAbsolutePath());
    assert(~startsWith(out, rel), 'outDir must not be inside the release folder');
    if exist(outDir, 'dir'), d = dir(outDir); assert(numel(d) <= 2, 'outDir must be new or empty'); end
    py = getenv('H2PRISM_PYTHON'); if isempty(py), py = 'python'; end
    gate = fullfile(pwd, 'tools', 'simulation', 'v2_normal_authorization.py');
    assert(isfile(gate), 'run from the repository root: authorization gate not found');
    attemptId = '';
    if strcmp(mode, 'preflight')
        [st, txt] = system(sprintf('"%s" "%s" status', py, gate));
        assert(st == 0 && ~contains(txt, 'NOT_AUTHORIZED'), 'authorization gate: %s', strtrim(txt));
    else
        % atomic one-attempt claim BEFORE any simulation; refused if already claimed (consumed) or not active
        [st, txt] = system(sprintf('"%s" "%s" claim --out-dir "%s"', py, gate, out));
        assert(st == 0, 'authorization claim refused: %s', strtrim(txt));
        lines = splitlines(strtrim(txt)); claimRec = jsondecode(lines{end});
        attemptId = claimRec.attempt_id;
    end
    mkdir(outDir); mkdir(fullfile(outDir, 'development')); mkdir(fullfile(outDir, 'confirmation'));
    work = tempname; mkdir(work);
    D = readtable(designCsv, 'TextType', 'string');
    names = unique(D.model_name);
    relHash = containers.Map();
    for i = 1:numel(names)
        relHash(char(names(i))) = sha256file(fullfile(releaseNormalDir, char(names(i)) + ".slx"));
    end
    products = ver; prodList = arrayfun(@(p) sprintf('%s %s', p.Name, p.Version), products, 'UniformOutput', false);
    failures = {}; pre = struct('run', {}, 'ok', {}, 'message', {});
    for r = 1:height(D)
        row = D(r, :);
        mdl = char(row.model_name);
        run = sprintf('%s_%s', row.scenario_id, row.model);
        base = fullfile(outDir, char(row.partition), run);
        runDir = fullfile(work, run); mkdir(runDir);
        copyfile(fullfile(releaseNormalDir, [mdl '.slx']), fullfile(runDir, [mdl '.slx']));
        try
            if bdIsLoaded(mdl), close_system(mdl, 0); end
            load_system(fullfile(runDir, [mdl '.slx']));
            assert(startsWith(get_param(mdl, 'FileName'), runDir), 'loaded model is not the private copy');
            set_param(mdl, 'SolverType', 'Fixed-step', 'Solver', 'ode14x', 'FixedStep', num2str(row.fixed_step_s));
            assert(strcmp(get_param(mdl, 'StopTime'), '20000'), 'unexpected StopTime');
            setByS(mdl, '59', 'final_value', row.ps_step_final_value_MPa);
            setByS(mdl, '241', 'slope', row.ps_ramp_slope_MPa_per_s);
            for sid = {'213', '222', '312', '215'}
                setByS(mdl, sid{1}, 'restriction_area', row.withdrawal_restriction_area_m2);
            end
            if strcmp(mode, 'preflight')
                pre(end+1) = struct('run', run, 'ok', true, 'message', ''); %#ok<AGROW>
                close_system(mdl, 0);
                continue
            end
            simOut = sim(mdl);
            [T, logged] = exportSignals(simOut);
            assert(T.Timestamp(end) >= 19999, 'simulation did not reach t = 19999 s');
            writetable(T, [base '_clean_solver_grid.csv']);
            prov = struct('scenario_id', row.scenario_id, 'independence_group', row.independence_group, ...
                'partition', char(row.partition), 'model', row.model, 'model_name', mdl, ...
                'released_model_sha256', relHash(mdl), ...
                'ps_step_final_value_MPa', str2double(getByS(mdl, '59', 'final_value')), ...
                'ps_ramp_slope_MPa_per_s', str2double(getByS(mdl, '241', 'slope')), ...
                'withdrawal_restriction_area_m2', cellfun(@(s) str2double(getByS(mdl, s, 'restriction_area')), ...
                    {'213', '222', '312', '215'}), ...
                'solver', get_param(mdl, 'Solver'), 'fixed_step_s', str2double(get_param(mdl, 'FixedStep')), ...
                'stop_time', get_param(mdl, 'StopTime'), 'logged_variables', {logged}, ...
                'noise_seed', row.noise_seed, 'matlab_release', matlabRelease.Release, 'products', {prodList}, ...
                'generated_utc', char(datetime('now', 'TimeZone', 'UTC', 'Format', 'yyyy-MM-dd''T''HH:mm:ss''Z''')), ...
                'clean_solver_grid_csv_sha256', sha256file([base '_clean_solver_grid.csv']), ...
                'authorization_scope', 'SIMULATION_GENERATION:V2_NORMAL_SUPPORT_DEV_AND_CONFIRMATION', ...
                'package_version', 'v3', 'attempt_id', attemptId);
            writeJson([base '_provenance.json'], prov);
            close_system(mdl, 0);                 % never save
        catch err
            if bdIsLoaded(mdl), close_system(mdl, 0); end
            failures{end+1} = run; %#ok<AGROW>
            writeJson([base '_FAILED.json'], struct('run', run, 'identifier', err.identifier, 'message', err.message, ...
                'mode', mode, 'utc', char(datetime('now', 'TimeZone', 'UTC'))));
            if strcmp(mode, 'preflight')
                pre(end+1) = struct('run', run, 'ok', false, 'message', err.message); %#ok<AGROW>
            end
        end
    end
    for i = 1:numel(names)                    % the released models must be byte-identical afterwards
        assert(strcmp(relHash(char(names(i))), sha256file(fullfile(releaseNormalDir, char(names(i)) + ".slx"))), ...
               'released model changed: %s', names(i));
    end
    if strcmp(mode, 'preflight')
        writeJson(fullfile(outDir, 'PREFLIGHT_REPORT.json'), struct('matlab_release', matlabRelease.Release, ...
            'products', {prodList}, 'runs', pre, 'n_ok', sum([pre.ok]), 'n_failed', sum(~[pre.ok])));
    end
    assert(isempty(failures), 'failed runs: %s (see *_FAILED.json; follow the failure procedure)', strjoin(failures, ', '));
end

function setByS(mdl, sid, prm, val)
    h = Simulink.ID.getHandle([mdl ':' sid]);
    set_param(h, prm, num2str(val, '%.10g'));
    got = str2double(get_param(h, prm));
    assert(abs(got - val) <= 1e-12 * max(1, abs(val)), 'parameter %s of SID %s not set', prm, sid);
end

function v = getByS(mdl, sid, prm)
    v = get_param(Simulink.ID.getHandle([mdl ':' sid]), prm);
end

function [T, logged] = exportSignals(simOut)
    % The model's own logged sensors only (pressure_sensorN -> PSN, flow_sensorN -> MFSN), as the release scripts.
    v = simOut.who; logged = {};
    ps = sortNat(v(startsWith(v, 'pressure_sensor'))); fs = sortNat(v(startsWith(v, 'flow_sensor')));
    first = simOut.get(ps{1});
    T = table(first.Time(:), 'VariableNames', {'Timestamp'});
    for k = 1:numel(ps)
        s = simOut.get(ps{k}); assert(isequal(s.Time(:), T.Timestamp), 'time grids differ');
        T.(['PS' extractAfter(ps{k}, 'pressure_sensor')]) = reshape(squeeze(s.Data), [], 1); logged{end+1} = ps{k}; %#ok<AGROW>
    end
    for k = 1:numel(fs)
        s = simOut.get(fs{k}); assert(isequal(s.Time(:), T.Timestamp), 'time grids differ');
        T.(['MFS' extractAfter(fs{k}, 'flow_sensor')]) = reshape(squeeze(s.Data), [], 1); logged{end+1} = fs{k}; %#ok<AGROW>
    end
end

function out = sortNat(c)
    n = cellfun(@(s) str2double(regexp(s, '\d+$', 'match', 'once')), c);
    [~, i] = sort(n); out = c(i);
end

function writeJson(p, s)
    fid = fopen(p, 'w'); fwrite(fid, jsonencode(s, 'PrettyPrint', true)); fclose(fid);
end

function h = sha256file(p)
    md = java.security.MessageDigest.getInstance('SHA-256');
    fid = fopen(p, 'r'); b = fread(fid, inf, '*uint8'); fclose(fid);
    md.update(b);
    h = lower(reshape(dec2hex(typecast(md.digest(), 'uint8'))', 1, []));
end
