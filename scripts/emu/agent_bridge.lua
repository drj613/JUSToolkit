-- scripts/emu/agent_bridge.lua
-- Agent control bridge. Load once in melonDS's Lua console.
-- Protocol: scripts/emu/jus_ipc.py docstring + spec §3.
package.path = (os.getenv("JUS_EMU_SRC") or "scripts/emu") .. "/?.lua;"
    .. package.path
local core = require("bridge_core")

local IPC_DIR = os.getenv("JUS_EMU_DIR") or "/tmp/jus_emu"
local BUS = "ARM9 System Bus"
local POLL_INTERVAL = 10
local SETTLE_MAX = 120            -- callbacks; S4-informed
local SAVE_STABLE_POLLS = 3       -- save done = file size stable this long
local FLUSH_EVERY = 600
local MAIN_RAM_LO, MAIN_RAM_HI = 0x02000000, 0x02400000
local INPUT_APPLY_OFFSET = 0      -- set from the S3 finding in README

local MAX_CATCHUP = 8            -- plan frames advanced in one callback

local session = tostring(os.time()) .. "-" .. tostring(math.random(1000000))
local state = "idle"  -- idle|plan_running|loading_state|saving_state|flushing
local tick = 0
local last_fc = nil              -- framecount at the previous callback
local pm, run_dir, cmd_id, log_buf = nil, nil, nil, {}
local settle, pending_plan = nil, nil
local saving = nil                -- {slot, path, last_size, stable, id}
local default_watches = {}

-- ---------- io ------------------------------------------------------------
local function write_atomic(path, content)
    local f = assert(io.open(path .. ".tmp", "w"))
    f:write(content); f:close()
    assert(os.rename(path .. ".tmp", path))  -- POSIX rename clobbers
end

local function heartbeat()
    write_atomic(IPC_DIR .. "/heartbeat.json", core.jenc(core.obj({
        session = session, framecount = emu.framecount(),
        wallclock = os.time(), state = state })))
end

local function ack(id, ok, payload)
    if id == nil then return end
    local body = core.obj({ id = id, epoch = session, ok = ok })
    if ok then body.result = payload else body.error = tostring(payload) end
    write_atomic(IPC_DIR .. "/ack/" .. id .. ".json", core.jenc(body))
end

-- ---------- input (see plan header for set({})/set(nil) semantics) --------
local function force_neutral() joypad.set({}); input.NDSTapUp() end
local function release_override() joypad.set(nil); input.NDSTapUp() end

-- ---------- memory --------------------------------------------------------
local function valid_ptr(p)
    return p >= MAIN_RAM_LO and p < MAIN_RAM_HI and p % 4 == 0
end

local function resolve_chain(chain)
    local p = chain[1]
    for i = 2, #chain do
        if not (p >= MAIN_RAM_LO and p < MAIN_RAM_HI) then return nil end
        p = memory.read_u32_le(p, BUS)
        if not valid_ptr(p) then return nil end
        p = p + chain[i]
    end
    return p
end

local function read_watch(w)
    local addr
    if w.chain then
        local base = resolve_chain(w.chain)
        if base == nil then return nil end
        addr = base + (w.offset or 0)
    else
        addr = w.addr
    end
    if w.len == 1 then return memory.read_u8(addr, BUS) end
    if w.len == 2 then return memory.read_u16_le(addr, BUS) end
    if w.len == 4 then return memory.read_u32_le(addr, BUS) end
    return memory.read_bytes_as_array(addr, w.len, BUS)
end

-- ---------- logging -------------------------------------------------------
local function flush_log()
    if run_dir == nil or #log_buf == 0 then return end
    local f = assert(io.open(run_dir .. "/log.jsonl", "a"))
    f:write(table.concat(log_buf, "\n")); f:write("\n"); f:close()
    log_buf = {}
end

-- ---------- savestate sidecars -------------------------------------------
local function state_path(slot) return IPC_DIR .. "/states/" .. slot end

local function write_sidecar(slot)
    write_atomic(state_path(slot) .. ".meta.json", core.jenc(core.obj({
        slot = slot, framecount_at_save = emu.framecount(),
        session = session, saved_at = os.time() })))
end

local function read_sidecar(slot)
    local f = io.open(state_path(slot) .. ".meta.json", "r")
    if f == nil then return nil end
    local body = f:read("a"); f:close()
    local fc = body:match('"framecount_at_save":(%d+)')
    return fc and tonumber(fc) or nil
end

