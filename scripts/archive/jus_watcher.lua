-- Jump Ultimate Stars - RAM Watcher for DeSmuME
--
-- !! WINDOWS ONLY !!
-- DeSmuME Lua scripting is only available on Windows builds.
-- For Mac/Linux, use scripts/gdb/jus_gdb_watcher.py with melonDS instead.
--
-- This script monitors key game values during battle and logs changes.
-- Useful for reverse engineering damage formulas, finding new addresses, etc.
--
-- Usage:
--   1. Open DeSmuME (Windows) with JUS ROM loaded
--   2. Tools -> Lua Scripting -> New Lua Script Window
--   3. Load this script
--   4. Enter a battle - values will be displayed on screen
--
-- Note: Addresses are from Action Replay codes and may need adjustment.

-- ============================================================================
-- KNOWN ADDRESSES (from AR codes)
-- ============================================================================

-- Game ID: AJUJ-65E1D889

local ADDR = {
    -- Battle state (from AR codes)
    battle_timer     = 0x021DEA71,  -- 1 byte, counts down from 99
    battle_timer_wifi = 0x021E29B0, -- 2 bytes (wifi mode)

    -- Player health (from "Refill Health" codes)
    -- Spaced 0x50 (80 bytes) apart - battle player struct size
    player1_hp       = 0x021DF1D5,
    player2_hp       = 0x021DF225,
    player3_hp       = 0x021DF275,
    player4_hp       = 0x021DF2C5,

    -- Special meter (from "Unlimited Special" codes)
    special_meter_1  = 0x021DF731,  -- 1 byte
    special_meter_2  = 0x021DF8B1,  -- 1 byte

    -- Player state pointers (wifi mode) - points to character state struct
    player1_state_ptr = 0x021E2A7C,
    player2_state_ptr = 0x021E2A80,
    player3_state_ptr = 0x021E2A84,
    player4_state_ptr = 0x021E2A88,

    -- Koma sprites (for visual debugging)
    koma_sprite_1    = 0x021DB611,
    koma_sprite_2    = 0x021DB609,

    -- Currency/Progress (from "Infinite Gems" codes)
    gems_start       = 0x020B7718,  -- 6 consecutive u32 values
    koma_points      = 0x020B76C8,  -- Koma points

    -- Deck/Menu
    active_deck      = 0x020AFEB4,  -- Current deck index
    koma_flags_start = 0x020B0BAC,  -- Array of unlock flags
    course_flags     = 0x020B0C93,  -- Course unlock flags
    side_koma_start  = 0x0228AAB0,  -- Side koma holder (6 slots)

    -- Code hook point (from "Infinite Health" code)
    health_code_addr = 0x020784FC,  -- ARM9 code that handles HP
}

-- Character state struct offsets (from wifi codes)
-- These are offsets from the player state pointer
local CHAR_OFFSETS = {
    ground_air    = 0x0078,  -- 0x00=air, 0x22=ground
    positive_status = 0x0088,  -- Status effect ID
    negative_status = 0x00A0,  -- Status flags
    jump_count    = 0x00D9,  -- Current jump count
    air_actions   = 0x00DA,  -- Air action count
    defense_timer = 0x0102,  -- Defense duration remaining
}

-- ============================================================================
-- CONFIGURATION
-- ============================================================================

local config = {
    show_overlay = true,      -- Display values on screen
    log_changes = true,       -- Print changes to console
    log_file = nil,           -- Set to filename to write log
    watch_interval = 1,       -- Frames between checks (1 = every frame)

    -- Colors for overlay
    colors = {
        bg = 0x80000000,      -- Semi-transparent black
        text = 0xFFFFFFFF,    -- White
        highlight = 0xFF00FF00, -- Green for changes
        warning = 0xFFFF0000,  -- Red for damage
    }
}

-- ============================================================================
-- STATE TRACKING
-- ============================================================================

local state = {
    frame_count = 0,
    in_battle = false,

    -- Previous values for change detection
    prev = {
        leader_hp = 0,
        nonleader_hp = 0,
        special_1 = 0,
        special_2 = 0,
        timer = 0,
    },

    -- Change history (for logging)
    history = {},
}

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

local function read_byte(addr)
    return memory.readbyte(addr)
end

local function read_word(addr)
    return memory.readword(addr)  -- 16-bit
end

local function read_dword(addr)
    return memory.readdword(addr)  -- 32-bit
end

