function h2prism_run_final_outlet_matrix(root)
% Compile and approve both rival pairs before running any trajectory.
directory = fileparts(mfilename('fullpath'));
repo = fileparts(fileparts(directory));
targets = ["sid312","sid215"];
twins = ["normal","outlet_opening"];
for target = targets
    for twin = twins
        folder = fullfile(root,target,twin);
        if ~isfile(fullfile(folder,'preflight.json'))
            h2prism_center_outlet_case('preflight',folder);
        end
    end
end
previous = getenv('PYTHONPATH');
restore = onCleanup(@() setenv('PYTHONPATH',previous)); %#ok<NASGU>
setenv('PYTHONPATH',fullfile(repo,'src'));
python = fullfile(repo,'.venv','Scripts','python.exe');
[status,output] = system(sprintf('"%s" -m h2prism.final_research approve "%s"',python,root));
assert(status==0,'Saved pair approval failed: %s',output);
for target = targets
    for twin = twins
        folder = fullfile(root,target,twin);
        log = fullfile(folder,'execution.log');
        if isfile(log)
            assert(contains(fileread(log),'=== PHASE 12 CAPTURE COMPLETED ===') && ...
                isfile(fullfile(folder,'center_extracted.mat')) && isfile(fullfile(folder,'outlet_evidence.mat')), ...
                'A prior attempt lacks completion evidence: %s',folder);
        else
            fprintf('RUN %s / %s\n',target,twin);
            h2prism_center_outlet_case('execute',folder);
        end
    end
end
disp('=== CENTER RIVAL MATRIX COMPLETED ===')
end
