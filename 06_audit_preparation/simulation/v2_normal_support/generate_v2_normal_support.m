function generate_v2_normal_support(releaseNormalDir, designCsv, outDir)
% GENERATE_V2_NORMAL_SUPPORT  Authorized scope: SIMULATION_GENERATION:V2_NORMAL_SUPPORT_DEV_AND_CONFIRMATION.
%   NORMAL operating scenarios only (DESIGN.csv, 9 points x 3 models). No events, no training, no evaluation.
%
%   releaseNormalDir  folder holding the RELEASED Normal_HNetwork_gest_{center,down,up}.slx (never modified)
%   designCsv         06_audit_preparation/simulation/v2_normal_support/DESIGN.csv (hash pinned in DESIGN.sha256)
%   outDir            empty output folder OUTSIDE the release (e.g. data/generated/v2_normal_support)
%
%   For each design row: copy the model to a private work folder, set the three factors by block SID, read every
%   value back, run with the released launcher's solver settings (ode14x, fixed step per model), export the CLEAN
%   signals with the model's OWN logged sensor list (no padding), and write a provenance JSON. The released model
%   files are never saved; their SHA-256 is recorded before and after the run and must be unchanged.

    assert(exist(outDir, 'dir') == 0 || numel(dir(outDir)) <= 2, 'outDir must be new or empty');
    mkdir(outDir); mkdir(fullfile(outDir, 'development')); mkdir(fullfile(outDir, 'confirmation'));
    work = tempname; mkdir(work);
    D = readtable(designCsv, 'TextType', 'string');
    names = unique(D.model_name);
    relHash = containers.Map();
    for i = 1:numel(names)
        relHash(char(names(i))) = sha256file(fullfile(releaseNormalDir, char(names(i)) + ".slx"));
    end
    addpath(work);
    for r = 1:height(D)
        row = D(r, :);
        mdl = char(row.model_name);
        src = fullfile(releaseNormalDir, [mdl '.slx']);
        run = sprintf('%s_%s', row.scenario_id, row.model);
        runDir = fullfile(work, run); mkdir(runDir);
        copyfile(src, fullfile(runDir, [mdl '.slx']));
        cd0 = cd(runDir); cleanup = onCleanup(@() cd(cd0));
        load_system(mdl);
        set_param(mdl, 'SolverType', 'Fixed-step', 'Solver', 'ode14x', 'FixedStep', num2str(row.fixed_step_s));
        setByS(mdl, '59', 'final_value', row.ps_step_final_value_MPa);
        setByS(mdl, '241', 'slope', row.ps_ramp_slope_MPa_per_s);
        for sid = ["213" "222" "312" "215"]
            setByS(mdl, char(sid), 'restriction_area', row.withdrawal_restriction_area_m2);
        end
        simOut = sim(mdl);
        [T, logged] = exportSignals(simOut);
        part = char(row.partition);
        base = fullfile(outDir, part, run);
        writetable(T, [base '_clean.csv']);
        prov = struct('scenario_id', row.scenario_id, 'independence_group', row.independence_group, ...
            'partition', part, 'model', row.model, 'model_name', mdl, ...
            'released_model_sha256', relHash(mdl), ...
            'ps_step_final_value_MPa', str2double(getByS(mdl, '59', 'final_value')), ...
            'ps_ramp_slope_MPa_per_s', str2double(getByS(mdl, '241', 'slope')), ...
            'withdrawal_restriction_area_m2', cellfun(@(s) str2double(getByS(mdl, s, 'restriction_area')), ...
                {'213', '222', '312', '215'}), ...
            'solver', get_param(mdl, 'Solver'), 'fixed_step_s', str2double(get_param(mdl, 'FixedStep')), ...
            'stop_time', get_param(mdl, 'StopTime'), 'logged_variables', {logged}, ...
            'noise_seed', row.noise_seed, 'matlab_version', version, ...
            'generated_utc', char(datetime('now', 'TimeZone', 'UTC', 'Format', 'yyyy-MM-dd''T''HH:mm:ss''Z''')), ...
            'clean_csv_sha256', sha256file([base '_clean.csv']), ...
            'authorization_scope', 'SIMULATION_GENERATION:V2_NORMAL_SUPPORT_DEV_AND_CONFIRMATION');
        fid = fopen([base '_provenance.json'], 'w'); fwrite(fid, jsonencode(prov, 'PrettyPrint', true)); fclose(fid);
        close_system(mdl, 0);                 % never save
        clear cleanup
    end
    for i = 1:numel(names)                    % the released models must be byte-identical afterwards
        assert(strcmp(relHash(char(names(i))), sha256file(fullfile(releaseNormalDir, char(names(i)) + ".slx"))), ...
               'released model changed: %s', names(i));
    end
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
    % Model's own logged sensors only (pressure_sensorN -> PSN, flow_sensorN -> MFSN), as the release scripts do.
    v = simOut.who; logged = {};
    ps = sort_nat(v(startsWith(v, 'pressure_sensor'))); fs = sort_nat(v(startsWith(v, 'flow_sensor')));
    first = simOut.get(ps{1});
    T = table(first.Time, 'VariableNames', {'Timestamp'});
    for k = 1:numel(ps)
        s = simOut.get(ps{k}); T.(['PS' extractAfter(ps{k}, 'pressure_sensor')]) = s.Data; logged{end+1} = ps{k}; %#ok<AGROW>
    end
    for k = 1:numel(fs)
        s = simOut.get(fs{k}); T.(['MFS' extractAfter(fs{k}, 'flow_sensor')]) = s.Data; logged{end+1} = fs{k}; %#ok<AGROW>
    end
end

function out = sort_nat(c)
    n = cellfun(@(s) str2double(regexp(s, '\d+$', 'match', 'once')), c);
    [~, i] = sort(n); out = c(i);
end

function h = sha256file(p)
    md = java.security.MessageDigest.getInstance('SHA-256');
    fid = fopen(p, 'r'); b = fread(fid, inf, '*uint8'); fclose(fid);
    md.update(b);
    h = lower(reshape(dec2hex(typecast(md.digest(), 'uint8'))', 1, []));
end
