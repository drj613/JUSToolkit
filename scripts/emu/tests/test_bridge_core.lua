-- scripts/emu/tests/test_bridge_core.lua
-- Run: lua5.4 scripts/emu/tests/test_bridge_core.lua  (from repo root)
package.path = "scripts/emu/?.lua;" .. package.path
local core = require("bridge_core")
local passed, failed = 0, 0
local function eq(a, b, msg)
    if a == b then passed = passed + 1
    else failed = failed + 1; print("FAIL: " .. msg ..
         " expected=" .. tostring(b) .. " got=" .. tostring(a)) end
end

-- jenc: canonical (sorted keys), NULL sentinel, empty-object support
eq(core.jenc({b = 1, a = 2}), '{"a":2,"b":1}', "sorted keys")
eq(core.jenc({1, 2, 3}), "[1,2,3]", "array")
eq(core.jenc(core.NULL), "null", "null sentinel")
eq(core.jenc(core.obj({})), "{}", "empty object not array")
eq(core.jenc({x = core.NULL}), '{"x":null}', "null value kept")
eq(core.jenc('a"\n'), '"a\\"\\n"', "string escaping")
eq(core.jenc("\1"), '"\\u0001"', "control char escaping")
eq(core.jenc(3), "3", "integer stays integral")

-- segment lookup: gaps are force-neutral, not release
local plan = { segments = {
    { ["from"] = 0, ["to"] = 2, buttons = {"Right"} },
    { ["from"] = 5, ["to"] = 6, buttons = {"B"}, touch = nil },
  }, total_frames = 10 }
local m = core.mask_for_frame(plan, 1)
eq(m.buttons.Right, true, "in-segment button")
m = core.mask_for_frame(plan, 3)
eq(next(m.buttons), nil, "gap = empty pressed set")
eq(m.neutral_override, true, "gap keeps override active")
m = core.mask_for_frame(plan, 9)
eq(m.neutral_override, true, "tail keeps override active")

-- pressed list in fixed canonical order
local pl = core.pressed_list({ B = true, A = true, Right = true })
eq(table.concat(pl, ","), "A,B,Right", "canonical button order")

-- plan machine: init -> running -> done, with per-frame records
local pm = core.new_plan_machine(plan, { }, 0)
local rec
for i = 1, 10 do rec = pm:step(function() return {} end) end
eq(pm.state, "done", "plan machine completes")
eq(rec.f, 9, "last frame index")

-- watch values land in the record, nil becomes the NULL sentinel
local pm2 = core.new_plan_machine(plan, { { name = "hp", len = 1 },
                                          { name = "bad", len = 1 } }, 0)
local rec2 = pm2:step(function(spec)
    if spec.name == "hp" then return 40 end
    return nil
end)
eq(rec2.w.hp, 40, "watch value recorded")
eq(rec2.w.bad, core.NULL, "failed watch read becomes NULL")
eq(core.jenc(rec2.w), '{"bad":null,"hp":40}', "watch table encodes canonically")

-- settle machine: settles when framecount hits the sidecar target
local sm = core.new_settle_machine(1000, 60)   -- target fc, max wait
eq(sm:step(1500), "waiting", "not settled at other fc")
eq(sm:step(1000), "settled", "settled at target fc")
local sm2 = core.new_settle_machine(1000, 2)
sm2:step(1500)
eq(sm2:step(1501), "timeout", "settle timeout")

print(string.format("passed=%d failed=%d", passed, failed))
os.exit(failed == 0 and 0 or 1)
