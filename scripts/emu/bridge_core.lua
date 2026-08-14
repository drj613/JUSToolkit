-- scripts/emu/bridge_core.lua
-- Pure logic for the agent bridge: canonical JSON, plan/settle machines.
-- No emulator or filesystem access; unit-tested with the lua5.4 CLI.
local M = {}

M.NULL = setmetatable({}, { __tostring = function() return "null" end })
local OBJ = {}
function M.obj(t) return setmetatable(t, OBJ) end  -- force object encoding

M.BUTTON_ORDER = { "A","B","Select","Start","Right","Left","Up","Down",
                   "R","L","X","Y" }

local function esc(s)
    return (s:gsub('[%c"\\]', function(c)
        if c == '"' then return '\\"' end
        if c == "\\" then return "\\\\" end
        if c == "\n" then return "\\n" end
        if c == "\r" then return "\\r" end
        if c == "\t" then return "\\t" end
        return string.format("\\u%04x", c:byte())
    end))
end

function M.jenc(v)
    if v == M.NULL or v == nil then return "null" end
    local t = type(v)
    if t == "number" then
        if math.type(v) == "integer" then return string.format("%d", v) end
        return string.format("%.17g", v)
    end
    if t == "boolean" then return tostring(v) end
    if t == "string" then return '"' .. esc(v) .. '"' end
    if t == "table" then
        local is_obj = getmetatable(v) == OBJ
        if not is_obj and (#v > 0 or next(v) == nil) then
            local parts = {}
            for _, x in ipairs(v) do parts[#parts+1] = M.jenc(x) end
            return "[" .. table.concat(parts, ",") .. "]"
        end
        local keys = {}
        for k in pairs(v) do keys[#keys+1] = tostring(k) end
        table.sort(keys)
        local parts = {}
        for _, k in ipairs(keys) do
            parts[#parts+1] = '"' .. esc(k) .. '":' .. M.jenc(v[k])
        end
        return "{" .. table.concat(parts, ",") .. "}"
    end
    error("unencodable type: " .. t)
end

-- Which buttons/touch are active on a logical plan frame.
-- Gaps and tail return an empty pressed set with neutral_override=true:
-- the override stays on for the whole plan (physical input stays locked out).
function M.mask_for_frame(plan, frame)
    for _, seg in ipairs(plan.segments) do
        if frame >= seg["from"] and frame <= seg["to"] then
            local buttons = {}
            if seg.buttons then
                for _, b in ipairs(seg.buttons) do buttons[b] = true end
            end
            return { buttons = buttons, touch = seg.touch,
                     neutral_override = true }
        end
    end
    return { buttons = {}, touch = nil, neutral_override = true }
end

function M.pressed_list(buttons)
    local out = {}
    for _, b in ipairs(M.BUTTON_ORDER) do
        if buttons[b] then out[#out+1] = b end
    end
    return out
end

-- Plan machine: one step per _Update(); read_watch_fn is injected so the
-- machine stays testable without an emulator.
function M.new_plan_machine(plan, watches, input_apply_offset)
    local pm = { plan = plan, watches = watches or {}, frame = 0,
                 offset = input_apply_offset or 0, state = "running" }
    function pm:step(read_watch_fn)
        local eff = self.frame + self.offset
        local mask = M.mask_for_frame(self.plan, eff)
        local w = M.obj({})
        for _, spec in ipairs(self.watches) do
            local v = read_watch_fn(spec)
            w[spec.name] = (v == nil) and M.NULL or v
        end
        local rec = { f = self.frame, latch = M.pressed_list(mask.buttons),
                      w = w }
        self.frame = self.frame + 1
        if self.frame >= self.plan.total_frames then self.state = "done" end
        return rec, mask
    end
    return pm
end

-- Settle machine: a load has settled when framecount == target (the
-- sidecar's framecount_at_save; savestates restore the frame counter).
function M.new_settle_machine(target_fc, max_waits)
    local sm = { target = target_fc, waited = 0, max = max_waits }
    function sm:step(fc)
        if fc == self.target then return "settled" end
        self.waited = self.waited + 1
        if self.waited >= self.max then return "timeout" end
        return "waiting"
    end
    return sm
end

return M
