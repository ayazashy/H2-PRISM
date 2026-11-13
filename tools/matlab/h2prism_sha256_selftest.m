function ok = h2prism_sha256_selftest()
%H2PRISM_SHA256_SELFTEST  FIPS 180-4 known-answer vectors for h2prism_sha256bytes (empty, 'abc', two-block message).
    v = {'', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'; ...
         'abc', 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'; ...
         'abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq', ...
         '248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1'};
    ok = true;
    for i = 1:size(v, 1)
        ok = ok && strcmp(h2prism_sha256bytes(uint8(v{i, 1})), v{i, 2});
    end
end
