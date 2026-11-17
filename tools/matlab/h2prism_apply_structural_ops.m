function diffs = h2prism_apply_structural_ops(mdl, ops)
%H2PRISM_APPLY_STRUCTURAL_OPS  Apply the decided structural operations to a LOADED H2Net v1 copy (never a released model).
%   diffs = h2prism_apply_structural_ops('h2net_v1_center', spec.models.<name>.operations)
%   Status: IMPLEMENTED, UNVERIFIED IN MATLAB. Every operation either completes or raises an error naming the operation;
%   the caller (h2prism_build_h2net_v1) then discards the copy. Physical-port compatibility is enforced by Simscape itself:
%   add_line refuses ports of different domains, and connectAny() records which port accepted the connection.
%   Supported ops: set_params, drive_pressure_source, insert_series, replace_two_port, add_pt_sensor,
%   split_pipe_with_leak, apply_h2_tables (handled by the caller), log_existing_or_check (recorded only).
    assert(startsWith(mdl, 'h2net_v1_'), 'h2prism:copy', 'structural ops only on h2net_v1_ copies');
    if ~iscell(ops), ops = num2cell(ops); end
    newBlk = containers.Map();
    diffs = struct('id', {}, 'op', {}, 'detail', {});
    for k = 1:numel(ops)
        o = ops{k};
        try
            switch o.op
                case {'apply_h2_tables', 'log_existing_or_check'}
                    continue
                case 'set_params'
                    b = sidBlock(mdl, o.sid); f = fieldnames(o.params); d = {};
                    for j = 1:numel(f)
                        before = get_param(b, f{j}); set_param(b, f{j}, o.params.(f{j}));
                        d{end + 1} = sprintf('%s: %s -> %s', f{j}, before, get_param(b, f{j})); %#ok<AGROW>
                    end
                    diffs = add(diffs, o, strjoin(d, '; '));
                case 'drive_pressure_source'
                    b = sidBlock(mdl, o.sid);
                    [pIn, oldLine] = signalPortFedByConverter(b);
                    delete_line(oldLine);
                    src = addSignalSource(mdl, [o.id '_src'], o.variable, 'MPa');
                    connectAny(mdl, src.psOut, pIn);
                    diffs = add(diffs, o, sprintf('pressure differential now driven by workspace variable %s (nominal %.4f MPa)', o.variable, o.nominal_dp_MPa));
                case 'insert_series'
                    t = resolve(mdl, o.target_sid, newBlk);
                    tp = gasPort(t, o.target_port);
                    others = netPeers(tp);
                    disconnect(mdl, tp);
                    n = addBlock(mdl, o.block, o.name, t);
                    if isfield(o, 'params'), setAll(n, o.params); end
                    nh = get_param(n, 'PortHandles');
                    if strcmp(o.orientation, 'from_target')        % target -> new.A, new.B -> former peers
                        connectAny(mdl, tp, nh.LConn); connectPeers(mdl, nh.RConn, others);
                    else                                            % former peers -> new.A, new.B -> target
                        connectPeers(mdl, nh.LConn, others); connectAny(mdl, tp, nh.RConn);
                    end
                    if isfield(o, 'thermal'), addThermal(mdl, n, o.thermal); end
                    if isfield(o, 'log'), addLogging(mdl, n, o.log); end
                    if isfield(o, 'variable'), connectAny(mdl, getfield(addSignalSource(mdl, [o.id '_src'], o.variable, 'kg/s'), 'psOut'), [nh.LConn nh.RConn]); end %#ok<GFLD>
                    newBlk(['new:' o.id]) = n;
                    diffs = add(diffs, o, sprintf('inserted %s at %s port %s (%s)', o.name, o.target_sid, o.target_port, o.orientation));
                case 'replace_two_port'
                    b = sidBlock(mdl, o.sid);
                    netP = netPeers(gasPort(b, o.network_port));
                    other = 'B'; if strcmp(o.network_port, 'B'), other = 'A'; end
                    downP = netPeers(gasPort(b, other));
                    pos = get_param(b, 'Position'); old = get_param(b, 'Name');
                    disconnectAll(mdl, b); delete_block(b);
                    n = add_block(o.block, [mdl '/' o.name], 'Position', pos);
                    setAll(n, o.params);
                    nh = get_param(n, 'PortHandles');
                    connectPeers(mdl, nh.LConn, netP);              % A: network side (flow A -> B leaves the network)
                    connectPeers(mdl, nh.RConn, downP);             % B: former downstream (meter / atmospheric reservoir)
                    connectAny(mdl, getfield(addSignalSource(mdl, [o.id '_src'], o.variable, 'kg/s'), 'psOut'), [nh.LConn nh.RConn]); %#ok<GFLD>
                    newBlk(['new:' o.id]) = n;
                    diffs = add(diffs, o, sprintf('replaced %s (SID %s) by %s driven by %s', old, o.sid, o.name, o.variable));
                case 'add_pt_sensor'
                    t = resolve(mdl, o.at_sid, newBlk); tp = gasPort(t, o.at_port);
                    n = addBlock(mdl, o.block, o.name, t); nh = get_param(n, 'PortHandles');
                    connectAny(mdl, tp, [nh.LConn nh.RConn]);
                    addLogging(mdl, n, o.log);
                    diffs = add(diffs, o, sprintf('pressure & temperature sensor %s on SID %s port %s', o.name, o.at_sid, o.at_port));
                case 'split_pipe_with_leak'
                    b = sidBlock(mdl, o.sid);
                    L = str2double(get_param(b, 'length')); La = str2double(get_param(b, 'length_add'));
                    assert(isfinite(L) && L > 0, 'pipe length is not numeric: %s', get_param(b, 'length'));
                    bB = gasPort(b, 'B'); downPeers = netPeers(bB); disconnect(mdl, bB);
                    p2 = addBlock(mdl, getfull(b), [o.name '_pipe2'], b);          % copy of the pipe: identical parameters
                    set_param(b, 'length', num2str(L * o.fraction, 17)); set_param(p2, 'length', num2str(L * (1 - o.fraction), 17));
                    if isfinite(La), set_param(b, 'length_add', num2str(La / 2, 17)); set_param(p2, 'length_add', num2str(La / 2, 17)); end
                    h2 = get_param(p2, 'PortHandles');
                    connectAny(mdl, bB, h2.LConn); connectPeers(mdl, h2.RConn, downPeers);
                    r = addBlock(mdl, o.block, o.name, b); setAll(r, o.params); rh = get_param(r, 'PortHandles');
                    connectAny(mdl, bB, rh.LConn);
                    res = addBlock(mdl, o.reservoir, [o.name '_atm'], r);
                    set_param(res, 'pressure_spec', 'foundation.enum.pressure_spec.atmospheric');
                    resh = get_param(res, 'PortHandles');
                    connectAny(mdl, rh.RConn(1), [resh.LConn resh.RConn]);
                    connectAny(mdl, getfield(addSignalSource(mdl, [o.id '_src'], o.variable, 'm^2'), 'psOut'), [rh.LConn rh.RConn]); %#ok<GFLD>
                    diffs = add(diffs, o, sprintf('pipe SID %s split at %.2f L (%.1f m + %.1f m); leak branch %s driven by %s', ...
                        o.sid, o.fraction, L * o.fraction, L * (1 - o.fraction), o.name, o.variable));
                otherwise
                    error('h2prism:op', 'unknown structural op %s', o.op);
            end
        catch err
            error('h2prism:structural', 'structural op %s (%s) failed: %s', o.id, o.op, err.message);
        end
    end
