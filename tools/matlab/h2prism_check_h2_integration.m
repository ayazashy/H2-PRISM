function report = h2prism_check_h2_integration(outDir)
%H2PRISM_CHECK_H2_INTEGRATION  Phase 4: read-only check that the H2Net v1 hydrogen tables can be wired into a COPY.
%   report = h2prism_check_h2_integration(outDir)       run from the repository root after the smoke test PASSED.
%   - H2Net v1 grant: bound hashes unchanged (a change voids the grant; never reactivated here)
%   - build gate: PARAMETER_DECISIONS.yaml must say DECIDED before any H2Net copy is built (reported, not changed)
%   - loads a temporary copy of Normal_HNetwork_gest_center and checks that Gas Properties (G) exposes a dialog
%     parameter for every field of H2_REALGAS_TLU2_params.m and a real-gas specification option.
%   NO set_param, NO save, NO simulation. Writes <outDir>/H2_INTEGRATION_REPORT.json.
    if nargin < 1 || isempty(outDir), error('h2prism:args', 'outDir is required'); end
    E = h2prism_load_expectations();
    C = struct('id', {}, 'name', {}, 'status', {}, 'detail', {});
    root = pwd;
    b = E.h2net_v1_grant.bound; if iscell(b), b = [b{:}]; end
    okB = all(arrayfun(@(x) isfile(fullfile(root, x.file)) && strcmp(h2prism_sha256file(fullfile(root, x.file)), x.sha256), b));
    C = h2prism_add_check(C, 'I1', 'H2Net v1 grant-bound files', pass(okB), sprintf('%s (%s)', E.h2net_v1_grant.scope, E.h2net_v1_grant.status));
    dec = fileread(fullfile(root, '06_audit_preparation', 'simulation', 'h2net_v1', 'PARAMETER_DECISIONS.yaml'));
    tok = regexp(dec, '(?m)^status:\s*(\S+)', 'tokens', 'once');
    if isempty(tok), tok = {'MISSING'}; end
    gate = 'CLOSED'; if strcmp(tok{1}, 'DECIDED'), gate = 'OPEN'; end
    C = h2prism_add_check(C, 'I2', 'H2Net v1 build gate', 'SKIP', sprintf('PARAMETER_DECISIONS status %s -> build gate %s', tok{1}, gate));

    tabs = E.hydrogen_tables; if iscell(tabs), tabs = [tabs{:}]; end
    pm = tabs(endsWith({tabs.file}, '_params.m'));
    pf = fullfile(root, pm(1).file);
    okH = isfile(pf) && strcmp(h2prism_sha256file(pf), pm(1).sha256);
    C = h2prism_add_check(C, 'I3', 'H2 parameter file hash', pass(okH), pm(1).file);
    fields = {};
    if okH, H2 = evalH2(fileread(pf)); fields = fieldnames(H2); end

    models = E.models; if iscell(models), models = [models{:}]; end
    md = models(strcmp({models.name}, 'Normal_HNetwork_gest_center'));
    rel = fullfile(root, md.file);
    if ~strcmp(h2prism_sha256file(rel), md.sha256)
        C = h2prism_add_check(C, 'I4', 'released model hash', 'FAIL', md.file);
        report = h2prism_write_report(outDir, 'H2_INTEGRATION_REPORT.json', 'H2_INTEGRATION', C, struct('build_gate', gate));
        return
    end
    work = tempname; mkdir(work);
    copyName = 'h2chk_Normal_HNetwork_gest_center';
    copyfile(rel, fullfile(work, [copyName '.slx']));
    cleanup = onCleanup(@() restore(copyName, work));
    load_system(fullfile(work, [copyName '.slx']));
    gb = Simulink.ID.getFullName([copyName ':' E.released_gas.block_sid]);
    dp = get_param(gb, 'DialogParameters');
    names = fieldnames(dp);
    missing = setdiff(fields, names);
    C = h2prism_add_check(C, 'I4', 'Gas Properties (G) accepts every table field', pass(okH && isempty(missing)), ...
        sprintf('%d table fields; missing dialog parameters: %s', numel(fields), strjoin(missing, ', ')));
    opts = {};
    if isfield(dp, 'gas_spec') && isfield(dp.gas_spec, 'Enum'), opts = dp.gas_spec.Enum; end
    hasReal = any(contains(lower(opts), 'real'));
    C = h2prism_add_check(C, 'I5', 'real-gas specification option', pass(hasReal), ['gas_spec options: ' strjoin(opts, ' | ')]);
    clear cleanup
    extra = struct('build_gate', gate, 'gas_block_dialog_parameters', {names}, 'gas_spec_options', {opts});
    report = h2prism_write_report(outDir, 'H2_INTEGRATION_REPORT.json', 'H2_INTEGRATION', C, extra);
end

function H2 = evalH2(txt)
    eval(txt); %#ok<EVLDIR>   % hash-verified parameter file; defines struct H2
end

function restore(copyName, work)
    if bdIsLoaded(copyName), close_system(copyName, 0); end
    if exist(work, 'dir'), rmdir(work, 's'); end
end

function s = pass(tf)
    if tf, s = 'PASS'; else, s = 'FAIL'; end
end
