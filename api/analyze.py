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
    box = v.get("iris_box")
    ok_box = (isinstance(box, (list, tuple)) and len(box) == 4
              and all(isinstance(c, (int, float)) and c == c and abs(c) < 1e6 for c in box)
              and box[2] > box[0] and box[3] > box[1])
    if not ok_box:
        return {"ok": False, "reason": "no_eye",
                "message": "We could not find an eye in this photo. Fill the frame with one open eye and try again."}
    x1, y1, x2, y2 = box
    bx = [x1 * W / 1000, y1 * H / 1000, x2 * W / 1000, y2 * H / 1000]
    cx, cy = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
    r0 = ((bx[2] - bx[0]) + (bx[3] - bx[1])) / 4
    # the pupil is the one landmark a model gets right in a tight close-up: the iris is concentric with it,
    # so centring on the pupil survives an iris box that drifted onto the eyelid or the sclera
    pbox = v.get("pupil_box")
    pupil_px = None
    if (isinstance(pbox, (list, tuple)) and len(pbox) == 4
            and all(isinstance(c, (int, float)) and c == c for c in pbox)
            and pbox[2] > pbox[0] and pbox[3] > pbox[1]):
        px = ((pbox[0] + pbox[2]) / 2) * W / 1000
        py = ((pbox[1] + pbox[3]) / 2) * H / 1000
        prr = ((pbox[2] - pbox[0]) * W / 1000 + (pbox[3] - pbox[1]) * H / 1000) / 4
        # only trust it when it is plausibly a pupil inside this iris
        if prr < r0 * 0.75 and ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5 < r0 * 1.1:
            cx, cy, pupil_px = px, py, prr
    # refine on a working copy where the iris radius is ~120px
    f = min(1.0, 120.0 / max(r0, 1))
    g = L.to_gray(im.resize((max(8, int(W * f)), max(8, int(H * f))), Image.LANCZOS))
    rcx, rcy, rr = L.refine_circle(g, cx * f, cy * f, r0 * f)
    cx, cy, r = rcx / f, rcy / f, rr / f
    # sanity: a real iris is darker in the middle (pupil) than in its own ring. If it is not, the circle
    # landed on skin, sclera or an eyelid, and everything downstream would be built on a wrong crop.
    locked = L.iris_lock_ok(g, rcx, rcy, rr)
    crop = L.circular_crop(im, cx, cy, r)
    sharp = L.laplacian_var(crop)
    diam_orig = 2 * r * scale
    occl = float(v.get("iris_occluded_by_eyelids_percent") or 0)
    label = str(v.get("sharpness") or "")
    if not locked: verdict = "weak"
    elif diam_orig >= 500 and label != "blurry" and sharp >= 120 and occl <= 25: verdict = "good"
    elif diam_orig >= 300 and sharp >= 40 and occl <= 40: verdict = "ok"
    else: verdict = "weak"
    pad = 1.12; Sc = 2 * r * pad; ox, oy = cx - Sc / 2, cy - Sc / 2
    # the pupil, as a fraction of the square crop: a reflection landing here is rebuilt as darkness,
    # never handed to the image model
    pupil_r = None
    pb = v.get("pupil_box")
    if (isinstance(pb, (list, tuple)) and len(pb) == 4
            and all(isinstance(c, (int, float)) and c == c for c in pb) and pb[2] > pb[0] and pb[3] > pb[1]):
        pr = ((pb[2] - pb[0]) * W / 1000 + (pb[3] - pb[1]) * H / 1000) / 4
        pupil_r = max(0.04, min(0.34, pr / Sc))
    tips = []
    if diam_orig < 500: tips.append(f"Move closer or use 2x zoom: the iris is {int(diam_orig)} px, we want 500 px or more.")
    if label == "blurry" or sharp < 120: tips.append("Hold still and tap the iris on screen to focus before shooting.")
    if occl > 25: tips.append("Open the eye wide (lift the eyelid with a finger) so the whole iris is visible.")
    # a reflection sitting on the pupil hides nothing recoverable: say so instead of pretending to restore it
    on_pupil = False
    if pupil_r and v.get("glare_boxes"):
        pcx, pcy = (pb[0] + pb[2]) / 2, (pb[1] + pb[3]) / 2
        prad = max(pb[2] - pb[0], pb[3] - pb[1]) / 2
        for gb in v["glare_boxes"]:
            try:
                gcx, gcy = (gb[0] + gb[2]) / 2, (gb[1] + gb[3]) / 2
                if ((gcx - pcx) ** 2 + (gcy - pcy) ** 2) ** 0.5 < prad: on_pupil = True
            except Exception: pass
    if on_pupil:
        tips.append("The reflection sits on your pupil. Tilt your head or move the light to the side, or we will "
                    "have to rebuild the pupil as plain darkness.")
    elif v.get("glare_boxes"): tips.append("A reflection was found; we will remove it automatically.")
    if label != "sharp" or sharp < 120:
        tips.append("This came out soft. Use the back camera at 2x, tap the iris to focus, and keep the phone "
                    "steady; front cameras cannot focus at this distance at all.")
    if not locked:
        tips.insert(0, "We could not lock onto the round edge of your iris. Centre one eye in the frame with a "
                       "little space around it, and keep the eyelid out of the way.")
    msg = {"good": "Great capture. Real fibres are visible, we can restore them faithfully.",
           "ok": "Usable, but a closer or sharper shot would keep more of your real fibres.",
           "weak": "Too small or blurry for a faithful restoration. We can still make it beautiful, but the fibres will be interpreted."}[verdict]
    if not locked:
        msg = "We found an eye but could not lock onto the iris edge, so the crop would be off. Please take another photo."
    boxes = []
    for b in (v.get("glare_boxes") or []):
        try:
            gx1, gy1, gx2, gy2 = b
            boxes.append([(gx1 * W / 1000 - ox) / Sc, (gy1 * H / 1000 - oy) / Sc, (gx2 * W / 1000 - ox) / Sc, (gy2 * H / 1000 - oy) / Sc])
        except Exception:
            pass
    # a short-lived signed ticket: the paid endpoints refuse work without one, so a bare scripted loop
    # has to come through this (cheap) endpoint first instead of hitting the image model directly
    return {"ok": True, "ticket": L.mint_ticket("work"), "pupil_r": pupil_r,
            "iris": {"cx": cx / W, "cy": cy / H, "r": r / W}, "pad": pad, "glare_boxes_crop": boxes,
            "quality": {"diameter_px": int(diam_orig), "sharpness": round(sharp, 1), "sharpness_label": label, "occlusion_pct": occl,
                        "glare": bool(v.get("glare_boxes")), "locked": bool(locked),
                        "verdict": verdict, "message": msg, "tips": tips},
            "preview": L.pil_to_b64(crop.resize((320, 320), Image.LANCZOS), "JPEG", 85)}

def handle(req): L.run(req, analyze)

class handler(BaseHTTPRequestHandler):
    def do_POST(self): handle(self)
