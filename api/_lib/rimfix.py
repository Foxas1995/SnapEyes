# -*- coding: utf-8 -*-
"""Places the crop shows no iris, measured on the crop and repaired inside /api/deglare (frames 22 and 26, and any iris the photo's edge cuts).

The image model draws whatever it is given, and chroma_lock keeps the colour of the crop it was given, so a place where the crop holds no iris
(black past the photo's edge, a lid's highlight or its shadow) comes back as an invention in the colour of that place. Two measured defects, each
repaired only where it is found; a crop without them takes exactly the path it took before (byte for byte: 35 of the 37 saved live crops do,
the other two are 22 and 26).

  1. VOID (22, and every iris that runs off the photo). Where the circle leaves the photo the client's square is black. The model paints the black
     as sclera and lid, chroma_lock copies the photo's neutral chroma over it, and the outpainted part comes out as a grey crescent, a straight cut
     and the coloured photo rectangle's edge (wave-q3 diag: 72 % of the enhance outputs of 22, 52 % of the studio images; judge's blind labels of an
     iris cut by the photo edge at 15 or 30 % of r: crescent in 6 of 6 renders, 0 of 6 after the fill). fill_void() fills the void from this
     iris' own tone at the same radius and matches it to the photo along the void's edge. Only a void that is the photo's own edge counts
     (edge_share): a straight run of wholly black columns or rows of the square as sent. A black lid shadow or a very dark iris that merely
     touches the border is not one (Commons cm036 reads 9 % and cs082 23 % as black connected to the border, and neither has a photo edge in the
     square).
  2. LID REMNANT (26). The lid fill covers the lid mask, but the wet margin's cream highlight and the dark shadow wedge under a heavy lid lie just
     outside it; the model turned the highlight into a red or orange block and the wedge into a grey-green band. lid_remnant() fills a highlight
     next to the lid mask, and the shadow that touches it, like a reflection. It does not make a lid-covered iris real: the honest answer for such
     a photo is the eyelid block in analyze (the grey-green band and dark blobs of 26 stay).

The measurements, all on the crop and all deterministic (numpy and PIL only):
  - edge_share(): the black (R + G + B at or below VOID_THR) leading or trailing columns and rows of the square as sent that are wholly black
    (98 %), inside 0.95 iris radii, as a share of that disc; and void_share(): the black of the finished crop connected to the square's border,
    inside 0.95 iris radii, as a share of that disc. fill_void() acts when both read VOID_MIN_PCT or more (the first says it is the photo's edge, the
    second that black is still there: 08's void is covered by its lid fill before the fill looks). 22 reads 4.9 %, 08 3.5 %, every other saved crop 0.00 %.
  - lid_remnant(): pixels within REM_BAND of the lid mask's edge that are REM_HOT lighter than the iris at their radius (the same radius away from
    the lid), counted at a 1024 px side; it fires from REM_FIRE_PX = 400. 26 reads 967 to 4053 on 6 of its 7 test circles; the 39 other lid fills of
    the test crops read 171 or less. It fires too where a highlight is really there: photo 20 on a circle that takes in the lower lid margin
    (1948), the lids over the iris of 29 and w03, Commons cm021 (590).
Nothing is invented where the photo has no information: the void and the shadow take this iris' own tone at the same radius (the iris rotated
about the pupil centre, L.mirror_prefill; black, lid fill and reflections never donate) and the highlight is filled like any reflection
(L.glare_fill); a void reaching inside VOID_INNER (the photo's edge cuts the iris itself) or over VOID_MAX_PCT is not filled at all.
SNAPEYES_VOIDFILL=off switches the void fill off, SNAPEYES_LIDREMNANT=off the lid remnant (each: off, 0, false or no; read once at import, BOM
safe, like SNAPEYES_DEGLARE_MODEL); with both off deglare() replies and crops equal the base byte for byte.
A repair that fails for any reason leaves the crop as it was: it must never fail the deglare call.
Cost (judge, 2026-10-11, a machine shared with other jobs, min of 4 calls, 1024 px crop): where nothing is found fill_void takes 3 to 6 ms (edge_share
is the first gate and returns) and lid_remnant 37 to 43 ms on a lid-filled crop (it is not called without a lid fill); where a repair is made fill_void
takes 0.6 s (22 and a 277 px cut iris) and lid_remnant 0.74 to 0.81 s (26, cm021). A whole deglare call takes 0.7 to 14 s on that machine."""
import os, json
import numpy as np
from PIL import Image
from . import iris as L

