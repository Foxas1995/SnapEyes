# -*- coding: utf-8 -*-
"""How much of the iris an eyelid covers, measured on the photo itself (api/analyze.py, the "eyelid" block).

When lid skin, the lash line or lashes lie over part of the iris (a shot at an angle, where the upper lid cuts across
the iris, or an eye not opened wide), the studio model paints iris fibres over the lid and the artwork looks fake: the
customer sees "through the eyelid" (the owner, 2026-09-29, Drive photos d02/d04/d05). The vision model's
iris_occluded_by_eyelids_percent cannot carry a block (0 for an angled lid wedge, 15-27 for one photo on different
calls) and the deglare lid fill needs a strong lid edge (lid_pct 0 on those photos), so this module measures it.

A lid enters the iris from the rim as a cap: everything beyond a lid margin that crosses the iris as a line. lid_cover()
looks for that cap from NDIR directions all round (a lid can come in at any angle once the phone is tilted), in strips
DT wide parallel to the margin, from the rim inward. Each pixel of the iris ring is compared with the iris itself at
the same distance from the centre, read in the 30-degree sectors at least REF_AWAY degrees from the cap's direction
(where that lid does not reach), after two corrections:
  - white balance on the white of the eye all round the iris (the most colourless light pixels just outside it), so a
    warm or cold cast does not move pink skin across the lines;
  - the light across the iris: each 10-degree sector's mid-ring offset from the iris (smoothed, clipped), read only on
    pixels of the iris's own hue (lid skin over a coloured iris is left out of it) and only taken out where a sector is
    lighter (a lit side of the iris), never added where it is darker (the shadow under a lid, or the lid itself).
A pixel is lid SKIN when it is much lighter (SKIN_DL) or redder (SKIN_DA) than that iris, with a skin colour (hue
SKIN_HUE, chroma SKIN_C); DARK (the lash line, lashes) when it is DARK_DL darker. Reflections (light and colourless,
anything lighter than SPEC_HOT, or sky blue) and the white of the eye inside the circle are neither: a strip that is
mostly reflection ends the cap (a lid is not a mirror), and white-of-eye pixels vote against a lid. The cap is s1
strips of skin from the rim, then at most DARK_STRIPS strips of lash line right under it, chosen to maximise the
pixels that agree (a strip counts when more than MAJ of it agrees). A cap is then kept only when it looks like a lid:
  - its rim arc outside the circle is not mostly the white of the eye (SCLERA_VETO): a circle over the sclera, or a
    lit side of the iris next to the white, is not a lid;
  - it holds real skin (at least 10 pixels), and that skin carries on across the rim: its a*b* is within CONT_AB of
    the lid outside the circle beside it (a lid over the iris is the lid outside it; a lit iris or a window reflection
    next to a lid is not);
  - its skin has texture (lid skin, its margin and its lashes do): a smooth patch is a reflection or a veil.
Among the directions, each local best (by score) stands for one lid; its area is the largest cap within NEAR degrees
of it scoring at least NEAR_FRAC as well.

Returned: wedge_pct, the largest single lid as a share of the iris disc (the number the gate reads), and covered_pct,
that lid and the largest one at least 90 degrees away together. Calibrated on 50 photos with an iris labelled by eye
(wave-lid/labels.json) and on synthetic changes of them (window and warm reflections, veils, light ramps, caustics,
contrast, saturation and sharpening edits, exposure, casts, re-encoding, circle moves, rotations of real lids, real lids
pasted on clean eyes): see analyze.py EYELID_BLOCK_PCT. It measures skin; a curtain of dark lashes or mascara with
little lid skin inside the circle is not found (test photos 09, 11, 25, 29; Drive w12). Deterministic, numpy and PIL
only, about 40-75 ms (a 160 px square, 24 directions)."""
import math
import numpy as np
from PIL import Image
from . import iris as L

