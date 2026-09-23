# -*- coding: utf-8 -*-
"""POST /api/master_eye  {crop: b64 (the deglared iris square the preview used), pad, ticket, order, eye: 1-8,
                          rerender: true (optional)}
The paid deliverable, step 1 of 2: this eye rendered ONCE at 4096 x 4096 by the image model and stored privately
as orders/<order>/eye_<n>.jpg (JPEG q95 4:4:4, sRGB) with a small record orders/<order>/eye_<n>.json.

ticket: an unlock ticket for THIS order, kind "unlock-<order>" (store.unlock_kind). A plain "unlock" ticket or one
for another order is refused (403). order: lower-case letters, digits and "-", 4-64 characters.

eye is required. A second render of the same crop is a different iris, so a stored master is never rendered again
by accident: the slot is claimed (orders/<order>/eye_<n>.lock, created atomically) before the model is called, a
request for a slot that is stored returns that master, and a request while another one renders it gets 409.

rerender: true renders the slot once more, and only when its stored master failed the colour check (the record's
qa.ok is false) and was not rendered again before. The first render is kept as eye_<n>_first.jpg; the better of
the two (by that check) stays in eye_<n>.jpg, the other one is kept beside it.

Reply 200: {ok, key, eye, width, height, existing, seconds, render_seconds, qa, needs_review, rerender_available,
rerendered, ms}. needs_review is true when the stored master failed the colour check. The image itself is never
returned (a 4K base64 is 3-4.4 MB, at the 4.5 MB body limit); /api/master_compose reads it from storage.
Other replies (all {ok: false, reason, error, retry}):
  503 storage_not_configured  nowhere to keep the file; answered before the body is parsed or anything is spent
  403                         no valid unlock ticket for this order
  400                         bad input (L.run's sentence)
  409 rendering               another request is rendering this eye now; ask again after retry_after seconds
  503 busy_retry              not enough time left in this invocation to render; nothing was spent, retry now
  503 model_busy              the image model refused for now (429/5xx) or did not answer in time; retry later
  503 storage_busy            storage did not answer; retry later
  502 render_rejected         the model answered without a usable 4096 px image; a retry would pay for the same
                              outcome, so retry is false and the order needs a person"""
import os, sys, io, re, json, math, time, uuid, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import BaseHTTPRequestHandler
import requests
from PIL import Image
from _lib import iris as L
from _lib import store

MASTER_SIDE = 4096           # the deliverable: flash 4K measured 4096 x 4096, $0.153, 24-31 s (2026-09-23 spike)
MAX_IN_SIDE = 2048           # the deglared crop is at most 1024 px; a larger image is not one this site made
MIN_IN_SIDE = 64
# Time plan inside the 60 s function (L.run gives the work L.BUDGET = 52 s):
POST_RESERVE = 12.0          # kept free after the model call for decode, colour lock, QA, JPEG encode and the
                             # uploads, so a finished (paid) render is always stored
RENDER_NEED = 34.0           # the read timeout every model attempt must get: the slowest flash 4K render measured
                             # (30.7 s over 8 renders, 24.2-30.7 s) plus margin. With less, nothing is sent.
RETRY_SLEEP = 2.0
RETRY_NEED = RETRY_SLEEP + POST_RESERVE + RENDER_NEED   # 48 s: a second attempt only after a quick refusal
RETRY_CODES = (429, 500, 503)
PRE_TIMEOUT = 4.0            # storage calls before the render: short and not retried, so they cannot eat the render
LOCK_STALE = 75.0            # a claim older than this belongs to an invocation that is dead (60 s maximum)


def _eye(v):
    if v is None or v == "":
        raise L.ClientError(f"Send the eye number (1 to {L.MULTI_MAX}).")
    if (isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v != int(v)
            or not 1 <= int(v) <= L.MULTI_MAX):
        raise L.ClientError(f"The eye number must be between 1 and {L.MULTI_MAX}.")
    return int(v)


def _pad(v):
    """The crop padding the client used (1.12), clamped as /api/compose clamps it."""
    try:
        p = float(v) if v not in (None, "") else 1.12
    except (TypeError, ValueError):
        p = 1.12
    return min(2.0, max(1.0, p)) if p == p else 1.12


