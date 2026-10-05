# -*- coding: utf-8 -*-
"""The numbers of the Stiliai page of the admin panel (work package WP13a), worked out from the usage events' counts: pure functions of one summary (the
merged daily counts of api/_lib/events.py), no storage, no clock. The admin action styles_stats (api/_lib/ops.py) reads the days and calls report();
the audit entry of a change of the switch calls flip_numbers(); both run the SAME function (test I22: the opening line the page shows and the numbers
the audit entry keeps are one calculation, and the funnel equals a replay of the recorded events).

THE SET-LEVEL FUNNEL (spec 1.6.2). The gate multiplies over eyes (about 0.66 to the power N for N eyes on the calibration set), so the number that says
whether two or more eyes can be sold is not the pass rate of one eye but of a SET. A set is counted once, by its first request (the page marks the
requests that repeat a look at the same eyes with `again`, events.py); its gate result is the set's: ok, unknown (no sealed profile: a version 1 seal), or
the first failing eye's reason code. `retake` is the number of eyes the page replaced since the set's last compose. Per eye count (and per colour class of
the set) the funnel gives, always with n:
    first          sets seen with a known gate result and no retake: the first photo
    first_pass     of those, the ones that passed; rate_first = first_pass / first
    retake1_pass   sets with exactly one retake that passed
    rate_retake    (first_pass + min(sets that failed the first photo, retake1_pass)) / first: "pass counting one retake of the failing eyes". The page
                   does not link a set's two requests (an event holds no id of anything), so this is an upper bound: a retake of a set that had passed
                   counts too, capped by the number that failed. Said so on the page, with n.
    unknown        sets whose gate was unknown (not in a rate)
The opening line of a count of two or more eyes (the owner's criterion, 1.6.2 rule 2): at least OPEN_MIN_SETS first-photo sets, first-photo pass at least
OPEN_FIRST, at least OPEN_RETAKE counting one retake; green only when all three hold, and it says which does not (n_low, first_low, retake_low). One eye has
no line: a one eye set always has an advisory style to buy. The owner may open earlier knowingly: the numbers stand beside the switch and the audit entry
keeps them.

Module rule: from __future__ import annotations (Vercel's default Python is 3.12)."""
from __future__ import annotations

import math

from . import catalogue as CT
from . import events as E

OPEN_MIN_SETS = 30
OPEN_FIRST = 0.50
OPEN_RETAKE = 0.75
SLICES = ("lang", "market")
SLICED_TABLES = ("compose_funnel", "compose_funnel_cls", "compose_demand", "compose_chosen", "compose_style", "compose_tile_style", "compose_fallback",
                 "compose_tiles")
ASK_STAGES = ("preview", "live")
GATE_FAIL_BY_RULE = {"lid": ("lid", "both"), "fill": ("fill", "both"), "lid+fill": ("lid", "fill", "both")}


def _int(v):
    return v if isinstance(v, int) and not isinstance(v, bool) else (int(v) if isinstance(v, float) and v == v and abs(v) < 1e12 else 0)


def table(agg, name, sl=None):
    """One count table of a summary, as a dict: the table itself, or its slice ("lang:lt", "market:au") out of compose_slice."""
    if not sl:
        return {k: _int(v) for k, v in (agg.get(name) or {}).items()}
    pre = f"{sl}|{name}|"
    return {k[len(pre):]: _int(v) for k, v in (agg.get("compose_slice") or {}).items() if k.startswith(pre)}


def merge_all(aggs):
    """The summaries of several days as one (events.merge)."""
    out = E.empty()
    for a in aggs:
        out = E.merge(out, a or {})
    return out


def parse_slice(market=None, lang=None):
    """The slice name of the filters of a request: ("market:au" | "lang:lt" | None). One filter at a time (a count table has no market-by-language cell)."""
    if market and lang:
        raise ValueError("one filter at a time: a market or a language")
    if market:
        return f"market:{market}"
    if lang:
        return f"lang:{lang}"
    return None


