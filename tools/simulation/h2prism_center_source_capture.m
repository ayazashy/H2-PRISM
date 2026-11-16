function h2prism_center_source_capture(runDir, stopTime)
% Use a checksum-verified isolated copy. Never save the model.
assert(~isfile(fullfile(runDir,'center_setup.mat')) && ~isfile(fullfile(runDir,'center_raw.mat')), ...
    'Use a fresh output directory');
[inputMap, physicalInputs, guard] = h2prism_center_open_inputs(runDir); %#ok<NASGU>
name = 'Normal_HNetwork_gest_center';
keys = {'SolverType','Solver','FixedStep','StartTime','StopTime','RelTol','AbsTol', ...
        'LoadInitialState','InitialState','LoadExternalInput','ExternalInput'};
original = cell2struct(cellfun(@(p) get_param(name,p), keys, 'UniformOutput',false), keys, 2);

% The archived Center launcher sets the solver and step. An explicitly shorter
% interval is a diagnostic run and must not be treated as release reproduction.
set_param(name,'SolverType','Fixed-step','Solver','ode14x','FixedStep','0.8');
if nargin == 2
    set_param(name,'StopTime',char(string(stopTime)));
end
set_param(name,'SaveState','on','StateSaveName','center_states', ...
    'SaveFormat','Dataset','ReturnWorkspaceOutputs','on', ...
    'SignalLogging','on','SignalLoggingName','center_inputs', ...
    'SimscapeLogType','all','SimscapeLogName','center_simscape','SimscapeLogLimitData','off');

% Mark the two validated Simulink-side reservoir commands for logging.
for k = 1:numel(inputMap)
    set_param(inputMap(k).handle,'DataLogging','on','DataLoggingNameMode','Custom', ...
        'DataLoggingName',inputMap(k).logName);
end
inputMap = rmfield(inputMap,'handle');  % session-local handles are not provenance
configured = cell2struct(cellfun(@(p) get_param(name,p), keys, 'UniformOutput',false), keys, 2);
products = ver;
release = version;
gasBlocks = find_system(name,'LookUnderMasks','none','FollowLinks','off','RegExp','on','Name','^Gas Properties');
gasParameters = cellfun(@(b) get_param(b,'DialogParameters'), gasBlocks, 'UniformOutput',false);
gasSettings = cell(size(gasBlocks));
for k = 1:numel(gasBlocks)
    fields = fieldnames(gasParameters{k});
    entries = cellfun(@(p) get_param(gasBlocks{k},p), fields, 'UniformOutput',false);
    gasSettings{k} = cell2struct(entries, fields);
end
save('center_setup.mat','original','configured','inputMap','physicalInputs','products','release','gasBlocks','gasSettings');

out = sim(name);
save('center_raw.mat','out','-v7.3');
assert(~isempty(out.get('center_simscape')), 'Expected the full Simscape log for native physical inputs');
logged = out.get('center_inputs');
assert(all(ismember({inputMap.logName},logged.getElementNames())), 'Some mapped inputs were not logged');
names = [compose("pressure_sensor%d",1:10), compose("flow_sensor%d",1:3)];
for signal = names
    data = out.get(char(signal));
    assert(isvector(data.Data),'Expected one sensor value per timestamp');
    path = sprintf('%s.csv',char(signal));
    assert(~isfile(path),'Fresh sensor export path required');
    fid = fopen(path,'w');
    assert(fid ~= -1,'Cannot write sensor file');
    closeFile = onCleanup(@() fclose(fid));
    fprintf(fid,'Timestamp,Value\n');
    fprintf(fid,'%.17g,%.17g\n',[data.Time(:), data.Data(:)].');
    clear closeFile
end
end
