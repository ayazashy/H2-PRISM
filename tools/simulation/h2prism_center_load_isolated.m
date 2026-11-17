function [plan, file, guard] = h2prism_center_load_isolated(runDir)
% Load only the checksum-pinned isolated copy and close it without saving.
toolsDir = fileparts(mfilename('fullpath'));
plan = jsondecode(fileread(fullfile(toolsDir, 'center_input_plan.json')));
name = plan.model;
runDir = canonical(runDir);
repo = canonical(fileparts(fileparts(toolsDir)));
assert(~startsWith([runDir filesep],[repo filesep],'IgnoreCase',ispc), ...
    'Use an isolated output directory outside the repository');
file = fullfile(runDir, [name '.slx']);
assert(isfile(file) && ~bdIsLoaded(name), 'A fresh isolated copy and unloaded Center model are required');
assert(strcmp(file, canonical(file)), 'The model may not be a file alias');
actual = h2prism_center_sha256(file);
assert(strcmp(actual,plan.sha256), 'Center SLX checksum changed; review the input plan');

previousDir = pwd;
cd(runDir);
guard = onCleanup(@() closeAndRestore(name,previousDir));
load_system('simulink');
load_system('fl_lib');
load_system(file);
assert(strcmp(canonical(get_param(name,'FileName')),file), ...
    'Loaded Center model is not the isolated copy');
end

function closeAndRestore(name,previousDir)
restoreDir = onCleanup(@() cd(previousDir)); %#ok<NASGU>
if bdIsLoaded(name)
    close_system(name,0);
end
end

function path = canonical(value)
entry = java.io.File(value);
path = char(entry.getCanonicalPath());
end
