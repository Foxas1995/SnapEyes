# -*- coding: utf-8 -*-
"""POST /api/enhance  {crop: b64 clean iris square, mode: "faithful"|"artistic", pad, session, consent, meta}
faithful: Real-ESRGAN x4 for small crops -> Gemini restoration with thinking -> fidelity guard.
artistic: Gemini macro re-interpretation (beautiful, not pixel-faithful).
The page never gets the clean restoration (api/_lib/preview.py): "image" is an 800 px display copy with the preview
watermark across the iris, "sealed" the clean 1024 px JPEG encrypted with the server's key (what /api/compose and the
order draft take back), "sealed_sizes" the clean iris at the sides /api/compose is sent for 3-8 eyes, sealed too.
POST /api/enhance  {sample: true, image: b64}: the AI-generated sample eye's prepared restoration (SAMPLE_SHA256) comes
back the same way, with no ticket and no model call.
The eye profile (api/_lib/styles/eye.py): measured once here on the clean preview bytes (colour class, ring colours, pupil, the two
restoration gates, 1 to 2 s), sealed into all three seals (preview.py, seal v2) and told to the page in "profile" (eye_id, class,
ease, pupil class, the gate's ok per rule; reply field added, nothing else changes). Measured only when EYE.PROFILE_MIN_LEFT seconds
are left after the model call; otherwise the seals carry the eye id alone and "profile" says unknown: true (hard styles then ask
for the preview again). A failing measurement never costs the preview.
The Reveal (api/_lib/styles/reveal.py, work package WP9): the numbers the page needs to put the customer's own photo and this restoration on one
circle with a hard cut through the pupil ("reveal": the pupil, the registration shift of the photo layer, the restored edge, ok, soft, drift, lid;
about 150 bytes), measured on the clean restoration and the deglared crop it was made from, and the display copy built from the restoration with its
eyelid skin hidden and its pupil crushed to black (the sealed copies are untouched: they are the clean preview). ok false means the restored colour
drifted from the photo or the halves do not register: the page then shows the strip without the cut and says why. Measured only with
REVEAL_MIN_LEFT seconds left and for the site's crop padding (the body's "pad" may be anywhere in 1 to 2, and the Reveal's measurements are made at 1.12);
otherwise "reveal" is absent and the display copy is the plain one (the page keeps the plain before and after slider). Either way the display copy's
watermark sits on the iris disc of the request's padding, the one the profile and the seals carry.
No stored wide frame, no card: the browser builds the photo's frame itself (decision C10).
The conditional second restoration (2026-10-12, the owner allowed it for the preview only: the paid 4K master never runs twice): when the first
restoration fails a gate rule of RETRY_RULES and the invocation has RETRY_MIN_LEFT seconds left, the model is asked once more (it is not seeded:
every call is a new draw), the second restoration goes through the same steps and the same profile, and the better of the two is kept: the second
when it fails no rule the first passed and its severity (api/_lib/styles/gate.py severity) is at most RETRY_CLEAR of the first's, else the first.
A passing eye makes no second call and comes back exactly as before, and so does every eye with SNAPEYES_RETRY2=off. Only when a rule failed, the
reply gets "retry" (ran, kept, code, gate1, sev1, sev2, ms) and the event gets retry, gate1, sev1, sev2, retry_ms."""
import os, sys, json, time, base64, hashlib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import BaseHTTPRequestHandler
from PIL import Image
from _lib import iris as L
from _lib import pupilgeo as PG   # pupil repairs that start from a measurement of the render or of the photo
from _lib import pupil_seal as PS   # the render's pupil: a halo round it, a colour zone on a photo that is black there
from _lib import events as E   # the admin panel's usage events (no personal data)
from _lib import preview as P
from _lib.styles import eye as EYE   # the eye profile: measured here, sealed, read by compose, the order draft and the master
from _lib.styles import gate as GATE   # the gate's severity: how far past its rules an eye is (the second restoration)
from _lib.styles import reveal as REV   # the Reveal's numbers and its display copy (WP9)

# sha256 of public/assets/sample_eye_blue_restored.jpg, the sample eye's restoration the page ships (made once by the
# live engine, 2026-09-29). Replace the file and this changes with it; the page then falls back to the studio.
SAMPLE_SHA256 = "7e681ceca21955127d41cb6c899c4f5dd708819ea872a9dc305f8d0cce3e6cb7"
SAMPLE_B64_MAX = 600_000

