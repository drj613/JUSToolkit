-- scripts/emu/spike/s3_input_readback.lua
-- Latch B on rel frames 60-62; read back the CORE-COMMITTED mask.
-- PASS: committed_B=true on exactly 3 consecutive rel values.
-- Record (first committed rel) - 60 as INPUT_APPLY_OFFSET.
local start, log = nil, {}
function _Update()
    local fc = emu.framecount()
    if start == nil then start = fc; joypad.set({}) end
    local rel = fc - start
    if rel >= 60 and rel <= 62 then joypad.set({B = true})
    elseif rel == 63 then joypad.set({}) end
    if rel >= 55 and rel <= 70 then
        local c = joypad.get_committed()
        log[#log+1] = string.format("rel=%d committed_B=%s", rel,
                                    tostring(c.B))
    end
    if rel == 71 then
        joypad.set(nil)
        for _, line in ipairs(log) do print(line) end
    end
end
