# -*- coding: utf-8 -*-
"""styles.layouts: where the discs go, for 1-8 eyes, per layout family and canvas shape. A verbatim port of the scratch
prototype fx/layouts.py (work package WP4). These are the solo and legacy families (single, duo, row, circle, cluster) that the
singles engines and the legacy placement use. The collision scenes (pair, trio, zigzag, brick, ring, flower, chain) and the universe
layouts arrive with their engine packages, as ports of collision_layouts.py and uni_layout.py; the three solvers are merged
into this module only in the clean-up package, under the goldens.

Every number is a share of S (canvas short side) or of W / H, so a 4096 master is exactly 4 x the 1024 preview.
Families:
  single   n = 1      one disc 0.62-0.66 S (default 0.64) at y = 0.46 H; wallpaper 0.80 W at y = 0.56 H
  duo      n = 2      two whole discs D <= 0.58 S on a diagonal, near-touching (gap 0.03 D, angle 15 deg on landscape,
                      35 deg on square/portrait, 75 deg on the wallpaper = stacked), A upper left, B lower right,
                      pair centred at 0.47 H where the caption band allows (3:2: A top 0.08 H, B bottom 0.815 H)
  row      n = 1-8    panorama: one line (gap 0.08 D), or two staggered lines when that gives larger discs;
                      on the wallpaper the lines are columns
  circle   n = 1-8    discs evenly on a circle Rc = 0.27 S, D = min(0.30 S, 2 Rc sin(pi/n) 0.88), start angle
                      0 deg for odd n, 180/n for even n (none at 12 or 6 o'clock)
  cluster  n = 1-8    the repo's arrangements (single, duo, triangle, grid, galaxy = L._cluster), packed size x
                      shrink (default 0.84, the room Radiance Family's rays need)
Each family keeps its spec sizes as MAXIMUMS and scales the whole arrangement down only when the free box (canvas
minus margins, the wallpaper's clock fifth and the caption band) is too small, so every n passes the bounds
assertion (check) in 1:1, 3:2, 4:5, 3:1 and the 9:19.5 phone wallpaper, in every caption mode.

Caption modes (Caption.top = the band's upper edge; no disc goes below it):
  full   title + names + footer, the repo's positions: H - lift - (0.185 | 0.14 | 0.095 | 0.055) ut
  names  names + footer: H - lift - (0.10 | 0.07 | 0.033) ut   (1:1: names at 0.93 S)
  none   no text (Studio Black bare): 0.05 S margin, the wallpaper keeps 0.12 H for its buttons
  ut = max(S, 0.66 x long side) (L.TYPE_WIDE), lift = 0.06 H on the wallpaper (L.WALL_FOOT).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .. import iris as L

ASPECTS = {"1:1": (1.0, 1.0), "3:2": (3.0, 2.0), "4:5": (4.0, 5.0), "3:1": (3.0, 1.0), "9:19.5": (9.0, 19.5)}
WALL = "9:19.5"
FAMILIES = ("single", "duo", "row", "circle", "cluster")
N_RANGE = {"single": (1, 1), "duo": (2, 2), "row": (1, 8), "circle": (1, 8), "cluster": (1, 8)}
DEFAULT_CAPTION = {"single": "full", "duo": "full", "row": "names", "circle": "names", "cluster": "names"}
MARGIN = 0.05                # side and top margin, share of S
WALL_TOP = L.WALL_TOP        # 0.20 H left to the lock-screen clock
WALL_FOOT = L.WALL_FOOT      # 0.06 H under the caption (home bar)
WALL_FOOT_BARE = L.WALL_FOOT_BARE
TYPE_WIDE = L.TYPE_WIDE
MIN_D = 0.10                 # the bounds assertion refuses a disc smaller than this share of S


@dataclass
class Caption:
    mode: str
    u: float                  # the type scale (ut)
    top: float                # upper edge of the caption band, px
    title_y: float = None
    names_y: float = None
    footer_y: float = None
    title_px: float = 0.0
    names_px: float = 0.0
    footer_px: float = 0.0


@dataclass
class Slot:
    cx: float
    cy: float
    r: float                  # visible iris radius, px


@dataclass
class Layout:
    family: str
    aspect: str
    n: int
    W: int
    H: int
    S: int
    wall: bool
    caption: Caption
    box: tuple                # (x0, y0, x1, y1) the free box every disc must stay inside
    slots: list = field(default_factory=list)

    @property
    def key(self):
        """The layout part of the seed: the same design as artwork and as wallpaper differs on purpose."""
        return f"{self.family}/{self.aspect}"


def canvas_size(aspect, size=1024):
    """(W, H) with the LONGEST side = size (compose's convention: 1024 preview, 4096 master)."""
    a, b = ASPECTS[aspect]
    if a >= b:
        return int(size), max(8, int(round(size * b / a)))
    return max(8, int(round(size * a / b))), int(size)


def caption_geometry(W, H, mode, wall):
    S = min(W, H)
    ut = max(float(S), TYPE_WIDE * max(W, H))
    if mode == "none":
        return Caption("none", ut, H - (WALL_FOOT_BARE * H if wall else MARGIN * S))
    lift = WALL_FOOT * H if wall else 0.0
    if mode == "full":
        return Caption("full", ut, H - lift - 0.185 * ut, H - lift - 0.14 * ut, H - lift - 0.095 * ut, H - lift - 0.055 * ut,
                       0.042 * ut, 0.026 * ut, 0.014 * ut)
    if mode == "names":
        return Caption("names", ut, H - lift - 0.10 * ut, None, H - lift - 0.07 * ut, H - lift - 0.033 * ut,
                       0.0, 0.030 * ut, 0.013 * ut)
    raise ValueError(f"caption mode is full, names or none, not {mode!r}")


def free_box(W, H, cap, wall):
    S = min(W, H)
    top = WALL_TOP * H if wall else MARGIN * S
    return (MARGIN * S, top, W - MARGIN * S, cap.top)


def _fit(pts, box, max_d=None, prefer=None):
    """Unit-diameter disc centres pts -> (D px, [(cx, cy)]): the largest D (capped at max_d) at which the
    arrangement fits box, centred on prefer=(x, y) when given (clamped so it stays inside), else on the box centre."""
    x0, y0, x1, y1 = box
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    w, h = max(xs) - min(xs) + 1.0, max(ys) - min(ys) + 1.0
    D = min((x1 - x0) / w, (y1 - y0) / h)
    if max_d is not None:
        D = min(D, max_d)
    mx, my = (max(xs) + min(xs)) / 2.0, (max(ys) + min(ys)) / 2.0
    hw, hh = w * D / 2.0, h * D / 2.0
    bx, by = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    if prefer is not None:
        bx = min(max(prefer[0], x0 + hw), x1 - hw) if x1 - x0 >= 2 * hw else bx
        by = min(max(prefer[1], y0 + hh), y1 - hh) if y1 - y0 >= 2 * hh else by
    return D, [(bx + (px - mx) * D, by + (py - my) * D) for px, py in pts]


# ----------------------------------------------------------------------------- families
def _single(n, W, H, S, box, wall, d=0.64, y=None):
    if wall:
        D = 0.80 * W
        prefer = (W / 2.0, (y if y is not None else 0.56) * H)
    else:
        D = d * S
        prefer = (W / 2.0, (y if y is not None else 0.46) * H)
    return _fit([(0.0, 0.0)], box, D, prefer)


def _duo(n, W, H, S, box, wall, gap=0.03, angle=None, d_max=0.58, y=0.47):
    if angle is None:
        ar = W / float(H)
        angle = 75.0 if wall else (15.0 if ar >= 1.4 else 35.0)
    q = 1.0 + gap
    a = math.radians(angle)
    pts = [(-q / 2 * math.cos(a), -q / 2 * math.sin(a)), (q / 2 * math.cos(a), q / 2 * math.sin(a))]
    prefer = (W / 2.0, y * H) if y is not None else None
    return _fit(pts, box, d_max * S, prefer)


def _row_pts(n, lines, gap):
    p = 1.0 + gap
    if lines == 1:
        return [((i - (n - 1) / 2.0) * p, 0.0) for i in range(n)]
    top = (n + 1) // 2
    bot = n - top
    dy = p * math.sqrt(3.0) / 2.0
    pts = [(i * p, 0.0) for i in range(top)]
    pts += [((i + 0.5) * p, dy) for i in range(bot)]      # the lower line sits half a pitch over, in the gaps
    return pts


def _row(n, W, H, S, box, wall, gap=0.08, d_max=0.78, lines=None, prefer_single=1.05):
    """lines None: one line unless two staggered lines give discs prefer_single x larger."""
    best = None
    for k in ([lines] if lines else ([1, 2] if n >= 3 else [1])):
        pts = _row_pts(n, k, gap)
        if wall:
            pts = [(y, x) for x, y in pts]
        D, c = _fit(pts, box, d_max * S)
        if best is None or D > best[0] * (prefer_single if k > 1 else 1.0):
            best = (D, c)
    return best


def _circle(n, W, H, S, box, wall, rc=0.27, d_max=0.30, fill=0.88, y=None, d_one=0.56):
    if n == 1:
        return _fit([(0.0, 0.0)], box, d_one * S, None)
    start = 0.0 if (n % 2 == 1 or n == 2) else 180.0 / n
    D = min(d_max, 2.0 * rc * math.sin(math.pi / n) * fill)
    pts = [(rc / D * math.cos(math.radians(start + 360.0 * i / n)), rc / D * math.sin(math.radians(start + 360.0 * i / n)))
           for i in range(n)]
    prefer = (W / 2.0, (y if y is not None else (0.47 if not wall else 0.52)) * H)
    return _fit(pts, box, D * S, prefer)


def _cluster(n, W, H, S, box, wall, shrink=0.84, d_max=0.64):
    name = {1: "single", 2: "duo", 3: "triangle", 4: "grid"}.get(n, "galaxy")
    x0, y0, x1, y1 = box
    pts = L._arrangement(n, name, x1 - x0, y1 - y0, wall)
    D, c = _fit(pts, box, d_max * S / shrink)
    return D * shrink, c


_FAMILY_FN = {"single": _single, "duo": _duo, "row": _row, "circle": _circle, "cluster": _cluster}


def place(family, n, aspect="1:1", size=1024, caption=None, **opts):
    """Layout for n eyes of a design family on an aspect canvas whose longest side is size px.
    caption: 'full' | 'names' | 'none' (family default when None). opts go to the family (e.g. d=0.66 for single,
    gap=0.02 for a Studio Black duo, shrink=0.80 for Supernova Family, lines=2 for a row)."""
    if family not in _FAMILY_FN:
        raise ValueError(f"family is one of {FAMILIES}, not {family!r}")
    lo, hi = N_RANGE[family]
    if not lo <= n <= hi:
        raise ValueError(f"{family} takes {lo}-{hi} eyes, not {n}")
    W, H = canvas_size(aspect, size)
    S = min(W, H)
    wall = aspect == WALL
    cap = caption_geometry(W, H, caption or DEFAULT_CAPTION[family], wall)
    box = free_box(W, H, cap, wall)
    D, centres = _FAMILY_FN[family](n, W, H, S, box, wall, **opts)
    lay = Layout(family, aspect, n, W, H, S, wall, cap, box)
    lay.slots = [Slot(cx, cy, D / 2.0) for cx, cy in centres]
    return lay


def check(lay, min_d=MIN_D, eps=0.51):
    """Bounds assertion: every disc inside the free box (so inside the canvas, clear of the wallpaper clock and
    above the caption band), no two discs overlapping, no disc below min_d x S, caption lines inside the canvas
    and below every disc. Raises AssertionError naming the first failure."""
    x0, y0, x1, y1 = lay.box
    tag = f"{lay.family} n={lay.n} {lay.aspect} {lay.caption.mode} {lay.W}x{lay.H}"
    assert len(lay.slots) == lay.n, f"{tag}: {len(lay.slots)} slots"
    for i, s in enumerate(lay.slots):
        assert s.r * 2 >= min_d * lay.S - eps, f"{tag}: disc {i} is {2 * s.r / lay.S:.3f} S, below {min_d} S"
        assert s.cx - s.r >= x0 - eps and s.cx + s.r <= x1 + eps, f"{tag}: disc {i} x {s.cx - s.r:.1f}..{s.cx + s.r:.1f} outside {x0:.1f}..{x1:.1f}"
        assert s.cy - s.r >= y0 - eps and s.cy + s.r <= y1 + eps, f"{tag}: disc {i} y {s.cy - s.r:.1f}..{s.cy + s.r:.1f} outside {y0:.1f}..{y1:.1f}"
    for i in range(lay.n):
        for j in range(i + 1, lay.n):
            a, b = lay.slots[i], lay.slots[j]
            dist = math.hypot(a.cx - b.cx, a.cy - b.cy)
            assert dist >= a.r + b.r - eps, f"{tag}: discs {i} and {j} overlap ({dist:.1f} < {a.r + b.r:.1f})"
    cap = lay.caption
    low = max(s.cy + s.r for s in lay.slots)
    for name in ("title", "names", "footer"):
        y, px = getattr(cap, name + "_y"), getattr(cap, name + "_px")
        if y is None or not px:
            continue
        assert y + px / 2.0 <= lay.H + eps, f"{tag}: {name} line runs off the bottom"
        assert y - px / 2.0 >= low - eps, f"{tag}: {name} line overlaps a disc"
    return True


def all_cases():
    """Every (family, n, aspect, caption mode) the bounds test covers."""
    for fam in FAMILIES:
        lo, hi = N_RANGE[fam]
        for n in range(lo, hi + 1):
            for aspect in ASPECTS:
                for mode in ("full", "names", "none"):
                    yield fam, n, aspect, mode
