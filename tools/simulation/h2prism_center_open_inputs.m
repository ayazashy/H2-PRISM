function [inputMap, physicalInputs, guard] = h2prism_center_open_inputs(runDir)
% Validate and load the isolated, pinned Center model without simulating it.
[plan, ~, guard] = h2prism_center_load_isolated(runDir);
name = plan.model;
reservoir = sid(name,plan.reservoir.sid);
reservoirEvidence = struct('sid',plan.reservoir.sid,'library',libraryReference(reservoir), ...
    'release',version('-release'),'linkStatus',get_param(reservoir,'LinkStatus'), ...
    'area','','areaUnit','', ...
    'pressureInput','','temperatureInput','','reservoirSpec','', ...
    'pressureConnected',false,'temperatureConnected',false);
migrated = strcmp(reservoirEvidence.library,plan.reservoir.migration.library) && ...
    any(strcmp(reservoirEvidence.release,plan.reservoir.migration.supported_releases));
assert(migrated || strcmp(reservoirEvidence.library,plan.reservoir_library), ...
    'Unsupported Center reservoir library or release: %s (%s)',reservoirEvidence.library,reservoirEvidence.release);
reservoirEvidence.area = get_param(reservoir,'area_A');
reservoirEvidence.areaUnit = get_param(reservoir,'area_A_unit');
if migrated
    reservoirEvidence.pressureInput = char(string(get_param(reservoir,'pressure_input')));
    reservoirEvidence.temperatureInput = char(string(get_param(reservoir,'temperature_input')));
    if strcmp(reservoirEvidence.release,'2026b')
        reservoirEvidence.reservoirSpec = get_param(reservoir,'reservoir_spec');
    end
end
reservoirPorts = get_param(reservoir,'PortHandles');
subsystem = sid(name,'12');
outputs = get_param(subsystem,'PortHandles');
inputMap = struct('role',{},'block',{},'sourceBlock',{},'sourcePort',{},'logName',{},'unit',{},'handle',{},'reservoirEvidence',{});
for i = 1:numel(plan.reservoir_inputs)
    spec = plan.reservoir_inputs(i);
    converter = linked(name,spec.converter_sid,plan.converter_library);
    assert(strcmp(get_param(converter,'LinkStatus'),'resolved'), ...
        'Center converter link is not resolved at SID %s',spec.converter_sid);
    from = sid(name,spec.from_sid);
    goto = sid(name,spec.goto_sid);
    assert(strcmp(get_param(from,'BlockType'),'From') && strcmp(get_param(goto,'BlockType'),'Goto') && ...
        strcmp(get_param(from,'GotoTag'),spec.tag) && strcmp(get_param(goto,'GotoTag'),spec.tag), ...
        'Unexpected reservoir signal routing for %s',spec.role);
    cp = get_param(converter,'PortHandles');
    fp = get_param(from,'PortHandles');
    gp = get_param(goto,'PortHandles');
    assert(isscalar(cp.Inport) && isscalar(fp.Outport) && isscalar(gp.Inport) && ...
        spec.subsystem_output <= numel(outputs.Outport) && strcmp(get_param(converter,'Unit'),spec.unit), ...
        'Missing input port or unexpected converter unit for %s',spec.role);
    assert(driver(cp.Inport) == fp.Outport && driver(gp.Inport) == outputs.Outport(spec.subsystem_output), ...
        'Required reservoir input is missing or miswired: %s',spec.role);
    assert(numel([cp.LConn, cp.RConn]) == 1, 'Unexpected converter physical port configuration');
    if migrated
        peers = simscape.connectedPorts(reservoir,spec.reservoir_signal_name);
        assert(spec.reservoir_port <= numel(reservoirPorts.RConn), ...
            'Missing Center reservoir physical input port for %s',spec.role);
        converterPort = [cp.LConn, cp.RConn];
        reservoirPort = reservoirPorts.RConn(spec.reservoir_port);
        wire = get_param(converterPort,'Line');
        connected = isscalar(wire) && wire > 0 && ...
            isequal(wire,get_param(reservoirPort,'Line')) && ...
            h2prism_center_connection_matches(peers,[name ':' spec.converter_sid],@peerSID, ...
                {get_param(wire,'SrcPortHandle'),get_param(wire,'DstPortHandle')}, ...
                {converterPort,reservoirPort});
    else
        assert(spec.reservoir_port <= numel(reservoirPorts.RConn) && isscalar(cp.RConn), ...
            'Missing legacy reservoir physical input port');
        wire = get_param(cp.RConn,'Line');
        connected = isscalar(wire) && wire > 0 && ...
            isequal(wire,get_param(reservoirPorts.RConn(spec.reservoir_port),'Line'));
    end
    if strcmp(spec.reservoir_signal_name,'P')
        reservoirEvidence.pressureConnected = connected;
    elseif strcmp(spec.reservoir_signal_name,'T')
        reservoirEvidence.temperatureConnected = connected;
    else
        error('Unexpected Center reservoir physical port name');
    end
    inputMap(end+1) = struct('role',spec.role,'block',getfullname(converter), ... %#ok<AGROW>
        'sourceBlock',getfullname(from),'sourcePort',1,'logName',spec.role,'unit',spec.unit,'handle',fp.Outport,'reservoirEvidence',[]);
