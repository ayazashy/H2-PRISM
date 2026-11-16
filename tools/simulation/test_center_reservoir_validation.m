function tests = test_center_reservoir_validation
tests = functiontests(localfunctions);
end

function setupOnce(test)
directory = fileparts(mfilename('fullpath'));
test.TestData.plan = jsondecode(fileread(fullfile(directory,'center_input_plan.json')));
test.TestData.actual = struct('sid','1','linkStatus','resolved', ...
    'library','fl_lib/Gas/Elements/Reservoir (G)','release','2026b', ...
    'area','1.1340','areaUnit','m^2','pressureInput','true','temperatureInput','true', ...
    'reservoirSpec','foundation.enum.ReservoirSpec.StaticPressureTemperature', ...
    'pressureConnected',true,'temperatureConnected',true);
end

function testDocumentedMigrationsPass(test)
a = test.TestData.actual;
plan = test.TestData.plan;
verifyWarningFree(test,@() h2prism_validate_center_reservoir(a,plan));
a.release = '2026a';
a.reservoirSpec = '';
verifyWarningFree(test,@() h2prism_validate_center_reservoir(a,plan));
a.release = '2025b';
a.library = 'fl_lib/Gas/Elements/Controlled Reservoir (G)';
verifyWarningFree(test,@() h2prism_validate_center_reservoir(a,plan));
end

function testInvalidMappingsFail(test)
plan = test.TestData.plan;
cases = {
    'sid', '195', 'Identity';
    'linkStatus', 'inactive', 'Identity';
    'library', 'fl_lib/Gas/Elements/Reservoir (TL)', 'Library';
    'release', '2025b', 'Library';
    'area', '0.01', 'Area';
    'areaUnit', 'cm^2', 'Area';
    'pressureInput', 'false', 'ControlMode';
    'temperatureInput', 'false', 'ControlMode';
    'reservoirSpec', 'foundation.enum.ReservoirSpec.TotalPressureTemperature', 'Specification';
    'pressureConnected', false, 'Connections';
    'temperatureConnected', false, 'Connections';
};
for i = 1:size(cases,1)
    a = test.TestData.actual;
    a.(cases{i,1}) = cases{i,2};
    verifyError(test,@() h2prism_validate_center_reservoir(a,plan),['H2PRISM:Reservoir' cases{i,3}]);
end
end

function testSpaceNormalizedPeerResolvesToPinnedSID(test)
model = test.TestData.plan.model;
inputs = test.TestData.plan.reservoir_inputs;
for i = 1:numel(inputs)
    spec = inputs(i);
    suffix = '';
    if strcmp(spec.converter_sid,'6')
        suffix = '2';
    end
    visualPath = [model '/Simulink-PS' newline 'Converter' suffix];
    reportedPath = [model '/Simulink-PS Converter' suffix];
    expectedSID = [model ':' spec.converter_sid];
    resolve = @(path) resolveExpectedPath(path,reportedPath,expectedSID);
    endpoints = {101,201};
    peer = struct('Block',string(reportedPath),'PortName',"output");
    verifyFalse(test,strcmp(peer.Block,visualPath));
    verifyTrue(test,h2prism_center_connection_matches(peer,expectedSID,resolve,endpoints,endpoints));
    peer.Block = reportedPath;
    verifyTrue(test,h2prism_center_connection_matches(peer,expectedSID,resolve,endpoints,endpoints));
end
end

function testConnectionsRejectWrongCountSIDAndEndpoints(test)
peer = struct('Block',"model/Converter",'PortName',"output");
resolve = @(path) resolveExpectedPath(path,"model/Converter",'model:5');
endpoints = {101,201};
for peers = {peer([]), [peer peer], struct('PortName',"output")}
    verifyFalse(test,h2prism_center_connection_matches(peers{1},'model:5',resolve,endpoints,endpoints));
end
verifyFalse(test,h2prism_center_connection_matches(peer,'model:6',resolve,endpoints,endpoints));
peer.Block = "model/Unresolved";
verifyFalse(test,h2prism_center_connection_matches(peer,'model:5',resolve,endpoints,endpoints));
peer.Block = "model/Converter";
for actual = {{101,202}, {102,201}, {101,-1}, {101,[201 202]}, {201,101}}
    verifyFalse(test,h2prism_center_connection_matches(peer,'model:5',resolve,actual{1},endpoints));
end
end

function sid = resolveExpectedPath(path,expectedPath,expectedSID)
sid = '';
if strcmp(path,expectedPath)
    sid = expectedSID;
end
end
