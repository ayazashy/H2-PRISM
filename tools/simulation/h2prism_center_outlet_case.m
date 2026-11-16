function h2prism_center_outlet_case(action, caseDir)
% Build one isolated twin, or run the exact approved saved twin.
entry = java.io.File(caseDir);
caseDir = char(entry.getCanonicalPath());
designFile = fullfile(caseDir,'design.json');
spec = jsondecode(fileread(designFile));
assert(any(strcmp(spec.case,{'normal','outlet_opening'})),'Unsupported case');
original = fullfile(caseDir,'Normal_HNetwork_gest_center.slx');
derived = fullfile(caseDir,'Center_phase12.slx');
assert(strcmp(h2prism_center_sha256(original),spec.source_sha256),'Source checksum mismatch');
if strcmp(action,'preflight')
    preflight(caseDir,original,derived,spec);
elseif strcmp(action,'execute')
    execute(caseDir,derived,spec,designFile);
else
    error('Expected preflight or execute');
end
end

function preflight(caseDir,original,derived,spec)
receipt = fullfile(caseDir,'preflight.json');
assert(~isfile(derived) && ~isfile(receipt) && ~bdIsLoaded('Center_phase12'), ...
    'Use a fresh prepared case directory and close Center_phase12');
[inputMap,~,guard] = h2prism_center_open_inputs(caseDir); %#ok<ASGLU>
model = 'Normal_HNetwork_gest_center';
restriction = Simulink.ID.getHandle([model ':' spec.location.restriction_sid]);
boundary = Simulink.ID.getHandle([model ':' spec.location.reservoir_sid]);
assert(strcmp(get_param(boundary,'pressure_spec'),'foundation.enum.pressure_spec.atmospheric'), ...
    'Atmospheric pressure selection changed');
assert(strcmp(get_param(restriction,'LinkStatus'),'resolved') && ...
    strcmp(get_param(restriction,'restriction_type'),'foundation.enum.restriction_type.fixed') && ...
    strcmp(get_param(restriction,'restriction_area_unit'),'m^2') && ...
    str2double(get_param(restriction,'restriction_area')) == str2double(spec.area.initial_value), ...
    'Nominal outlet configuration differs');
assert(strcmp(get_param(restriction,'min_area_unit'),'m^2') && ...
    strcmp(get_param(restriction,'max_area_unit'),'m^2') && ...
    str2double(get_param(restriction,'min_area')) == str2double(spec.area.min) && ...
    str2double(get_param(restriction,'max_area')) == str2double(archivedMaximum(spec)),'Archived area limits changed');
assert(strcmp(get_param(Simulink.ID.getHandle([model ':7']),'UseLocalSolver'),'off'), ...
    'Unexpected local solver policy');
assertPath(model,restriction,spec.location);
exempt = [];
if isfield(spec,'overlay')
    exempt = [Simulink.ID.getHandle([model ':' spec.overlay.producer_sid]), ...
        Simulink.ID.getHandle([model ':' spec.overlay.receiver_sid])];
end
before = existingBlocks(model,restriction,exempt);
fixedKeys = {'restriction_area','restriction_area_unit','min_area','max_area','area','area_unit','Cd','B_lam'};
restrictionConstants = cellfun(@(key) get_param(restriction,key),fixedKeys,'UniformOutput',false);
area = str2double([string(spec.area.initial_value),string(spec.area.normal_final),string(spec.area.intervention_final)]);
bounds = str2double([string(spec.area.min),string(spec.area.max)]);
constantArea = isfield(spec,'overlay') && strcmp(spec.overlay.role,'internal_pressure');
assert(all(isfinite(area)) && all(area >= bounds(1) & area <= bounds(2)) && ...
    area(1) == area(2) && ((constantArea && area(3) == area(1)) || (~constantArea && area(3) > area(1))) && strcmp(spec.area.area_unit,'m^2') && ...
    strcmp(spec.area.time_unit,'s'),'Invalid design area or units');