local function log_msg(msg)
    print(string.format("[%06d] %s", state.frame_count, msg))
    table.insert(state.history, {
        frame = state.frame_count,
        message = msg,
    })
end

-- ============================================================================
-- BATTLE DETECTION
-- ============================================================================

local function detect_battle()
    -- Heuristic: if timer is non-zero and health values look valid,
    -- we're probably in battle
    local timer = read_byte(ADDR.battle_timer)
    local hp = read_byte(ADDR.leader_hp)

    -- Timer counts down from 99, HP is typically 50-200
    if timer > 0 and timer <= 99 and hp > 0 and hp <= 255 then
        return true
    end
    return false
end

-- ============================================================================
-- VALUE READING
-- ============================================================================

local function read_battle_state()
    return {
        timer = read_byte(ADDR.battle_timer),
        leader_hp = read_byte(ADDR.leader_hp),
        nonleader_hp = read_byte(ADDR.nonleader_hp),
        special_1 = read_byte(ADDR.special_meter_1),
        special_2 = read_byte(ADDR.special_meter_2),
    }
end

local function read_currency()
    local gems = {}
    for i = 0, 5 do
        gems[i+1] = read_dword(ADDR.gems_start + (i * 4))
    end
    return {
        gems = gems,
        koma_points = read_dword(ADDR.koma_points),
    }
end

-- ============================================================================
-- CHANGE DETECTION
-- ============================================================================

local function check_for_changes(current)
    local changes = {}

    if current.leader_hp ~= state.prev.leader_hp then
        local diff = current.leader_hp - state.prev.leader_hp
        local direction = diff > 0 and "+" or ""
        table.insert(changes, string.format("Leader HP: %d -> %d (%s%d)",
            state.prev.leader_hp, current.leader_hp, direction, diff))
    end

    if current.nonleader_hp ~= state.prev.nonleader_hp then
        local diff = current.nonleader_hp - state.prev.nonleader_hp
        local direction = diff > 0 and "+" or ""
        table.insert(changes, string.format("Non-leader HP: %d -> %d (%s%d)",
            state.prev.nonleader_hp, current.nonleader_hp, direction, diff))
    end

    if current.special_1 ~= state.prev.special_1 then
        table.insert(changes, string.format("Special 1: %d -> %d",
            state.prev.special_1, current.special_1))
    end

    if current.special_2 ~= state.prev.special_2 then
        table.insert(changes, string.format("Special 2: %d -> %d",
            state.prev.special_2, current.special_2))
    end

    -- Update previous state
    state.prev = {
        leader_hp = current.leader_hp,
        nonleader_hp = current.nonleader_hp,
        special_1 = current.special_1,
        special_2 = current.special_2,
        timer = current.timer,
    }

    return changes
end

-- ============================================================================
-- DISPLAY
-- ============================================================================

local function draw_overlay(battle)
    if not config.show_overlay then return end

    local x, y = 5, 5
    local line_height = 10

    -- Background
    gui.box(x-2, y-2, x+120, y + (7 * line_height) + 2, config.colors.bg)

    -- Title
    gui.text(x, y, "JUS Watcher", config.colors.text)
    y = y + line_height

    if state.in_battle then
        -- Battle values
        gui.text(x, y, string.format("Timer: %02d", battle.timer), config.colors.text)
        y = y + line_height

        gui.text(x, y, string.format("Leader HP: %d", battle.leader_hp),
            battle.leader_hp < state.prev.leader_hp and config.colors.warning or config.colors.text)
        y = y + line_height

        gui.text(x, y, string.format("Partner HP: %d", battle.nonleader_hp), config.colors.text)
        y = y + line_height

        gui.text(x, y, string.format("Special: %d/%d", battle.special_1, battle.special_2), config.colors.text)
        y = y + line_height

    else
        gui.text(x, y, "Not in battle", config.colors.text)
        y = y + line_height
    end

    gui.text(x, y, string.format("Frame: %d", state.frame_count), config.colors.text)
end

-- ============================================================================
-- MEMORY SCANNING HELPERS
-- ============================================================================

-- Search for a specific byte value in a range
local function scan_for_value(start_addr, end_addr, target_value)
    local results = {}
    for addr = start_addr, end_addr do
        if read_byte(addr) == target_value then
            table.insert(results, addr)
        end
    end
    return results
end