# ----------------------------------------------------------------------------- the funnel
def _row(eyes, cls=None):
    return {"eyes": eyes, "cls": cls, "first": 0, "first_pass": 0, "unknown": 0, "retake1": 0, "retake1_pass": 0, "retake2": 0, "retake2_pass": 0,
            "fails": {}, "rate_first": None, "rate_retake": None, "line": None}


def _finish(row):
    first, fp = row["first"], row["first_pass"]
    if first:
        row["rate_first"] = round(fp / first, 4)
        failed = first - fp
        row["rate_retake"] = round((fp + min(failed, row["retake1_pass"])) / first, 4)
    row["line"] = opening_line(row) if row["eyes"] >= 2 else None
    return row


def opening_line(row):
    """The opening criterion of a count of two or more eyes for one funnel row: {ok, n, need_n, first, need_first, retake, need_retake, why}. why lists what
    is not met (n_low, first_low, retake_low); ok is True only when nothing is."""
    n, rf, rr = row["first"], row["rate_first"], row["rate_retake"]
    why = []
    if n < OPEN_MIN_SETS:
        why.append("n_low")
    if rf is None or rf < OPEN_FIRST:
        why.append("first_low")
    if rr is None or rr < OPEN_RETAKE:
        why.append("retake_low")
    return {"ok": not why, "n": n, "need_n": OPEN_MIN_SETS, "first": rf, "need_first": OPEN_FIRST, "retake": rr, "need_retake": OPEN_RETAKE, "why": why}


def funnel(tab, by_class=False):
    """The funnel rows of compose_funnel ("<eyes>|<gate>|<retakes>") or, with by_class, of compose_funnel_cls ("<eyes>|<class>|<gate>|<retakes>"): a list of
    rows ordered by eye count (and class)."""
    rows = {}
    for key, n in tab.items():
        parts = key.split("|")
        if len(parts) != (4 if by_class else 3):
            continue
        try:
            eyes, retakes = int(parts[0]), int(parts[-1])
        except ValueError:
            continue
        cls = parts[1] if by_class else None
        gate = parts[-2]
        if not 1 <= eyes <= 8 or retakes not in (0, 1, 2):
            continue
        row = rows.setdefault((eyes, cls), _row(eyes, cls))
        if gate == "unknown":
            row["unknown"] += n
        elif retakes == 0:
            row["first"] += n
            if gate == "ok":
                row["first_pass"] += n
            else:
                row["fails"][gate] = row["fails"].get(gate, 0) + n
        else:
            row[f"retake{retakes}"] += n
            if gate == "ok":
                row[f"retake{retakes}_pass"] += n
    return [_finish(rows[k]) for k in sorted(rows, key=lambda k: (k[0], k[1] or ""))]


def flip_numbers(aggs, counts):
    """The set-level numbers of each eye count in `counts` at this moment, for the audit entry of a change of the switch: {"<n>": {n, first_pass, with_retake,
    unknown, line_ok, why}} (rates None where there is no set yet). aggs: the daily summaries."""
    rows = {r["eyes"]: r for r in funnel(table(merge_all(aggs), "compose_funnel"))}
    out = {}
    for n in counts:
        r = rows.get(n) or _finish(_row(n))
        out[str(n)] = {"n": r["first"], "first_pass": r["rate_first"], "with_retake": r["rate_retake"], "unknown": r["unknown"],
                       "line_ok": r["line"]["ok"] if r["line"] else None, "why": r["line"]["why"] if r["line"] else []}
    return out


