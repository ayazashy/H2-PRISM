function h2prism_phase3_normal_probe(runDir)
% Probe an isolated copy. The launcher/exporter are never executed or modified.
cd(runDir);
model = 'Normal_HNetwork_gest_center';
disp(version);
ver;
load_system('simulink');
load_system('fl_lib');
load_system(fullfile(runDir, [model '.slx']));
cleanup = onCleanup(@() close_system(model, 0)); %#ok<NASGU>
out = sim(model, 'StopTime', '1.6', 'SolverType', 'Fixed-step', ...
    'Solver', 'ode14x', 'FixedStep', '0.8');
names = [compose("pressure_sensor%d", 1:10), compose("flow_sensor%d", 1:3)];
clock = out.pressure_sensor1.Time(:);
rows = table(clock, 'VariableNames', {'Timestamp'});
for signal = names
    log = out.get(char(signal));
    assert(isequal(log.Time(:), clock), 'Sensor clocks differ');
    rows.(char(signal)) = log.Data(:);
end
output = fullfile(runDir, 'normal_probe.csv');
assert(~isfile(output), 'Probe output already exists');
writetable(rows, output);
end
