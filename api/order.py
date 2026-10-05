# -*- coding: utf-8 -*-
"""/api/order: one endpoint for an order's whole life (Vercel Hobby counts functions, so the four steps share one).

GET  /api/order?o=<order>&k=<key>[&s=<checkout session id>][&p=1]      the status (the same as action "status")
POST /api/order  {action: "draft", eye: 1-8, crop, sealed (or preview), pad, ticket, lang, ref, order?, k?}
POST /api/order  {action: "arrange", order, k, slots: [old eye numbers in the new order]}
POST /api/order  {action: "status", order, k, s?, previews?}
POST /api/order  {action: "make", order, k, eye: 1-8, s?}
POST /api/order  {action: "compose", order, k, s?}
POST /api/order  {action: "withdraw", order, k?, name, email, lang, nonce?}   the online withdrawal function
POST /api/order  {action: "advance", order, ticket, hop, ...}   the server's own making, one step (api/_lib/maker.py):
                 only the server's self-call, with its internal ticket; 403 forbidden for anyone else
GET  /api/order  from Vercel Cron (its x-vercel-cron-schedule header or vercel-cron user agent), or with ?cron=purge:
                 the daily clean-up (api/_lib/cleanup.py), only with "Authorization: Bearer <CRON_SECRET>"

draft: one eye of an unpaid order, uploaded on its own (the 4.5 MB request limit): crop = the deglared iris square the
  preview was made from (/api/deglare's crop), sealed = the "sealed" string /api/enhance returned (the clean preview,
  encrypted with the server's key: opened here, so the stored preview is exactly the enhance output while the page never
  holds it in the clear; refused 410 preview_expired after api/_lib/preview.py SEAL_TTL, 400 preview_invalid when it
  does not verify or is one of the smaller "sealed_sizes" copies, which only /api/compose opens). The eye record the draft
  stores (draft/eye_<n>.json) gains eye_id (the first 16 hex digits of the sha256 of the preview bytes, which is what the
  seal's own id says too) and, when the seal carries one, profile (the eye profile measured at /api/enhance, api/_lib/
  styles/eye.py: read from the seal, so authentic, never from the page); a style whose gate is hard reads its gate from
  it at checkout and the master compares its own measurement with it (those readers land with the checkout and master
  work packages; nothing reads it yet). A preview sealed before the profile existed, or one an old page sends plain, has
  the id and no profile (the gate is unknown). Old pages send
  preview = the clean image string instead, accepted for one release (a display copy, which an old page would get
  from the new /api/enhance, is refused 409 preview_outdated). pad = the pad
  both used, ticket = the work ticket from /api/analyze (15 minutes: proof the eye came through the engine). Without
  order and k a new order is made and its id and access key are returned; with them the eye is added to that order
  or replaces the eye in the same slot. One work ticket has at most one unpaid order (a repeat gets the same order
  back; after that order was paid, one new one). Refused once the order is paid (409 order_paid) or 24 h after it was made
  (410 draft_expired), while today's uploads are over the daily ceiling (503 uploads_paused), and after 30 uploads
  of one order in a day (429 too_many_uploads). Stored under orders/<order>/draft/ in the private bucket (see
  _lib/pay.py).
draft and arrange answer 503 payments_not_configured, before anything is read or stored, whenever this deployment
  takes no orders (pay.ordering_problem(): no Stripe; a live key without email, without CRON_SECRET or without
  complete legal texts; a test key on production).
arrange: re-maps the uploaded eyes after the customer removed or reordered one, without uploading them again
  (the work ticket that proved them lives 15 minutes). Unlisted slots are dropped with their files.
status: unpaid / pending / paid / making / review / ready / withdrawn / deleted, the eyes, and when ready a fresh
  signed download link
  (7 days). Before the webhook has arrived, the payment is confirmed with Stripe (the session id s from the success
  page, or the order's latest one). A paid order says "paid" only once its order confirmation email went out: until
  then "pending" with waiting_for "confirmation_email" (this call sends it when nobody has), and "review" when it
  cannot go out (the owner was told). A Stripe TEST payment counts only where test orders are allowed (never on
  production): elsewhere such an order is "unpaid" with payment_check "test_mode". A "paid" or "making" reply carries
  "server": {active, step, eye}: while active the server makes the order itself (api/_lib/maker.py) and the page
  only watches; an order whose making has begun and that has no live server step gets one asked for here
  (maker.nudge). A status read never starts an order: the withdrawal page reads it too.
make: renders one eye of a PAID order at 4096 px from its stored crop and preview (master_eye's own function, with an
  unlock ticket minted here, so one eye fits in one 60 s call). Call it once per eye; a stored eye is answered from
  storage and never rendered twice. Nothing is rendered before the order confirmation email went out (402
  confirming: ask for the status, which sends it) or for a test payment where test orders do not count (402
  test_payment). After the page made an eye, the server is asked to go on with the rest (maker.nudge), so a page
  closed now still gets its file. A failure where a paid render may have been lost (master_eye failed after the
  image model answered: the master not stored, the post-processing broken) is counted per order
  (render_lost_<i>.json); the LOST_MAX-th (2) holds the order for a person (409 in_review, review.json, the owner
  told), so no retry by anyone pays for the same failure again and again.
compose: once every eye is made, the artwork with the paid style, layout, names and title, and the download link. The
  artwork is made by the order's master PLAN (api/_lib/styles/steps.py): one "art" step per call (the default plan is one
  step; a plan with more answers state "making" with artwork {done, of, step} and the caller asks again). A style of the
  legacy engine takes the very same path with master_compose's own function inside the step, so its file and digest are
  unchanged. One compose at a time (compose.lock: another one is answered 409 "rendering", like an eye); a step holds its own
  claim, try record and process guards besides. A step that can never fit this function, a killed step that keeps dying, a
  master whose colour class is not the preview's and a plate that is not there twice hold the order for a person
  (409 in_review, review.json, the owner told): never another style. A ready artwork sends the customer the "ready" email, once (maker.ready_mail_once). When a check says
  a person should look first, the delivery waits (state review)
  and the owner is told; scripts/order_admin.py release hands it out. Every hold (review.json or a held artwork) is
  also noted in cleanup/review/ (pay.index_review): the daily clean-up reminds the owner once when it has waited
  pay.REVIEW_REMIND_HOURS (36 h; the terms promise the file within 48 h).
withdraw: the online withdrawal function (api/_lib/withdraw.py): records the statement with the time it arrived,
  stops the order when nothing was made yet (state withdrawn: make and compose answer 409 withdrawn, draft and
  checkout too), emails the receipt and tells the owner (at once for an order's first statement, else in the daily
  digest; every email bounded by daily ceilings). Where the right had already lapsed it is recorded and answered all
  the same. A status reply carries "withdrawal" once a statement exists. Where this deployment cannot have sold
  anything (pay.sells(): no keys that count, and no live payment ever recorded), a statement for an order that is
  not stored is not recorded: 409 with the reason code "no_order" and recorded false (no "withdrawal" object, no
  email), which the page shows with its own text (nothing was recorded: check the number, or email the withdrawal).
advance: the server's own making of a paid order without the page (api/_lib/maker.py): one step with make_eye or
  compose_order (the same code and rules as make and compose), then a self-call for the next step. Started by the
  one who sends the order confirmation email, by the page's status call when nobody is on an unfinished order, and
  by the daily clean-up for orders older than 30 minutes that nobody finished. With "probe" instead of an order:
  one hop of the self-call test (maker.probe, scripts/order_admin.py selfcall-probe: does Vercel let the server call
  itself as often in a row as an order needs?), with the test's own internal ticket; nothing of any order is touched.

Every reply is JSON; errors are {ok: false, reason, error, retry} as the paid endpoints answer them. API.md in the
work notes lists them all."""
import os, sys, io, time, hmac, base64, hashlib, binascii, secrets
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlsplit, parse_qs
from PIL import Image
from _lib import iris as L
from _lib import store
from _lib import pay
from _lib import withdraw as W
from _lib import cleanup as C
from _lib import maker as M
from _lib import preview as P
from _lib import duration
from _lib.styles import steps as SP
import master_eye as ME
import master_compose as MC

