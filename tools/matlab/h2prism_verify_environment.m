function report = h2prism_verify_environment(outDir)
%H2PRISM_VERIFY_ENVIRONMENT  Phase 1: read-only MATLAB environment verification for H2-PRISM / H2Net v1.
%   report = h2prism_verify_environment(outDir)     run from the repository root, e.g.
%       addpath tools/matlab; h2prism_verify_environment('matlab_readiness/<date>')
%   Checks release, products, licences, memory, parallel pool, Python interoperability, released .slx files and
%   hashes, hydrogen tables and hashes, H2Net v1 grant-bound hashes, required Simscape libraries.
%   Writes <outDir>/ENVIRONMENT_REPORT.json. Never opens, modifies or simulates any model.
    if nargin < 1 || isempty(outDir), error('h2prism:args', 'outDir is required'); end
    E = h2prism_load_expectations();
    C = struct('id', {}, 'name', {}, 'status', {}, 'detail', {});
    root = pwd;

    % E1 release
    old = isMATLABReleaseOlderThan(E.matlab.minimum_release);
    C = h2prism_add_check(C, 'E1', 'MATLAB release', pass(~old), sprintf('%s; minimum %s; models saved in %s', ...
        version, E.matlab.minimum_release, E.matlab.models_saved_in));

    % E2 products installed / E3 licences
    v = ver; names = {v.Name};
    for k = 1:numel(E.matlab.required_products)
        p = E.matlab.required_products{k};
        hit = any(strcmp(names, p));
        C = h2prism_add_check(C, sprintf('E2.%d', k), ['installed: ' p], pass(hit), versionOf(v, p));
    end
    lic = struct('MATLAB', 'MATLAB', 'Simulink', 'Simulink', 'Simscape', 'Simscape');
    for k = 1:numel(E.matlab.required_licenses)
        p = E.matlab.required_licenses{k};
        t = license('test', lic.(p)) == 1;
        co = false; msg = '';
        if t, [co, msg] = license('checkout', lic.(p)); end
        C = h2prism_add_check(C, sprintf('E3.%d', k), ['licence: ' p], pass(t && co == 1), ...
            sprintf('test=%d checkout=%d %s', t, co, strtrim(msg)));
    end

    % E4 memory
    m = h2prism_memory_status();
    if isnan(m.total_mb)
        C = h2prism_add_check(C, 'E4', 'physical memory', 'WARN', 'not reported on this platform; memory guard inactive');
    else
        okTotal = m.total_mb >= E.memory_mb.minimum_total;
        okAvail = m.available_mb >= E.memory_mb.minimum_available_to_start;
        st = 'PASS'; if ~okAvail, st = 'FAIL'; elseif ~okTotal, st = 'WARN'; end
        C = h2prism_add_check(C, 'E4', 'physical memory', st, sprintf(['total %.0f MB, available %.0f MB, MATLAB %.0f MB ' ...
            '(need >= %d MB available to start; close other applications if this fails)'], m.total_mb, m.available_mb, ...
            m.matlab_used_mb, E.memory_mb.minimum_available_to_start));
    end

    % E5 no parallel pool (one simulation process at a time)
    if any(strcmp(names, 'Parallel Computing Toolbox'))
        pool = gcp('nocreate');
        C = h2prism_add_check(C, 'E5', 'no parallel pool', pass(isempty(pool)), ...
            'Parallel Computing Toolbox installed; a pool must not be running (one simulation process, no parallel workers)');
    else
        C = h2prism_add_check(C, 'E5', 'no parallel pool', 'PASS', 'Parallel Computing Toolbox not installed');
    end

    % E6 Python interoperability (authorization gates are Python, called through system())
    py = getenv('H2PRISM_PYTHON');
    if isempty(py), py = fullfile(root, '.venv', 'Scripts', 'python.exe'); end
    if isfile(py)
        [s, out] = system(sprintf('"%s" -c "import sys, numpy, yaml; print(sys.version.split()[0])"', py));
        C = h2prism_add_check(C, 'E6', 'Python for authorization gates', pass(s == 0), sprintf('%s -> %s', py, strtrim(out)));
    else
        C = h2prism_add_check(C, 'E6', 'Python for authorization gates', 'FAIL', ...
            sprintf('not found: %s (create the repo .venv or set H2PRISM_PYTHON)', py));
    end

    % E7 released models present and unchanged
    for k = 1:numel(E.models)
        md = item(E.models, k);
        f = fullfile(root, md.file);
        if ~isfile(f)
            C = h2prism_add_check(C, sprintf('E7.%d', k), ['released model: ' md.name], 'FAIL', ['missing: ' md.file]);
            continue
        end
        h = h2prism_sha256file(f);
        C = h2prism_add_check(C, sprintf('E7.%d', k), ['released model: ' md.name], pass(strcmp(h, md.sha256)), ...
            sprintf('sha256 %s (expected %s)', h(1:16), md.sha256(1:16)));
    end

    % E8 hydrogen tables present and unchanged; parameter file evaluates to consistent grids
    for k = 1:numel(E.hydrogen_tables)
        t = item(E.hydrogen_tables, k);
        f = fullfile(root, t.file);
        ok = isfile(f) && strcmp(h2prism_sha256file(f), t.sha256);
        C = h2prism_add_check(C, sprintf('E8.%d', k), ['H2 table file: ' t.file(find(t.file == '/', 1, 'last') + 1:end)], pass(ok), ...
            sprintf('sha256 pinned %s', t.sha256(1:16)));
    end
    tabs = E.hydrogen_tables; if iscell(tabs), tabs = [tabs{:}]; end
    pm = tabs(endsWith({tabs.file}, '_params.m'));
    if ~isempty(pm) && isfile(fullfile(root, pm(1).file)) && strcmp(h2prism_sha256file(fullfile(root, pm(1).file)), pm(1).sha256)
        C = checkH2Struct(C, root);             % evaluated only after its hash matched
    else
        C = h2prism_add_check(C, 'E8.S', 'H2 parameter struct', 'FAIL', 'parameter file missing or hash mismatch: not evaluated');
    end

    % E9 H2Net v1 grant-bound files unchanged (a change voids the grant; never reactivated here)
    b = E.h2net_v1_grant.bound;
    for k = 1:numel(b)
        bb = item(b, k);
        ok = isfile(fullfile(root, bb.file)) && strcmp(h2prism_sha256file(fullfile(root, bb.file)), bb.sha256);
        C = h2prism_add_check(C, sprintf('E9.%d', k), ['H2Net v1 grant-bound: ' bb.file], pass(ok), ...
            sprintf('grant status %s, scope %s', E.h2net_v1_grant.status, E.h2net_v1_grant.scope));
    end

    % E10 required libraries load (libraries only; closed without saving)
    for k = 1:numel(E.matlab.required_libraries)
        L = E.matlab.required_libraries{k};
        try
            wasLoaded = bdIsLoaded(L);
            load_system(L);
            if ~wasLoaded, close_system(L, 0); end
            C = h2prism_add_check(C, sprintf('E10.%d', k), ['library: ' L], 'PASS', 'loads');
        catch err
            C = h2prism_add_check(C, sprintf('E10.%d', k), ['library: ' L], 'FAIL', err.message);
        end
    end

    extra = struct('memory', m, 'products', {strcat(names, {' '}, {v.Version})}, 'python', py);
    report = h2prism_write_report(outDir, 'ENVIRONMENT_REPORT.json', 'ENVIRONMENT', C, extra);