def _switch(name):
    """True unless the environment variable `name` says off, 0, false or no (BOM safe)."""
    return (os.environ.get(name) or "on").strip().lstrip("\ufeff").lower() not in ("off", "0", "false", "no")


VOID_ON = _switch("SNAPEYES_VOIDFILL")
REM_ON = _switch("SNAPEYES_LIDREMNANT")

VOID_THR = 9                         # the square is black where the circle left the photo: R + G + B at or below this
VOID_EDGE_FRAC = 0.98                # a column or row of the square is a photo's edge side when this share of it is black
VOID_SIDE = 256                      # the gate reads a copy this size
VOID_RHO = 0.95                      # ...inside this radius (mask_disk's feather starts at about 0.965)
VOID_MIN_PCT = 1.0                   # fill from this share of the disc (a sliver less is left to the model)
VOID_MAX_PCT = 30.0                  # past this the photo shows too little of the iris to borrow from: nothing is filled
VOID_INNER = 0.70                    # a void reaching inside this radius (iris radii) cuts the iris itself: not filled
VOID_EDGE_REACH = 0.10               # the void reaches this far (iris radii) along the disc's edge past the part inside VOID_RHO
VOID_GROW = 0.016                    # the filled area reaches this far past the black (the photo's JPEG-ringing edge), side share
VOID_SOFT = 0.004                    # the filled area's feather (Gaussian sigma, side share)
VOID_EDGE = 0.95                     # the fill's own colour ends here (iris radii): mask_disk's feather starts at about 0.965
FILL_WORK = 384                      # fills are worked at this size (a fill this smooth needs no more)
FILL_BAND = 0.016                    # the band of photo just outside a fill that it is matched to, side share
FILL_REACH = 0.030                   # the match is carried this far into the fill (Gaussian sigma, side share)
FILL_SMOOTH = 0.006                  # the fill is smoothed this much (Gaussian sigma, side share)
REM_BAND = 0.22                      # lid remnants are read this far (iris radii) beyond the lid mask's edge...
REM_HOT = (1.45, 150.0)              # ...a highlight: this much lighter than the iris ring at its radius, and this light (luma)
REM_DARK = 0.40                      # ...a shadow: darker than this share of the ring
REM_FIRE_PX = 400                    # a highlight of at least this many px (at 1024) fires the repair (a component: REM_COMP_PX)
REM_COMP_PX = 150
REM_DARK_PX = 2000                   # a shadow counts from this many px (at 1024), when it lies within REM_NEAR of the highlight
REM_NEAR = 0.05                      # (iris radii)
REM_GROW = (0.035, 0.02)             # the highlight and the shadow are filled this far past their edge (side share)
REM_MAX_PCT = 15.0                   # a remnant hole over this share of the disc is not filled (the lid is not the problem)
_W = np.array([0.299, 0.587, 0.114], np.float32)


def tag(res, void_pct=0.0, remnant_pct=0.0):
    """The deglare reply res, with the share of the disc each repair filled added when it made one (otherwise res itself)."""
    if void_pct > 0:
        res["void_pct"] = void_pct
    if remnant_pct > 0:
        res["remnant_pct"] = remnant_pct
    return res


def log(void_pct=0.0, remnant_pct=0.0):
    """One log line (no image, no personal data) when a repair was made: what production needs to watch the gates."""
    if void_pct or remnant_pct:
        print("snapeyes rimfix " + json.dumps({"void_pct": void_pct, "remnant_pct": remnant_pct}), flush=True)


def _dil(m, k):
    """Square dilation of a boolean mask by a k x k window (k odd): exactly L._grow_mask's result, from a running sum of
    the padded mask instead of k shifted copies (the windows here reach 90 px: 150 ms against 17 ms at 384 px)."""
    r = k // 2
    out = m
    for ax in (0, 1):
        p = np.pad(out, [(r, r) if a == ax else (0, 0) for a in (0, 1)]).astype(np.int32)
        c = np.cumsum(p, axis=ax, dtype=np.int32)
        c = np.concatenate([np.zeros_like(np.take(c, [0], axis=ax)), c], axis=ax)
        n = out.shape[ax]
        out = (np.take(c, np.arange(k, k + n), axis=ax) - np.take(c, np.arange(0, n), axis=ax)) > 0
    return out


def _grow(m, px):
    return _dil(m, max(3, int(round(2 * px)) | 1))


def _rho(w, pad):
    ax = (np.arange(w) - w / 2 + 0.5) / (L.iris_radius_frac(pad) * w)
    return np.sqrt(ax[None, :] ** 2 + ax[:, None] ** 2)


