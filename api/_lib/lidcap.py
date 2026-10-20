# -*- coding: utf-8 -*-
"""The thin lid that iris.lid_mask leaves alone, filled like any lid inside /api/deglare (the owner, 2026-10-20: "the restoration added brown
pigment where my eyelid covered the iris, and my iris has none there").

Where the brown came from. iris.lid_mask finds a lid by a strong margin (a cap clearly lighter or darker than the iris below it) and leaves thin
rim lids alone on purpose (its docstring: 02, 07, 15 ... the owner's own 215106 and 215208). On a light iris (blue, grey, green) a thin upper or
lower lid over the rim is exactly that case: the lid skin is about as light as the iris, so no margin passes, lid_pct is 0, and the skin and the
lash line go to the image model as they are. /api/enhance then draws iris fibres over them and iris.chroma_lock keeps the colour the photo has
there, which is the skin's: a warm brown or pink band in a blue or grey iris. Measured on the stored chain of 2026-10-12 (the clean previews of
wave-l1; the cap of coverage.py; the reference is the iris at least 60 degrees round from the cap at the same radius; medians inside the cap): on
the blue, grey and green irises the restoration's cap sat 10 to 16 a*b* units off its own iris (cm013 16.4 at hue 64, cs100 12.6 at hue 26, cm009
12.7, cs024 13.0, against an iris of chroma 1.2 to 3.6), as far as the photo's skin was (12.7 to 16.0 in the photo); on a brown iris the skin is
close to the iris' own colour and the same step reads 4.5 (cm014), which is why the brown test photos never showed it. The lid remnant fill (A21,
rimfix.py) never ran on these (it needs a lid fill), nor the void fill (no photo edge), and the colour check only measures (it never moves a pixel).
The owner's family photos d02, d04 and d05 (a blue-grey iris like his, a lid over the top) read lid_pct 0 as well.

What this does. analyze.py already measures a lid as a cap from the rim (api/_lib/coverage.py: lid skin carrying on across the rim, with texture,
not the white of the eye and not a reflection; it holds back a photo whose cap passes EYELID_BLOCK_PCT). When lid_mask finds no lid, the same
measurement is read on the square deglare gets (coverage._lids: the largest lid and the largest one at least 90 degrees from it), and each cap
of CAP_PCT[0] to CAP_PCT[1] of the disc becomes a lid mask: the iris beyond the cap's margin line (CAP_REACH further in, for the lash line right
under it), and, because a lid's margin is curved where the cap's line is straight, the lid pixels coverage.py itself classifies (skin, or the lash
line and lashes: much darker than the iris at their radius), and skin its block rule does not need to see (a skin hue well off the iris' own
colour at its radius: CAP_WARM), that lie within CAP_ARC degrees of the cap, outside CAP_INNER, and touch the cap; a lid pixel near the rim
carries its column out to the rim. Never inside 0.25 iris radii nor the pupil, to 1.02 radii, with lid_mask's own soft
edge. deglare then takes the path every found lid takes: the fill from this iris at the same radius (mirror_prefill with the far donors), the drift
guard (iris.lid_drift: a fill that moved the colour off the iris is not used), the tone at the edge and the fibre band from single donors
(iris.lid_composite), the remnant (rimfix.lid_remnant). The model then gets the iris' own colours where the lid was, and chroma_lock keeps them.
A crop with no cap, or a lid lid_mask found, takes exactly the path it took before (byte for byte). A failure leaves the crop as it was.
SNAPEYES_LIDCAP=off (or 0 / false / no; read once at import, BOM safe) switches it off. Cost: coverage's measurement, 40 to 75 ms, only when
lid_mask found nothing; a cap that is filled costs the lid path's time (about 1 s at 1024 px)."""
import os, math
import numpy as np
from . import iris as L
from . import coverage as CV


def _switch(name):
    """True unless the environment variable `name` says off, 0, false or no (BOM safe)."""
    return (os.environ.get(name) or "on").strip().lstrip("\ufeff").lower() not in ("off", "0", "false", "no")