set_param(restriction,'restriction_type','foundation.enum.restriction_type.variable');
if isfield(spec.area,'source_max')
    set_param(restriction,'max_area',spec.area.max);
    assert(strcmp(get_param(restriction,'max_area_unit'),'m^2') && ...
        str2double(get_param(restriction,'max_area'))==str2double(spec.area.max),'Unexpected derived area limit');
    restrictionConstants{strcmp(fixedKeys,'max_area')} = get_param(restriction,'max_area');
end
command = add_block('fl_lib/Physical Signals/Sources/PS Step',[model '/Phase12 Outlet Area']);
finalArea = spec.area.normal_final;
if strcmp(spec.case,'outlet_opening')
    finalArea = spec.area.intervention_final;
end
set_param(command,'step_time',spec.area.step_time,'step_time_unit',spec.area.time_unit, ...
    'initial_value',spec.area.initial_value,'initial_value_unit',spec.area.area_unit, ...
    'final_value',finalArea,'final_value_unit',spec.area.area_unit);
simscape.addConnection(command,'O',restriction,'area_in');
if isfield(spec,'overlay')
    exempt = h2prism_center_command_overlay(model,spec,true);
end
assertCommand(model,restriction,spec);
keys = fieldnames(spec.solver);
for i = 1:numel(keys)
    set_param(model,keys{i},spec.solver.(keys{i}));
end
set_param(model,'SaveState','on','StateSaveName','center_states','SaveFormat','Dataset', ...
    'ReturnWorkspaceOutputs','on','SignalLogging','on','SignalLoggingName','center_inputs', ...
    'SimscapeLogType','all','SimscapeLogName','center_simscape','SimscapeLogLimitData','off');
for i = 1:numel(inputMap)
    set_param(inputMap(i).handle,'DataLogging','on','DataLoggingNameMode','Custom', ...
        'DataLoggingName',inputMap(i).logName);
end
% Diagram update compiles the model but does not simulate a trajectory.
set_param(model,'SimulationCommand','update');
actualSolver = struct;
for i = 1:numel(keys)
    actualSolver.(keys{i}) = get_param(model,keys{i});
end
assert(isequal(actualSolver,spec.solver),'Compiled model configuration differs from design');
assertPath(model,restriction,spec.location);
assertCommand(model,restriction,spec);
assert(isequaln(restrictionConstants,cellfun(@(key) get_param(restriction,key),fixedKeys,'UniformOutput',false)), ...
    'Restriction properties beyond the intended type and command changed');
if isfield(spec,'overlay')
    h2prism_center_command_overlay(model,spec,false);
end
after = existingBlocks(model,restriction,[command,exempt]);
assert(isequaln(before,after),'An unrelated existing block link or connection changed');
closeDerived = onCleanup(@() closeIfLoaded('Center_phase12')); %#ok<NASGU>
save_system(model,derived);
assert(strcmp(h2prism_center_sha256(original),spec.source_sha256),'Original copy hash changed');
evidence = struct('case',spec.case,'source_sha256',spec.source_sha256, ...
    'derived_sha256',h2prism_center_sha256(derived),'compile_status','PASSED', ...
    'solver',actualSolver,'existing_block_links_parameters_and_connections_unchanged',true, ...
    'location',spec.location,'command_final_area_m2',finalArea,'version',version,'products',ver);
f = fopen(receipt,'wt');
assert(f >= 0,'Cannot write preflight receipt');
closeFile = onCleanup(@() fclose(f)); %#ok<NASGU>
fprintf(f,'%s\n',jsonencode(evidence,'PrettyPrint',true));
disp('=== PHASE 12 PREFLIGHT COMPLETED ===')
end

function state = existingBlocks(model,restriction,exempt)
if nargin == 2
    exempt = -1;
