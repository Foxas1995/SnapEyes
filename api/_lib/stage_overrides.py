# -*- coding: utf-8 -*-
"""The owner's stage override of the style catalogue (work package WP13a): the object in private storage, the run-time read path that
catalogue.stage_of uses, the checks a style must pass before the owner makes it orderable, the change itself, the audit log of every change.

What a stage is (api/_lib/styles_registry.py): the literal of the registry is the CEILING of a style, a reviewed code change. The EFFECTIVE stage
is the lower of the ceiling and the owner's override, which is set in the admin page, needs no deploy, and can lower a style (take it back to
preview or lab) or restore it up to the ceiling, never above. An override above the ceiling is refused by the admin action AND ignored by the
reader (effective_stage), so a hand-edited file cannot raise a style either. A style becomes `live` (orderable) only after the owner has
recorded his own look at its final renders (check L1) and the independent score of the art director (L0: mean at least L0_MEAN and no axis below
L0_AXIS, with the scorer's name; a score below the bar is recorded and shown, and does not count) or his written waiver of it: the action refuses
`live` otherwise. L0 has no bare tick: it is recorded with its evidence (a score), or waived in words. Ordering itself is a different switch (pay.ordering_problem), closed until the owner opens it.

THE OBJECT: ONE file, ops/styles/overrides.json (the override of every id; its single writer is the admin action styles_override, which holds a
lock, checks the revision number the page saw, and clears the cache on this instance):

    {"v": 1, "rev": 7, "at": "<iso>",
     "styles": {"<id>": {"stage_by_eyes": {"1": "preview"},            the override per eye count (a count that is missing has none)
                         "checklist": {"1": {"L0": {"ticked_at", "by", "score"?}, "L1": {"ticked_at", "by"}, ...}},      L0 to L11 per eye count
                         "waiver": {"1": {"at", "by", "text"}},         the owner's written waiver of L0 for that count
                         "by": "<admin key kind>", "at": "<iso>", "reason": "<text>", "reason_kind": "quality"}},
     "limits": {"min_n", "error_rate", "review_rate", "gate_fail_rate"}}   what the attention card of the Stiliai page compares with

The state is kept per eye count (not per range) so that a later change of the registry's ranges never orphans a tick; the page groups equal
neighbours. A tick is dated and attributed (the admin key's kind: there is one owner).

THE READ PATH. stage_of is asked on every compose, every checkout and every catalogue request, many times per request (every tile of every
style), so it cannot read one object per id: source(style_id, n) reads the one object through a cache of TTL_S (30) seconds. A refresh that fails
is remembered for ERR_TTL_S (5) seconds, so a storage that does not answer costs one slow call and not thirty. FAILING CLOSED, where money is
involved: a storage error is never read as "no override". catalogue.orderable and orderable_ids are strict: they raise StorageError (the
checkout answers 503 storage_busy, nothing is created). The picker, the tile list, the public catalogue and GET /api/checkout use stage_of
without strict: they fall back to the ceiling capped at preview, never live. Not configured at all (no storage on this deployment, a test, the
dev server) is not an error: there is nothing to override and nothing can be ordered. An unreadable FILE (not JSON, another version) is a storage
error; an unreadable ENTRY (a stage that is not one) reads as `lab`: closed, never open.

This instance sees an admin change at once, the others within TTL_S seconds. The cache holds no secret and no personal data.

THE AUDIT LOG: ops/styles/audit/<YYYY-MM-DD>/<HHMMSSmmm>-<rand>.json, one entry per change (upsert False, so an entry is never overwritten): who
(the key's kind), what (style, eye counts, the override before and after, the ceiling), why (the owner's reason and its kind), the ticks that
changed, the set-level gate numbers of the count at that moment (with n), the price test that was running (the flip changes its sample),
whether the owner had read that line, what he chose for the orders in flight, and how many were held. The generic admin audit
(ops/audit, action styles_override) carries the same change in one short line; this one is the record. Module rule: from __future__ import
annotations (Vercel's default Python is 3.12)."""
from __future__ import annotations

import copy
import json
import re
import secrets
import threading
import time

from . import catalogue as CT
from . import iris as L
from . import store

