# -*- coding: utf-8 -*-
"""POST /api/master_compose  {keys: ["orders/<order>/eye_<n>.jpg", ...] 1-8 in canvas order, style, layout,
                              names, title, ticket, order}
The paid deliverable, step 2 of 2: the stored 4096 px eye masters placed on the chosen style at 4096 px on the
longest side (L.compose_multi for a style of the legacy engine, no watermark; the step runner of api/_lib/styles/steps.py
for a style of the v3 engine, which has its own plan and digest), stored privately as orders/<order>/artwork_<digest>.jpg
(JPEG q95 4:4:4, sRGB) and handed out as a signed link valid for 7 days. The digest of a legacy style covers every input,
including which render each eye slot holds, so the same request again returns the stored file without composing it twice,
and a changed names line or a re-rendered eye makes a new file. (A paid order's own artwork is made by api/order.py
compose_order through the master plan; this endpoint is what the lab and the admin tools call.)

ticket: an unlock ticket for THIS order, kind "unlock-<order>" (store.unlock_kind); anything else is a 403.

Reply 200: {ok, url, key, width, height, bytes, style, layout, count, existing, expires_in, seconds, qa,
needs_review, ms}. needs_review is true when an eye's master failed its colour check, does not match the preview the
customer approved (its record's preview.ok, see /api/master_eye), or a pupil came out tinted.
The file is never returned inline: a 4K JPEG as base64 is 3-4.4 MB, at the 4.5 MB body limit.
Other replies: 503 storage_not_configured (before anything else), 403 without a valid ticket for this order,
400 for bad input or an eye that is not stored for this order, 503 busy_retry when the eyes were loaded too late
to compose inside this invocation, 503 storage_busy when storage did not answer (all retryable)."""
import os, sys, io, re, time, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import BaseHTTPRequestHandler
from PIL import Image
from _lib import iris as L
from _lib import catalogue
from _lib import store
from _lib import words as WORDS
from _lib import events as E   # the admin panel's usage events (no personal data)
from _lib.styles import costs as CO   # what a master takes, in seconds and megabytes (one table for every engine)
from _lib.styles import steps as SP   # the master plan: a style of the v3 engine is made by its step runner

SIZE = 4096                  # longest side of the delivered artwork
LINK_SECONDS = 7 * 86400     # the signed download link
MASTER_SIDE = 4096           # what /api/master_eye stores; anything else in an eye slot is not a master
# Seconds the composition needs once the eyes are loaded, on ONE core (Vercel Hobby: 1 vCPU): below it the request is refused with a
# retryable 503 before the work starts, because compose_multi has no deadline of its own. The legacy engine's figures (compose_multi at 4096
# measured on one Ryzen core, times STYLE_SLOW_CPU for a slower vCPU, plus a reserve for the JPEG encode, the upload, the record and the link:
# 21.8 s for one eye, 31.9 s for eight) now live with every other design's in api/_lib/styles/costs.py (legacy_need): one table answers "how
# long does this master take" for every engine, and the factor is the one STYLE_SLOW_CPU (measured by the admin action cpu_probe).
COMPOSE_BASE, COMPOSE_PER_EYE, STORE_RESERVE = CO.LEGACY_BASE_S, CO.LEGACY_PER_EYE_S, CO.LEGACY_RESERVE_S
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


def _compose_need(n):
    return CO.legacy_need(n)


def step_need(style, n, layout=None):
    """Seconds a call needs to make the master of n eyes in this style: the legacy engine's own figure, or the step cost of the style's design
    (api/_lib/styles/costs.py). None when the cost table has no row for it."""
    if catalogue.is_legacy(style):
        return CO.legacy_need(n)
    eng = catalogue.engine_for(style, n)
    try:
        return CO.step_need(CO.cost_key(eng), n, side=eng.get("work_side")) if eng else None
    except CO.NoCost:
        return None


def _text(v, n):
    return _CONTROL.sub("", v)[:n].strip() if isinstance(v, str) else ""


def _keys(v, order):
    """1-8 eye keys, each exactly an eye slot of this order (no other path can be read through this endpoint)."""
    if not isinstance(v, list) or not 1 <= len(v) <= L.MULTI_MAX:
        raise L.ClientError(f"Send between 1 and {L.MULTI_MAX} eyes.")
    slot = re.compile(r"^orders/" + re.escape(order) + r"/eye_[1-8]\.jpg$")
    if not all(isinstance(k, str) and slot.fullmatch(k) for k in v):
        raise L.ClientError("Each eye must be one stored for this order.")
    return list(v)


