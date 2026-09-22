# -*- coding: utf-8 -*-
"""POST /api/analyze  {image: b64 (<=1600px), origWidth, origHeight}
Finds the iris, refines the limbus circle, measures size and sharpness, returns the crop geometry for the client."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import BaseHTTPRequestHandler
import numpy as np
from PIL import Image
from _lib import iris as L

def analyze(body):
    im = L.b64_to_pil(body["image"])
    W, H = im.size
    ow, oh = int(body.get("origWidth") or W), int(body.get("origHeight") or H)
    scale = ow / float(W)
    v = L.gemini_json(L.VISION_MODEL, L.PROMPT_VISION, im)
    if not v or v.get("found") is False or "iris_box" not in v:
        return {"ok": False, "reason": "no_eye", "message": "We could not find an eye in this photo. Fill the frame with one open eye and try again."}
    x1, y1, x2, y2 = v["iris_box"]
    bx = [x1 * W / 1000, y1 * H / 1000, x2 * W / 1000, y2 * H / 1000]
    cx, cy = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
    r0 = ((bx[2] - bx[0]) + (bx[3] - bx[1])) / 4
    # refine on a working copy where the iris radius is ~120px
    f = min(1.0, 120.0 / max(r0, 1))
    g = L.to_gray(im.resize((max(8, int(W * f)), max(8, int(H * f))), Image.LANCZOS))
    rcx, rcy, rr = L.refine_circle(g, cx * f, cy * f, r0 * f)
    cx, cy, r = rcx / f, rcy / f, rr / f
    crop = L.circular_crop(im, cx, cy, r)
    sharp = L.laplacian_var(crop)
    diam_orig = 2 * r * scale
    occl = float(v.get("iris_occluded_by_eyelids_percent") or 0)
    label = str(v.get("sharpness") or "")
    if diam_orig >= 500 and label != "blurry" and sharp >= 120 and occl <= 25: verdict = "good"
    elif diam_orig >= 300 and sharp >= 40 and occl <= 40: verdict = "ok"
    else: verdict = "weak"
    tips = []
    if diam_orig < 500: tips.append(f"Move closer or use 2x zoom: the iris is {int(diam_orig)} px, we want 500 px or more.")
    if label == "blurry" or sharp < 120: tips.append("Hold still and tap the iris on screen to focus before shooting.")
    if occl > 25: tips.append("Open the eye wide (lift the eyelid with a finger) so the whole iris is visible.")
    if v.get("glare_boxes"): tips.append("A reflection was found; we will remove it automatically.")
    msg = {"good": "Great capture. Real fibres are visible, we can restore them faithfully.",
           "ok": "Usable, but a closer or sharper shot would keep more of your real fibres.",
           "weak": "Too small or blurry for a faithful restoration. We can still make it beautiful, but the fibres will be interpreted."}[verdict]
    pad = 1.12; Sc = 2 * r * pad; ox, oy = cx - Sc / 2, cy - Sc / 2
    boxes = []
    for b in (v.get("glare_boxes") or []):
        try:
            gx1, gy1, gx2, gy2 = b
            boxes.append([(gx1 * W / 1000 - ox) / Sc, (gy1 * H / 1000 - oy) / Sc, (gx2 * W / 1000 - ox) / Sc, (gy2 * H / 1000 - oy) / Sc])
        except Exception:
            pass
    return {"ok": True, "iris": {"cx": cx / W, "cy": cy / H, "r": r / W}, "pad": pad, "glare_boxes_crop": boxes,
            "quality": {"diameter_px": int(diam_orig), "sharpness": round(sharp, 1), "sharpness_label": label, "occlusion_pct": occl,
                        "glare": bool(v.get("glare_boxes")), "verdict": verdict, "message": msg, "tips": tips},
            "preview": L.pil_to_b64(crop.resize((320, 320), Image.LANCZOS), "JPEG", 85)}

def handle(req): L.run(req, analyze)

class handler(BaseHTTPRequestHandler):
    def do_POST(self): handle(self)