PATH = "ops/styles/overrides.json"
AUDIT_DIR = "ops/styles/audit"
VERSION = 1
TTL_S = 30.0                     # seconds an instance keeps what it read
ERR_TTL_S = 5.0                  # a failed read is remembered this long
READ_TIMEOUT_S = 3.0
MAX_BYTES = 256 << 10            # the object is read back with this ceiling (it holds at most 28 ids x 8 counts of small records)
CHECKS = tuple(f"L{i}" for i in range(12))        # L0 to L11 of spec 4.1: each a tick of the owner, dated and attributed
SETTABLE = ("lab", "preview", "live")             # what the owner can set; restore removes the override
REASON_KINDS = ("quality", "capacity", "soon", "other")
IN_FLIGHT = ("finish", "hold")
REASON_MAX = 200
WAIVER_MIN, WAIVER_MAX = 8, 300
L0_MEAN, L0_AXIS = 3.96, 3.80     # the bar of the independent score (spec 1.6.1): mean at least this, no axis below that; below it only the written waiver counts
LIMITS_DEFAULT = {"min_n": 20, "error_rate": 0.05, "review_rate": 0.10, "gate_fail_rate": 0.60}
LIMIT_KEYS = tuple(LIMITS_DEFAULT)

_EMAIL_LIKE = re.compile(r"[^\s@]+@[^\s@]+")
_CTRL = re.compile(r"[\x00-\x1f\x7f]")
_RANGE = re.compile(r"^([1-8])(?:-([1-8]))?$")

_now = time.monotonic            # the cache's clock (a test moves it)
_LOCK = threading.Lock()
_WRITE_LOCK = threading.Lock()
_READ_LOCK = threading.Lock()      # one storage read of the object at a time (load)
_CACHE = {"obj": None, "t": 0.0, "err": None, "err_t": 0.0}


class StageStoreError(store.StorageError):
    """The owner's overrides could not be read (storage down, the file is not what this code wrote). catalogue.orderable lets it out (503
    storage_busy at checkout); stage_of without strict falls back to the ceiling capped at preview."""


# ----------------------------------------------------------------------------- the object
def empty():
    return {"v": VERSION, "rev": 0, "at": None, "styles": {}, "limits": dict(LIMITS_DEFAULT)}


def _text(v, n):
    s = _CTRL.sub(" ", str(v if v is not None else ""))
    s = _EMAIL_LIKE.sub("[email]", " ".join(s.split()))
    return s[:n]


def _iso(t=None):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() if t is None else t))


def _count_key(k):
    return k if isinstance(k, str) and re.fullmatch(r"[1-8]", k) else None


def _mark(rec):
    """A tick record as stored: {ticked_at, by, score?, director?}; anything else is dropped."""
    if not isinstance(rec, dict) or not isinstance(rec.get("ticked_at"), str):
        return None
    out = {"ticked_at": _text(rec["ticked_at"], 24), "by": _text(rec.get("by"), 40)}
    sc = rec.get("score")
    if isinstance(sc, dict):
        nums = {k: round(float(sc[k]), 3) for k in ("mean", "min_axis") if isinstance(sc.get(k), (int, float)) and not isinstance(sc.get(k), bool)
                and abs(sc[k]) < 100}
        if nums:
            out["score"] = nums
    if isinstance(rec.get("director"), str) and rec["director"].strip():
        out["director"] = _text(rec["director"], 80)
    return out