end
blocks = find_system(model,'SearchDepth',1,'Type','Block');
state = struct;
for i = 1:numel(blocks)
    handle = get_param(blocks{i},'Handle');
    if handle == restriction || any(handle == exempt)
        continue
    end
    sid = split(string(Simulink.ID.getSID(handle)),":");
    reference = get_param(handle,'ReferenceBlock');
    parameters = {};
    if startsWith(reference,{'fl_lib/','nesl_utility/'})
        keys = fieldnames(get_param(handle,'DialogParameters'));
        parameters = cellfun(@(key) get_param(handle,key),keys,'UniformOutput',false);
    end
    state.("SID_" + sid(end)) = {get_param(handle,'BlockType'), ...
        get_param(handle,'StaticLinkStatus'),reference,get_param(handle,'PortConnectivity'),parameters};
end
state = orderfields(state);
end

function assertCommand(model,restriction,spec)
cmd = [model '/Phase12 Outlet Area'];
assert(strcmp(get_param(cmd,'LinkStatus'),'resolved'),'Area source link unresolved');
peers = simscape.connectedPorts(restriction,'area_in');
assert(isscalar(peers) && strcmp(peers.PortName,'O') && ...
    getSimulinkBlockHandle(peers.Block,false) == get_param(cmd,'Handle'),'Incorrect area command producer');
expected = spec.area.normal_final;
if strcmp(spec.case,'outlet_opening')
    expected = spec.area.intervention_final;
end
assert(str2double(get_param(cmd,'initial_value')) == str2double(spec.area.initial_value) && ...
    str2double(get_param(cmd,'final_value')) == str2double(expected) && ...
    str2double(get_param(cmd,'step_time')) == str2double(spec.area.step_time) && ...
    strcmp(get_param(cmd,'step_time_unit'),'s') && ...
    strcmp(get_param(cmd,'initial_value_unit'),'m^2') && strcmp(get_param(cmd,'final_value_unit'),'m^2'), ...
    'Area command configuration differs');
end

function value = archivedMaximum(spec)
value = spec.area.max;
if isfield(spec.area,'source_max')
    value = spec.area.source_max;
end
end

function assertPath(model,restriction,location)
upstream = reshape(sort(string(location.upstream_junction_sids)),1,[]);
assert(isequal(sort(peerSIDs(restriction,'A')),upstream),'Unexpected upstream gas junction');
if isempty(location.flow_sensor_sid)
    assert(isequal(peerSIDs(restriction,'B'),string(location.reservoir_sid)), ...
        'Restriction does not connect directly to the approved atmospheric sink');
else
    sensor = Simulink.ID.getHandle([model ':' location.flow_sensor_sid]);
    assert(isequal(peerSIDs(restriction,'B'),string(location.flow_sensor_sid)) && ...
        isequal(peerSIDs(sensor,'B'),string(location.reservoir_sid)), ...
        'Unexpected metered atmospheric outlet path');
end
end

function [restriction,sink] = logNodes(spec)
restriction = 'Local_Restriction_G3';
sink = 'Reservoir_G1';
if isfield(spec.location,'restriction_log_node')
    restriction = spec.location.restriction_log_node;
    sink = spec.location.sink_log_node;
end
end

function out = peerSIDs(handle,port)
peers = simscape.connectedPorts(handle,port);
out = strings(1,numel(peers));
for i = 1:numel(peers)
    h = getSimulinkBlockHandle(peers(i).Block,false);
    assert(h > 0,'Unresolved physical peer');
    sid = split(string(Simulink.ID.getSID(h)),":");
    out(i) = sid(end);
end
end

function execute(caseDir,derived,spec,designFile)
approval = jsondecode(fileread(fullfile(fileparts(caseDir),'approval.json')));
record = approval.cases.(spec.case);
hash = h2prism_center_sha256(derived);
assert(strcmp(record.derived_sha256,hash) && ...
    strcmp(record.design_sha256,h2prism_center_sha256(designFile)) && ...
    strcmp(record.preflight_sha256,h2prism_center_sha256(fullfile(caseDir,'preflight.json'))), ...
    'Approved artifacts differ');
raw = fullfile(caseDir,'center_raw.mat');
log = fullfile(caseDir,'execution.log');
outputs = {'center_raw.mat','execution.log','center_extracted.mat','outlet_evidence.mat', ...
    'sensor_checkpoint.mat','logging_policy.mat','extract_errors.mat','stages.log'};
