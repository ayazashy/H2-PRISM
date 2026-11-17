function [ok, m] = h2prism_memory_guard(minAvailableMb)
%H2PRISM_MEMORY_GUARD  true if at least minAvailableMb of physical memory is available (unknown counts as not ok).
    m = h2prism_memory_status();
    ok = ~isnan(m.available_mb) && m.available_mb >= minAvailableMb;
end
