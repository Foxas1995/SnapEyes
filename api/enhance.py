# -*- coding: utf-8 -*-
"""POST /api/enhance  {crop: b64 clean iris square, mode: "faithful"|"artistic", pad, session, consent, meta}
faithful: Real-ESRGAN x4 for small crops -> Gemini restoration with thinking -> fidelity guard.
artistic: Gemini macro re-interpretation (beautiful, not pixel-faithful)."""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import BaseHTTPRequestHandler
from PIL import Image
from _lib import iris as L

def enhance(body):
    t0 = time.time()
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
    res = {"ok": True, "mode": mode, "image": L.pil_to_b64(out, "JPEG", 93), "fidelity": round(fid, 3), "used_sr": used_sr,
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
    return res

def handle(req): L.run(req, enhance)

class handler(BaseHTTPRequestHandler):
    def do_POST(self): handle(self)