# ----------------------------------------------------------------------------- the demand for a style that cannot be bought yet
def demand(agg, sl=None):
    """Rows {style, name, eyes, stage, tiles, large, soon, blocked} (tiles looked at, large previews made, clicks on the buy button of a style that was
    Soon, checkouts refused for it), by style and eye count, busiest first. A row is the stage the style had when it was asked for."""
    rows = {}
    for key, n in table(agg, "compose_demand", sl).items():
        parts = key.split("|")
        if len(parts) != 4 or parts[2] not in ASK_STAGES or parts[3] not in ("tile", "large"):
            continue
        try:
            eyes = int(parts[1])
        except ValueError:
            continue
        r = rows.setdefault((parts[0], eyes, parts[2]), {"style": parts[0], "name": CT.name_of(parts[0]), "eyes": eyes, "stage": parts[2], "tiles": 0,
                                                         "large": 0, "soon": 0, "blocked": 0})
        r["tiles" if parts[3] == "tile" else "large"] += n
    if not sl:                                 # the clicks carry no language or market of their own: they are not in a slice
        for key, n in table(agg, "help_demand").items():
            parts = key.split("|")
            if len(parts) != 3 or parts[0] not in ("soon", "blocked"):
                continue
            try:
                eyes = int(parts[2])
            except ValueError:
                continue
            hit = [r for (sid, e, st), r in rows.items() if sid == parts[1] and e == eyes and st == "preview"]
            if hit:
                hit[0][parts[0]] += n
            else:
                rows[(parts[1], eyes, "preview")] = {"style": parts[1], "name": CT.name_of(parts[1]), "eyes": eyes, "stage": "preview", "tiles": 0,
                                                     "large": 0, "soon": n if parts[0] == "soon" else 0, "blocked": n if parts[0] == "blocked" else 0}
    return sorted(rows.values(), key=lambda r: (-(r["tiles"] + r["large"] + r["soon"] + r["blocked"]), r["style"], r["eyes"]))


def chosen(agg, sl=None):
    t = table(agg, "compose_chosen", sl)
    pick, other = t.get("pick", 0), t.get("other", 0)
    return {"pick": pick, "other": other, "share": round(pick / (pick + other), 4) if pick + other else None}


def previews(agg, sl=None):
    """Rows {style, name, previews, tiles}: the large previews the customer asked for and the tiles of the batches, by style (tiles apart from previews)."""
    pre, til = table(agg, "compose_style", sl), table(agg, "compose_tile_style", sl)
    return sorted(({"style": s, "name": CT.name_of(s), "previews": pre.get(s, 0), "tiles": til.get(s, 0)} for s in set(pre) | set(til)),
                  key=lambda r: (-(r["previews"] + r["tiles"]), r["style"]))


def requests(agg, sl=None):
    """The requests that made or judged a set (the sum of compose_tiles: a request is counted once, whatever its tiles) and how many of them drew
    nothing (key 0: the tile list alone, a set the gate held back)."""
    t = table(agg, "compose_tiles", sl)
    return {"total": sum(t.values()), "drew_nothing": t.get("0", 0)}


# ----------------------------------------------------------------------------- render times
def percentile(buckets, q):
    """The upper bound in ms of the bucket that holds the q-quantile of a histogram {bucket index: count}; None when it is in the open bucket above the
    last bound (the true value is above E.HIST_MS[-1]) or the histogram is empty."""
    total = sum(buckets.values())
    if not total:
        return None
    need, cum = math.ceil(q * total), 0
    for i in sorted(buckets):
        cum += buckets[i]
        if cum >= need:
            return E.HIST_MS[i] if i < len(E.HIST_MS) else None
    return None


def times(agg):
    """Rows {what (compose, tile or art), style, name, eyes, n, p50_ms, p95_ms, over}: the spread of the render times by style and eye count, from the
    histogram (p50 and p95 are the upper bounds of their buckets: at most one bucket too high). over: the count above the last bound."""
    rows = {}
    for key, n in table(agg, "ms_hist").items():
        parts = key.split("|")
        if len(parts) != 4:
            continue
        try:
            eyes, b = int(parts[2]), int(parts[3])
        except ValueError:
            continue
        rows.setdefault((parts[0], parts[1], eyes), {})[b] = n
    out = []
    for (what, style, eyes), bk in sorted(rows.items()):
        out.append({"what": what, "style": style, "name": CT.name_of(style), "eyes": eyes, "n": sum(bk.values()), "p50_ms": percentile(bk, 0.50),
                    "p95_ms": percentile(bk, 0.95), "over": bk.get(len(E.HIST_MS), 0)})
    return out


