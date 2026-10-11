# -*- coding: utf-8 -*-
"""The circle overshoot guard of api/analyze.py: a limbus fit that runs off the photo is refitted inside a sane radius.

Why. iris.refine_circle() maximises the radial intensity gradient over 49 centres and radii 0.82 to 1.22 x the vision
box's r0. Where a candidate circle runs off the photo its missing samples are dropped per radius (np.nanmean), so the
profile at those radii is the mean of only the sector still inside the photo, and a saturated reflection on the limbus
of that sector makes a step stronger than the real limbus. The fit then snaps to a circle much larger than the iris,
mostly outside the photo. Test photo 22 (a macro that fills the frame, a reflection on the right limbus): in 8 of 14
fits the circle came out 16 to 18 % larger than the vision circle with 8.5 % of its disc outside the photo (the other
6 fits found the true limbus, r 1.05 to 1.08 x r0, nothing outside). The client cuts its crop from this circle with
black where the photo ends, the image model paints that black void as sclera and lid, the colour lock turns the paint
grey (a grey crescent and a vertical cut at the side of the photo, 6 of 6 renders of the big circle against 0 of 12 of
the repaired one), the lower lid's skin and lashes inside the disc feed deglare's fibre donors (the X), and the eyelid
gate read 11.1 to 11.8 on 4 of the 8 big circles (line 11.0) and blocked a photo that is fine.

What. guard() is called on every fit and stays quiet unless BOTH of these hold (each one is a measurement):
  1. the fitted disc lies outside the photo by at least NEW_VOID_PCT percent of its area MORE than the vision circle
     does (the vision box is cut from the same photo, so its circle is the honest baseline for how much of the iris
     the photo really lacks; a fit that adds a void of its own is the artefact);
  2. the fitted circle locks on an iris (iris.iris_lock_score): a circle that does not lock is never cropped.
Then the limbus is searched again from the same start with the radius cap RADIUS_CAP x r0 (same maths, same centres,
+30 to 70 ms), and that circle is taken when it locks and adds less than REPAIR_ADDED_MAX points of void; failing that
the vision circle itself when that locks; failing that the fit is left as it was (the guard never turns a locked photo
into an unlocked one). Quiet means the function returns its input numbers untouched, so every photo it does not fire on
gets exactly the circle it got before.

There is deliberately NO test on the fitted radius against the vision radius. The first version had one (ratio >= 1.15)
and it was brittle in both directions, because the vision box radius itself moves between calls (per photo the largest
deviation from its median over 6 to 14 real replies: median 1.2 %, 90th percentile 3.5 %, 4 % of the photos above 6 %).
With the box start moved by +-3 % the ratio test missed 6 of 16 overshooting fits of photo 22 (the same circle reads
ratio 1.095 to 1.145 when r0 is 3 to 6 % larger), and with r0 6 % too small it fired on 11 correct fits of photo 08
(ratio 1.157 to 1.175 for a circle that is right) and shrank them by 6 to 17 %. The added void does not depend on r0
that way: over 59 fits that could fire (real, synthetic and r0 / centre jitter) every overshooting fit adds 5.3 points
or more (41 of 41 fire) and every correct fit adds 5.2 or less.

Calibration (wave-q3/artifacts/A/work and A/verify: replay.py, margins.py, jitter.py, synth.py). 660 fits (53 photos
with an iris found, 6 to 14 cached real vision replies each, both box readings) plus 400 fits on 100 synthetic photos
(real photos cropped so the iris runs off the left edge by 5, 15 or 30 % of r, or framed tightly on all four sides like
photo 22, each with and without a painted reflection on the right limbus), plus 3975 fits of the same real photos with
the box start moved (r0 x 0.94 to 1.06, centre +-0.04 r0). The raw circle of each overshoot is 0.10 to 0.17 r off the
reference (the median of that photo's quiet fits, or the known truth) and 5 to 15 % too big; the repaired one is within
0.07 r in position and 4 % in radius. The nearest fits that do not fire: a correctly fitted cut iris of the synthetic
set adds 4.0 to 4.5 points, a correct fit of photo 08 with a 6 % undersized box adds 5.2.
"""
import json
import os
import numpy as np