def _records(keys):
    """The record /api/master_eye wrote next to each master, read by its exact key (None when missing)."""
    return {k: store.get_json(k[:-4] + ".json") for k in sorted(set(keys))}


def _pad_of(recs):
    """The pad the masters were cut with. compose_multi takes one r_frac for all eyes; the site always cuts at 1.12,
    and a mismatch is logged, not guessed at."""
    pads = []
    for rec in recs.values():
        try:
            p = float(rec.get("pad")) if rec else None
        except (ValueError, TypeError):
            p = None
        pads.append(p if p is not None and 1.0 <= p <= 2.0 else None)
    known = [p for p in pads if p is not None]
    if len(set(known)) > 1:
        print(f"snapeyes master_compose: eyes were cut with different pads {pads}; using {known[0]}", flush=True)
    return known[0] if known else 1.12


def _pupil_failed(qa):
    """The composition's own check measures the pupil of each graded eye; only a measured failure counts (a
    pupil that was not found is no verdict)."""
    if not isinstance(qa, dict):
        return False
    if isinstance(qa.get("eyes"), list):
        return any(_pupil_failed(q) for q in qa["eyes"])
    return qa.get("pupil_neutral") is False


def _identity(rec):
    """Which render a slot holds: a re-render rewrites the record, so the artwork digest changes with it."""
    if not rec:
        return "no-record"
    return f"{rec.get('created')}|{rec.get('bytes')}|{rec.get('kept') or ''}"


def _load(key):
    raw = store.get(key)
    if raw is None:
        raise L.ClientError("An eye of this order is not stored yet.")
    im = Image.open(io.BytesIO(raw))
    if im.size != (MASTER_SIDE, MASTER_SIDE):
        raise RuntimeError(f"{key} is {im.size[0]}x{im.size[1]}, not a {MASTER_SIDE} px master")
    return im.convert("RGB")


def _master_engine(order, keys, style, layout, names, title, date, t0):
    """A style of the v3 engine asked of this endpoint (the lab, the admin tools): the same plan, guards, claim and executor as a paid order's
    (api/_lib/styles/steps.py), run once for these eyes. A step that must be held answers 409 step_held with the owner's sentence."""
    n = len(keys)
    spec = {"eyes": n, "style": style, "layout": layout, "names": names, "title": title, "date": date if isinstance(date, str) else ""}
    lab = order.startswith("lab-")
    ctx = SP.Ctx(order, spec, by="lab" if lab else "api", lab=lab, eyes_from="master", arrival_left=L.time_left())
    try:
        # a lab test order's style folder belongs to the lab (another style starts again from nothing); any other order has ONE plan: a request for
        # another style than its plan's is a hold (plan_mismatch), never the artwork of the other style
        got = SP.lab_run(ctx) if lab else SP.advance(ctx)
    except SP.Hold as h:
        raise store.Answer(409, "step_held", h.note, False, None, hold=h.reason) from h
    r = got["artwork"] or {}
    return {"ok": True, "url": r.get("url"), "key": r.get("key"), "width": r.get("width"), "height": r.get("height"), "bytes": r.get("bytes"),
            "style": style, "layout": layout, "count": n, "existing": bool(r.get("existing")), "expires_in": SP.LINK_SECONDS,
            "seconds": round(time.time() - t0, 1), "qa": r.get("qa"), "needs_review": bool(r.get("needs_review")), "plan8": got.get("plan8"),
            "design_used": got.get("design_used"), "final": bool(got["final"])}


