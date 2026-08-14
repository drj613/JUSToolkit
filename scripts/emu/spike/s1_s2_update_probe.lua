-- scripts/emu/spike/s1_s2_update_probe.lua
-- S1: does _Update() fire per frame? during pause? during GDB stop?
-- S2: is synchronous file I/O safe from the callback? (timing judged
--     externally by s2_timing_monitor.py; os.clock() is CPU-time only)
local count = 0

function _Update()
    count = count + 1
    -- representative I/O: heartbeat-like rename publication every frame
    local f = io.open("/tmp/jus_emu_spike.tmp", "w")
    f:write(string.format('{"count":%d,"frame":%d}', count, emu.framecount()))
    f:close()
    os.rename("/tmp/jus_emu_spike.tmp", "/tmp/jus_emu_spike.json")
    -- representative memory load: 512 bytes over the ARM9 bus
    memory.read_bytes_as_array(0x021DF000, 512, "ARM9 System Bus")
    if count % 600 == 0 then
        print("frames=" .. count .. " framecount=" .. emu.framecount())
    end
end
