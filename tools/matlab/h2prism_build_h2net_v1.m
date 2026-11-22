function report = h2prism_build_h2net_v1(runDir, realGasSpecValue)
%H2PRISM_BUILD_H2NET_V1  X05: build the H2Net v1 COPIES from the DECIDED build spec (all parameter and structural ops).
%   report = h2prism_build_h2net_v1(runDir, realGasSpecValue)   from the repository root, e.g.
%       h2prism_build_h2net_v1('h2net_v1_run', 'foundation.enum.gas_spec.real_gas')
%   Gate (refuses before touching anything): python tools/simulation/h2net_v1_gates.py check validate must report only
%   the missing BUILD_REPORT (i.e. decisions, executor, grant hashes, V2 targets and MATLAB readiness all satisfied).
%   Per model, ONE AT A TIME: verify the released hash -> copy to <runDir>/build/models/h2net_v1_<pos>.slx -> load the
%   copy -> hydrogen tables -> every structural / parameter op of the spec -> check expected logging variables ->
%   update diagram (compile) -> save the COPY -> re-verify the released hash. ANY failure: the copy is closed WITHOUT
%   saving and deleted, BUILD_REPORT.json says FAILED with the failing op, and the function errors.
%   Status: IMPLEMENTED, UNVERIFIED IN MATLAB. Nothing is simulated here.
    if nargin < 2 || isempty(realGasSpecValue), error('h2prism:args', 'runDir and realGasSpecValue are required'); end
    root = pwd;
    py = getenv('H2PRISM_PYTHON'); if isempty(py), py = fullfile(root, '.venv', 'Scripts', 'python.exe'); end
    [st, txt] = system(sprintf('"%s" "%s" check validate', py, fullfile(root, 'tools', 'simulation', 'h2net_v1_gates.py')));
    lines = splitlines(strtrim(txt)); probs = lines(startsWith(strtrim(lines), '- '));
    probs = probs(~contains(probs, 'BUILD_REPORT'));
    assert(st == 0 || isempty(probs), 'h2prism:gate', 'build gate closed:\n%s', strjoin(probs, newline));
    E = h2prism_load_expectations();
    [okMem, mem] = h2prism_memory_guard(E.memory_mb.minimum_available_between_models);
    assert(okMem, 'h2prism:memory', '%.0f MB available', mem.available_mb);
    specFile = fullfile(runDir, 'build', 'H2NET_V1_BUILD_SPEC_DECIDED.json');
    S = jsondecode(fileread(specFile));
    assert(strcmp(S.status, 'SPECIFICATION_DECIDED'), 'h2prism:spec', 'spec not generated from the decision record');
    outDir = fullfile(runDir, 'build', 'models');
    if ~exist(outDir, 'dir'), mkdir(outDir); end
    src = E.models; if iscell(src), src = [src{:}]; end
    names = fieldnames(S.models);
    rep = struct('model', {}, 'copy', {}, 'copy_sha256', {}, 'diff', {}, 'missing_log_variables', {}, 'released_hash_ok', {});
    status = 'COMPLETE'; failure = '';
    for i = 1:numel(names)
        M = S.models.(names{i});
        if ~isfield(M, 'operations'), status = 'INCOMPLETE'; failure = sprintf('%s: %s', names{i}, M.status); continue, end
        rel = fullfile(root, src(strcmp({src.name}, names{i})).file);
        h0 = h2prism_sha256file(rel);
        assert(strcmp(h0, M.source_sha256), 'h2prism:hash', 'released model %s changed', names{i});
        copyName = M.target_name; copyFile = fullfile(outDir, [copyName '.slx']);
        assert(~isfile(copyFile), 'h2prism:out', '%s exists; use a new runDir', copyFile);
        copyfile(rel, copyFile);
        try
            load_system(copyFile);
            h2prism_apply_h2_gas_to_copy(copyName, realGasSpecValue);
            diffs = h2prism_apply_structural_ops(copyName, M.operations);
            tw = find_system(copyName, 'LookUnderMasks', 'all', 'BlockType', 'ToWorkspace');
            have = cellstr(get_param(tw, 'VariableName'));
            missing = setdiff(cellstr(M.expected_log_variables), have);
            assert(isempty(missing), 'h2prism:log', 'missing logging variables: %s', strjoin(missing, ', '));
            set_param(copyName, 'SimulationCommand', 'update');
            save_system(copyName, copyFile);
            close_system(copyName, 0);
        catch err
            if bdIsLoaded(copyName), close_system(copyName, 0); end
            if isfile(copyFile), delete(copyFile); end
            status = 'FAILED'; failure = sprintf('%s: %s', names{i}, err.message);
            writeReport(runDir, status, failure, rep, S);
            rethrow(err);
        end
        rep(end + 1) = struct('model', names{i}, 'copy', copyFile, 'copy_sha256', h2prism_sha256file(copyFile), 'diff', diffs, ...
            'missing_log_variables', {{}}, 'released_hash_ok', strcmp(h2prism_sha256file(rel), h0)); %#ok<AGROW>
        assert(rep(end).released_hash_ok, 'h2prism:hash', 'released model changed during the build');
    end
    report = writeReport(runDir, status, failure, rep, S);
end

function r = writeReport(runDir, status, failure, rep, S)
    r = struct('status', status, 'failure', failure, 'decisions_sha256', S.decisions_sha256, 'models', rep, ...
        'created', char(datetime('now', 'Format', 'yyyy-MM-dd''T''HH:mm:ssXXX', 'TimeZone', 'local')), 'matlab', version, ...
        'note', 'COMPLETE = every op applied, logging channels present, diagram compiles. Not physical validation.');
    fid = fopen(fullfile(runDir, 'build', 'BUILD_REPORT.json'), 'w', 'n', 'UTF-8');
    c = onCleanup(@() fclose(fid));
    fwrite(fid, jsonencode(r, 'PrettyPrint', true), 'char');
end
