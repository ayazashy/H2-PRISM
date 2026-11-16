function evidenceFile = h2prism_center_reservoir_diagnostic(runDir)
% Record live Simscape port evidence without applying the capture gate or simulating.
[plan, file, guard] = h2prism_center_load_isolated(runDir);
evidence = struct('sourceFile',file,'pinnedSHA256',plan.sha256, ...
    'timestampUTC',char(datetime('now','TimeZone','UTC','Format','yyyy-MM-dd''T''HH:mm:ss.SSS''Z''')), ...
    'version',version,'release',version('-release'),'products',ver);
evidence.expectedInputs = plan.reservoir_inputs;
reservoir = blockHandle(plan.model,plan.reservoir.sid);
evidence.reservoir = inspectBlock(reservoir,["A","T","P"]);
for key = ["area_A","area_A_unit","pressure_input","temperature_input","reservoir_spec"]
    evidence.reservoir.parameters.(key) = probe(@() get_param(reservoir,key));
end
for i = 1:numel(plan.reservoir_inputs)
    spec = plan.reservoir_inputs(i);
    converter = blockHandle(plan.model,spec.converter_sid);
    evidence.converters(i) = inspectBlock(converter,strings(1,0));
    evidence.preflightTests(i).role = spec.role;
    evidence.preflightTests(i).portQuery = spec.reservoir_signal_name;
    evidence.preflightTests(i).expectedBlockPath = getfullname(converter);
    evidence.preflightTests(i).result = probe(@() previousComparison( ...
        reservoir,spec.reservoir_signal_name,converter));
end
evidence.dirtyBeforeClose = get_param(plan.model,'Dirty');
clear guard
evidence.closed = ~bdIsLoaded(plan.model);
evidence.sha256AfterClose = h2prism_center_sha256(file);
evidence.checksumPreserved = strcmp(evidence.sha256AfterClose,plan.sha256);
evidenceFile = [tempname(fileparts(file)) '_center_reservoir_diagnostic.mat'];
save(evidenceFile,'evidence');
fprintf('Center reservoir diagnostic evidence: %s\n',evidenceFile);
fprintf('%s\n',jsonencode(evidence,'PrettyPrint',true));
assert(evidence.closed && evidence.checksumPreserved, ...
    'The isolated copy did not close cleanly or its checksum changed');
end

function handle = blockHandle(model,sid)
handle = Simulink.ID.getHandle([model ':' sid]);
assert(isnumeric(handle) && isscalar(handle) && handle > 0,'Invalid handle for Center SID %s',sid);
end

function block = inspectBlock(handle,requestedNames)
block = struct('sid',Simulink.ID.getSID(handle),'path',getfullname(handle), ...
    'referenceBlock',probe(@() get_param(handle,'ReferenceBlock')), ...
    'linkStatus',probe(@() get_param(handle,'LinkStatus')), ...
    'portHandles',probe(@() get_param(handle,'PortHandles')), ...
    'portConnectivity',probe(@() get_param(handle,'PortConnectivity')));
block.physicalPorts = probe(@() physicalProperties(handle));
if block.physicalPorts.succeeded && ~isempty(block.physicalPorts.value)
    names = string({block.physicalPorts.value.name});
    requestedNames = unique([requestedNames,names],'stable');
end
block.namedConnections = struct('portQuery',{},'peers',{});
for name = requestedNames
    block.namedConnections(end+1) = struct('portQuery',name, ... %#ok<AGROW>
        'peers',probe(@() namedPeers(handle,name)));
end
block.physicalLines = struct('portGroup',{},'portIndex',{},'portHandle',{},'line',{});
if block.portHandles.succeeded
    ports = block.portHandles.value;
    for side = ["LConn","RConn"]
        for i = 1:numel(ports.(side))
            p = ports.(side)(i);
            block.physicalLines(end+1) = struct('portGroup',side,'portIndex',i, ... %#ok<AGROW>
                'portHandle',p,'line',probe(@() inspectLines(p)));
        end
    end
end
end

function rows = physicalProperties(handle)
portProperties = simscape.connectionPortProperties(handle);
rows = struct('name',{},'label',{},'labelMissing',{},'type',{});
for i = 1:numel(portProperties)
    port = portProperties(i);
    label = string(port.Label);
    labelMissing = isempty(label) || ismissing(label);
    if labelMissing
        label = "";
    end
    type = port.ConnectionType;
    rows(i) = struct('name',char(port.Name),'label',label,'labelMissing',labelMissing, ...
        'type',strtrim(evalc('disp(type)')));
end
end

function result = namedPeers(handle,name)
peers = simscape.connectedPorts(handle,char(name));
result = struct('shape',size(peers),'peers',peers, ...
    'peerIdentity',struct('reportedPath',{},'resolvedSID',{}));
for i = 1:numel(peers)
    result.peerIdentity(i).reportedPath = peers(i).Block;
    result.peerIdentity(i).resolvedSID = probe(@() sidForPath(peers(i).Block));
end
end

function sid = sidForPath(path)
handle = getSimulinkBlockHandle(path,false);
assert(handle > 0,'Reported peer path did not resolve in the loaded model');
sid = Simulink.ID.getSID(handle);
end

function connected = previousComparison(reservoir,name,converter)
peers = simscape.connectedPorts(reservoir,name);
connected = isscalar(peers) && strcmp(peers.Block,getfullname(converter));
end

function result = inspectLines(port)
handles = get_param(port,'Line');
result = struct('handles',handles,'endpoints',struct('handle',{},'srcPortHandle',{}, ...
    'dstPortHandle',{},'lineParent',{},'lineChildren',{}));
for h = reshape(handles(handles > 0),1,[])
    result.endpoints(end+1) = struct('handle',h, ... %#ok<AGROW>
        'srcPortHandle',probe(@() get_param(h,'SrcPortHandle')), ...
        'dstPortHandle',probe(@() get_param(h,'DstPortHandle')), ...
        'lineParent',probe(@() get_param(h,'LineParent')), ...
        'lineChildren',probe(@() get_param(h,'LineChildren')));
end
end

function result = probe(read)
result = struct('succeeded',false,'value',[],'errorIdentifier','','errorMessage','');
try
    result.value = read();
    result.succeeded = true;
catch exception
    result.errorIdentifier = exception.identifier;
    result.errorMessage = exception.message;
end
end
