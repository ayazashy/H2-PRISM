function capture = h2prism_center_collect_capture(out, datasetLogging, checkpoint, outletNode)
% Materialize scientific outputs as plain MATLAB arrays and structs.
if nargin < 4
    outletNode = 'Local_Restriction_G3';
end
metadata = out.SimulationMetadata;
info = metadata.ExecutionInfo;
execution = struct('stopEvent',char(info.StopEvent), ...
    'errorDiagnostic',strtrim(evalc('disp(info.ErrorDiagnostic)')), ...
    'warningCount',numel(info.WarningDiagnostics),'warnings',strtrim(evalc('disp(info.WarningDiagnostics)')));
execution.simulationErrorMessage = char(out.ErrorMessage);
execution.modelName = metadata.ModelInfo.ModelName;
execution.solverInfo = metadata.ModelInfo.SolverInfo;
execution.start_s = metadata.ModelInfo.StartTime;
execution.stop_s = metadata.ModelInfo.StopTime;
for name = [compose("pressure_sensor%d",1:10),compose("flow_sensor%d",1:3)]
    sensors.(name) = timeseriesData(out.get(char(name)));
end
if datasetLogging
    inputs = out.get('center_inputs');
    for name = ["reservoir_pressure","reservoir_temperature"]
        element = inputs.getElement(char(name));
        commands.(name) = timeseriesData(element.Values);
    end
    states = out.get('center_states');
    initial = struct('name',{},'blockPath',{},'kind',{},'samples',{});
    for i = 1:states.numElements
        element = states.getElement(i);
        initial(i).name = char(element.Name);
        initial(i).blockPath = strtrim(evalc('disp(element.BlockPath)'));
        initial(i).kind = class(element.Values);
        if isa(element.Values,'timeseries') && ~isempty(element.Values.Time)
            vals = getdatasamples(element.Values,[1,numel(element.Values.Time)]);
            initial(i).samples = struct('firstTime',element.Values.Time(1), ...
                'lastTime',element.Values.Time(end),'values',vals,'units',unitText(element.Values.DataInfo.Units));
        end
    end
else
    commands = struct;
    initial = struct('name',{},'blockPath',{},'kind',{},'samples',{});
end
capture = struct('execution',execution,'sensors',sensors);
if ~isempty(checkpoint)
    assert(~isfile(checkpoint),'Use a fresh sensor checkpoint');
    save(checkpoint,'-struct','capture','-v7');
end
root = out.get('center_simscape');
inventory = evalc('print(root)');
logSeries = struct('path',{},'unit',{},'time',{},'values',{});
logErrors = struct('path',{},'message',{});
paths = ["Reservoir/P","Reservoir/T","Reservoir/mdot_A","Reservoir/A/p","Reservoir/A/T", ...
    "PS_Step/O","PS_Ramp/O","Pressure_Source_G1/P","Pressure_Source_G3/P", ...
    "Constant_Volume_Chamber_G/rho_I","Constant_Volume_Chamber_G/p_I","Constant_Volume_Chamber_G/T_I", ...
    "Constant_Volume_Chamber_G/mdot_A","Constant_Volume_Chamber_G/mdot_B", ...
    "Constant_Volume_Chamber_G/mdot_C","Constant_Volume_Chamber_G/mdot_D"];
for component = ["Reservoir_G",compose("Reservoir_G%d",1:4)]
    paths = [paths, component + ["/mdot_A","/A/p","/A/T","/p_I","/T_I"]]; %#ok<AGROW>
end
for component = compose("Pipe_G%d",[1:5,7:8])
    paths = [paths, component + ["/mdot_A","/mdot_B","/rho_I","/p_I","/T_I"]]; %#ok<AGROW>
end
for component = compose("Flow_Rate_Sensor_G%d",1:3)
    paths = [paths, component + "/M"]; %#ok<AGROW>
end
for component = ["Pressure_Temperature_Sensor_G",compose("Pressure_Temperature_Sensor_G%d",[1:5,7,11:13])]
    paths = [paths, component + ["/Pa","/A/T"]]; %#ok<AGROW>
end
if ~datasetLogging
    paths = paths(~ismember(paths,"Constant_Volume_Chamber_G/" + ["mdot_B","mdot_C","mdot_D"]));
    paths = [paths,"Phase12_Outlet_Area/O",string(outletNode) + ["/area_in","/mdot_A","/A/p","/B/p"]];
end
for path = paths
    try
        leaf = root;
        for identifier = reshape(split(path,"/"),1,[])
            leaf = leaf.(identifier);
        end
        series = leaf.series;
        logSeries(end+1) = struct('path',char(path),'unit',char(series.unit), ... %#ok<AGROW>
            'time',time(series),'values',values(series));
    catch exception
        logErrors(end+1) = struct('path',char(path),'message',exception.message); %#ok<AGROW>
    end
end
if ~datasetLogging
    if ~isempty(logErrors)
        save(fullfile(fileparts(checkpoint),'extract_errors.mat'),'logErrors','-v7');
        error('A required physical history could not be read; see extract_errors.mat');
    end
    for i = 1:numel(logSeries)
        item = logSeries(i);
        assert(isvector(item.values) && isequal(item.time(:),capture.sensors.pressure_sensor1.time(:)) && ...
            numel(item.values)==numel(item.time) && all(isfinite(item.values)), ...
            'Incomplete physical history: %s',item.path);
        if strcmp(item.path,'Reservoir/P')
            commands.reservoir_pressure = item;
        elseif strcmp(item.path,'Reservoir/T')
            commands.reservoir_temperature = item;
        end
        if endsWith(item.path,["/rho_I","/p_I","/T_I"])
            initial(end+1) = struct('name',item.path,'blockPath','','kind','Simscape series', ... %#ok<AGROW>
                'samples',struct('firstTime',item.time(1),'lastTime',item.time(end), ...
                'values',[item.values(1),item.values(end)],'units',item.unit));
        end
    end
end
capture.commands = commands;
capture.initial = initial;
capture.inventory = inventory;
capture.logSeries = logSeries;
capture.logErrors = logErrors;
end

function record = timeseriesData(signal)
record = struct('time',signal.Time,'values',signal.Data,'unit',unitText(signal.DataInfo.Units), ...
    'timeUnit',signal.TimeInfo.Units);
end

function label = unitText(unit)
try
    label = char(unit);
catch
    label = strtrim(evalc('disp(unit)'));
end
end
