# -*- coding: utf-8 -*-
"""cx_powder: the powder of the collision designs (BRIEF_V3_FINAL 1.5, 3.0, 3.1-3.4), numpy only.

Everything is placed in units of R (of the iris a particle belongs to) and rasterised by cx_raster, so 4096 == 1024.

Measured on the owner's H11 (R = 313 px, both irises): about 1650 visible particles per iris = 366 per R of exposed outline; diameters
43 % < 0.6 % R, 24 % 0.6-1.0, 11 % 1.0-1.3, 12 % 1.3-1.9, 6 % 1.9-2.9, 2.7 % 2.9-4.5, 0.4 % > 4.5; density per R^2 in e (distance outside
the union) 793 / 1387 / 833 / 238 / 25 for e 0-0.1 / 0.1-0.2 / 0.2-0.3 / 0.3-0.45 / 0.45-0.6 R, then nothing: the halo is 0.5 R, not more.
The brief's profile n(e) = 0.85 exp(-e/L1)/L1 + 0.15 exp(-e/L2)/L2 (L1 0.18 R, L2 0.42 R) with the owner's onset (nothing hugs the limb)
reproduces that; chips carry the colour of their own iris and a share p(s) = 0.05 + 0.35 exp(-(s / 0.25 R)^2) of the partner's colour at
the notches.
"""
from __future__ import annotations

# PORT of work package WP7A (step A): cx_powder.py of the DG1 snapshot of the scratch prototype, verbatim but for the edits
# scripts/styles_tests/port_collision.py lists (imports, the JET and RIVER plates, a bounded cache); test_goldens_collision.py replays the edits on the scratch and the pixels of the
# scratch's own pictures.

import math

import numpy as np

from .. import core as C
from . import raster as RS

NB = 1440                                   # angular bins round an iris
SIZE_HIST = [(0.15, 0.6, 0.43), (0.6, 1.0, 0.24), (1.0, 1.3, 0.11), (1.3, 1.9, 0.12), (1.9, 2.9, 0.08)]   # % of R (the >= 2.9 % R
_HW = np.array([h[2] for h in SIZE_HIST])                                                                 # chunks are separate)
_HW = _HW / _HW.sum()


def partner_share(s_abs_R):
    """Brief R4: p(s) = 0.05 + 0.35 exp(-(s / 0.25)^2), s = lateral distance from the notch bisector in R."""
    return 0.05 + 0.35 * np.exp(-(np.asarray(s_abs_R) / 0.25) ** 2)


# density of the owner's H11 halo: chips per R^2 by distance e outside the union (R units) -> inverse CDF over e
_E_EDGES = np.array([0.0, 0.1, 0.2, 0.3, 0.45, 0.6, 0.8, 1.0])
_E_DENS = np.array([793.0, 1387.0, 833.0, 238.0, 25.0, 1.0, 0.3])
_E_W = _E_DENS * np.diff(_E_EDGES) * (1.0 + 0.5 * (_E_EDGES[:-1] + _E_EDGES[1:]))
_E_CDF = np.concatenate([[0.0], np.cumsum(_E_W) / _E_W.sum()])


def sample_e(rnd, n, tail=1.0):
    """e (R units) drawn from the measured H11 halo profile (piecewise constant density, linear CDF inside a bin). tail scales bins >= 0.45 R."""
    u = rnd.uniform(n)
    i = np.clip(np.searchsorted(_E_CDF, u, side="right") - 1, 0, len(_E_W) - 1)
    f = (u - _E_CDF[i]) / np.maximum(_E_CDF[i + 1] - _E_CDF[i], 1e-12)
    return _E_EDGES[i] + f * (_E_EDGES[i + 1] - _E_EDGES[i])


def angdiff(a, b):
    return (a - b + math.pi) % (2 * math.pi) - math.pi


class Geo:
    """Union-of-discs geometry on the exact (snapped) scene."""

    def __init__(self, sc):
        self.sc = sc
        self.c = np.array(sc.centres, np.float64)
        self.R = np.array(sc.R, np.float64)
        self.Rm = float(self.R.mean())
        self.n = len(self.R)
        th = (np.arange(NB) + 0.5) * (2 * math.pi / NB)
        self.th = th
        self.cs = np.stack([np.cos(th), np.sin(th)], 1)
        self.exposed = []
        for k in range(self.n):
            p = self.c[k][None, :] + 1.0005 * self.R[k] * self.cs
            ok = np.ones(NB, bool)
            for j in range(self.n):
                if j != k:
                    ok &= np.hypot(p[:, 0] - self.c[j][0], p[:, 1] - self.c[j][1]) > self.R[j] * 1.001
            self.exposed.append(ok)
        self.arc_R = [float(e.sum()) / NB * 2 * math.pi for e in self.exposed]
        self.notch_arc = []                                  # arc distance (R) of every bin to the nearest OUTER notch of its iris
        for k in range(self.n):
            d = np.full(NB, 9.0)
            for nc in sc.notches:
                if nc.kind == "outer" and k in (nc.i, nc.j):
                    a = math.atan2(nc.y - self.c[k][1], nc.x - self.c[k][0]) % (2 * math.pi)
                    d = np.minimum(d, np.abs(angdiff(th, a)))
            self.notch_arc.append(d)
        cen = self.c.mean(0)
        self.centroid = (float(cen[0]), float(cen[1]))

    def e_field(self, x, y):
        """Distance outside the union (R units of the nearest disc, negative inside) and the index of that disc."""
        best, kk = None, None
        for k in range(self.n):
            e = (np.hypot(x - self.c[k][0], y - self.c[k][1]) - self.R[k]) / self.R[k]
            if best is None:
                best, kk = e, np.zeros(e.shape, np.int8)
            else:
                m = e < best
                best = np.where(m, e, best)
                kk = np.where(m, np.int8(k), kk)
        return best, kk

    def inside_any(self, x, y, margin=0.985):
        m = np.zeros(np.shape(x), bool)
        for k in range(self.n):
            m |= np.hypot(x - self.c[k][0], y - self.c[k][1]) < self.R[k] * margin
        return m


class Particles:
    FIELDS = ("x", "y", "d", "k", "phi", "e", "cls", "u", "v", "w", "gain", "o", "src", "nid")

    def __init__(self):
        self.a = {f: [] for f in self.FIELDS}

    def add(self, **kw):
        n = len(kw["x"])
        for f in self.FIELDS:
            v = kw.get(f)
            if v is None:
                v = 1.0 if f == "gain" else (kw["k"] if f == "o" else (-1.0 if f == "nid" else 0.0))
            self.a[f].append(np.asarray(v, np.float64) * np.ones(n))

    def cat(self):
        return {f: (np.concatenate(v) if v else np.zeros(0)) for f, v in self.a.items()}


