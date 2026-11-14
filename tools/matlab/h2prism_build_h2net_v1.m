function report = h2prism_build_h2net_v1(outDir, readinessDir, realGasSpecValue)
%H2PRISM_BUILD_H2NET_V1  X05 stage 1: build H2Net v1 COPIES with the parameter-level changes of the build spec.
%   report = h2prism_build_h2net_v1(outDir, readinessDir, realGasSpecValue)      run from the repository root.
%   NOT RUN by the readiness tooling. Refuses (error, nothing written) unless ALL gates hold:
%     G1 06_audit_preparation/simulation/h2net_v1/PARAMETER_DECISIONS.yaml has status: DECIDED (owner record)
%     G2 candidate/H2NET_V1_BUILD_SPEC.json was generated from DECIDED values (status SPECIFICATION_DECIDED...)
%     G3 H2Net v1 grant-bound files (specification, gas_physics.py) match their pinned hashes
%     G4 the readiness reports in readinessDir pass tools/matlab/check_matlab_reports.py (exit 0)
%     G5 outDir is new or empty and not under data/raw; >= 1.5 GB physical memory available
%   Per model, ONE AT A TIME: verify the released hash -> copy to <outDir>/h2net_v1_<pos>_stage1.slx -> load the copy
%   -> apply parameter_ops (hydrogen tables via h2prism_apply_h2_gas_to_copy; set_param by SID, recording the released
%   and the new value) -> save the COPY -> close -> re-verify the released hash. structural_ops (demand sinks, end
%   sink, aftercoolers, leak branches, let-down) are NOT implemented here: they are written to BUILD_REPORT.json as a
%   pending worklist. A stage-1 copy is therefore NOT an H2Net v1 model and must not be simulated for data.
    if nargin < 3 || isempty(realGasSpecValue), error('h2prism:args', 'outDir, readinessDir and realGasSpecValue are required'); end
    root = pwd;
    E = h2prism_load_expectations();
    % G1
    dec = fileread(fullfile(root, '06_audit_preparation', 'simulation', 'h2net_v1', 'PARAMETER_DECISIONS.yaml'));
    tok = regexp(dec, '(?m)^status:\s*(\S+)', 'tokens', 'once');
    assert(~isempty(tok) && strcmp(tok{1}, 'DECIDED'), 'h2prism:decisions', 'G1: PARAMETER_DECISIONS.yaml is not DECIDED');
    % G2
    specFile = fullfile(root, '06_audit_preparation', 'simulation', 'h2net_v1', 'candidate', 'H2NET_V1_BUILD_SPEC.json');
    S = jsondecode(fileread(specFile));
    assert(startsWith(S.status, 'SPECIFICATION_DECIDED'), 'h2prism:spec', 'G2: build spec was generated from PROPOSED values');
    % G3
    b = E.h2net_v1_grant.bound; if iscell(b), b = [b{:}]; end
    for k = 1:numel(b)
        assert(strcmp(h2prism_sha256file(fullfile(root, b(k).file)), b(k).sha256), 'h2prism:grant', ...
            'G3: grant-bound file changed (%s): the grant is void', b(k).file);
    end
    % G4
    py = getenv('H2PRISM_PYTHON'); if isempty(py), py = fullfile(root, '.venv', 'Scripts', 'python.exe'); end
    [st, txt] = system(sprintf('"%s" "%s" "%s"', py, fullfile(root, 'tools', 'matlab', 'check_matlab_reports.py'), readinessDir));
    assert(st == 0, 'h2prism:readiness', 'G4: readiness not verified:\n%s', txt);
    % G5
    assert(~contains(strrep(char(java_free_abs(outDir)), '\', '/'), '/data/raw/'), 'h2prism:out', 'G5: outDir under data/raw');
    if exist(outDir, 'dir'), d = dir(outDir); assert(numel(d) <= 2, 'h2prism:out', 'G5: outDir must be new or empty'); end
    [okMem, mem] = h2prism_memory_guard(E.memory_mb.minimum_available_between_models);
    assert(okMem, 'h2prism:memory', 'G5: %.0f MB available', mem.available_mb);
    mkdir(outDir);

    models = fieldnames(S.models);
    rep = struct('model', {}, 'copy', {}, 'parameter_diff', {}, 'pending_structural_ops', {}, 'released_hash_ok', {});
    for i = 1:numel(models)
        M = S.models.(models{i});
        src = E.models; if iscell(src), src = [src{:}]; end
        srcRec = src(strcmp({src.name}, models{i}));
        rel = fullfile(root, srcRec.file);
        h0 = h2prism_sha256file(rel);
        assert(strcmp(h0, M.source_sha256), 'h2prism:hash', 'released model %s changed', models{i});
        copyName = ['h2net_v1_' M.position '_stage1'];
        copyFile = fullfile(outDir, [copyName '.slx']);
        copyfile(rel, copyFile);
        load_system(copyFile);
        diffs = struct('sid', {}, 'param', {}, 'released', {}, 'new', {});
        ops = M.parameter_ops; if ~iscell(ops), ops = num2cell(ops); end
        for k = 1:numel(ops)
            op = ops{k};
            switch op.op
                case 'apply_h2_tables'
                    h2prism_apply_h2_gas_to_copy(copyName, realGasSpecValue);
                    diffs(end + 1) = struct('sid', op.sid, 'param', 'gas (15 table fields)', 'released', 'perfect_gas', 'new', 'real_gas H2 tables'); %#ok<AGROW>
                case 'set_param'
                    blk = Simulink.ID.getFullName([copyName ':' op.sid]);
                    f = fieldnames(op.params);
                    for j = 1:numel(f)
                        before = get_param(blk, f{j});
                        set_param(blk, f{j}, op.params.(f{j}));
                        diffs(end + 1) = struct('sid', op.sid, 'param', f{j}, 'released', before, 'new', get_param(blk, f{j})); %#ok<AGROW>
                    end
                case 'keep'
                    % recorded only; the value stays as released
            end
        end
        save_system(copyName, copyFile);
        close_system(copyName, 0);
        h1 = h2prism_sha256file(rel);
        rep(end + 1) = struct('model', models{i}, 'copy', copyFile, 'parameter_diff', diffs, ...
            'pending_structural_ops', {M.structural_ops}, 'released_hash_ok', strcmp(h1, h0)); %#ok<AGROW>
    end
    report = struct('stage', 'STAGE1_PARAMETERS_ONLY (not an H2Net v1 model; do not simulate for data)', ...
        'created', char(datetime('now', 'Format', 'yyyy-MM-dd''T''HH:mm:ssXXX', 'TimeZone', 'local')), 'models', rep);
    fid = fopen(fullfile(outDir, 'BUILD_REPORT.json'), 'w', 'n', 'UTF-8');
    c = onCleanup(@() fclose(fid));
    fwrite(fid, jsonencode(report, 'PrettyPrint', true), 'char');
end

function p = java_free_abs(p)
    p = char(p);
    if ~(startsWith(p, filesep) || (numel(p) > 1 && p(2) == ':')), p = fullfile(pwd, p); end
end