def _measure(clean, pad, memo=False):
    """(profile, ms): the eye's profile measured on the clean preview bytes (what every later step reads back), or (None, None) when
    the invocation has no time left for it or the measurement fails. A preview is never lost to its profile."""
    if not EYE.time_for_profile():
        return None, None
    t0 = time.time()
    try:
        prof = EYE.profile_of_bytes(clean, pad=pad, memo=memo)
    except Exception as e:  # noqa: the page gets its preview; the gate is then unknown until the preview is made again
        print("snapeyes enhance: profile not measured:", L._scrub(repr(e))[:200], flush=True)
        return None, None
    return prof, int((time.time() - t0) * 1000)


def _public(prof, clean):
    """The reply's "profile": the public part of the profile, or just the eye id and unknown: true when it was not measured."""
    return prof.public() if prof is not None else {"eye_id": P.eye_id_of(clean), "v": EYE.PROFILE_V, "unknown": True}


def _codes(prof, ms):
    """The event fields of one eye's profile (codes and numbers only): gate ok / lid / fill / both / unknown, the first reason code of
    a failure, the colour class, the pupil class, the measuring time."""
    if prof is None:
        return {"gate": "unknown", "reason": "none"}
    g = {r: prof.gate(r) for r in ("lid", "fill")}
    failed = [r for r in ("lid", "fill") if g[r]["ok"] is False]
    why = next((c for r in failed for c in g[r]["why"]), None)
    return {"gate": ("both" if len(failed) == 2 else failed[0]) if failed else ("unknown" if any(x["ok"] is None for x in g.values()) else "ok"),
            "reason": why or "none", "cls": prof.cls, "pupil": prof.pupil_cls, "profile_ms": ms}


# The conditional second restoration (module text). SNAPEYES_RETRY2=off, 0, false or no switches it off (read once at import, BOM safe).
RETRY_ON = (os.environ.get("SNAPEYES_RETRY2") or "on").strip().lstrip("\ufeff").lower() not in ("off", "0", "false", "no")
RETRY_RULES = ("lid",)       # the gate rules whose failure asks for it. The seal carries "lid" (read by every style but the three Universe ones: singles, pairs,
                             # groups) and "fill" (the Universe styles). A new draw mends a failed lid rule in 4 of 9 live cases (15 of 31 on the stored bake-off
                             # numbers) and a failed fill rule in 0 of 4 (3 of 20)
RETRY_MIN_LEFT = 32.0        # seconds left in the invocation (after the first profile) that a second restoration needs: the slowest model call of the
                             # 118 flash calls of the bake-off (20.2 s; p90 16.1, p99 19.2), what a draw does after the call (locks, repairs, JPEG, the
                             # profile: 2.3 s at most measured here, 3.8 s at Vercel's slow factor of 1.67), the Reveal and the seals (1.0 s there) and 7 s
                             # of safety. The budget is 52 s and the p90 of a whole enhance about 17 s: a retry starts unless the first draw took over 20 s
RETRY_CLEAR = 0.8            # when both fail, the second is kept only when its severity is at most this share of the first's

Draw = collections.namedtuple("Draw", "out clean prof ms fid fallback qa")   # one restoration, from the model call to the measured profile


