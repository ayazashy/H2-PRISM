function h = h2prism_sha256bytes(b)
%H2PRISM_SHA256BYTES  SHA-256 (FIPS 180-4) of a uint8 vector, pure MATLAB. Returns lower-case hex.
    K = uint32([ ...
        0x428a2f98 0x71374491 0xb5c0fbcf 0xe9b5dba5 0x3956c25b 0x59f111f1 0x923f82a4 0xab1c5ed5 ...
        0xd807aa98 0x12835b01 0x243185be 0x550c7dc3 0x72be5d74 0x80deb1fe 0x9bdc06a7 0xc19bf174 ...
        0xe49b69c1 0xefbe4786 0x0fc19dc6 0x240ca1cc 0x2de92c6f 0x4a7484aa 0x5cb0a9dc 0x76f988da ...
        0x983e5152 0xa831c66d 0xb00327c8 0xbf597fc7 0xc6e00bf3 0xd5a79147 0x06ca6351 0x14292967 ...
        0x27b70a85 0x2e1b2138 0x4d2c6dfc 0x53380d13 0x650a7354 0x766a0abb 0x81c2c92e 0x92722c85 ...
        0xa2bfe8a1 0xa81a664b 0xc24b8b70 0xc76c51a3 0xd192e819 0xd6990624 0xf40e3585 0x106aa070 ...
        0x19a4c116 0x1e376c08 0x2748774c 0x34b0bcb5 0x391c0cb3 0x4ed8aa4a 0x5b9cca4f 0x682e6ff3 ...
        0x748f82ee 0x78a5636f 0x84c87814 0x8cc70208 0x90befffa 0xa4506ceb 0xbef9a3f7 0xc67178f2]);
    H = uint32([0x6a09e667 0xbb67ae85 0x3c6ef372 0xa54ff53a 0x510e527f 0x9b05688c 0x1f83d9ab 0x5be0cd19]);
    b = uint8(b(:));
    L = numel(b) * 8;                                        % message length in bits (exact in double below 2^53)
    pad = mod(55 - numel(b), 64);
    lenBytes = zeros(8, 1, 'uint8');
    for i = 1:8
        lenBytes(9 - i) = uint8(mod(floor(L / 2^(8 * (i - 1))), 256));
    end
    m = [b; uint8(128); zeros(pad, 1, 'uint8'); lenBytes];
    words = reshape(m, 4, []);
    W32 = bitor(bitor(bitshift(uint32(words(1, :)), 24), bitshift(uint32(words(2, :)), 16)), ...
                bitor(bitshift(uint32(words(3, :)), 8), uint32(words(4, :))));
    nBlocks = numel(W32) / 16;
    W = zeros(1, 64, 'uint32');
    for blk = 1:nBlocks
        W(1:16) = W32((blk - 1) * 16 + (1:16));
        for t = 17:64
            s0 = bitxor(bitxor(rotr(W(t - 15), 7), rotr(W(t - 15), 18)), bitshift(W(t - 15), -3));
            s1 = bitxor(bitxor(rotr(W(t - 2), 17), rotr(W(t - 2), 19)), bitshift(W(t - 2), -10));
            W(t) = add32(W(t - 16), s0, W(t - 7), s1);
        end
        a = H(1); bb = H(2); c = H(3); d = H(4); e = H(5); f = H(6); g = H(7); hh = H(8);
        for t = 1:64
            S1 = bitxor(bitxor(rotr(e, 6), rotr(e, 11)), rotr(e, 25));
            ch = bitxor(bitand(e, f), bitand(bitcmp(e), g));
            T1 = add32(hh, S1, ch, K(t), W(t));
            S0 = bitxor(bitxor(rotr(a, 2), rotr(a, 13)), rotr(a, 22));
            mj = bitxor(bitxor(bitand(a, bb), bitand(a, c)), bitand(bb, c));
            T2 = add32(S0, mj);
            hh = g; g = f; f = e; e = add32(d, T1); d = c; c = bb; bb = a; a = add32(T1, T2);
        end
        H = [add32(H(1), a), add32(H(2), bb), add32(H(3), c), add32(H(4), d), ...
             add32(H(5), e), add32(H(6), f), add32(H(7), g), add32(H(8), hh)];
    end
    h = lower(reshape(dec2hex(H, 8)', 1, []));
end

function y = rotr(x, n)
    y = bitor(bitshift(x, -n), bitshift(x, 32 - n));          % uint32 shifts discard overflowed bits
end

function s = add32(varargin)
    acc = 0;
    for i = 1:nargin
        acc = acc + double(varargin{i});
    end
    s = uint32(mod(acc, 2^32));
end