CROP_B64_MAX = 3_000_000     # the deglared crop: a 1024 px JPEG q95 is 0.3-0.8 MB as base64
PREVIEW_B64_MAX = 1_600_000  # the /api/enhance preview: a 1024 px JPEG q93
BODY_B64_MAX = 4_300_000     # both together, under Vercel's 4.5 MB request limit
IMG_MIN, IMG_MAX = 64, 2048  # the sizes /api/master_eye accepts
FORMATS = {"JPEG": ("jpg", "image/jpeg"), "PNG": ("png", "image/png")}
FILE_MAX = 8 << 20           # a stored draft file larger than this is not one we stored
PREVIEW_LINK = 3600          # the order page's thumbnails of the approved previews
LINK_SECONDS = MC.LINK_SECONDS
LOST_MAX = 2                 # paid renders an order may lose (master_eye failed after the model call), then it is held
                             # for a person (_render_lost): one automatic retry, never a loop of paid ones


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def _too_large(what):
    return store.Answer(413, "too_large", f"The {what} is too large. Please send it as the site made it.", False)


def _ordering_open():
    """New orders only where this deployment takes them (503 payments_not_configured otherwise): the same rule as
    /api/checkout, so a deployment without Stripe keys stores nothing, exactly as before payments existed."""
    why = pay.ordering_problem()
    if why:
        raise pay.PayNotConfigured(why)


def _image(s, what, cap):
    """(bytes, format, side) of an uploaded image, refused (400/413) unless it is a square JPEG or PNG of the sizes
    master_eye accepts and decodes completely (a truncated file is refused now, not at render time)."""
    if not isinstance(s, str) or not s:
        raise L.ClientError(f"Send the {what} as base64 text.")
    if len(s) > cap:
        raise _too_large(what)
    if s.startswith("data:") and "," in s[:80]:
        s = s.split(",", 1)[1]
    try:
        raw = base64.b64decode("".join(s.split()), validate=True)
    except (binascii.Error, ValueError):
        raise L.ClientError(f"The {what} is not valid base64.") from None
    try:
        im = Image.open(io.BytesIO(raw))
        fmt, (w, h) = im.format, im.size
    except Exception:  # noqa: not an image, or a decompression bomb
        raise L.ClientError(f"We could not read the {what}.") from None
    if fmt not in FORMATS:
        raise L.ClientError(f"The {what} must be a JPEG or PNG image.")
    if w * h > L.MAX_PIXELS or max(w, h) > IMG_MAX or min(w, h) < IMG_MIN:
        raise L.ClientError(f"The {what} must be {IMG_MIN} to {IMG_MAX} pixels.")
    if abs(w - h) > 2:
        raise L.ClientError(f"The {what} must be square.")
    try:
        im.load()
    except Exception:  # noqa
        raise L.ClientError(f"We could not read the {what}.") from None
    return raw, fmt, min(w, h)


def _preview_image(body):
    """(bytes, format, side) of the eye's approved preview (see _preview_full)."""
    return _preview_full(body)[:3]


