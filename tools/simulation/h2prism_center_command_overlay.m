function handles = h2prism_center_command_overlay(model,spec,build)
% Insert a physical-signal sum, retaining the original source and gas wiring.
o = spec.overlay;
receiver = Simulink.ID.getHandle([model ':' o.receiver_sid]);
producer = Simulink.ID.getHandle([model ':' o.producer_sid]);
step = [model '/Phase13 Command Offset'];
adder = [model '/Phase13 Command Sum'];
assert(strcmp(get_param(receiver,'LinkStatus'),'resolved') && ...
    strcmp(get_param(producer,'LinkStatus'),'resolved'), 'Overlay endpoint link is unresolved');
if strcmp(o.role,'internal_pressure')
    assert(strcmp(regexprep(get_param(receiver,'ReferenceBlock'),'\s+',' '), ...
        'fl_lib/Gas/Sources/Pressure Source (G)') && ...
        strcmp(get_param(receiver,'source_type'),'foundation.enum.constant_controlled.controlled'), ...
        'SID 55 is not the controlled gas pressure source');
end
final = o.normal_final;
if strcmp(spec.case,'outlet_opening')
    final = o.intervention_final;
end
if build
    old = simscape.connectedPorts(receiver,o.port);
    assert(isscalar(old) && getSimulinkBlockHandle(old.Block,false)==producer, ...
        'Pinned overlay producer or receiver differs');
    sourcePort = char(old.PortName);
    receiverBefore = identity(receiver);
    producerBefore = identity(producer);
    gasBefore = gasPeers(receiver,o.role);
    simscape.removeConnection(receiver,o.port);
    stepHandle = add_block('fl_lib/Physical Signals/Sources/PS Step',step);
    sumHandle = add_block('fl_lib/Physical Signals/Functions/PS Add',adder);
    set_param(stepHandle,'step_time',o.step_time,'step_time_unit','s', ...
        'initial_value','0','initial_value_unit','MPa','final_value',final,'final_value_unit','MPa');
    simscape.addConnection(producer,sourcePort,sumHandle,'I1');
    simscape.addConnection(stepHandle,'O',sumHandle,'I2');
    simscape.addConnection(sumHandle,'O',receiver,o.port);
    assert(isequaln(receiverBefore,identity(receiver)) && ...
        isequaln(producerBefore,identity(producer)) && isequal(gasBefore,gasPeers(receiver,o.role)), ...
        'An original link, parameter, or conserving gas connection changed');
end
checkPeer(adder,'I1',producer);
checkPeer(adder,'I2',get_param(step,'Handle'),'O');
checkPeer(receiver,o.port,get_param(adder,'Handle'),'O');
assert(strcmp(get_param(step,'LinkStatus'),'resolved') && strcmp(get_param(adder,'LinkStatus'),'resolved') && ...
    str2double(get_param(step,'step_time'))==str2double(o.step_time) && ...
    str2double(get_param(step,'initial_value'))==0 && ...
    str2double(get_param(step,'final_value'))==str2double(final) && ...
    strcmp(get_param(step,'step_time_unit'),'s') && ...
    strcmp(get_param(step,'initial_value_unit'),'MPa') && strcmp(get_param(step,'final_value_unit'),'MPa'), ...
    'Overlay command parameters differ');
handles = [producer,receiver,get_param(step,'Handle'),get_param(adder,'Handle')];
end

function checkPeer(block,port,expected,peerPort)
peers = simscape.connectedPorts(block,port);
assert(isscalar(peers) && getSimulinkBlockHandle(peers.Block,false)==expected, ...
    'Unexpected overlay peer for port %s',port);
if nargin == 4
    assert(strcmp(peers.PortName,peerPort),'Unexpected overlay peer port for %s',port);
end
end

function state = identity(block)
keys = fieldnames(get_param(block,'DialogParameters'));
state = {get_param(block,'ReferenceBlock'),get_param(block,'LinkStatus'), ...
    cellfun(@(key) get_param(block,key),keys,'UniformOutput',false)};
end

function connections = gasPeers(receiver,role)
ports = "A";
if strcmp(role,'internal_pressure')
    ports = ["A","B"];
end
connections = cell(size(ports));
for i = 1:numel(ports)
    peers = simscape.connectedPorts(receiver,ports(i));
    assert(~isempty(peers),'Missing gas conserving connection');
    connections{i} = sort(string({peers.Block}) + ":" + string({peers.PortName}));
end
end