def _void(arr, pad, side, quick=True):
    """(share of the disc inside VOID_RHO, mask) of the black connected to the border, on an array `side` wide. With
    quick, the labelling is skipped when the black inside the disc is under half of VOID_MIN_PCT (nothing to find)."""
    blk = arr.sum(-1) <= VOID_THR
    disc = _rho(side, pad) < VOID_RHO
    nd = float(disc.sum())
    if quick and 100.0 * float((blk & disc).sum()) < 0.5 * VOID_MIN_PCT * nd:
        return 0.0, None
    lab, n = L._components(blk)
    edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    edge = edge[edge > 0]
    if edge.size == 0:
        return 0.0, None
    v = np.isin(lab, edge)
    return 100.0 * float((v & disc).sum()) / max(1.0, nd), v


def void_share(img, pad):
    """The share (percent) of the disc that is black because the circle left the photo, read on a small copy."""
    a = np.asarray(img.convert("RGB").resize((VOID_SIDE, VOID_SIDE), Image.BOX)).astype(np.int32)
    return _void(a, pad, VOID_SIDE)[0]


def _lead(f):
    """How many entries at the start of f are at least VOID_EDGE_FRAC."""
    k = 0
    while k < len(f) and f[k] >= VOID_EDGE_FRAC:
        k += 1
    return k


def edge_share(raw, pad):
    """Percent of the disc (inside VOID_RHO) that lies beyond the photo's own edge, read on the square as sent (raw: the crop as the client cut
    it, before any mask). The client draws the photo on a black canvas, so what the circle leaves of the photo is black over the full width or
    height: the leading or trailing columns and rows that are (almost) wholly black. A lid shadow, a dark iris or a black lash line is black only
    in part of a column, so it is never read as the photo's edge (void_share alone reads black connected to the border, which a dark shadow
    can be: Commons cm036 reads 9 % and cs082 23 % that way, and neither has a photo edge in the square)."""
    a = np.asarray(raw.convert("RGB").resize((VOID_SIDE, VOID_SIDE), Image.BOX)).astype(np.int32)
    blk = a.sum(-1) <= VOID_THR
    n = VOID_SIDE
    colf, rowf = blk.mean(0), blk.mean(1)
    band = np.zeros_like(blk)
    k1, k2 = _lead(colf), _lead(colf[::-1])
    if k1:
        band[:, :k1] = True
    if k2:
        band[:, n - k2:] = True
    k1, k2 = _lead(rowf), _lead(rowf[::-1])
    if k1:
        band[:k1, :] = True
    if k2:
        band[n - k2:, :] = True
    if not band.any():
        return 0.0
    disc = _rho(n, pad) < VOID_RHO
    return 100.0 * float((band & disc).sum()) / max(1.0, float(disc.sum()))


def _donor_fill(im, H, rho, pad, avoid=None):
    """The fill for the bool area H of the w x w PIL image im: this iris' own tone at the same radius (mirror_prefill
    with its far donors; H, `avoid` (a lid fill: synthetic, it does not donate) and black never donate), then matched to
    the photo along H's edge: the colour of a band of photo just outside H (FILL_BAND) minus the fill's, carried into H
    by a wide Gaussian that fades with the distance from the band. The fill is then the photo's own colour at the edge
    (no seam, no rectangle edge for the render and its colour lock to keep) and the iris' tone further in; smoothed
    inside H (the donors' support ends in a ragged line at the rim). float32 w x w x 3 (only H is to be used)."""
    w = im.size[0]
    P = np.asarray(im, np.float32)
    Hb = _grow(H, FILL_BAND * w)
    hole = Hb if avoid is None else (Hb | avoid)
    f2 = np.clip(L._blur_f(hole.astype(np.float32), 1.0), 0.0, 1.0)
    f2 = np.where(hole, np.maximum(f2, 0.999), f2).astype(np.float32)
    F = np.asarray(L.mirror_prefill(im, f2, L.LID_EXTRA_DONORS), np.float32)
    band = Hb & ~H & (rho < 0.95) & (P.sum(-1) > 12.0)
    if band.any():
        Bw = band.astype(np.float32)
        sg = FILL_REACH * w
        den = L._blur_f(Bw, sg)
        c0 = max(float(np.percentile(den[band], 75)), 1e-3)
        Pb = np.stack([L._blur_f(P[..., c], 1.0) for c in range(3)], -1)
        R_ = (Pb - F) * Bw[..., None]
        F = F + np.stack([L._blur_f(R_[..., c], sg) for c in range(3)], -1) / np.maximum(den, c0)[..., None]
    Fb = np.stack([L._blur_f(F[..., c], FILL_SMOOTH * w) for c in range(3)], -1)
    return np.where(H[..., None], Fb, F)


