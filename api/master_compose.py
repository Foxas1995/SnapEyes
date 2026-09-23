# -*- coding: utf-8 -*-
"""POST /api/master_compose  {keys: ["orders/<order>/eye_<n>.jpg", ...] 1-8 in canvas order, style, layout,
                              names, title, ticket, order}
The paid deliverable, step 2 of 2: the stored 4096 px eye masters placed on the chosen style at 4096 px on the
longest side (L.compose_multi, no watermark), stored privately as orders/<order>/artwork_<digest>.jpg (JPEG q95
4:4:4, sRGB) and handed out as a signed link valid for 7 days. The digest covers every input, including which
render each eye slot holds, so the same request again returns the stored file without composing it twice, and a
changed names line or a re-rendered eye makes a new file.

ticket: an unlock ticket for THIS order, kind "unlock-<order>" (store.unlock_kind); anything else is a 403.

Reply 200: {ok, url, key, width, height, bytes, style, layout, count, existing, expires_in, seconds, qa,
needs_review, ms}. needs_review is true when an eye's master failed its colour check or a pupil came out tinted.
The file is never returned inline: a 4K JPEG as base64 is 3-4.4 MB, at the 4.5 MB body limit.
Other replies: 503 storage_not_configured (before anything else), 403 without a valid ticket for this order,
400 for bad input or an eye that is not stored for this order, 503 busy_retry when the eyes were loaded too late
to compose inside this invocation, 503 storage_busy when storage did not answer (all retryable)."""
import os, sys, io, re, time, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import BaseHTTPRequestHandler
from PIL import Image
from _lib import iris as L
from _lib import store

SIZE = 4096                  # longest side of the delivered artwork
LINK_SECONDS = 7 * 86400     # the signed download link
MASTER_SIDE = 4096           # what /api/master_eye stores; anything else in an eye slot is not a master
# Seconds the composition needs once the eyes are loaded, on ONE core (Vercel Hobby: 1 vCPU): compose_multi at 4096
# measured on one Ryzen core, times SLOW_CPU for a slower vCPU, plus STORE_RESERVE for the JPEG encode, the upload,
# the record and the link. Below it the request is refused with a retryable 503 before the work starts, because
# compose_multi has no deadline of its own. See _compose_need().
COMPOSE_BASE, COMPOSE_PER_EYE = 10.5, 0.9     # one core, 2026-09-23: 1 eye 6.2-10.5 s (by style), 2 eyes 9.6-12.6 s,
                                              # 4 eyes 11.5-12.4 s, 8 eyes 11.0-16.5 s; one run on a busy core: 20.9 s
SLOW_CPU = 1.6               # a slower or shared vCPU: n=1 needs 21.8 s, n=8 needs 31.9 s of the 52 s budget
STORE_RESERVE = 5.0
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


def _compose_need(n):
    return round(SLOW_CPU * (COMPOSE_BASE + COMPOSE_PER_EYE * (n - 1)) + STORE_RESERVE, 1)


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


def master_compose(body):
    t0 = time.time()
    if not isinstance(body, dict):
        raise L.ClientError("Send a JSON object.")
    order = store.check_order(body.get("order"))
    if not L.check_ticket(body.get("ticket"), kind=store.unlock_kind(order)):
        raise PermissionError("master_compose: unlock ticket missing, expired, of another kind or for another order")
    keys = _keys(body.get("keys"), order)
    n = len(keys)
    style = body.get("style")
    if not isinstance(style, str) or style not in L.STYLES:
        raise L.ClientError("Choose one of the styles: " + ", ".join(L.STYLES) + ".")
    layout = body.get("layout")
    if layout in (None, ""):
        layout = L.multi_layout(n)
    elif not isinstance(layout, str) or layout not in L.layouts_for(n):
        raise L.ClientError(f"{n} eye{'s' if n > 1 else ''} can use: " + ", ".join(L.layouts_for(n)) + ".")
    names, title = _text(body.get("names"), 60), _text(body.get("title"), 40)
    W, H = L.multi_canvas(n, layout, SIZE)
    folder = f"orders/{order}"
    recs = _records(keys)
    eyes_review = any(isinstance(r, dict) and isinstance(r.get("qa"), dict) and r["qa"].get("ok") is False
                      for r in recs.values())
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
    return {"ok": True, "url": url, "key": key, "width": W, "height": H, "bytes": len(data), "style": style,
            "layout": layout, "count": n, "existing": False, "expires_in": LINK_SECONDS,
            "seconds": round(time.time() - t0, 1), "qa": qa, "needs_review": eyes_review or _pupil_failed(qa)}


def handle(req):
    store.serve(req, "master_compose", master_compose)


class handler(BaseHTTPRequestHandler):
    def do_POST(self): handle(self)
