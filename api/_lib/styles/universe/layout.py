# -*- coding: utf-8 -*-
"""uni_layout: where the irises go in the UNIVERSE family. Numbers of BRIEF_V3_FINAL after the addendum (section 0.6):
solo 3.5.x, pair = Collision Infinity 3.1 (d = R + r_p + 0.015 R, clamp 1.22-1.50), groups = Family Colours 3.3 / 3.4
(trio = the measured H24 isosceles 1.53 / 1.71 R, zigzag N=4, brick N=5 (2+3) and N=6 (3+3), ring; d = 1.65 R everywhere).

All sizes are shares of the canvas short side S (or W where the brief says W), so a 4096 master is exactly 4x the 1024 preview.
Screen frame: x right, y DOWN. The brief's axis angles are counter-clockwise from 3 o'clock, so u = (cos a, -sin a) and
"+v" = u rotated +90 deg counter-clockwise on screen = (u_y, -u_x). A is the first-named person.
"""
from __future__ import annotations

# PORT of work package WP8A (step A): uni_layout.py of the scratch prototype, verbatim but for the edits scripts/styles_tests/port_universe.py lists
# (no code changed); test_goldens_universe.py replays the edits on the scratch and the pixels of the scratch's own pictures.

import math
from dataclasses import dataclass, field

SOLO_R = {"echo": 0.25, "deepfield": 0.24, "vortex": 0.22, "starfield": 0.22}     # brief 3.5.2-3.5.5, Appendix A
DUO_R_H = 0.27                # Collision Infinity: R = 0.27 H (3:2 and 5:4)
NAMES_SHRINK = 0.94
NAMES_LIFT = 0.03             # share of the short side
D_MIN, D_MAX = 1.22, 1.50     # pair centre distance clamp, units of R (0.6 R1)
CLEAR = 0.025                 # front limb clears the other pupil rim by this (units of R): the brief says 0.015, but the F3 skirt (to 1.015 R) then reaches the rim itself
KISS_D = 1.70                 # fallback geometry when the pupils need more than D_MAX (3.2)
GROUP_D = 1.65                # Family Colours spacing (0.6 R8, D18)
TRIO_BASE = 1.53              # measured H24
TRIO_FLANK = 1.71


@dataclass
class Slot:
    cx: float
    cy: float
    R: float


@dataclass
class Contact:
    a: int
    b: int
    kind: str = "crumble"     # 'weave' (S weave: A front on the +v side) or 'crumble' (single front, decided by the solver)
    d: float = 0.0            # centre distance px
    front: int = -1           # crumble: index of the front iris (-1 = not decided yet); apex rule sets it


@dataclass
class Layout:
    kind: str                 # solo | duo | group
    n: int
    W: int
    H: int
    S: int
    slots: list
    contacts: list = field(default_factory=list)
    names: bool = False
    text_box: tuple = None    # (x0, y0, x1, y1) px where the names go (matter is culled there)
    aspect: str = "1:1"
    R_units: float = 0.0
    key: str = ""
    layout: str = ""
    info: dict = field(default_factory=dict)


ASP = {"1:1": (1, 1), "3:2": (3, 2), "5:4": (5, 4), "4:5": (4, 5), "3:1": (3, 1), "9:19.5": (9, 19.5)}


def canvas_size(aspect, size):
    a, b = ASP[aspect]
    if a >= b:
        return int(size), max(8, int(round(size * b / a)))
    return max(8, int(round(size * a / b))), int(size)


def _text_box(W, H, S, n):
    """Where the names line sits (baseline 0.93 S single / 0.90 H couple / 0.955 S groups): matter is culled around it."""
    if n == 1:
        base, cap = (0.88 * H if H > 1.5 * W else 0.93 * S), 0.017 * S         # a wallpaper keeps the name above the lock-screen foot (WALL_FOOT 0.06 H), below the iris
    elif n == 2:
        base, cap = 0.90 * H, 0.02 * W
    else:
        base, cap = (0.955 * S if W == H else 0.94 * H), (0.016 if n <= 4 else 0.013) * S
    return (0.08 * W, base - 1.8 * cap, 0.92 * W, base + 1.0 * cap)


