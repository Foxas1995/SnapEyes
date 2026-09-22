# -*- coding: utf-8 -*-
"""POST /api/deglare  {crop: b64 square iris crop (black outside), pad}
Detects specular reflections; if present, asks the image model to rebuild only that area and blends it back."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import BaseHTTPRequestHandler
from PIL import Image
from _lib import iris as L

def deglare(body):
    if not L.check_ticket(body.get("ticket")):
        raise PermissionError("expired_or_missing_ticket")
    crop = L.b64_to_pil(body["crop"])
    if crop.size[0] != crop.size[1]:
        s = min(crop.size); crop = crop.crop((0, 0, s, s))
    if crop.size[0] > L.WORK: crop = crop.resize((L.WORK, L.WORK), Image.LANCZOS)
    pad = float(body.get("pad") or 1.12)
    crop = L.mask_disk(crop, pad)
    used_sr = False
    if crop.size[0] < L.SR_MAX_SIDE:
        # small iris: faithful x4 upscale first, so the reflection patch is rebuilt with more context
        crop = L.sr_x4(crop); used_sr = True
        if crop.size[0] > L.WORK: crop = crop.resize((L.WORK, L.WORK), Image.LANCZOS)
    S = crop.size[0]; r_px = L.iris_radius_frac(pad) * S
    boxes = [[c * S for c in b] for b in (body.get("glare_boxes") or []) if isinstance(b, (list, tuple)) and len(b) == 4]
    hard, feather, pct = L.glare_mask(crop, r_px, boxes)
    if pct < L.GLARE_MIN_PCT:
        return {"ok": True, "glare_pct": round(pct, 2), "changed": False, "used_sr": used_sr, "crop": L.pil_to_b64(crop, "JPEG", 95)}
    prefilled = L.mirror_prefill(crop, feather)
    try:
        patch = L.gemini_image(L.PROMPT_DEGLARE, prefilled)
        clean = L.composite(crop, patch, feather)
    except Exception:
        clean = prefilled
    return {"ok": True, "glare_pct": round(pct, 2), "changed": True, "used_sr": used_sr, "crop": L.pil_to_b64(clean, "JPEG", 95)}

def handle(req): L.run(req, deglare)

class handler(BaseHTTPRequestHandler):
    def do_POST(self): handle(self)
