# -*- coding: utf-8 -*-
"""The pupil, measured on the photo or the render itself, and the repairs that start from a measurement (round 3).

Every repair here is gated by a number read off the image it would change, by our own numpy estimator; when the number does
not reach its threshold the function returns None, or the very object it was given, and the picture is exactly the one it
was before. No model call, numpy and PIL only. A fault inside any of it costs the customer nothing (the repair is skipped and
logged). Kill switches (read once at import, BOM-safe like SNAPEYES_DEGLARE_MODEL; off, 0, false or no): SNAPEYES_PUPIL=off
switches every repair of this round off (this module and api/_lib/pupil_seal.py), and one name per behaviour:
SNAPEYES_PUPIL_DISC, SNAPEYES_PUPIL_TONE, SNAPEYES_PUPIL_EDGE, SNAPEYES_PUPIL_GRADE.

 1. pupil_disc (deglare). pupil_fill paints the VISION pupil, a disc centred on the frame, and the true pupil sits off
    the frame centre by a median 0.048 iris radii (7 of 31 test photos by more than 0.08). Where a reflection makes it
    fill anyway, and the vision disc paints lit pixels black that lie outside the pupil or leaves a lit corner inside
    it, the fill is the pupil's own circle (fit_pupil: radial edge evidence, dark inside, confirmed against
    pupil_circle) with a crisp edge. The model was then given a pale crescent or a window corner beside a black disc
    and drew it back as a blue crescent (18) or a blue arc (15). Not where a window is mirrored over the iris beside the
    pupil (25: the lit part the vision disc hid is a fifth of the pupil's area): the fill cannot rebuild that, the vision disc is kept.
 2. tone_guard (enhance, after pupil_lock). A pupil the model drew grey where the photo's is black is taken down to the
    photo's darkness, to the render's own edge.
 3. edge_guard (enhance, after tone_guard). Blue light on the pupil's edge of a warm iris (29, 15, 18, 11: a window
    mirrored at the rim, carried into the fibres by the lock) takes the iris' colour, keeping its brightness. Blue and grey
    irises are never touched: a bluish rim is their own colour.
 4. grade_pupil (studio_grade). A room lit inside a wide pupil lifts the radial median the grade reads the pupil's
    radius from: 0.44 for the owner's 215102, whose pupil ends at 0.50, and the band between stayed a grey ring round
    the black disc. The grade flattens to the pupil circle's own edge where that band is pupil, not iris.
The halo round a pupil the model drew too small and the colour zone of a photo that is black there are api/_lib/pupil_seal.py."""
import os, math, json
import numpy as np
from PIL import Image
from . import iris as L


def _on(*names):
    """True unless one of these environment variables says off, 0, false or no (read once at import; the BOM strip is for
    values set from PowerShell)."""
    return all((os.environ.get(n) or "on").strip().lstrip("\ufeff").lower() not in ("off", "0", "false", "no") for n in names)


DISC_ON = _on("SNAPEYES_PUPIL", "SNAPEYES_PUPIL_DISC")
TONE_ON = _on("SNAPEYES_PUPIL", "SNAPEYES_PUPIL_TONE")
EDGE_ON = _on("SNAPEYES_PUPIL", "SNAPEYES_PUPIL_EDGE")
GRADE_ON = _on("SNAPEYES_PUPIL", "SNAPEYES_PUPIL_GRADE")


def _fault(where, e):
    """A repair must never cost the customer the picture: log the fault, carry on without the repair."""
    print("snapeyes pupilgeo fault " + where + " " + L._scrub(repr(e))[:200], flush=True)


def _log(what, **kv):
    print("snapeyes pupilgeo " + what + " " + json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in kv.items()}), flush=True)


WARM_CROP = -8.0          # a warm iris: its blue lean, (Cb - Cr) / sqrt 2 over 0.35-0.88 of the iris radius as reflection_chroma measures it
WARM_RENDER = -12.0       # (REFL_IRIS_BLUE), is at or below this, read on the photo's crop (deglare) or on the render (enhance). The brown,
                          # amber, olive and beige test eyes read -11 to -57 (25 is the nearest, -11.3 on its crop, -16.3 on its render); the
                          # blue and grey ones -7 to +18. The defects these repairs answer (a white halo, a blue arc or patch at the pupil's
                          # rim) were seen on warm irises; on a blue or grey iris a bluish rim is its own colour and nothing was seen to repair