def _norm_style(sid, rec):
    """One style's record as normalized. A stage that is not one reads as `lab` (closed); an entry of no count is dropped."""
    if not isinstance(rec, dict):
        return None
    stages = {}
    for k, v in (rec.get("stage_by_eyes") if isinstance(rec.get("stage_by_eyes"), dict) else {}).items():
        if _count_key(k):
            stages[k] = v if v in SETTABLE else "lab"
    checklist = {}
    for k, row in (rec.get("checklist") if isinstance(rec.get("checklist"), dict) else {}).items():
        if _count_key(k) and isinstance(row, dict):
            marks = {c: m for c, m in ((c, _mark(row.get(c))) for c in CHECKS) if m}
            if marks:
                checklist[k] = marks
    waiver = {}
    for k, w in (rec.get("waiver") if isinstance(rec.get("waiver"), dict) else {}).items():
        if _count_key(k) and isinstance(w, dict) and isinstance(w.get("text"), str) and w["text"].strip():
            waiver[k] = {"at": _text(w.get("at"), 24), "by": _text(w.get("by"), 40), "text": _text(w["text"], WAIVER_MAX)}
    if not (stages or checklist or waiver):
        return None
    return {"stage_by_eyes": stages, "checklist": checklist, "waiver": waiver, "by": _text(rec.get("by"), 40), "at": _text(rec.get("at"), 24),
            "reason": _text(rec.get("reason"), REASON_MAX),
            "reason_kind": rec.get("reason_kind") if rec.get("reason_kind") in REASON_KINDS else "other"}


def _limit_ok(k, v):
    """A limit as the attention card takes it: min_n a whole number from 0 to 10000, the others a share from 0 to 1."""
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v != v:
        return False
    if k == "min_n":
        return float(v).is_integer() and 0 <= v <= 10000
    return 0 <= v <= 1


def _norm_limits(raw):
    out = dict(LIMITS_DEFAULT)
    for k in LIMIT_KEYS:
        v = (raw or {}).get(k) if isinstance(raw, dict) else None
        if _limit_ok(k, v):
            out[k] = int(v) if k == "min_n" else round(float(v), 4)
    return out


def normalize(obj):
    """The object as this code reads it (a fresh dict). Raises StageStoreError for a file that is not an object of this version."""
    if not isinstance(obj, dict) or obj.get("v") != VERSION:
        raise StageStoreError("overrides: not an object of version 1")
    styles = {}
    for sid, rec in (obj.get("styles") if isinstance(obj.get("styles"), dict) else {}).items():
        if CT.known(sid):
            n = _norm_style(sid, rec)
            if n:
                styles[sid] = n
    rev = obj.get("rev")
    return {"v": VERSION, "rev": rev if isinstance(rev, int) and not isinstance(rev, bool) and rev >= 0 else 0, "at": _text(obj.get("at"), 24) or None,
            "styles": styles, "limits": _norm_limits(obj.get("limits"))}


def _parse(raw):
    if raw is None:
        return empty()
    try:
        obj = json.loads(raw)
    except ValueError:
        raise StageStoreError("overrides: not JSON") from None
    return normalize(obj)


# ----------------------------------------------------------------------------- the read path
def invalidate():
    with _LOCK:
        _CACHE.update(obj=None, t=0.0, err=None, err_t=0.0)


def _remember(obj):
    with _LOCK:
        _CACHE.update(obj=obj, t=_now(), err=None, err_t=0.0)


def _cached():
    """The cached object, or raises the remembered failure, or None when a read is due. Under _LOCK."""
    now = _now()
    if _CACHE["obj"] is not None and now - _CACHE["t"] < TTL_S:
        return _CACHE["obj"]
    if _CACHE["err"] is not None and now - _CACHE["err_t"] < ERR_TTL_S:
        raise StageStoreError(_CACHE["err"])
    return None


def load(force=False, timeout=READ_TIMEOUT_S):
    """The normalized object (a shared dict: copy it before changing it). force: read now. A deployment without storage has none (the empty one).
    Raises StageStoreError when the storage or the file cannot be read; a failure is remembered for ERR_TTL_S seconds, except a request's own lack of
    time (that says nothing about the storage, and must not close the page for everyone else). One read at a time per instance: the threads that find the
    cache expired wait for the one that reads and then use its answer (a stampede of 40 asks is one storage call, not 40)."""
    if not store.configured():
        return empty()
    if not force:
        with _LOCK:
            hit = _cached()
        if hit is not None:
            return hit
    # the wait for the thread that reads is bounded by this request's own time (it never costs more than one read)
    if not _READ_LOCK.acquire(timeout=max(0.0, min(timeout + 0.5, store.time_left() - store.MIN_LEFT))):
        raise StageStoreError("overrides: out of time")
    try:
        if not force:
            with _LOCK:
                hit = _cached()          # the thread that held the lock before has read it (or failed): its answer stands
            if hit is not None:
                return hit
        if store.time_left() < store.MIN_LEFT:      # the request is out of time: no storage call can start, and nothing is remembered of it
            raise StageStoreError("overrides: out of time")
        try:
            obj = _parse(store.get(PATH, max_bytes=MAX_BYTES, timeout=timeout, retry=False))
        except Exception as e:  # noqa: whatever it was, the answer is "unreadable", never "no override"
            msg = str(e) if isinstance(e, StageStoreError) else f"overrides not read ({type(e).__name__})"
            if "out of time" not in str(e):         # (store._call's own refusal for want of time, or ours)
                with _LOCK:
                    _CACHE.update(obj=None, t=0.0, err=msg, err_t=_now())
            print(f"snapeyes styles: {msg}", flush=True)
            raise (e if isinstance(e, StageStoreError) else StageStoreError(msg)) from None
        _remember(obj)
        return obj
    finally:
        _READ_LOCK.release()


