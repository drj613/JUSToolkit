"""Plan/watch validation and conversion to Lua literals.

Spec: docs/superpowers/specs/2026-08-14-melonds-agent-control-design.md §5.
Limits: <=32 watches, <=512 watched bytes/frame, chain depth <=3.
validate_watches() is THE watch validator; every CLI path uses it.
"""
from jus_addresses import resolve_watch

BUTTONS = {  # CLI accepts uppercase; values are the fork's exact casing
    "A": "A", "B": "B", "SELECT": "Select", "START": "Start",
    "RIGHT": "Right", "LEFT": "Left", "UP": "Up", "DOWN": "Down",
    "R": "R", "L": "L", "X": "X", "Y": "Y",
}
MAX_WATCHES = 32
MAX_WATCH_BYTES = 512
MAX_CHAIN_DEPTH = 3
MAIN_RAM = (0x02000000, 0x02400000)
TOUCH_W, TOUCH_H = 256, 192


class PlanError(ValueError):
    pass


def validate_watches(specs):
    """Validate a list of concrete watch specs. Raises PlanError."""
    if len(specs) > MAX_WATCHES:
        raise PlanError("too many watches (%d > %d)" % (len(specs), MAX_WATCHES))
    names = set()
    total = 0
    for w in specs:
        name = w.get("name")
        if not name or name in names:
            raise PlanError("missing/duplicate watch name: %r" % name)
        names.add(name)
        ln = w.get("len", 0)
        if not (isinstance(ln, int) and 1 <= ln <= MAX_WATCH_BYTES):
            raise PlanError("bad len for %s" % name)
        total += ln
        if "chain" in w:
            if len(w["chain"]) - 1 > MAX_CHAIN_DEPTH:
                raise PlanError("chain too deep: %s" % name)
            if not isinstance(w.get("offset", 0), int):
                raise PlanError("bad offset: %s" % name)
        elif "addr" in w:
            a = w["addr"]
            if not (MAIN_RAM[0] <= a and a + ln <= MAIN_RAM[1]):
                raise PlanError("read outside main RAM: %s" % name)
        else:
            raise PlanError("watch needs addr or chain: %s" % name)
    if total > MAX_WATCH_BYTES:
        raise PlanError("watch byte budget exceeded (%d > %d)" %
                        (total, MAX_WATCH_BYTES))
    return specs


def _nonneg(v, what):
    v = int(v)
    if v < 0:
        raise PlanError("%s must be >= 0, got %d" % (what, v))
    return v


def validate_plan(plan):
    """Return a normalized copy of the plan, or raise PlanError."""
    out = {"name": str(plan["name"]),
           "load_state": plan.get("load_state"),
           "tail_frames": _nonneg(plan.get("tail_frames", 0), "tail_frames")}

    segs, last_end = [], -1
    raw = plan["segments"]
    if raw != sorted(raw, key=lambda s: int(s["from"])):
        raise PlanError("segments must be sorted by 'from'")
    for seg in raw:
        f = _nonneg(seg["from"], "from")
        t = _nonneg(seg["to"], "to")
        if t < f:
            raise PlanError("segment to < from: %s" % seg)
        if f <= last_end:
            raise PlanError("segments overlap at frame %d" % f)
        last_end = t
        norm = {"from": f, "to": t}
        if "buttons" in seg:
            btns = []
            for b in seg["buttons"]:
                if b.upper() not in BUTTONS:
                    raise PlanError("unknown button %r" % b)
                btns.append(BUTTONS[b.upper()])
            if ("Left" in btns and "Right" in btns) or \
               ("Up" in btns and "Down" in btns):
                raise PlanError("contradictory d-pad in segment %s" % seg)
            norm["buttons"] = btns
        if "touch" in seg:
            x, y = int(seg["touch"]["x"]), int(seg["touch"]["y"])
            if not (0 <= x < TOUCH_W and 0 <= y < TOUCH_H):
                raise PlanError("touch out of bounds: %d,%d" % (x, y))
            norm["touch"] = {"x": x, "y": y}
        if "buttons" not in norm and "touch" not in norm:
            raise PlanError("segment has neither buttons nor touch: %s" % seg)
        segs.append(norm)
    if not segs:
        raise PlanError("plan has no segments")
    out["segments"] = segs
    out["total_frames"] = last_end + 1 + out["tail_frames"]

    watches = []
    for w in plan.get("watches", []):
        watches.extend(resolve_watch(w) if isinstance(w, str) else [dict(w)])
    out["watches"] = validate_watches(watches)
    return out


_ESCAPES = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r", "\t": "\\t"}


def _quote(s):
    body = "".join(_ESCAPES.get(c, "\\%d" % ord(c) if ord(c) < 32 else c)
                   for c in s)
    return '"%s"' % body


def lua_literal(v):
    if v is None:
        return "nil"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return "0x%X" % v if v > 255 else str(v)
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, str):
        return _quote(v)
    if isinstance(v, list):
        return "{" + ", ".join(lua_literal(x) for x in v) + "}"
    if isinstance(v, dict):
        parts = ["[%s] = %s" % (_quote(str(k)), lua_literal(val))
                 for k, val in sorted(v.items()) if val is not None]
        return "{" + ", ".join(parts) + "}"
    raise TypeError(type(v))


def plan_to_lua(normalized):
    """Emit the validated plan as a Lua literal chunk ('return {...}')."""
    return "return " + lua_literal(normalized)
