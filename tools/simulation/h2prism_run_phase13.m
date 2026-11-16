function h2prism_run_phase13(root,prior,reference)
% Run approved controls before interventions and audit each before continuing.
directory = fileparts(mfilename('fullpath'));
repo = fileparts(fileparts(directory));
python = fullfile(repo,'.venv','Scripts','python.exe');
assert(isfile(python) && isfolder(prior) && isfolder(reference), ...
    'Phase 13 requires the repository Python environment and both audited references');
previous = getenv('PYTHONPATH');
restore = onCleanup(@() setenv('PYTHONPATH',previous)); %#ok<NASGU>
setenv('PYTHONPATH',fullfile(repo,'src'));
pairs = ["pressure_rival","alternate_profile"];
twins = ["normal","outlet_opening"];
for pair = pairs
    for twin = twins
        folder = fullfile(root,pair,twin);
        if ~isfile(fullfile(folder,'preflight.json'))
            h2prism_center_outlet_case('preflight',folder);
        end
    end
end
checked(sprintf('"%s" -m h2prism.phase13 approve "%s" "%s"',python,root,prior));
for pair = pairs
    for twin = twins
        folder = fullfile(root,pair,twin);
        log = fullfile(folder,'execution.log');
        if isfile(log)
            assert(contains(fileread(log),'=== PHASE 12 CAPTURE COMPLETED ==='), ...
                'Prior attempt lacks completion evidence. Preserved at %s',folder);
        else
            h2prism_center_outlet_case('execute',folder);
        end
        checked(sprintf('"%s" -m h2prism.phase13 validate "%s" "%s" --reference "%s" --pair %s --case %s', ...
            python,root,prior,reference,pair,twin));
    end
end
disp('=== ALL PHASE 13 CAPTURES ACCEPTED ===')
end

function checked(command)
[status,output] = system(command);
fprintf('%s',output);
assert(status==0,'Phase 13 approval or capture acceptance failed with exit status %d',status);
end