-- ---------- plan lifecycle -----------------------------------------------
local function abort_plan(reason)
    force_neutral()
    if run_dir then
        log_buf[#log_buf+1] = core.jenc(core.obj({ aborted = tostring(reason),
                                                   f = pm and pm.frame or 0 }))
        flush_log()
    end
    ack(cmd_id, false, reason)
    release_override()
    pm, run_dir, cmd_id, pending_plan, settle, state =
        nil, nil, nil, nil, nil, "idle"
end

local function finish_plan()
    force_neutral()
    flush_log()
    write_atomic(run_dir .. "/done-" .. cmd_id .. ".json",
                 core.jenc(core.obj({ frames = pm.frame, ok = true,
                                      epoch = session })))
    ack(cmd_id, true, core.obj({ frames = pm.frame,
                                 log = run_dir .. "/log.jsonl" }))
    release_override()
    pm, run_dir, cmd_id, state = nil, nil, nil, "idle"
end

local function start_plan(p)
    pm = core.new_plan_machine(p, p.watches or default_watches,
                               INPUT_APPLY_OFFSET)
    log_buf = {}
    state = "plan_running"
end

-- One plan frame. Lua runs on the GUI thread via a queued signal, so a
-- callback is NOT one emulated frame: advance by the framecount delta so the
-- plan keeps its schedule, and record the delta so skips are visible in the log.
local function plan_step(fc, elapsed)
    local rec, mask
    local steps = math.min(elapsed, MAX_CATCHUP)
    for i = 1, steps do
        rec, mask = pm:step(read_watch)
        rec.fc = fc
        rec.d = elapsed
        log_buf[#log_buf+1] = core.jenc(rec)
        if pm.state == "done" then break end
    end
    if next(mask.buttons) then joypad.set(mask.buttons) else joypad.set({}) end
    if mask.touch then input.NDSTapDown(mask.touch.x, mask.touch.y)
    else input.NDSTapUp() end
    if #log_buf >= FLUSH_EVERY then flush_log() end
    if pm.state == "done" then finish_plan() end
end

-- ---------- state machines: load / save ----------------------------------
local function begin_state_load(id, slot, then_plan)
    local target = read_sidecar(slot)
    if target == nil then
        ack(id, false, "no sidecar for state '" .. slot ..
            "' (unknown or pre-protocol savestate)")
        return
    end
    force_neutral()                          -- spec: neutral before load
    cmd_id, pending_plan = id, then_plan
    savestate.load(state_path(slot) .. ".mln")
    settle = core.new_settle_machine(target, SETTLE_MAX)
    state = "loading_state"
end

local function settle_step()
    local r = settle:step(emu.framecount())
    if r == "settled" then
        settle = nil
        if pending_plan then
            local p = pending_plan; pending_plan = nil
            start_plan(p)
        else
            ack(cmd_id, true, core.obj({ loaded = true,
                                         framecount = emu.framecount() }))
            cmd_id, state = nil, "idle"
            release_override()
        end
    elseif r == "timeout" then
        abort_plan("state load did not settle (framecount never hit target)")
    end
end

local function begin_state_save(id, slot)
    saving = { slot = slot, path = state_path(slot) .. ".mln",
               last_size = -1, stable = 0, waited = 0, id = id }
    os.remove(saving.path)
    savestate.save(saving.path)
    state = "saving_state"
end

local function saving_step()
    local f = io.open(saving.path, "rb")
    local size = -1
    if f then size = f:seek("end"); f:close() end
    if size > 0 and size == saving.last_size then
        saving.stable = saving.stable + 1
        if saving.stable >= SAVE_STABLE_POLLS then
            write_sidecar(saving.slot)
            ack(saving.id, true, core.obj({ slot = saving.slot, bytes = size }))
            saving, state = nil, "idle"
            return
        end
    else
        saving.stable = 0
    end
    saving.last_size = size
    saving.waited = saving.waited + 1
    if saving.waited > SETTLE_MAX then
        ack(saving.id, false, "savestate.save produced no stable file")
        saving, state = nil, "idle"
    end
end

-- ---------- commands ------------------------------------------------------
local handlers = {}

function handlers.status(args)
    return core.obj({ state = state, framecount = emu.framecount(),
                      session = session,
                      plan = pm and pm.plan.name or core.NULL })
end

function handlers.peek(args)
    local v = read_watch({ chain = args.chain, offset = args.offset,
                           addr = args.addr, len = args.len })
    if v == nil then error("pointer chain invalid (not in battle?)") end
    return core.obj({ value = v })
end

function handlers.poke(args)
    memory.write_bytes_as_array(args.addr, args.bytes, BUS)
    return core.obj({ written = #args.bytes })
end

function handlers.dump(args)
    local f = assert(io.open(args.outfile, "wb"))
    local addr, remaining = args.start, args["end"] - args.start
    while remaining > 0 do
        local n = math.min(remaining, 4096)
        local bytes = memory.read_bytes_as_array(addr, n, BUS)
        local chars = {}
        for i = 1, n do chars[i] = string.char(bytes[i]) end
        f:write(table.concat(chars))
        addr, remaining = addr + n, remaining - n
    end
    f:close()
    return core.obj({ bytes = args["end"] - args.start,
                      outfile = args.outfile })
end

function handlers.set_watches(args)
    if #args.specs > 32 then error("too many watches") end
    local total = 0
    for _, s in ipairs(args.specs) do total = total + (s.len or 0) end
    if total > 512 then error("watch byte budget exceeded") end
    default_watches = args.specs
    return core.obj({ count = #args.specs,
                      note = "applies to subsequent plans without watches" })
end

function handlers.selftest(args)
    -- Synchronous half only. The async half is `state save _selftest`
    -- followed by `state load _selftest`, driven by the CLI (see README).
    local bytes = memory.read_bytes_as_array(0x021DF000, 512, BUS)
    return core.obj({ framecount = emu.framecount(), read_ok = #bytes == 512,
                      session = session })
end

local function load_plan_file(path)
    local pf = io.open(path, "r")
    if pf == nil then return nil, "plan file missing" end
    local body = pf:read("a"); pf:close()
    local chunk = load(body, "plan", "t", {})
    if chunk == nil then return nil, "plan parse error" end
    local ok, p = pcall(chunk)
    if not ok or type(p) ~= "table" then return nil, "plan not a table" end
    return p
end

local function poll_commands()
    local inbox = IPC_DIR .. "/cmd/inbox.lua"
    local f = io.open(inbox, "r")
    if f == nil then return end
    local content = f:read("a"); f:close()
    os.remove(inbox)
    local chunk = load(content, "cmd", "t", {})
    if chunk == nil then return end
    local ok, cmd = pcall(chunk)
    if not ok or type(cmd) ~= "table" then return end
    if cmd.epoch ~= session then
        ack(cmd.id, false, "stale epoch " .. tostring(cmd.epoch))
        return
    end
    if cmd.op == "run_plan" then
        local p, err = load_plan_file(cmd.args.plan_path)
        if p == nil then ack(cmd.id, false, err); return end
        run_dir, cmd_id = cmd.args.run_dir, cmd.id
        if p.load_state then
            begin_state_load(cmd.id, p.load_state, p)
        else
            start_plan(p)
        end
        return
    end
    if cmd.op == "state_load" then
        begin_state_load(cmd.id, cmd.args.slot, nil); return
    end
    if cmd.op == "state_save" then
        begin_state_save(cmd.id, cmd.args.slot); return
    end
    local h = handlers[cmd.op]
    if h == nil then
        ack(cmd.id, false, "unknown op " .. tostring(cmd.op)); return
    end
    local hok, result = pcall(h, cmd.args)
    ack(cmd.id, hok, result)
end

local function check_stop()
    local f = io.open(IPC_DIR .. "/stop.flag", "r")
    if f then
        f:close(); os.remove(IPC_DIR .. "/stop.flag")
        if state == "plan_running" or state == "loading_state" then
            abort_plan("stopped by client")
        end
    end
end

-- ---------- main loop -----------------------------------------------------
os.execute("mkdir -p " .. IPC_DIR .. "/cmd " .. IPC_DIR .. "/ack " ..
           IPC_DIR .. "/runs " .. IPC_DIR .. "/states")
release_override()
heartbeat()
print("agent_bridge up, session " .. session)

function _Update()
    tick = tick + 1
    local ok, err = pcall(function()
        local fc = emu.framecount()
        local elapsed = (last_fc == nil) and 1 or (fc - last_fc)
        last_fc = fc
        -- Only advance a plan when the emulator actually advanced frames.
        if state == "plan_running" and elapsed > 0 then plan_step(fc, elapsed) end
        if state == "loading_state" then settle_step() end
        if state == "saving_state" then saving_step() end
        if tick % POLL_INTERVAL == 0 then
            heartbeat()
            check_stop()
            if state == "idle" then poll_commands() end
        end
    end)
    if not ok then
        pcall(force_neutral)
        pcall(abort_plan, "lua error: " .. tostring(err))
        pcall(release_override)
    end
end
