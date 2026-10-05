# -*- coding: utf-8 -*-
"""collision: the COLLISION family of SnapEyes styles (ported from the scratch prototype). numpy + PIL only in this module's runtime.

Designs (BRIEF_V3_FINAL sections 2-3), every one with a dark powder version, a clean version and a filled ("universe") version:
  infinity   Collision Infinity: two irises overlap like an infinity sign, S weave, thin dark edge, powder in each
             eye's colours round the union and bursting at the two notches;  clean=True -> Clean Infinity
  kiss       Kiss Collision: d 1.70 R on a diagonal, crumbling seam, perpendicular burst
  trio       Trio Collision (N = 3): the measured H24 isosceles
  family     Family Colours (N = 4-8): zigzag, brick, ring, flower, cluster
  chain      Infinity Chain (N = 3-6): S weave on every link, d 1.40 R, 3:2 / 3:1 / column

Call:  res = render(design, irises, fmt=..., size=1024, names=[...], bg='dark' | 'universe', clean=False, opts={...})
       res.img (PIL RGB), res.info (timings, geometry, shares), res.scene, res.tiles, res.discs, res.comp, res.img8, res.particles
Switches for the owner's sign-offs (all render both ways): opts['zone_c'] (D8), opts['seam'] ('band' | 'hard', D13), opts['edge'] ('brief' | 'ref'),
opts['seam_dust'] (D15), opts['kiss_d'] (D18). Other opts: hairline, plates (default True), breakup (True), rotate (trio), flood (tests).
"""
from __future__ import annotations

# PORT of work package WP7A (step A): collision.py of the DG1 snapshot of the scratch prototype, verbatim but for the edits
# scripts/styles_tests/port_collision.py lists (imports, a bounded cache, the style ids out of the text); test_goldens_collision.py replays the edits on the scratch and the pixels of the
# scratch's own pictures.
# WP7B (step B) moved the seed and the place of the pixel decisions and nothing else (STEP_B of the same tool): see api/_lib/styles/seeds.py.

import copy
import math
import time

import numpy as np
from PIL import Image, ImageDraw

from .. import core as C
from .. import palette as PAL
from .. import pupil as PUPM
from .. import seeds as SD
from . import compositor as CC
from . import extra as EX
from . import fill as FL
from . import haze as HZ
from . import kit as K
from . import lens_mode as LM
from . import powder as PW
from . import raster as RS
from . import scenes as CL
from . import seam_plan as SP

BG_DARK = (2, 2, 4)                      # #020204: near-black that still counts as black in the Y < 3/255 share (T4); the brief says #040406
BG_CLEAN = (0, 0, 0)
DARK_EDGE_L = 26.0
WIND_SET = (0.0, 25.0, 50.0, 130.0, 155.0, 180.0)      # brief 3.1: CCW degrees, y up
STYLE = "collision"


class Result:
    pass


class NotOffered(ValueError):
    """The design is not offered for these irises (a bar pupil): the caller answers `available: false, why: <why>` and shows no picture."""

    def __init__(self, msg, why="not_offered"):
        super().__init__(msg)
        self.why = why


class DesignChanged(ValueError):
    """The plan froze a choice that the eyes of this render contradict (the plan says Collision Infinity and the pupils now say the Kiss geometry, a front
    order that does not fit the scene): never another picture than the approved one, so the caller holds the order. `why` names it."""

    def __init__(self, msg, why="design_changed"):
        super().__init__(msg)
        self.why = why


def place_disc_exact(iris, cx, cy, tgt, index=0):
    """fx.core.place_disc for a requested tight disc size `tgt` (px) instead of a requested radius: the graded frame whose tight disc is exactly tgt px
    (or the nearest one), the top-left rounded to whole pixels. The disc's exact (cx, cy, R) are what effects use."""
    L = C.L
    Sd0 = int(round(tgt / L.STUDIO_FILL))
    best = None
    for Sd in range(Sd0 - 3, Sd0 + 4):
        t = max(8, int(round(Sd * L.STUDIO_FILL)))
        if best is None or abs(t - tgt) < abs(best[1] - tgt):
            best = (Sd, t)
        if t == tgt:
            best = (Sd, t)
            break
    Sd, t = best
    frame = iris.graded(Sd)
    sq, tg = C._tight(frame)
    d = C.Disc()
    d.iris, d.index, d.Sd = iris, index, Sd
    d.g = np.ascontiguousarray(sq)
    d.alpha = L.disk_alpha(tg, tg / 2.0, C.FEATHER).astype(np.float32)
    d.x0, d.y0 = int(round(cx - tg / 2.0)), int(round(cy - tg / 2.0))
    d.cx, d.cy, d.R = d.x0 + tg / 2.0, d.y0 + tg / 2.0, tg / 2.0
    return d