# SNAPEYES_CIRCLEGUARD=off (or 0 / false / no) switches the guard off: the fit is then refine_circle's, exactly as before. Read once at
# import, like SNAPEYES_DEGLARE_MODEL, and BOM safe (a value pasted with a byte order mark still reads).
ON = (os.environ.get("SNAPEYES_CIRCLEGUARD") or "on").strip().lstrip("\ufeff").lower() not in ("off", "0", "false", "no")

NEW_VOID_PCT = 5.0       # points of the fitted disc outside the photo, beyond what the vision circle has outside
REPAIR_ADDED_MAX = 3.5   # the refit is taken when it adds less void than this over the vision circle
RADIUS_CAP = 1.12        # the refit's radius search ends here (x the vision radius); refine_circle's own end is 1.22
_GRID_N = 96             # the disc is sampled on a 96 x 96 grid: 0.1 ms, within 1 percentage point of the exact area


def _disc_grid():
    u = (np.arange(_GRID_N) + 0.5) / _GRID_N * 2 - 1
    gx, gy = np.meshgrid(u, u)
    m = gx * gx + gy * gy <= 1
    return gx[m], gy[m]


_GX, _GY = _disc_grid()


def disc_out_pct(cx, cy, r, W, H):
    """Percent of the disc (cx, cy, r) that lies outside the photo [0, W-1] x [0, H-1], all in the same pixels.
    Deterministic; refine_circle treats a sample outside that box as missing."""
    px = cx + _GX * r
    py = cy + _GY * r
    return 100.0 * float(((px < 0) | (px > W - 1) | (py < 0) | (py > H - 1)).mean())


def guard(L, g, c0, cref):
    """(cx, cy, r, info). g is the gray working copy the circle was fitted on, c0 = (cx, cy, r0) the vision circle and
    cref = (cx, cy, r) what refine_circle returned, all in g's pixels. info is None when the guard stayed quiet (then
    the returned circle is cref, the very same numbers); else a small dict for the capture log. A failure of the guard
    itself is logged and leaves the fit as it was: it can cost no one the analysis. SNAPEYES_CIRCLEGUARD=off: always quiet."""
    if not ON:
        return cref[0], cref[1], cref[2], None
    try:
        return _guard(L, g, c0, cref)
    except Exception as e:  # noqa
        print("snapeyes overshoot " + json.dumps({"error": L._scrub(repr(e))[:160]}), flush=True)
        return cref[0], cref[1], cref[2], None


def _guard(L, g, c0, cref):
    cx0, cy0, r0 = c0
    cx, cy, r = cref
    if not r0 > 0:
        return cx, cy, r, None
    H, W = g.shape
    out = disc_out_pct(cx, cy, r, W, H)
    if out < NEW_VOID_PCT:                       # the added void cannot exceed the void itself: the usual, 0.1 ms exit
        return cx, cy, r, None
    out0 = disc_out_pct(cx0, cy0, r0, W, H)
    if out - out0 < NEW_VOID_PCT:
        return cx, cy, r, None
    if not L.iris_lock_score(g, cx, cy, r)[0]:
        return cx, cy, r, None
    c2 = L.refine_circle(g, cx0, cy0, r0, hi=RADIUS_CAP)
    how = "capped"
    if not (L.iris_lock_score(g, *c2)[0] and disc_out_pct(c2[0], c2[1], c2[2], W, H) - out0 < REPAIR_ADDED_MAX):
        c2, how = (cx0, cy0, r0), "vision"
        if not L.iris_lock_score(g, *c2)[0]:
            return cx, cy, r, None
    return c2[0], c2[1], c2[2], {"out_pct": round(out, 1), "added_pct": round(out - out0, 1), "ratio": round(r / r0, 3),
                                 "fix": how, "r_after": round(c2[2] / r, 3)}
