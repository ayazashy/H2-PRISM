function report = h2prism_write_report(outDir, fileName, kind, checks, extra)
%H2PRISM_WRITE_REPORT  Write <outDir>/<fileName> (JSON). overall = FAIL if any check FAILs, else PASS.
    if nargin < 5, extra = struct(); end
    st = {checks.status};
    report = struct('kind', kind, 'created', char(datetime('now', 'Format', 'yyyy-MM-dd''T''HH:mm:ssXXX', 'TimeZone', 'local')), ...
        'matlab_version', version, 'computer', computer, 'overall', 'PASS', ...
        'n_pass', sum(strcmp(st, 'PASS')), 'n_fail', sum(strcmp(st, 'FAIL')), 'n_warn', sum(strcmp(st, 'WARN')), ...
        'n_skip', sum(strcmp(st, 'SKIP')), 'checks', checks, 'extra', extra, ...
        'note', 'Engineering readiness evidence only. A successful load or compile is NOT physical validation.');
    if report.n_fail > 0, report.overall = 'FAIL'; end
    if ~exist(outDir, 'dir'), mkdir(outDir); end
    fid = fopen(fullfile(outDir, fileName), 'w', 'n', 'UTF-8');
    c = onCleanup(@() fclose(fid));
    fwrite(fid, jsonencode(report, 'PrettyPrint', true), 'char');
    fprintf('==> %s: %s (%d pass, %d fail, %d warn, %d skip) -> %s\n', kind, report.overall, report.n_pass, ...
        report.n_fail, report.n_warn, report.n_skip, fullfile(outDir, fileName));
end