# ----------------------------------------------------------------------------- solo
def solo(look, size, aspect="1:1", names=False, r_scale=1.0):
    W, H = canvas_size(aspect, size)
    S = min(W, H)
    wall = aspect == "9:19.5"
    if wall:
        R = 0.31 * W * (SOLO_R[look] / 0.25) * 0.8
        cy = 0.40 * H
    elif aspect in ("4:5",):
        R = SOLO_R[look] * W
        cy = 0.44 * H
    else:
        R = SOLO_R[look] * S
        cy = 0.50 * H
    R *= r_scale
    cx = W / 2.0
    if names:
        R *= NAMES_SHRINK
        cy -= NAMES_LIFT * S
    lay = Layout("solo", 1, W, H, S, [Slot(cx, cy, R)], [], names, aspect=aspect, R_units=R / S, key=f"solo/{look}/{aspect}")
    if names:
        lay.text_box = _text_box(W, H, S, 1)
    return lay


# ----------------------------------------------------------------------------- pair
def duo_distance(reach_a, reach_b, clear=CLEAR, dmin=D_MIN, dmax=D_MAX):
    """d / R for the S-weave pair: max(1 + r_p toward the partner of either iris) + 0.015 R, clamped 1.22-1.50 (brief 1.2).
    Returns (d, d_needed, fallback)."""
    need = 1.0 + max(reach_a, reach_b) + clear
    return min(max(need, dmin), dmax), need, need > dmax + 1e-9


def duo(size, reach_a=0.27, reach_b=0.27, aspect="3:2", names=False, d_override=None, kiss=None):
    """Collision Infinity geometry (3.1). reach_* = the pupil's reach toward the partner along the axis (units of R).
    kiss=True forces the Kiss fallback (d 1.70 R, crumble)."""
    W, H = canvas_size(aspect, size)
    S = min(W, H)
    if aspect in ("3:2", "5:4"):
        R = DUO_R_H * H
        ang = 0.0
        mid = (0.5 * W, 0.50 * H)
    elif aspect == "1:1":
        R = 0.18 * S
        ang = math.radians(35.0)
        mid = (0.5 * W, 0.50 * H)
    elif aspect == "4:5":
        R = 0.17 * H
        ang = math.radians(60.0)
        mid = (0.5 * W, 0.50 * H)
    else:
        raise ValueError(aspect)
    if names:
        R *= NAMES_SHRINK
        mid = (mid[0], mid[1] - NAMES_LIFT * S)
    d, need, fb = duo_distance(reach_a, reach_b)
    fallback = bool(fb) if kiss is None else bool(kiss)
    if fallback:
        d = KISS_D
    if d_override is not None:
        d = d_override
    dpx = d * R
    ux, uy = math.cos(ang), -math.sin(ang)
    A = Slot(mid[0] - ux * dpx / 2, mid[1] - uy * dpx / 2, R)
    B = Slot(mid[0] + ux * dpx / 2, mid[1] + uy * dpx / 2, R)
    kind = "crumble" if fallback else "weave"
    lay = Layout("duo", 2, W, H, S, [A, B], [Contact(0, 1, kind, dpx)], names, aspect=aspect, R_units=R / H,
                 key=f"duo/{aspect}", layout="collision_infinity" if not fallback else "kiss_fallback")
    lay.info.update(d_units=d, d_needed=need, overlap_fallback=fallback, axis=(ux, uy), axis_deg=math.degrees(ang))
    if names:
        lay.text_box = _text_box(W, H, S, 2)
    return lay


# ----------------------------------------------------------------------------- groups
def _pts_trio(d_base=TRIO_BASE, d_flank=TRIO_FLANK):
    """H24 isosceles in units of R, apex first: apex (0, -h), base (+-d_base/2, 0); apex height from the flank length."""
    h = math.sqrt(d_flank ** 2 - (d_base / 2.0) ** 2)
    return [(0.0, -h), (-d_base / 2.0, 0.0), (d_base / 2.0, 0.0)]


def _pts_zigzag(d):
    dy = 0.45
    dx = math.sqrt(d * d - (2 * dy) ** 2)
    return [((i - 1.5) * dx, (-dy if i % 2 == 0 else dy)) for i in range(4)]


def _pts_brick(n, d):
    r3 = math.sqrt(3.0) / 2.0
    if n == 5:
        return [(-d / 2, -d * r3 / 2), (d / 2, -d * r3 / 2), (-d, d * r3 / 2), (0.0, d * r3 / 2), (d, d * r3 / 2)]
    if n == 6:
        top = [((i - 1.0) * d - d / 4.0, -d * r3 / 2) for i in range(3)]
        bot = [((i - 1.0) * d + d / 4.0, d * r3 / 2) for i in range(3)]
        return top + bot
    raise ValueError(n)


def _pts_ring(n, d):
    rho = d / (2.0 * math.sin(math.pi / n))
    return [(rho * math.sin(2 * math.pi * i / n), -rho * math.cos(2 * math.pi * i / n)) for i in range(n)]