SIDE = 160                   # px: the working square
PAD = 1.25                   # the square reaches this many iris radii from the centre (the ring beside the rim)
RIM = 0.96                   # the ring read runs from here...
INNER = 0.25                 # ...in to here, or PUPIL_GAP past the pupil (pupil_r) when that is further out
PUPIL_GAP = 0.06
BLUR = 1                     # box blur radius at SIDE before the colour tests: single fibres out
REF_BIN = 0.03               # radial bins of the iris reference (iris radii)
NSEC = 12                    # 30-degree sectors of the iris reference
REF_AWAY = 60.0              # a cap's iris: the sectors at least this far (degrees) from its direction
LIGHT_CLIP = 15.0            # L* limit of a sector's light correction (a*, b*: half of it)
LIGHT_DH = 20.0              # the light is read on pixels within this many degrees of the iris's hue
SKIN_DL = 15.0               # skin: this much lighter than the iris at its radius...
SKIN_DA = 8.0                # ...or this much redder (a*, with a* above 4)
SKIN_HUE = (10.0, 85.0)      # and a skin hue (degrees of atan2(b*, a*))...
SKIN_C = 8.0                 # ...and chroma
DARK_DL = 12.0               # lash line, lashes: this much darker
SPEC_L, SPEC_C = 70.0, 0.55  # a reflection: L* above SPEC_L, chroma under 8 or SPEC_C of the iris's...
SPEC_HOT = 78.0              # ...or anything lighter than this (a warm lamp is lighter than lid skin)
SCLERA_DE = 12.0             # dE76 from the white of the eye: the white inside the circle...
LIKE_CMAX = 10.0             # ...when also no more colourful than this (or the white's chroma + 6)
DT = 0.03                    # strip width (iris radii)
DARK_STRIPS = 4              # at most this many strips of lash line under the skin (0.12 of the radius)
MAJ = 0.45                   # a strip agrees when more than this share of it does
END_SHARE = 0.5              # a strip more than this share reflection ends the cap
NDIR = 24                    # directions a lid may come from (every 15 degrees)
NEAR, NEAR_FRAC = 30.0, 0.6  # a lid's area: the largest cap this close to its best direction, scoring this well
SCLERA_VETO = 0.4            # a cap whose rim arc outside is more than this share white of the eye is not a lid
CONT_AB = 15.0               # the cap's skin and the lid outside the rim: a*b* at most this far apart...
CONT_MIN = 3                 # ...read on the rim arc of at least this many strips...
CONT_LMIN = 15.0             # ...leaving out pixels darker than this outside (lashes, mascara carry no colour)
TEX_REL, TEX_ABS = 1.0, 4.5  # a cap's skin smoother than the iris beside it (and under TEX_ABS)...
TEX_FLOOR = 2.5              # ...or smoother than this at all is a reflection or a veil (L* std in a 5 px box)
WB_GAIN = (0.8, 1.25)        # white balance gains are clamped to this
MINPX = 6                    # pixels a reference cell needs

def _box_blur(a, r):
    if r <= 0:
        return a
    k = 2 * r + 1
    p = np.pad(a, ((r, r), (r, r), (0, 0)), mode="edge")
    c = np.pad(np.cumsum(np.cumsum(p, 0, dtype=np.float64), 1), ((1, 0), (1, 0), (0, 0)))
    return ((c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)).astype(np.float32)

def _lin(c):
    return np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)

def _white(rgb, band):
    """(rgb balanced on the white of the eye in band, the white's Lab), or (rgb, None) when too little of it shows"""
    if band.sum() < 40:
        return rgb, None
    px = rgb[band]
    mx, mn = px.max(1), px.min(1)
    sat = (mx - mn) / np.maximum(mx, 1.0)
    lum = px @ np.array([0.299, 0.587, 0.114], np.float32)
    sel = (lum >= np.percentile(lum, 60)) & (sat <= np.percentile(sat, 40)) & (mx < 250)
    if sel.sum() < 15 or float(np.median(lum[sel])) <= 90:
        return rgb, None
    white = _lin(px[sel] / 255.0).mean(0)
    gain = np.clip(white.mean() / np.maximum(white, 1e-4), *WB_GAIN)
    lin = np.clip(_lin(rgb / 255.0) * gain, 0, 1)
    out = (np.where(lin > 0.0031308, 1.055 * lin ** (1 / 2.4) - 0.055, lin * 12.92) * 255).astype(np.float32)
    return out, np.median(L.srgb_to_lab(out[band][sel]), 0)