def _blend(img, F, H, pad):
    """img with the w x w fill F put in over the bool area H (feathered, inside the photo's own disc)."""
    S, w = img.size[0], F.shape[0]
    al = np.clip(L._blur_f(H.astype(np.float32), VOID_SOFT * w), 0.0, 1.0)
    al = np.where(H, 1.0, al)
    if w != S:
        F = np.asarray(Image.fromarray(np.clip(F, 0, 255).astype(np.uint8)).resize((S, S), Image.BICUBIC), np.float32)
        al = np.clip(np.asarray(Image.fromarray(al.astype(np.float32), "F").resize((S, S), Image.BICUBIC)), 0.0, 1.0)
    al = al * L.disk_alpha(S, float(L.iris_radius_frac(pad) * S))
    P = np.asarray(img.convert("RGB"), np.float32)
    out = P * (1.0 - al[..., None]) + F * al[..., None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def fill_void(img, pad, raw=None):
    """img (the finished crop) with the black where the circle left the photo filled (_donor_fill). raw: the square as the client sent it, on which
    the photo's own edge is read (edge_share): without it nothing is filled. Returns (image, share): the image itself, unchanged, and share 0.0
    when the crop has no void (no photo edge in the square, or under VOID_MIN_PCT black left), too much of one (over VOID_MAX_PCT), one that
    reaches into the iris itself (inside VOID_INNER), or when anything goes wrong."""
    if not VOID_ON or raw is None:
        return img, 0.0
    try:
        return _fill_void(img, pad, raw)
    except Exception:
        return img, 0.0


def _fill_void(img, pad, raw):
    if edge_share(raw, pad) < VOID_MIN_PCT:         # not the photo's own edge: a dark lid shadow or a dark iris is no void
        return img, 0.0
    pct = void_share(img, pad)
    if pct < VOID_MIN_PCT or pct > VOID_MAX_PCT:
        return img, 0.0
    S = img.size[0]
    w = min(S, FILL_WORK)
    im = img.convert("RGB").resize((w, w), Image.BOX) if w != S else img.convert("RGB")
    _, v = _void(np.asarray(im).astype(np.int32), pad, w)
    if v is None:
        return img, 0.0
    rho = _rho(w, pad)
    core = v & (rho < VOID_RHO)                     # the black past the photo inside the disc...
    if int((core & (rho < VOID_INNER)).sum()) > 0.001 * float((rho < 1.0).sum()):
        return img, 0.0                             # the photo's edge cuts the iris itself, not only its rim: nothing to borrow
    # ...and the black between it and the disc's edge (not the black round the whole disc: the rest of the edge is untouched)
    vd = core | (_grow(core, VOID_EDGE_REACH * L.iris_radius_frac(pad) * w) & v & (rho < 1.02))
    H = _grow(vd, VOID_GROW * w)                    # the photo's resampled edge pixels go too
    F = _donor_fill(im, H, rho, pad)
    # past VOID_EDGE the fill takes the colour it has at that radius on the same ray: the donors of the disc's own
    # feathered rim are dark and stair-stepped, and the fade to black is disk_alpha's (in _blend), as for the photo
    out_r = rho > VOID_EDGE
    if out_r.any():
        yy, xx = np.nonzero(out_r)
        k = VOID_EDGE / rho[out_r]
        cx = w / 2 - 0.5
        fx, fy = cx + (xx - cx) * k, cx + (yy - cx) * k
        x0 = np.clip(np.floor(fx).astype(int), 0, w - 2); y0 = np.clip(np.floor(fy).astype(int), 0, w - 2)
        ax_, ay_ = (fx - x0)[:, None], (fy - y0)[:, None]
        F[out_r] = (F[y0, x0] * (1 - ax_) * (1 - ay_) + F[y0, x0 + 1] * ax_ * (1 - ay_)
                    + F[y0 + 1, x0] * (1 - ax_) * ay_ + F[y0 + 1, x0 + 1] * ax_ * ay_)
    return _blend(img, F, H, pad), round(pct, 2)


def _comps(m, min_px):
    """The 8-connected components of m with at least min_px pixels: (their union, labels, kept label ids)."""
    lab, n = L._components(m)
    if n == 0:
        return m & False, lab, []
    sz = np.bincount(lab.ravel())[1:]
    keep = [i + 1 for i, s in enumerate(sz) if s >= min_px]
    return np.isin(lab, keep), lab, keep


def _open(m, px):
    """Opening (erode, then dilate) by a square of px x px."""
    return _grow(~_grow(~m, px / 2.0), px / 2.0)


def lid_remnant(img, lid_hard, pad, pupil_rho=None):
    """img (the finished crop of a photo whose lid was filled) with the lid's remnants filled the way the lid was: the
    wet margin's highlight just outside the lid mask, and the lid's shadow where it touches that highlight (the shadow
    wedge under a heavy lid, which the lid's own mask stops short of). Measured on the crop: the iris ring at each
    radius (median luma, 0.03 iris radii wide) from the pixels farther than 0.25 iris radii from the lid mask; a
    highlight is a pixel within REM_BAND of the mask that is REM_HOT lighter than that ring (after a 1 px opening,
    components of REM_COMP_PX); the repair acts from REM_FIRE_PX highlight pixels, and a shadow (darker than REM_DARK of
    the ring, components of REM_DARK_PX) is filled with it when it lies within REM_NEAR of the highlight. Returns (image,
    share of the disc filled in percent): img itself and 0.0 when there is no lid fill or no highlight, or the hole
    would pass REM_MAX_PCT. lid_hard: the lid mask (any size, nonzero = lid). pupil_rho: the pupil in iris radii."""
    if not REM_ON or lid_hard is None:
        return img, 0.0
    try:
        S = img.size[0]
        w = min(S, FILL_WORK)
        k = (w / 1024.0) ** 2
        im = img.convert("RGB").resize((w, w), Image.BOX) if w != S else img.convert("RGB")
        lid = np.asarray(Image.fromarray((np.asarray(lid_hard) > 0).astype(np.uint8) * 255).resize((w, w), Image.NEAREST)) > 0
        if not lid.any():
            return img, 0.0
        a = np.asarray(im, np.float32)
        y = a @ _W
        rho = _rho(w, pad)
        R = L.iris_radius_frac(pad) * w
        z = (rho > max(0.3, (pupil_rho or 0.0) * 1.2)) & (rho < 0.95) & (y > 6.0)
        far = z & ~_grow(lid, 0.25 * R)
        bins = np.minimum((rho / 0.03).astype(int), 40)
        med = np.full(41, np.nan)
        for b in range(41):
            m = far & (bins == b)
            if m.sum() >= 200 * k:
                med[b] = np.median(y[m])
        ok = np.isfinite(med)
        if ok.sum() < 5:
            return img, 0.0
        ii = np.arange(41)
        ref = np.interp(ii, ii[ok], med[ok])[bins]
        band = z & _grow(lid, REM_BAND * R) & ~_grow(lid, 1)
        hot = _open(band & (y > REM_HOT[0] * ref) & (y > REM_HOT[1]), 3)
        hotc, _, _ = _comps(hot, REM_COMP_PX * k)
        if hotc.sum() < REM_FIRE_PX * k:
            return img, 0.0
        H = _grow(hotc, REM_GROW[0] * w)
        dark = _open(band & (y < REM_DARK * ref), 5)
        darkc, lab, _ = _comps(dark, REM_DARK_PX * k)
        if darkc.any():
            near = _grow(H, REM_NEAR * R)
            ids = [i for i in np.unique(lab[darkc]) if (near & (lab == i)).any()]
            if ids:
                H = H | _grow(np.isin(lab, ids), REM_GROW[1] * w)
        H &= (rho < 0.95) & (rho > max(0.3, (pupil_rho or 0.0) * 1.1)) & ~lid & (a.sum(-1) > 12.0)
        pct = 100.0 * float(H.sum()) / max(1.0, float((rho < 1.0).sum()))
        if pct > REM_MAX_PCT or pct <= 0.0:
            return img, 0.0
        # filled like a reflection (glare_fill: the tone of the iris at that radius plus the photo's own departure from it
        # carried in from round the hole, so a hole in shade stays in shade; then the fibre band from single donors)
        feather = np.clip(L._blur_f(H.astype(np.float32), 0.0098 * w), 0.0, 1.0)
        F = L.glare_fill(im, feather, (H * 255).astype(np.uint8), R, pupil_rho, avoid=(lid * 255).astype(np.uint8))
        al = feather
        if w != S:
            F = F.resize((S, S), Image.BICUBIC)
            al = np.clip(np.asarray(Image.fromarray(feather.astype(np.float32), "F").resize((S, S), Image.BICUBIC)), 0.0, 1.0)
        P = np.asarray(img.convert("RGB"), np.float32)
        out = P * (1.0 - al[..., None]) + np.asarray(F, np.float32) * al[..., None]
        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)), round(pct, 2)
    except Exception:
        return img, 0.0