def _preview_full(body):
    """(bytes, format, side, meta) of the eye's approved preview. New pages send it sealed (/api/enhance "sealed"), opened
    here; old pages the clean "preview" string, accepted for one release. Sealed wins when both are sent. A display copy
    (the watermarked 800 px image the new /api/enhance shows) is never an order's preview: the 4K file would be made
    from its watermark. meta: what the seal says about the eye (preview.unseal_full: v, kind, eye_id, profile), None for
    a plain preview."""
    ss = body.get("sealed")
    if isinstance(ss, str) and ss:
        if len(ss) > P.SEALED_B64_MAX:
            raise _too_large("preview")
        try:
            clean, meta = P.unseal_full(ss, kinds=(P.KIND_ORDER,))   # a smaller compose copy is never an order's preview
        except P.SealExpired:
            raise store.Answer(410, "preview_expired", "This preview is too old. Please take the photo again.",
                               False) from None
        except P.SealError:
            raise store.Answer(400, "preview_invalid", "We could not verify this preview. Please take the photo again.",
                               False) from None
        return _image(base64.b64encode(clean).decode("ascii"), "preview", PREVIEW_B64_MAX) + (meta,)
    got = _image(body.get("preview"), "preview", PREVIEW_B64_MAX)
    if P.is_display(got[0]):
        raise store.Answer(409, "preview_outdated", "This page is out of date. Please reload it and take the photo "
                           "again.", False)
    return got + (None,)


def _withdrawn():
    return store.Answer(409, "withdrawn", "This order was withdrawn, so nothing is made for it.", False)


def _in_review():
    return store.Answer(409, "in_review", "A person is checking your artwork before it is delivered. We will write to "
                        "you by email, or write to info@snapeyes.com.", False)


def _to_review(order, eye, reason, note=None):
    """Hold the order for a person: review.json, and a note to the owner (note: what the owner needs to know, a sentence). Nothing more is rendered
    for it. eye None: the hold is about the artwork, not one eye."""
    now = int(time.time())
    try:
        store.put(f"orders/{order}/review.json", store.json_bytes({"reason": reason, "eye": eye, "t": now,
                                                                   "iso": pay.iso(now)}), "application/json", upsert=True)
    except store.StorageError as e:
        pay.log(f"order {order}: review mark not stored: {e}")
    pay.index_review(order, now)          # the daily clean-up's reminder after pay.REVIEW_REMIND_HOURS
    pay.owner_note(order, "review", f"SnapEyes: order {order} needs a look",
                   f"Order {order}, {'eye ' + str(eye) if eye else 'the artwork'}: {reason}.\n" + (f"{note}\n" if note else "") +
                   f"Nothing more is rendered for this order until review.json is cleared.\n"
                   f"Status: python scripts/order_admin.py status {order}\n")


def _require_paid(order, rec, s):
    paid, pending = pay.confirm_paid(order, rec, s)
    if paid and not pay.paid_counts(paid):
        pay.log(f"order {order}: paid in Stripe TEST mode, and this deployment makes nothing for test payments")
        raise store.Answer(402, "test_payment", "This order was paid in Stripe's test mode, so no file is made for it "
                           "here.", False)
    if paid:
        return paid
    if pending:
        raise store.Answer(402, "payment_processing", "Your payment is still being confirmed. We start as soon as it "
                           "is.", True, 30)
    raise store.Answer(402, "not_paid", "This order is not paid yet.", False)


def _download(order, key, dl, url=None):
    url = url or store.signed_url(key, LINK_SECONDS)
    sep = "&" if "?" in url else "?"
    return {"url": url, "download_url": f"{url}{sep}download=SnapEyes-{order}.jpg", "expires_in": LINK_SECONDS,
            "width": dl.get("width"), "height": dl.get("height"), "bytes": dl.get("bytes")}


# ----------------------------------------------------------------------------- draft
def draft(body):
    _ordering_open()
    ticket = body.get("ticket")
    if not L.check_ticket(ticket):
        raise PermissionError("order draft: work ticket missing or expired")
    eye = ME._eye(body.get("eye"))
    cs, ss = body.get("crop"), body.get("sealed")
    ps = ss if isinstance(ss, str) and ss else body.get("preview")
    if isinstance(cs, str) and isinstance(ps, str) and len(cs) + len(ps) > BODY_B64_MAX:
        raise _too_large("upload")
    craw, cfmt, cside = _image(cs, "crop", CROP_B64_MAX)
    praw, pfmt, pside, pmeta = _preview_full(body)
    pad = ME._pad(body.get("pad"))
    lang = pay.lang_of(body.get("lang"))
    ref = body.get("ref")
    ref = L.safe_segment(ref, 40) if isinstance(ref, str) and ref else None
    order, k = body.get("order"), body.get("k")
    created = False
    if order in (None, "") and k in (None, ""):
        pay.draft_room(len(craw) + len(praw))
        order, k, rec, created = pay.order_for_ticket(ticket, lang)
        if created:
            pay.log(f"order {order} created (draft eye {eye})")
    else:
        rec = _open_draft(order, k)
        pay.draft_room(len(craw) + len(praw), order)
    folder = f"orders/{order}/draft"
    uid = secrets.token_hex(4)
    (cext, ctype), (pext, ptype) = FORMATS[cfmt], FORMATS[pfmt]
    cpath, ppath = f"{folder}/eye_{eye}_crop_{uid}.{cext}", f"{folder}/eye_{eye}_preview_{uid}.{pext}"
    old = None
    if created:
        pay.parallel([lambda: store.put(cpath, craw, ctype, upsert=False),
                      lambda: store.put(ppath, praw, ptype, upsert=False)])
    else:
        old, _, _ = pay.parallel([lambda: store.get_json(f"{folder}/eye_{eye}.json", timeout=8.0),
                                  lambda: store.put(cpath, craw, ctype, upsert=False),
                                  lambda: store.put(ppath, praw, ptype, upsert=False)])
    pay.draft_logged(len(craw) + len(praw), order)
    now = int(time.time())
    erec = {"eye": eye, "pad": pad, "ref": ref, "uploaded_at": now, "uploaded": pay.iso(now),
            "crop": {"path": cpath, "type": ctype, "side": cside, "bytes": len(craw), "sha256": _sha(craw)},
            "preview": {"path": ppath, "type": ptype, "side": pside, "bytes": len(praw), "sha256": _sha(praw)},
            "eye_id": (pmeta or {}).get("eye_id") or P.eye_id_of(praw)}
    if (pmeta or {}).get("profile") is not None:
        erec["profile"] = pmeta["profile"].rec        # the sealed eye profile (authentic: it came out of the seal, not from the page)
    # written last: the slot only ever points at complete files
    store.put(f"{folder}/eye_{eye}.json", store.json_bytes(erec), "application/json", upsert=True)
    if isinstance(old, dict):
        # the retaken eye's earlier files go now (best effort; scripts/order_admin.py purge removes what is left)
        for part in ("crop", "preview"):
            p = (old.get(part) or {}).get("path") if isinstance(old.get(part), dict) else None
            if isinstance(p, str) and p.startswith(folder + "/") and p not in (cpath, ppath):
                try:
                    store.delete(p, timeout=5.0, retry=False)
                except store.StorageError as e:
                    pay.log(f"order {order}: old draft file not removed: {e}")
    return {"ok": True, "order": order, "k": k, "eye": eye, "created": created, "expires_at": pay.expires_at(rec)}


