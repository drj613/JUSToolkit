-- scripts/emu/spike/s4_savestate_probe.lua
-- S4: async savestate semantics. Run with MODE="save" in a battle at a
-- memorable moment, then MODE="load" after playing further.
local MODE = "load"  -- "save" | "load"
local issued_at, last_fc, cbs = nil, nil, 0
local marker = math.random(1, 1000000)  -- Lua VM state: should survive load

function _Update()
    local fc = emu.framecount()
    if issued_at == nil then
        issued_at, last_fc = fc, fc
        if MODE == "save" then
            savestate.save("/tmp/jus_emu_spike_state.mln")
            print("save issued at frame " .. fc .. " marker=" .. marker)
        else
            savestate.load("/tmp/jus_emu_spike_state.mln")
            print("load issued at frame " .. fc .. " marker=" .. marker)
        end
        return
    end
    -- log every callback for 120 callbacks so the settle profile is visible
    cbs = cbs + 1
    if cbs <= 120 and fc ~= last_fc then
        print(string.format("cb %d: framecount=%d (issued_at=%d) marker=%d",
                            cbs, fc, issued_at, marker))
    end
    last_fc = fc
end
