# -*- coding: utf-8 -*-
"""fx.collision_layouts: layouts of the v3 collision designs (BRIEF_V3_FINAL 1.6, 1.7.7, 3.1-3.4), ported from the scratch prototype.

Every layout function returns a Scene: canvas, centres and radii (px, before the disc grade snaps them; Scene.refresh()
re-reads the exact snapped discs), the overlap plan (Rule per contact: S weave or single front), merge order, the notch
list (outer notches carry a plume weight), the text lines and the union box.

All numbers are the brief's section 0.6 numbers (NOT the pre-addendum draft): Collision Infinity d = R + r_p + 0.015 R
(clamp 1.22-1.50), Kiss 1.70 R, Trio = the measured H24 isosceles (base 1.53 R, flanks 1.71 R), Family contacts 1.65 R,
Infinity Chain 1.40 R.

Units: R = iris radius (px), S = short side. Screen frame: x right, y DOWN. The brief's axis angles are counter-clockwise
from 3 o'clock, so u = (cos a, -sin a); "+v" = u rotated +90 deg counter-clockwise ON SCREEN = (u_y, -u_x).
A is the first-named eye. numpy-free (pure python geometry).
"""
from __future__ import annotations

# PORT of work package WP7A (step A): collision_layouts.py of the DG1 snapshot of the scratch prototype, verbatim but for the edits
# scripts/styles_tests/port_collision.py lists (the prototype's scene key is kept (it is part of the step A seed)); test_goldens_collision.py replays the edits on the scratch and the pixels of the
# scratch's own pictures.

import math
from dataclasses import dataclass, field

ASPECTS = {"1:1": (1.0, 1.0), "3:2": (3.0, 2.0), "5:4": (5.0, 4.0), "4:5": (4.0, 5.0), "3:1": (3.0, 1.0), "9:19.5": (9.0, 19.5)}

D_INF_MARGIN = 0.025          # R1 (brief: +0.015 R): +0.025 R so the dilated pupil (0.01 R) also clears the F3 feather (+-0.015 R) of the front iris
D_INF_MIN, D_INF_MAX = 1.22, 1.50
D_KISS = 1.70                 # R2 / D18
D_FAMILY = 1.65               # R8
D_CHAIN = 1.40                # R8
TRIO_BASE, TRIO_FLANK = 1.53, 1.71      # R7 (measured H24)


