# -*- coding: utf-8 -*-
"""The one duration constant of the site's functions, and every number that is tied to it.

DURATION_S is the longest a function may run: the "maxDuration" of every entry of vercel.json (scripts/check_styles.mjs holds the two equal,
a build check: raising the limit is ONE coordinated change, never one number in one file). The work inside a call, the leases that tell
a live holder from a dead one, and the waits of the server's own chain are all derived from it here, because a lease shorter than the
longest life of its holder lets a second caller take over a render that is still alive (two writers, a second artwork beside one whose link
may be mailed already). With 60 s the derived numbers are the ones the code has always had (52, 75, 100, 40, 4):

    budget          D - 8      the work a call gives itself (iris.BUDGET): the last 8 s are for the reply, the encode and a cold start's imports
    function_seconds D         what maker.py calls FUNCTION_SECONDS
    spare           4          of the 8 s after the work, what a self-call may still use (maker.SPARE)
    lease_stale     D + 15     a claim older than this belongs to an invocation that is dead: the order's advance.lock, compose.lock, an eye's
                               claim, a step's claim (a claim outlives any live holder by 15 s)
    compose_stale   D + 15     (the same rule, the name order.py gave it)
    fresh           D + 40     advance.json younger than this: the server is on the order
    wait_max        D - 20     the longest back-off between two steps and the longest wait of one relay hop (a relay is an invocation too)
    cleanup_stale   2 D        the daily clean-up's own lock

Nothing here imports anything: the constants are read by iris.py, maker.py, order.py, master_eye.py, cleanup.py and styles/costs.py, which load
in every function, and by the tests."""
from __future__ import annotations

DURATION_S = 60              # vercel.json maxDuration of every function (the build check holds them equal)

REPLY_MARGIN_S = 8           # the part of a call the work never uses
SPARE_FRACTION = 0.5         # of that margin, what a self-call may still use after the work
LEASE_MARGIN_S = 15          # a lease outlives its holder's longest life by this much
FRESH_MARGIN_S = 40
WAIT_MARGIN_S = 20           # a relay hop that waits must still be able to ask for the next step afterwards
WATCHDOG_EXTRA_S = 5         # the watchdog fires this long after the lease has aged out

MIN_DURATION_S = 60          # below this the watchdog's two relays do not cover a lease (problems() says so)
MAX_DURATION_S = 900


def derive(d: float = DURATION_S) -> dict:
    """Every derived number of a duration d."""
    d = float(d)
    budget = d - REPLY_MARGIN_S
    lease = d + LEASE_MARGIN_S
    wait_max = d - WAIT_MARGIN_S
    watchdog_total = lease + WATCHDOG_EXTRA_S
    first = min(wait_max, watchdog_total)
    return {"duration": d, "budget": budget, "function_seconds": d, "spare": REPLY_MARGIN_S * SPARE_FRACTION,
            "lease_stale": lease, "compose_stale": lease, "fresh": d + FRESH_MARGIN_S, "wait_max": wait_max,
            "cleanup_stale": 2 * d,
            # the watchdog: a relay hop that waits, then another that waits, then a normal step (api/_lib/maker.py arm_watchdog)
            "watchdog_first": first, "watchdog_then": max(0.0, watchdog_total - first), "watchdog_total": watchdog_total}


def problems(d: float = DURATION_S) -> list:
    """The lease rules, as sentences, that a duration breaks (empty: sound). The tests run it for several durations."""
    x = derive(d)
    out = []
    if not MIN_DURATION_S <= d <= MAX_DURATION_S:
        out.append(f"a duration of {d} s is outside {MIN_DURATION_S} to {MAX_DURATION_S}")
    if not x["lease_stale"] >= d + LEASE_MARGIN_S:
        out.append("a lease must outlive the longest life of its holder by the lease margin")
    if not x["compose_stale"] >= x["lease_stale"]:
        out.append("the compose claim must be at least as long as a lease")
    if not x["fresh"] > x["lease_stale"]:
        out.append("advance.json stays fresh longer than a lease")
    if not x["budget"] <= d - REPLY_MARGIN_S:
        out.append("the work must leave the reply margin")
    if not x["watchdog_total"] >= x["lease_stale"]:
        out.append("the watchdog must fire after the lease has aged out")
    if not (x["watchdog_first"] <= x["wait_max"] and x["watchdog_then"] <= x["wait_max"]):
        out.append("each relay of the watchdog must wait no longer than the longest wait")
    if not x["wait_max"] + x["spare"] + 4.0 <= d:
        out.append("a relay hop that waits must still have time to ask for the next step")
    return out


_D = derive()
BUDGET_S = _D["budget"]
FUNCTION_SECONDS = _D["function_seconds"]
SPARE_S = _D["spare"]
LEASE_STALE_S = _D["lease_stale"]
COMPOSE_STALE_S = _D["compose_stale"]
FRESH_S = _D["fresh"]
WAIT_MAX_S = int(_D["wait_max"])
CLEANUP_STALE_S = _D["cleanup_stale"]
WATCHDOG_FIRST_S = int(_D["watchdog_first"])
WATCHDOG_THEN_S = int(_D["watchdog_then"])