def _median_by(cell, v, n):
    """per-cell median of v (NaN where a cell has under MINPX values)"""
    o = np.lexsort((v, cell))
    vs = v[o]
    cnt = np.bincount(cell, minlength=n)
    st = np.concatenate([[0], np.cumsum(cnt)[:-1]])
    out = np.full(n, np.nan, np.float32)
    ok = cnt >= MINPX
    if len(vs):
        lo = st + (cnt - 1) // 2
        hi = np.minimum(st + cnt // 2, len(vs) - 1)
        out[ok] = (vs[lo[ok]] + vs[hi[ok]]) / 2
    return out

def _fill(ref):
    """NaN rows take the nearest row that has values (None when none has)"""
    have = np.nonzero(~np.isnan(ref[:, 0]))[0]
    if len(have) == 0:
        return None
    ref = ref.copy()
    for i in range(len(ref)):
        if np.isnan(ref[i, 0]):
            ref[i] = ref[have[np.argmin(np.abs(have - i))]]
    return ref

def _nanmed0(a):
    """median over axis 0 leaving NaN out (NaN where a column has no value)"""
    s = np.sort(a, 0)
    n = (~np.isnan(a)).sum(0)
    lo = np.maximum((n - 1) // 2, 0)[None]
    hi = np.maximum(n // 2, 0)[None]
    v = (np.take_along_axis(s, lo, 0)[0] + np.take_along_axis(s, hi, 0)[0]) / 2
    return np.where(n == 0, np.nan, v)

def _prep(im, cx, cy, r, pupil_r):
    """the working square around the circle, as flat pixel lists with their classes' inputs (see the docstring)"""
    W, H = im.size
    S = 2 * r * PAD
    box = (int(round(cx - S / 2)), int(round(cy - S / 2)), int(round(cx + S / 2)), int(round(cy + S / 2)))
    sq = im.crop(box).resize((SIDE, SIDE), Image.BOX if S >= SIDE else Image.BILINEAR)   # black outside the photo
    k = SIDE / float(box[2] - box[0])
    ax = (np.arange(SIDE) + 0.5) / k + box[0]
    ay = (np.arange(SIDE) + 0.5) / k + box[1]
    off = ((ay < 1) | (ay > H - 1))[:, None] | ((ax < 1) | (ax > W - 1))[None, :]
    X = np.repeat(((ax - cx) / r)[None, :], SIDE, 0)
    Y = np.repeat(((ay - cy) / r)[:, None], SIDE, 1)
    rho = np.hypot(X, Y)
    ang = (np.degrees(np.arctan2(Y, X)) + 360.0) % 360.0
    rgb, white = _white(np.asarray(sq, np.float32), (rho > 1.05) & (rho < 1.24) & ~off)
    lab0 = L.srgb_to_lab(rgb).astype(np.float32)
    lab = _box_blur(lab0, BLUR)
    m1 = _box_blur(lab0[..., :1], 2)[..., 0]
    m2 = _box_blur(lab0[..., :1] ** 2, 2)[..., 0]
    tex = np.sqrt(np.maximum(m2 - m1 * m1, 0.0))
    pup = (pupil_r or 0.0) / L.iris_radius_frac()          # pupil radius in iris radii (pupil_r: share of the crop side)
    use = (rho < RIM) & (rho > max(INNER, pup + PUPIL_GAP)) & ~off
    if use.sum() < 60:
        return None
    nb = int(round((1.0 - INNER) / REF_BIN))
    iu = np.nonzero(use)
    lu = lab[iu]
    Xu, Yu, ru, au = X[iu], Y[iu], rho[iu], ang[iu]
    Cu = np.hypot(lu[:, 1], lu[:, 2])
    hu = np.degrees(np.arctan2(lu[:, 2], lu[:, 1]))
    rb = np.clip(((ru - INNER) / REF_BIN).astype(int), 0, nb - 1)
    # the white of the eye inside the circle, and reflections, before any reference is read
    like = np.zeros(len(lu), bool)
    if white is not None:
        like = (np.sqrt(((lu - white) ** 2).sum(-1)) < SCLERA_DE) & (Cu < max(LIKE_CMAX, math.hypot(white[1], white[2]) + 6.0))
    g = ~((lu[:, 0] > SPEC_L) & (Cu < 8.0)) & ~like
    if g.sum() < 40:
        return None
    ref0 = _fill(np.stack([_median_by(rb[g], lu[g, c], nb) for c in range(3)], 1))
    if ref0 is None:
        return None
    refC0 = np.hypot(ref0[rb, 1], ref0[rb, 2])
    d0 = lu - ref0[rb]
    sky = (d0[:, 2] < -12) & (d0[:, 0] > 0) & (d0[:, 1] < 2)
    spec = ((lu[:, 0] > SPEC_L) & (Cu < np.maximum(8.0, SPEC_C * refC0))) | (lu[:, 0] > SPEC_HOT) | sky
    refl = spec | like
    ok = ~refl
    # the light across the iris: 10-degree sectors of the mid ring, iris-hued pixels only, lit sectors only
    s36 = np.minimum((au / 10).astype(int), 35)
    hr = np.degrees(np.arctan2(ref0[rb, 2], ref0[rb, 1]))
    dh = np.abs((hu - hr + 180.0) % 360.0 - 180.0)
    mid = ok & (ru > max(0.40, pup + 0.08)) & (ru < max(0.62, pup + 0.28)) & ((dh < LIGHT_DH) | (Cu < 8.0) | (refC0 < 8.0))
    cnt = np.bincount(s36[mid], minlength=36)
    field = np.zeros((36, 3), np.float32)
    for c in range(3):
        o = np.bincount(s36[mid], weights=d0[mid, c], minlength=36) / np.maximum(cnt, 1)
        o[cnt < 5] = 0
        o = np.convolve(np.concatenate([o[-1:], o, o[:1]]), [0.25, 0.5, 0.25], "valid")
        lim = LIGHT_CLIP if c == 0 else LIGHT_CLIP / 2
        field[:, c] = np.clip(o, -lim, lim)
    field = field * (field[:, :1] > 0)
    lf = lu - field[s36]
    # the iris per 30-degree sector and radial bin (a cap reads the sectors away from it)
    sec = np.minimum((au / (360.0 / NSEC)).astype(int), NSEC - 1)
    cell = (sec * nb + rb)[ok]
    cm = np.stack([_median_by(cell, lf[ok, c], NSEC * nb) for c in range(3)], 1).reshape(NSEC, nb, 3)
    # the ring outside the rim: the white of the eye there, and the lid's colour for the continuity test
    io = np.nonzero((rho > 1.03) & (rho < 1.16) & ~off)
    lo = lab[io]
    Co = np.hypot(lo[:, 1], lo[:, 2])
    rim_col = cm[:, min(nb - 1, int((0.93 - INNER) / REF_BIN)), 0]
    rim_col = rim_col[~np.isnan(rim_col)]
    rimL = float(np.median(rim_col)) if len(rim_col) else 0.0
    if white is not None:
        scl = (Co < max(12.0, math.hypot(white[1], white[2]) + 6.0)) & (lo[:, 0] > max(45.0, rimL + 8, float(white[0]) - 20.0))
    else:
        scl = (Co < 12.0) & (lo[:, 0] > max(45.0, rimL + 8))
    idd = np.nonzero((rho < 1.0) & ~off)
    return dict(Xu=Xu, Yu=Yu, ru=ru, lu=lu, lf=lf, rb=rb, refl=refl, spec=spec, like=like & ~spec, cm=cm, tex=tex[iu],
                skinhue=(hu >= SKIN_HUE[0]) & (hu <= SKIN_HUE[1]) & (Cu >= SKIN_C),
                Xo=X[io], Yo=Y[io], lo=lo, scl=scl, Xd=X[idd], Yd=Y[idd], ndisc=max(int((rho < 1.0).sum()), 1))

def _classes(Q, phi):
    """(skin, dark) over the ring for a cap from direction phi (degrees; image coordinates, 270 = up), or None"""
    cen = (np.arange(NSEC) + 0.5) * 360.0 / NSEC
    ref = _nanmed0(Q["cm"][np.abs((cen - phi + 180.0) % 360.0 - 180.0) >= REF_AWAY])
    if np.isnan(ref).any():
        ref = _fill(ref)
        if ref is None:
            return None
    d = Q["lf"] - ref[Q["rb"]]
    skin = ((d[:, 0] > SKIN_DL) | ((d[:, 1] > SKIN_DA) & (Q["lu"][:, 1] > 4))) & Q["skinhue"] & ~Q["refl"]
    dark = (d[:, 0] < -DARK_DL) & ~Q["refl"]
    return skin, dark

def _cap(Q, phi, skin, dark):
    """(area %, depth in iris radii, score, strips) of the lid cap from direction phi; zeros when there is none"""
    none = (0.0, 0.0, 0.0, 0)
    c, s = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    t = Q["Xu"] * c + Q["Yu"] * s
    ns = int(RIM / DT)
    k = np.floor((RIM - t) / DT).astype(int)
    m = (k >= 0) & (k < ns)
    kk = k[m]
    na = np.bincount(kk, minlength=ns).astype(np.float64)
    n = na - np.bincount(kk, weights=Q["refl"][m], minlength=ns) + np.bincount(kk, weights=Q["like"][m], minlength=ns)
    w = n >= 4
    gs = np.concatenate([[0.0], np.cumsum(np.where(w, np.bincount(kk, weights=skin[m], minlength=ns) - MAJ * n, 0.0))])
    gd = np.concatenate([[0.0], np.cumsum(np.where(w, np.bincount(kk, weights=dark[m], minlength=ns) - MAJ * n, 0.0))])
    stop = np.nonzero((na >= 4) & (np.bincount(kk, weights=Q["spec"][m], minlength=ns) > END_SHARE * na))[0]
    amax = int(stop[0]) if len(stop) else ns
    if amax < 1:
        return none
    A = np.arange(1, amax + 1)[:, None]
    B = np.arange(0, DARK_STRIPS + 1)[None, :]
    sc = np.where(A + B <= amax, gs[A] + gd[np.minimum(A + B, amax)] - gd[A], -1e9)
    i = int(np.argmax(sc))
    best = float(sc.flat[i])
    if best <= 0:
        return none
    s1 = i // sc.shape[1] + 1
    depth = s1 + i % sc.shape[1]
    tcut = RIM - depth * DT
    to = Q["Xo"] * c + Q["Yo"] * s
    arc = to > tcut
    if arc.sum() >= 10 and Q["scl"][arc].mean() > SCLERA_VETO:
        return none                                          # the white of the eye beside it: not a lid
    zone = m & (k < s1)
    isel = zone & skin
    if isel.sum() < 10:
        return none                                          # no skin to speak of
    osel = (to > RIM - max(depth, CONT_MIN) * DT) & ~Q["scl"] & (Q["lo"][:, 0] > CONT_LMIN)
    if osel.sum() >= 10:
        dab = np.median(Q["lu"][isel][:, 1:], 0) - np.median(Q["lo"][osel][:, 1:], 0)
        if math.hypot(dab[0], dab[1]) > CONT_AB:
            return none                                      # does not carry on across the rim: not the lid outside
    tin = float(np.median(Q["tex"][isel]))
    rest = ~zone & ~Q["refl"] & (Q["ru"] > 0.5)
    tref = float(np.median(Q["tex"][rest])) if rest.sum() >= 30 else tin
    if (tin < TEX_REL * tref and tin < TEX_ABS) or tin < TEX_FLOOR:
        return none                                          # smooth: a reflection or a veil
    area = 100.0 * ((Q["Xd"] * c + Q["Yd"] * s) > tcut).sum() / Q["ndisc"]
    return area, depth * DT, best, depth

def lid_cover(im, cx, cy, r, pupil_r=None):
    """{"wedge_pct", "covered_pct", "side", "tilt", "depth"} for the analyze circle (cx, cy, r in pixels of im, the
    photo as analyze received it; pupil_r the vision pupil as a share of the pad-1.12 crop side), or None when the
    iris cannot be read. side: where the largest lid comes from (top, bottom, left, right); tilt: its direction in
    degrees (image coordinates, 270 = straight down from the top). Deterministic; numpy and PIL only."""
    if r < 4:
        return None
    Q = _prep(im, cx, cy, r, pupil_r)
    if Q is None:
        return None
    out = []
    for i in range(NDIR):
        phi = i * 360.0 / NDIR
        cl = _classes(Q, phi)
        out.append((phi,) + (_cap(Q, phi, *cl) if cl is not None else (0.0, 0.0, 0.0, 0)))
    n = len(out)
    # each local best stands for one lid; its area is the largest cap near it that scores nearly as well
    peaks = [i for i in range(n) if out[i][3] > 0 and out[i][3] >= out[i - 1][3] and out[i][3] >= out[(i + 1) % n][3]]
    reach = int(NEAR / (360.0 / n))
    lids = set()
    for p in peaks:
        best = p
        for dj in range(-reach, reach + 1):
            j = (p + dj) % n
            if out[j][3] >= NEAR_FRAC * out[p][3] and out[j][1] > out[best][1]:
                best = j
        lids.add(best)
    if not lids:
        return {"wedge_pct": 0.0, "covered_pct": 0.0, "side": None, "tilt": None, "depth": 0.0}
    lids = sorted(lids)
    i1 = max(lids, key=lambda i: out[i][1])
    other = [i for i in lids if abs((out[i][0] - out[i1][0] + 180) % 360 - 180) >= 90]
    i2 = max(other, key=lambda i: out[i][1]) if other else i1
    cov = np.zeros(len(Q["Xd"]), bool)
    for i in {i1, i2}:
        c, s = math.cos(math.radians(out[i][0])), math.sin(math.radians(out[i][0]))
        cov |= (Q["Xd"] * c + Q["Yd"] * s) > RIM - out[i][4] * DT
    phi = out[i1][0]
    side = "top" if 225 <= phi <= 315 else "bottom" if 45 <= phi <= 135 else "left" if 135 < phi < 225 else "right"
    return {"wedge_pct": round(float(out[i1][1]), 1), "covered_pct": round(float(100.0 * cov.sum() / Q["ndisc"]), 1),
            "side": side, "tilt": int(round(phi)), "depth": round(float(out[i1][2]), 2)}