end

h2prism_validate_center_reservoir(reservoirEvidence,plan);
for i = 1:numel(inputMap)
    inputMap(i).reservoirEvidence = reservoirEvidence;
end

% Native physical-signal wires are verified in the pinned archive by the
% offline check. They have no Simulink signal port to mark for logging.
physicalInputs = struct('role',{},'sourceBlock',{},'targetBlock',{},'parameters',{},'loggingLimitation',{});
for i = 1:numel(plan.physical_inputs)
    spec = plan.physical_inputs(i);
    source = linked(name,spec.source_sid,spec.library);
    target = linked(name,spec.target_sid,plan.pressure_source_library);
    assert(strcmp(get_param(target,'source_type'),plan.controlled_mode), ...
        'Expected controlled pressure source for %s',spec.role);
    parameters = struct;
    for j = 1:numel(spec.parameters)
        key = spec.parameters{j};
        parameters.(key) = get_param(source,key);
        parameters.([key '_unit']) = get_param(source,[key '_unit']);
    end
    physicalInputs(end+1) = struct('role',spec.role,'sourceBlock',getfullname(source), ... %#ok<AGROW>
        'targetBlock',getfullname(target),'parameters',parameters, ...
        'loggingLimitation','Native Simscape signal. Inspect the full Simscape log for command histories.');
end
assert(isequal(sort({inputMap.role}),{'reservoir_pressure','reservoir_temperature'}) && ...
    isequal(sort({physicalInputs.role}),{'pressure_source_ramp','pressure_source_step'}), ...
    'Incomplete or unsupported Center physical-input plan');
end

function handle = sid(model, value)
handle = Simulink.ID.getHandle([model ':' value]);
assert(isscalar(handle) && isnumeric(handle) && handle > 0, 'Missing required Center SID %s',value);
end

function handle = linked(model, value, expected)
handle = sid(model,value);
normalized = libraryReference(handle);
assert(strcmp(normalized,expected), 'Unsupported library link at Center SID %s: %s',value,normalized);
end

function normalized = libraryReference(handle)
reference = get_param(handle,'ReferenceBlock');
normalized = strtrim(regexprep(strrep(reference,'\n',' '),'\s+',' '));
end

function source = driver(port)
line = get_param(port,'Line');
assert(isscalar(line) && line > 0,'Required Simulink input has no line');
source = get_param(line,'SrcPortHandle');
assert(isscalar(source) && source > 0,'Required Simulink input has no supported driver');
end

function value = peerSID(path)
handle = getSimulinkBlockHandle(path,false);
value = '';
if isscalar(handle) && handle > 0
    value = Simulink.ID.getSID(handle);
end
end