def _lean(im, r_frac):
    """The iris' blue lean, (Cb - Cr) / sqrt 2, median over 0.35-0.88 of the iris radius, on a 128 px copy."""
    _, cb, cr = [np.asarray(p).astype(np.float32) for p in im.convert("RGB").resize((128, 128), Image.BOX).convert("YCbCr").split()]
    ax = (np.arange(128) - 64 + 0.5) / (r_frac * 128)
    rc = np.hypot(ax[None, :], ax[:, None])
    core = (rc > 0.35) & (rc < 0.88)
    return float((np.median(cb[core]) - np.median(cr[core])) / math.sqrt(2.0))


# ----------------------------------------------------------------------------- 1. the pupil's own circle (deglare)
GEO_SIDE = 256            # the edge evidence is read on a copy this size
GEO_SHIFT = 0.22          # the pupil centre is searched this far (iris radii) from the frame centre
GEO_COVER = 0.80          # a circle counts when this share of its 48 directions shows an edge (cover, strength above GEO_EDGE)...
GEO_EDGE = 1.5            # ...where the strength is the outward brightness rise, or 0.7 x the colour change, per pixel at GEO_SIDE
GEO_SCORE = 3.4           # ...and the mean strength (clipped at 6) reaches this. On the 41 test photos the circles drawn right by
                          # eye read 3.4-6.0 with cover 0.83-1.0; the ones a reflection or a dark frame fooled (02, 17, 20, w06)
                          # read cover 0.52-0.77
GEO_PRIOR = (0.75, 1.35)  # ...its radius lies between these shares of the vision pupil's (which also bounds the search)...
GEO_AGREE = 0.065         # ...it agrees (centre and radius, iris radii) with pupil_circle, or pupil_circle_chroma, where one finds a circle...
GEO_BORDER = 0.02         # ...and its centre is not on the border of the search square


