function m = h2prism_memory_status()
%H2PRISM_MEMORY_STATUS  Physical memory (MB) and MATLAB process use. NaN where the platform does not report it.
    m = struct('total_mb', NaN, 'available_mb', NaN, 'matlab_used_mb', NaN, 'source', 'unavailable');
    if ispc
        [u, s] = memory;
        m.total_mb = s.PhysicalMemory.Total / 2^20;
        m.available_mb = s.PhysicalMemory.Available / 2^20;
        m.matlab_used_mb = u.MemUsedMATLAB / 2^20;
        m.source = 'memory()';
    end
end