end

% ------------------------------------------------------------------------------------------------ helpers
function d = add(d, o, txt)
    d(end + 1) = struct('id', o.id, 'op', o.op, 'detail', txt);
end

function b = sidBlock(mdl, sid)
    b = Simulink.ID.getFullName([mdl ':' sid]);
end

function b = resolve(mdl, key, newBlk)
    if startsWith(key, 'new:'), b = getfull(newBlk(key)); else, b = sidBlock(mdl, key); end
end

function p = getfull(h)
    if ischar(h), p = h; else, p = getfullname(h); end
end

function h = gasPort(b, AB)
    ph = get_param(b, 'PortHandles');
    if strcmp(AB, 'A'), h = ph.LConn(1); else, h = ph.RConn(1); end
end

function peers = netPeers(port)
    % all OTHER ports connected to the same physical line(s) as PORT
    peers = [];
    ln = get_param(port, 'Line');
    if ln == -1, return, end
    pts = [get_param(ln, 'SrcPortHandle'); get_param(ln, 'DstPortHandle')];
    peers = setdiff(unique(pts(pts > 0)), port);
end

function disconnect(mdl, port) %#ok<INUSD>
    ln = get_param(port, 'Line');
    if ln ~= -1, delete_line(ln); end
end

function disconnectAll(mdl, b)
    ph = get_param(b, 'PortHandles');
    for h = [ph.LConn ph.RConn], disconnect(mdl, h); end
end

function connectPeers(mdl, cand, peers)
    for p = peers(:)', connectAny(mdl, p, cand); end
end

function used = connectAny(mdl, src, candidates)
    % connect SRC to the first candidate port that Simscape accepts (domain-checked by add_line); error if none
    for c = candidates(:)'
        try
            add_line(mdl, src, c, 'autorouting', 'smart'); used = c; return
        catch
        end
    end
    error('h2prism:port', 'no compatible free port accepted the connection');
end

function n = addBlock(mdl, lib, name, near)
    p = get_param(near, 'Position');
    lib = libPath(lib);
    n = add_block(lib, [mdl '/' name], 'MakeNameUnique', 'on', 'Position', p + [60 60 60 60]);