end

function s = pass(tf)
    if tf, s = 'PASS'; else, s = 'FAIL'; end
end

function s = versionOf(v, p)
    i = find(strcmp({v.Name}, p), 1);
    if isempty(i), s = 'not installed'; else, s = sprintf('%s %s', v(i).Version, v(i).Release); end
end

function x = item(a, k)
    if iscell(a), x = a{k}; else, x = a(k); end
end

function C = checkH2Struct(C, root)
    f = fullfile(root, '06_audit_preparation', 'simulation', 'h2net_v1', 'properties', 'H2_REALGAS_TLU2_params.m');
    try
        txt = fileread(f);
        H2 = evalH2(txt);
        T = str2num(H2.T_TLU2); p = str2num(H2.p_TLU2); %#ok<ST2NM>
        fn = setdiff(fieldnames(H2), {'T_TLU2', 'p_TLU2'});
        bad = {};
        for i = 1:numel(fn)
            v = str2num(H2.(fn{i})); %#ok<ST2NM>
            if ~isempty(v) && ~isscalar(v) && ~isequal(size(v), [numel(T), numel(p)]), bad{end + 1} = fn{i}; end %#ok<AGROW>
        end
        ok = numel(T) > 1 && numel(p) > 1 && isempty(bad) && all(diff(T) > 0) && all(diff(p) > 0);
        C = h2prism_add_check(C, 'E8.S', 'H2 parameter struct', pass(ok), sprintf('T %d points (%g-%g K), p %d points (%g-%g MPa), %d fields%s', ...
            numel(T), T(1), T(end), numel(p), p(1), p(end), numel(fn) + 2, mismatch(bad)));
    catch err
        C = h2prism_add_check(C, 'E8.S', 'H2 parameter struct', 'FAIL', err.message);
    end
end

function H2 = evalH2(txt)
    eval(txt); %#ok<EVLDIR>  % defines struct H2 (string-valued fields); file is hash-verified above
end

function s = mismatch(bad)
    if isempty(bad), s = ''; else, s = ['; wrong size: ' strjoin(bad, ', ')]; end
end