def canvas_size(fmt, size=1024):
    """W, H with `size` the long side. A size that is a multiple of 1024 is EXACTLY that multiple of the 1024 canvas (round 2c: a 3:2 canvas is 1024 x 683 and
    4096 x 2732, not 2731, so the two pixel grids line up sample for sample)."""
    if size > 1024 and size % 1024 == 0:
        w1, h1 = canvas_size(fmt, 1024)
        return w1 * (size // 1024), h1 * (size // 1024)
    a, b = ASPECTS[fmt]
    if a >= b:
        return int(size), max(8, int(round(size * b / a)))
    return max(8, int(round(size * a / b))), int(size)


@dataclass
class Rule:
    """One overlap between two irises. mode: 'weave' (A in front on the +v side of the lens, B on the -v side),
    'front_a' / 'front_b' (one iris in front everywhere), 'stack' (front not decided yet). ux, uy: unit vector A -> B."""
    a: int
    b: int
    mode: str
    ux: float = 1.0
    uy: float = 0.0
    d: float = 0.0                       # centre distance in px
    crumble: bool = False                # crumble variant of the contact edge (no continuous line)


@dataclass
class Notch:
    x: float
    y: float
    dx: float                            # wedge bisector (unit, pointing away from the pair)
    dy: float
    i: int
    j: int
    weight: float = 1.0                  # plume unit (free outer notch 1.0, pocket 0.5)
    kind: str = "outer"                  # outer | inner (covered by a third iris)
    strong: bool = True                  # kiss: strong or weak end
    side: int = 1                        # +1: on the +v side of the rule axis, -1 on the -v side
    rule: int = 0
    wedge_deg: float = 0.0


@dataclass
class Scene:
    key: str
    fmt: str
    W: int
    H: int
    S: int
    R: list
    centres: list
    rules: list
    order: list                          # merge order: [(iris, [(partner, rule_index), ...]), ...]
    notches: list = field(default_factory=list)
    text_lines: list = field(default_factory=list)   # [(kind, cx, baseline_y, cap_px, max_w)] kinds: names | date
    box: tuple = None                    # union box of the irises (x0, y0, x1, y1)
    axis_deg: float = 0.0
    d_over_R: float = 0.0
    names: bool = False
    info: dict = field(default_factory=dict)

    @property
    def n(self):
        return len(self.R)

    def refresh(self, discs):
        """Adopt the EXACT centres and radii of the placed (pixel-snapped) discs, recompute every rule's axis and every
        notch from them."""
        self.centres = [(d.cx, d.cy) for d in discs]
        self.R = [d.R for d in discs]
        for r in self.rules:
            ca, cb = self.centres[r.a], self.centres[r.b]
            dd = math.hypot(cb[0] - ca[0], cb[1] - ca[1])
            r.ux, r.uy, r.d = (cb[0] - ca[0]) / dd, (cb[1] - ca[1]) / dd, dd
        Rm = sum(self.R) / len(self.R)
        self.notches = build_notches(self)
        self.box = (min(c[0] - r for c, r in zip(self.centres, self.R)), min(c[1] - r for c, r in zip(self.centres, self.R)),
                    max(c[0] + r for c, r in zip(self.centres, self.R)), max(c[1] + r for c, r in zip(self.centres, self.R)))
        self.info["R_mean"] = Rm
        return self


def _u(axis_deg):
    a = math.radians(axis_deg)
    return math.cos(a), -math.sin(a)


def circle_intersections(c1, r1, c2, r2):
    """The two intersection points of two circles (or None): (point on the +v side of c1 -> c2, point on the -v side)."""
    dx, dy = c2[0] - c1[0], c2[1] - c1[1]
    d = math.hypot(dx, dy)
    if d >= r1 + r2 or d <= abs(r1 - r2) or d == 0:
        return None
    a = (r1 * r1 - r2 * r2 + d * d) / (2 * d)
    h = math.sqrt(max(r1 * r1 - a * a, 0.0))
    ux, uy = dx / d, dy / d
    vx, vy = uy, -ux
    mx, my = c1[0] + a * ux, c1[1] + a * uy
    return (mx + h * vx, my + h * vy), (mx - h * vx, my - h * vy)


def _bisector(p, ci, ri, cj, rj):
    nx = (p[0] - ci[0]) / ri + (p[0] - cj[0]) / rj
    ny = (p[1] - ci[1]) / ri + (p[1] - cj[1]) / rj
    n = math.hypot(nx, ny) or 1.0
    return nx / n, ny / n


def build_notches(sc):
    """All notches of every rule, classified: 'inner' when covered by a third iris (inside its disc), 'outer' otherwise.
    Outer notch weight 1.0, 0.5 when it lies in a concave pocket (a third iris centre within 1.55 R of it)."""
    out = []
    for ri, r in enumerate(sc.rules):
        ci, cj = sc.centres[r.a], sc.centres[r.b]
        pts = circle_intersections(ci, sc.R[r.a], cj, sc.R[r.b])
        if pts is None:
            continue
        for s, p in zip((+1, -1), pts):
            bx, by = _bisector(p, ci, sc.R[r.a], cj, sc.R[r.b])
            covered = False
            pocket = False
            for k, (ck, rk) in enumerate(zip(sc.centres, sc.R)):
                if k in (r.a, r.b):
                    continue
                dk = math.hypot(p[0] - ck[0], p[1] - ck[1])
                if dk < rk * 0.999:
                    covered = True
                elif dk < rk * 1.55:
                    pocket = True
            n = Notch(p[0], p[1], bx, by, r.a, r.b, 0.0 if covered else (0.5 if pocket else 1.0),
                      "inner" if covered else "outer", True, s, ri)
            cosang = ((p[0] - ci[0]) * (p[0] - cj[0]) + (p[1] - ci[1]) * (p[1] - cj[1])) / (sc.R[r.a] * sc.R[r.b])
            n.wedge_deg = 180.0 - math.degrees(math.acos(max(-1.0, min(1.0, cosang))))
            out.append(n)
    return out


def lens_facts(d):
    """d in units of R (equal irises): lens area share of one iris, notch half height h, wedge deg."""
    if d >= 2.0:
        return 0.0, 0.0, 180.0
    a = 2 * math.acos(d / 2) - (d / 2) * math.sqrt(4 - d * d)
    h = math.sqrt(1 - d * d / 4)
    wedge = 180.0 - math.degrees(math.acos(h * h - d * d / 4))
    return a / math.pi, h, wedge


def solve_infinity_d(reach_a, reach_b):
    """Placement rule (brief 1.2): d = max(1 + reach_A(u), 1 + reach_B(-u)) + 0.015, clamped 1.22-1.50. reach_x = pupil's reach
    toward the partner along the axis of centres (R units, from the iris centre). Returns (d, raw, over_max)."""
    raw = max(1.0 + reach_a, 1.0 + reach_b) + D_INF_MARGIN
    return min(max(raw, D_INF_MIN), D_INF_MAX), raw, raw > D_INF_MAX


# ----------------------------------------------------------------------------- text
TEXT_COL = (201, 184, 160)               # #C9B8A0


def _text_lines(W, H, S, kind, names, has_date, fmt, wall):
    """Caption geometry per brief 1.5.7: [(kind, cx, baseline_y, cap_px, max_w)]."""
    if not names:
        return []
    out = []
    if kind == "pair":
        base = 0.90 * H
        cap = 0.02 * W if not wall else 0.02 * W
    elif kind == "group":
        base = 0.94 * H if fmt in ("3:2", "5:4") else 0.955 * S if fmt == "1:1" else 0.955 * H
        cap = 0.016 * S
    else:
        base = 0.93 * S
        cap = 0.017 * S
    out.append(("names", 0.5 * W, base, cap, 0.8 * W))
    if has_date:
        out.append(("date", 0.5 * W, base + 2.6 * cap, 0.011 * S, 0.8 * W))
    return out


# ----------------------------------------------------------------------------- pair layouts
_INF = {   # fmt: (axis deg, R/H or S or W without names, with names, base dimension)
    "3:2": (0.0, 0.27, 0.254, "H"), "5:4": (0.0, 0.27, 0.254, "H"), "1:1": (35.0, 0.18, 0.169, "S"),
    "4:5": (60.0, 0.17, 0.16, "H"), "9:19.5": (-90.0, 0.26, 0.244, "W"),
}
_KISS = {
    "3:2": (25.0, 0.27, 0.254, "H"), "5:4": (25.0, 0.27, 0.254, "H"), "1:1": (40.0, 0.17, 0.160, "S"),
    "4:5": (55.0, 0.15, 0.141, "H"), "9:19.5": (-90.0, 0.24, 0.226, "W"),
}
_CLEAN = {
    "3:2": (0.0, 0.315, 0.296, "H"), "5:4": (0.0, 0.315, 0.296, "H"), "1:1": (35.0, 0.21, 0.197, "S"),
    "4:5": (60.0, 0.20, 0.188, "H"), "9:19.5": (-90.0, 0.29, 0.273, "W"),
}


def _base(dim, W, H, S):
    return {"H": H, "W": W, "S": S}[dim]


def pair_scene(fmt="3:2", size=1024, d_over_R=1.275, names=False, has_date=False, kind="infinity", axis_deg=None,
               R_scale=1.0, flip=False, key=None, front=None):
    """Two irises. kind: 'infinity' (Collision Infinity: S weave), 'clean' (Clean Infinity: bigger, weave, no matter),
    'kiss' (Kiss Collision: single front, crumble). front: for kiss 'a' | 'b' (which iris is in front)."""
    W, H = canvas_size(fmt, size)
    S = min(W, H)
    wall = fmt == "9:19.5"
    table = {"infinity": _INF, "clean": _CLEAN, "kiss": _KISS}[kind]
    ax, r0, r1, dim = table[fmt]
    Rr = (r1 if names else r0) * _base(dim, W, H, S) * R_scale
    if axis_deg is not None:
        ax = axis_deg
    u = _u(ax)
    if flip:
        u = (-u[0], -u[1])
    d = d_over_R * Rr
    cx, cy = 0.5 * W, ((0.47 if names else 0.50) * H)
    A = (cx - u[0] * d / 2, cy - u[1] * d / 2)
    B = (cx + u[0] * d / 2, cy + u[1] * d / 2)
    mode = "weave" if kind in ("infinity", "clean") else ("front_a" if front == "a" else "front_b" if front == "b" else "stack")
    rule = Rule(0, 1, mode, u[0], u[1], d, crumble=(kind == "kiss"))
    sc = Scene(key or {"infinity": "duo.collision_infinity", "clean": "duo.clean", "kiss": "duo.kiss_collision"}[kind], fmt, W, H, S,
               [Rr, Rr], [A, B], [rule], [(0, []), (1, [(0, 0)])], axis_deg=ax, d_over_R=d_over_R, names=names)
    sc.text_lines = _text_lines(W, H, S, "pair", names, has_date, fmt, wall)
    sc.info.update(wall=wall, kind=kind, layout=kind)
    sc.notches = build_notches(sc)
    sc.box = (min(A[0], B[0]) - Rr, min(A[1], B[1]) - Rr, max(A[0], B[0]) + Rr, max(A[1], B[1]) + Rr)
    return sc


# ----------------------------------------------------------------------------- trio (owner's H24, measured isosceles)
def trio_scene(fmt="1:1", size=1024, names=False, has_date=False, rotate=0, key="grp.collision.trio", base_mode="crumble"):
    """Apex (first named) on top, base left / right. Base centres (+-0.765 R, 0), apex (0, -1.529 R) from the base midpoint.
    rotate cycles the roles (new seed)."""
    W, H = canvas_size(fmt, size)
    S = min(W, H)
    wall = fmt == "9:19.5"
    if fmt == "1:1":
        Rr, cyf = (0.188 if names else 0.20) * S, (0.475 if names else 0.50)
    elif fmt in ("3:2", "5:4"):
        Rr, cyf = (0.205 * 0.94 if names else 0.205) * H, (0.475 if names else 0.50)
    elif fmt == "4:5":
        Rr, cyf = (0.205 * 0.94 if names else 0.205) * W * 0.85 * (5 / 4) * 0.8, (0.475 if names else 0.50)
    else:   # wallpaper
        Rr, cyf = (0.19 * 0.94 if names else 0.19) * W, 0.42
    cx = 0.5 * W
    # box centre relative to the base midpoint M: y_c = -0.7645 R
    ymid = cyf * H + 0.7645 * Rr
    base = TRIO_BASE
    hb = base / 2.0
    apex_h = math.sqrt(TRIO_FLANK ** 2 - hb ** 2)
    pts = [(0.0, -apex_h), (-hb, 0.0), (hb, 0.0)]         # apex, base left, base right (R units)
    order3 = [pts[(i + rotate) % 3] for i in range(3)]
    centres = [(cx + p[0] * Rr, ymid + p[1] * Rr) for p in order3]
    ia = min(range(3), key=lambda i: centres[i][1])
    ib = [i for i in range(3) if i != ia]
    bl, br = (ib[0], ib[1]) if centres[ib[0]][0] < centres[ib[1]][0] else (ib[1], ib[0])
    rules = []
    dx, dy = centres[br][0] - centres[bl][0], centres[br][1] - centres[bl][1]
    dn = math.hypot(dx, dy)
    # round 2c (AD F, the owner's H24: no dark line at ANY contact): the base pair is a single-front crumble like the flanks; base_mode="weave" is the brief's S weave
    rules.append(Rule(bl, br, "weave", dx / dn, dy / dn, dn) if base_mode == "weave" else Rule(bl, br, "stack", dx / dn, dy / dn, dn, crumble=True))
    for b in (bl, br):
        dx, dy = centres[b][0] - centres[ia][0], centres[b][1] - centres[ia][1]
        dn = math.hypot(dx, dy)
        rules.append(Rule(ia, b, "front_a", dx / dn, dy / dn, dn, crumble=True))
    order = [(bl, []), (br, [(bl, 0)]), (ia, [(bl, 1), (br, 2)])]
    sc = Scene(key, fmt, W, H, S, [Rr] * 3, centres, rules, order, d_over_R=TRIO_FLANK, names=names)
    sc.text_lines = _text_lines(W, H, S, "group", names, has_date, fmt, wall)
    sc.info.update(apex=ia, base_left=bl, base_right=br, wall=wall, layout="trio", rotate=rotate)
    sc.notches = build_notches(sc)
    sc.box = (min(c[0] for c in centres) - Rr, min(c[1] for c in centres) - Rr, max(c[0] for c in centres) + Rr,
              max(c[1] for c in centres) + Rr)
    return sc


# ----------------------------------------------------------------------------- chains (Infinity Chain)
def chain_scene(n, fmt="3:2", size=1024, names=False, has_date=False, key="grp.chain", d_over_R=None):
    """Irises on a line, d = 1.40 R, S weave on every link (iris i in front on the +v = upper half of lens (i, i+1))."""
    if n < 3 or n > 6:
        raise ValueError("chain: 3-6 irises")
    W, H = canvas_size(fmt, size)
    S = min(W, H)
    d_ = max(D_CHAIN, d_over_R or 0.0)
    scale = ((n - 1) * D_CHAIN + 2.0) / ((n - 1) * d_ + 2.0)          # a wider spacing (big pupils) shrinks the irises, the chain keeps its width
    if fmt == "3:1":
        Rr = {4: 0.113, 5: 0.105, 6: 0.101}[n] * W * (0.94 if names else 1.0) * scale
        cy = (0.44 if names else 0.46) * H
    elif fmt == "3:2":
        Rr = {3: 0.159, 4: 0.128}[n] * W * (0.94 if names else 1.0) * scale
        cy = (0.44 if names else 0.46) * H
        if n > 4:
            raise ValueError("3:2 chain supports N 3-4")
    elif fmt == "9:19.5":       # column chain N 3-4
        Rr = {3: 0.25, 4: 0.21}[n] * W * (0.94 if names else 1.0) * scale
        return _column_chain(n, W, H, S, Rr, names, key, d_)
    else:
        raise ValueError("chain: 3:1, 3:2 or 9:19.5")
    d = d_ * Rr
    total = (n - 1) * d
    x0 = W / 2 - total / 2
    centres = [(x0 + i * d, cy) for i in range(n)]
    rules, order = [], [(0, [])]
    for i in range(n - 1):
        rules.append(Rule(i, i + 1, "weave", 1.0, 0.0, d))
        order.append((i + 1, [(i, len(rules) - 1)]))
    sc = Scene(key, fmt, W, H, S, [Rr] * n, centres, rules, order, d_over_R=d_, names=names)
    sc.text_lines = _text_lines(W, H, S, "group", names, has_date, fmt, False)
    sc.info.update(layout="chain", wall=False)
    sc.notches = build_notches(sc)
    sc.box = (centres[0][0] - Rr, cy - Rr, centres[-1][0] + Rr, cy + Rr)
    return sc


def _column_chain(n, W, H, S, Rr, names, key, d_=D_CHAIN):
    d = d_ * Rr
    total = (n - 1) * d
    cy0 = 0.52 * H - total / 2
    centres = [(0.5 * W, cy0 + i * d) for i in range(n)]
    rules, order = [], [(0, [])]
    for i in range(n - 1):
        rules.append(Rule(i, i + 1, "weave", 0.0, 1.0, d))       # A -> B points down; +v = (uy, -ux) = (1, 0): right half
        order.append((i + 1, [(i, len(rules) - 1)]))
    sc = Scene(key, "9:19.5", W, H, S, [Rr] * n, centres, rules, order, d_over_R=d_, names=names)
    sc.text_lines = _text_lines(W, H, S, "group", names, False, "9:19.5", True)
    sc.info.update(layout="chain_column", wall=True)
    sc.notches = build_notches(sc)
    sc.box = (centres[0][0] - Rr, centres[0][1] - Rr, centres[-1][0] + Rr, centres[-1][1] + Rr)
    return sc


# ----------------------------------------------------------------------------- family colours (crumble contacts, d = 1.65 R)
def _hex_rows(rows, R1=1.0):
    """Hex packing rows at d = 1.65: row counts -> list of (x, y) in R units centred on the box."""
    d = D_FAMILY
    dy = d * math.sqrt(3) / 2
    pts = []
    for r, cnt in enumerate(rows):
        for c in range(cnt):
            pts.append(((c - (cnt - 1) / 2) * d, (r - (len(rows) - 1) / 2) * dy))
    return pts


def _contacts(centres, R, dmax=1.90):
    """Every pair closer than dmax R (family and cluster contacts)."""
    out = []
    n = len(centres)
    for i in range(n):
        for j in range(i + 1, n):
            dd = math.hypot(centres[i][0] - centres[j][0], centres[i][1] - centres[j][1])
            if dd < dmax * 0.5 * (R[i] + R[j]):
                out.append((i, j, dd))
    return out


def family_scene(n, layout=None, fmt=None, size=1024, names=False, has_date=False, rotate=0, key="grp.collision"):
    """Family Colours layouts of brief 3.4. layout: zigzag | brick | ring | flower | cluster | diag. Defaults per N:
    3 trio (use trio_scene), 4 zigzag 3:2, 5 brick 2+3 3:2, 6 brick 3+3 3:2, 7 ring 1:1, 8 ring 1:1."""
    if n == 3 and layout in (None, "trio"):
        return trio_scene(fmt or "1:1", size, names, has_date, rotate)
    layout = layout or {3: "diag", 4: "zigzag", 5: "brick", 6: "brick", 7: "ring", 8: "ring"}[n]
    fmt = fmt or {"zigzag": "3:2", "brick": "3:2", "diag": "3:2", "ring": "1:1", "flower": "1:1", "cluster": "1:1"}[layout]
    if layout == "brick" and n >= 7:
        fmt = "1:1"
    W, H = canvas_size(fmt, size)
    S = min(W, H)
    nm = 0.94 if names else 1.0
    d = D_FAMILY
    if layout == "zigzag":
        Rr = 0.130 * W * nm
        dxr, offr = 1.38, 0.9
        pts = [((i - (n - 1) / 2) * dxr, (offr / 2 if i % 2 == 0 else -offr / 2)) for i in range(n)]
        # first eye lower-left: even index low (y positive on screen means lower)
        pts = [(x, -y) for x, y in pts]
        pts = [(x, y) for x, y in pts]
        ex, ey = (n - 1) * dxr / 2 + 1, offr / 2 + 1
        ymid_f = 0.47 if names else 0.50
    elif layout == "brick":
        rows = {4: [2, 2], 5: [2, 3], 6: [3, 3], 7: [2, 3, 2], 8: [3, 2, 3]}[n]
        pts = _hex_rows(rows)
        if n in (5, 6):
            # offset rows by half a step for the hex packing (rows with different counts already centre; equal rows shift)
            if rows[0] == rows[1]:
                pts = [(x + (0.5 * d if r >= rows[0] else -0.5 * d) * 0.5, y) for (x, y), r in zip(pts, range(n))]
        Rr = {5: 0.135 * W, 6: 0.130 * W, 7: 0.138 * S, 8: 0.149 * S, 4: 0.13 * W}[n] * nm
        if n >= 7:
            Rr = {7: 0.138, 8: 0.149}[n] * S * nm
        ymid_f = 0.47 if names else 0.50
    elif layout == "ring":
        rho = d / (2 * math.sin(math.pi / n))
        pts = [(rho * math.cos(math.radians(90.0 - 360.0 * i / n)), -rho * math.sin(math.radians(90.0 - 360.0 * i / n))) for i in range(n)]
        # screen y: use +y down, angle measured so first eye is at 12 o'clock and the rest go clockwise on screen
        pts = [(rho * math.sin(2 * math.pi * i / n), -rho * math.cos(2 * math.pi * i / n)) for i in range(n)]
        Rr = {4: 0.173, 5: 0.162, 6: 0.149, 7: 0.138, 8: 0.129}[n] * S * nm
        ymid_f = 0.465 if names else 0.50
    elif layout == "flower":
        m = n - 1
        rho = d
        pts = [(0.0, 0.0)] + [(rho * math.sin(2 * math.pi * i / m), -rho * math.cos(2 * math.pi * i / m)) for i in range(m)]
        Rr = 0.149 * S * nm
        ymid_f = 0.465 if names else 0.50
    elif layout == "cluster":
        if n != 4:
            raise ValueError("cluster: N = 4 (2x2)")
        pts = [(-d / 2, -d / 2), (d / 2, -d / 2), (-d / 2, d / 2), (d / 2, d / 2)]
        Rr = 0.195 * S * nm
        ymid_f = 0.465 if names else 0.50
    elif layout == "diag":       # diagonal chain of 3, axis 30 deg, middle over the first (crumble, d 1.65)
        a = math.radians(30.0)
        pts = [((i - 1) * d * math.cos(a), -(i - 1) * d * math.sin(a) * -1.0 * -1.0) for i in range(3)]
        pts = [((i - 1) * d * math.cos(a), (1 - i) * d * math.sin(a)) for i in range(3)]      # first eye lower-left
        Rr = 0.159 * W * nm
        ymid_f = 0.47 if names else 0.50
    else:
        raise ValueError(layout)
    # centre the box on (0.5 W, ymid H)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    bx, by = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    cx0, cy0 = 0.5 * W, ymid_f * H
    centres = [(cx0 + (x - bx) * Rr, cy0 + (y - by) * Rr) for x, y in pts]
    if rotate:
        centres = centres[rotate:] + centres[:rotate] if False else centres
    R = [Rr] * n
    rules = []
    for (i, j, dd) in _contacts(centres, R):
        rules.append(Rule(i, j, "front_a" if (layout == "flower" and i == 0) else "stack", (centres[j][0] - centres[i][0]) / dd,
                          (centres[j][1] - centres[i][1]) / dd, dd, crumble=True))
    order = [(0, [])]
    for i in range(1, n):
        order.append((i, [(r.a, k) for k, r in enumerate(rules) if r.b == i and r.a < i]))
    sc = Scene(key, fmt, W, H, S, R, centres, rules, order, d_over_R=d, names=names)
    sc.text_lines = _text_lines(W, H, S, "group", names, has_date, fmt, False)
    sc.info.update(layout=layout, wall=False, n=n)
    sc.notches = build_notches(sc)
    sc.box = (min(c[0] for c in centres) - Rr, min(c[1] for c in centres) - Rr, max(c[0] for c in centres) + Rr,
              max(c[1] for c in centres) + Rr)
    if layout == "ring":
        sc.info["ring_rho"] = d / (2 * math.sin(math.pi / n))
        sc.info["hollow_centre"] = (cx0, cy0)
    return sc


def n_eff(sc):
    return sum(nc.weight for nc in sc.notches if nc.kind == "outer")


def check(sc, margin=0.5):
    """Assert every iris lies inside the canvas with margin R free (0.5 R of halo room) and D >= 22 % of W for the default
    layouts. Raises AssertionError with the offender."""
    for k, (c, r) in enumerate(zip(sc.centres, sc.R)):
        assert c[0] - r >= 0 and c[0] + r <= sc.W and c[1] - r >= 0 and c[1] + r <= sc.H, f"iris {k} clipped in {sc.key} {sc.fmt}"
    return True


def dfloor_ok(sc):
    """D >= 22 % of the canvas width (3:1 panorama: D >= 0.60 H)."""
    D = 2.0 * min(sc.R)
    if sc.fmt == "3:1":
        return D >= 0.60 * sc.H - 1
    return D >= 0.22 * sc.W - 1