def _maps(im):
    """The edge planes of the image on a GEO_SIDE square, as stacked (d/dx, d/dy) pairs, shape (6, n, n), in the order of
    L*, a*, b*. Brightness is blurred one pixel; the colour is read on half the side and stretched back (it changes
    slowly, and the conversion to CIELAB is most of the cost)."""
    n = GEO_SIDE
    lum = L._lock_lum(im).astype(np.float32)
    lab = L.srgb_to_lab(np.asarray(im.convert("RGB").resize((n // 2, n // 2), Image.BOX))).astype(np.float32)
    gy, gx = np.gradient(L._blur_f(lum, 1.0))
    g = [gx, gy]
    for k in (1, 2):
        gy, gx = np.gradient(L._resize_plane(lab[..., k], n, Image.BILINEAR))
        g += [gx, gy]
    return np.stack(g).astype(np.float32)


def _score(g, cxs, cys, rhos, R, na=48):
    """Edge evidence of every candidate circle: (value, mean strength, cover), arrays over (cx, cy, rho). The brightness
    counts only where it rises outward (a pupil is dark inside): a polarity-blind search locked on the hand reflected in 25."""
    th = (np.arange(na) + 0.5) / na * 2 * math.pi
    ct, st = np.cos(th).astype(np.float32), np.sin(th).astype(np.float32)
    cx, cy, rho = np.meshgrid(cxs, cys, rhos, indexing="ij")
    x = (GEO_SIDE / 2 - 0.5 + (cx[..., None] + rho[..., None] * ct) * R).astype(np.float32)
    y = (GEO_SIDE / 2 - 0.5 + (cy[..., None] + rho[..., None] * st) * R).astype(np.float32)
    inside = (x.min(-1) > 2) & (y.min(-1) > 2) & (x.max(-1) < GEO_SIDE - 3) & (y.max(-1) < GEO_SIDE - 3)
    x0 = np.clip(np.floor(x).astype(np.int32), 0, GEO_SIDE - 2); y0 = np.clip(np.floor(y).astype(np.int32), 0, GEO_SIDE - 2)
    fx, fy = x - x0, y - y0
    v = (g[:, y0, x0] * ((1 - fx) * (1 - fy)) + g[:, y0, x0 + 1] * (fx * (1 - fy))
         + g[:, y0 + 1, x0] * ((1 - fx) * fy) + g[:, y0 + 1, x0 + 1] * (fx * fy))      # (6, nx, ny, nr, na)
    up = v[0] * ct + v[1] * st
    e = np.maximum(np.maximum(up, 0.0), 0.7 * np.hypot(v[2] * ct + v[3] * st, v[4] * ct + v[5] * st))
    sc = np.minimum(e, 6.0).mean(-1)
    cov = (e > GEO_EDGE).mean(-1)
    return np.where(inside, sc * (0.4 + cov), -1.0), sc, cov


def fit_pupil(im, r_frac, prior_rho):
    """(cx, cy, rho, strength, cover) of the pupil, in iris radii from the frame centre, or None: the circle with the
    clearest edge evidence, searched round the frame centre within GEO_SHIFT and at GEO_PRIOR of the vision pupil's
    radius prior_rho. A coarse grid, then a fine one round its best circle. im: a square iris image."""
    g = _maps(im)
    R = r_frac * GEO_SIDE
    rmin, rmax = max(0.10, prior_rho * GEO_PRIOR[0]), min(0.70, prior_rho * GEO_PRIOR[1])
    cs = np.arange(-GEO_SHIFT, GEO_SHIFT + 1e-6, 0.04)
    rs = np.arange(rmin, rmax + 1e-6, 0.02)
    val, sc, cov = _score(g, cs, cs, rs, R, 32)
    i = np.unravel_index(int(np.argmax(val)), val.shape)
    if val[i] < 0:
        return None
    cx0, cy0, r0 = cs[i[0]], cs[i[1]], rs[i[2]]
    cs2 = np.arange(cx0 - 0.04, cx0 + 0.041, 0.01)
    ys2 = np.arange(cy0 - 0.04, cy0 + 0.041, 0.01)
    rs2 = np.arange(max(0.08, r0 - 0.04), r0 + 0.041, 0.01)
    val, sc, cov = _score(g, cs2, ys2, rs2, R)
    j = np.unravel_index(int(np.argmax(val)), val.shape)
    return float(cs2[j[0]]), float(ys2[j[1]]), float(rs2[j[2]]), float(sc[j]), float(cov[j])


def _sane(f, prior_rho):
    """fit_pupil's circle has clear edge evidence all round (GEO_COVER, GEO_SCORE), its centre is off the border of the
    search square (GEO_BORDER) and its radius is GEO_PRIOR of the vision pupil's."""
    return (f is not None and f[4] >= GEO_COVER and f[3] >= GEO_SCORE
            and max(abs(f[0]), abs(f[1])) <= GEO_SHIFT - GEO_BORDER and GEO_PRIOR[0] <= f[2] / prior_rho <= GEO_PRIOR[1])


def _confirmed(f, im, r_frac):
    """Where pupil_circle (brightness), or else pupil_circle_chroma, finds a circle on the same image the fit agrees with
    it (GEO_AGREE); where neither does, the fit stands on its own edge evidence."""
    c = L.pupil_circle(im, r_frac)
    if c is None:
        c = L.pupil_circle_chroma(im, r_frac)
    return c is None or (math.hypot(f[0] - c[0], f[1] - c[1]) <= GEO_AGREE and abs(f[2] - c[2]) <= GEO_AGREE)


DISC_OVERLAP = 0.04       # pupil_fill's own trigger: a reflection over this share of the vision pupil (only that fill is moved)
DISC_GROW = 1.03          # the fill is the true pupil x this (its edge is blurred): black inside, an edge of PUPIL_DISC_FEATHER, and the
                          # glare mask keeps every pixel outside it (the vision fill: a 22% fade, the glare kept outside 1.04 x the vision pupil)
DISC_BRIGHT = 110.0       # a pixel this bright (Y, 0-255) is a reflection or pale iris, not pupil
DISC_MISS = (0.07, 0.006) # the vision disc is wrong where, as a share of the true pupil's area, the lit pixels it paints black outside the
                          # true pupil plus those it leaves inside reach the first, or those it leaves inside reach the second alone (a
                          # corner of a window beside the fill: 18). Read on the 14 test frames where pupil_fill fills: 25 0.18, 15 0.11, 11 0.076
                          # (over), 18 0.011 (left); the blue and grey irises d04 0.17 and d05 0.054 (WARM_CROP keeps them out); the rest 0.0-0.03.
                          # Under the live jitter of the analyze circle (287 crops of 41 photos, circles moved 2-10 % and rescaled 0.9-1.1) the
                          # eyes that need no fill read 0.05-0.065 at some circles (07, 20), the three that do read 0.07 and more (11, 15) or
                          # 0.01 and more on the second number (18): the first threshold is 0.07, not the 0.05 the 14 frames alone allowed
DISC_PUPIL_MAX = 0.40     # a dilated pupil (the vision pupil's radius over this, iris radii) keeps the vision disc: the lit part the disc hides
                          # is large there and the fit is a guess. 25 and 19 read 0.46-0.53 under that jitter, and the draws made on those
                          # inputs showed no gain (25: a grey-blue ring and a white blotch against HEAD's white crescent and faint arc; 19: a
                          # pupil of another size, at random); 11, 15, 18, 07, 20 read 0.22-0.35
DISC_OVER_MAX = 0.15      # ...but not a window: where the vision disc paints more than this share of the pupil's area black outside the true
                          # pupil (25: 0.182, a window mirrored over the iris beside a dilated pupil that sits 0.16 off the frame centre) the
                          # lit region is too large for the fill to reconstruct once the disc stops covering it: glare_fill left a smear with
                          # lash shadows there and the model kept it in 3 of 8 draws (a worse defect than the faint arcs the vision disc leaves
                          # at HEAD, 1 of 8 a halo), so the vision disc stays. Fired 11 0.076, 15 0.111; nearest, 25: 0.182


def pupil_disc(crop, pr_px, glare_hard, r_frac):
    """(dx, dy, fill radius, limit) in pixels, the first two from the frame centre: the disc pupil_fill should paint
    and drop_pupil should keep clear (both the same radius) instead of the vision pupil's, or None. Asked only where
    pupil_fill would fill anyway (a reflection over DISC_OVERLAP of the vision pupil, read the way it reads it);
    answered only when the pupil's own circle is sane (_sane), the two discs differ in what they do to the lit pixels
    (DISC_MISS, read on a GEO_SIDE copy) without that part being a window over the iris (DISC_OVER_MAX), the pupil is not dilated
    (DISC_PUPIL_MAX) and the circle is confirmed (_confirmed), on a warm iris (WARM_CROP). Every other photo gets exactly the fill it got before."""
    try:
        return _pupil_disc(crop, pr_px, glare_hard, r_frac)
    except Exception as e:
        _fault("pupil_disc", e)
        return None


def _pupil_disc(crop, pr_px, glare_hard, r_frac):
    if not DISC_ON or glare_hard is None or pr_px < 4:
        return None
    S = crop.size[0]
    x0, x1 = max(0, int(S / 2 - pr_px) - 2), min(S, int(S / 2 + pr_px) + 3)
    yy, xx = np.mgrid[x0:x1, x0:x1]
    vis = np.sqrt((xx - S / 2 + 0.5) ** 2 + (yy - S / 2 + 0.5) ** 2) < pr_px
    if not vis.any() or float((glare_hard[x0:x1, x0:x1][vis] > 0).mean()) < DISC_OVERLAP:
        return None
    if _lean(crop, r_frac) > WARM_CROP:
        return None
    R = r_frac * S
    rv = pr_px / R
    if rv > DISC_PUPIL_MAX:
        return None
    f = fit_pupil(crop, r_frac, rv)
    if not _sane(f, rv):
        return None
    n = GEO_SIDE
    ax = (np.arange(n) - n / 2 + 0.5) / (r_frac * n)
    a = np.asarray(crop.convert("RGB").resize((n, n), Image.BOX)).astype(np.float32)
    bright = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]) > DISC_BRIGHT
    vis = np.hypot(ax[None, :], ax[:, None]) < rv
    df = np.hypot(ax[None, :] - f[0], ax[:, None] - f[1])
    fit = df < f[2]
    area = float(fit.sum())
    over = float((bright & vis & (df > f[2] + 0.01)).sum()) / area          # painted black, outside the true pupil
    left = float((bright & fit & ~vis).sum()) / area                         # left lit, inside it
    if over + left < DISC_MISS[0] and left < DISC_MISS[1]:
        return None
    if over > DISC_OVER_MAX:
        return None
    if not _confirmed(f, crop, r_frac):
        return None
    _log("disc", cx=f[0], cy=f[1], rho=f[2], vision=rv, over=over, left=left)
    return f[0] * R, f[1] * R, f[2] * R * DISC_GROW, f[2] * R * DISC_GROW


# ----------------------------------------------------------------------------- 2. a pupil the model drew grey (enhance)
TONE_EXCESS = 20.0        # the render's pupil core (median brightness inside 0.6 of its own circle, Y 0-255) is this much brighter than the
TONE_MIN = 30.0           # photo's at the same place, and at least this bright (the grade reads a pupil only below PUPIL_DARK 30)
                          # Measured over the 113 stage images of the 37 test frames (the four draws of the six frames that get
                          # re-rendered, and the ones made with the measured fill): excess 2.4 at most and a median of -6.5 (a hazy or
                          # reflecting photo pupil is brighter than the render's) for every render but one, 11 (draw r4): 35.5, a flat grey disc


def tone_guard(out, base, r_frac):
    """The model sometimes draws a flat grey pupil (11, one draw of eight with the measured fill: Y 44 against the photo's 8), which the
    grade cannot take out (its neutral_pupil only darkens what is under PUPIL_DARK, and flattens down to the darkest 15% of the
    pupil, which is the whole disc). Measured: the render's pupil core against the photo's at the same place (TONE_EXCESS, TONE_MIN).
    Then the pupil, to the render's own edge, is taken down to the photo's own darkness (never above pupil_lock's ceiling
    PUPIL_LOCK_TONE_MAX), neutral, over an edge of PUPIL_LOCK_FEATHER: pupil_lock's rule for a disk that is too light instead of
    too large. out: the render after pupil_lock; base: the image the model was given. Anything else: out, the same object."""
    try:
        return _tone_guard(out, base, r_frac)
    except Exception as e:
        _fault("tone_guard", e)
        return out


def _tone_guard(out, base, r_frac):
    if not TONE_ON:
        return out
    lo = L._lock_lum(out)
    m = lo.shape[0]
    ax = (np.arange(m) - m / 2 + 0.5) / (r_frac * m)
    if float(np.median(lo[np.hypot(ax[None, :], ax[:, None]) < 0.06])) < TONE_MIN:     # the cheap look: a dark pupil on the frame centre
        return out
    pc = L.pupil_circle(out, r_frac)
    if pc is None:
        return out
    core = np.hypot(ax[None, :] - pc[0], ax[:, None] - pc[1]) < 0.6 * pc[2]
    yo, ys = lo[core], L._lock_lum(base)[core]
    if yo.size < 30:
        return out
    co, cs = float(np.median(yo)), float(np.median(ys))
    if co < TONE_MIN or co - cs < TONE_EXCESS:
        return out
    tone = min(cs + 4.0, L.PUPIL_LOCK_TONE_MAX)
    S = out.size[0]
    R = r_frac * S
    w = max(L.PUPIL_LOCK_FEATHER * R, 1.5)
    x0, y0, ep = S / 2 + pc[0] * R, S / 2 + pc[1] * R, pc[3] * R
    c0, r0 = max(0, int(x0 - ep - w) - 1), max(0, int(y0 - ep - w) - 1)
    c1, r1 = min(S, int(math.ceil(x0 + ep + w)) + 2), min(S, int(math.ceil(y0 + ep + w)) + 2)
    blk = np.array(out.convert("RGB").crop((c0, r0, c1, r1))).astype(np.float32)
    dd = np.hypot((np.arange(c0, c1) + 0.5 - x0)[None, :], (np.arange(r0, r1) + 0.5 - y0)[:, None])
    a = 0.5 - 0.5 * np.cos(np.clip((ep + w / 2 - dd) / w, 0.0, 1.0) * math.pi)
    blk = np.clip(blk - a[..., None] * np.maximum(blk - tone, 0.0) + 0.5, 0, 255).astype(np.uint8)
    res = out.convert("RGB")
    res.paste(Image.fromarray(blk), (c0, r0))
    _log("tone", core=co, photo=cs, tone=tone)
    return res


# ----------------------------------------------------------------------------- 3. blue light on the pupil's edge of a warm iris (enhance)
EDGE_POLAR = (96, 0.005, -0.04, 0.22)   # angles, radial step, first and last radius past the render pupil's edge (iris radii)
EDGE_REF = (0.10, 0.20)   # the iris beyond, per angle (median over +-3 angles): the colour the edge should have
EDGE_NEAR = (-0.01, 0.06) # an arc lies on the pupil's edge: samples are counted here
EDGE_Q = 25.0             # a sample is lit, at most EDGE_B in b* and this much bluer (b* lower) than the iris beyond: the arc's core
EDGE_B = 5.0              # (blue or neutral on a warm iris is never its own colour)
EDGE_LIT = 18.0           # lit: L* above this (the dark rim of the pupil itself is for the grade)
EDGE_A = 14.0             # ...and at most this magenta (a*): blue or neutral light has a* -8 to 15 (29's patch: median 10), the violet fibres of
                          # 27 (an orange iris with a violet rim: a* 16-23, b* near 0) are the iris' own colour and are not light on its edge
EDGE_MIN = 15             # samples of the 96 x 15 in the near band. Read on the render after pupil_lock (the 55 fresh renders and the 469
                          # saved ones of the present machinery): 29 39-45, 15 17-36, 11 15-43, 18 (two renders of four) 20-49; the
                          # owner's four eyes, the violet 27 (with EDGE_A) and every other test frame 0-5
EDGE_LOOK = (6, 15.0)     # the cheap look, on a 128 px copy: at least this many lit (L* above EDGE_LIT), bluish (b* at most EDGE_B, a* at most
                          # EDGE_A + 4) pixels within 0.6 iris radii that are also this far under the iris' median b* (0.25-0.75 radii), else
                          # there is nothing to look at and the circle fit (the costly part) is skipped. Every render the full test flags passes it
EDGE_QSOFT = (6.0, 18.0)  # the repair, in the arc's angles: none at the first b* shortfall, full at the second (the bluish rest of it);
                          # angles up to 12 steps from a flagged one with two such samples belong to the arc
EDGE_REACH = (0.09, 0.14) # the repair is full to the first and gone at the second radius past the edge
EDGE_TONE = 2.5           # the colour given back is scaled by the pixel's brightness over the iris' (down to 1 / this): dark stays dark


def _lab_planes(a):
    lab = L.srgb_to_lab(a)
    return lab[..., 0], lab[..., 1], lab[..., 2]


def _polar(arr, pc, r_frac, S):
    """RGB samples of arr on EDGE_POLAR's angles x radii round the circle pc: (radii past the edge, samples)."""
    R = r_frac * S
    na, dr, d0, d1 = EDGE_POLAR
    t = (np.arange(na) + 0.5) / na * 2 * math.pi - math.pi
    dd = np.arange(d0, d1 + 1e-9, dr)
    r = pc[3] + dd
    x = np.clip(S / 2 - 0.5 + (pc[0] + r[None, :] * np.cos(t)[:, None]) * R, 0, S - 1.001)
    y = np.clip(S / 2 - 0.5 + (pc[1] + r[None, :] * np.sin(t)[:, None]) * R, 0, S - 1.001)
    x0 = np.floor(x).astype(np.int32); y0 = np.floor(y).astype(np.int32)
    fx = (x - x0)[..., None]; fy = (y - y0)[..., None]
    a = arr.astype(np.float32)
    return dd, a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x0 + 1] * fx * (1 - fy) + a[y0 + 1, x0] * (1 - fx) * fy + a[y0 + 1, x0 + 1] * fx * fy


def edge_guard(out, r_frac):
    """Blue or cyan light on the pupil's edge of a warm iris: a window or the sky mirrored at the rim (29 a blue patch, 15 and 18 a
    thin arc), which the colour lock copies into the render's fibres. Measured on the render round its own pupil circle:
    per angle the colour of the iris beyond (EDGE_REF), then the lit samples on the edge (EDGE_NEAR) whose b* is EDGE_Q under
    it and at most EDGE_B, all angles together at least EDGE_MIN, on an iris that is warm (WARM_RENDER). Then the pixels within
    EDGE_REACH of the edge, in the angles of the arc, take that angle's iris colour in proportion to how much bluer they are
    (EDGE_QSOFT), keeping their own brightness. A blue or grey iris, less blue on the edge, or none: the same object."""
    try:
        return _edge_guard(out, r_frac)
    except Exception as e:
        _fault("edge_guard", e)
        return out


def _edge_guard(out, r_frac):
    if not EDGE_ON:
        return out
    S = out.size[0]
    if _lean(out, r_frac) > WARM_RENDER:
        return out
    small = np.asarray(out.convert("RGB").resize((128, 128), Image.BOX))
    rc = np.hypot(*np.meshgrid((np.arange(128) - 64 + 0.5) / (r_frac * 128), (np.arange(128) - 64 + 0.5) / (r_frac * 128)))
    Ls, As, Bs = _lab_planes(small)
    medb = float(np.median(Bs[(rc > 0.25) & (rc < 0.75)]))
    if int(((Ls > EDGE_LIT) & (Bs <= EDGE_B) & (As <= EDGE_A + 4.0) & (Bs <= medb - EDGE_LOOK[1]) & (rc < 0.6)).sum()) < EDGE_LOOK[0]:
        return out                                                              # no blue near the pupil anywhere: nothing to look at
    pc = L.pupil_circle(out, r_frac)
    if pc is None:
        return out
    arr = np.asarray(out.convert("RGB"))
    dd, P = _polar(arr, pc, r_frac, S)
    Lc, Ac, Bc = _lab_planes(P)
    na = P.shape[0]
    refm = (dd >= EDGE_REF[0]) & (dd <= EDGE_REF[1])
    sm = lambda v: np.median(np.stack([np.roll(v, k, 0) for k in range(-3, 4)], 0), 0)
    Rl, Rb = sm(np.median(Lc[:, refm], 1)), sm(np.median(Bc[:, refm], 1))
    near = (dd >= EDGE_NEAR[0]) & (dd <= EDGE_NEAR[1])
    lit = (Lc > EDGE_LIT) & (Lc > 0.25 * Rl[:, None]) & near[None, :]
    flag = lit & ((Rb[:, None] - Bc) >= EDGE_Q) & (Bc <= EDGE_B) & (Ac <= EDGE_A)
    if int(flag.sum()) < EDGE_MIN:
        return out
    hit = flag.any(1)
    soft = (lit & ((Rb[:, None] - Bc) >= EDGE_QSOFT[1]) & (Bc <= EDGE_B + 6.0) & (Ac <= EDGE_A + 4.0)).sum(1) >= 2
    for _ in range(12):
        hit = hit | (soft & (np.roll(hit, 1) | np.roll(hit, -1)))
    hit = hit.astype(np.float32)
    arc = np.clip(sum(np.roll(hit, k) for k in range(-2, 3)) / 2.0, 0.0, 1.0)
    Pu = np.clip(P + 0.5, 0, 255).astype(np.uint8)
    ycc = np.asarray(Image.fromarray(Pu.reshape(1, -1, 3)).convert("YCbCr")).reshape(P.shape).astype(np.float32)
    rcb, rcr, ry = sm(np.median(ycc[:, refm, 1], 1)), sm(np.median(ycc[:, refm, 2], 1)), sm(np.median(ycc[:, refm, 0], 1))
    R = r_frac * S
    reach = pc[3] + EDGE_REACH[1] + 0.02
    x0, x1 = max(0, int(S / 2 + (pc[0] - reach) * R)), min(S, int(S / 2 + (pc[0] + reach) * R) + 1)
    y0, y1 = max(0, int(S / 2 + (pc[1] - reach) * R)), min(S, int(S / 2 + (pc[1] + reach) * R) + 1)
    win = arr[y0:y1, x0:x1]
    Xg, Yg = np.meshgrid((np.arange(x0, x1) + 0.5 - S / 2) / R - pc[0], (np.arange(y0, y1) + 0.5 - S / 2) / R - pc[1])
    d = np.hypot(Xg, Yg) - pc[3]
    ang = (np.arctan2(Yg, Xg) + math.pi) / (2 * math.pi) * na - 0.5
    k0 = np.floor(ang).astype(np.int32); f = (ang - k0).astype(np.float32); k0 %= na; k1 = (k0 + 1) % na
    interp = lambda v: v[k0] * (1 - f) + v[k1] * f
    Lw, _, Bw = _lab_planes(win)
    ramp = lambda v, lo, hi: np.clip((v - lo) / (hi - lo), 0.0, 1.0)
    w = (ramp(interp(Rb) - Bw, *EDGE_QSOFT) * ramp(Lw, 12.0, EDGE_LIT) * interp(arc)
         * (1.0 - ramp(d, *EDGE_REACH)) * ramp(d, -0.03, -0.01)).astype(np.float32)
    if not w.max() > 0:
        return out
    w = np.clip(L._blur_f(w, max(1.0, S * 0.002)) * 1.5, 0.0, 1.0)
    y8, cb8, cr8 = [np.asarray(p).astype(np.float32) for p in Image.fromarray(win).convert("YCbCr").split()]
    k = np.clip((y8 + 4.0) / (interp(ry) + 4.0), 1.0 / EDGE_TONE, 1.0)
    ncb = cb8 + ((128.0 + (interp(rcb) - 128.0) * k) - cb8) * w
    ncr = cr8 + ((128.0 + (interp(rcr) - 128.0) * k) - cr8) * w
    fixed = np.asarray(Image.merge("YCbCr", (Image.fromarray(np.clip(y8 + 0.5, 0, 255).astype(np.uint8)),
                                             Image.fromarray(np.clip(ncb + 0.5, 0, 255).astype(np.uint8)),
                                             Image.fromarray(np.clip(ncr + 0.5, 0, 255).astype(np.uint8)))).convert("RGB"))
    res = arr.copy()
    res[y0:y1, x0:x1] = np.where((w > 0.004)[..., None], fixed, win)          # only the pixels the repair touches
    _log("edge", samples=int(flag.sum()), angles=int(hit.sum()))
    return Image.fromarray(res)


# ----------------------------------------------------------------------------- 4. the grade's pupil edge (studio_grade)
GRADE_GAP = 0.03          # pupil_circle's edge lies this far (iris radii) past the radius the grade reads for the pupil...
GRADE_BAND = 0.5          # ...and the band between them is pupil, not iris: its median brightness is under this share of the iris
GRADE_SECTORS = 0.6       # just beyond it (edge + 0.06 to + 0.18), in this share of the 24 sectors round the circle
GRADE_SPREAD = 25.0       # ...and a scene is lit inside the pupil: the spread of its brightness (90th minus 10th percentile over 0.75 of its
                          # radius, grey levels) is at least this. The three renders of 215102 read 39-49; every other render measured (the
                          # 37 fresh frames, the owner's 215120 saved twice) 0.7-13.3, a black pupil with its edge blur (215120: a gap of 0.031)
GRADE_SIDE = 256          # read on a copy this size


def grade_pupil(circ, lum, R, S, w0, rho0):
    """(cx, cy, edge) the grade should flatten the pupil to, or None. studio_grade reads the pupil's radius as the first
    radius where the median brightness climbs a quarter of the way from the core to the iris (rho0), about the frame
    centre or the pupil circle's centre. A room or a person lit inside a wide pupil (the owner's 215102: a grey wall, about
    40 of 255 over the last 0.05 of the pupil) lifts that median: rho0 0.44-0.46 for a pupil that ends at 0.50, and the band
    between stayed a grey ring round the black disc. circ: pupil_circle of the same brightness, (cx, cy, rho, edge) in iris radii
    from the frame centre, or None. Answered only when its edge lies GRADE_GAP past rho0, something is lit inside the pupil
    (GRADE_SPREAD) and in GRADE_SECTORS of the 24 sectors round it the band [rho0, edge] is darker than GRADE_BAND of the
    iris beyond it: a pupil, not a dark inner iris.
    lum: the grade's window of the luminance, starting at frame index w0; S: the frame side; R: the iris radius in pixels."""
    try:
        return _grade_pupil(circ, lum, R, S, w0, rho0)
    except Exception as e:
        _fault("grade_pupil", e)
        return None


def _grade_pupil(circ, lum, R, S, w0, rho0):
    if not GRADE_ON or circ is None or rho0 is None or circ[3] - rho0 < GRADE_GAP:
        return None
    n = lum.shape[0]
    m = min(n, GRADE_SIDE)
    small = np.asarray(Image.fromarray(np.ascontiguousarray(lum, dtype=np.float32), mode="F").resize((m, m), Image.BOX), dtype=np.float32)
    ax = (w0 + (np.arange(m) + 0.5) * n / m - S / 2.0) / R
    X, Y = ax[None, :] - circ[0], ax[:, None] - circ[1]
    d = np.hypot(X, Y)
    core = small[d < 0.75 * circ[2]]
    if core.size < 30 or float(np.percentile(core, 90) - np.percentile(core, 10)) < GRADE_SPREAD:
        return None
    sec = ((np.arctan2(Y, X) + math.pi) / (2 * math.pi) * 24).astype(np.int32) % 24
    band = (d >= rho0) & (d < circ[3])
    ring = (d > circ[3] + 0.06) & (d < circ[3] + 0.18) & (np.hypot(ax[None, :], ax[:, None]) < 0.92)
    ok = tot = 0
    for k in range(24):
        b, r = band & (sec == k), ring & (sec == k)
        if b.sum() < 4 or r.sum() < 8:
            continue
        tot += 1
        ok += float(np.median(small[b])) < GRADE_BAND * float(np.median(small[r]))
    if tot < 12 or ok < GRADE_SECTORS * tot:
        return None
    return circ[0], circ[1], circ[3]      # (no log line: studio_grade runs in the regression guards, which compare printed output)
