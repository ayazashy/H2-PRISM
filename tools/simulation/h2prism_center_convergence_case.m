function h2prism_center_convergence_case(runDir, baseline, step)
% Execute only a prepared NORMAL resolution case. Leave failed evidence intact.
manifest = jsondecode(fileread(fullfile(runDir,'case.json')));
assert(manifest.step_s == step && any(step == [0.4,0.2]),'Mismatch in prepared step');
assert(strcmp(h2prism_center_sha256(baseline),manifest.baseline_setup_sha256), ...
    'Baseline setup checksum changed');
file = fullfile(runDir,'Normal_HNetwork_gest_center.slx');
assert(strcmp(h2prism_center_sha256(file),manifest.model_sha256),'Prepared model checksum changed');
log = fullfile(runDir,'center_convergence_execution.log');
assert(~isfile(log) && ~isfile(fullfile(runDir,'center_solver_delta.mat')), ...
    'Use a fresh prepared case directory');
diary(log);
stopLog = onCleanup(@() diary('off')); %#ok<NASGU>
fprintf('START NORMAL at fixed step %.17g s\n',step);
try
    h2prism_center_source_capture(runDir,[],struct('step',step,'baseline',baseline));
    h2prism_center_extract_capture(runDir,fullfile(runDir,'center_extracted.mat'));
    assert(strcmp(h2prism_center_sha256(file),manifest.model_sha256),'Model checksum changed after run');
    fprintf('=== CONVERGENCE CAPTURE COMPLETED ===\n');
catch exception
    fprintf(2,'%s\n',getReport(exception,'extended','hyperlinks','off'));
    rethrow(exception)
end
end