# ----------------------------------------------------------------------------- parameters per design
def params(design, sc, n, clean=False, universe=False):
    """Powder parameters of a design (brief 3.1-3.4, round 2c AD tuning); universe = 40 % matter. Emission in R units: dust_lam / grain_lam /
    chunk_lam per R of exposed outline, big = BIG chips per eye (at most 12), L1 / L2 the emission e-fold (0.11 / 0.25 R)."""
    if design == "infinity":
        p = dict(dust_lam=1100, grain_lam=380, chunk_lam=16, chunk_L=0.07, big=6, L1=0.075, L2=0.10, cut=0.55, b=0.36, blobs_pair=3, fg=(0, 0), haze=0.0, haze_reach=0.42, haze_floor=0.09, jet_scale=0.5,
                 cloud=0.18, cloud_cap=0.55, cloud_rim=0.25, cloud_floor=0.25, cloud_gamma=1.5, cloud_reach=0.35, plate_gain=0.0,
                 jet=lambda nc, geo: dict(Bg=500, Bc=14, phi_c=38, r_d=0.45, r_m=0.85))
    elif design == "kiss":
        p = dict(dust_lam=520, grain_lam=150, chunk_lam=25, big=6, L1=0.09, L2=0.20, b=0.15, blobs_pair=3, fg=(0, 0), haze=0.0, haze_reach=0.5, cut=0.5, river_reach=1.25, river_n=1500, river_nc=16, cloud=0.0, plate_gain=0.0, river_gain=0.0,
                 jet=lambda nc, geo: (dict(Bg=700, Bc=24, phi_c=30, r_d=0.80, r_m=1.20) if nc.strong else dict(Bg=420, Bc=14, phi_c=45, r_d=0.50, r_m=0.90)))
    elif design == "trio":
        def jet(nc, geo, sc=sc):
            if {nc.i, nc.j} == {sc.info["base_left"], sc.info["base_right"]}:
                return dict(Bg=600, Bc=20, phi_c=42, r_d=0.50, r_m=0.90)
            return dict(Bg=420, Bc=14, phi_c=42, r_d=0.40, r_m=0.75)
        p = dict(dust_lam=590, grain_lam=175, chunk_lam=45, big=6, L1=0.10, L2=0.24, b=0.15, blobs_total=3, fg=(0, 0), haze=0.0, haze_reach=0.55, plate_gain=0.0, cloud=0.22, cloud_cap=0.5, cloud_floor=0.30, cloud_gamma=1.6, cloud_reach=0.32, cloud_rim=0.25, cloud_black=0.03, jet=jet)
    elif design == "family":
        ne = max(CL.n_eff(sc), 1.0)
        big = n >= 6
        p = dict(dust_lam=520 if big else 700, grain_lam=170 if big else 220, chunk_lam=25 if big else 40, big=4, L1=0.10, L2=0.24, b=0.15,
                 blobs_total=8 if big else 5, fg=(0, 0), haze=0.0, haze_reach=0.5, plate_gain=0.0, cloud=0.18 if big else 0.24, cloud_cap=0.5, cloud_floor=0.32, cloud_gamma=1.6, cloud_reach=0.32, cloud_rim=0.3, cloud_black=0.03,
                 jet=lambda nc, geo, ne=ne: dict(Bg=min(700, 4200 / ne), Bc=min(24, 90 / ne), phi_c=38, r_d=0.45, r_m=0.85))
    elif design == "chain":
        ne = max(CL.n_eff(sc), 1.0)
        p = dict(dust_lam=420, grain_lam=120, chunk_lam=20, big=3, L1=0.10, L2=0.24, b=0.15, blobs_total=3, fg=(0, 0), haze=0.0, cut=0.6, plate_gain=0.0, cloud=0.12, cloud_cap=0.45, cloud_floor=0.32, cloud_gamma=1.6, cloud_reach=0.32, cloud_rim=0.2, cloud_black=0.03,
                 jet=lambda nc, geo, ne=ne: dict(Bg=min(350, 2100 / ne), Bc=min(12, 45 / ne), phi_c=38, r_d=0.45, r_m=0.85))
    else:
        raise ValueError(design)
    if design != "infinity":                                   # round 2c: the same size discipline as the infinity (fewer, smaller chunks; brighter small chips)
        p["chunk_lam"] = p["chunk_lam"] * 0.55
        p["big"] = max(2, int(p["big"] * 0.6))
    p.setdefault("gain_grain", 1.35)
    p.setdefault("gain_dust", 1.30)
    if universe:
        p = dict(p)
        for kk in ("dust_lam", "grain_lam", "chunk_lam"):
            p[kk] = p[kk] * 0.40
        p["big"] = max(2, int(p["big"] * 0.5))
        bj = p["jet"]
        p["jet"] = lambda nc, geo, bj=bj: {**bj(nc, geo), "Bg": bj(nc, geo)["Bg"] * 0.5, "Bc": bj(nc, geo)["Bc"] * 0.4}
        p["haze"] = p["haze"] * 0.5
    return p


# ----------------------------------------------------------------------------- colours and edge modes
def make_pals(irises):
    rots = PAL.pair_hues(irises)
    return [PAL.Pal(ir, r) for ir, r in zip(irises, rots)]


_LST = C.BoundedCache(32)


def _canon_disc(iris):
    """The tight graded disc of the canonical 256 grade (resolution independent decisions: fronts and edge modes are the same at every size)."""
    k = iris.digest
    got = _LST.get(k)
    if got is None:
        sq, t = C._tight(iris.graded(C.REF_SIDE))
        R = t / 2.0
        ax = (np.arange(t, dtype=np.float32) + 0.5 - R) / R
        rr = np.sqrt(ax[None, :] ** 2 + ax[:, None] ** 2)
        th = np.arctan2(ax[:, None] + 0 * ax[None, :], ax[None, :] + 0 * ax[:, None])
        m = (rr >= 0.60) & (rr <= 0.95)
        Ls = np.zeros(sq.shape[:2], np.float32)
        Ls[m] = C.lch(sq[m].astype(np.float64) / 255.0)[0]
        got = _LST.put(k, (m, th, Ls))
    return got


def band_lstar(iris, phi_seam, span=math.radians(60.0)):
    """Mean L* of the iris band 0.60-0.95 R within +-span of the seam direction phi_seam (screen angle toward the partner), on the canonical grade."""
    m, th, Ls = _canon_disc(iris)
    dang = np.abs((th - phi_seam + math.pi) % (2 * math.pi) - math.pi)
    sel = m & (dang <= span)
    return float(Ls[sel].mean()) if sel.any() else 50.0


