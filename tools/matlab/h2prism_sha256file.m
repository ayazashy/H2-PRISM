function h = h2prism_sha256file(p)
%H2PRISM_SHA256FILE  Lower-case hex SHA-256 of a file's bytes (read only).
    fid = fopen(p, 'r');
    assert(fid > 0, 'h2prism:io', 'cannot open %s', p);
    c = onCleanup(@() fclose(fid));
    b = fread(fid, inf, '*uint8');
    md = java.security.MessageDigest.getInstance('SHA-256');
    if ~isempty(b), md.update(typecast(b, 'int8')); end
    d = typecast(md.digest(), 'uint8');
    h = lower(reshape(dec2hex(d, 2)', 1, []));
end