end

function p = libPath(lib)
    % library names may contain line breaks ("Local Restriction\n(G)"): resolve by the name without whitespace
    if getSimulinkBlockHandle(lib) ~= -1 || ~startsWith(lib, 'fl_lib/'), p = lib; return, end
    load_system('fl_lib');
    want = regexprep(lib(find(lib == '/', 1, 'last') + 1:end), '\s', '');
    hits = find_system('fl_lib', 'LookUnderMasks', 'all', 'FollowLinks', 'on');
    m = hits(cellfun(@(h) strcmp(regexprep(h(find(h == '/', 1, 'last') + 1:end), '\s', ''), want), hits));
    assert(numel(m) == 1, 'h2prism:lib', 'library block %s not found uniquely', lib);
    p = m{1};
end

function setAll(b, params)
    f = fieldnames(params);
    for j = 1:numel(f), set_param(b, f{j}, params.(f{j})); end
end

function [pIn, oldLine] = signalPortFedByConverter(b)
    ph = get_param(b, 'PortHandles');
    for h = [ph.LConn ph.RConn]
        ln = get_param(h, 'Line');
        if ln == -1, continue, end
        pts = [get_param(ln, 'SrcPortHandle'); get_param(ln, 'DstPortHandle')];
        for q = pts(pts > 0 & pts ~= h)'
            if contains(get_param(get_param(q, 'Parent'), 'ReferenceBlock'), 'Simulink-PS')
                pIn = h; oldLine = ln; return
            end
        end
    end
    error('h2prism:port', 'no physical-signal input fed by a Simulink-PS Converter on %s', b);
end

function s = addSignalSource(mdl, name, variable, unit)
    fw = add_block('simulink/Sources/From Workspace', [mdl '/' name], 'MakeNameUnique', 'on', 'VariableName', variable);
    cv = add_block(libPathNesl('Simulink-PS Converter'), [mdl '/' name '_ps'], 'MakeNameUnique', 'on');
    set_param(cv, 'Unit', unit);
    fh = get_param(fw, 'PortHandles'); chh = get_param(cv, 'PortHandles');
    add_line(mdl, fh.Outport(1), chh.Inport(1), 'autorouting', 'smart');
    s = struct('fromWorkspace', fw, 'converter', cv, 'psOut', chh.RConn(1));
end

function addLogging(mdl, sensor, logc)
    sh = get_param(sensor, 'PortHandles');
    outs = [sh.RConn sh.LConn];
    if isfield(logc, 'port_index'), outs = sh.RConn(logc.port_index); end   % e.g. T output of the P&T sensor (UNVERIFIED index)
    cv = add_block(libPathNesl('PS-Simulink Converter'), [mdl '/' logc.variable '_ps'], 'MakeNameUnique', 'on');
    set_param(cv, 'Unit', logc.unit);
    ch = get_param(cv, 'PortHandles');
    connectAny(mdl, ch.LConn(1), outs);
    tw = add_block('simulink/Sinks/To Workspace', [mdl '/' logc.variable], 'MakeNameUnique', 'on', ...
        'VariableName', logc.variable, 'SaveFormat', 'Timeseries');
    th = get_param(tw, 'PortHandles');
    add_line(mdl, ch.Outport(1), th.Inport(1), 'autorouting', 'smart');
end

function addThermal(mdl, pipeBlk, th)
    ts = addBlock(mdl, th.temperature_source, [get_param(pipeBlk, 'Name') '_Tsrc'], pipeBlk);
    dp = fieldnames(get_param(ts, 'DialogParameters'));
    tname = dp(ismember(lower(dp), {'t', 'temperature', 't_const'}));
    assert(~isempty(tname), 'h2prism:param', 'Temperature Source parameter not found (%s)', strjoin(dp, ','));
    set_param(ts, tname{1}, th.temperature_K);
    tr = addBlock(mdl, th.thermal_reference, [get_param(pipeBlk, 'Name') '_Tref'], pipeBlk);
    ph = get_param(pipeBlk, 'PortHandles'); tsh = get_param(ts, 'PortHandles'); trh = get_param(tr, 'PortHandles');
    hPort = setdiff([ph.LConn ph.RConn], [ph.LConn(1) ph.RConn(1)]);     % pipe thermal port H
    assert(~isempty(hPort), 'h2prism:port', 'pipe thermal port H not found');
    connectAny(mdl, hPort(1), [tsh.LConn tsh.RConn]);
    connectAny(mdl, trh.LConn(1), [tsh.LConn tsh.RConn]);
end

function p = libPathNesl(name)
    load_system('nesl_utility');
    hits = find_system('nesl_utility', 'SearchDepth', 1, 'Name', name);
    assert(numel(hits) == 1, 'h2prism:lib', 'nesl_utility/%s not found', name);
    p = hits{1};
end