def decide_fronts(sc, lstar, cap=2):
    """Single-front rules (brief 1.3.2): the iris whose seam-side band has the higher mean L* is in front (ties, delta L* < 3: the lower-left
    one, A for a pair). Stacking solver (brief 1.1 rule 7, T19): among ALL orientations of the undecided contacts pick the one with no iris
    the back one at more than `cap` contacts and no 3-cycle among mutually touching irises (a triple region needs one top iris), and among
    those the one that departs least from the luminance rule (sum of the flipped contacts' margins); exhaustive for up to 16 contacts, the
    layouts of the brief have at most 13. lstar(iris_index, phi) -> mean L* of that iris's band toward direction phi. Deterministic.
    Returns {rule: margin}."""
    pend = [i for i, r in enumerate(sc.rules) if r.mode == "stack"]
    if not pend:
        return {}
    marg, pref = {}, {}
    for i in pend:
        r = sc.rules[i]
        pa = math.atan2(r.uy, r.ux)
        dl = lstar(r.a, pa) - lstar(r.b, pa + math.pi)
        if abs(dl) < 3.0:
            ca, cb = sc.centres[r.a], sc.centres[r.b]
            a_front = (ca[1] - ca[0] * 0.05) >= (cb[1] - cb[0] * 0.05)          # lower-left first (screen y grows downward)
        else:
            a_front = dl > 0
        pref[i] = 1 if a_front else 0
        marg[i] = abs(dl)
    E = len(pend)
    fixed = [(i, r) for i, r in enumerate(sc.rules) if r.mode in ("front_a", "front_b")]
    n = sc.n
    if E <= 16:
        masks = np.arange(1 << E, dtype=np.int64)
        bits = ((masks[:, None] >> np.arange(E)[None, :]) & 1).astype(np.int8)          # 1: a in front
        cnt = np.zeros((len(masks), n), np.int16)
        top = np.zeros((len(masks), len(sc.rules)), np.int16)
        for e, i in enumerate(pend):
            r = sc.rules[i]
            cnt[:, r.b] += bits[:, e]                # a in front: b is the back one
            cnt[:, r.a] += 1 - bits[:, e]
            top[:, i] = np.where(bits[:, e] == 1, r.a, r.b)
        for i, r in fixed:
            cnt[:, (r.b if r.mode == "front_a" else r.a)] += 1
            top[:, i] = r.a if r.mode == "front_a" else r.b
        viol = np.maximum(cnt - cap, 0).sum(1).astype(np.int32)
        pair = {}
        for ri, r in enumerate(sc.rules):
            pair[(min(r.a, r.b), max(r.a, r.b))] = ri
        tris = [(i, j, k) for (i, j) in pair for k in range(j + 1, n) if (i, k) in pair and (j, k) in pair]
        for (i, j, k) in tris:
            t1, t2, t3 = top[:, pair[(i, j)]], top[:, pair[(i, k)]], top[:, pair[(j, k)]]
            # cyclic iff every iris wins exactly one of its two contacts of the triangle
            wi = (t1 == i).astype(np.int8) + (t2 == i)
            wj = (t1 == j).astype(np.int8) + (t3 == j)
            wk = (t2 == k).astype(np.int8) + (t3 == k)
            viol += 3 * ((wi == 1) & (wj == 1) & (wk == 1)).astype(np.int32)
        cost = np.zeros(len(masks), np.float64)
        for e, i in enumerate(pend):
            cost += np.where(bits[:, e] != pref[i], marg[i] + 0.01, 0.0)
        best = np.lexsort((masks, cost, viol))[0]
        for e, i in enumerate(pend):
            sc.rules[i].mode = "front_a" if bits[best, e] == 1 else "front_b"
    else:
        for i in pend:
            sc.rules[i].mode = "front_a" if pref[i] else "front_b"
    return dict(marg)


def back_counts(sc):
    cnt = {}
    for r in sc.rules:
        if r.mode in ("front_a", "front_b"):
            b = r.b if r.mode == "front_a" else r.a
            cnt[b] = cnt.get(b, 0) + 1
    return cnt


def rebuild_order(sc):
    """Merge order: irises in index order, each with the partners it touches that were merged before it (the per-pixel occupant rule resolves
    where three irises meet)."""
    order = [(0, [])]
    for j in range(1, sc.n):
        order.append((j, [((r.a if r.b == j else r.b), ri) for ri, r in enumerate(sc.rules) if (r.b == j and r.a < j) or (r.a == j and r.b < j)]))
    sc.order = order


# ----------------------------------------------------------------------------- text
def layout_text(sc, names, date=None):
    """Caption layout per brief 1.5.7: [(text, font size, tracking em, x0, baseline, width, kind)] for the customer's strings only."""
    if not names or not sc.text_lines:
        return []
    sep = " ∞ " if sc.info.get("kind") in ("infinity", "clean") or str(sc.info.get("layout", "")).startswith("chain") else (" & " if sc.n == 2 else " · ")
    text = sep.join(n.upper() for n in names)
    probe = ImageDraw.Draw(Image.new("L", (8, 8)))
    out = []
    for kind, cx, base, cap, maxw in sc.text_lines:
        t = text if kind == "names" else (date or "")
        if not t:
            continue
        size = max(6, int(round(cap / 0.70)))
        tr = 0.18 if kind == "names" else 0.30
        f = C.L._font("Cinzel.ttf", size, "Regular")
        w = probe.textlength(t, font=f) + tr * size * (len(t) - 1)
        while w > maxw and size > 6:
            size -= 1
            f = C.L._font("Cinzel.ttf", size, "Regular")
            w = probe.textlength(t, font=f) + tr * size * (len(t) - 1)
        out.append((t, size, tr, cx - w / 2, base, w, kind))
    return out


def text_boxes(tl):
    return [(x0, base - 0.80 * size, x0 + w, base + 0.25 * size) for (t, size, tr, x0, base, w, kind) in tl]


def draw_names(img, sc, names, date=None, tl=None):
    """The customer's names (the only text): caps Cinzel, tracking +0.18 em, #C9B8A0, the date at 55 %."""
    tl = tl if tl is not None else layout_text(sc, names, date)
    d = ImageDraw.Draw(img)
    drawn = []
    col = (201, 184, 160)
    for (t, size, tr, x0, base, w, kind) in tl:
        f = C.L._font("Cinzel.ttf", size, "Regular")
        x = x0
        fill = col if kind == "names" else tuple(int(0.55 * v) for v in col)
        for i, ch in enumerate(t):
            d.text((x, base), ch, font=f, fill=fill, anchor="ls")
            x += d.textlength(t[:i + 1], font=f) - d.textlength(t[:i], font=f) + tr * size
        drawn.append(t)
    return drawn