# size classes of round 2c (AD review: chips were 2.3-2.8 x too large), diameters in % of R of the iris the matter belongs to
DUST_PCT = (0.30, 0.80)           # sub-pixel to 1.5 px at R = 184
GRAIN_PCT = (0.60, 1.40)
CHUNK_PCT = (1.40, 3.20)          # x (1 + 0.5 e/R)
BIG_PCT = (3.20, 6.50)            # x (1 + 0.5 e/R), at most 12 per eye, never beyond e = 0.65 R
BIG_MAX_E = 0.65
CLS_DUST, CLS_GRAIN, CLS_CHUNK, CLS_BLOB, CLS_FG, CLS_BIG = 0, 1, 2, 3, 4, 5
DEPTH_E0, DEPTH_E1 = 0.15, 0.55           # depth dimming range (AD: 0.25-0.60, measured against the owner's H11 profile)


def _logu(rnd, n, lo, hi):
    return np.exp(np.log(lo) + rnd.uniform(n) * (np.log(hi) - np.log(lo)))


def sample_e2(rnd, n, L1, L2, share2=0.15, e0=0.012):
    """Emission distance e (R units): e0 + exponential, 85 % dense zone L1 and 15 % tail L2 (brief 3.0.2 with the AD's tighter L1 0.11 R, L2 0.25 R)."""
    u = np.maximum(rnd.uniform(n), 1e-9)
    tail = rnd.uniform(n) < share2
    return e0 - np.log(u) * np.where(tail, L2, L1)


def size_pct(rnd, n, e, big_mul=0.5):
    """Diameters (% of R) of the fine classes: 40 % dust-size, 60 % grain (round 2c sizes)."""
    dust = rnd.uniform(n) < 0.40
    d = np.where(dust, _logu(rnd, n, *DUST_PCT), _logu(rnd, n, *GRAIN_PCT))
    return d


def _angdens(geo, k, rnd, prm, theta_w, jets=True):
    """Angular density of iris k over its NB bins: exposure x wind x lobes (+ jets carrying 20 %), normalised, and the reach factor."""
    th = geo.th
    wind = 1.0 + prm["b"] * np.cos(th - theta_w)
    lobes = np.clip(1.0 + prm.get("lobe_amp", 0.25) * (2.0 * C.periodic_fbm1d(NB, rnd, octaves=2, base=4, gain=0.5) - 1.0), 0.5, 1.6)           # brief 3.0.3: 3-5 lobes of +-25 %
    f = geo.exposed[k] * wind * lobes
    reach = np.ones(NB)
    if jets:
        ex = np.nonzero(geo.exposed[k])[0]
        nj = 6 + int(rnd.uniform() * 3)
        if len(ex) > 20:
            jf = np.zeros(NB)
            for c0 in th[ex[rnd.integers(nj, 0, len(ex))]]:
                g = np.exp(-0.5 * (np.abs(angdiff(th, c0)) / math.radians(5.0)) ** 2) * geo.exposed[k]
                jf += g
                reach = np.maximum(reach, 1.0 + 0.35 * g)
            f = 0.8 * f / f.sum() + 0.2 * jf / max(jf.sum(), 1e-9)
    return f / f.sum(), reach


def _sample_theta(f, rnd, n):
    cdf = np.cumsum(f)
    cdf /= cdf[-1]
    ui = np.minimum(np.searchsorted(cdf, rnd.uniform(n)), NB - 1)
    return ui, (ui + rnd.uniform(n)) * (2 * math.pi / NB)


def _reach_var(rnd, ui, prm):
    return 1.0 + prm.get("reach_var", 0.12) * (2.0 * C.periodic_fbm1d(NB, rnd, octaves=2, base=5, gain=0.5)[ui] - 1.0)


def halo(geo, rnd, prm, theta_w):
    """Fine matter along the exposed outline of every iris (round 2c): DUST (sub-pixel to 1.5 px specks, dense at the rim: the glitter band of
    the owner's H11) and GRAINS (polygons of 0.6-1.4 % R), both with emission e = e0 + exp(L1 0.11 R) / exp(L2 0.25 R) mixture.
    prm: dust_lam, grain_lam (per R of exposed arc), L1, L2, b, cut, reach_var, dense_mul."""
    P = Particles()
    cut = prm.get("cut", 0.95)
    L1, L2 = prm.get("L1", 0.11), prm.get("L2", 0.25)
    for k in range(geo.n):
        if geo.arc_R[k] <= 0.05:
            continue
        f, jet_reach = _angdens(geo, k, rnd, prm, theta_w[k])
        arc = geo.arc_R[k] * prm.get("dense_mul", 1.0)
        # ---- dust: the glitter band
        nd = int(round(prm.get("dust_lam", 1300) * arc))
        if nd > 0:
            ui, th = _sample_theta(f, rnd, nd)
            reach = _reach_var(rnd, ui, prm) * jet_reach[ui]
            e = sample_e2(rnd, nd, L1 * 0.85, L2 * 0.8, 0.12) * reach
            keep = (rnd.uniform(nd) < (0.50 + 0.50 * C.smoothstep((e - 0.012) / 0.05))) & (e < cut)
            th, e = th[keep], e[keep]
            m = len(th)
            rr = geo.R[k] * (1.0 + e)
            dpc = _logu(rnd, m, *DUST_PCT)
            P.add(x=geo.c[k][0] + rr * np.cos(th), y=geo.c[k][1] + rr * np.sin(th), d=dpc / 100.0 * geo.R[k], k=np.full(m, k), phi=th, e=e,
                  cls=np.full(m, CLS_DUST), u=rnd.uniform(m), v=rnd.uniform(m), w=rnd.uniform(m), gain=np.full(m, 0.50))
        # ---- grains: little polygons
        ng = int(round(prm.get("grain_lam", 420) * arc))
        if ng > 0:
            ui, th = _sample_theta(f, rnd, ng)
            reach = _reach_var(rnd, ui, prm) * jet_reach[ui]
            e = sample_e2(rnd, ng, L1, L2, 0.15) * reach
            keep = (rnd.uniform(ng) < (0.45 + 0.55 * C.smoothstep((e - 0.015) / 0.07))) & (e < cut)
            th, e = th[keep], e[keep]
            m = len(th)
            tang = rnd.normal(m, 0.0, 0.020 + 0.07 * e)
            rr = geo.R[k] * (1.0 + e)
            x = geo.c[k][0] + rr * np.cos(th) - tang * geo.R[k] * np.sin(th)
            y = geo.c[k][1] + rr * np.sin(th) + tang * geo.R[k] * np.cos(th)
            dpc = _logu(rnd, m, *GRAIN_PCT) * (1.0 + 0.3 * np.clip(e, 0, 1.0))
            P.add(x=x, y=y, d=dpc / 100.0 * geo.R[k], k=np.full(m, k), phi=th, e=e, cls=np.full(m, CLS_GRAIN), u=rnd.uniform(m), v=rnd.uniform(m), w=rnd.uniform(m))
    return P