def _draw(mode, base, source, r_frac, pad):
    """One restoration of the deglared crop: the model call, the locks, the pupil repairs, the colour QA, the clean JPEG and its profile.
    The steps /api/enhance has always had; a second restoration makes them again on the same crop."""
    fallback = False
    if mode == "artistic":
        out = raw = L.gemini_image(L.PROMPT_ARTISTIC, base)
        # this is the product now, so the colour is locked all the way to the client's own photo:
        # the model may sculpt structure and light, it may not decide what colour their eye is
        out = L.chroma_lock(out, base)
        out = L.pupil_lock(out, base, r_frac)   # nor how wide their pupil is: no iris where the photo shows none
        fid = L.ssim_lowfreq(base, out, r_frac)
    else:
        out = raw = L.gemini_image(L.PROMPT_ENHANCE, base, thinking="high")
        out = L.chroma_lock(out, base)   # the model restores structure; the colour stays the client's own
        out = L.pupil_lock(out, base, r_frac)
        fid = L.ssim_lowfreq(base, out, r_frac)
        if fid < L.FIDELITY_FLOOR:
            out, fallback = base, True
    out = out.resize((L.WORK, L.WORK), Image.LANCZOS)
    if not fallback:
        # the last look at the render's pupil: each repair is measured on the render and returns the very same object when it
        # finds nothing, so a right pupil comes back untouched (api/_lib/pupilgeo.py, api/_lib/pupil_seal.py; SNAPEYES_PUPIL=off)
        out = PG.tone_guard(out, base, r_frac)   # a pupil the model drew grey goes back to the photo's dark
        out = PS.seal(out, raw, base, r_frac)    # a smooth halo round a pupil drawn too small; a blue-grey zone on a photo that is black there
        out = PG.edge_guard(out, r_frac)         # blue light on the rim of a warm iris is a window, not the eye
    # colour QA: how far the render moved the iris colour from the deglared crop it was made from. The pupil
    # is only made neutral later, by the grade in /api/compose, so it is checked there. Logged, never blocking.
    qa = L.colour_qa("enhance", result=out, source=source, r_frac=r_frac)
    # the clean restoration exactly as the page used to receive it (JPEG q93): sealed, never shown. The order's preview
    # and master_eye's preview_sha are these bytes, as before
    clean = base64.b64decode(L.pil_to_b64(out, "JPEG", 93))
    prof, prof_ms = _measure(clean, pad)
    return Draw(out, clean, prof, prof_ms, fid, fallback, qa)


def _failing(prof):
    """The gate rules a profile fails."""
    return {r for r in GATE.RULES if prof.gate(r)["ok"] is False}


def _retry(first, mode, base, source, r_frac, pad):
    """The first restoration fails a rule of RETRY_RULES: (the Draw to use, the note of the retry). With RETRY_MIN_LEFT seconds left the model is
    asked once more and the second restoration is kept when it fails no rule the first passed and its severity is at most RETRY_CLEAR of the
    first's (a restoration that passes is 0.0); otherwise the first stays. A second restoration that fails or cannot be measured costs nothing:
    the first is kept. The note: code (kept1, kept2, time, error), gate1 (the first draw's gate code), sev1, sev2 and ms (what the second took)."""
    note = {"gate1": _codes(first.prof, first.ms)["gate"], "sev1": GATE.severity(first.prof)}
    if L.time_left() < RETRY_MIN_LEFT:
        return first, {**note, "code": "time"}
    t1 = time.time()
    try:
        second = _draw(mode, base, source, r_frac, pad)
    except Exception as e:  # noqa: the page gets the first restoration
        print("snapeyes enhance: second restoration not made:", L._scrub(repr(e))[:200], flush=True)
        return first, {**note, "code": "error"}
    note["ms"] = int((time.time() - t1) * 1000)
    if second.prof is None:                         # no time left to measure it, or the measurement failed: it cannot be judged
        return first, {**note, "code": "error"}
    note["sev2"] = GATE.severity(second.prof)
    keep = _failing(second.prof) <= _failing(first.prof) and note["sev2"] <= RETRY_CLEAR * note["sev1"]
    return (second if keep else first), {**note, "code": "kept2" if keep else "kept1"}


def _retry_codes(note):
    """The event fields of a retry note (codes and numbers only); none when no rule failed."""
    return {"retry": note["code"], "gate1": note["gate1"], "sev1": note["sev1"], "sev2": note.get("sev2"), "retry_ms": note.get("ms")} if note else {}


def sample(body):
    """The AI-generated sample eye's prepared restoration, sent back by the page as it downloaded it: the display copy
    and the sealed originals, exactly as a real restoration comes back, so the sample shows and composes through the
    same path. Only that one file is accepted: no ticket and no model call, so this is no free watermarking service."""
    s = body.get("image")
    if not isinstance(s, str) or not s or len(s) > SAMPLE_B64_MAX:
        raise L.ClientError("That is not the sample eye.")
    try:
        raw = base64.b64decode(s, validate=True)
    except ValueError:
        raise L.ClientError("That is not the sample eye.") from None
    if hashlib.sha256(raw).hexdigest() != SAMPLE_SHA256:
        raise L.ClientError("That is not the sample eye.")
    prof, _ = _measure(raw, 1.12, memo=True)          # the same file every time: measured once per instance
    return {"ok": True, "mode": "artistic", "sample": True, **P.protect(L.b64_to_pil(s), raw, profile=prof), "profile": _public(prof, raw)}

