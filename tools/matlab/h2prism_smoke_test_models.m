function report = h2prism_smoke_test_models(outDir, compileModels, modelNames)
%H2PRISM_SMOKE_TEST_MODELS  Phase 3: non-destructive compatibility smoke test of the six released source models.
%   report = h2prism_smoke_test_models(outDir)                   load + inspect + compile (update diagram), all six
%   report = h2prism_smoke_test_models(outDir, false)            load + inspect only
%   report = h2prism_smoke_test_models(outDir, true, {'Normal_HNetwork_gest_center'})   a subset
%   Run from the repository root after h2prism_verify_environment has PASSED.
%
%   Per model, ONE AT A TIME: memory guard -> verify the released file hash -> copy it to a temporary folder under a
%   new name -> load the COPY -> library links and callbacks -> Gas Properties (G) SID 4 parameters (active gas
%   specification) -> Pipe (G) friction parameters -> sensor blocks by SID and To Workspace variable names (output
%   schema) -> input parameter interface SIDs (normal models) -> solver settings -> optional update diagram (compile,
%   NOT a simulation) -> close WITHOUT saving -> delete the copy -> re-verify the released hash.
%   The released files are never loaded, modified or saved; nothing is simulated; no parameter value is changed.
%   A successful load/compile is NOT physical validation. Writes <outDir>/SMOKE_REPORT.json.
    if nargin < 1 || isempty(outDir), error('h2prism:args', 'outDir is required'); end
    if nargin < 2 || isempty(compileModels), compileModels = true; end
    E = h2prism_load_expectations();
    C = struct('id', {}, 'name', {}, 'status', {}, 'detail', {});
    root = pwd;
    detail = struct();
    models = E.models;
    if iscell(models), models = [models{:}]; end
    if nargin >= 3 && ~isempty(modelNames), models = models(ismember({models.name}, modelNames)); end
    assert(~isempty(models), 'h2prism:args', 'no model selected');
    stopped = '';

    for k = 1:numel(models)
        md = models(k);
        id = sprintf('M%d', k);
        [ok, mem] = h2prism_memory_guard(E.memory_mb.minimum_available_between_models);
        if ~ok && ~isnan(mem.available_mb)
            stopped = sprintf('stopped before %s: %.0f MB available < %d MB', md.name, mem.available_mb, ...
                E.memory_mb.minimum_available_between_models);
            C = h2prism_add_check(C, [id '.mem'], [md.name ': memory guard'], 'FAIL', stopped);
            break
        end
        if bdIsLoaded(md.name)
            C = h2prism_add_check(C, [id '.0'], [md.name ': not already loaded'], 'FAIL', ...
                'a model with the released name is loaded in this session; close it and restart MATLAB');
            continue
        end
        rel = fullfile(root, md.file);
        h0 = h2prism_sha256file(rel);
        d0 = dir(rel);
        C = h2prism_add_check(C, [id '.1'], [md.name ': released hash'], pass(strcmp(h0, md.sha256)), h0(1:16));
        if ~strcmp(h0, md.sha256), continue, end

        work = tempname; mkdir(work);
        copyName = ['smk_' md.name];
        copyFile = fullfile(work, [copyName '.slx']);
        copyfile(rel, copyFile);
        oldDir = cd(work);
        Simulink.fileGenControl('set', 'CacheFolder', work, 'CodeGenFolder', work);
        cleanup = onCleanup(@() restore(oldDir, copyName, work));
        info = struct('name', md.name, 'copy', copyName);
        try
            load_system(copyFile);
            C = h2prism_add_check(C, [id '.2'], [md.name ': load copy'], 'PASS', sprintf('loaded as %s', copyName));
        catch err
            C = h2prism_add_check(C, [id '.2'], [md.name ': load copy'], 'FAIL', err.message);
            clear cleanup; detail.(md.name) = info; continue
        end

        % dependencies: library links, callbacks
        li = libinfo(copyName);
        libs = unique({li.Library});
        unresolved = sum(strcmp({li.LinkStatus}, 'unresolved'));
        extraLibs = setdiff(libs, E.matlab.required_libraries);
        C = h2prism_add_check(C, [id '.3'], [md.name ': library links'], pass(unresolved == 0), ...
            sprintf('libraries {%s}; unresolved %d%s', strjoin(libs, ', '), unresolved, listIf(' ; not in expected list: ', extraLibs)));
        cb = {'PreLoadFcn', 'PostLoadFcn', 'InitFcn', 'StartFcn', 'StopFcn', 'CloseFcn'};
        cbv = cellfun(@(c) get_param(copyName, c), cb, 'UniformOutput', false);
        info.callbacks = cell2struct(cbv, cb, 2);
        nonEmpty = cb(~cellfun(@isempty, cbv));
        C = h2prism_add_check(C, [id '.4'], [md.name ': model callbacks'], ternary(isempty(nonEmpty), 'PASS', 'WARN'), ...
            listIf('non-empty (review): ', nonEmpty, 'none'));

        % active gas specification (released: expected perfect gas, R = 0.287)
        try
            gb = Simulink.ID.getFullName([copyName ':' E.released_gas.block_sid]);
            gp = dialogDump(gb);
            info.gas_block = struct('path', gb, 'reference', get_param(gb, 'ReferenceBlock'), 'parameters', gp);
            spec = ''; if isfield(gp, 'gas_spec'), spec = gp.gas_spec; end
            hasR = any(structfun(@(x) ischar(x) && abs(str2double(x) - E.released_gas.expected_R_kJ_per_kgK) < 1e-9, gp));
            C = h2prism_add_check(C, [id '.5'], [md.name ': active gas specification'], ...
                pass(strcmp(spec, E.released_gas.gas_spec_raw) && hasR), sprintf('%s: gas_spec=%s (%s); R=0.287 present=%d', ...
                get_param(gb, 'ReferenceBlock'), spec, enumText(gb, 'gas_spec'), hasR));
        catch err
            C = h2prism_add_check(C, [id '.5'], [md.name ': active gas specification'], 'FAIL', err.message);
        end

        % pipe friction parameters (recorded for X04; not judged)
        pipes = struct();
        for s = 1:numel(E.pipe_sids)
            try
                pb = Simulink.ID.getFullName([copyName ':' E.pipe_sids{s}]);
                pipes.(['sid_' E.pipe_sids{s}]) = dialogDump(pb);
            catch err
                pipes.(['sid_' E.pipe_sids{s}]) = struct('error', err.message);
            end
        end
        info.pipes = pipes;

        % sensors by SID and output schema (To Workspace variable names)
        sens = md.sensors; if iscell(sens), sens = [sens{:}]; end
        missing = {};
        for s = 1:numel(sens)
            try
                b = Simulink.ID.getFullName([copyName ':' sens(s).sid]);
                if ~contains(lower(get_param(b, 'Name')), 'sensor'), missing{end + 1} = [sens(s).sensor_id ' (not a sensor)']; end %#ok<AGROW>
            catch
                missing{end + 1} = [sens(s).sensor_id ' SID ' sens(s).sid]; %#ok<AGROW>
            end
        end
        C = h2prism_add_check(C, [id '.6'], [md.name ': sensor blocks by SID'], pass(isempty(missing)), ...
            sprintf('%d expected%s', numel(sens), listIf('; missing: ', missing)));
        tw = find_system(copyName, 'LookUnderMasks', 'all', 'FollowLinks', 'on', 'BlockType', 'ToWorkspace');
        vars = {}; fmts = {};
        if ~isempty(tw)
            vars = cellstr(get_param(tw, 'VariableName')); fmts = unique(cellstr(get_param(tw, 'SaveFormat')));
        end
        vars = sort(vars);
        expVars = sort({sens.variable});
        info.to_workspace = struct('variables', {vars}, 'save_format', {fmts});
        C = h2prism_add_check(C, [id '.7'], [md.name ': output schema'], pass(isequal(vars(:), expVars(:))), ...
            sprintf('To Workspace %d variables; expected %d%s%s', numel(vars), numel(expVars), ...
            listIf('; unexpected: ', setdiff(vars, expVars)), listIf('; missing: ', setdiff(expVars, vars))));

        % input parameter interface (normal models)
        pif = md.parameter_interface;
        if isempty(pif)
            C = h2prism_add_check(C, [id '.8'], [md.name ': parameter interface'], 'SKIP', 'no interface registered for anomalous models');
        else
            if iscell(pif), pif = [pif{:}]; end
            bad = {}; vals = struct();
            for s = 1:numel(pif)
                try
                    b = Simulink.ID.getFullName([copyName ':' pif(s).sid]);
                    vals.(['sid_' pif(s).sid]) = get_param(b, pif(s).parameter);
                catch err
                    bad{end + 1} = sprintf('SID %s %s: %s', pif(s).sid, pif(s).parameter, err.message); %#ok<AGROW>
                end
            end
            info.parameter_interface_values = vals;
            C = h2prism_add_check(C, [id '.8'], [md.name ': parameter interface'], pass(isempty(bad)), ...
                sprintf('%d parameters readable%s', numel(pif) - numel(bad), listIf('; ', bad)));
        end

        % solver settings (recorded, never changed)
        info.solver = struct('Solver', get_param(copyName, 'Solver'), 'RelTol', get_param(copyName, 'RelTol'), ...
            'AbsTol', get_param(copyName, 'AbsTol'), 'MaxStep', get_param(copyName, 'MaxStep'), ...
            'StopTime', get_param(copyName, 'StopTime'), 'SaveFormat', get_param(copyName, 'SaveFormat'));

        % compile (update diagram): not a simulation; checks Simscape network construction and parameters
        if compileModels
            t0 = tic;
            try
                set_param(copyName, 'SimulationCommand', 'update');
                C = h2prism_add_check(C, [id '.9'], [md.name ': update diagram'], 'PASS', sprintf('%.1f s', toc(t0)));
            catch err
                C = h2prism_add_check(C, [id '.9'], [md.name ': update diagram'], 'FAIL', err.message);
            end
        else
            C = h2prism_add_check(C, [id '.9'], [md.name ': update diagram'], 'SKIP', 'compile not requested');
        end
        mem2 = h2prism_memory_status();
        info.memory_after_mb = mem2.available_mb;
        clear cleanup                                   % closes the copy without saving, deletes it
        h1 = h2prism_sha256file(rel); d1 = dir(rel);
        C = h2prism_add_check(C, [id '.10'], [md.name ': released file unchanged'], pass(strcmp(h1, h0) && d1.datenum == d0.datenum), ...
            'hash and timestamp re-verified after the check');
        detail.(md.name) = info;
    end
    extra = struct('models', detail, 'compile', compileModels, 'stopped', stopped);
    report = h2prism_write_report(outDir, 'SMOKE_REPORT.json', 'SOURCE_MODEL_SMOKE_TEST', C, extra);