# per layout: canvas, R share (of the named base), base
GROUP_TABLE = {
    "trio": ("1:1", "S", 0.20),
    "zigzag": ("3:2", "W", 0.130),
    "brick5": ("3:2", "W", 0.135),
    "brick6": ("3:2", "W", 0.130),
    "ring5": ("1:1", "S", 0.162),
    "ring6": ("1:1", "S", 0.149),
}


def default_layout(n):
    return {3: "trio", 4: "zigzag", 5: "brick5", 6: "brick6"}[n]


def group(n, size, names=False, layout=None, d=GROUP_D, aspect=None, rotate=0, trio_base="crumble"):
    """Family Colours layouts of brief 3.3 / 3.4 for N = 3-6 (universe family). d = 1.65 R at every contact (D18: 1.70 as variant);
    the trio keeps the measured H24 isosceles (base 1.53 R, flanks 1.71 R) whatever d says. rotate cycles the roles of the
    first-named eyes (a new seed)."""
    name = layout or default_layout(n)
    asp0, base, share = GROUP_TABLE[name]
    aspect = aspect or asp0
    W, H = canvas_size(aspect, size)
    S = min(W, H)
    if name == "trio":
        pts = _pts_trio()
        centre_y = -(pts[0][1] - 1.0 + 1.0) / 2.0          # box centre of apex top (-h - 1) and base bottom (+1)
        top, bot = pts[0][1] - 1.0, 1.0
        my = (top + bot) / 2.0
        pts = [(x, y - my) for x, y in pts]
    else:
        if name == "zigzag":
            pts = _pts_zigzag(d)
        elif name.startswith("brick"):
            pts = _pts_brick(n, d)
        else:
            pts = _pts_ring(n, d)
        mx = (max(p[0] for p in pts) + min(p[0] for p in pts)) / 2.0
        my = (max(p[1] for p in pts) + min(p[1] for p in pts)) / 2.0
        pts = [(x - mx, y - my) for x, y in pts]
    if rotate and name == "trio":
        pts = [pts[(i + rotate) % 3] for i in range(3)]
    unit = {"S": S, "W": W, "H": H}[base]
    R = share * unit
    cx0 = W / 2.0
    cy0 = H / 2.0
    if names:
        R *= NAMES_SHRINK
        cy0 -= NAMES_LIFT * S
    slots = [Slot(cx0 + x * R, cy0 + y * R, R) for x, y in pts]
    contacts = []
    for i in range(n):
        for j in range(i + 1, n):
            dist = math.hypot(slots[i].cx - slots[j].cx, slots[i].cy - slots[j].cy)
            if dist < 1.95 * R:
                contacts.append(Contact(i, j, "crumble", dist))
    lay = Layout("group", n, W, H, S, slots, contacts, names, aspect=aspect, R_units=R / S, key=f"group{n}/{name}/{aspect}", layout=name)
    if name == "trio":
        # apex (the topmost slot) in front of both bases; the base pair is a crumble too (AD D3: the owner's H24 has no weave there) unless
        # trio_base="weave" (the brief's S weave between the bases)
        ia = min(range(3), key=lambda i: slots[i].cy)
        ib = [i for i in range(3) if i != ia]
        bl, br = (ib[0], ib[1]) if slots[ib[0]].cx < slots[ib[1]].cx else (ib[1], ib[0])
        lay.contacts = []
        lay.contacts.append(Contact(bl, br, "weave" if trio_base == "weave" else "crumble",
                                    math.hypot(slots[bl].cx - slots[br].cx, slots[bl].cy - slots[br].cy)))
        for b in (bl, br):
            lay.contacts.append(Contact(ia, b, "crumble", math.hypot(slots[ia].cx - slots[b].cx, slots[ia].cy - slots[b].cy), front=ia))
        lay.info.update(apex=ia, base_left=bl, base_right=br)
    lay.info.update(d_units=d if name != "trio" else TRIO_BASE, R_px=R)
    if names:
        lay.text_box = _text_box(W, H, S, n)
    return lay


def check(lay, margin=0.5):
    """Every iris inside the canvas with margin (units of R) free."""
    for i, s in enumerate(lay.slots):
        assert s.cx - s.R * (1 + margin) >= -1 and s.cx + s.R * (1 + margin) <= lay.W + 1, f"iris {i} x out of bounds in {lay.key}"
        assert s.cy - s.R * (1 + margin) >= -1 and s.cy + s.R * (1 + margin) <= lay.H + 1, f"iris {i} y out of bounds in {lay.key}"
    return True