assert(~any(cellfun(@(name) isfile(fullfile(caseDir,name)),outputs)) && ~bdIsLoaded('Center_phase12'), ...
    'Use a fresh approved run directory and close Center_phase12');
stageFile = fullfile(caseDir,'stages.log');
previous = pwd;
cd(caseDir);
restore = onCleanup(@() cd(previous)); %#ok<NASGU>
guard = onCleanup(@() closeIfLoaded('Center_phase12')); %#ok<NASGU>
diary(log);
stopDiary = onCleanup(@() diary('off')); %#ok<NASGU>
try
    load_system(derived);
    model = 'Center_phase12';
    loaded = java.io.File(get_param(model,'FileName'));
    assert(strcmp(char(loaded.getCanonicalPath()),derived), ...
        'Loaded twin differs from approved file');
    restriction = Simulink.ID.getHandle([model ':' spec.location.restriction_sid]);
    assertPath(model,restriction,spec.location);
    assertCommand(model,restriction,spec);
    if isfield(spec,'overlay')
        h2prism_center_command_overlay(model,spec,false);
    end
    keys = {'SignalLogging','SaveState','SaveOutput','SaveFinalState'};
    before = cellfun(@(key) get_param(model,key),keys,'UniformOutput',false);
    for i = 1:numel(keys)
        set_param(model,keys{i},'off');
    end
    after = cellfun(@(key) get_param(model,key),keys,'UniformOutput',false);
    verifySolver(model,spec.solver);
    assert(all(strcmp(after,'off')) && strcmp(get_param(model,'SimscapeLogType'),'all') && ...
        strcmp(get_param(model,'SimscapeLogLimitData'),'off'),'Unexpected logging policy');
    save(fullfile(caseDir,'logging_policy.mat'),'keys','before','after','hash','-v7');
    writeStage(stageFile,'SIM_STARTED');
    out = sim(model);
    writeStage(stageFile,'SIM_RETURNED');
    info = out.SimulationMetadata.ExecutionInfo;
    assert(strcmp(info.StopEvent,'ReachedStopTime') && isempty(info.ErrorDiagnostic) && isempty(out.ErrorMessage), ...
        'Simulation failed to reach stop time cleanly');
    writeStage(stageFile,'NUMERIC_EXTRACTION_STARTED');
    [restrictionNode,~] = logNodes(spec);
    capture = h2prism_center_collect_capture(out,false,fullfile(caseDir,'sensor_checkpoint.mat'),restrictionNode,isfield(spec,'overlay'));
    verifyCapture(capture,spec);
    capture.approved_model_sha256 = hash;
    save(raw,'-struct','capture','-v7');
    capture.raw_sha256 = h2prism_center_sha256(raw);
    save(fullfile(caseDir,'center_extracted.mat'),'-struct','capture','-v7');
    writeStage(stageFile,'NUMERIC_CAPTURE_SAVED');
    response = runtimeEvidence(out,spec);
    assert(strcmp(hash,h2prism_center_sha256(derived)),'Approved derived model changed during simulation');
    save(fullfile(caseDir,'outlet_evidence.mat'),'response','hash','-v7');
    disp('=== PHASE 12 CAPTURE COMPLETED ===')
catch exception
    fprintf(2,'%s\n',getReport(exception,'extended','hyperlinks','off'));
    rethrow(exception)
end
end

function verifySolver(model,expected)
keys = fieldnames(expected);
for i = 1:numel(keys)
    assert(strcmp(get_param(model,keys{i}),expected.(keys{i})), ...
        'Logging override altered solver or initialization setting: %s',keys{i});
end
end

function verifyCapture(capture,spec)
step = str2double(spec.solver.FixedStep);
stop = str2double(spec.solver.StopTime);
assert(capture.execution.start_s == 0 && capture.execution.stop_s == stop && ...
    capture.execution.solverInfo.FixedStepSize == step && ...
    strcmp(capture.execution.solverInfo.Solver,spec.solver.Solver),'Executed solver differs');
