#!/bin/sh
#
# Outbox-gate reminder — fires before the loops schedule their next wake.
#
# Non-blocking by design: emits a systemMessage and exits 0. It sets no
# permissionDecision, so it can never stall or deny ScheduleWakeup (a hard
# block could deadlock an unattended loop). See
# docs/orchestration/COORDINATION-PROTOCOL.md and outbox-gate-hook.md.

# Consume and ignore the hook's stdin JSON.
cat >/dev/null 2>&1 || true

cat <<'JSON'
{"systemMessage":"Outbox gate — before scheduling the next wake: have you flushed this wake's outbox? (1) Publish any retraction or relabel of something you sent the partner. (2) Send any result bearing on the partner's open questions. (3) Run `br sync --flush-only`. A measurement missing its conditions block, or an address missing its reachability basis, is INCOMPLETE — fix or label it before it lands in canon. See docs/orchestration/COORDINATION-PROTOCOL.md."}
JSON

exit 0
