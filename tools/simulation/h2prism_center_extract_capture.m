function h2prism_center_extract_capture(runDir, output)
% Read a completed SimulationOutput and save plain data. Does not load or simulate the SLX.
assert(~isfile(output),'Use a fresh extraction file');
file = fullfile(runDir,'center_raw.mat');
raw_sha256 = h2prism_center_sha256(file);
stored = load(file,'out');
out = stored.out;
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
assert(strcmp(raw_sha256,h2prism_center_sha256(file)),'Raw capture checksum changed during extraction');
save(output,'raw_sha256','execution','sensors','commands','initial','inventory','logSeries','logErrors','-v7');
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
