# -*- coding: utf-8 -*-
"""POST /api/enhance  {crop: b64 clean iris square, mode: "faithful"|"artistic", pad, session, consent, meta}
faithful: Real-ESRGAN x4 for small crops -> Gemini restoration with thinking -> fidelity guard.
artistic: Gemini macro re-interpretation (beautiful, not pixel-faithful).
The page never gets the clean restoration (api/_lib/preview.py): "image" is an 800 px display copy with the preview
watermark across the iris, "sealed" the clean 1024 px JPEG encrypted with the server's key (what /api/compose and the
order draft take back), "sealed_sizes" the clean iris at the sides /api/compose is sent for 3-8 eyes, sealed too.
POST /api/enhance  {sample: true, image: b64}: the AI-generated sample eye's prepared restoration (SAMPLE_SHA256) comes
back the same way, with no ticket and no model call."""
import os, sys, json, time, base64, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import BaseHTTPRequestHandler
from PIL import Image
from _lib import iris as L
from _lib import events as E   # the admin panel's usage events (no personal data)
from _lib import preview as P

# sha256 of public/assets/sample_eye_blue_restored.jpg, the sample eye's restoration the page ships (made once by the
# live engine, 2026-09-29). Replace the file and this changes with it; the page then falls back to the studio.
SAMPLE_SHA256 = "7e681ceca21955127d41cb6c899c4f5dd708819ea872a9dc305f8d0cce3e6cb7"
SAMPLE_B64_MAX = 600_000

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
    return {"ok": True, "mode": "artistic", "sample": True, **P.protect(L.b64_to_pil(s), raw)}

def enhance(body):
    t0 = time.time()
    if body.get("sample") is True:
        return sample(body)
    if not L.check_ticket(body.get("ticket")):
        raise PermissionError("expired_or_missing_ticket")
    crop = L.b64_to_pil(body["crop"])
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
    fallback = False
    if mode == "artistic":
        out = L.gemini_image(L.PROMPT_ARTISTIC, base)
        # this is the product now, so the colour is locked all the way to the client's own photo:
        # the model may sculpt structure and light, it may not decide what colour their eye is
        out = L.chroma_lock(out, base)
        out = L.pupil_lock(out, base, r_frac)   # nor how wide their pupil is: no iris where the photo shows none
        fid = L.ssim_lowfreq(base, out, r_frac)
    else:
        out = L.gemini_image(L.PROMPT_ENHANCE, base, thinking="high")
        out = L.chroma_lock(out, base)   # the model restores structure; the colour stays the client's own
        out = L.pupil_lock(out, base, r_frac)
        fid = L.ssim_lowfreq(base, out, r_frac)
        if fid < L.FIDELITY_FLOOR:
            out, fallback = base, True
    out = out.resize((L.WORK, L.WORK), Image.LANCZOS)
    # colour QA: how far the render moved the iris colour from the deglared crop it was made from. The pupil
    # is only made neutral later, by the grade in /api/compose, so it is checked there. Logged, never blocking.
    qa = L.colour_qa("enhance", result=out, source=source, r_frac=r_frac)
    # the clean restoration exactly as the page used to receive it (JPEG q93): sealed, never shown. The order's preview
    # and master_eye's preview_sha are these bytes, as before
    clean = base64.b64decode(L.pil_to_b64(out, "JPEG", 93))
    res = {"ok": True, "mode": mode, **P.protect(out, clean), "fidelity": round(fid, 3), "used_sr": used_sr,
           "fallback": fallback, "seconds": round(time.time() - t0, 1), "qa": qa}
    # optional training memory (only with consent and when storage is configured)
    if body.get("consent") and body.get("session"):
        sid = L.safe_segment(body["session"])
        meta = {"session": sid, "mode": mode, "fidelity": res["fidelity"], "used_sr": used_sr, "fallback": fallback,
                "input_px": s, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "meta": body.get("meta") or {}}
        u1 = L.store(f"eyes/{sid}/crop_{s}px.jpg", L.pil_bytes(L.b64_to_pil(body["crop"]), "JPEG", 95), "image/jpeg")
        u2 = L.store(f"eyes/{sid}/{mode}.jpg", L.pil_bytes(out, "JPEG", 93), "image/jpeg")
        L.store(f"eyes/{sid}/{mode}.json", json.dumps(meta).encode(), "application/json")
        res["stored"] = bool(u1 and u2)
    E.record("enhance", mode=mode, qa_ok=bool(qa.get("ok")), ring_de00=qa.get("ring_de00"), fallback=fallback, used_sr=used_sr, fidelity=res["fidelity"])
    return res

def handle(req): L.run(req, enhance)

class handler(BaseHTTPRequestHandler):
    def do_POST(self): handle(self)
