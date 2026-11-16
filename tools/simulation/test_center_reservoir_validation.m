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