def source(style_id, n):
    """The override stage for this style and eye count (preview, lab or live), or None when the owner set none. catalogue.stage_of reads it."""
    rec = load()["styles"].get(style_id)
    return rec["stage_by_eyes"].get(str(n)) if rec else None


def save(obj):
    """Write the object (the admin action's, under its lock) and make this instance see it at once. The revision goes up by one."""
    new = dict(obj, v=VERSION, rev=int(obj.get("rev") or 0) + 1, at=_iso())
    store.put(PATH, store.json_bytes(new), "application/json", upsert=True, timeout=8.0)
    norm = normalize(new)
    _remember(norm)
    return norm


# ----------------------------------------------------------------------------- the request
def _counts(v, lo, hi):
    """Eye counts of a request: 3, [3, 4], "4-8" or "3" (inside the style's range)."""
    if isinstance(v, bool) or v is None:
        raise L.ClientError("eyes is a number, a list of numbers or a range like 4-8.")
    if isinstance(v, int):
        out = [v]
    elif isinstance(v, str):
        m = _RANGE.fullmatch(v.strip())
        if not m:
            raise L.ClientError("eyes is a number, a list of numbers or a range like 4-8.")
        a, b = int(m.group(1)), int(m.group(2) or m.group(1))
        out = list(range(min(a, b), max(a, b) + 1))
    elif isinstance(v, list) and 1 <= len(v) <= 8 and all(isinstance(x, int) and not isinstance(x, bool) for x in v):
        out = sorted(set(v))
    else:
        raise L.ClientError("eyes is a number, a list of numbers or a range like 4-8.")
    if not out or any(not lo <= n <= hi for n in out):
        raise L.ClientError(f"This style takes {lo} to {hi} eyes.")
    return out