def _open_draft(order, k):
    """The record of an order whose eyes may still change (not paid, not expired)."""
    rec = pay.load_order(order, k)
    if pay.draft_expired(rec):
        raise store.Answer(410, "draft_expired", "This unpaid order is more than 24 hours old. Please start a new one.",
                           False)
    paid, stopped = pay.parallel([lambda: store.exists(f"orders/{order}/paid.json", timeout=8.0),
                                  lambda: store.exists(f"orders/{order}/withdrawn.json", timeout=8.0)])
    if paid:
        raise store.Answer(409, "order_paid", "This order is paid, so its eyes can no longer change.", False)
    if stopped:
        raise _withdrawn()
    return rec


def arrange(body):
    """Re-map the uploaded eyes without uploading them again (the work ticket that proved them lives 15 minutes):
    slots = [old slot numbers in the new canvas order], e.g. [1, 3] after the customer removed eye 2. Slots not
    listed are dropped, with their files."""
    _ordering_open()
    order, k = body.get("order"), body.get("k")
    _open_draft(order, k)
    slots = body.get("slots")
    if (not isinstance(slots, list) or not 1 <= len(slots) <= pay.MAX_EYES
            or not all(isinstance(s, int) and not isinstance(s, bool) and 1 <= s <= pay.MAX_EYES for s in slots)
            or len(set(slots)) != len(slots)):
        raise L.ClientError(f"Send slots: the eye numbers (1 to {pay.MAX_EYES}) in their new order, each once.")
    folder = f"orders/{order}/draft"
    recs = pay.parallel([lambda i=i: store.get_json(f"{folder}/eye_{i}.json", timeout=8.0)
                         for i in range(1, pay.MAX_EYES + 1)])
    have = {i: r for i, r in enumerate(recs, 1) if isinstance(r, dict)}
    missing = [s for s in slots if s not in have]
    if missing:
        raise store.Answer(409, "eyes_missing", "Some of those eyes are not uploaded.", False, None, missing=missing)
    new = {i: dict(have[s], eye=i) for i, s in enumerate(slots, 1)}
    writes = [lambda i=i, r=r: store.put(f"{folder}/eye_{i}.json", store.json_bytes(r), "application/json", upsert=True)
              for i, r in new.items() if have.get(i) != r]
    if writes:
        pay.parallel(writes)
    keep = {p for r in new.values() for p in ((r.get("crop") or {}).get("path"), (r.get("preview") or {}).get("path"))}
    for i in sorted(set(have) - set(new)):          # slot numbers no longer used
        store.delete(f"{folder}/eye_{i}.json", timeout=8.0)
    for i in sorted(set(have) - set(slots)):        # eyes no longer on the artwork: their files go
        for part in ("crop", "preview"):
            p = (have[i].get(part) or {}).get("path") if isinstance(have[i].get(part), dict) else None
            if isinstance(p, str) and p.startswith(folder + "/") and p not in keep:
                try:
                    store.delete(p, timeout=5.0, retry=False)
                except store.StorageError as e:
                    pay.log(f"order {order}: dropped draft file not removed: {e}")
    return {"ok": True, "order": order,
            "eyes": [{"eye": i, "ref": r.get("ref"), "uploaded_at": r.get("uploaded_at")} for i, r in new.items()]}


# ----------------------------------------------------------------------------- status
def _unpaid(order, rec, pending, check):
    got = pay.parallel([lambda i=i: store.get_json(f"orders/{order}/draft/eye_{i}.json", timeout=8.0)
                        for i in range(1, pay.MAX_EYES + 1)] +
                       [lambda: store.get_json(f"orders/{order}/withdrawn.json", timeout=8.0),
                        lambda: store.get_json(f"orders/{order}/withdrawal.json", timeout=8.0)])
    drafts, stopped, summary = got[:pay.MAX_EYES], got[pay.MAX_EYES], got[pay.MAX_EYES + 1]
    eyes = [{"eye": i, "uploaded": True, "ref": d.get("ref"), "uploaded_at": d.get("uploaded_at")}
            for i, d in enumerate(drafts, 1) if isinstance(d, dict)]
    state = "withdrawn" if isinstance(stopped, dict) else ("pending" if pending else "unpaid")
    out = {"ok": True, "order": order, "state": state, "lang": pay.lang_of(rec.get("lang")),
           "expires_at": pay.expires_at(rec), "expired": pay.draft_expired(rec), "eyes": eyes,
           "payments": pay.ordering_open()}
    if isinstance(summary, dict):
        out["withdrawal"] = _withdrawal_view(summary)
    co = rec.get("checkout")
    if isinstance(co, dict) and isinstance(co.get("spec"), dict):
        out["checkout"] = {"eyes": co["spec"].get("eyes"), "style": co["spec"].get("style"), "amount": co.get("amount"),
                           "currency": pay.currency_of(co.get("currency")).upper(),
                           "market": co.get("market") or co["spec"].get("market") or pay.DEFAULT_MARKET}
    if check:
        out["payment_check"] = check
    return out