# ----------------------------------------------------------------------------- pupils
def _pupil_fn(disc, pup):
    """Callable(xs, ys, dil) -> bool mask of the pupil dilated by dil (R) on canvas pixel centres."""
    cx, cy, R = disc.cx, disc.cy, disc.R
    rt = pup["r_theta"]
    m = len(rt)
    pcx, pcy = cx + pup["cx"] * R, cy + pup["cy"] * R

    def fn(xs, ys, dil=0.0):
        dx = (xs - pcx) / R
        dy = (ys - pcy) / R
        r = np.sqrt(dx * dx + dy * dy)
        th = np.arctan2(dy + 0 * dx, dx + 0 * dy) % (2 * math.pi)
        f = th * (m / (2 * math.pi)) - 0.5
        i0 = np.floor(f).astype(np.int64)
        w = f - i0
        edge = rt[i0 % m] * (1 - w) + rt[(i0 + 1) % m] * w
        return r <= edge + dil
    return fn


def _kiss_strength(sc, rnd):
    """Kiss: one notch is the strong end (60/40); the design seed flips which."""
    flip = rnd.uniform() < 0.5
    for nc in sc.notches:
        if nc.kind == "outer":
            nc.strong = (nc.side > 0) != flip


def wind_angles(design, geo, rnd):
    """Wind direction (screen radians) per iris: pairs one common direction from the brief's set, groups away from the centroid."""
    if design in ("trio", "family", "chain") and geo.n >= 3:
        cx, cy = geo.centroid
        return [math.atan2(geo.c[k][1] - cy, geo.c[k][0] - cx) if math.hypot(geo.c[k][0] - cx, geo.c[k][1] - cy) > 1e-3 else 0.0 for k in range(geo.n)]
    a = math.radians(WIND_SET[int(rnd.uniform() * len(WIND_SET))] + rnd.uniform(None, -10.0, 10.0))
    return [-a] * geo.n          # brief angles are CCW with y up, the engine's are clockwise with y down


def measure_edge_deltas(img8, sc, edge_modes, T=320):
    """Contact-edge contrast at a T px tile (brief 6.2 T10): per rule, the median over the visible front arc of L*(back iris band at 0.09 R outside the
    limb) minus the darkest L* across the limb (0.96-1.04 R). 'hairline' for rules drawn in hairline mode. Returns {rule_index: delta or 'hairline'}."""
    scale = T / max(sc.W, sc.H)
    small = np.asarray(Image.fromarray(img8).resize((max(1, int(round(sc.W * scale))), max(1, int(round(sc.H * scale)))), Image.BOX)).astype(np.float64) / 255.0
    Hs, Ws = small.shape[:2]
    out = {}
    for ri, r in enumerate(sc.rules):
        if edge_modes.get(ri) == "hairline":
            out[ri] = "hairline"
            continue
        if r.mode == "weave":
            front, back, need_side = r.a, r.b, True
        else:
            front = r.a if r.mode == "front_a" else r.b
            back = r.b if front == r.a else r.a
            need_side = False
        cf, cb = np.array(sc.centres[front]), np.array(sc.centres[back])
        Rf = sc.R[front]
        ux, uy = (cb - cf) / np.linalg.norm(cb - cf)
        a0 = math.atan2(uy, ux)
        vals_v, vals_b = [], []
        for tt in np.linspace(-0.45, 0.45, 21):
            if need_side and tt < 0.12:
                continue
            dth = math.asin(float(np.clip(tt, -0.99, 0.99)))
            px, py = cf[0] + Rf * math.cos(a0 + dth), cf[1] + Rf * math.sin(a0 + dth)
            if math.hypot(px - cb[0], py - cb[1]) > sc.R[back] * 0.9:
                continue
            lo = []
            for rho in np.linspace(0.96, 1.04, 9):
                qx = (cf[0] + Rf * rho * math.cos(a0 + dth)) * scale
                qy = (cf[1] + Rf * rho * math.sin(a0 + dth)) * scale
                if 0 <= int(qy) < Hs and 0 <= int(qx) < Ws:
                    lo.append(float(C.lch(small[int(qy), int(qx)])[0]))
            bx = (cf[0] + Rf * 1.09 * math.cos(a0 + dth)) * scale
            by = (cf[1] + Rf * 1.09 * math.sin(a0 + dth)) * scale
            if lo and 0 <= int(by) < Hs and 0 <= int(bx) < Ws:
                vals_v.append(min(lo))
                vals_b.append(float(C.lch(small[int(by), int(bx)])[0]))
        if vals_v:
            out[ri] = float(np.median(np.array(vals_b) - np.array(vals_v)))
    return out


