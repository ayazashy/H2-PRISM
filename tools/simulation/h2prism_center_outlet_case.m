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
restriction = Simulink.ID.getHandle([model ':213']);
boundary = Simulink.ID.getHandle([model ':200']);
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
    str2double(get_param(restriction,'max_area')) == str2double(spec.area.max),'Archived area limits changed');
assert(strcmp(get_param(Simulink.ID.getHandle([model ':7']),'UseLocalSolver'),'off'), ...
    'Unexpected local solver policy');
assertPath(model,restriction);
before = existingBlocks(model,restriction);
fixedKeys = {'restriction_area','restriction_area_unit','min_area','max_area','area','area_unit','Cd','B_lam'};
restrictionConstants = cellfun(@(key) get_param(restriction,key),fixedKeys,'UniformOutput',false);
area = str2double([string(spec.area.initial_value),string(spec.area.normal_final),string(spec.area.intervention_final)]);
bounds = str2double([string(spec.area.min),string(spec.area.max)]);
assert(all(isfinite(area)) && all(area >= bounds(1) & area <= bounds(2)) && ...
    area(1) == area(2) && area(3) > area(1) && strcmp(spec.area.area_unit,'m^2') && ...
    strcmp(spec.area.time_unit,'s'),'Invalid design area or units');
set_param(restriction,'restriction_type','foundation.enum.restriction_type.variable');
command = add_block('fl_lib/Physical Signals/Sources/PS Step',[model '/Phase12 Outlet Area']);
finalArea = spec.area.normal_final;
if strcmp(spec.case,'outlet_opening')
    finalArea = spec.area.intervention_final;
end
set_param(command,'step_time',spec.area.step_time,'step_time_unit',spec.area.time_unit, ...
    'initial_value',spec.area.initial_value,'initial_value_unit',spec.area.area_unit, ...
    'final_value',finalArea,'final_value_unit',spec.area.area_unit);
simscape.addConnection(command,'O',restriction,'area_in');
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
assertPath(model,restriction);
assertCommand(model,restriction,spec);
assert(isequaln(restrictionConstants,cellfun(@(key) get_param(restriction,key),fixedKeys,'UniformOutput',false)), ...
    'Restriction properties beyond the intended type and command changed');
after = existingBlocks(model,restriction,command);
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
    if handle == restriction || handle == exempt
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

function assertPath(model,restriction)
sensor = Simulink.ID.getHandle([model ':218']);
assert(isequal(sort(peerSIDs(restriction,'A')), ["47","48","50"]) && ...
    isequal(peerSIDs(restriction,'B'),"218") && isequal(peerSIDs(sensor,'B'),"200"), ...
    'SID 213 atmospheric branch differs from the pinned source');
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
assert(~isfile(raw) && ~isfile(log) && ~bdIsLoaded('Center_phase12'), ...
    'Use a fresh approved run directory and close Center_phase12');
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
    restriction = Simulink.ID.getHandle([model ':213']);
    assertPath(model,restriction);
    assertCommand(model,restriction,spec);
    out = sim(model);
    save(raw,'out','hash','-v7.3');
    info = out.SimulationMetadata.ExecutionInfo;
    assert(strcmp(info.StopEvent,'ReachedStopTime') && isempty(info.ErrorDiagnostic) && isempty(out.ErrorMessage), ...
        'Simulation failed to reach stop time cleanly');
    h2prism_center_extract_capture(caseDir,fullfile(caseDir,'center_extracted.mat'));
    response = runtimeEvidence(out,spec);
    assert(strcmp(hash,h2prism_center_sha256(derived)),'Approved derived model changed during simulation');
    save(fullfile(caseDir,'outlet_evidence.mat'),'response','hash','-v7');
    disp('=== PHASE 12 CAPTURE COMPLETED ===')
catch exception
    fprintf(2,'%s\n',getReport(exception,'extended','hyperlinks','off'));
    rethrow(exception)
end
end

function response = runtimeEvidence(out,spec)
root = out.get('center_simscape');
area = readSeries(root.Phase12_Outlet_Area.O,'m^2');
seen = readSeries(root.Local_Restriction_G3.area_in,'m^2');
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
rate = readSeries(root.Local_Restriction_G3.mdot_A,'kg/s');
sinkRate = readSeries(root.Reservoir_G1.mdot_A,'kg/s');
up = readSeries(root.Local_Restriction_G3.A.p,'Pa');
down = readSeries(root.Local_Restriction_G3.B.p,'Pa');
pressure = readSeries(root.Reservoir_G1.p_I,'Pa');
temperature = readSeries(root.Reservoir_G1.T_I,'K');
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