def master_compose(body):
    t0 = time.time()
    if not isinstance(body, dict):
        raise L.ClientError("Send a JSON object.")
    order = store.check_order(body.get("order"))
    if not L.check_ticket(body.get("ticket"), kind=store.unlock_kind(order)):
        raise L.UnlockError("master_compose: unlock ticket missing, expired, of another kind or for another order")
    keys = _keys(body.get("keys"), order)
    n = len(keys)
    style = body.get("style")
    # the render path ignores stages (an order already paid for a style rolled back still renders); it needs a built engine. A style of the v3
    # engine is made by the master plan's step runner (_master_engine), never by L.compose_multi, which reads an id it does not know as the
    # default style
    renderable = catalogue.renderable_ids(n)
    if not isinstance(style, str) or style not in renderable:
        raise L.ClientError("Choose one of the styles: " + ", ".join(renderable) + ".")
    layout = body.get("layout")
    layouts = catalogue.layouts_for(style, n)
    if layout in (None, ""):
        layout = layouts[0]
    elif not isinstance(layout, str) or layout not in layouts:
        raise L.ClientError(f"{n} eye{'s' if n > 1 else ''} can use: " + ", ".join(layouts) + ".")
    names, title = WORDS.names_wire(body.get("names")), _text(body.get("title"), 40)       # a list of names (the order's spec) is joined as the legacy engine reads it; 200 in all
    if not catalogue.is_legacy(style):
        return _master_engine(order, keys, style, layout, names, title, body.get("date"), t0)
    W, H = L.multi_canvas(n, layout, SIZE)
    folder = f"orders/{order}"
    recs = _records(keys)
    eyes_review = any(store.needs_review(r) for r in recs.values())
    spec = {"keys": keys, "style": style, "layout": layout, "names": names, "title": title, "size": SIZE}
    ident = dict(spec, eyes=[_identity(recs[k]) for k in keys])
    digest = hashlib.sha256(json.dumps(ident, sort_keys=True, ensure_ascii=True).encode()).hexdigest()[:16]
    key = f"{folder}/artwork_{digest}.jpg"
    if store.exists(key):
        art = store.get_json(key[:-4] + ".json") or {}
        url = store.signed_url(key, LINK_SECONDS)
        print(f"snapeyes master_compose: {key} already stored, link re-signed", flush=True)
        qa = art.get("qa")
        return {"ok": True, "url": url, "key": key, "width": W, "height": H, "bytes": art.get("bytes"), "style": style,
                "layout": layout, "count": n, "existing": True, "expires_in": LINK_SECONDS,
                "seconds": round(time.time() - t0, 1), "qa": qa,
                "needs_review": eyes_review or _pupil_failed(qa)}
    pad = _pad_of(recs)
    t1 = time.time()
    ims = [_load(k) for k in keys]            # each by its exact key; a missing one is the customer's 400
    t2 = time.time()
    need = _compose_need(n)
    if L.time_left() < need:
        print(f"snapeyes master_compose not composed: {L.time_left():.1f} s left after loading {n} eyes, "
              f"{need:.1f} s needed", flush=True)
        raise store.busy("busy_retry", 5, "We are busy for a moment. Please try again now.")
    keep = {}
    out = L.compose_multi(ims, style=style, names=names, title=title or None, watermark=False,
                          r_frac=L.iris_radius_frac(pad), size=SIZE, layout=layout, keep=keep)
    del ims
    t3 = time.time()
    if out.size != (W, H):
        raise RuntimeError(f"master_compose: canvas came out {out.size}, expected {(W, H)}")
    graded = keep.pop("graded", None)
    if isinstance(graded, list):
        eyes = [L.colour_qa(f"master_compose {folder} eye {i + 1}/{n}", graded=g) for i, g in enumerate(graded)]
        qa = {"ok": all(q["ok"] for q in eyes), "eyes": eyes}
    else:
        qa = L.colour_qa(f"master_compose {folder}", graded=graded)
    del graded
    data = store.jpeg_bytes(out, 95)
    del out
    t4 = time.time()
    store.put(key, data, "image/jpeg", upsert=True)
    record = dict(ident, pad=pad, width=W, height=H, bytes=len(data), qa=qa,
                  created=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    try:
        store.put(key[:-4] + ".json", store.json_bytes(record), "application/json", upsert=True)
    except store.StorageError as e:
        print("snapeyes master_compose record not stored:", L._scrub(str(e))[:200], flush=True)
    url = store.signed_url(key, LINK_SECONDS)
    t5 = time.time()
    # the link is a bearer credential: it goes to the customer only, never into a log line
    print(f"snapeyes master_compose: {key} {W}x{H} {n} eye(s) {style}/{layout} bytes {len(data)} load {t2 - t1:.1f} s "
          f"compose {t3 - t2:.1f} s encode {t4 - t3:.1f} s store+sign {t5 - t4:.1f} s total {t5 - t0:.1f} s", flush=True)
    E.record("master", step="compose", order=order, count=n, style=style, needs_review=eyes_review or _pupil_failed(qa), existing=False)
    return {"ok": True, "url": url, "key": key, "width": W, "height": H, "bytes": len(data), "style": style,
            "layout": layout, "count": n, "existing": False, "expires_in": LINK_SECONDS,
            "seconds": round(time.time() - t0, 1), "qa": qa, "needs_review": eyes_review or _pupil_failed(qa)}


def handle(req):
    store.serve(req, "master_compose", master_compose)


class handler(BaseHTTPRequestHandler):
    def do_POST(self): handle(self)