# ----------------------------------------------------------------------------- decisions
def decisions(sc_can, irises, design, design0, info, o, frozen):
    """The discrete choices of one artwork that depend on the PIXELS of its irises, decided ONCE on a copy of the canonical (1024 px) scene, so that they are
    the same at every size, or taken from the plan (frozen) when the plan fixed them before the render: which iris is in front at each contact the scene
    leaves undecided (the brighter seam side; the stacking solver for the groups), whether a contact is drawn as a hairline (its back band is dark) and,
    decided earlier in render() from the same irises, the overlap fallback of Collision Infinity and its woven or stacked lens. The master of an order is
    made from ANOTHER image of the same eyes than its preview (a 4096 px render registered to the 1024 px restoration), whose band luminance can differ by
    a fraction of a unit: a tie (a difference under 3) could go the other way, so the plan stores what the preview decided and the master obeys it.
    design is the design drawn (a fallen back infinity is a kiss), design0 the one asked for. Returns {fronts: {rule index: mode}, pend: a scene rule was left
    to decide (the merge order is built again), lens_stack, hairline: [rule index], info: facts to report, frozen: the plan's record of all of it}.
    DesignChanged when a frozen choice does not fit this scene."""
    s = copy.deepcopy(sc_can)
    pend = [i for i, r in enumerate(s.rules) if r.mode == "stack"]
    lens_stack = info.get("lens_mode_used") == "stack" and design == "infinity" and len(s.rules) == 1
    facts, fronts = {}, {}
    if "fronts" in frozen:
        fz = frozen["fronts"]
        ok = (isinstance(fz, dict) and all(isinstance(k, (str, int)) and str(k).isdigit() for k in fz) and all(v in ("front_a", "front_b") for v in fz.values())
              and sorted(int(k) for k in fz) == sorted(pend + ([0] if lens_stack else [])))
        if not ok:
            raise DesignChanged("the plan's front order %r does not fit this scene (contacts left to decide: %r)" % (fz, pend))
        fronts = {int(k): v for k, v in fz.items()}
        for i, m in fronts.items():
            s.rules[i].mode = m
    else:
        if pend:
            if design == "kiss":
                r = s.rules[0]
                pa = math.atan2(r.uy, r.ux)
                la, lb = band_lstar(irises[0], pa), band_lstar(irises[1], pa + math.pi)
                r.mode = "front_b" if lb - la > 3.0 else "front_a"             # ties (and A brighter): A, the lower-left eye, in front
                facts["front"] = r.mode
            else:
                cache = {}

                def lstar(k, phi):
                    key = (k, round(phi, 3))
                    if key not in cache:
                        cache[key] = band_lstar(irises[k], phi)
                    return cache[key]
                facts["stack"] = decide_fronts(s, lstar)
            fronts = {i: s.rules[i].mode for i in pend}
        if lens_stack:
            # DG1 rung 2: the stack lens: one iris in front over the whole lens (brief 1.3.2: the one whose seam-side band is brighter, ties A), no weave, no seam
            r = s.rules[0]
            pa = math.atan2(r.uy, r.ux)
            la, lb = band_lstar(irises[0], pa), band_lstar(irises[1], pa + math.pi)
            r.mode = "front_b" if lb - la > 3.0 else "front_a"
            facts["front"] = r.mode
            fronts[0] = r.mode
    nr = len(s.rules)
    if "hairline" in frozen:
        hz = frozen["hairline"]
        if not (isinstance(hz, list) and all(isinstance(i, int) and not isinstance(i, bool) and 0 <= i < nr for i in hz)):
            raise DesignChanged("the plan's hairline contacts %r do not fit this scene (%d contacts)" % (hz, nr))
        natural = sorted(set(hz))
    else:
        natural = []
        for ri, r in enumerate(s.rules):
            pa = math.atan2(r.uy, r.ux)
            la = band_lstar(irises[r.a], pa)
            lb = band_lstar(irises[r.b], pa + math.pi)
            back_L = min(la, lb) if r.mode == "weave" else (lb if r.mode == "front_a" else la)
            if back_L < DARK_EDGE_L:
                natural.append(ri)
    out = {"fronts": {str(i): m for i, m in sorted(fronts.items())}, "hairline": natural}
    if design0 == "infinity":
        out["fallback"] = "overlap_fallback" if info.get("overlap_fallback") else None
        if not info.get("overlap_fallback"):
            out["lens"] = info.get("lens_mode_used")
    return {"fronts": fronts, "pend": bool(pend), "lens_stack": bool(lens_stack), "hairline": list(range(nr)) if o.get("hairline") else natural, "info": facts, "frozen": out}