def parse(body):
    """The checked request of styles_override (L.ClientError, a 400, for what is malformed): {style, counts, stage, ticks, evidence, waiver,
    reason, reason_kind, in_flight, price_test_seen, rev, confirm}. stage None: only the ticks or the waiver change."""
    if not isinstance(body, dict):
        raise L.ClientError("Send a JSON object.")
    sid = body.get("style")
    if not CT.known(sid):
        raise L.ClientError("Not a style of the catalogue.")
    lo, hi = CT.eyes_range(sid)
    counts = _counts(body.get("eyes"), lo, hi)
    stage = body.get("stage")
    if stage is not None and stage not in SETTABLE + ("restore",):
        raise L.ClientError("stage is lab, preview, live or restore.")
    ticks = body.get("tick")
    if ticks is None:
        ticks = {}
    if not isinstance(ticks, dict) or not all(k in CHECKS and isinstance(v, bool) for k, v in ticks.items()):
        raise L.ClientError("tick is an object of L0 to L11 with true or false.")
    if ticks.get("L0") is True:
        raise L.ClientError("L0 is not ticked: it is the independent score. Send evidence {L0: {mean, min_axis, by}}, or the waiver {text} in your own words.")
    evidence = body.get("evidence")
    if evidence is None:
        evidence = {}
    if not isinstance(evidence, dict) or set(evidence) - {"L0"}:
        raise L.ClientError("evidence holds the score of L0: {L0: {mean, min_axis, by}}.")
    ev0 = evidence.get("L0")
    if ev0 is not None:
        if not isinstance(ev0, dict) or not ev0 or set(ev0) - {"mean", "min_axis", "by"}:
            raise L.ClientError("The score of L0 is {mean, min_axis, by}.")
        for k in ("mean", "min_axis"):
            v = ev0.get(k)
            if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= 5):
                raise L.ClientError("A score is a number from 0 to 5.")
        if ev0.get("by") is not None and not isinstance(ev0["by"], str):
            raise L.ClientError("The scorer's name is text.")
    waiver = body.get("waiver", None)
    waiver_text = None
    if waiver is not None and waiver is not False:
        t = waiver.get("text") if isinstance(waiver, dict) else None
        if not isinstance(t, str) or not WAIVER_MIN <= len(_text(t, 10_000)) <= WAIVER_MAX:
            raise L.ClientError(f"The waiver is {{text}}: your own words, {WAIVER_MIN} to {WAIVER_MAX} characters.")
        waiver_text = _text(t, WAIVER_MAX)
    reason = body.get("reason")
    if reason is not None and not isinstance(reason, str):
        raise L.ClientError("reason is text.")
    kind = body.get("reason_kind", "other")
    if kind not in REASON_KINDS:
        raise L.ClientError("reason_kind is quality, capacity, soon or other.")
    in_flight = body.get("in_flight")
    if in_flight is not None and in_flight not in IN_FLIGHT:
        raise L.ClientError("in_flight is finish or hold.")
    rev = body.get("rev")
    if rev is not None and (isinstance(rev, bool) or not isinstance(rev, int) or rev < 0):
        raise L.ClientError("rev is the revision the page was shown.")
    if stage is None and not ticks and ev0 is None and waiver is None:
        raise L.ClientError("Nothing to change: send a stage, a tick or a waiver.")
    return {"style": sid, "counts": counts, "stage": stage, "ticks": ticks, "evidence": ev0, "waiver": waiver_text,
            "waiver_remove": waiver is False, "reason": _text(reason, REASON_MAX), "reason_kind": kind, "in_flight": in_flight,
            "price_test_seen": body.get("price_test_seen") is True, "rev": rev, "confirm": body.get("confirm") is True}


# ----------------------------------------------------------------------------- the change
def l0_state(rec, n):
    """What L0 stands at for one eye count: "pass" (a score with both numbers, mean at least L0_MEAN, no axis below L0_AXIS, and the scorer's name),
    "below_bar" (a score under the bar: recorded and shown, and it does not count), "incomplete" (an L0 mark without both numbers or without the scorer's
    name), "waiver" (no passing score, but the owner's written waiver of it), or None (neither). Spec 1.6.1: below the bar only the waiver counts."""
    k = str(n)
    mark = (((rec or {}).get("checklist") or {}).get(k) or {}).get("L0")
    state = None
    if mark:
        sc = mark.get("score") or {}
        mean, axis = sc.get("mean"), sc.get("min_axis")
        if mean is None or axis is None or not mark.get("director"):
            state = "incomplete"
        elif mean >= L0_MEAN and axis >= L0_AXIS:
            return "pass"
        else:
            state = "below_bar"
    if k in ((rec or {}).get("waiver") or {}):
        return "waiver"
    return state


def missing_for_live(rec, n):
    """What a count still lacks before the owner may make it live: [] or the codes L1 and L0 (L0 is met by a passing score with the scorer's name, or by a
    written waiver: l0_state; a score below the bar does not meet it)."""
    marks = (((rec or {}).get("checklist") or {}).get(str(n))) or {}
    out = []
    if "L1" not in marks:
        out.append("L1")
    if l0_state(rec, n) not in ("pass", "waiver"):
        out.append("L0")
    return out


def can_live(rec, n):
    return not missing_for_live(rec, n)