def _arc_points(geo, nc, iris_sel, s):
    """Points on the exposed arc of the iris in iris_sel (array of iris indices per particle), s = arc offset (R) from the notch."""
    n = len(s)
    x = np.zeros(n)
    y = np.zeros(n)
    nx = np.zeros(n)
    ny = np.zeros(n)
    for kk in (nc.i, nc.j):
        sel = iris_sel == kk
        if not sel.any():
            continue
        a0 = math.atan2(nc.y - geo.c[kk][1], nc.x - geo.c[kk][0])
        sg = 1.0
        for cand in (0.06, -0.06):
            p = geo.c[kk] + geo.R[kk] * np.array([math.cos(a0 + cand), math.sin(a0 + cand)])
            if all(math.hypot(p[0] - geo.c[j][0], p[1] - geo.c[j][1]) > geo.R[j] for j in range(geo.n) if j != kk):
                sg = 1.0 if cand > 0 else -1.0
                break
        ang = a0 + sg * s[sel]
        x[sel] = geo.c[kk][0] + geo.R[kk] * np.cos(ang)
        y[sel] = geo.c[kk][1] + geo.R[kk] * np.sin(ang)
        nx[sel] = np.cos(ang)
        ny[sel] = np.sin(ang)
    return x, y, nx, ny


def _plate_cloud_points(geo, nc, sp, rnd, n, prm, plate, bis, mirror):
    """Positions of n particles drawn from the LUMINANCE of a P-CX-JET plate registered on the notch (source point on the notch, axis on the
    bisector, scaled so the weighted 63 % distance equals r_d): the powder sprays where a photographed jet of powder really sprays, but as
    sharp iris-coloured chips instead of grey smoke. Returns (x, y, lat_R, dist_R) or None."""
    from . import jetplates as PL
    W, H = geo.sc.W, geo.sc.H
    R = float(geo.R[nc.i])
    r_d, r_m = sp["r_d"], sp["r_m"]
    pc = math.radians(sp["phi_c"])
    reach = r_d * R
    out = None
    for it in range(2):
        win = PL.place_jet(plate, nc.x, nc.y, bis, reach, W, H, mirror=mirror, window_R=r_m * 1.15 + 0.15, R_px=R, step=2, fade=0.16)
        if win is None:
            return None
        lum, x0, y0, _ = win
        h, w = lum.shape
        gx = ((np.arange(w, dtype=np.float32) + 0.5) * 2.0 + (x0 - nc.x))[None, :]
        gy = ((np.arange(h, dtype=np.float32) + 0.5) * 2.0 + (y0 - nc.y))[:, None]
        dist = np.sqrt(gx * gx + gy * gy) / R
        da = np.abs(((np.arctan2(gy, gx) - bis + math.pi) % (2 * math.pi)) - math.pi)
        cone = np.clip(_ssf(pc * 1.45, pc * 0.90, da), 0, 1)
        radial = _ssf(r_m * 1.05, r_m * 0.60, dist) * _ssf(0.03, 0.22, dist)
        wgt = np.maximum(lum - prm.get("plate_floor", 0.10), 0.0) ** 1.3 * cone * radial
        tot = float(wgt.sum())
        if tot <= 1e-6:
            return None
        flat = wgt.ravel()
        o = np.argsort(dist.ravel())
        cum = np.cumsum(flat[o])
        q63 = float(dist.ravel()[o][min(np.searchsorted(cum, 0.632 * cum[-1]), len(o) - 1)])
        if abs(q63 - r_d) <= 0.08 * r_d or it == 1:
            out = (wgt, x0, y0, gx, gy, dist)
            break
        reach *= r_d / max(q63, 1e-3)
    wgt, x0, y0, gx, gy, dist = out
    flat = wgt.ravel()
    cdf = np.cumsum(flat)
    cdf /= cdf[-1]
    idx = np.minimum(np.searchsorted(cdf, rnd.uniform(n)), len(flat) - 1)
    iy, ix = np.divmod(idx, wgt.shape[1])
    px = x0 + (ix + rnd.uniform(n)) * 2.0
    py = y0 + (iy + rnd.uniform(n)) * 2.0
    lat = ((px - nc.x) * (-nc.dy) + (py - nc.y) * nc.dx) / R
    return px, py, lat, np.hypot(px - nc.x, py - nc.y) / R


