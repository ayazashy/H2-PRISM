function sha256 = h2prism_center_sha256(file)
% Hash the source bytes without opening the model.
fid = fopen(file,'rb');
assert(fid ~= -1, 'Cannot read isolated source');
closeFile = onCleanup(@() fclose(fid));
bytes = fread(fid,Inf,'*uint8');
clear closeFile
digest = java.security.MessageDigest.getInstance('SHA-256');
digest.update(typecast(bytes,'int8'));
sha256 = lower(reshape(dec2hex(typecast(digest.digest(),'uint8'),2).',1,[]));
end