def _paid_facts(order, n, mail=False):
    """What is stored for a paid order, read at once: made (per eye), delivery, review, released, deleted,
    withdrawn (withdrawn.json), withdrawal (the latest statement's summary) and, with mail=True, mail
    (mail_delivery.json), beat (advance.json: the server's own making, api/_lib/maker.py), making (making.json
    exists: making began) and art ({done, of, step}: the master plan's steps, api/_lib/styles/steps.py)."""
    folder = f"orders/{order}"
    res = pay.parallel([lambda i=i: store.exists(f"{folder}/eye_{i}.jpg", timeout=8.0) for i in range(1, n + 1)] +
                       [lambda: store.get_json(f"{folder}/delivery.json", timeout=8.0),
                        lambda: store.get_json(f"{folder}/review.json", timeout=8.0),
                        lambda: store.exists(f"{folder}/release.json", timeout=8.0),
                        lambda: store.exists(f"{folder}/deleted.json", timeout=8.0),
                        lambda: store.get_json(f"{folder}/withdrawn.json", timeout=8.0),
                        lambda: store.get_json(f"{folder}/withdrawal.json", timeout=8.0)] +
                       ([lambda: store.get_json(f"{folder}/mail_delivery.json", timeout=8.0),
                         lambda: store.get_json(f"{folder}/advance.json", timeout=8.0),
                         lambda: store.exists(f"{folder}/making.json", timeout=8.0)] + SP.state_reads(order) if mail else []))
    return {"made": list(res[:n]), "delivery": res[n], "review": res[n + 1], "released": bool(res[n + 2]),
            "deleted": bool(res[n + 3]), "withdrawn": res[n + 4], "withdrawal": res[n + 5],
            "mail": res[n + 6] if mail else None, "beat": res[n + 7] if mail else None,
            "making": bool(res[n + 8]) if mail else False,
            "art": SP.progress(SP.state_from(order, res[n + 9:n + 13])) if mail else None}


def _withdrawal_view(summary):
    """The latest withdrawal statement as the order page shows it (no personal data)."""
    return {k: summary.get(k) for k in ("id", "at", "received", "state", "effective", "reason", "mail")}


def _deleted():
    return store.Answer(410, "deleted", "The files of this order were deleted (they are kept for 12 months, or less on "
                        "request). Write to info@snapeyes.com.", False)


def _paid_reply(order, paid, made, delivery, review, released, url=None, previews=False, deleted=False,
                waiting=None, withdrawn=None, withdrawal=None, artwork=None):
    spec = paid["spec"]
    n = spec["eyes"]
    held = isinstance(delivery, dict) and bool(delivery.get("needs_review")) and not released
    if isinstance(withdrawn, dict):
        state = "withdrawn"       # the customer withdrew before anything was made: nothing is made or delivered
    elif deleted:
        state = "deleted"
    elif isinstance(delivery, dict) and not held:
        state = "ready"
    elif held or isinstance(review, dict):
        state = "review"
    elif any(made):
        state = "making"
    else:
        state = "paid"
    if waiting and state in ("paid", "making"):
        state = "pending"         # paid, but nothing may be made before the order confirmation went out
    out = {"ok": True, "order": order, "state": state, "lang": spec.get("lang"), "count": n, "style": spec.get("style"),
           "layout": spec.get("layout"), "names": pay.names_text(spec), "title": spec.get("title"),
           "amount": paid.get("amount_total"), "currency": pay.currency_of(paid.get("currency")).upper(),
           "market": paid.get("market") or spec.get("market") or pay.DEFAULT_MARKET,
           "eyes": [{"eye": i, "made": bool(made[i - 1])} for i in range(1, n + 1)]}
    if state == "pending":
        out["waiting_for"] = waiting
    if isinstance(artwork, dict) and state in ("paid", "making", "pending"):
        # the master plan's progress: {done, of, step}: steps done, steps in all, the name of the next one (the default plan has one, "art")
        out["artwork"] = {"done": artwork.get("done"), "of": artwork.get("of"), "step": artwork.get("step")}
    if isinstance(withdrawal, dict):
        out["withdrawal"] = _withdrawal_view(withdrawal)
    if state in ("deleted", "withdrawn"):
        return out
    if state == "ready":
        out["download"] = _download(order, delivery["key"], delivery, url)
    if previews:
        recs = pay.parallel([lambda i=i: store.get_json(f"orders/{order}/draft/eye_{i}.json", timeout=8.0)
                             for i in range(1, n + 1)])
        paths = [(r.get("preview") or {}).get("path") if isinstance(r, dict) and isinstance(r.get("preview"), dict)
                 else None for r in recs]
        links = pay.parallel([lambda p=p: store.signed_url(p, PREVIEW_LINK) if isinstance(p, str) else None
                              for p in paths])
        for e, u in zip(out["eyes"], links):
            e["preview_url"] = u
    return out


def _status(order, rec, s=None, previews=False):
    check = None
    try:
        paid, pending = pay.confirm_paid(order, rec, s)
    except (pay.PayBusy, pay.PayError, pay.PayNotConfigured) as e:
        # the webhook will still mark the order; the page asks again
        pay.log(f"order {order}: payment check unavailable: {e}")
        paid, pending, check = None, None, "unavailable"
    if paid and not pay.paid_counts(paid):
        pay.log(f"order {order}: paid in Stripe TEST mode, and this deployment makes nothing for test payments")
        return _unpaid(order, rec, None, "test_mode")
    if not paid:
        return _unpaid(order, rec, pending, check)
    f = _paid_facts(order, paid["spec"]["eyes"], mail=True)
    review, waiting = f["review"], None
    if not f["deleted"] and not isinstance(f["withdrawn"], dict) and not isinstance(f["delivery"], dict) \
            and not isinstance(review, dict):
        # the order confirmation first (it confirms the withdrawal waiver): nothing is made before it went out
        c = pay.confirmation(order, rec, paid, cur=f["mail"])
        if c == "held":
            review = {"reason": pay.MAIL_REVIEW}
        elif c == "waiting":
            waiting = "confirmation_email"
    out = _paid_reply(order, paid, f["made"], f["delivery"], review, f["released"], previews=previews,
                      deleted=f["deleted"], waiting=waiting, withdrawn=f["withdrawn"], withdrawal=f["withdrawal"], artwork=f["art"])
    if out["state"] in ("paid", "making"):
        # the server's own making (api/_lib/maker.py): the page drives nothing while it is on the order, and an
        # order whose making has begun gets it asked for again when no step is live. A status read never STARTS an
        # order (the withdrawal page reads this too: opening it must not start the work that ends the right)
        v = M.view(f["beat"], order)
        if not v["active"] and (f["making"] or any(f["made"])) and M.nudge(order, f["beat"], why="status"):
            v = M.view(f["beat"], order)
        out["server"] = v
    return out


