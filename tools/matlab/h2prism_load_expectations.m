function E = h2prism_load_expectations()
%H2PRISM_LOAD_EXPECTATIONS  Pinned values (tools/matlab/h2prism_matlab_expectations.json). Run from the repo root.
    p = fullfile(pwd, 'tools', 'matlab', 'h2prism_matlab_expectations.json');
    assert(isfile(p), 'h2prism:root', 'run from the repository root (expectations file not found: %s)', p);
    E = jsondecode(fileread(p));
end
