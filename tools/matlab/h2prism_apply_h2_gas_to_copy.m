function h2prism_apply_h2_gas_to_copy(copyModel, realGasSpecValue)
%H2PRISM_APPLY_H2_GAS_TO_COPY  H2Net v1 step S1 on a NEW model copy (integration path; NOT RUN by the readiness checks).
%   Sets the Gas Properties (G) block of an already-loaded H2Net v1 copy to the hash-verified normal-hydrogen tables.
%   Refuses unless ALL hold:
%     * copyModel starts with 'h2net_v1_' and its file is NOT under data/raw (never a released model);
%     * the H2Net v1 grant-bound files and the parameter file match their pinned hashes;
%     * PARAMETER_DECISIONS.yaml says status: DECIDED (owner decisions S2-S8 recorded);
%     * realGasSpecValue is given explicitly (the value selecting real gas, read from H2_INTEGRATION_REPORT.json
%       gas_spec options -- never guessed).
%   It does not save the model; the caller saves the COPY and records the parameter diff (action X05).
    assert(startsWith(copyModel, 'h2net_v1_'), 'h2prism:copy', 'only H2Net v1 copies (name prefix h2net_v1_)');
    f = get_param(copyModel, 'FileName');
    assert(~contains(strrep(f, '\', '/'), '/data/raw/'), 'h2prism:copy', 'refusing a file under data/raw');
    E = h2prism_load_expectations();
    root = pwd;
    b = E.h2net_v1_grant.bound; if iscell(b), b = [b{:}]; end
    for k = 1:numel(b)
        assert(strcmp(h2prism_sha256file(fullfile(root, b(k).file)), b(k).sha256), 'h2prism:grant', ...
            'grant-bound file changed (%s): the grant is void; a new request is required', b(k).file);
    end
    dec = fileread(fullfile(root, '06_audit_preparation', 'simulation', 'h2net_v1', 'PARAMETER_DECISIONS.yaml'));
    tok = regexp(dec, '(?m)^status:\s*(\S+)', 'tokens', 'once');
    assert(~isempty(tok) && strcmp(tok{1}, 'DECIDED'), 'h2prism:decisions', ...
        'PARAMETER_DECISIONS.yaml is not DECIDED: H2Net v1 copies must not be built yet');
    assert(nargin >= 2 && ~isempty(realGasSpecValue), 'h2prism:args', 'realGasSpecValue must be given explicitly');
    tabs = E.hydrogen_tables; if iscell(tabs), tabs = [tabs{:}]; end
    pm = tabs(endsWith({tabs.file}, '_params.m'));
    pf = fullfile(root, pm(1).file);
    assert(strcmp(h2prism_sha256file(pf), pm(1).sha256), 'h2prism:tables', 'hydrogen parameter file hash mismatch');
    H2 = evalH2(fileread(pf));
    gb = Simulink.ID.getFullName([copyModel ':' E.released_gas.block_sid]);
    set_param(gb, 'gas_spec', realGasSpecValue);
    fn = fieldnames(H2);
    for i = 1:numel(fn)
        set_param(gb, fn{i}, H2.(fn{i}));
    end
end

function H2 = evalH2(txt)
    eval(txt); %#ok<EVLDIR>
end