def status(body):
    rec = pay.load_order(body.get("order"), body.get("k"))
    return _status(body["order"], rec, body.get("s"), body.get("previews") is True)


# ----------------------------------------------------------------------------- make and compose
def _draft_files(drec):
    if not isinstance(drec, dict):
        return None
    c, p = drec.get("crop"), drec.get("preview")
    if not (isinstance(c, dict) and isinstance(p, dict) and isinstance(c.get("path"), str) and isinstance(p.get("path"), str)):
        return None
    return c, p, drec.get("pad")


def make(body):
    order, k = body.get("order"), body.get("k")
    rec = pay.load_order(order, k)
    eye = ME._eye(body.get("eye"))
    paid = _require_paid(order, rec, body.get("s"))
    return make_eye(order, rec, paid, eye)


def make_eye(order, rec, paid, eye, server=False):
    """One eye of a paid order (paid: its paid record, already checked to count here): every rule of make, for the
    order page (make) and for the server's own making (server=True, api/_lib/maker.py advance). After the page made an
    eye, the server is asked to go on with the rest (maker.nudge), so the order is finished even if the page is
    closed now."""
    n = paid["spec"]["eyes"]
    if eye > n:
        raise L.ClientError(f"This order has {n} eye{'s' if n > 1 else ''}.")
    folder = f"orders/{order}"
    # short and not retried: these reads must not eat the render's time (master_eye needs ~46 s of the 52)
    stored, review, drec, deleted, mail, stopped, beat = pay.parallel([
        lambda: store.exists(f"{folder}/eye_{eye}.jpg", timeout=5.0, retry=False),
        lambda: store.get_json(f"{folder}/review.json", timeout=5.0, retry=False),
        lambda: store.get_json(f"{folder}/draft/eye_{eye}.json", timeout=5.0, retry=False),
        lambda: store.exists(f"{folder}/deleted.json", timeout=5.0, retry=False),
        lambda: store.get_json(f"{folder}/mail_delivery.json", timeout=5.0, retry=False),
        lambda: store.exists(f"{folder}/withdrawn.json", timeout=5.0, retry=False),
        lambda: store.get_json(f"{folder}/advance.json", timeout=5.0, retry=False)])
    if stopped:
        raise _withdrawn()
    if deleted:
        raise _deleted()
    if isinstance(review, dict) and not stored:
        raise _in_review()
    if not stored:
        # performance starts only after the order confirmation went out (it confirms the withdrawal waiver).
        # Not sent from here, the render needs the time: the status call sends it.
        c = pay.confirmation(order, rec, paid, cur=mail, send=False)
        if c == "held":
            raise _in_review()
        if c == "waiting":
            raise store.Answer(402, "confirming", "Your order confirmation email is on its way. We start as soon as "
                               "it has gone out.", True, 10)
    req = {"order": order, "eye": eye, "ticket": L.mint_ticket(store.unlock_kind(order), 300)}
    if not stored:
        files = _draft_files(drec)
        if files is None:
            _to_review(order, eye, "draft_missing")
            raise _in_review()
        c, p, pad = files
        craw, praw = pay.parallel([lambda: store.get(c["path"], max_bytes=FILE_MAX, timeout=8.0, retry=False),
                                   lambda: store.get(p["path"], max_bytes=FILE_MAX, timeout=8.0, retry=False)])
        if craw is None or praw is None or _sha(craw) != c.get("sha256") or _sha(praw) != p.get("sha256"):
            _to_review(order, eye, "draft_files_missing_or_changed")
            raise _in_review()
        req.update(crop=base64.b64encode(craw).decode("ascii"), preview=base64.b64encode(praw).decode("ascii"), pad=pad)
        del craw, praw
        # making.json: the moment performance began (the first render of this order, right before the model is
        # called), read by the withdrawal function: from here on the right of withdrawal has lapsed
        _making_started(order, eye, mail)
    try:
        r = ME.master_eye(req)
    except store.Answer as a:
        if a.status == 502:
            _to_review(order, eye, str(a.body.get("reason") or "render_rejected"))
        raise
    except Exception as e:
        if isinstance(e, (store.StorageExists, L.ClientError)) or store.unspent(e):
            raise                        # nothing paid was lost (master_eye marks these): a retry costs nothing
        lost = _render_lost(order, eye, e)
        if lost >= LOST_MAX:
            raise _in_review() from e    # held for a person (_render_lost): the page and the server stop here
        store.mark_lost(e, lost)         # the server's own making stops instead of trying again at once
        raise
    pay.log(f"order {order}: eye {eye}/{n} {'was stored' if r.get('existing') else 'made'} in {r.get('seconds')} s"
            f"{' NEEDS REVIEW' if r.get('needs_review') else ''}{' (server)' if server else ''}")
    if not server and not r.get("existing"):
        # making has begun: the server goes on with the rest too, so a page closed now still gets its file
        M.nudge(order, beat, why="page_made_an_eye")
    return {"ok": True, "order": order, "eye": eye, "count": n, "made": True, "existing": bool(r.get("existing")),
            "seconds": r.get("seconds")}