def transition(obj, req, who_kind, now=None):
    """Apply a checked request to the object: (new object, report). The object is not changed. Refusals are store.Answer (409): the style has no engine
    to switch (planned) or is retired, a stage above the ceiling, `live` without the ticks. report: {before, after, ceiling, effective_before,
    effective_after, ticked, unticked, waiver, changed}: per eye count where it is a map."""
    sid, counts, stage = req["style"], req["counts"], req["stage"]
    iso = _iso(now)
    new = copy.deepcopy(obj)
    rec = new["styles"].get(sid) or {"stage_by_eyes": {}, "checklist": {}, "waiver": {}, "by": "", "at": "", "reason": "", "reason_kind": "other"}
    ceilings = {n: CT.ceiling(sid, n) for n in counts}
    for n, c in ceilings.items():
        if c in ("planned", "retired"):
            raise store.Answer(409, "not_switchable", "A style that is planned has no engine to switch, and a retired one is final: that is a change of the "
                               "registry, not of this page.", False, eyes=n, ceiling=c)
    if stage in SETTABLE:
        over = {n: c for n, c in ceilings.items() if CT.STAGE_RANK[stage] > CT.STAGE_RANK[c]}
        if over:
            raise store.Answer(409, "above_ceiling", "The ceiling of the registry is lower than that: only a reviewed change of the code raises it.", False,
                               ceiling={str(n): c for n, c in ceilings.items()}, above=sorted(over))
    before = {str(n): rec["stage_by_eyes"].get(str(n)) for n in counts}
    eff_before = {str(n): CT.stage_with(sid, n, rec["stage_by_eyes"].get(str(n)), ceilings[n]) for n in counts}
    ticked, unticked = [], []
    for n in counts:
        k = str(n)
        marks = rec["checklist"].setdefault(k, {})
        for code, on in req["ticks"].items():
            if on and code not in marks:
                marks[code] = {"ticked_at": iso, "by": who_kind}
                ticked.append(f"{code}@{n}")
            elif not on and code in marks:
                del marks[code]
                unticked.append(f"{code}@{n}")
        if req["evidence"] is not None:
            m = dict(marks.get("L0") or {"ticked_at": iso, "by": who_kind})
            ev = req["evidence"]
            sc = {k2: round(float(ev[k2]), 3) for k2 in ("mean", "min_axis") if ev.get(k2) is not None}
            if sc:
                m["score"] = {**(m.get("score") or {}), **sc}           # one number can be corrected without sending the other again
            if isinstance(ev.get("by"), str) and ev["by"].strip():
                m["director"] = _text(ev["by"], 80)
            if "L0" not in marks:
                ticked.append(f"L0@{n}")
            marks["L0"] = m
        if not marks:
            rec["checklist"].pop(k, None)
        if req["waiver"] is not None:
            rec["waiver"][k] = {"at": iso, "by": who_kind, "text": req["waiver"]}
        elif req["waiver_remove"]:
            rec["waiver"].pop(k, None)
    if stage == "live":
        built = CT.renderable(sid)
        if not built:
            raise store.Answer(409, "no_engine", "This deployment has no engine for this style.", False)
        lacking = {str(n): missing_for_live(rec, n) for n in counts if missing_for_live(rec, n)}
        if lacking:
            raise store.Answer(409, "needs_ticks", "Live needs your own look at the final renders (L1) and the independent score (L0: at least "
                               f"{L0_MEAN} on average and no axis under {L0_AXIS}) or your written waiver of it, for every eye count asked for.", False, missing=lacking,
                               l0={str(n): l0_state(rec, n) for n in counts})
    for n in counts:
        k = str(n)
        if stage == "restore":
            rec["stage_by_eyes"].pop(k, None)
        elif stage in SETTABLE:
            rec["stage_by_eyes"][k] = stage
    after = {str(n): rec["stage_by_eyes"].get(str(n)) for n in counts}
    eff_after = {str(n): CT.stage_with(sid, n, rec["stage_by_eyes"].get(str(n)), ceilings[n]) for n in counts}
    if stage is not None or req["ticks"] or req["evidence"] is not None or req["waiver"] is not None or req["waiver_remove"]:
        rec["by"], rec["at"] = who_kind, iso
        if stage is not None:
            rec["reason"], rec["reason_kind"] = req["reason"], req["reason_kind"]
    if rec["stage_by_eyes"] or rec["checklist"] or rec["waiver"]:
        new["styles"][sid] = rec
    else:
        new["styles"].pop(sid, None)
    same = json.dumps(_strip(new.get("styles")), sort_keys=True) == json.dumps(_strip(obj.get("styles")), sort_keys=True)
    return new, {"before": before, "after": after, "ceiling": {str(n): c for n, c in ceilings.items()}, "effective_before": eff_before,
                 "effective_after": eff_after, "ticked": ticked, "unticked": unticked,
                 "waiver": "set" if req["waiver"] is not None else ("removed" if req["waiver_remove"] else None), "changed": not same,
                 "l0": {str(n): l0_state(new["styles"].get(sid), n) for n in counts}}