def _ssf(x0, x1, x):
    t = np.clip((np.asarray(x, np.float64) - x0) / (x1 - x0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def jets(geo, rnd, prm, kind="grain"):
    """Notch jets at every outer notch. prm['jet'](notch, geo) -> dict(Bg, Bc, phi_c, r_d, r_m) or None. kind 'grain' emits Bg fine particles
    (dust and grains, round 2c sizes), 'chunk' emits Bc chunks. Round 2c: positions are drawn from the luminance of a photographed P-CX-JET plate
    registered on the notch (plate-guided spray, prm['plate_jets'], default on) - the plate only decides WHERE; the matter is sharp chips in
    the origin irises' colours - with the parametric fan (direction = wedge bisector mixed 60/40 with the origin arc's normal, cone half angle
    phi_c, Weibull distance r_d / r_m, 1 % tail to 1 R) as the fallback. Colour by origin side with the partner share p(s)."""
    from . import jetplates as PL
    P = Particles()
    notches = [(ni, nc) for ni, nc in enumerate(geo.sc.notches) if nc.kind == "outer" and nc.weight > 0]
    use_plates = prm.get("plate_jets", True) and prm.get("jet") is not None
    plates = PL.pick("JET", rnd, len(notches)) if (use_plates and notches) else []
    for j, (ni, nc) in enumerate(notches):
        sp = prm["jet"](nc, geo)
        if sp is None:
            continue
        n = int((sp["Bg"] if kind == "grain" else sp["Bc"]) * (1.0 if sp.get("absolute") else nc.weight) * prm.get("jet_scale", 1.0))
        if n <= 0:
            continue
        phi_c, r_d, r_m = math.radians(sp["phi_c"]), sp["r_d"], sp["r_m"]
        beta = math.atan2(nc.dy, nc.dx)
        got = None
        if plates:
            mirror = rnd.uniform() < 0.5
            got = _plate_cloud_points(geo, nc, sp, rnd, n, prm, plates[j % len(plates)], beta, mirror)
        if got is not None:
            px, py, lat, dist = got
            ci = geo.c[nc.i]
            si = np.sign((ci[0] - nc.x) * (-math.sin(beta)) + (ci[1] - nc.y) * math.cos(beta))
            si = si if si != 0 else 1.0
            sidew = _ssf(-0.12, 0.12, lat * si)                          # 1 on the side of iris i
            iris = np.where(rnd.uniform(n) < sidew, nc.i, nc.j)
        else:
            iris = np.where(rnd.uniform(n) < 0.5, nc.i, nc.j)
            s = np.minimum(np.abs(rnd.normal(n, 0.0, 0.17)), 0.35)
            x, y, nxv, nyv = _arc_points(geo, nc, iris, s)
            dirx, diry = 0.6 * nc.dx + 0.4 * nxv, 0.6 * nc.dy + 0.4 * nyv
            base = np.arctan2(diry, dirx)
            ang_dir = base + phi_c * np.clip(rnd.normal(n, 0.0, 0.42), -1.0, 1.0)
            rays = beta + phi_c * rnd.uniform(5, -0.8, 0.8)
            pick = rnd.uniform(n) < 0.22
            ang_dir = np.where(pick, rays[rnd.integers(n, 0, 5)] + rnd.normal(n, 0.0, math.radians(1.8)), ang_dir)
            u = np.maximum(rnd.uniform(n), 1e-6)
            dist = np.minimum(r_d * (-np.log(u)) ** (1.0 / 1.35), r_m)
            dist = np.where(rnd.uniform(n) < 0.012, rnd.uniform(n, r_m, 1.0), dist)
            px = x + np.cos(ang_dir) * dist * geo.R[nc.i]
            py = y + np.sin(ang_dir) * dist * geo.R[nc.i]
            lat = ((px - nc.x) * (-nc.dy) + (py - nc.y) * nc.dx) / geo.R[nc.i]
        if kind != "grain":
            keepc = dist <= BIG_MAX_E + 0.1
            px, py, dist, lat, iris = px[keepc], py[keepc], dist[keepc], lat[keepc], iris[keepc]
            n = len(px)
            if n == 0:
                continue
        swap = rnd.uniform(n) < partner_share(np.abs(lat))
        k_col = np.where(swap, np.where(iris == nc.i, nc.j, nc.i), iris).astype(int)
        phi = np.arctan2(py - geo.c[k_col][:, 1], px - geo.c[k_col][:, 0])
        if kind == "grain":
            isd = rnd.uniform(n) < prm.get("jet_dust", 0.55)
            dpc = np.where(isd, _logu(rnd, n, *DUST_PCT), _logu(rnd, n, *GRAIN_PCT) * (1.0 + 0.3 * dist))
            cls = np.where(isd, CLS_DUST, CLS_GRAIN)
            gain = np.where(isd, 0.50, 1.0)
        else:
            dpc = _logu(rnd, n, *CHUNK_PCT) * (1.0 + 0.5 * dist)
            cls = np.full(n, CLS_CHUNK)
            gain = np.ones(n)
        P.add(x=px, y=py, d=dpc / 100.0 * geo.Rm, k=k_col, o=iris, src=(1 if kind == "grain" else 2), nid=ni, phi=phi, e=dist, cls=cls, u=rnd.uniform(n), v=rnd.uniform(n),
              w=rnd.uniform(n), gain=gain)
    return P


def river_particles(geo, rnd, prm, strong_pos=True, kind="grain"):
    """Kiss Collision S band (brief 3.2 layer 3, round 2c): the matter of the river of powder through the contact, positions drawn from the LUMINANCE of a
    photographed P-CX-RIVER plate (axis on the perpendicular of the pair, centre width river_w R, asymmetric 60 / 40 with the +v end strong),
    colour by the nearer iris with the partner share; sharp chips, not smoke. kind 'grain' (dust + grains) or 'chunk'."""
    from . import jetplates as PL
    P = Particles()
    W, H = geo.sc.W, geo.sc.H
    for ri, r in enumerate(geo.sc.rules):
        ci, cj = geo.c[r.a], geo.c[r.b]
        mid = (ci + cj) / 2
        R = float(geo.R[r.a])
        n = int(prm.get("river_n", 1500) if kind == "grain" else prm.get("river_nc", 16))
        if n <= 0:
            continue
        pl = PL.pick("RIVER", rnd, 1)
        if not pl:
            continue
        p = pl[0]
        axis = math.atan2(-r.ux, r.uy)
        win = PL.place_river(p, mid[0], mid[1], axis, prm.get("river_w", 0.75) * R, W, H, mirror=rnd.uniform() < 0.5, window_R=prm.get("river_win", 1.8), R_px=R, step=2)
        if win is None:
            continue
        lum, x0, y0, _ = win
        h, w = lum.shape
        gx = ((np.arange(w, dtype=np.float32) + 0.5) * 2.0 + x0)[None, :]
        gy = ((np.arange(h, dtype=np.float32) + 0.5) * 2.0 + y0)[:, None]
        dist = np.hypot(gx - mid[0], gy - mid[1]) / R
        rr = prm.get("river_reach", 1.25)
        radial = _ssf(rr, rr * 0.55, dist)
        vx, vy = r.uy, -r.ux
        side = ((gx - mid[0]) * vx + (gy - mid[1]) * vy) / R
        asym = np.where(side > 0, 1.0 if strong_pos else 0.62, 0.62 if strong_pos else 1.0)
        wgt = np.maximum(lum - prm.get("plate_floor", 0.10), 0.0) ** 1.3 * radial * asym
        # matter never lies on the lens / inside a disc: drop the weight inside every iris
        for k in range(geo.n):
            wgt = wgt * (np.hypot(gx - geo.c[k][0], gy - geo.c[k][1]) > geo.R[k] * 0.99)
        tot = float(wgt.sum())
        if tot <= 1e-6:
            continue
        cdf = np.cumsum(wgt.ravel())
        cdf /= cdf[-1]
        idx = np.minimum(np.searchsorted(cdf, rnd.uniform(n)), wgt.size - 1)
        iy, ix = np.divmod(idx, wgt.shape[1])
        px = x0 + (ix + rnd.uniform(n)) * 2.0
        py = y0 + (iy + rnd.uniform(n)) * 2.0
        di = np.hypot(px - ci[0], py - ci[1]) / geo.R[r.a]
        dj = np.hypot(px - cj[0], py - cj[1]) / geo.R[r.b]
        sw = _ssf(-0.30, 0.30, dj - di)                              # probability of iris a's colour
        origin = np.where(rnd.uniform(n) < sw, r.a, r.b)
        lat = np.abs(((px - mid[0]) * (-r.ux) + (py - mid[1]) * (-r.uy)) / R) * 0 + np.abs((px - mid[0]) * vx + (py - mid[1]) * vy) / R
        swap = rnd.uniform(n) < partner_share(np.maximum(lat - 0.3, 0.0) * 0 + np.abs(dj - di) * 0.5)
        k_col = np.where(swap, np.where(origin == r.a, r.b, r.a), origin).astype(int)
        e_out, _ = geo.e_field(px, py)
        e_out = np.clip(e_out, 0.0, 1.5)
        phi = np.arctan2(py - geo.c[k_col][:, 1], px - geo.c[k_col][:, 0])
        if kind == "grain":
            isd = rnd.uniform(n) < prm.get("jet_dust", 0.55)
            dpc = np.where(isd, _logu(rnd, n, *DUST_PCT), _logu(rnd, n, *GRAIN_PCT) * (1.0 + 0.3 * e_out))
            cls = np.where(isd, CLS_DUST, CLS_GRAIN)
            gain = np.where(isd, 0.50, 1.0)
        else:
            keepc = e_out <= BIG_MAX_E + 0.1
            px, py, e_out, k_col, origin, phi = px[keepc], py[keepc], e_out[keepc], k_col[keepc], origin[keepc], phi[keepc]
            n = len(px)
            if n == 0:
                continue
            dpc = _logu(rnd, n, *CHUNK_PCT) * (1.0 + 0.5 * e_out)
            cls = np.full(n, CLS_CHUNK)
            gain = np.ones(n)
        P.add(x=px, y=py, d=dpc / 100.0 * geo.Rm, k=k_col, o=origin, src=(6 if kind == "grain" else 7), nid=-1, phi=phi, e=e_out, cls=cls, u=rnd.uniform(n), v=rnd.uniform(n),
              w=rnd.uniform(n), gain=gain)
    return P


def outline_chunks(geo, rnd, prm, theta_w):
    """Chunks (1.4-3.2 % R x (1 + 0.5 e)) on the halo plus at most prm['big'] BIG chips (3.2-6.5 %) per eye (iris-chips and atlas sprites
    with real fibres), sparser and bigger outward; nothing beyond e 0.65 R."""
    P = Particles()
    for k in range(geo.n):
        if geo.arc_R[k] < 0.05:
            continue
        share = geo.arc_R[k] / (2 * math.pi) / 0.72
        n = int(round(prm.get("chunk_lam", 70) * geo.arc_R[k]))
        f, _ = _angdens(geo, k, rnd, prm, theta_w[k], jets=False)
        if n > 0:
            ui, theta = _sample_theta(f, rnd, n)
            e = np.minimum(0.03 + rnd.exponential(n, prm.get('chunk_L', 0.10)), BIG_MAX_E)
            rr = geo.R[k] * (1.0 + e)
            dpc = _logu(rnd, n, *CHUNK_PCT) * (1.0 + 0.5 * e)
            P.add(x=geo.c[k][0] + rr * np.cos(theta), y=geo.c[k][1] + rr * np.sin(theta), d=dpc / 100.0 * geo.R[k], k=np.full(n, k), src=3, phi=theta, e=e,
                  cls=np.full(n, CLS_CHUNK), u=rnd.uniform(n), v=rnd.uniform(n), w=rnd.uniform(n))
        nb = int(round(min(prm.get("big", 10), 12) * min(share, 1.0)))
        if nb > 0:
            ui, theta = _sample_theta(f, rnd, nb)
            e = np.minimum(0.06 + rnd.exponential(nb, 0.20), BIG_MAX_E)
            rr = geo.R[k] * (1.0 + e)
            dpc = _logu(rnd, nb, *BIG_PCT) * (1.0 + 0.5 * e)
            P.add(x=geo.c[k][0] + rr * np.cos(theta), y=geo.c[k][1] + rr * np.sin(theta), d=dpc / 100.0 * geo.R[k], k=np.full(nb, k), src=3, phi=theta, e=e,
                  cls=np.full(nb, CLS_BIG), u=rnd.uniform(nb), v=rnd.uniform(nb), w=rnd.uniform(nb))
    return P


def blobs(geo, rnd, prm, theta_w):
    """Defocused chips: prm['blobs_pair'] in total for a pair (AD: 3 per pair, alpha 0.25, e >= 0.40 R so they never read as dust on the lens)
    or blobs_total for groups; 4-6 % R, blur 0.02 R."""
    P = Particles()
    tot = prm.get("blobs_total", prm.get("blobs_pair", 3))
    for k in range(geo.n):
        n = max(0, int(round(tot / geo.n)))
        if geo.arc_R[k] < 0.3:
            n = 0
        if n <= 0:
            continue
        f, _ = _angdens(geo, k, rnd, prm, theta_w[k], jets=False)
        ui, theta = _sample_theta(f, rnd, n)
        e = rnd.uniform(n, 0.40, 0.72)
        rr = geo.R[k] * (1.0 + e)
        P.add(x=geo.c[k][0] + rr * np.cos(theta), y=geo.c[k][1] + rr * np.sin(theta), d=rnd.uniform(n, 4.0, 6.0) / 100.0 * geo.R[k],
              k=np.full(n, k), src=4, phi=theta, e=e, cls=np.full(n, CLS_BLOB), u=rnd.uniform(n), v=rnd.uniform(n), w=rnd.uniform(n))
    return P


# ----------------------------------------------------------------------------- rasterising particles with palettes
def _colours(pals, d):
    n = len(d["x"])
    rgb = np.zeros((n, 3), np.float32)
    k = d["k"].astype(int)
    for kk in range(len(pals)):
        sel = k == kk
        if sel.any():
            rgb[sel] = pals[kk].chips2(d["phi"][sel], d["u"][sel], d["v"][sel], d["w"][sel])
    return rgb


def _depth(e):
    """Depth dimming of far matter (AD A4): x (1 - 0.6 smoothstep(0.25, 0.6, e / R)) so far chips are dim."""
    t = np.clip((np.asarray(e) - DEPTH_E0) / (DEPTH_E1 - DEPTH_E0), 0.0, 1.0)
    return 1.0 - 0.6 * t * t * (3 - 2 * t)


def rasterise(cv, geo, pals, discs, d, rnd, atlas, prm, wind_streaks=True, mask_fn=None, seed=1):
    """Draw a merged particle dict d into the float canvas cv (H, W, 3). Classes: 0 dust, 1 grain, 2 chunk (polygons), 3 blob, 4 foreground,
    5 big chip (atlas silhouette filled with the iris's own band). Every random attribute of a particle comes from its own row of a table drawn
    BEFORE any culling, so the same particle looks the same at 1024 and 4096 however the culling at the iris rims and the canvas edge falls.
    Round 2c: every chip is a flat, opaque colour lit by its own luminance factor 0.30-1.0 (H11 has dim dust as well as bright chips), dimmed
    with distance (depth), 15 % carry a lit facet edge, no texture inside, and the big chips are filled with the real band pixels."""
    H, W = cv.shape[:2]
    n0 = len(d["x"])
    if n0 == 0:
        return {}
    RT = C.Rand(seed, "raster-table").uniform((n0, 30)).astype(np.float64)
    d["rt"] = RT
    ins = geo.inside_any(d["x"], d["y"], 0.985)
    ok = (~ins) & (d["x"] > -30) & (d["x"] < W + 30) & (d["y"] > -30) & (d["y"] < H + 30)
    for key in d:
        d[key] = d[key][ok]
    if mask_fn is not None:
        f = mask_fn(d["x"], d["y"])
        d["gain"] = d["gain"] * f
        keepm = f > 0.02
        for key in d:
            d[key] = d[key][keepm]
    n = len(d["x"])
    RT = d["rt"]
    rgb = _colours(pals, d)
    cls = d["cls"].astype(int)
    px = d["d"]
    gf = d["gain"]
    stats = {}
    Rm = geo.Rm                      # every size threshold is relative to R, never to pixels: 4096 == 1024
    depth = _depth(d["e"]).astype(np.float32)
    lf = (0.22 + 0.78 * RT[:, 19] ** 2.0).astype(np.float32)          # per-chip luminance factor 0.22-1.0 (dim brown dust to bright chips)
    lf = np.where(RT[:, 21] < 0.08, lf * 1.35, lf).astype(np.float32)                   # about 8 % of the chips catch the light (the colours stay below the tone-map knee)
    lf = np.where(cls == CLS_DUST, 0.45 + 0.55 * RT[:, 19] ** 1.3, lf).astype(np.float32)
    dof = (cls == 1) & (RT[:, 0] < 0.03)                      # micro-depth: 3 % of the grains are defocused
    small = ((cls == 0) | ((cls == 1) & (px < 0.0074 * Rm))) & ~dof
    ii = np.nonzero(small)[0]
    # amplitude of a Gaussian stamp is capped below the tone-map knee (0.8): the soft shoulder is non-linear, and a speck's peak grows with the
    # resolution (same energy, fewer pixels); below the knee the 4096 master is exactly the box-reduced 1024 picture
    bd = prm.get("gain_dust", 1.0)
    RS.gauss_stamps(cv, d["x"][ii], d["y"][ii], np.maximum(px[ii], 0.0016 * Rm) * 0.34, rgb[ii], np.minimum(lf[ii] * depth[ii] * gf[ii] * 1.25 * bd, 0.80))
    gg = np.nonzero(((cls == 1) & (px >= 0.0074 * Rm) & ~dof) | (cls == 2))[0]
    if len(gg):
        nv = 5 + np.minimum((RT[gg, 3] * 4).astype(np.int64), 3)                     # 5..8 vertices
        asp = 1.0 + 1.2 * RT[gg, 2] ** 1.5                                           # aspect 1 .. 2.2
        rot = RT[gg, 1] * 2 * math.pi
        facet = RT[gg, 18] < 0.15
        RS.chip_polys(cv, d["x"][gg], d["y"][gg], np.maximum(px[gg], 0.0074 * Rm), rot, asp, nv, rgb[gg] * (lf[gg] * depth[gg])[:, None],
                      gf[gg] * prm.get("gain_grain", 1.0), RT[gg], facet)
    di = np.nonzero(dof)[0]
    if len(di):
        RS.gauss_stamps(cv, d["x"][di], d["y"][di], np.maximum(px[di] * 0.55, 0.0042 * Rm), rgb[di], np.minimum(0.30 * gf[di] * depth[di] * prm.get("gain_grain", 1.0), 0.8))
    cc = np.nonzero(cls == CLS_BIG)[0]
    if len(cc) and atlas is not None:
        rotc = RT[cc, 5] * 2 * math.pi
        sidx = np.minimum((RT[cc, 6] * atlas.n).astype(np.int64), atlas.n - 1)
        flipc = RT[cc, 7] < 0.5
        kk = d["k"][cc].astype(int)
        sx = np.zeros(len(cc))
        sy = np.zeros(len(cc))
        for i, c in enumerate(cc):
            dsc = discs[kk[i]]
            rho = 0.72 + 0.22 * RT[c, 13]
            phi = d["phi"][c] + 0.25 * (RT[c, 14] - 0.5)
            sx[i] = dsc.cx + rho * dsc.R * math.cos(phi)
            sy[i] = dsc.cy + rho * dsc.R * math.sin(phi)

        def patch_fn(i, w, h, rot):
            dsc = discs[kk[i]]
            g = dsc.g
            cx0 = int(round(sx[i] - dsc.x0))
            cy0 = int(round(sy[i] - dsc.y0))
            x0, y0 = cx0 - w // 2, cy0 - h // 2
            xa, ya = max(0, x0), max(0, y0)
            xb, yb = min(g.shape[1], x0 + w), min(g.shape[0], y0 + h)
            out = np.zeros((h, w, 3), np.float32)
            if xa < xb and ya < yb:
                out[ya - y0:yb - y0, xa - x0:xb - x0] = g[ya:yb, xa:xb].astype(np.float32) / 255.0
            out = np.clip(out * 1.30 + 0.04, 0, 1.3)
            return out
        irism = RT[cc, 8] < 0.6                        # brief 1.7.6: 60 % iris-chips (real fibres), 40 % flake-sheet sprites
        asp = 0.42 + 0.53 * RT[cc, 9]
        gauss = np.sqrt(-2.0 * np.log(np.maximum(1.0 - RT[cc, 10], 1e-9))) * np.cos(2 * math.pi * RT[cc, 11])
        rotc = np.where(irism, d["phi"][cc] + 0.5 * gauss, rotc)        # iris chips fly along the emission direction
        RS.chunk_stamps(cv, atlas, d["x"][cc], d["y"][cc], np.maximum(px[cc], 0.028 * Rm), rotc, sidx, patch_fn, rgb[cc],
                        (0.55 + 0.45 * lf[cc]) * depth[cc] * gf[cc] * prm.get("gain_chunk", 1.0), 0.0, flipc, irism, asp,
                        (RT[cc, 12] * 1e9).astype(np.int64))
    fgi = np.nonzero(cls == CLS_FG)[0]
    if len(fgi) and atlas is not None:
        RS.chunk_stamps(cv, atlas, d["x"][fgi], d["y"][fgi], np.maximum(px[fgi], 0.023 * Rm), RT[fgi, 17] * 6.283,
                        np.minimum((RT[fgi, 18] * atlas.n).astype(np.int64), atlas.n - 1), None, rgb[fgi], 0.42 * gf[fgi], 0.04 * geo.Rm)
    bb = np.nonzero(cls == CLS_BLOB)[0]
    if len(bb):
        sg = np.maximum(px[bb] * 0.42, 0.0046 * Rm)
        RS.gauss_stamps(cv, d["x"][bb], d["y"][bb], sg, rgb[bb] * (0.7 + 0.5 * d["v"][bb])[:, None].astype(np.float32),
                        np.minimum(0.25 * gf[bb] * prm.get("gain_blob", 1.0), 0.8))
    if wind_streaks:
        st = np.nonzero(((cls == 1) | (cls == 0)) & (d["e"] > 0.45) & (px > 0.0065 * Rm) & (RT[:, 15] < 0.10))[0]
        if len(st):
            ang = np.arctan2(d["y"][st] - np.array([geo.c[int(k)][1] for k in d["k"][st]]), d["x"][st] - np.array([geo.c[int(k)][0] for k in d["k"][st]]))
            RS.streak_stamps(cv, d["x"][st], d["y"][st], (0.04 + 0.06 * RT[st, 16]) * geo.Rm, np.maximum(px[st] * 0.25, 0.6), ang, rgb[st],
                             0.30 * gf[st] * depth[st])
    stats["n"] = n
    stats["dust"] = int(small.sum())
    stats["grain"] = int(((cls == 1) & ~small).sum())
    stats["chunk"] = int((cls == CLS_CHUNK).sum())
    stats["big"] = int(len(cc))
    return stats


# ----------------------------------------------------------------------------- haze (fine dust cloud between the chips)
def _fbm(W, H, cells, rnd, octaves=3, gain=0.55):
    acc = np.zeros((H, W), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        acc += amp * C.value_noise2d(W, H, cells * 2 ** o, rnd)
        tot += amp
        amp *= gain
    return acc / tot


def haze(geo, pals, rnd, prm, theta_w, W, H, S, mask_fn=None):
    """Soft dust between the chips, computed on a coarse grid and upsampled once: density exp(-e / Lh) outside the union, masked to
    prm['haze_reach'] R (brief: nothing beyond about 0.75 R), angular modulation of the wind and lobes, cloud structure from domain-warped
    fbm, plus a dust cloud along every notch's cone. Colour: the nearest iris's haze palette, mixed toward the partner at notches.
    Returns the light layer (H, W, 3) float32 or None."""
    amp = prm.get("haze", 0.0)
    if amp <= 0:
        return None
    f = max(2, int(round(S / 256.0)))
    gw, gh = -(-W // f), -(-H // f)
    xs = ((np.arange(gw, dtype=np.float32) + 0.5) * f)[None, :]
    ys = ((np.arange(gh, dtype=np.float32) + 0.5) * f)[:, None]
    X = np.broadcast_to(xs, (gh, gw))
    Y = np.broadcast_to(ys, (gh, gw))
    e, kk = geo.e_field(X, Y)
    reach = prm.get("haze_reach", 0.75)
    Lh = prm.get("haze_L", 0.20)
    dens = np.exp(-np.maximum(e, 0.0) / Lh) * C.smoothstep(e / 0.06) * C.smoothstep((reach - e) / 0.35)
    # angular modulation per nearest iris
    th = np.arctan2(Y - geo.c[:, 1][kk], X - geo.c[:, 0][kk])
    bins = np.minimum(((th % (2 * math.pi)) * (NB / (2 * math.pi))).astype(np.int64), NB - 1)
    mod = np.ones((gh, gw), np.float32)
    for k in range(geo.n):
        fk, _ = _angdens(geo, k, rnd, prm, theta_w[k], jets=False)
        fk = np.where(geo.exposed[k], fk, 0.0)
        fk = fk / max(fk[geo.exposed[k]].mean(), 1e-9) if geo.exposed[k].any() else fk
        sel = kk == k
        mod[sel] = fk[bins[sel]]
    dens = dens * np.clip(mod, 0.0, 2.2)
    if mask_fn is not None:
        dens = dens * mask_fn(X, Y)
    # cloud structure: domain-warped fbm in R units (cells across the short side derived from the R fraction)
    cells = max(3, int(round(S / (0.42 * geo.Rm))))
    n1 = _fbm(gw, gh, cells, rnd, 3)
    n2 = _fbm(gw, gh, cells * 1.7, rnd, 2)
    cloud = C.smoothstep((0.55 * n1 + 0.45 * n2 - 0.32) / 0.42)
    dens = dens * (0.30 + 1.15 * cloud)
    # notch clouds: dust cone along the bisector
    col = np.zeros((gh, gw, 3), np.float32)
    share = np.zeros((gh, gw), np.float32)
    boost = np.zeros((gh, gw), np.float32)
    for nc in geo.sc.notches:
        if nc.kind != "outer" or nc.weight <= 0:
            continue
        sp = prm["jet"](nc, geo)
        if sp is None:
            continue
        R0 = geo.R[nc.i]
        ax = ((X - nc.x) * nc.dx + (Y - nc.y) * nc.dy) / R0
        lat = ((X - nc.x) * (-nc.dy) + (Y - nc.y) * nc.dx) / R0
        width = 0.16 + np.tan(math.radians(sp["phi_c"]) * 0.75) * np.maximum(ax, 0)
        b = np.exp(-0.5 * (lat / width) ** 2) * np.exp(-np.maximum(ax, 0) / (sp["r_d"] * 0.9)) * (ax > -0.15) * (0.5 + 0.7 * nc.weight)
        boost = np.maximum(boost, b.astype(np.float32))
        pair_cols = np.zeros((gh, gw, 3), np.float32)
        share = np.maximum(share, (b * 0.9).astype(np.float32))
    dens = dens + prm.get("notch_haze", 1.6) * boost * (0.5 + 0.9 * cloud) * (e > -0.02)
    # colour of the haze
    for k in range(geo.n):
        sel = kk == k
        if not sel.any():
            continue
        uu = np.full(int(sel.sum()), 0.5)
        col[sel] = pals[k].haze(th[sel], uu, uu)
    if geo.n >= 2:
        # mix toward the mean of the two colours where a notch cloud is strong
        mean_col = np.zeros((gh, gw, 3), np.float32)
        for k in range(geo.n):
            uu = np.full(gh * gw, 0.5)
            mean_col += pals[k].haze(np.arctan2(Y - geo.c[k][1], X - geo.c[k][0]).ravel(), uu, uu).reshape(gh, gw, 3)
        mean_col /= geo.n
        share = np.clip(share, 0, 0.6)[..., None]
        col = col * (1 - share) + mean_col * share
    dens = np.maximum(dens - prm.get("haze_floor", 0.05), 0.0)            # nothing below the floor: the black stays black
    light = (col * (dens * amp)[..., None]).astype(np.float32)
    up = np.empty((H, W, 3), np.float32)
    for c_ in range(3):
        up[..., c_] = C.upsample(np.ascontiguousarray(light[..., c_]), W, H, f)
    return up


# ----------------------------------------------------------------------------- plate layers (P-CX-JET notch jets, P-CX-RIVER kiss band)
def _ss(x0, x1, x):
    t = np.clip((x - x0) / (x1 - x0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _add_up(cv, val, x0, y0, f):
    """Add a contribution computed on an f px grid (h, w, 3) into cv at canvas (x0, y0): bicubic upsampling per channel, cropped to the canvas."""
    H, W = cv.shape[:2]
    h, w = val.shape[:2]
    if f == 1:
        cv[y0:y0 + h, x0:x0 + w] += val
        return
    wp, hp = min(w * f, W - x0), min(h * f, H - y0)
    for c_ in range(3):
        cv[y0:y0 + hp, x0:x0 + wp, c_] += C.upsample(np.ascontiguousarray(val[..., c_].astype(np.float32)), w * f, h * f, f)[:hp, :wp]


def _tintcol(pal, ang):
    """Colour a white plate is tinted with: the iris's CHIP palette at this angle (round 2c AD fix B: the plate takes the chips' own hues, not a
    muddy haze colour), lifted so the plate luminance carries the highlights."""
    c = pal.chips2(np.array([ang]), np.array([0.55]), np.array([0.65]), np.array([0.5]))[0]
    m = float(c.max())
    return (c / max(m, 1e-3) * 0.95).astype(np.float32)


_DITHER_TILES = C.BoundedCache(16)


def _dither_tile(seed, n=256):
    t = _DITHER_TILES.get((seed, n))
    if t is None:
        g = np.random.Generator(np.random.PCG64(seed & 0x7FFFFFFF))
        t = _DITHER_TILES.put((seed, n), g.random((n, n)).astype(np.float32))
    return t


def _dither_side(s, gx, gy, R, seed):
    """Hard per-pixel choice between the two origin colours with probability s (1 on iris i's side): the two hues meet in a fine speckle,
    never blend into a third hue (blue + yellow = mud green). The noise is a fixed tile looked up in R units (cells 0.035 R and 0.012 R)."""
    a = _dither_tile(seed)
    b = _dither_tile(seed + 77)
    n = a.shape[0]
    ia = (np.floor(gx / (0.035 * R)).astype(np.int64) % n, np.floor(gy / (0.035 * R)).astype(np.int64) % n)
    ib = (np.floor(gx / (0.012 * R)).astype(np.int64) % n, np.floor(gy / (0.012 * R)).astype(np.int64) % n)
    ia = np.broadcast_arrays(ia[1], ia[0])
    ib = np.broadcast_arrays(ib[1], ib[0])
    nv = 0.55 * a[ia[0], ia[1]] + 0.45 * b[ib[0], ib[1]]
    nv = np.clip((nv - 0.5) * 2.0 + 0.5, 0.0, 1.0)
    return (s > nv).astype(np.float32)


def plate_layers(cv, geo, pals, prm, rnd, W, H, kind="jets", strong_pos=True, mask_fn=None):
    """Add the photographed powder of the jet (or river) plates, tinted by the two origin irises, into cv (before the irises). Returns info."""
    from . import jetplates as PL
    info = dict(n=0, keys=[])
    fgrid = int(max(1, min(4, round(geo.Rm / 184.0))))        # the plates are soft: computed on a grid of fgrid px cells (1024 preview: 1) and upsampled
    if kind == "jets":
        notches = [nc for nc in geo.sc.notches if nc.kind == "outer" and nc.weight > 0]
        plates = PL.pick("JET", rnd, len(notches))
        if not plates:
            return info
        for nc, p in zip(notches, plates):
            sp = prm["jet"](nc, geo)
            if sp is None:
                continue
            R = geo.R[nc.i]
            bis = math.atan2(nc.dy, nc.dx)
            mirror = rnd.uniform() < 0.5
            reach_px = sp["r_d"] * R * prm.get("plate_reach", 1.0)
            win = PL.place_jet(p, nc.x, nc.y, bis, reach_px, W, H, mirror=mirror, window_R=sp["r_m"] * 1.35 + 0.25, R_px=R, step=fgrid, fade=0.16)
            if win is None:
                continue
            lum, x0, y0, (a, t) = win
            h, w = lum.shape
            gx = ((np.arange(w, dtype=np.float32) + 0.5) * fgrid + (x0 - nc.x))[None, :]
            gy = ((np.arange(h, dtype=np.float32) + 0.5) * fgrid + (y0 - nc.y))[:, None]
            lat = (gx * (-math.sin(bis)) + gy * math.cos(bis)) / R
            ax = (gx * math.cos(bis) + gy * math.sin(bis)) / R
            dist = np.sqrt(gx * gx + gy * gy) / R
            radial = _ss(sp["r_m"] * 1.10, sp["r_m"] * 0.62, dist)
            da = np.abs(((np.arctan2(gy, gx) - bis + math.pi) % (2 * math.pi)) - math.pi)
            pc = math.radians(sp["phi_c"])
            cone = _ss(pc * 1.55, pc * 0.95, da) + (dist < 0.18) * 1.0          # a fan, never the plate's own twin lobes
            radial = radial * np.clip(cone, 0, 1) * _ss(0.04, 0.34, dist)          # no hard bright neck at the notch: the chips carry that part
            # the plate is narrower than the cone asked for: keep its own shape, only cut by the reach
            # colours by origin side: sign of the lateral offset of each iris centre
            ci, cj = geo.c[nc.i], geo.c[nc.j]
            si = np.sign(((ci[0] - nc.x) * (-math.sin(bis)) + (ci[1] - nc.y) * math.cos(bis)))
            si = si if si != 0 else 1.0
            ai = math.atan2(nc.y - ci[1], nc.x - ci[0])
            aj = math.atan2(nc.y - cj[1], nc.x - cj[0])
            uu = np.full(1, 0.42)
            col_i = _tintcol(pals[nc.i], ai)
            col_j = _tintcol(pals[nc.j], aj)
            width = 0.22 + 0.25 * np.clip(ax, 0, 1.2)
            s = _ss(-width, width, lat * si)                     # probability of iris i's colour
            s = _dither_side(s, gx + nc.x, gy + nc.y, R, int(rnd.uniform() * 1e6))
            tint = col_i[None, None, :] * s[..., None] + col_j[None, None, :] * (1 - s[..., None])
            g = prm.get("plate_gain", 0.5) * (0.6 + 0.4 * nc.weight) * sp.get("plate_mul", 1.0)
            mk = mask_fn(gx + nc.x, gy + nc.y) if mask_fn is not None else 1.0
            val = (np.maximum(lum - prm.get("plate_floor", 0.12), 0.0) ** prm.get("plate_gamma", 1.25) * radial * g * mk)[..., None] * tint
            _add_up(cv, val, x0, y0, fgrid)
            info["n"] += 1
            info["keys"].append(p["key"])
    else:
        notch_pairs = {}
        for nc in geo.sc.notches:
            if nc.kind == "outer":
                notch_pairs.setdefault(nc.rule, []).append(nc)
        for ri, r in enumerate(geo.sc.rules):
            if ri not in notch_pairs:
                continue
            ci, cj = geo.c[r.a], geo.c[r.b]
            mid = (ci + cj) / 2
            R = geo.R[r.a]
            axis = math.atan2(r.ux, -r.uy)                        # direction of +v = (uy, -ux)
            axis = math.atan2(-r.ux, r.uy)
            p = PL.pick("RIVER", rnd, 1)
            if not p:
                continue
            p = p[0]
            width_px = prm.get("river_w", 0.75) * R
            mirror = rnd.uniform() < 0.5
            win = PL.place_river(p, mid[0], mid[1], axis, width_px, W, H, mirror=mirror, window_R=prm.get("river_win", 2.5), R_px=R, step=fgrid)
            if win is None:
                continue
            lum, x0, y0, (a, t) = win
            h, w = lum.shape
            gx = ((np.arange(w, dtype=np.float32) + 0.5) * fgrid + x0)[None, :]
            gy = ((np.arange(h, dtype=np.float32) + 0.5) * fgrid + y0)[:, None]
            di = np.hypot(gx - ci[0], gy - ci[1]) / geo.R[r.a]
            dj = np.hypot(gx - cj[0], gy - cj[1]) / geo.R[r.b]
            s = _ss(-0.30, 0.30, dj - di)                         # 1 nearer to A
            s = _dither_side(s, gx, gy, R, int(rnd.uniform() * 1e6))
            ua = np.full(1, 0.42)
            ang_a = math.atan2(mid[1] - ci[1], mid[0] - ci[0])
            ang_b = math.atan2(mid[1] - cj[1], mid[0] - cj[0])
            col_a = _tintcol(pals[r.a], ang_a)
            col_b = _tintcol(pals[r.b], ang_b)
            tint = col_a[None, None, :] * s[..., None] + col_b[None, None, :] * (1 - s[..., None])
            dist = np.hypot(gx - mid[0], gy - mid[1]) / R
            radial = _ss(prm.get("river_reach", 1.9), prm.get("river_reach", 1.9) * 0.55, dist)
            # asymmetry: the +v end is strong (60/40)
            vx, vy = r.uy, -r.ux
            side = ((gx - mid[0]) * vx + (gy - mid[1]) * vy) / R
            asym = np.where(side > 0, 1.0 if strong_pos else 0.62, 0.62 if strong_pos else 1.0)
            mk = mask_fn(gx, gy) if mask_fn is not None else 1.0
            val = (np.maximum(lum - prm.get("plate_floor", 0.12), 0.0) ** prm.get("plate_gamma", 1.25) * radial * asym * prm.get("river_gain", 0.55) * mk)[..., None] * tint
            _add_up(cv, val, x0, y0, fgrid)
            info["n"] += 1
            info["keys"].append(p["key"])
    return info
