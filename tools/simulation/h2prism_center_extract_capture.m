function h2prism_center_extract_capture(runDir, output)
% Read a completed SimulationOutput and save plain data. Does not load or simulate the SLX.
assert(~isfile(output),'Use a fresh extraction file');
file = fullfile(runDir,'center_raw.mat');
raw_sha256 = h2prism_center_sha256(file);
stored = load(file,'out');
out = stored.out;
capture = h2prism_center_collect_capture(out,true,'');
assert(strcmp(raw_sha256,h2prism_center_sha256(file)),'Raw capture checksum changed during extraction');
capture.raw_sha256 = raw_sha256;
save(output,'-struct','capture','-v7');
end