def _base(s, pad):
    """The model input, built as /api/enhance builds it for the artistic preview: the crop squared, masked to the
    iris disk, at WORK px. The Real-ESRGAN x4 that /api/enhance runs on crops under SR_MAX_SIDE is left out on
    purpose: /api/deglare already upscales those, the image model reads the picture as 258 input tokens whatever
    its pixel size (4K spike, 2026-09-23), and x4 on one vCPU would take the seconds the 4K render needs."""
    if not isinstance(s, str) or not s:
        raise L.ClientError("Send the iris crop as base64 text.")
    crop = L.b64_to_pil(s, max_side=MAX_IN_SIDE)
    side = min(crop.size)
    if side < MIN_IN_SIDE:
        raise L.ClientError(f"The iris crop must be at least {MIN_IN_SIDE} pixels.")
    crop = crop.crop((0, 0, side, side))
    if side > L.WORK:
        crop = crop.resize((L.WORK, L.WORK), Image.LANCZOS)
    crop = L.mask_disk(crop, pad)
    if crop.size[0] != L.WORK:
        crop = crop.resize((L.WORK, L.WORK), Image.LANCZOS)
    return crop, side


def _rejected(why, order, eye):
    print(f"snapeyes master REFUSED: {why} (order {order} eye {eye})", flush=True)
    return store.Answer(502, "render_rejected", "We could not finish this artwork automatically. Retrying will not "
                        "help; we will check it by hand.", False)


def _render_4k(base, order, eye):
    """One 4K render of PROMPT_ARTISTIC. The same request L.gemini_image(PROMPT_ARTISTIC, base, size="4K") sends,
    through L.gemini with its own retry off, because only this function knows when an attempt still fits. Every
    attempt gets the time left minus POST_RESERVE as its read timeout and is not sent when that is under
    RENDER_NEED. A quick refusal (429/500/503) is tried once more when RETRY_NEED seconds are left.
    Returns (image, attempts, token counts); anything but 4096 x 4096 is refused, never stored."""
    parts = [{"text": L.PROMPT_ARTISTIC}, {"inlineData": {"mimeType": "image/png", "data": L.pil_to_b64(base, "PNG")}}]
    cfg = {"responseModalities": ["IMAGE", "TEXT"], "imageConfig": {"aspectRatio": "1:1", "imageSize": "4K"}}
    attempt = 0
    while True:
        attempt += 1
        timeout = L.time_left() - POST_RESERVE
        if timeout < RENDER_NEED:
            print(f"snapeyes master not rendered: order {order} eye {eye} attempt {attempt} would get {timeout:.1f} s, "
                  f"under RENDER_NEED {RENDER_NEED:.0f} s", flush=True)
            if attempt == 1:
                raise store.busy("busy_retry", 5, "We are busy for a moment. Please try again now.")
            raise store.busy("model_busy", 20, "The artwork renderer is busy. Please try again in a moment.")
        t_start = time.time()
        try:
            j = L.gemini(L.IMAGE_MODEL, parts, dict(cfg), timeout=timeout, retries=0)
            break
        except Exception as e:
            m = re.search(r" HTTP (\d{3})", str(e)) if isinstance(e, RuntimeError) else None
            code = int(m.group(1)) if m else None
            left = L.time_left()
            print(f"snapeyes master render failed: order {order} eye {eye} attempt {attempt} after "
                  f"{time.time() - t_start:.1f} s, {type(e).__name__} HTTP {code}, {left:.1f} s left", flush=True)
            if attempt == 1 and code in RETRY_CODES and left >= RETRY_NEED:
                time.sleep(RETRY_SLEEP)
                continue
            if code in (429, 500, 502, 503, 504) or isinstance(e, (requests.Timeout, requests.ConnectionError)):
                raise store.busy("model_busy", 20, "The artwork renderer is busy. Please try again in a moment.") from None
            if code == 400:
                raise _rejected("image model answered HTTP 400", order, eye) from None
            raise
    cand = (j.get("candidates") or [{}])[0]
    raw = None
    for p in (cand.get("content") or {}).get("parts") or []:
        if "inlineData" in p:
            raw = base64.b64decode(p["inlineData"]["data"])
            break
    if raw is None:
        raise _rejected(f"image model returned no image (finishReason {cand.get('finishReason')})", order, eye)
    out = Image.open(io.BytesIO(raw))
    if out.size != (MASTER_SIDE, MASTER_SIDE):
        # the whole point of this endpoint is the 4096 px file: anything else is refused, never stored
        raise _rejected(f"image model returned {out.size[0]}x{out.size[1]}, not {MASTER_SIDE}x{MASTER_SIDE}", order, eye)
    usage = j.get("usageMetadata") or {}
    return out.convert("RGB"), attempt, {"prompt": usage.get("promptTokenCount"), "output": usage.get("candidatesTokenCount")}


