# -*- coding: utf-8 -*-
"""POST /api/deglare  {crop: b64 square iris crop, as the client cuts it (not masked), pad, pupil_r, glare_boxes}
Detects specular reflections and eyelids (skin, lash line, lashes, lid shadow inside the iris circle). A reflection
is rebuilt by the image model and blended back; an eyelid is filled from the same person's iris at the same radius
(mirror_prefill), never from the model: the model's lid patches were a different iris (a new colour band, a straight
two-tone seam, sharper than the photo), while /api/enhance re-renders the whole disc in one pass and restores the
fibres over the fill without a seam.
Reply: {ok, glare_pct, lid_pct, changed, used_sr, pupil_overlap, crop}. glare_pct and lid_pct are shares of the iris
disk, measured separately; with no eyelid found (lid_pct 0) the result is exactly the glare-only one."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import BaseHTTPRequestHandler
import numpy as np
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
    raw = crop                          # the square as sent: what lies outside the circle tells a lid from iris
    crop = L.mask_disk(crop, pad)
    used_sr = False
    if crop.size[0] < L.SR_MAX_SIDE:
        # small iris: faithful x4 upscale first, so the reflection patch is rebuilt with more context
        crop = L.sr_x4(crop); used_sr = True
        if crop.size[0] > L.WORK: crop = crop.resize((L.WORK, L.WORK), Image.LANCZOS)
    S = crop.size[0]; r_px = L.iris_radius_frac(pad) * S
    boxes = [[c * S for c in b] for b in (body.get("glare_boxes") or []) if isinstance(b, (list, tuple)) and len(b) == 4]
    parts = L._glare_core_halo(crop, r_px, boxes)      # glare_mask's core and halo, read again by glare_extent below
    hard, feather, pct = L.glare_mask(crop, r_px, boxes, parts=parts)
    mask_src = crop
    try:
        pr = float(body.get("pupil_r") or 0)
    except Exception:
        pr = 0.0
    pupil_ok = 0.04 <= pr <= 0.34
    # eyelids: found on the unmasked square, drawn at the working size, the pupil left out; counted apart from the
    # glare. Only with the analyze pupil (every analyzed photo has one): read from the crop instead, a wide pupil came
    # out at a third of its size (19: 0.16 for 0.46) and the fill reached into it. A crop without a lid takes exactly
    # the glare-only path below
    lid_hard, lid_feather, lid_pct = None, None, 0.0
    if pupil_ok:
        lid_hard, lid_feather, lid_pct = L.lid_mask(raw, L.iris_radius_frac(pad) * raw.size[0], glare_hard=hard,
                                                    size=S, pupil_rho=pr / L.iris_radius_frac(pad))
    # a reflection on the pupil is not recoverable iris detail; rebuild that part as darkness ourselves and
    # keep it out of the model's mask, or it paints window frames inside the eye
    pupil_overlap, pupil_changed = 0.0, False
    if pupil_ok:
        pr_px = pr * S
        dark, pupil_overlap = L.pupil_fill(crop, pr_px, hard, r_frac=L.iris_radius_frac(pad))
        pupil_changed, crop = dark is not crop, dark     # a glint on the pupil, or a haze over all of it
        hard, feather = L.drop_pupil(hard, feather, pr_px)
        pct = 100.0 * float((hard > 0).sum()) / max(1.0, float((hard.size)))
        pct = round(pct * (S * S) / max(1.0, 3.1416 * r_px * r_px), 2)
    base = crop
    if lid_pct > 0:
        # the lid area from the same radius of this iris: glare and lid pixels do not donate, and a lid too wide for
        # the near donors borrows from further round the circle
        # (the fill then goes in feathered in tone as well as in alpha: lid_composite)
        prho = pr / L.iris_radius_frac(pad)
        filled = L.mirror_prefill(crop, np.maximum(feather, lid_feather), L.LID_EXTRA_DONORS)
        base = L.composite(crop, filled, lid_feather)
        if L.lid_drift(crop, base, lid_hard, hard, r_px) > L.LID_DRIFT_MAX:
            base, lid_pct = crop, 0.0           # no clean iris to borrow from: leave the lid to the grade, as before
    if pct < L.GLARE_MIN_PCT:
        if lid_pct > 0:
            base = L.lid_composite(crop, filled, lid_hard, lid_feather, r_px, prho, glare_hard=hard)
        return {"ok": True, "glare_pct": round(pct, 2), "lid_pct": round(lid_pct, 2),
                "changed": pupil_changed or lid_pct > 0, "used_sr": used_sr,
                "pupil_overlap": round(pupil_overlap, 3), "crop": L.pil_to_b64(base, "JPEG", 95)}
    # the reflection holes: the whole glint with its halo, outline ring and soft shoulder (glare_extent), never less than
    # glare_mask's. The gate above and every lid and pupil decision still read glare_mask's, so a crop below the gate is
    # exactly as before. The holes get the lid path's kind of fill (glare_fill: the tone of the iris round them, single
    # donors' fibres): it is the model's input, and what stays wherever patch_guard throws the reply out
    prho = pr / L.iris_radius_frac(pad) if pupil_ok else None
    lid_glare = hard                    # the lid composite reads glare_mask's, as before: the lid itself is unchanged
    hard, feather, _ = L.glare_extent(mask_src, r_px, boxes, pupil_px=pr * S if pupil_ok else 0.0,
                                      avoid=lid_hard if lid_pct > 0 else None, parts=parts)
    if pupil_ok:
        hard, feather = L.drop_pupil(hard, feather, pr * S)
    if lid_pct <= 0:
        prefilled = L.glare_fill(crop, feather, hard, r_px, prho)
        try:
            patch = L.gemini_image(L.PROMPT_DEGLARE, prefilled)
            # a reply that redrew the whole iris is not composited: its holes take the fill (patch_guard)
            clean = L.patch_guard(L.composite(crop, patch, feather), prefilled, patch, feather, r_px)
        except Exception:
            clean = prefilled
    else:
        # the model sees the lid already filled and rebuilds only the reflections: the glare is composited exactly as
        # without a lid, then the lid fill goes on top, so the model's pixels never land in the lid and no photo glare
        # survives where a reflection meets the lid's soft edge (21: a bright line along the lower lid). The holes off
        # the lid take glare_fill, blended once onto the lid fill; the lid keeps its own fill
        off_lid = feather * (1.0 - lid_feather)
        prefilled = L.glare_fill(crop, off_lid, ((hard > 0) & (lid_feather < 0.5)).astype(np.uint8), r_px, prho,
                                 avoid=lid_hard, base=filled, hole=np.maximum(feather, lid_feather))
        try:
            patch = L.gemini_image(L.PROMPT_DEGLARE, prefilled)
            hole = np.maximum(feather, lid_feather)
            glared = L.patch_guard(L.composite(crop, patch, feather), prefilled, patch, hole, r_px,
                                   share=feather / np.maximum(hole, 1e-6))
        except Exception:
            glared = prefilled                  # as without a lid: the fill borrowed from the same radius everywhere
        clean = L.lid_composite(glared, filled, lid_hard, lid_feather, r_px, prho, photo=crop, glare_hard=lid_glare)
    return {"ok": True, "glare_pct": round(pct, 2), "lid_pct": round(lid_pct, 2), "changed": True, "used_sr": used_sr,
            "pupil_overlap": round(pupil_overlap, 3), "crop": L.pil_to_b64(clean, "JPEG", 95)}

def handle(req): L.run(req, deglare)

class handler(BaseHTTPRequestHandler):
    def do_POST(self): handle(self)