CAP_ON = _switch("SNAPEYES_LIDCAP")
CAP_PCT = (0.5, 20.0)        # a cap is filled from the first share of the disc (percent) to the second; a larger one is no thin lid
CAP_REACH = 0.02             # the straight part reaches this far (iris radii) past the cap's margin line: the lash line right under it
CAP_ARC = 100.0              # the curved part: lid pixels within this many degrees of the cap's direction...
CAP_INNER = 0.60             # ...outside this radius (iris radii)...
CAP_RIM = (0.84, 0.96)       # ...and a lid pixel in this band carries its 3-degree column out to the rim
CAP_WARM = (6.0, 6.0)        # ...and lid skin coverage's block rule does not need: a skin hue (coverage.SKIN_HUE) at least the first in chroma and the
                             # second in a*b* off the iris at its radius (the photo's own colours, no light correction): a pink lower lid on a grey iris
CAP_GROW = 1                 # the lid pixels are closed and grown by this many pixels of coverage's square (0.016 iris radii each)
CAP_MAX_GROWTH = 3.0         # the curved part may make the mask at most this many times the straight part (else only the straight part)


def _grid(Q, flags):
    """The flags of coverage's ring pixels (Q["Xu"], Q["Yu"]) drawn back on its SIDE x SIDE square (False elsewhere)."""
    n = CV.SIDE
    k = n / (2.0 * CV.PAD)
    px = np.clip(np.floor(Q["Xu"] * k + n / 2.0).astype(int), 0, n - 1)
    py = np.clip(np.floor(Q["Yu"] * k + n / 2.0).astype(int), 0, n - 1)
    g = np.zeros((n, n), bool)
    g[py[flags], px[flags]] = True
    return g


def _curved(Q, tilt, core):
    """The lid pixels of the cap from `tilt` that touch its straight part `core` (both on coverage's square): coverage's own classes."""
    cl = CV._classes(Q, tilt)
    if cl is None:
        return np.zeros_like(core)
    skin, dark = cl
    ang = np.degrees(np.arctan2(Q["Yu"], Q["Xu"])) % 360.0
    off = np.abs((ang - tilt + 180.0) % 360.0 - 180.0)
    near = off <= CAP_ARC
    # the iris at each radius on the photo's own colours (the sectors coverage reads for this cap, reflections left out)
    lu, rb = Q["lu"], Q["rb"]
    away = (off >= CV.REF_AWAY) & ~Q["refl"]
    nb = int(rb.max()) + 1
    ref = np.stack([CV._median_by(rb[away], lu[away, c], nb) for c in range(3)], 1)
    ref = CV._fill(ref)
    warm = np.zeros(len(lu), bool)
    if ref is not None:
        C = np.hypot(lu[:, 1], lu[:, 2])
        hue = np.degrees(np.arctan2(lu[:, 2], lu[:, 1]))
        dab = np.hypot(lu[:, 1] - ref[rb, 1], lu[:, 2] - ref[rb, 2])
        warm = (hue >= CV.SKIN_HUE[0]) & (hue <= CV.SKIN_HUE[1]) & (C >= CAP_WARM[0]) & (dab >= CAP_WARM[1]) & ~Q["refl"]
    lid = _grid(Q, (skin | dark | warm) & near & (Q["ru"] > CAP_INNER))
    for _ in range(CAP_GROW):
        lid = L._dilate8(lid)
    lab, n = L._components(lid | core)
    if n == 0:
        return np.zeros_like(core)
    ids = np.unique(lab[core & (lab > 0)])
    return np.isin(lab, ids[ids > 0])