# ----------------------------------------------------------------------------- the slot
def _qa_failed(rec):
    return isinstance(rec, dict) and isinstance(rec.get("qa"), dict) and rec["qa"].get("ok") is False


def _can_rerender(rec):
    return _qa_failed(rec) and not rec.get("rerendered")


def _stored_reply(t0, key, eye, rec):
    qa = rec.get("qa") if isinstance(rec, dict) else None
    return {"ok": True, "key": key, "eye": eye, "width": MASTER_SIDE, "height": MASTER_SIDE, "existing": True,
            "seconds": round(time.time() - t0, 1), "render_seconds": 0.0, "qa": qa, "needs_review": _qa_failed(rec),
            "rerender_available": _can_rerender(rec), "rerendered": bool(isinstance(rec, dict) and rec.get("rerendered"))}


def _claim(folder, eye):
    """Claim the slot before any model spend: create eye_<n>.lock, which only one request can do. A live claim of
    another request is a 409; a claim older than LOCK_STALE (its invocation is dead) is taken over."""
    lock = f"{folder}/eye_{eye}.lock"
    mine = store.json_bytes({"t": round(time.time(), 3), "id": uuid.uuid4().hex})
    age = None
    for _ in range(3):
        try:
            store.put(lock, mine, "application/json", upsert=False, timeout=PRE_TIMEOUT, retry=False)
            return lock
        except store.StorageExists:
            pass
        raw = store.get(lock, max_bytes=4096, timeout=PRE_TIMEOUT, retry=False)
        if raw is None:
            continue                      # released a moment ago: claim it
        try:
            t = float(json.loads(raw).get("t"))
        except (ValueError, TypeError, AttributeError):
            t = None
        age = None if t is None or not math.isfinite(t) else time.time() - t
        if age is not None and age < LOCK_STALE:
            break
        print(f"snapeyes master: {lock} is stale ({'unreadable' if age is None else f'{age:.0f} s old'}), taken over", flush=True)
        store.delete(lock, timeout=PRE_TIMEOUT, retry=False)
    wait = 20 if age is None else int(max(5, min(40, 40 - age)))
    print(f"snapeyes master: {lock} is held by another request, answered 409", flush=True)
    raise store.Answer(409, "rendering", "This eye is still being made. Please wait a moment.", True, wait)


def _release(lock):
    try:
        store.delete(lock, timeout=PRE_TIMEOUT, retry=False)
    except store.StorageError as e:
        # harmless: the next request sees the master itself, or takes the claim over once it is stale
        print("snapeyes master lock not released:", L._scrub(str(e))[:200], flush=True)


def _keep_better(folder, eye, key, prev, qa, data):
    """A re-render: the better of the two renders (by the colour check) stays in eye_<n>.jpg. The first render is
    copied to eye_<n>_first.jpg before it is replaced, and a re-render that is not better is kept as
    eye_<n>_second.jpg. Nothing that was paid for is deleted. Returns which one is in eye_<n>.jpg."""
    pq = prev.get("qa") or {}
    new_ring, old_ring = qa.get("ring_de00"), pq.get("ring_de00")
    better = bool(qa.get("ok")) or (new_ring is not None and (old_ring is None or new_ring < old_ring))
    if better:
        try:
            store.copy(key, f"{folder}/eye_{eye}_first.jpg")
        except store.StorageExists:
            pass                           # copied by an earlier attempt that did not finish
        except store.StorageError as e:
            print("snapeyes master: first render not copied, the re-render is kept beside it:", L._scrub(str(e))[:200], flush=True)
            better = False
    if better:
        store.put(key, data, "image/jpeg", upsert=True)
        return "second"
    store.put(f"{folder}/eye_{eye}_second.jpg", data, "image/jpeg", upsert=True)
    return "first"


