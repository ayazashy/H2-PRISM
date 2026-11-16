function h2prism_center_source_capture(runDir, stopTime)
% Use a checksum-verified isolated copy. Never save the model.
cd(runDir);
name = 'Normal_HNetwork_gest_center';
file = fullfile(runDir, [name '.slx']);
assert(isfile(file), 'Isolated Center model is missing');
assert(~isfile('center_setup.mat') && ~isfile('center_raw.mat'), 'Use a fresh output directory');
load_system('simulink');
load_system('fl_lib');
load_system(file);
cleanup = onCleanup(@() close_system(name, 0)); %#ok<NASGU>
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

% Capture the actual Simulink signals driving Simulink-PS converters. Store the
% port-to-log mapping; a source may drive more than one converter.
blocks = find_system(name,'LookUnderMasks','none','FollowLinks','off','BlockType','Reference');
inputMap = struct('block', {}, 'sourceBlock', {}, 'sourcePort', {}, 'logName', {});
ports = [];
for k = 1:numel(blocks)
    block = blocks{k};
    if ~contains(get_param(block,'SourceBlock'),'Simulink-PS')
        continue
    end
    ph = get_param(block,'PortHandles');
    for p = ph.Inport
        line = get_param(p,'Line');
        if line == -1
            continue
        end
        src = get_param(line,'SrcPortHandle');
        if src == -1
            continue
        end
        idx = find(ports == src, 1);
        if isempty(idx)
            ports(end+1) = src; %#ok<AGROW>
            idx = numel(ports);
            set_param(src,'DataLogging','on','DataLoggingNameMode','Custom', ...
                'DataLoggingName',sprintf('physical_input_%d',idx));
        end
        inputMap(end+1) = struct('block',block,'sourceBlock',get_param(src,'Parent'), ...
            'sourcePort',get_param(src,'PortNumber'), ... %#ok<AGROW>
            'logName',sprintf('physical_input_%d',idx));
    end
end

assert(~isempty(inputMap),'No controlled physical inputs were mapped for logging');
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
save('center_setup.mat','original','configured','inputMap','products','release','gasBlocks','gasSettings');

out = sim(name);
save('center_raw.mat','out','-v7.3');
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