end

function restore(oldDir, copyName, work)
    if bdIsLoaded(copyName), close_system(copyName, 0); end   % 0 = do not save
    Simulink.fileGenControl('reset');
    cd(oldDir);
    if exist(work, 'dir'), rmdir(work, 's'); end
end

function s = pass(tf)
    if tf, s = 'PASS'; else, s = 'FAIL'; end
end

function s = ternary(c, a, b)
    if c, s = a; else, s = b; end
end

function s = listIf(prefix, items, emptyText)
    if nargin < 3, emptyText = ''; end
    if isempty(items), s = emptyText; else, s = [prefix strjoin(items, ', ')]; end
end

function p = dialogDump(blk)
    dp = get_param(blk, 'DialogParameters');
    p = struct();
    if isempty(dp), return, end
    f = fieldnames(dp);
    for i = 1:numel(f)
        try
            v = get_param(blk, f{i});
            if ischar(v) || isstring(v), p.(f{i}) = char(v); end
        catch
        end
    end
end

function s = enumText(blk, param)
    s = 'enum options not reported';
    try
        dp = get_param(blk, 'DialogParameters');
        if isfield(dp, param) && isfield(dp.(param), 'Enum') && ~isempty(dp.(param).Enum)
            s = ['options: ' strjoin(dp.(param).Enum, ' | ')];
        end
    catch
    end
end