def _strip(styles):
    """The part of the styles that a change is judged by (what is stored but who and when): the stages, the waivers' words, which checks are ticked and what
    evidence (the score, the scorer) a tick carries. A tick again, with the same evidence, is no change."""
    out = {}
    for sid, rec in (styles or {}).items():
        out[sid] = {"stage_by_eyes": rec.get("stage_by_eyes"), "waiver": {k: v.get("text") for k, v in (rec.get("waiver") or {}).items()},
                    "checklist": {k: {c: {f: x for f, x in m.items() if f not in ("ticked_at", "by")} for c, m in v.items()} for k, v in (rec.get("checklist") or {}).items()}}
    return out


def set_limits(obj, limits):
    """A copy of the object with the attention card's limits changed (L.ClientError for a bad value)."""
    if not isinstance(limits, dict) or not limits or set(limits) - set(LIMIT_KEYS):
        raise L.ClientError("limits holds " + ", ".join(LIMIT_KEYS) + ".")
    new = copy.deepcopy(obj)
    for k, v in limits.items():
        if not _limit_ok(k, v):
            raise L.ClientError(f"{k} is " + ("a whole number from 0 to 10000." if k == "min_n" else "a share from 0 to 1."))
        new["limits"][k] = int(v) if k == "min_n" else round(float(v), 4)
    return new


# ----------------------------------------------------------------------------- the audit log
def audit_put(entry, now=None):
    """One audit entry (never overwrites). Returns the path, or None when it could not be written (the change itself stands)."""
    now = time.time() if now is None else now
    g = time.gmtime(now)
    e = dict(entry, v=1, t=round(now, 3), iso=_iso(now))
    # the name sorts by time down to the millisecond, so that "newest first" is the order of the names (two changes in one second keep their order)
    path = f"{AUDIT_DIR}/{time.strftime('%Y-%m-%d', g)}/{time.strftime('%H%M%S', g)}{int((now % 1) * 1000):03d}-{secrets.token_hex(4)}.json"
    try:
        store.put(path, store.json_bytes(e), "application/json", upsert=False, timeout=5.0, retry=False)
        return path
    except Exception as ex:  # noqa: the change is done; its log line must not undo it
        print(f"snapeyes styles: audit entry not written ({type(ex).__name__})", flush=True)
        return None


def audit_read(limit=100, days=60, style=None, now=None):
    """The audit entries, newest first: at most `limit`, looking back `days` UTC days (stops when the invocation runs short of time)."""
    now = time.time() if now is None else now
    out = []
    first = time.strftime("%Y-%m-%d", time.gmtime(now - days * 86400))
    # the days that HAVE entries (one listing of the folder), newest first: not one request per day of the look back
    present = sorted((r["name"] for r in store.list_all(AUDIT_DIR) if r["folder"] and re.fullmatch(r"\d{4}-\d\d-\d\d", r["name"]) and r["name"] >= first), reverse=True)
    for d in present:
        if len(out) >= limit or L.time_left() < 8:
            break
        names = sorted((r["name"] for r in store.list_all(f"{AUDIT_DIR}/{d}") if not r["folder"] and r["name"].endswith(".json")), reverse=True)
        for nm in names:
            if len(out) >= limit or L.time_left() < 8:
                break
            e = store.get_json(f"{AUDIT_DIR}/{d}/{nm}", timeout=6.0)
            if isinstance(e, dict) and (style is None or e.get("style") == style):
                out.append(e)
    return out