def cap_mask(raw, pad, pupil_r, size):
    """(hard uint8 0/255, feathered float32 0..1, pct of the disc, caps) of the thin lids coverage.py reads on raw (the square as the client sent
    it, its circle centred, radius iris_radius_frac(pad) of its side), drawn at size x size like iris.lid_mask's masks; caps: [(tilt, pct)] of the
    caps used. None when the switch is off, nothing is found, or anything fails. pupil_r: the analyze pupil, a share of the crop side (deglare's
    body pupil_r)."""
    if not CAP_ON:
        return None
    try:
        n = raw.size[0]
        r = n * L.iris_radius_frac(pad)
        Q = CV._prep(raw, n / 2.0, n / 2.0, r, pupil_r) if r >= 4 else None
        got = CV._lids(Q) if Q is not None else None
        if got is None:
            return None
        out, i1, i2 = got
        caps = [(float(out[i][0]), float(out[i][2]), float(out[i][1])) for i in ([i1] if i2 == i1 else [i1, i2])]
        caps = [c for c in caps if CAP_PCT[0] <= c[2] <= CAP_PCT[1]]
        if not caps:
            return None
        g = CV.SIDE
        ax = (np.arange(g) + 0.5) / (g / (2.0 * CV.PAD)) - CV.PAD          # coverage's square in iris radii
        GX, GY = np.meshgrid(ax, ax)
        Grho = np.hypot(GX, GY)
        straight = np.zeros((g, g), bool)
        lid = np.zeros((g, g), bool)
        for tilt, depth, _ in caps:
            c, s = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
            core = ((GX * c + GY * s) > CV.RIM - depth - CAP_REACH) & (Grho < 1.02)
            straight |= core
            lid |= core | _curved(Q, tilt, core)
        # a lid pixel near the rim carries its column out to the rim (coverage reads nothing past RIM)
        gang = (np.degrees(np.arctan2(GY, GX)) % 360.0 / 3.0).astype(int) % 120
        cols = np.zeros(120, bool)
        cols[np.unique(gang[lid & (Grho > CAP_RIM[0]) & (Grho < CAP_RIM[1])])] = True
        cols = cols | np.roll(cols, 1) | np.roll(cols, -1)
        lid |= cols[gang] & (Grho >= CAP_RIM[1]) & (Grho < 1.02)
        if lid.sum() > CAP_MAX_GROWTH * max(1, int(straight.sum())):
            lid = straight
        # drawn at the caller's size: the square of coverage is PAD iris radii each side, the caller's is 1 / (2 iris_radius_frac(pad))
        S = int(size)
        R = L.iris_radius_frac(pad) * S
        sx = (np.arange(S) - S / 2 + 0.5) / R
        X, Y = np.meshgrid(sx, sx)
        rho = np.sqrt(X * X + Y * Y)
        smooth = L._blur_f(lid.astype(np.float32), 0.8)                     # the square's pixel steps out before the threshold...
        fx = np.clip((X + CV.PAD) * (g / (2.0 * CV.PAD)) - 0.5, 0.0, g - 1.001)
        fy = np.clip((Y + CV.PAD) * (g / (2.0 * CV.PAD)) - 0.5, 0.0, g - 1.001)
        x0, y0 = fx.astype(int), fy.astype(int)
        ax_, ay_ = fx - x0, fy - y0
        m = (smooth[y0, x0] * (1 - ax_) * (1 - ay_) + smooth[y0, x0 + 1] * ax_ * (1 - ay_)     # ...and read between its pixels
             + smooth[y0 + 1, x0] * (1 - ax_) * ay_ + smooth[y0 + 1, x0 + 1] * ax_ * ay_) >= 0.5
        del fx, fy, x0, y0, ax_, ay_
        pupil_rho = float(pupil_r or 0.0) / L.iris_radius_frac(pad)
        keep = rho > max(0.25, pupil_rho * 1.04)
        m &= (rho < 1.02) & keep
        del X, Y
        disk = rho < 1.0
        pct = 100.0 * float((m & disk).sum()) / max(1.0, float(disk.sum()))
        if pct <= 0.0:
            return None
        soft = np.clip(2.0 * L._blur_f(m.astype(np.float32), max(1.0, L.LID_FEATHER * S / 2.0)), 0.0, 1.0)
        soft = (np.maximum(soft, m.astype(np.float32)) * keep).astype(np.float32)
        return (m * 255).astype(np.uint8), soft, pct, [(int(round(t)), round(p, 1)) for t, _, p in caps]
    except Exception:
        return None
