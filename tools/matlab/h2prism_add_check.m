function checks = h2prism_add_check(checks, id, name, status, detail)
%H2PRISM_ADD_CHECK  Append one check. status: PASS | FAIL | WARN | SKIP.
    assert(any(strcmp(status, {'PASS', 'FAIL', 'WARN', 'SKIP'})), 'bad status');
    checks(end + 1) = struct('id', id, 'name', name, 'status', status, 'detail', detail);
    fprintf('[%s] %-4s %s: %s\n', status, id, name, detail);
end