# ----------------------------------------------------------------------------- errors, holds, review, fallbacks, gate
def errors_by_style(agg):
    """Rows {style, name, errors, asked, rate}: the error events that named the style over the asks (previews, tiles and the errors themselves). An
    error event carries no language and no market, so this is never sliced."""
    err = table(agg, "error_style")
    pre, til = table(agg, "compose_style"), table(agg, "compose_tile_style")
    rows = []
    for s in sorted(set(err) | set(pre) | set(til)):
        e = err.get(s, 0)
        asked = pre.get(s, 0) + til.get(s, 0) + e
        if e:
            rows.append({"style": s, "name": CT.name_of(s), "errors": e, "asked": asked, "rate": round(e / asked, 4) if asked else None})
    return sorted(rows, key=lambda r: -r["errors"])


def review_by_style(agg):
    """Rows {style, name, review, made, rate}: the artworks held for a look over the artworks made (one art step is one artwork), by style."""
    rev, made = table(agg, "master_review_style"), table(agg, "master_art_style")
    rows = [{"style": s, "name": CT.name_of(s), "review": rev.get(s, 0), "made": made.get(s, 0),
             "rate": round(rev.get(s, 0) / made[s], 4) if made.get(s) else None} for s in sorted(set(rev) | set(made))]
    return sorted(rows, key=lambda r: (-r["review"], r["style"]))


def fallbacks(agg, sl=None):
    """Rows {style, fallback, count, of, share}: how often a style's picture fell back (kiss for a wide pupil, stack_contrast for the stacked lens of a pair
    of colours that differ strongly), over the pictures made of that style (previews and tiles). The stack's share per pair design is the number the owner
    asked for (WP13 d)."""
    fb = table(agg, "compose_fallback", sl)
    pre, til = table(agg, "compose_style", sl), table(agg, "compose_tile_style", sl)
    rows = []
    for key, n in fb.items():
        s, _, code = key.partition("|")
        of = pre.get(s, 0) + til.get(s, 0)
        rows.append({"style": s, "name": CT.name_of(s), "fallback": code, "count": n, "of": of, "share": round(n / of, 4) if of else None})
    return sorted(rows, key=lambda r: (r["style"], r["fallback"]))


def gate_by_style(agg):
    """Rows {style, name, policy, rule, seen, failed, rate}: the restoration gate's failures per eye (the enhance events' codes ok, lid, fill, both) under
    each style's own rule: a style that needs the lid rule fails an eye that fails it (lid or both). Measured per eye at /api/enhance, so it has no
    selection bias (a style that was never drawn for a failing eye still counts that eye)."""
    g = table(agg, "enhance_gate")
    known = sum(v for k, v in g.items() if k != "unknown")
    rows = []
    for sid in CT.ids():
        pol, e = CT.gate_policy(sid), CT.ENGINE.get(sid) or {}
        rule = e.get("gate_rules") or ""
        if pol in (None, "none") or rule not in GATE_FAIL_BY_RULE:
            continue
        failed = sum(g.get(c, 0) for c in GATE_FAIL_BY_RULE[rule])
        rows.append({"style": sid, "name": CT.name_of(sid), "policy": pol, "rule": rule, "seen": known, "failed": failed,
                     "rate": round(failed / known, 4) if known else None})
    return rows


