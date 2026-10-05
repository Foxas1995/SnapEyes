# -*- coding: utf-8 -*-
"""styles.steps: the master plan of a paid order, its steps and the state machine that runs them (work package WP6a).

Every paid artwork is made by a PLAN: a record of what will be drawn (the style, the design actually used, the layout, the canvas, the
eyes' ids, the seed key, the steps with their estimated seconds and megabytes), made ONCE, stored next to the order and read by every
step; the master never works the geometry out again. The default plan is one step, "art": every release-1 style fits one 60 s call
(SPIKE, section 4.1). The planner, the plan record, the done records, the two process guards and the per-step events are built all the
same: they carry the admin's visibility (the order page, the order detail, the lab) and the rule that a larger duration limit collapses
everything to single steps with no other change. A second kind of step (the reserve split of the plan, WP6b) plugs into EXECUTORS.

The records (orders/<order>/style/, all small JSON, removed 14 days after delivery.json by api/_lib/cleanup.py):

    plan.json            {v, reg, pv, engine_v, style, family, design_used, fallback, layout, canvas, opts, eye_ids[], eye_prof[], work_side,
                          seed_key, plate_families[], cost_key, steps: [{name, kind, eyes[], need_s, est_mb}], plan8, created_at}
                         created with upsert=False (the first writer wins), never changed. plan8 (8 hex) names its identity: everything that
                         decides the picture and nothing that is only provenance or an estimate (the registry hash `reg` is recorded, not hashed:
                         an unrelated registry edit must never rename an unfinished order's file)
    rerun.json           {n, t, by, reason}: the admin's rerun count; it salts the artwork's digest, so a rerun never overwrites the file that
                         delivery.json (and a mailed link) points to
    done_<step>.json     {step, rerun, outputs[{path, bytes, sha12}], ms, cpu_s, peak_mb, rss_mb, hwm_mb, attempt, inputs, result, drift, by, at}
                         written LAST, after the outputs: a reader trusts only a done record whose output exists
    try_<step>.json      {kills, open, plate, errors[], watchdog, attempts, t}: the step's failures. `open` is set before the render and cleared
                         after delivery.json: a claim that finds it still set knows the last attempt was KILLED and counts one kill (the third
                         holds the order); a storage error, a busy answer or a refusal never counts; a second identical exception holds; the
                         second plate fault holds (a plate fault is not a MAX_BUSY hop)
    <step>.lock          the step's claim (created atomically, taken over after duration.LEASE_STALE_S, as master_eye's eye claim)

The state machine of one step, in order (run_step): read the plan and the done records; wait for the two process guards (guard.py: the memory
budget and the one-heavy-render-at-a-time semaphore); check the time and memory it needs (a plan that can NEVER fit, or a fresh invocation that
cannot fit it, is a configuration error: Hold style_step_too_big, no busy hop is spent; an invocation that already used its time is only
busy; a step that finds the instance's room taken by another render is answered 503 room_retry with a back-off as long as the holder still
needs by its own estimate, because a busy answer retried at once spends the chain's ten busy hops in the few seconds of the waits); claim
<step>.lock; set try_<step>.json {kills, open: true}; arm the watchdog; render; write the outputs; write done_<step>.json; let the
caller write delivery.json; clear `open`. Whatever kills the process at any seam leaves a state the next call reads and finishes (a kill after the
done record and before delivery.json: the next call finds the finished artwork and only writes delivery.json).

The watchdog: nothing runs after a killed step except the order page (when it is open), the status nudge and the daily run (once a day on Hobby),
so a killed step could wait days against a 48 hour promise. The step therefore arms a relay of the server's own chain before it renders
(maker.arm_watchdog: two relay hops that wait out the lease, then a normal step), at most WATCHDOG_MAX times: a killed step is retaken within
duration.watchdog_total plus one step, with no page open.

Holds (Hold, raised to the caller, which writes review.json and tells the owner; the order is never made in another style): style_step_too_big,
style_not_priced, engine_skew (the plan was made under another ENGINE_V), class_changed (the master's colour class is not the preview's: never
another palette), style_step_failed (the third kill, the second identical exception), plate_unavailable (the second plate fault), no_engine.

A style of the legacy engine is one art step as well (the executor calls the legacy master compose with the very body it always had: the artwork's
file name is that function's own digest, unchanged); a style of the v3 engine is drawn here by its family's preview() at 4096 px and stored as
artwork_<sha256(plan8, rerun)[:16]>.jpg. Module rule: from __future__ import annotations (Vercel's default Python is 3.12).
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import math
import re
import secrets
import time

from .. import catalogue as CT
from .. import duration as D
from .. import store
from . import ENGINE_V
from . import costs as CO
from . import guard as GD

ART = "art"
FOLDER = "style"
PLAN_VERSION = 1
SIZE = 4096                          # the long side of the delivered artwork
LINK_SECONDS = 7 * 86400             # the signed download link (master_compose.LINK_SECONDS)
KILLS_MAX = 3                        # the third kill holds the order
ERRORS_MAX = 2                       # a second identical exception holds it
PLATE_MAX = 2                        # the second plate fault holds it
PLATE_RETRY_S = 20                   # a first plate fault is answered 503 plate_retry, to be asked again after this many seconds
ROOM_MIN_S = 5                       # a step that found no room (guard.Busy) is answered 503 room_retry and asked again after the holder's remaining
ROOM_MAX_S = D.WAIT_MAX_S            # estimate (retry_after), never less than ROOM_MIN_S nor more than ROOM_MAX_S (the longest back-off of a chain)
ROOM_DEFAULT_S = 10                  # ... and this many seconds when no holder declared an estimate
WATCHDOG_MAX = 2                     # relays armed for one step, at most
FRESH_ARRIVAL_S = 3.0                # an invocation that had at least BUDGET minus this much left on arrival is fresh
LOCK_STALE = D.LEASE_STALE_S         # a claim older than this belongs to an invocation that is dead
WORDS_RAW_MAX = 1000                 # characters of one customer text field that are read at all
WORDS_PARTS_MAX = 16
RECORD_MAX = 48 << 10                # a record is read back with store.get_json (64 KB): keep well under
INDEX = "cleanup/style"              # one marker per order that has a style folder: the clean-up's index (api/_lib/cleanup.py)


class Hold(Exception):
    """The order must be held for a person: never made in another style, never retried. reason is a code (the owner's note and the events carry it),
    note a sentence for the owner."""

    def __init__(self, reason, note=""):
        super().__init__(reason)
        self.reason = reason
        self.note = note or reason


# ----------------------------------------------------------------------------- the context of one call
class Ctx:
    """What a step needs to know about the order it works for. spec: the paid spec {eyes, style, layout, names, title, date?, opts?}. finish(result)
    writes delivery.json and returns it (None for an admin call that writes its own). arm(): arms the watchdog (None: none, an admin call waits for
    its own answer). legacy(body): the legacy master compose (the order module's own MC.master_compose, so a test that stubs it is heard). lab: a
    lab test order (no paid record, no checkout plan, nothing is held)."""

    def __init__(self, order, spec, rec=None, paid=None, by="server", arrival_left=None, finish=None, arm=None, legacy=None, lab=False,
                 eyes_from="draft"):
        self.order = store.check_order(order)
        self.spec = spec if isinstance(spec, dict) else {}
        self.rec, self.paid = rec, paid
        self.by, self.lab = by, bool(lab)
        self.arrival_left = arrival_left
        self.finish, self.arm, self.legacy = finish, arm, legacy
        self.eyes_from = eyes_from
        self.folder = f"orders/{self.order}"

    @property
    def n(self):
        return int(self.spec.get("eyes") or 0)


# ----------------------------------------------------------------------------- small helpers
def _pay():
    from .. import pay
    return pay


def _L():
    from .. import iris
    return iris


def _log(msg):
    try:
        _pay().log(msg)
    except Exception:  # noqa: a log line must never cost a step
        pass


def _parallel(fns):
    return _pay().parallel(fns)


def _safe(name):
    return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_") or "step"


def _sfx(rerun):
    return f"_r{int(rerun)}" if rerun else ""


def path(order, name):
    return f"orders/{store.check_order(order)}/{FOLDER}/{name}"


def _jbytes(obj):
    return store.json_bytes(_plain(obj))


def _plain(v, depth=0):
    """A JSON-safe copy of what an engine reported (numpy numbers and arrays, tuples, bytes): small values only."""
    if depth > 6:
        return None
    if v is None or isinstance(v, (bool, str)):
        return v
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return v if v == v and abs(v) != float("inf") else None
    if isinstance(v, dict):
        return {str(k)[:60]: _plain(x, depth + 1) for k, x in list(v.items())[:60]}
    if isinstance(v, (list, tuple)):
        return [_plain(x, depth + 1) for x in list(v)[:40]]
    item = getattr(v, "item", None)
    if callable(item):
        try:
            return _plain(item(), depth + 1)
        except Exception:  # noqa
            return None
    return str(v)[:120]


def _sha12(data):
    return hashlib.sha256(data).hexdigest()[:12]


def _hash8(text):
    return hashlib.sha256(str(text).encode("utf-8", "replace")).hexdigest()[:8]


def _iso(t=None):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() if t is None else t))


# ----------------------------------------------------------------------------- the customer's words
def _clean_names(value, limit=60):
    """The customer's names as the v3 engine draws them (the same function of the same input as api/compose.py _engine_text, so the paid file draws
    the words of the preview; a test holds them equal): cleaned, one lockup line, without a letter the artwork font cannot draw."""
    from . import text as TX
    if isinstance(value, (list, tuple)):
        value = [v[:WORDS_RAW_MAX] for v in value[:WORDS_PARTS_MAX] if isinstance(v, str)]
    elif isinstance(value, str):
        value = value[:WORDS_RAW_MAX]
    else:
        return ""
    parts = [p for p in (TX.clean("".join(ch for ch in n if not TX.unsupported(ch))) for n in TX.split_names(value)) if p]
    out = TX.lockup(parts)
    return out[:limit] if limit else out


def _clean_date(value, limit=20):
    from . import text as TX
    if not isinstance(value, str):
        return ""
    out = TX.clean("".join(ch for ch in value[:WORDS_RAW_MAX] if not TX.unsupported(ch)))
    return out[:limit] if limit else out


def master_words(spec):
    """(names line, date line) the paid file draws: the names cut at 60 characters and the date at 20, as the preview does."""
    return _clean_names(spec.get("names"), 60), _clean_date(spec.get("date"), 20)


def words_sha(spec):
    n, d = master_words(spec)
    return _hash8(f"{n}\n{d}")


# ----------------------------------------------------------------------------- the plan
PLAN8_KEYS = ("v", "pv", "engine_v", "style", "family", "design_used", "fallback", "layout", "canvas", "opts", "eyes", "eye_ids", "work_side",
              "seed_key", "plate_families", "plates", "clean")


def plan8(plan):
    """The identity of a plan: 8 hex digits of everything that decides the picture. NOT in it: the registry hash (provenance), the estimates, the
    time of creation, the profile facts: an edit of an unrelated registry entry, a new slow factor or a different clock never renames an artwork."""
    core = {k: plan.get(k) for k in PLAN8_KEYS}
    core["steps"] = [[s.get("name"), s.get("kind"), s.get("eyes")] for s in (plan.get("steps") or []) if isinstance(s, dict)]
    return hashlib.sha256(json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest()[:8]


def valid_plan(plan):
    """A stored plan this code can run: the plan's version, a style of the registry, at least one step with a name and a kind."""
    if not isinstance(plan, dict) or plan.get("v") != PLAN_VERSION or not CT.known(plan.get("style")):
        return False
    steps = plan.get("steps")
    return (isinstance(steps, list) and steps and all(isinstance(s, dict) and isinstance(s.get("name"), str) and isinstance(s.get("kind"), str)
                                                       for s in steps) and isinstance(plan.get("eyes"), int) and 1 <= plan["eyes"] <= 8)


def _opts(spec):
    o = spec.get("opts") if isinstance(spec.get("opts"), dict) else {}
    return {k: o.get(k) for k in ("swap", "rotate", "look")}


def _eye_facts(eyes):
    """[{cls, rgb, pad}] of the sealed profiles the eyes carry (None where an eye has none): the colour class the preview was drawn for, the ring colour
    in tenths of a level and the crop padding in thousandths, so that the master can say how far it drifted (class and colour, and the pad it was cut with)."""
    out = []
    for e in eyes or []:
        prof = (e or {}).get("profile")
        st = prof.get("stats") if isinstance(prof, dict) else None
        if isinstance(prof, dict) and isinstance(prof.get("cls"), str) and isinstance(st, dict) and isinstance(st.get("rgb"), list):
            row = {"cls": prof["cls"], "rgb": [int(x) for x in st["rgb"][:3]]}
            if isinstance(prof.get("pad"), int) and not isinstance(prof.get("pad"), bool):
                row["pad"] = prof["pad"]
            out.append(row)
        else:
            out.append(None)
    return out


def make_plan(spec, eyes=None, factor=None):
    """The plan of a spec ({style, layout, eyes, opts}) and its eyes ([{eye_id, profile}], the draft's records): resolve() of the engine (no pixels), the
    steps with their estimated seconds and megabytes, plan8. Pure: it stores nothing. Raises Hold when no engine can draw the style."""
    style, n = spec.get("style"), spec.get("eyes")
    if not CT.known(style) or not isinstance(n, int) or isinstance(n, bool) or not CT.in_range(style, n):
        raise Hold("no_engine", f"style {style!r} does not take {n!r} eyes")
    eng = CT.engine_for(style, n)
    if eng is None:
        raise Hold("no_engine", f"style {style!r} has no engine for {n} eyes")
    layout = spec.get("layout") or CT.default_layout(style, n)
    opts = _opts(spec)
    plan = {"v": PLAN_VERSION, "reg": CT.registry_hash(), "pv": CT.PLATES_VERSION, "style": style, "eyes": n, "layout": layout, "opts": opts,
            "family": eng["module"], "eye_ids": [str((e or {}).get("eye_id") or "")[:16] for e in (eyes or [])],
            "eye_prof": _eye_facts(eyes), "plate_families": list(eng.get("plates") or []), "work_side": eng.get("work_side")}
    if eng["module"] == "legacy":
        plan.update(engine_v=0, design_used=style, fallback=None, canvas="artwork", seed_key=None, clean=0, cost_key=None)
    else:
        from .. import styles as ST
        try:
            rp = ST.resolve({"style": style, "layout": layout, "eyes": n, "opts": opts, "canvas": None}, [(e or {}).get("profile") for e in (eyes or [])])
        except ST.EngineNotBuilt as e:
            raise Hold("no_engine", str(e)) from None
        try:
            key = CO.cost_key(eng, "dark", opts.get("look"))
        except CO.NoCost:
            key = None
        plates = [str(x) for x in rp["plates"]] if isinstance(rp.get("plates"), (list, tuple)) and rp["plates"] else None
        plan.update(engine_v=ENGINE_V, design_used=rp.get("design_used"), fallback=rp.get("fallback"), canvas=rp.get("canvas"),
                    seed_key=rp.get("seed_key"), seed_from=rp.get("seed_from"), clean=1 if rp.get("clean") else 0, cost_key=key, plates=plates)
        if plates:
            # the 4K plates the picture will draw from (the id, the storage path, the sha256 and the size of each: checkout verifies that every one is in
            # storage before the customer pays, and the step never substitutes another). A family that draws plates not known before the render
            # (the single styles seed from the master's own bytes until the seed comes from eye_id) leaves plates empty: the family is in plate_families.
            from . import plates as PL
            plan["plates_needed"] = PL.needed(plates)
    plan["steps"] = plan_steps(plan, factor)
    plan["plan8"] = plan8(plan)
    return plan


def plan_steps(plan, factor=None):
    """The steps of a plan: one "art" step covering every eye. (WP6b: the planner cuts a master into more only when the need passes
    costs.STYLE_STEP_BUDGET; until that work lands the step is one and the plan says it would like to be cut.)"""
    n = plan["eyes"]
    cap = capacity(plan, factor)
    return [{"name": ART, "kind": ART, "eyes": list(range(1, n + 1)), "need_s": cap["need_s"], "est_mb": cap["est_mb"],
             "split_wanted": bool(cap["need_s"] is not None and CO.exceeds_step_budget(cap["need_s"]))}]


def capacity(plan, factor=None):
    """Can the plan's art step run at all on this instance? {ok, why, need_s, est_mb, factor, budget_s, mem_budget_mb}: why is None, "time" (the need
    passes the work budget at this factor: it can NEVER finish), "memory" (the estimate passes the memory budget) or "no_cost" (the cost table has
    no row: a style the table cannot price is not one that may be sold). Checkout refuses a plan that is not ok (409 capacity, WP12); a paid order
    whose plan is not ok is held (Hold style_step_too_big), never retried as busy."""
    F = CO.slow_factor() if factor is None else float(factor)
    if plan.get("family") == "legacy":
        need = CO.legacy_need(plan["eyes"], F)
        return {"ok": need <= CO.WORK_BUDGET_S, "why": None if need <= CO.WORK_BUDGET_S else "time", "need_s": need, "est_mb": None, "factor": F,
                "budget_s": CO.WORK_BUDGET_S, "mem_budget_mb": CO.MEM_BUDGET_MB}
    a = CO.assess(plan.get("cost_key"), plan["eyes"], size=SIZE, side=plan.get("work_side"), factor=F)
    return {"ok": bool(a["ok"]), "why": a["why"], "need_s": a["need_s"], "est_mb": a["est_mb"], "factor": F, "budget_s": CO.WORK_BUDGET_S,
            "mem_budget_mb": CO.MEM_BUDGET_MB}


def longest_chain():
    """The longest planned chain of the server's own making, in hops: the eyes, the master steps of the plan, and the ready email. The default plan is
    one art step, so eight eyes are 8 + 1 + 1 = 10 hops, the same chain as before the plan existed (eyes, compose, mail): the v3 work adds no hop."""
    best = 0
    for sid in CT.ids():
        lo, hi = CT.eyes_range(sid)
        for n in range(lo, hi + 1):
            e = CT.engine_for(sid, n)
            best = max(best, n + (len(e["steps"]) if e and e.get("steps") else 1) + 1)
    return best


# ----------------------------------------------------------------------------- the stored state
def _rerun_n(rec):
    n = rec.get("n") if isinstance(rec, dict) else 0
    return n if isinstance(n, int) and not isinstance(n, bool) and 0 <= n <= 1000 else 0


def _new_try():
    return {"kills": 0, "open": False, "plate": 0, "errors": [], "watchdog": 0, "attempts": 0}


def _read_try(rec):
    t = _new_try()
    if isinstance(rec, dict):
        for k in ("kills", "plate", "watchdog", "attempts"):
            if isinstance(rec.get(k), int) and not isinstance(rec.get(k), bool):
                t[k] = max(0, min(rec[k], 1000))
        t["open"] = rec.get("open") is True
        if isinstance(rec.get("errors"), list):
            t["errors"] = [str(x)[:40] for x in rec["errors"][:10]]
        for k in ("t", "id", "last", "plate_id"):
            if k in rec:
                t[k] = rec[k]
    return t


def state_reads(order):
    """The reads of the first round of read_state (the plan, the rerun count, the unsalted done and try records of the art step), as functions of no
    argument: maker._facts runs them in its own parallel read, so the chain's decision costs no extra round trip."""
    g = lambda name: (lambda: store.get_json(path(order, name), timeout=5.0, retry=False))
    return [g("plan.json"), g("rerun.json"), g(f"done_{ART}.json"), g(f"try_{ART}.json")]


def state_from(order, vals):
    """The state from the four values of state_reads (a plan with more than one step, or a rerun, needs a second round: read_state)."""
    plan, rr, done0, try0 = vals
    plan = plan if valid_plan(plan) else None
    rerun = _rerun_n(rr)
    names = [s["name"] for s in plan["steps"]] if plan else [ART]
    if rerun or names != [ART]:
        return read_state(order)
    return _state(plan, rerun, {ART: done0 if isinstance(done0, dict) else None}, {ART: _read_try(try0)}, names)


def _state(plan, rerun, done, tries, names):
    missing = [s for s in names if not done.get(s)]
    return {"plan": plan, "rerun": rerun, "done": done, "tries": tries, "names": names, "next": missing[0] if missing else None,
            "done_n": len(names) - len(missing), "of": len(names)}


def read_state(order):
    """The stored state of the order's steps: plan, rerun count, the done and try record of every step (two parallel rounds)."""
    g = lambda name: (lambda: store.get_json(path(order, name), timeout=5.0, retry=False))
    plan, rr = _parallel([g("plan.json"), g("rerun.json")])
    plan = plan if valid_plan(plan) else None
    rerun = _rerun_n(rr)
    names = [s["name"] for s in plan["steps"]] if plan else [ART]
    reads = []
    for nm in names:
        reads += [g(f"done_{_safe(nm)}{_sfx(rerun)}.json"), g(f"try_{_safe(nm)}{_sfx(rerun)}.json")]
    got = _parallel(reads)
    done = {nm: (got[2 * i] if isinstance(got[2 * i], dict) else None) for i, nm in enumerate(names)}
    tries = {nm: _read_try(got[2 * i + 1]) for i, nm in enumerate(names)}
    return _state(plan, rerun, done, tries, names)


def progress(state):
    """{done, of, step}: what the order page and the status reply show of the artwork: steps done, steps in all, the name of the next one."""
    return {"done": state["done_n"], "of": state["of"], "step": state["next"]}


# ----------------------------------------------------------------------------- the plan record
def _stored_plan(rec):
    """A plan the checkout froze (order.json "plan", or inside "checkout"): the master reads it and never works the geometry out again."""
    if not isinstance(rec, dict):
        return None
    for p in (rec.get("plan"), (rec.get("checkout") or {}).get("plan") if isinstance(rec.get("checkout"), dict) else None):
        if valid_plan(p):
            return p
    return None


def _eye_inputs(ctx):
    """[{eye_id, profile}] of the order's eyes: the draft's records (the sealed profile read from the seal, never from the page), or for a lab test
    order the eye masters' own records."""
    n = ctx.n
    names = ([f"{ctx.folder}/draft/eye_{i}.json" for i in range(1, n + 1)] if ctx.eyes_from == "draft"
             else [f"{ctx.folder}/eye_{i}.json" for i in range(1, n + 1)])
    recs = _parallel([lambda p=p: store.get_json(p, timeout=5.0, retry=False) for p in names])
    return [{"eye_id": (r or {}).get("eye_id") if isinstance(r, dict) else None, "profile": (r or {}).get("profile") if isinstance(r, dict) else None}
            for r in recs]


def index_style(order):
    """The clean-up's index: one marker per order that has a style folder (api/_lib/cleanup.py removes the folder 14 days after delivery.json)."""
    try:
        store.put(f"{INDEX}/{order}.json", store.json_bytes({"t": int(time.time())}), "application/json", upsert=False, timeout=4.0, retry=False)
    except store.StorageExists:
        pass
    except store.StorageError as e:
        _log(f"order {order}: style index not stored: {e}")


def create_plan(ctx):
    """The order's plan: the one the checkout froze, else made now from the eyes' sealed profiles and stored (upsert=False: of two callers the first
    wins and both use that one)."""
    plan = _stored_plan(ctx.rec)
    if plan is None:
        plan = make_plan(ctx.spec, _eye_inputs(ctx))
    plan = dict(plan, created_at=plan.get("created_at") or int(time.time()))
    data = _jbytes(plan)
    if len(data) > RECORD_MAX:
        raise Hold("plan_too_large", f"the plan record is {len(data)} bytes")
    try:
        store.put(path(ctx.order, "plan.json"), data, "application/json", upsert=False, timeout=6.0, retry=False)
        if not ctx.lab:
            index_style(ctx.order)
    except store.StorageExists:
        cur = store.get_json(path(ctx.order, "plan.json"), timeout=6.0, retry=False)
        if valid_plan(cur):
            plan = cur
    return plan


def check_skew(plan):
    """The running ENGINE_V against the plan's: a deploy between payment and master that changed a golden must never draw a picture the preview did
    not show (a legacy plan carries no engine version)."""
    if plan.get("family") != "legacy" and plan.get("engine_v") != ENGINE_V:
        raise Hold("engine_skew", f"the plan was made under engine version {plan.get('engine_v')}, this deployment runs {ENGINE_V}")


HOLDS = {
    "style_step_too_big": ("the master of this order can never finish in one call on this deployment (its time or memory need passes the budget at the "
                           "slow factor in force), so it was held instead of retried",
                           "Measure the factor (scripts/cpu_probe.py --remote, STYLE_SLOW_CPU), check the function memory (STYLE_FUNCTION_MEM_MB), or "
                           "raise the duration limit (api/_lib/duration.py with vercel.json maxDuration) or build the reserve split; then clear the "
                           "review"),
    "style_not_priced": ("the cost table has no row for this style and eye count, so nobody knows whether its master fits a call",
                         "Bake a row for it (scripts/bake_costs.py) or make the order by hand; then clear the review"),
    "engine_skew": ("the engine's pictures changed (ENGINE_V) between this order's payment and its master: drawing it now would not be the picture "
                    "the customer approved",
                    "Roll the deployment back to the version the order was paid under, or look at the picture the running version draws (the admin "
                    "laboratory) and, if you accept it, have the order's plan made again (delete its style/plan.json); then clear the review"),
    "class_changed": ("the 4096 px master of an eye has another colour class than its preview (the palette would not be the approved one)",
                      "Look at the preview and the master in the admin panel; render the eye again if the master is wrong, or write to the customer"),
    "style_step_failed": ("a master step was killed three times, or raised the same exception twice",
                          "Look at the Vercel log of /api/order and /api/admin around the order's time (memory? time?); fix the cause; then clear the "
                          "review"),
    "plate_unavailable": ("a 4K plate of this style is not in storage, or is not the file the registry names, twice in a row",
                          "Upload the plates (python scripts/upload_plates.py --yes) and check the storage with the admin action plates_status; then "
                          "clear the review. The order is never drawn with another plate"),
    "plan_mismatch": ("the plan stored for this order is for another style or another number of eyes than the order's own record says (it was changed "
                      "by hand?)", "Look at orders/<order>/style/plan.json and the paid record; delete the plan if it is wrong; then clear the review"),
    "no_engine": ("no engine can draw this style for this number of eyes on this deployment",
                  "The style may have been rolled back to a build without its engine: deploy the build that has it; then clear the review"),
}


def hold_text(reason, order):
    """(why it waits, what to do) of a hold of the master steps for the owner's reminder (api/_lib/cleanup.py), or None for another reason."""
    h = HOLDS.get(str(reason or "").split(" ")[0])
    if h is None:
        return None
    return h[0], f"{h[1]}. In the admin panel (/admin, order {order}) or: python scripts/order_admin.py clear-review {order}."


# ----------------------------------------------------------------------------- claims and the try record
def _claim(order, name):
    """Claim <name> (style/<name>.lock), created atomically: of two callers exactly one gets it. A live claim of another is a 409 rendering; one older
    than LOCK_STALE belongs to an invocation that is dead and is taken over. Returns (path, id)."""
    lock = path(order, f"{_safe(name)}.lock")
    mine = secrets.token_hex(6)
    body = store.json_bytes({"t": round(time.time(), 3), "id": mine})
    age = None
    for _ in range(3):
        try:
            store.put(lock, body, "application/json", upsert=False, timeout=5.0, retry=False)
            return lock, mine
        except store.StorageExists:
            pass
        cur = store.get_json(lock, timeout=5.0, retry=False)
        if cur is None:
            continue                     # released a moment ago
        try:
            age = time.time() - float(cur.get("t"))
        except (TypeError, ValueError):
            age = None
        if age is not None and -60.0 < age < LOCK_STALE:
            break
        _log(f"order {order}: a stale step claim ({'unreadable' if age is None else f'{age:.0f} s old'}) is taken over")
        store.delete(lock, timeout=5.0, retry=False)
    wait = 15 if age is None else int(max(5, min(D.WAIT_MAX_S, LOCK_STALE - age)))
    raise store.Answer(409, "rendering", "Your artwork is being put together. Please wait a moment.", True, wait)


def _release(claim):
    lock, mine = claim
    try:
        cur = store.get_json(lock, timeout=4.0, retry=False)
        if isinstance(cur, dict) and cur.get("id") == mine:
            store.delete(lock, timeout=4.0, retry=False)
    except store.StorageError as e:
        _log(f"step claim not released (taken over after {LOCK_STALE:.0f} s): {e}")


def _write_try(order, step, rerun, t):
    t = dict(t, t=round(time.time(), 3))
    store.put(path(order, f"try_{_safe(step)}{_sfx(rerun)}.json"), _jbytes(t), "application/json", upsert=True, timeout=5.0, retry=False)


def _try_open(order, step, rerun, claim):
    """Read the try record under the claim; an `open` still set means the last attempt was killed: count it, and hold at the third kill. Then set
    open. Returns the record."""
    rec = _read_try(store.get_json(path(order, f"try_{_safe(step)}{_sfx(rerun)}.json"), timeout=5.0, retry=False))
    if rec["open"]:
        rec["kills"] += 1
        _log(f"order {order}: step {step} was killed before ({rec['kills']} of {KILLS_MAX})")
        if rec["kills"] >= KILLS_MAX:
            rec["open"] = False
            _write_try(order, step, rerun, rec)
            raise Hold("style_step_failed", f"step {step} was killed {rec['kills']} times (no done record): the render dies in this function, "
                       f"look at the Vercel log of /api/order and /api/admin")
    rec.update(open=True, attempts=rec["attempts"] + 1, id=claim[1])
    _write_try(order, step, rerun, rec)
    return rec


def _try_close(order, step, rerun, rec):
    try:
        rec = dict(rec, open=False)
        _write_try(order, step, rerun, rec)
    except store.StorageError as e:
        _log(f"order {order}: step {step} left open (a false kill is counted at the next attempt): {e}")


# ----------------------------------------------------------------------------- the executors
class Out:
    """What an executor made: result (the artwork's reply), outputs (the stored objects), extras for the done record."""

    def __init__(self, result, outputs, **extra):
        self.result, self.outputs, self.extra = result, outputs, extra


def artwork_key(order, plan, rerun):
    d = hashlib.sha256(json.dumps({"plan8": plan.get("plan8") or plan8(plan), "rerun": int(rerun)}, sort_keys=True).encode()).hexdigest()[:16]
    return f"orders/{order}/artwork_{d}.jpg"


def _identity(rec):
    """Which render an eye slot holds: a re-render rewrites the record, so a changed master changes this (master_compose._identity)."""
    if not isinstance(rec, dict) or not rec:
        return "no-record"
    return f"{rec.get('created')}|{rec.get('bytes')}|{rec.get('kept') or ''}"


def _inputs(ctx, plan, recs):
    return {"eyes": [_identity(r) for r in recs], "words": words_sha(ctx.spec), "plan8": plan.get("plan8")}


def _eye_keys(ctx, step):
    return [f"{ctx.folder}/eye_{i}.jpg" for i in step["eyes"]]


def _pupil_failed(qa):
    if isinstance(qa, dict) and isinstance(qa.get("eyes"), list):
        return any(_pupil_failed(q) for q in qa["eyes"])
    return isinstance(qa, dict) and qa.get("pupil_neutral") is False


def _exec_legacy(ctx, plan, step, rerun):
    """The legacy engine: the order module's own master compose, called with the body it always got. Its file name is its own digest (unchanged)."""
    if ctx.legacy is None:
        raise Hold("no_engine", "no legacy composer was given to this step")
    L = _L()
    spec = ctx.spec
    body = {"order": ctx.order, "ticket": L.mint_ticket(store.unlock_kind(ctx.order), 300), "keys": _eye_keys(ctx, step),
            "style": spec.get("style"), "layout": spec.get("layout"), "names": spec.get("names") or "", "title": spec.get("title") or ""}
    r = ctx.legacy(body)
    res = {k: r.get(k) for k in ("key", "width", "height", "bytes", "style", "layout", "count", "needs_review", "existing", "qa", "url", "seconds")}
    res["needs_review"] = bool(r.get("needs_review"))
    out = [{"path": r.get("key"), "bytes": r.get("bytes"), "sha12": None}]
    recs = _parallel([lambda k=k: store.get_json(k[:-4] + ".json", timeout=5.0, retry=False) for k in body["keys"]])
    return Out(res, out, inputs=_inputs(ctx, plan, recs))


def _exec_engine(ctx, plan, step, rerun):
    """A style of the v3 engine: the eyes' 4096 px masters from storage, the family's preview() at 4096 px (clean: the paid file has no watermark),
    the checks, JPEG q95 4:4:4, the artwork and its record. Idempotent: an artwork whose digest is already stored with its record is reused."""
    L = _L()
    from .. import styles as ST
    from . import core as SCORE
    order, folder, n = ctx.order, ctx.folder, plan["eyes"]
    keys = _eye_keys(ctx, step)
    key = artwork_key(order, plan, rerun)
    recs = _parallel([lambda k=k: store.get_json(k[:-4] + ".json", timeout=5.0, retry=False) for k in keys])
    inputs = _inputs(ctx, plan, recs)
    if store.exists(key, timeout=5.0, retry=False):
        art = store.get_json(key[:-4] + ".json", timeout=5.0, retry=False)
        if isinstance(art, dict) and art.get("bytes"):
            # a kill between the outputs and the done record: the outputs are complete (the record is written after the picture), so reuse them
            _log(f"order {order}: {key} is stored already, not drawn again")
            res = {k: art.get(k) for k in ("width", "height", "bytes", "style", "layout", "count", "qa")}
            res.update(key=key, existing=True, needs_review=bool(art.get("needs_review")), url=store.signed_url(key, LINK_SECONDS), seconds=0.0)
            return Out(res, [{"path": key, "bytes": art.get("bytes"), "sha12": art.get("sha12")}, {"path": key[:-4] + ".json", "bytes": None, "sha12": None}],
                       inputs=inputs, drift=art.get("drift"), reused=True)
    side = min(int(plan.get("work_side") or SIZE), SIZE)
    eyes, drift = [], []
    for i, (k, rec) in enumerate(zip(keys, recs), 1):
        raw = store.get(k, timeout=20.0, retry=False)
        if raw is None:
            raise store.Answer(409, "eyes_not_ready", "Not every eye is finished yet.", True, 5, missing=[i])
        eid = (rec or {}).get("eye_id") if isinstance(rec, dict) else None
        eyes.append(SCORE.Iris(raw, f"eye{i}", max_side=side, eye_id=eid if isinstance(eid, str) and eid else None))
        del raw
    prof = plan.get("eye_prof") or []
    for i, eye in enumerate(eyes):
        want = prof[i] if i < len(prof) else None
        if not want:
            drift.append(None)
            continue
        st = eye.stats
        d_rgb = max(abs(a / 10.0 - b) for a, b in zip(want["rgb"], st["mean_rgb"]))
        row = {"cls": [want["cls"], st["class"]], "d_rgb": round(d_rgb, 1)}
        mrec = recs[i] if i < len(recs) else None
        if isinstance(want.get("pad"), int) and isinstance(mrec, dict) and isinstance(mrec.get("pad"), (int, float)) and not isinstance(mrec.get("pad"), bool):
            row["d_pad"] = round(abs(want["pad"] / 1000.0 - float(mrec["pad"])), 3)         # the crop padding of the preview against the master's
        drift.append(row)
        if want["cls"] != st["class"]:
            raise Hold("class_changed", f"eye {i + 1}: the master's colour class is {st['class']}, the preview's was {want['cls']} (the ring colour "
                       f"moved {d_rgb:.1f} levels): the picture would take another palette than the one the customer approved")
    names, date = master_words(ctx.spec)
    fam_spec = {"style": plan["style"], "layout": plan["layout"], "eyes": n, "canvas": plan.get("canvas"), "names": names, "date": date, "opts": plan.get("opts")}
    t0 = time.time()
    pv = ST.preview(eyes, fam_spec, size=SIZE, watermark=False, check=True)
    t1 = time.time()
    graded = list(pv.graded or [])
    qa_eyes = [L.colour_qa(f"art {folder} eye {i + 1}/{n}", graded=L.Image.fromarray(g)) for i, g in enumerate(graded)]
    qa = {"ok": all(q["ok"] for q in qa_eyes) if qa_eyes else None, "eyes": qa_eyes}
    sc = pv.selfcheck if isinstance(pv.selfcheck, dict) else None
    sc_brief = None if sc is None else {"ok": bool(sc.get("ok")), "ms": sc.get("ms"),
                                        "checks": {k: {kk: vv for kk, vv in c.items() if kk in ("ok", "bad", "share", "violations", "drawn", "count")}
                                                   for k, c in (sc.get("checks") or {}).items() if isinstance(c, dict)}}
    eyes_review = any(store.needs_review(r) for r in recs)
    needs_review = bool(eyes_review or _pupil_failed(qa) or (sc is not None and sc.get("ok") is False))
    img = pv.img
    W, H = img.size
    facts, seed, times, design = _plain(pv.log), str(pv.seed), _plain(pv.times), pv.design
    data = store.jpeg_bytes(img, 95)
    del img, pv, eyes
    sha12 = _sha12(data)
    store.put(key, data, "image/jpeg", upsert=True)
    record = {"v": 1, "order": order, "style": plan["style"], "layout": plan["layout"], "count": n, "design_used": design, "canvas": plan.get("canvas"),
              "width": W, "height": H, "bytes": len(data), "sha12": sha12, "qa": qa, "selfcheck": sc_brief, "needs_review": needs_review,
              "plan8": plan.get("plan8"), "engine_v": plan.get("engine_v"), "reg": plan.get("reg"), "pv": plan.get("pv"), "rerun": int(rerun),
              "seed": seed, "times": times, "drift": drift, "inputs": inputs, "created": _iso()}
    if len(json.dumps(facts)) < 12000:
        record["facts"] = facts
    try:
        store.put(key[:-4] + ".json", _jbytes(record), "application/json", upsert=True)
    except store.StorageError as e:
        _log(f"order {order}: artwork record not stored: {e}")
    res = {"key": key, "width": W, "height": H, "bytes": len(data), "style": plan["style"], "layout": plan["layout"], "count": n, "existing": False,
           "needs_review": needs_review, "qa": qa, "url": store.signed_url(key, LINK_SECONDS), "seconds": round(time.time() - t0, 1)}
    return Out(res, [{"path": key, "bytes": len(data), "sha12": sha12}, {"path": key[:-4] + ".json", "bytes": None, "sha12": None}],
               inputs=inputs, drift=drift, render_s=round(t1 - t0, 2), selfcheck=sc_brief)


def _exec_art(ctx, plan, step, rerun):
    return (_exec_legacy if plan.get("family") == "legacy" else _exec_engine)(ctx, plan, step, rerun)


EXECUTORS = {ART: _exec_art}          # kind -> executor(ctx, plan, step, rerun) -> Out (WP6b adds the reserve split's prep kind)


# ----------------------------------------------------------------------------- running a step
def _record(ctx, plan, step, k, of, ms=None, hold=None, existing=False, **kw):
    """The master event of a step (api/_lib/events.py): codes and numbers only."""
    try:
        from .. import events as E
        E.record("master", step=_safe(step["name"]), part=k, of=of, ms=ms, order=ctx.order, count=plan["eyes"], style=plan["style"],
                 design=plan.get("design_used"), existing=existing, hold=hold, **kw)
    except Exception:  # noqa: an event never costs a step
        pass


def _fresh(ctx):
    """Had this invocation (almost) all its time on arrival? Then a refusal for lack of time is a configuration error, not a busy moment."""
    L = _L()
    left = ctx.arrival_left if ctx.arrival_left is not None else L.time_left()
    return left >= L.BUDGET - FRESH_ARRIVAL_S


def _too_big(plan, cap, why):
    return Hold("style_step_too_big", f"the {plan['style']} master of {plan['eyes']} eye(s) ({plan.get('design_used')}) needs about {cap['need_s']} s "
                f"(the work budget is {cap['budget_s']:.0f} s at the slow factor {cap['factor']}) and {cap['est_mb']} MB (the memory budget is "
                f"{cap['mem_budget_mb']} MB): {why}. It can never finish in one call here, so it is held, not retried.")


def _busy():
    return store.busy("busy_retry", 5, "We are busy for a moment. Please try again now.")


def _room(e):
    """The answer to a step that found no room (guard.Busy: another heavy render holds this instance's CPU or memory): 503 room_retry whose retry_after
    is how long the holder that frees room first still needs by its own estimate, between ROOM_MIN_S and ROOM_MAX_S (ROOM_DEFAULT_S when it declared
    none). The chain and the order page wait that long before they ask again, so a second paid order does not spend its busy hops in the few seconds
    the waits take (the first answer of this kind was busy_retry, asked again at once: ten hops in about twenty seconds, then a note that blamed the
    image model). `room` names the guard that refused (cpu or memory)."""
    eta = getattr(e, "eta_s", None)
    s = ROOM_DEFAULT_S if not isinstance(eta, (int, float)) or isinstance(eta, bool) or eta != eta else int(math.ceil(eta))
    s = int(max(ROOM_MIN_S, min(ROOM_MAX_S, s)))
    return store.Answer(503, "room_retry", "We are busy for a moment. Please try again shortly.", True, s, room=str(getattr(e, "kind", ""))[:8])


def _counted_failure(ctx, plan, step, rerun, tr, e):
    """An executor raised an exception of its own. A plate that is missing or does not match is counted in the try record (kind plate: never a
    MAX_BUSY hop), answered 503 plate_retry the first time and held the second. Any other exception is noted by its signature: the second identical
    one holds the order (the first is raised as it is: the chain's making_error note, one more retry). Raises the hold or the answer."""
    order, name = ctx.order, step["name"]
    if hasattr(e, "plate_id") and hasattr(e, "why"):
        tr["plate"] += 1
        tr["plate_id"] = str(getattr(e, "plate_id"))[:80]
        tr["last"] = f"plate:{getattr(e, 'why')}"
        _write_try(order, name, rerun, tr)
        if tr["plate"] >= PLATE_MAX:
            raise Hold("plate_unavailable", f"a plate of the {plan['style']} master is not available twice in a row ({tr['plate_id']}, "
                       f"{getattr(e, 'why')}): the order is held, never drawn with another plate") from e
        raise store.Answer(503, "plate_retry", "A file we need is not ready for a moment. Please try again shortly.", True, PLATE_RETRY_S) from e
    sig = f"{type(e).__name__}:{_hash8(str(e))}"
    seen = sig in tr["errors"]
    tr["last"] = sig
    tr["errors"] = (tr["errors"] + [sig])[-ERRORS_MAX:]
    _write_try(order, name, rerun, tr)
    if seen:
        raise Hold("style_step_failed", f"step {name} raised the same exception twice ({type(e).__name__}): {str(e)[:160]}") from e


def run_step(ctx, plan, step, k, rerun=0, after=None):
    """One step through the state machine of the module text. after(out), when given, runs after the done record and inside the claim, before `open`
    is cleared (compose_order writes delivery.json there). Returns {out, done}. Raises Hold, store.Answer (409 rendering, 503 busy_retry, 503
    room_retry, 503 plate_retry, 409 eyes_not_ready) or the executor's own exception (after counting it)."""
    L = _L()
    order, name = ctx.order, step["name"]
    of = len(plan["steps"])
    exe = EXECUTORS.get(step.get("kind"))
    try:
        if exe is None:
            raise Hold("no_engine", f"no executor for a step of kind {step.get('kind')!r}")
        cap = capacity(plan)
        mb, secs = cap["est_mb"], cap["need_s"]
        # a plan that can never fit is a configuration error: held before any guard, claim or record (no busy hop is spent on it)
        if cap["why"] in ("time", "memory"):
            raise _too_big(plan, cap, cap["why"])
        if cap["why"] == "no_cost" and not ctx.lab:
            raise Hold("style_not_priced", f"the cost table has no row for the {plan['style']} master of {plan['eyes']} eye(s): a style the table "
                       f"cannot price is not one that is made after payment")
        with contextlib.ExitStack() as stack:
            try:
                stack.enter_context(GD.slot(est_mb=mb, est_s=secs, left=L.time_left()))
            except GD.Busy as e:
                _log(f"order {order}: no room for the {name} step ({e.kind}), asked again in a moment")
                raise _room(e) from None
            # the wait for the guards counts against the time: look at what is left only now
            if secs is not None and secs > L.time_left():
                if _fresh(ctx):
                    raise _too_big(plan, cap, f"a fresh call has only {L.time_left():.0f} s left")
                raise _busy()
            claim = _claim(order, name)
            stack.callback(_release, claim)
            tr = _try_open(order, name, rerun, claim)
            stack.callback(_try_close, order, name, rerun, tr)
            if ctx.arm is not None and tr["watchdog"] < WATCHDOG_MAX:
                tr["watchdog"] += 1
                try:
                    _write_try(order, name, rerun, tr)
                    ctx.arm()
                except Exception as e:  # noqa: the watchdog is a help, never a reason to stop the step
                    _log(f"order {order}: watchdog not armed: {type(e).__name__}")
            watch = GD.MemWatch().start()
            c0, t0 = time.process_time(), time.time()
            try:
                out = exe(ctx, plan, step, rerun)
            except (Hold, store.Answer, store.StorageError):
                watch.stop()
                raise
            except BaseException as e:
                watch.stop()
                if isinstance(e, Exception):
                    _counted_failure(ctx, plan, step, rerun, tr, e)
                raise
            mem = watch.stop()
            ms = int(round((time.time() - t0) * 1000))
            drift = out.extra.get("drift")
            done = {"v": 1, "step": name, "rerun": int(rerun), "outputs": out.outputs, "ms": ms, "cpu_s": round(time.process_time() - c0, 2),
                    "peak_mb": mem["peak_mb"], "rss_mb": mem["rss_mb"], "hwm_mb": mem["hwm_mb"], "attempt": tr["attempts"],
                    "inputs": out.extra.get("inputs"), "drift": drift, "need_s": secs, "est_mb": mb, "by": ctx.by, "at": _iso(),
                    "result": {kk: out.result.get(kk) for kk in ("key", "width", "height", "bytes", "style", "layout", "count", "needs_review", "existing")}}
            store.put(path(order, f"done_{_safe(name)}{_sfx(rerun)}.json"), _jbytes(done), "application/json", upsert=True, timeout=6.0, retry=False)
            if not (out.extra.get("reused") or out.result.get("existing")):
                # (a step that drew nothing, the legacy composer answering the stored file or an artwork reused after a kill, writes no event, as the
                # legacy composer never did)
                _record(ctx, plan, step, k, of, ms=ms, peak_mb=mem["peak_mb"], hwm_mb=mem["hwm_mb"], need_s=secs, cpu_s=done["cpu_s"],
                        needs_review=bool(out.result.get("needs_review")), kills=tr["kills"],
                        d_rgb=max((d["d_rgb"] for d in (drift or []) if isinstance(d, dict)), default=None))
            if after is not None:
                after(out)
            return {"out": out, "done": done}
    except Hold as h:
        _record(ctx, plan, step, k, of, hold=h.reason, need_s=step.get("need_s"))
        raise


# ----------------------------------------------------------------------------- the order's steps, one call at a time
def bump_rerun(order, by="admin", reason=""):
    """Raise the order's rerun count by one (rerun.json) and return it: the artwork's digest changes with it, so the new file lies beside the delivered
    one and the delivered one is never deleted."""
    cur = store.get_json(path(order, "rerun.json"), timeout=5.0, retry=False)
    n = _rerun_n(cur) + 1
    store.put(path(order, "rerun.json"), store.json_bytes({"n": n, "t": int(time.time()), "iso": _iso(), "by": str(by)[:20], "reason": str(reason)[:120]}),
              "application/json", upsert=True, timeout=6.0, retry=False)
    return n


def restore_rerun(order, delivery):
    """After the style folder was cleaned up (api/_lib/cleanup.py removes it 14 days after delivery.json) the rerun count went with it, and a later admin
    recompose would make the plan again at count 0 and point the delivery back at an older file. The delivered artwork's own record says which rerun it is:
    when there is no rerun.json, write one from it. Returns the count (0 for a first artwork, a legacy artwork or an unreadable record)."""
    key = delivery.get("key") if isinstance(delivery, dict) else None
    if not (isinstance(key, str) and key.endswith(".jpg")):
        return 0
    rec = store.get_json(key[:-4] + ".json", timeout=6.0, retry=False)
    n = rec.get("rerun") if isinstance(rec, dict) else 0
    n = n if isinstance(n, int) and not isinstance(n, bool) and 0 < n <= 1000 else 0
    if n:
        try:
            store.put(path(order, "rerun.json"), store.json_bytes({"n": n, "t": int(time.time()), "iso": _iso(), "by": "restore", "reason": "style folder cleaned up"}),
                      "application/json", upsert=False, timeout=6.0, retry=False)
        except store.StorageExists:
            pass
    return n


def _unchanged(ctx, plan, st):
    """Is every input of the finished art step still what it was (the eyes' masters, the words)? A re-rendered master or a changed line makes a recompose
    a new file; nothing changed makes it the same one."""
    step = plan["steps"][-1]
    done = st["done"].get(step["name"]) or {}
    was = done.get("inputs") if isinstance(done.get("inputs"), dict) else None
    if was is None:
        return False
    recs = _parallel([lambda k=k: store.get_json(k[:-4] + ".json", timeout=5.0, retry=False) for k in _eye_keys(ctx, step)])
    now = _inputs(ctx, plan, recs)
    return was.get("eyes") == now["eyes"] and was.get("words") == now["words"]


def _finished(plan, st):
    """The artwork of an order whose steps are all done (a call after the last done record: the delivery is what is missing), or None when its output
    is not in storage any more (the step is then run again)."""
    done = st["done"].get(plan["steps"][-1]["name"])
    res = dict((done or {}).get("result") or {})
    key = res.get("key")
    if not isinstance(key, str) or not store.exists(key, timeout=6.0, retry=False):
        return None
    res.update(existing=True, url=store.signed_url(key, LINK_SECONDS))
    return res


def _for_delivery(plan, res):
    """The artwork as delivery.json records it: a style of the v3 engine adds the design it was drawn in and the plan's identity (plan8); a legacy
    order's delivery.json is what it always was."""
    out = dict(res)
    if plan.get("family") != "legacy":
        out.update(plan8=plan.get("plan8"), design_used=plan.get("design_used"))
    return out


def _final(plan, st, res, ran, delivery=None):
    return {"final": True, "artwork": res, "progress": {"done": st["of"], "of": st["of"], "step": None}, "delivery": delivery, "ran": ran,
            "plan8": plan.get("plan8"), "design_used": plan.get("design_used")}


def advance(ctx, mode="next"):
    """Do the next missing step of the order's plan; when it was the last, the artwork is handed to ctx.finish (delivery.json) before the call ends.
    mode: "next" (the chain, the order page), "recompose" (the admin: the same file when no input changed, a new one when a master was re-rendered; the
    legacy engine decides that itself), "rerun" (the admin: always a new file; not for the legacy engine). Returns {final, artwork, progress, delivery,
    ran, plan8, design_used}; final is False when more steps remain (the caller asks again). Raises what run_step raises."""
    order = ctx.order
    st = read_state(order)
    plan = st["plan"]
    if plan is None:
        plan = create_plan(ctx)
        st = read_state(order)
        plan = st["plan"] or plan
    if plan.get("style") != ctx.spec.get("style") or plan.get("eyes") != ctx.n:
        # the stored plan is for another style or another number of eyes than the order asks for: never the artwork of another style
        raise Hold("plan_mismatch", f"the order's stored plan is for {plan.get('style')} with {plan.get('eyes')} eye(s), the order asks for "
                   f"{ctx.spec.get('style')} with {ctx.n}")
    legacy = plan.get("family") == "legacy"
    rerun, force = st["rerun"], False
    if mode == "rerun":
        if legacy:
            raise store.Answer(409, "rerun_not_available", "This order is drawn by the legacy engine: re-render an eye and recompose instead.", False)
        check_skew(plan)
        rerun = bump_rerun(order, ctx.by, "rerun")
        st = read_state(order)
    elif mode == "recompose":
        if legacy:
            force = True                 # master_compose answers the same file when nothing changed, a new one when a master did
        elif st["next"] is None and not _unchanged(ctx, plan, st):
            check_skew(plan)
            rerun = bump_rerun(order, ctx.by, "recompose")
            st = read_state(order)
    ran = []
    if st["next"] is None and not force:
        res = _finished(plan, st)
        if res is not None:
            delivery = ctx.finish(_for_delivery(plan, res)) if ctx.finish is not None else None
            return _final(plan, st, res, ran, delivery)
        st["next"] = plan["steps"][-1]["name"]           # the output is gone from storage: draw it again
    name = plan["steps"][-1]["name"] if force else st["next"]
    step = next(s for s in plan["steps"] if s["name"] == name)
    k = plan["steps"].index(step) + 1
    last = k == len(plan["steps"])
    check_skew(plan)
    box = {}

    def after(out):
        if last and ctx.finish is not None:
            box["delivery"] = ctx.finish(_for_delivery(plan, out.result))

    got = run_step(ctx, plan, step, k, rerun, after=after)
    ran.append(name)
    if last:
        return _final(plan, st, dict(got["out"].result), ran, box.get("delivery"))
    st = read_state(order)
    return {"final": False, "artwork": None, "progress": progress(st), "delivery": None, "ran": ran, "plan8": plan.get("plan8"),
            "design_used": plan.get("design_used")}


# ----------------------------------------------------------------------------- the laboratory
def lab_reset(order):
    """Delete the style folder of a LAB test order (never of a paid one): its records, locks and done and try records of every rerun."""
    folder = f"orders/{store.check_order(order)}/{FOLDER}"
    names = ["plan.json", "rerun.json", f"{ART}.lock", f"done_{ART}.json", f"try_{ART}.json"]
    names += [f"done_{ART}_r{i}.json" for i in range(1, 40)] + [f"try_{ART}_r{i}.json" for i in range(1, 40)]
    gone = [f"{folder}/{n}" for n in names if store.exists(f"{folder}/{n}", timeout=5.0, retry=False)]
    if gone:
        store.delete_many(gone)
    return len(gone)


def lab_run(ctx, fresh=False, dry=False):
    """The admin laboratory's master (VE1: stored 4096 px masters as the eyes of a lab test order, no payment, no image model): the same plan, guards,
    claim and executor as a paid order's. fresh: draw again (a new file beside the old). dry: the plan and the capacity only. A lab order's style
    folder belongs to the lab: when the request names another style, layout, option or eye count than the stored plan, it starts again from nothing."""
    if not ctx.lab:
        raise store.Answer(409, "not_lab", "Only a lab test order (lab-...) is run this way.", False)
    st = read_state(ctx.order)
    old, spec = st["plan"], ctx.spec
    if old is not None and (old.get("style"), old.get("layout"), old.get("eyes"), old.get("opts")) != (
            spec.get("style"), spec.get("layout") or CT.default_layout(spec.get("style"), ctx.n), ctx.n, _opts(spec)):
        lab_reset(ctx.order)
        st = read_state(ctx.order)
    if dry:
        plan = st["plan"] or make_plan(spec, _eye_inputs(ctx))
        return {"dry": True, "plan": plan, "capacity": capacity(plan)}
    return advance(ctx, "rerun" if (fresh and st["plan"] is not None) else "next")
