function raw = h2prism_validate_h2net_v1(runDir, stopTime_s)
%H2PRISM_VALIDATE_H2NET_V1  Physical-validation SIMULATIONS V2, V3, V4, V6 on the built H2Net v1 copies (grant (c) scope).
%   raw = h2prism_validate_h2net_v1('h2net_v1_run', 3600)          from the repository root
%   Gate: python tools/simulation/h2net_v1_gates.py check validate must be OPEN (decisions, executor, grant hashes, V2
%   targets, MATLAB readiness, BUILD_REPORT COMPLETE). Runs ONE simulation at a time, memory-guarded; writes RAW steady
%   values only (<runDir>/validation/VALIDATION_RAW.json). PASS/FAIL is decided by
%   tools/simulation/h2net_v1_validation.py against the targets and the thresholds of the decision record.
%   V5 needs a decided segmentation (S5) and V7 a separate grant: not run here. Status: IMPLEMENTED, UNVERIFIED IN MATLAB.
    if nargin < 2, stopTime_s = 3600; end
    root = pwd;
    py = getenv('H2PRISM_PYTHON'); if isempty(py), py = fullfile(root, '.venv', 'Scripts', 'python.exe'); end
    [st, txt] = system(sprintf('"%s" "%s" check validate', py, fullfile(root, 'tools', 'simulation', 'h2net_v1_gates.py')));
    assert(st == 0, 'h2prism:gate', 'validation gate closed:\n%s', txt);
    E = h2prism_load_expectations();
    S = jsondecode(fileread(fullfile(runDir, 'build', 'H2NET_V1_BUILD_SPEC_DECIDED.json')));
    T = jsondecode(fileread(fullfile(runDir, 'targets', 'V2_TARGETS.json')));
    outDir = fullfile(runDir, 'validation'); if ~exist(outDir, 'dir'), mkdir(outDir); end
    names = fieldnames(S.models);
    raw = struct('stop_time_s', stopTime_s, 'matlab', version, 'models', struct());
    for i = 1:numel(names)
        M = S.models.(names{i});
        if ~isfield(M, 'operations'), continue, end
        mdl = M.target_name;
        load_system(fullfile(runDir, 'build', 'models', [mdl '.slx']));
        c = onCleanup(@() close_system(mdl, 0));                     % never saved by validation
        pts = T.targets.(names{i}); if ~iscell(pts), pts = num2cell(pts); end
        demandVars = demandVariables(M); leakVars = leakVariables(M);
        rec = struct('V2', {{}}, 'V4', {{}}, 'V6', struct());
        for k = 1:numel(pts)
            p = pts{k};
            guard(E);
            setInputs(M, p, demandVars, leakVars, stopTime_s, '', 0);
            rec.V2{end + 1} = struct('demand_multiplier', p.demand_multiplier, 'values', finalValues(sim(mdl, 'StopTime', num2str(stopTime_s))));
        end
        nominal = pts{cellfun(@(q) abs(q.demand_multiplier - 1), pts) == min(cellfun(@(q) abs(q.demand_multiplier - 1), pts))};
        ops = M.operations; if ~iscell(ops), ops = num2cell(ops); end
        for k = 1:numel(ops)
            if strcmp(ops{k}.op, 'split_pipe_with_leak')
                guard(E);
                setInputs(M, nominal, demandVars, leakVars, stopTime_s, ops{k}.variable, ops{k}.v4_area_m2_for_2pct);
                rec.V4{end + 1} = struct('leak', ops{k}.id, 'area_m2', ops{k}.v4_area_m2_for_2pct, ...
                    'values', finalValues(sim(mdl, 'StopTime', num2str(stopTime_s))));
            end
        end
        guard(E);
        setInputs(M, nominal, demandVars, leakVars, stopTime_s, '', 0);
        rt = str2double(get_param(mdl, 'RelTol'));
        rec.V6 = struct('reltol_ref', rt, 'reltol_tight', rt / 10, ...
            'ref', finalValues(sim(mdl, 'StopTime', num2str(stopTime_s))), ...
            'tight', finalValues(sim(mdl, 'StopTime', num2str(stopTime_s), 'RelTol', num2str(rt / 10))));
        raw.models.(names{i}) = rec;
        clear c
    end
    fid = fopen(fullfile(outDir, 'VALIDATION_RAW.json'), 'w', 'n', 'UTF-8');
    cf = onCleanup(@() fclose(fid));
    fwrite(fid, jsonencode(raw, 'PrettyPrint', true), 'char');
end

function guard(E)
    [ok, m] = h2prism_memory_guard(E.memory_mb.minimum_available_between_models);
    assert(ok, 'h2prism:memory', 'stopping safely: %.0f MB available', m.available_mb);
end

function v = demandVariables(M)
    ops = M.operations; if ~iscell(ops), ops = num2cell(ops); end
    v = {};
    for k = 1:numel(ops)
        if isfield(ops{k}, 'variable') && startsWith(ops{k}.variable, 'h2_demand_'), v{end + 1} = ops{k}.variable; end %#ok<AGROW>
    end
end

function v = leakVariables(M)
    ops = M.operations; if ~iscell(ops), ops = num2cell(ops); end
    v = {};
    for k = 1:numel(ops)
        if strcmp(ops{k}.op, 'split_pipe_with_leak'), v{end + 1} = ops{k}.variable; end %#ok<AGROW>
    end
end

function setInputs(M, p, demandVars, leakVars, tEnd, leakOn, leakArea)
    t = [0; tEnd];
    for k = 1:numel(demandVars)
        outlet = erase(demandVars{k}, 'h2_demand_');
        val = demandOf(p, outlet);
        assignin('base', demandVars{k}, timeseries([val; val], t));
    end
    comp = p.compressors; if ~iscell(comp), comp = num2cell(comp); end
    for k = 1:numel(comp)
        assignin('base', ['h2_dp_' comp{k}.compressor], timeseries([comp{k}.dp_MPa; comp{k}.dp_MPa], t));
    end
    for k = 1:numel(leakVars)
        a = 0; if strcmp(leakVars{k}, leakOn), a = leakArea; end
        assignin('base', leakVars{k}, timeseries([a; a], t));
    end
end

function val = demandOf(p, outlet)
    % demand of an outlet at this target point, as used by the reference solver (V2_TARGETS.json demand_kg_s)
    val = p.demand_kg_s.(outlet);
end

function s = finalValues(out)
    % last value and drift over the last 10 % of every logged To Workspace variable
    s = struct();
    vars = out.who;
    for k = 1:numel(vars)
        ts = out.get(vars{k});
        if ~isa(ts, 'timeseries'), continue, end
        d = ts.Data(:); n = numel(d); i0 = max(1, floor(0.9 * n));
        s.(vars{k}) = struct('last', d(end), 'drift', abs(d(end) - d(i0)) / max(abs(d(end)), eps));
    end
end