def _render_lost(order, eye, e):
    """master_eye failed where a paid render may have been lost (not marked unspent: the master could not be stored,
    the post-processing broke after the model answered). Counted per order, whoever asked (the order page, the
    server's own making, the admin panel): render_lost_<i>.json, each created atomically, so two losses at once both
    count. The LOST_MAX-th holds the order for a person (review.json, the owner told once): nothing more is rendered
    for it by itself, so the same failure is never paid for again and again. After the owner clears that hold, each
    further loss holds it again at once. A count that cannot be stored holds it too (the safe side). Returns the
    count. Never raises."""
    detail = pay.scrub(f"{type(e).__name__}: {e}")[:200]
    now = time.time()
    n = LOST_MAX + 1
    try:
        mark = store.json_bytes({"eye": eye, "t": round(now, 3), "iso": pay.iso(now), "error": detail})
        for i in range(1, LOST_MAX + 1):
            try:
                store.put(f"orders/{order}/render_lost_{i}.json", mark, "application/json", upsert=False, timeout=5.0,
                          retry=False)
                n = i
                break
            except store.StorageExists:
                continue
    except Exception as se:  # noqa: not countable, so held rather than paid for again
        pay.log(f"order {order}: a lost render was not counted: {type(se).__name__}")
        n = LOST_MAX
    count = str(n) if n <= LOST_MAX else f"more than {LOST_MAX}"
    pay.log(f"order {order}: eye {eye}: a paid render may be lost ({count}, {LOST_MAX} allowed): {detail}")
    if n >= LOST_MAX:
        _to_review(order, eye, f"render_lost ({count} paid renders lost after the image model call; the last: "
                               f"{detail})")
    return n


def _making_started(order, eye, mail):
    """Record when making began, once per order (never raises: the stored eyes are the evidence otherwise)."""
    now = time.time()
    try:
        store.put(f"orders/{order}/making.json",
                  store.json_bytes({"t": round(now, 3), "iso": pay.iso(now), "eye": eye,
                                    "confirmation_at": mail.get("t") if isinstance(mail, dict) else None}),
                  "application/json", upsert=False, timeout=3.0, retry=False)
    except store.StorageExists:
        pass
    except store.StorageError as e:
        pay.log(f"order {order}: making.json not stored: {e}")


def compose(body):
    order, k = body.get("order"), body.get("k")
    rec = pay.load_order(order, k)
    paid = _require_paid(order, rec, body.get("s"))
    return compose_order(order, rec, paid)


COMPOSE_STALE = duration.COMPOSE_STALE_S   # a compose claim older than this belongs to an invocation that is dead (the longest life of one, plus 15 s)


def _compose_claim(order):
    """Claim composing the order's artwork (compose.lock, created atomically) so the order page and the server
    never compose it twice at once. A live claim of another request is a 409 with the reason "rendering" (the page's
    driver waits and asks again, as for an eye); one older than COMPOSE_STALE is taken over. Returns the claim."""
    path = f"orders/{order}/compose.lock"
    cid = secrets.token_hex(6)
    age = None
    for _ in range(3):
        try:
            store.put(path, store.json_bytes({"t": round(time.time(), 3), "id": cid}), "application/json",
                      upsert=False, timeout=5.0, retry=False)
            return path, cid
        except store.StorageExists:
            pass
        cur = store.get_json(path, timeout=5.0, retry=False)
        if cur is None:
            continue                     # released a moment ago
        try:
            age = time.time() - float(cur.get("t"))
        except (TypeError, ValueError):
            age = None
        if age is not None and -60.0 < age < COMPOSE_STALE:
            break
        pay.log(f"order {order}: a stale compose claim is taken over")
        store.delete(path, timeout=5.0, retry=False)
    wait = 15 if age is None else int(max(5, min(40, COMPOSE_STALE - age)))
    raise store.Answer(409, "rendering", "Your artwork is being put together. Please wait a moment.", True, wait)


def _compose_release(claim):
    path, cid = claim
    try:
        cur = store.get_json(path, timeout=4.0, retry=False)
        if isinstance(cur, dict) and cur.get("id") == cid:
            store.delete(path, timeout=4.0, retry=False)
    except store.StorageError as e:
        pay.log(f"compose claim not released (taken over after {COMPOSE_STALE:.0f} s): {e}")


def _write_delivery(order, r):
    """delivery.json of a made artwork (what every reader of an order's artwork reads): the file, its size, the style and layout, whether a check
    wants a person to look first. A style of the v3 engine adds the design it was drawn in, the fallback the plan took (overlap_fallback: the Kiss geometry for a
    wide pupil; stack_contrast: the stacked lens of a pair whose colours differ strongly) and the plan's identity (plan8). Returns it."""
    now = int(time.time())
    delivery = {"key": r["key"], "width": r.get("width"), "height": r.get("height"), "bytes": r.get("bytes"),
                "style": r.get("style"), "layout": r.get("layout"), "count": r.get("count"),
                "needs_review": bool(r.get("needs_review")), "created_at": now, "created": pay.iso(now)}
    for k in ("design_used", "fallback", "plan8"):
        if r.get(k):
            delivery[k] = r[k]
    store.put(f"orders/{order}/delivery.json", store.json_bytes(delivery), "application/json", upsert=True)
    return delivery


def master_ctx(order, rec, paid, by, arrival_left=None, finish=True, arm=True):
    """The context of the order's master steps (api/_lib/styles/steps.py): the paid spec, the delivery writer, the watchdog, and the legacy composer
    (looked up when it is called, so a test that replaces MC.master_compose is heard)."""
    return SP.Ctx(order, paid["spec"], rec=rec, paid=paid, by=by, arrival_left=arrival_left,
                  finish=(lambda r: _write_delivery(order, r)) if finish else None,
                  arm=(lambda: M.arm_watchdog(order)) if arm else None,
                  legacy=lambda body: MC.master_compose(body))