# ----------------------------------------------------------------------------- main
def render(design, irises, fmt=None, size=1024, names=None, date=None, bg="dark", clean=False, opts=None, layout=None, key=None, frozen=None, plan_only=False):
    """One artwork. See the module docstring. Returns a Result. WP7B (step B): key is the plan's seed key (seeds.py: the style, the layout, the options and the
    plates version; the design drawn, the ground and the clean flag are filled in here), from which and from the eyes' ids (irises[k].eye_id) the seed is
    made; opts seed_mode "legacy" seeds as before step B (the bytes of the irises, the design, the scene key and the names). frozen is what the plan fixed
    before the render (decisions() names its fields: fallback, lens, fronts, hairline): taken from it instead of decided from these irises. plan_only stops
    after those decisions and the seed (res.frozen, res.seed, res.info) and draws nothing: the plan pass."""
    o = dict(opts or {})
    frozen = dict(frozen or {})
    design0 = design
    t0 = time.perf_counter()
    res = Result()
    n = len(irises)
    has_names = bool(names)
    universe = bg == "universe" and not clean
    pups = [K.pupil(ir) for ir in irises]
    info = {"design": design, "bg": bg, "clean": clean, "n": n}
    gates = [K.gate(ir) for ir in irises]
    info["input_gate"] = gates
    info["gate_fail"] = [i for i, g in enumerate(gates) if not g["ok"]]
    info["pupil_classes"] = [p_.get("cls") for p_ in pups]
    if "bar" in info["pupil_classes"]:
        # D17: a bar-pupil iris (horse, goat) is a true ellipse (the animals family, an_core): it is never overlapped here and never cropped to a circle
        info["not_offered"] = "bar pupil: the collision family does not overlap horizontal bars"
        if o.get("strict_gate") or not o.get("allow_bar"):
            # DG1 review fix: the collision family REFUSES a bar pupil (brief 3.1 'horizontal bars never overlap (not offered)', D17, INTEGRATION_SPEC C9 `available: false, why: bar_pupil`);
            # it used to render a picture and only set info['not_offered'], so a caller that did not look at the flag shipped a bar pupil overlapped like a round one.
            # opts allow_bar=True keeps the old behaviour for the boards and the tests that want the flag only.
            raise NotOffered(info["not_offered"], why="bar_pupil")
    if o.get("strict_gate") and info["gate_fail"]:
        raise ValueError("input gate: eyelid or skin remnants in iris %s (restoration must remove them)" % info["gate_fail"])
    if (design in ("infinity", "kiss") and n != 2) or (design == "trio" and n != 3):
        raise ValueError("wrong number of eyes for " + design)
    kind = {"infinity": "clean" if clean else "infinity", "kiss": "kiss"}.get(design)
    plan_pre = None
    if design in ("infinity", "kiss"):
        fmt = fmt or "3:2"
        tmp = CL.pair_scene(fmt, size, 1.3, has_names, bool(date), kind)
        u = (tmp.rules[0].ux, tmp.rules[0].uy)
        ra = PUPM.reach(pups[0], u)
        rb = PUPM.reach(pups[1], (-u[0], -u[1]))
        if design == "infinity":
            d_over_R, raw, over = CL.solve_infinity_d(ra, rb)
            if "fallback" in frozen:
                if frozen["fallback"] == "overlap_fallback":
                    over = True                      # the plan drew the Kiss geometry for these pupils: so does every render of the order
                elif over:
                    raise DesignChanged("the plan draws the infinity overlap, but the pupils of these eyes reach %.3f R (the limit is the Kiss fallback)" % raw)
            info.update(d_raw=raw, reach=(ra, rb), overlap_fallback=bool(over))
            if over:
                design, kind = "kiss", "kiss"
                d_over_R = o.get("kiss_d", CL.D_KISS)
            elif (frozen.get("lens") or o.get("lens_mode", "auto")) in ("auto", "stack", "weave"):
                # DG1 rung 2 (fx/lens_mode.py): the automatic woven lens / stack lens decision, from the plan of the weave on the canonical grade (same at every size)
                t_lm = time.perf_counter()
                pl0 = SP.plan_seam(irises[0], irises[1], d_over_R, u[0], u[1], pups[0], pups[1], C, mode=o.get("plan_mode", "plan"), beta=o.get("beta", CC.Cfg.beta))
                plan_pre = (pl0, d_over_R)                       # reused as the weave plan below (the snapped canonical geometry differs from the solver's d by < 0.002 R)
                lens_used = LM.decide(pl0.info, frozen.get("lens") or o.get("lens_mode", "auto"))
                info.update(lens_mode_used=lens_used, lens_K=round(pl0.info["K_chosen"], 2), lens_decide_s=round(time.perf_counter() - t_lm, 3))
                if lens_used == "stack":
                    d_over_R = LM.stack_distance(d_over_R)
                    info.update(stack_d=d_over_R, fallback="stack_contrast")
        else:
            d_over_R = o.get("kiss_d", CL.D_KISS)
        build = lambda sz: CL.pair_scene(fmt, sz, d_over_R, has_names, bool(date), kind)
    elif design == "trio":
        build = lambda sz: CL.trio_scene(fmt or "1:1", sz, has_names, bool(date), rotate=o.get("rotate", 0), base_mode=o.get("trio_base", "crumble"))
    elif design == "family":
        build = lambda sz: CL.family_scene(n, layout, fmt, sz, has_names, bool(date))
    elif design == "chain":
        fmt_c = fmt or ("3:2" if n <= 4 else "3:1")
        u_c = (0.0, 1.0) if fmt_c == "9:19.5" else (1.0, 0.0)
        d_need = max(1.0 + max(PUPM.reach(pups[i], u_c), PUPM.reach(pups[i + 1], (-u_c[0], -u_c[1]))) + CL.D_INF_MARGIN for i in range(n - 1))
        info["chain_d_need"] = d_need
        build = lambda sz: CL.chain_scene(n, fmt_c, sz, has_names, bool(date), d_over_R=d_need)
    else:
        raise ValueError(design)
    sc = build(size)
    CAN = 1024
    sc_can = build(CAN)                       # the matter is emitted on this canonical (unsnapped, 1024 px) geometry and scaled: 4096 == 1024
    kscale = sc.W / float(sc_can.W)
    info["design_used"] = "stack" if info.get("lens_mode_used") == "stack" else design
    W, H = sc.W, sc.H
    # -- discs ---------------------------------------------------------------------------------
    g0 = sum(ir.grade_seconds for ir in irises)
    # the canonical (1024 px) discs: the geometry every size derives from. A 2048 / 4096 render places its discs at EXACT multiples of the canonical
    # snapped centres and radii, so the 4096 picture is the 1024 picture sample for sample (round 2c: an iris that is half a pixel off between two sizes
    # loses most of its SSIM in the fibres; this is what kept T9 at 0.963)
    d1 = [C.place_disc(ir, c[0], c[1], r, i) for i, (ir, c, r) in enumerate(zip(irises, sc_can.centres, sc_can.R))]
    sc_can.refresh(d1)
    if size == CAN:
        discs = d1
    elif size > CAN and size % CAN == 0 and o.get("exact_scale", True):
        kx = size // CAN
        discs = [place_disc_exact(ir, d.cx * kx, d.cy * kx, int(round(2 * d.R * kx)), i) for i, (ir, d) in enumerate(zip(irises, d1))]
    else:
        discs = [C.place_disc(ir, c[0], c[1], r, i) for i, (ir, c, r) in enumerate(zip(irises, sc.centres, sc.R))]
    sc.refresh(discs)
    grade_s = sum(ir.grade_seconds for ir in irises) - g0
    for ir in irises:
        ir.ring
    t1 = time.perf_counter()
    mem = {}
    if o.get("mem"):
        mem["after_discs"] = K.peak_rss_mb()
    # -- fronts and order (WP7B: decided once on the canonical scene, or the plan's) ------------------
    dec = decisions(sc_can, irises, design, design0, info, o, frozen)
    for ri, mode in dec["fronts"].items():
        sc.rules[ri].mode = mode
    if dec["lens_stack"]:
        sc.rules[0].crumble = False
    if dec["pend"]:
        rebuild_order(sc)
    info.update(dec["info"])
    info["rules"] = [(r.a, r.b, r.mode) for r in sc.rules]
    if o.get("seed_mode") == "legacy":
        seed = C.design_seed(irises, STYLE + "." + design + "." + bg + (".clean" if clean else ""), sc.key + "/" + ",".join(names or []))
    else:
        if not isinstance(key, dict):
            raise ValueError("a render needs the plan's seed key (seeds.py) or opts seed_mode legacy")
        # names, date, canvas, size and pixels are NOT in the seed: a typo in a name must never reshuffle the powder, a preview and a master draw the same
        seed = SD.seed_for_key([ir.eye_id for ir in irises], dict(key, design_used=info["design_used"], bg=bg, clean=bool(clean)))
    res.seed = seed
    res.frozen = dec["frozen"]
    info["frozen"] = dec["frozen"]
    if plan_only:
        info["d_over_R"] = [round(r.d / sc.R[r.a], 4) for r in sc.rules]
        res.img = res.img8 = res.comp = None
        res.info, res.scene, res.discs, res.irises, res.opts = info, sc, discs, irises, o
        return res
    pals = make_pals(irises)
    geo = PW.Geo(sc)
    geo_can = PW.Geo(sc_can)
    # -- tiles, edge modes ---------------------------------------------------------------------
    tiles = [CC.iris_tile(d, i) for i, d in enumerate(discs)]
    edge_modes, hair_cols = {ri: "hairline" for ri in dec["hairline"]}, {}
    for k in range(n):
        Lh, Ch, hh = C.lch(pals[k].ring.mean(0))
        hair_cols[k] = np.asarray(C.from_lch(70.0, min(float(Ch) * 1.1, 60.0), float(hh)), np.float32) * 255.0
    seam_mode = o.get("seam", "plan")
    cfg = CC.Cfg(preset=o.get("edge", "brief"), zone_c=o.get("zone_c", True), band=(0.01 if seam_mode == "hard" else 0.04), seam=seam_mode,
                 seed=int(seed % 100003), **{k_: o[k_] for k_ in ("seam_hw", "seam_amp", "seam_lam", "seam_bend", "seam_fine", "seam_wave", "blend", "pad", "dp_sigma", "dp_rho", "beta") if k_ in o})
    t_plan = time.perf_counter()
    if seam_mode == "plan":
        cfg.plans = {}
        for ri, r in enumerate(sc.rules):
            if r.mode != "weave":
                continue
            rc = sc_can.rules[ri]
            dR = rc.d / sc_can.R[rc.a]                          # the canonical (1024 px) geometry: the plan is the same at every size
            if o.get("plan_fn") is not None:
                cfg.plans[ri] = o["plan_fn"](irises[r.a], irises[r.b], dR, rc.ux, rc.uy, pups[r.a], pups[r.b])
            elif plan_pre is not None and abs(dR - plan_pre[1]) < 0.01 and o.get("support_budget", SP.SUPPORT_BUDGET) == SP.SUPPORT_BUDGET:
                cfg.plans[ri] = plan_pre[0]                    # the plan made for the rung 2 decision (same irises, same lens frame): not planned twice
            else:
                cfg.plans[ri] = SP.plan_seam(irises[r.a], irises[r.b], dR, rc.ux, rc.uy, pups[r.a], pups[r.b], C, mode=o.get("plan_mode", "plan"), beta=cfg.beta,
                                                support_budget=o.get("support_budget", SP.SUPPORT_BUDGET))
    info["plan_s"] = round(time.perf_counter() - t_plan, 3)
    pupil_fns = {k: _pupil_fn(discs[k], pups[k]) for k in range(n)}
    comp = CC.Compositor(sc, tiles, cfg, edge_modes, hair_cols, pupil_fns)
    # -- background and matter -----------------------------------------------------------------
    rnd = C.Rand(seed, "collision")
    mstats = {}
    res.particles = None
    res.mask_fn = None
    if universe:
        cv, finfo = FL.fill(sc, geo, irises, pals, discs, C.Rand(seed, "fill"), o.get("fill"), base=(sc_can, geo_can))
        info["fill"] = finfo
    else:
        cv = C.canvas(W, H, BG_CLEAN if clean else BG_DARK)
    if not clean:
        prm = params(design, sc, n, clean, universe)
        prm.update(o.get("prm", {}))
        prm["pv"] = (key or {}).get("pv")                        # the plates version of the spec reaches the haze's plate pick
        prm["plate_jets"] = bool(o.get("plates", True)) and prm.get("plate_jets", True)
        theta_w = wind_angles(design, geo_can, rnd)
        info["wind_deg"] = [round(math.degrees(-t) % 360, 1) for t in theta_w]
        if design == "kiss":
            _kiss_strength(sc_can, rnd)
        for nc in sc.notches:                               # the same flags on the snapped scene (plates, haze)
            for nc2 in sc_can.notches:
                if nc2.rule == nc.rule and nc2.side == nc.side:
                    nc.strong = nc2.strong
        tl = layout_text(sc, names, date)
        mask_fn = EX.matter_mask(sc, text_boxes(tl))
        res.mask_fn = mask_fn
        plist = [PW.halo(geo_can, rnd, prm, theta_w), PW.jets(geo_can, rnd, prm, "grain"), PW.outline_chunks(geo_can, rnd, prm, theta_w),
                 PW.jets(geo_can, rnd, prm, "chunk"), PW.blobs(geo_can, rnd, prm, theta_w), EX.fg_chunks(geo_can, rnd, prm, theta_w)]
        if design == "kiss" and prm.get("river", True) and o.get("plates", True):
            strong_can = any(nc.strong for nc in sc_can.notches if nc.kind == "outer" and nc.side > 0)
            plist += [PW.river_particles(geo_can, rnd, prm, strong_can, "grain"), PW.river_particles(geo_can, rnd, prm, strong_can, "chunk")]
        dd = [q.cat() for q in plist if len(q.a["x"]) and any(len(v) for v in q.a["x"])]
        d = {f: (np.concatenate([x[f] for x in dd]) if dd else np.zeros(0)) for f in PW.Particles.FIELDS}
        d["x"] = d["x"] * kscale
        d["y"] = d["y"] * kscale
        d["d"] = d["d"] * kscale
        use_plates = o.get("plates", True)
        if use_plates and (prm.get("cloud", 0.0) > 0 or prm.get("plate_gain", 0.0) > 0 or prm.get("river_gain", 0.0) > 0 or prm.get("haze", 0.0) > 0):
            # the soft photographed layers (cloud-plate haze, faint plate smoke) are computed ONCE on the canonical 1024 geometry with the 1K plates and
            # upsampled, so the 4096 master carries the same haze as the preview (T9) and its cost does not grow with the size
            Wc, Hc = sc_can.W, sc_can.H
            soft = np.zeros((Hc, Wc, 3), np.float32)
            mask_can = (lambda x, y, m=mask_fn, k=kscale: m(np.asarray(x) * k, np.asarray(y) * k))
            rs = C.Rand(seed, "soft")
            if prm.get("haze", 0.0) > 0:
                hz = PW.haze(geo_can, pals, rs, dict(prm, notch_haze=prm.get("notch_haze", 1.6) * 0.35), theta_w, Wc, Hc, sc_can.S, mask_can)
                if hz is not None:
                    soft += hz
            if prm.get("cloud", 0.0) > 0:
                info["cloud"] = HZ.cloud_haze(soft, geo_can, pals, C.Rand(seed, "cloud"), prm, Wc, Hc, mask_can)
            pinfo = {}
            if design == "kiss" and prm.get("river_gain", 0.0) > 0:
                strong_pos = any(nc.strong for nc in sc_can.notches if nc.kind == "outer" and nc.side > 0)
                pinfo["river"] = PW.plate_layers(soft, geo_can, pals, prm, rs, Wc, Hc, "river", strong_pos, mask_can)
            if prm.get("plate_gain", 0.0) > 0:
                pinfo["jets"] = PW.plate_layers(soft, geo_can, pals, prm, rs, Wc, Hc, "jets", True, mask_can)
            info["plates"] = pinfo
            FL.add_resized(cv, soft)
            del soft
        res.particles = {kk: v.copy() for kk, v in d.items()}
        mstats = PW.rasterise(cv, geo, pals, discs, d, rnd, K.atlas(), prm, True, mask_fn, int(seed % (2**31)))
        info["counts"] = mstats
        if o.get("breakup", True):
            info["breakup_px"] = EX.breakup(cv, geo, discs, rnd, prm, int(seed % 1000003))
    if o.get("mem"):
        mem["after_matter"] = K.peak_rss_mb()
    if o.get("flood"):
        cv += np.float32(o["flood"])
    t2 = time.perf_counter()
    res.cv = cv.copy() if o.get("keep_cv") else None
    img8 = C.finish(cv, [], seed, paste=False)
    del cv
    if o.get("mem"):
        mem["after_finish"] = K.peak_rss_mb()
    auto_hl = o.get("auto_hairline", True) and cfg.preset == "brief" and not clean and len(sc.rules) > 0
    res.img8_nopaste = img8.copy() if o.get("keep_cv") else None
    bg8 = img8.copy() if auto_hl else None
    comp.compose()
    comp.paste(img8)
    if auto_hl:
        # T10: a contact edge that does not read at 320 px (delta L* < 8 against the back iris) falls back to the hairline mode (brief 1.3.5)
        dl = measure_edge_deltas(img8, sc, edge_modes)
        weak = [ri for ri, v in dl.items() if v != "hairline" and v < 8.0]
        info["edge_delta_320"] = {ri: (v if v == "hairline" else round(v, 1)) for ri, v in dl.items()}
        if weak:
            for ri in weak:
                edge_modes[ri] = "hairline"
            info["auto_hairline"] = weak
            comp = CC.Compositor(sc, tiles, cfg, edge_modes, hair_cols, pupil_fns)
            comp.compose()
            img8[:] = bg8
            comp.paste(img8)
    info["edge_modes"] = dict(edge_modes)
    if o.get("mem"):
        mem["after_compose"] = K.peak_rss_mb()
        info["mem"] = mem
    res.seam_dust_mask = None
    res.seam_dust_alpha = None
    if o.get("seam_dust") and not clean:
        Pd, Ad, mask = EX.seam_dust(geo, pals, C.Rand(seed, "seamdust"), W, H, params(design, sc, n, clean, universe), discs)
        img8[:] = np.clip(Pd + img8.astype(np.float32) * (1.0 - Ad[..., None]) + 0.5, 0, 255).astype(np.uint8)
        res.seam_dust_mask = mask
        res.seam_dust_alpha = Ad
    t3 = time.perf_counter()
    img = Image.fromarray(img8)
    tl = layout_text(sc, names, date)
    info["text"] = draw_names(img, sc, names, date, tl)
    t4 = time.perf_counter()
    info.update(times=dict(grade=round(grade_s, 3), setup=round(t1 - t0 - grade_s, 3), matter=round(t2 - t1, 3), finish=round(t3 - t2, 3),
                           text=round(t4 - t3, 3), total=round(t4 - t0, 3), without_grade=round(t4 - t0 - grade_s, 3)))
    info["vis"] = comp.visible_share()
    info["d_over_R"] = [round(r.d / sc.R[r.a], 4) for r in sc.rules]
    res.img, res.img8, res.info, res.scene, res.tiles, res.discs, res.comp, res.cfg, res.geo = img, img8, info, sc, tiles, discs, comp, cfg, geo
    res.irises, res.pals, res.opts, res.pups, res.text_layout = irises, pals, o, pups, tl
    return res