def enhance(body):
    t0 = time.time()
    if body.get("sample") is True:
        return sample(body)
    if not L.check_ticket(body.get("ticket")):
        raise PermissionError("expired_or_missing_ticket")
    crop = L.b64_to_pil(body.get("crop"))
    s = min(crop.size); crop = crop.crop((0, 0, s, s))
    if s < 48: raise ValueError("crop too small")
    if s > L.WORK:                      # mask and model both work at WORK; do not allocate more than that
        crop = crop.resize((L.WORK, L.WORK), Image.LANCZOS); s = L.WORK
    mode = body.get("mode")
    if mode not in ("faithful", "artistic"): mode = "faithful"
    pad = float(body.get("pad") or 1.12)
    r_frac = L.iris_radius_frac(pad)
    crop = L.mask_disk(crop, pad)
    source = crop                       # the deglared crop as it arrived: the colour reference for the QA below
    used_sr = bool(body.get("used_sr"))
    if s < L.SR_MAX_SIDE:
        crop = L.sr_x4(crop); used_sr = True
    base = crop.resize((L.WORK, L.WORK), Image.LANCZOS)
    draw, retry = _draw(mode, base, source, r_frac, pad), {}
    if RETRY_ON and draw.prof is not None and _failing(draw.prof) & set(RETRY_RULES):
        draw, retry = _retry(draw, mode, base, source, r_frac, pad)
    out, clean, prof, prof_ms, fid, fallback, qa = draw
    rv = REV.reveal_for(source, out, pad=pad)    # the Reveal's numbers (about 0.5 s) and the display copy as the Reveal shows it, its watermark on this padding's iris disc; {"params": None} when unmeasured
    prot = P.protect(out, clean, profile=prof)
    if rv["image"] is not None:
        prot["image"] = REV.display_b64(rv["image"])    # the same watermark, over the restoration with its eyelid hidden and its pupil black
    res = {"ok": True, "mode": mode, **prot, "profile": _public(prof, clean), "fidelity": round(fid, 3),
           "used_sr": used_sr, "fallback": fallback, "seconds": round(time.time() - t0, 1), "qa": qa}
    if rv["params"] is not None:
        res["reveal"] = rv["params"]
    if retry:                           # only when a rule failed: ran (a second restoration was made and compared), kept (which one), the note's codes and numbers
        res["retry"] = {"ran": retry["code"] in ("kept1", "kept2"), "kept": "second" if retry["code"] == "kept2" else "first", **retry}
    # optional training memory (only with consent and when storage is configured)
    if body.get("consent") and body.get("session"):
        sid = L.safe_segment(body["session"])
        meta = {"session": sid, "mode": mode, "fidelity": res["fidelity"], "used_sr": used_sr, "fallback": fallback,
                "input_px": s, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "meta": body.get("meta") or {}}
        u1 = L.store(f"eyes/{sid}/crop_{s}px.jpg", L.pil_bytes(L.b64_to_pil(body["crop"]), "JPEG", 95), "image/jpeg")
        u2 = L.store(f"eyes/{sid}/{mode}.jpg", L.pil_bytes(out, "JPEG", 93), "image/jpeg")
        L.store(f"eyes/{sid}/{mode}.json", json.dumps(meta).encode(), "application/json")
        res["stored"] = bool(u1 and u2)
    E.record("enhance", mode=mode, qa_ok=bool(qa.get("ok")), ring_de00=qa.get("ring_de00"), fallback=fallback, used_sr=used_sr, fidelity=res["fidelity"],
             reveal=rv["code"], **({"reveal_ms": rv["ms"]} if rv["params"] is not None else {}), **_codes(prof, prof_ms), **_retry_codes(retry))
    return res

def handle(req): L.run(req, enhance)

class handler(BaseHTTPRequestHandler):
    def do_POST(self): handle(self)