def compose_order(order, rec, paid, server=False):
    """The artwork of a paid order (paid: its paid record, already checked to count here): every rule of compose, for
    the order page (compose) and the server's own making (server=True, api/_lib/maker.py). ONE master step per call (the
    default plan has one: the artwork); a plan with more answers state "making" with artwork {done, of, step}. Once an
    artwork is ready without a hold, the customer gets the "ready" email, once (maker.ready_mail_once)."""
    arrival_left = L.time_left()
    spec = paid["spec"]
    n = spec["eyes"]
    f = _paid_facts(order, n)
    made, delivery, review, released, deleted = f["made"], f["delivery"], f["review"], f["released"], f["deleted"]
    if isinstance(f["withdrawn"], dict):
        raise _withdrawn()
    if deleted:
        raise _deleted()
    if isinstance(delivery, dict):
        # composed before: the same file, a fresh link (or still held for review)
        return _paid_reply(order, paid, made, delivery, review, released)
    if isinstance(review, dict):
        raise _in_review()
    missing = [i for i, m in enumerate(made, 1) if not m]
    if missing:
        raise store.Answer(409, "eyes_not_ready", "Not every eye is finished yet.", True, 5, missing=missing)
    folder = f"orders/{order}"
    claim = _compose_claim(order)
    try:
        # under the claim, look again: a request that composed it between the first look and the claim wins
        done = store.get_json(f"{folder}/delivery.json", timeout=5.0, retry=False)
        if isinstance(done, dict):
            return _paid_reply(order, paid, made, done, None, released)
        try:
            got = SP.advance(master_ctx(order, rec, paid, "server" if server else "page", arrival_left))
        except SP.Hold as h:
            _to_review(order, None, h.reason, h.note)
            raise _in_review() from h
        if not got["final"]:
            return _paid_reply(order, paid, [True] * n, None, None, released, artwork=got["progress"])
        r = got["artwork"]
        delivery = got["delivery"] or _write_delivery(order, dict(r, plan8=got.get("plan8"), design_used=got.get("design_used"), fallback=got.get("fallback")))
    finally:
        _compose_release(claim)
    now = delivery["created_at"]
    held = delivery["needs_review"] and not released
    if held:
        pay.index_review(order, now)      # the daily clean-up's reminder after pay.REVIEW_REMIND_HOURS
        pay.owner_note(order, "review", f"SnapEyes: order {order} waits for your look",
                       f"Order {order}: the artwork is made, but a check says a person should look first "
                       f"(colour or preview match).\nIt is NOT delivered until you release it:\n"
                       f"  python scripts/order_admin.py status {order}\n  python scripts/order_admin.py release {order}\n")
    pay.log(f"order {order}: artwork {'HELD for review' if held else 'ready'} "
            f"{delivery['width']}x{delivery['height']} {delivery['bytes']} bytes{' (server)' if server else ''}")
    if not held:
        M.ready_mail_once(order, rec, paid, released)
    return _paid_reply(order, paid, [True] * n, delivery, None, released, url=r.get("url"))


def advance(body):
    """POST /api/order {action: "advance", ...}: the server's own making, one step (api/_lib/maker.py). Only with the
    internal ticket the server's self-call carries: 403 forbidden for anyone else, before anything is read."""
    return M.advance(body, STEPS)


STEPS = {"make_eye": lambda order, rec, paid, eye: make_eye(order, rec, paid, eye, server=True),
         "compose_order": lambda order, rec, paid: compose_order(order, rec, paid, server=True)}


# ----------------------------------------------------------------------------- routing
ACTIONS = {"draft": draft, "arrange": arrange, "status": status, "make": make, "compose": compose,
           "withdraw": W.withdraw, "advance": advance}


def dispatch(body):
    act = body.get("action")
    fn = ACTIONS.get(act) if isinstance(act, str) else None
    if fn is None:
        raise L.ClientError("Send an action: draft, arrange, status, make, compose or withdraw.")
    return fn(body)


def _query(req):
    q = parse_qs(urlsplit(req.path).query, keep_blank_values=False)
    return {k: v[0] for k, v in q.items() if v and isinstance(v[0], str)}


def get_status(q):
    rec = pay.load_order(q.get("o"), q.get("k"))
    return _status(q["o"], rec, q.get("s"), q.get("p") in ("1", "true"))


def is_cron(req, q):
    """A clean-up call: Vercel Cron marks its requests (x-vercel-cron-schedule, user agent vercel-cron/1.0; the
    vercel.json path is the plain /api/order), or ?cron=purge by hand. Either way CRON_SECRET decides."""
    ua = str(req.headers.get("user-agent") or "").lower()
    return q.get("cron") == "purge" or bool(req.headers.get("x-vercel-cron-schedule")) or ua.startswith("vercel-cron/")


def cron_purge(req):
    """The daily clean-up (vercel.json crons, once a day on Hobby): api/_lib/cleanup.py run(), time-boxed inside
    this 60 s function (it stops with more: true 10 s before the budget ends; the next day goes on). Only with
    "Authorization: Bearer <CRON_SECRET>"."""
    secret = pay._env("CRON_SECRET")
    if len(secret) < 16:
        raise store.Answer(503, "cron_not_configured", "CRON_SECRET is not set.", False)
    got = str(req.headers.get("authorization") or "")
    if not hmac.compare_digest(got.encode("utf-8", "replace"), ("Bearer " + secret).encode("utf-8")):
        raise store.Answer(403, "forbidden", "Not allowed.", False)
    return C.run(yes=True, stop_left=10.0)


def handle_get(req):
    q = _query(req)
    if is_cron(req, q):
        pay.serve(req, "order cron", lambda body: cron_purge(req), gate=False)
        return
    pay.serve(req, "order", lambda body: get_status(q), gate=False)


def handle_post(req):
    pay.serve(req, "order", dispatch)


def handle(req):
    """scripts/dev_api.py calls handle() for GET and POST alike."""
    if req.command == "GET":
        handle_get(req)
    else:
        handle_post(req)


class handler(BaseHTTPRequestHandler):
    def do_GET(self): handle_get(self)
    def do_POST(self): handle_post(self)