def reveal(agg):
    """{codes: {ok, colour, registration, none, error}, n, ok_share, ms}: what the page could show of the Reveal's cut, per eye."""
    r = table(agg, "enhance_reveal")
    n = sum(r.values())
    ms = (agg.get("ms") or {}).get("reveal")
    return {"codes": r, "n": n, "ok_share": round(r.get("ok", 0) / n, 4) if n else None,
            "ms": round(ms[0] / ms[1], 1) if isinstance(ms, (list, tuple)) and len(ms) == 2 and ms[1] else None}


# ----------------------------------------------------------------------------- the attention card
def attention(agg, limits, health=None):
    """What crossed a limit the owner set (the Stiliai page's attention card): {style, kind (error, review, gate), rate, n, limit} for a style whose error
    rate, review rate or per-eye gate failure rate is above its limit with at least limits["min_n"] events behind it, {kind: "health", key} for a health
    boolean that is false (health: {styles, plates_4k}), {kind: "hold", code, n} for orders held for a style step. The rates are the ones of
    errors_by_style, review_by_style and gate_by_style: one calculation."""
    out = []
    min_n = limits.get("min_n", 0)
    for r in errors_by_style(agg):
        if r["rate"] is not None and r["asked"] >= min_n and r["rate"] > limits.get("error_rate", 1):
            out.append({"style": r["style"], "kind": "error", "rate": r["rate"], "n": r["asked"], "limit": limits["error_rate"]})
    for r in review_by_style(agg):
        if r["rate"] is not None and r["made"] >= min_n and r["rate"] > limits.get("review_rate", 1):
            out.append({"style": r["style"], "kind": "review", "rate": r["rate"], "n": r["made"], "limit": limits["review_rate"]})
    for r in gate_by_style(agg):
        if r["rate"] is not None and r["seen"] >= min_n and r["rate"] > limits.get("gate_fail_rate", 1):
            out.append({"style": r["style"], "kind": "gate", "rate": r["rate"], "n": r["seen"], "limit": limits["gate_fail_rate"]})
    for key, ok in sorted((health or {}).items()):
        if ok is False:
            out.append({"kind": "health", "key": key})
    for code, n in sorted(table(agg, "master_hold").items()):
        out.append({"kind": "hold", "code": code, "n": n})
    return out


# ----------------------------------------------------------------------------- the report
def report(agg, limits=None, sl=None, health=None):
    """Everything the Stiliai page shows of one period's counts (agg: the merged summary). sl: the filter ("lang:lt", "market:au"): the tables that carry
    a language and a market (SLICED_TABLES) are the slice's own; the others (the restoration gate, the master, the errors) are not sliced and are
    reported whole, which `filter.whole` says."""
    limits = limits or {"min_n": 20, "error_rate": 0.05, "review_rate": 0.10, "gate_fail_rate": 0.60}
    f = funnel(table(agg, "compose_funnel", sl))
    return {"requests": requests(agg, sl), "funnel": f, "funnel_by_class": funnel(table(agg, "compose_funnel_cls", sl), by_class=True),
            "opening": {str(r["eyes"]): r["line"] for r in f if r["line"]}, "demand": demand(agg, sl), "chosen": chosen(agg, sl), "previews": previews(agg, sl),
            "fallbacks": fallbacks(agg, sl), "times": times(agg), "errors": errors_by_style(agg), "review": review_by_style(agg),
            "gate": {"codes": table(agg, "enhance_gate"), "reasons": table(agg, "enhance_reason"), "classes": table(agg, "enhance_class"),
                     "pupils": table(agg, "enhance_pupil"), "by_style": gate_by_style(agg)},
            "holds": table(agg, "master_hold"), "master": {"made_by_style": table(agg, "master_art_style"), "fallback": table(agg, "master_fallback")},
            "help": {"routes": table(agg, "help_route"), "why": table(agg, "help_why"), "eyes": table(agg, "help_eyes")},
            "reveal": reveal(agg), "attention": attention(agg, limits, health),
            "filter": {"slice": sl, "sliced": list(SLICED_TABLES), "whole": ["times", "errors", "review", "gate", "holds", "master", "help", "reveal", "attention"]}}
