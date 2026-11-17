function h2prism_run_command_delay(root,reference)
% Compile and compare the twins, then validate each before proceeding.
directory = fileparts(mfilename('fullpath'));
repo = fileparts(fileparts(directory));
python = fullfile(repo,'.venv','Scripts','python.exe');
previous = getenv('PYTHONPATH');
restore = onCleanup(@() setenv('PYTHONPATH',previous)); %#ok<NASGU>
setenv('PYTHONPATH',fullfile(repo,'src'));
cases = ["normal","outlet_opening"];
assert(~isfile(fullfile(root,'approval.json')), 'Use a fresh unapproved pilot');
for name = cases
    folder = fullfile(root,name);
    assert(~isfile(fullfile(folder,'execution.log')), 'Prior evidence exists');
    if ~isfile(fullfile(folder,'preflight.json'))
        h2prism_center_outlet_case('preflight',folder);
    end
end
checked(sprintf('"%s" -m h2prism.phase13_command_delay approve "%s"',python,root));
for name = cases
    folder = fullfile(root,name);
    h2prism_center_outlet_case('execute_diagnostic',folder);
    checked(sprintf('"%s" -m h2prism.phase13_command_delay validate "%s" --reference "%s" --case %s', ...
        python,root,reference,name));
end
end

function checked(command)
[status,output] = system(command);
fprintf('%s',output);
assert(status==0,'Pilot verification failed with exit status %d',status);
end
