function h2prism_center_source_capture(runDir, stopTime, convergence)
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
if nargin >= 2 && ~isempty(stopTime)
    set_param(name,'StopTime',char(string(stopTime)));
end
if nargin == 3
    assert(isempty(stopTime) && any(convergence.step == [0.4,0.2]),'Invalid convergence case');
    verifyStepOnly(name,keys,convergence,inputMap,physicalInputs);
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
if nargin == 3
    info = out.SimulationMetadata.ExecutionInfo;
    assert(strcmp(info.StopEvent,'ReachedStopTime') && isempty(out.ErrorMessage) && ...
        isempty(info.ErrorDiagnostic),'Convergence simulation did not reach stop time cleanly');
end
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

function verifyStepOnly(name,keys,convergence,inputMap,physicalInputs)
baseline = load(convergence.baseline,'configured','inputMap','physicalInputs','gasSettings');
snapshot = @() cell2struct(cellfun(@(p) get_param(name,p),keys,'UniformOutput',false),keys,2);
before = snapshot();
assert(isequal(before,baseline.configured),'Baseline solver or initialization settings differ');
assert(isequal(rmfield(inputMap,'handle'),baseline.inputMap) && ...
    isequal(physicalInputs,baseline.physicalInputs),'Baseline input mapping or definitions differ');
blocks = find_system(name,'LookUnderMasks','none','FollowLinks','off','RegExp','on','Name','^Gas Properties');
gas = cell(size(blocks));
for i = 1:numel(blocks)
    names = fieldnames(get_param(blocks{i},'DialogParameters'));
    gas{i} = cell2struct(cellfun(@(p) get_param(blocks{i},p),names,'UniformOutput',false),names);
end
assert(isequal(gas,baseline.gasSettings),'Baseline gas settings differ');
% Enumerate reviewed solver controls from the pinned SolverCC record.
requested = {'SolverType','Solver','StartTime','StopTime','AbsTol','AutoScaleAbsTol','FixedStep', ...
    'InitialStep','MaxOrder','ZcThreshold','ConsecutiveZCsStepRelTol','MaxConsecutiveZCs', ...
    'ExtrapolationOrder','NumberNewtonIterations','MaxStep','MinStep','MaxConsecutiveMinStep', ...
    'RelTol','EnableMultiTasking','AllowMultiTaskInputOutput','ConcurrentTasks', ...
    'SolverJacobianMethodControl','DaesscMode','StateRefinementMethod','ShapePreserveControl', ...
    'ZeroCrossControl','ZeroCrossAlgorithm','AlgebraicLoopSolver','SolverResetMethod', ...
    'PositivePriorityOrder','AutoInsertRateTranBlk','SampleTimeConstraint','InsertRTBMode', ...
    'DecoupledContinuousIntegration','MinimalZcImpactIntegration','ODENIntegrationMethod', ...
    'EnableFixedStepZeroCrossing','MaxZcPerStep','MaxZcBracketingIterations'};
available = get_param(name,'ObjectParameters');
readable = isfield(available,requested);
parameters = requested(readable);
unavailable = requested(~readable);
readSolver = @() cellfun(@(key) get_param(name,key),parameters,'UniformOutput',false);
solverBefore = readSolver();
solverConfiguration = Simulink.ID.getHandle([name ':7']);
localSolverBefore = get_param(solverConfiguration,'UseLocalSolver');
assert(strcmp(localSolverBefore,'off'),'Unexpected Simscape local solver policy');
set_param(name,'FixedStep',char(string(convergence.step)));
solverAfter = readSolver();
changed = ~cellfun(@isequal,solverBefore,solverAfter);
assert(isequal(parameters(changed),{'FixedStep'}) && ...
    strcmp(get_param(solverConfiguration,'UseLocalSolver'),localSolverBefore), ...
    'Unexpected solver setting changed');
after = snapshot();
assert(isequal(rmfield(before,'FixedStep'),rmfield(after,'FixedStep')),'Unexpected configuration delta');
versions = ver;
save('center_solver_delta.mat','before','after','parameters','solverBefore','solverAfter','changed','versions','unavailable','localSolverBefore');
end