def master_eye(body):
    t0 = time.time()
    if not isinstance(body, dict):
        raise L.ClientError("Send a JSON object.")
    order = store.check_order(body.get("order"))
    if not L.check_ticket(body.get("ticket"), kind=store.unlock_kind(order)):
        raise PermissionError("master_eye: unlock ticket missing, expired, of another kind or for another order")
    eye = _eye(body.get("eye"))
    pad = _pad(body.get("pad"))
    want_rerender = body.get("rerender") is True
    folder = f"orders/{order}"
    key, rec_key = f"{folder}/eye_{eye}.jpg", f"{folder}/eye_{eye}.json"
    store.ensure_private(timeout=PRE_TIMEOUT, retry=False)      # a public bucket is refused before any spend
    if store.exists(key, timeout=PRE_TIMEOUT, retry=False):
        rec = store.get_json(rec_key, timeout=PRE_TIMEOUT, retry=False)
        if not (want_rerender and _can_rerender(rec)):
            # a retry of a stored slot is answered from storage: nothing is decoded, claimed or rendered
            print(f"snapeyes master: {key} already stored, not rendered again", flush=True)
            return _stored_reply(t0, key, eye, rec)
    base, input_px = _base(body.get("crop"), pad)
    lock = _claim(folder, eye)
    try:
        # under the claim, look again: a request that stored this slot between the first look and the claim wins
        prev = None
        if store.exists(key, timeout=PRE_TIMEOUT, retry=False):
            prev = store.get_json(rec_key, timeout=PRE_TIMEOUT, retry=False)
            if not (want_rerender and _can_rerender(prev)):
                return _stored_reply(t0, key, eye, prev)
        t1 = time.time()
        out, attempts, tokens = _render_4k(base, order, eye)
        render_s = time.time() - t1
        t2 = time.time()
        # the model may sculpt structure and light; the colour stays the client's own photo, upsampled to 4096
        out = L.chroma_lock(out, base)
        r_frac = L.iris_radius_frac(pad)
        qa = L.colour_qa(f"master {folder} eye {eye}", result=out, source=base, r_frac=r_frac)
        fid = L.ssim_lowfreq(base, out, r_frac)
        data = store.jpeg_bytes(out, 95)
        del out
        t3 = time.time()
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        this = {"pad": pad, "model": L.IMAGE_MODEL, "image_size": "4K", "width": MASTER_SIDE, "height": MASTER_SIDE,
                "input_px": input_px, "attempts": attempts, "render_seconds": round(render_s, 1),
                "fidelity": round(fid, 3), "qa": qa, "tokens": tokens, "bytes": len(data), "created": now}
        if prev is None:
            try:
                store.put(key, data, "image/jpeg", upsert=False)
            except store.StorageExists:
                # only when a claim was taken over from a request that was not dead after all
                print(f"snapeyes master: {key} was stored meanwhile; this render is discarded", flush=True)
                return _stored_reply(t0, key, eye, store.get_json(rec_key))
            record = dict(this, order=order, eye=eye)
            kept = None
        else:
            kept = _keep_better(folder, eye, key, prev, qa, data)
            first = {k: prev.get(k) for k in ("qa", "fidelity", "bytes", "created", "render_seconds")}
            second = dict(this)
            record = dict(second if kept == "second" else prev, order=order, eye=eye, rerendered=True, kept=kept,
                          first=dict(first, key=f"{folder}/eye_{eye}_first.jpg" if kept == "second" else key),
                          second=dict(second, key=key if kept == "second" else f"{folder}/eye_{eye}_second.jpg"))
        t4 = time.time()
        record["seconds"] = round(time.time() - t0, 1)
        try:
            store.put(rec_key, store.json_bytes(record), "application/json", upsert=True)
        except store.StorageError as e:
            # the master itself is stored; master_compose uses the standard pad without this record
            print("snapeyes master record not stored:", L._scrub(str(e))[:200], flush=True)
        print(f"snapeyes master: {key} stored ({'re-render, kept the ' + kept + ' one' if kept else 'first render'}) "
              f"attempts {attempts} render {render_s:.1f} s post {t3 - t2:.1f} s upload {t4 - t3:.1f} s total "
              f"{time.time() - t0:.1f} s bytes {len(data)} fidelity {fid:.3f} tokens {tokens}", flush=True)
        return {"ok": True, "key": key, "eye": eye, "width": MASTER_SIDE, "height": MASTER_SIDE, "existing": False,
                "seconds": round(time.time() - t0, 1), "render_seconds": round(render_s, 1), "qa": record.get("qa"),
                "needs_review": _qa_failed(record), "rerender_available": _can_rerender(record),
                "rerendered": bool(record.get("rerendered"))}
    finally:
        _release(lock)


def handle(req):
    store.serve(req, "master_eye", master_eye)


class handler(BaseHTTPRequestHandler):
    def do_POST(self): handle(self)