-- Watch a specific address and print when it changes
local function watch_address(addr, name, size)
    size = size or 1
    local read_fn = size == 1 and read_byte or (size == 2 and read_word or read_dword)

    memory.registerwrite(addr, function()
        local new_val = read_fn(addr)
        log_msg(string.format("%s (0x%08X) changed to: %d (0x%X)", name, addr, new_val, new_val))
    end)

    print(string.format("Watching %s at 0x%08X (%d bytes)", name, addr, size))
end

-- ============================================================================
-- MAIN LOOP
-- ============================================================================

local function on_frame()
    state.frame_count = state.frame_count + 1

    -- Only check every N frames
    if state.frame_count % config.watch_interval ~= 0 then
        return
    end

    -- Detect battle state
    state.in_battle = detect_battle()

    if state.in_battle then
        local battle = read_battle_state()

        -- Check for changes
        if config.log_changes then
            local changes = check_for_changes(battle)
            for _, change in ipairs(changes) do
                log_msg(change)
            end
        end

        -- Draw overlay
        draw_overlay(battle)
    else
        draw_overlay(nil)
    end
end

-- ============================================================================
-- INTERACTIVE COMMANDS
-- ============================================================================

-- Call these from the Lua console:

function jus_status()
    print("=== JUS Watcher Status ===")
    print(string.format("Frame: %d", state.frame_count))
    print(string.format("In Battle: %s", state.in_battle and "Yes" or "No"))

    if state.in_battle then
        local battle = read_battle_state()
        print(string.format("Timer: %d", battle.timer))
        print(string.format("Leader HP: %d", battle.leader_hp))
        print(string.format("Partner HP: %d", battle.nonleader_hp))
        print(string.format("Special: %d / %d", battle.special_1, battle.special_2))
    end

    local currency = read_currency()
    print(string.format("Koma Points: %d", currency.koma_points))
    print(string.format("Gems: %s", table.concat(currency.gems, ", ")))
end

function jus_watch(addr, name, size)
    watch_address(addr, name or "Custom", size or 1)
end

function jus_scan(start_addr, end_addr, value)
    local results = scan_for_value(start_addr, end_addr, value)
    print(string.format("Found %d matches for value %d:", #results, value))
    for i, addr in ipairs(results) do
        if i <= 20 then
            print(string.format("  0x%08X", addr))
        end
    end
    if #results > 20 then
        print(string.format("  ... and %d more", #results - 20))
    end
    return results
end

function jus_read(addr, size)
    size = size or 16
    print(string.format("Reading %d bytes from 0x%08X:", size, addr))
    local hex = ""
    local ascii = ""
    for i = 0, size - 1 do
        local b = read_byte(addr + i)
        hex = hex .. string.format("%02X ", b)
        ascii = ascii .. (b >= 32 and b <= 126 and string.char(b) or ".")
        if (i + 1) % 16 == 0 then
            print(string.format("  %s | %s", hex, ascii))
            hex = ""
            ascii = ""
        end
    end
    if #hex > 0 then
        print(string.format("  %-48s | %s", hex, ascii))
    end
end

function jus_dump_history()
    print("=== Change History ===")
    for i, entry in ipairs(state.history) do
        if i > #state.history - 50 then  -- Last 50 entries
            print(string.format("[%06d] %s", entry.frame, entry.message))
        end
    end
end

-- ============================================================================
-- REGISTER CALLBACKS
-- ============================================================================

print("===================================")
print("  JUS Watcher loaded!")
print("===================================")
print("")
print("Commands available in console:")
print("  jus_status()         - Show current values")
print("  jus_watch(addr,name) - Watch address for changes")
print("  jus_scan(s,e,val)    - Scan range for value")
print("  jus_read(addr,size)  - Hex dump memory")
print("  jus_dump_history()   - Show change log")
print("")
print("Known addresses:")
print(string.format("  Leader HP:    0x%08X", ADDR.leader_hp))
print(string.format("  Partner HP:   0x%08X", ADDR.nonleader_hp))
print(string.format("  Timer:        0x%08X", ADDR.battle_timer))
print(string.format("  Special 1:    0x%08X", ADDR.special_meter_1))
print(string.format("  HP Code Hook: 0x%08X", ADDR.health_code_addr))
print("")

-- Set up auto-watchers for HP changes
watch_address(ADDR.leader_hp, "Leader HP", 1)
watch_address(ADDR.nonleader_hp, "Partner HP", 1)

-- Register frame callback
gui.register(on_frame)