expected = (0:round(stop/step)).' * step;
clock = capture.sensors.pressure_sensor1.time(:);
assert(numel(clock)==numel(expected) && all(isfinite(clock)) && all(diff(clock)>0) && ...
    all(abs(clock-expected)<=8*eps(max(1,abs(expected)))),'Incomplete saved clock');
keys = fieldnames(capture.sensors);
assert(numel(keys)==13,'Missing sensor channel');
for i = 1:numel(keys)
    signal = capture.sensors.(keys{i});
    assert(isequal(signal.time(:),clock) && isvector(signal.values) && ...
        numel(signal.values)==numel(clock) && all(isfinite(signal.values)), ...
        'Incomplete sensor history: %s',keys{i});
end
end

function writeStage(path,message)
f = fopen(path,'at');
assert(f>=0,'Cannot write stage log');
cleanup = onCleanup(@() fclose(f)); %#ok<NASGU>
fprintf(f,'%s\n',message);
end

function response = runtimeEvidence(out,spec)
root = out.get('center_simscape');
[restrictionNode,sinkNode] = logNodes(spec);
restriction = root.(restrictionNode);
sink = root.(sinkNode);
area = readSeries(root.Phase12_Outlet_Area.O,'m^2');
seen = readSeries(restriction.area_in,'m^2');
assert(isequal(area.time,seen.time) && all(abs(area.values-seen.values) <= 1e-12), ...
    'Restriction received a different area history than the command');
assert(all(diff(area.time)>0) && area.time(1)==0 && area.time(end)==20000 && all(isfinite(area.values)), ...
    'Incomplete area history');
specTime = str2double(spec.area.step_time);
initial = str2double(spec.area.initial_value);
final = str2double(spec.area.normal_final);
if strcmp(spec.case,'outlet_opening')
    final = str2double(spec.area.intervention_final);
end
before = area.time < specTime - 8*eps(specTime);
after = area.time > specTime + str2double(spec.solver.FixedStep) + 8*eps(specTime);
assert(any(before) && any(after) && all(abs(area.values(before)-initial)<=1e-12) && ...
    all(abs(area.values(after)-final)<=1e-12),'Recorded area sequence differs from design');
firstChange = [];
if final ~= initial
    firstChange = area.time(find(abs(area.values-initial)>1e-12,1));
    assert(isscalar(firstChange) && firstChange >= specTime-8*eps(specTime) && ...
        firstChange <= specTime+str2double(spec.solver.FixedStep)+8*eps(specTime),'Opening timing differs');
end
rate = readSeries(restriction.mdot_A,'kg/s');
sinkRate = readSeries(sink.mdot_A,'kg/s');
up = readSeries(restriction.A.p,'Pa');
down = readSeries(restriction.B.p,'Pa');
pressure = readSeries(sink.p_I,'Pa');
temperature = readSeries(sink.T_I,'K');
assert(isequal(rate.time,sinkRate.time,up.time,down.time,pressure.time,temperature.time,area.time), ...
    'Physical response clocks differ');
assert(all(abs(rate.values-sinkRate.values)<=1e-8) && ...
    all(up.values(after)>down.values(after)) && all(rate.values(after)>0), ...
    'The outlet flow did not show the expected pressure-driven direction');
assert(all(abs(pressure.values-100000)<=1e-4) && all(abs(temperature.values-293.15)<=1e-6), ...
    'Atmospheric sink state differs from source runtime evidence');
response = struct('area',area,'restriction_area_input',seen,'signed_outlet_flow',rate, ...
    'signed_sink_flow',sinkRate,'upstream_pressure',up,'downstream_pressure',down, ...
    'sink_pressure',pressure,'sink_temperature',temperature,'first_change_s',firstChange);
end

function s = readSeries(node,unit)
s = struct('time',time(node.series),'values',values(node.series,Units=unit),'unit',unit);
assert(all(isfinite(s.time)) && all(isfinite(s.values)),'Nonfinite physical output');
end

function closeIfLoaded(model)
if bdIsLoaded(model)
    close_system(model,0);
end
end
