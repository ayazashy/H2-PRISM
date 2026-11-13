function h = h2prism_sha256file(p)
%H2PRISM_SHA256FILE  Lower-case hex SHA-256 of a file's bytes (read only).
%   Pure MATLAB (FIPS 180-4): MATLAB R2026b ships without a Java runtime by default, so java.security cannot be
%   assumed. Validated by h2prism_sha256_selftest (FIPS known-answer vectors) and, in every readiness run, by matching
%   the Python-computed pinned hashes of the released models and hydrogen tables.
    fid = fopen(p, 'r');
    assert(fid > 0, 'h2prism:io', 'cannot open %s', p);
    c = onCleanup(@() fclose(fid));
    b = fread(fid, inf, '*uint8');
    h = h2prism_sha256bytes(b);
end
