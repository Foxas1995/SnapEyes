# -*- coding: utf-8 -*-
"""The style catalogue: the helpers every other module asks instead of keeping its own list of style ids, names, layouts or
price rules. The data is api/_lib/styles_registry.py (public: ids, names, eye counts, layouts, stages, price class, gate policy,
pick, work_side) and api/_lib/styles_engine.py (how each style is drawn; Python only). Nothing here reads storage, the network
or an engine: importing this module is cheap and safe in every function (enhance, checkout, the webhook).

Stages (styles_registry.py explains them). The literal is the CEILING. The effective stage is the lower of the ceiling and an
override the owner sets in the admin page (stage_of); the override read path lands with the admin work package and plugs in through
set_override_source, so until then the effective stage is the ceiling. A style whose engine module is not in the repository
(engine_built) is never routed to, whatever its stage says: a planned or laboratory id can exist before its engine does.

The price class (black or art) is ONE predicate, is_black(style): pay.price_cents, abtest.ladder_price, src/shared/markets.ts
priceMinor, scripts/check_prices.mjs priceRule and scripts/check_experiments.mjs ladderRule all read it and the build compares them.
An unknown id is of the art class, as the old comparison with one id was.

Module rule: every module of the v3 work starts with the __future__ import below (Vercel's default Python is 3.12)."""
from __future__ import annotations

import hashlib
import importlib.util
import json

from . import styles_registry as R
from . import styles_engine as X

STYLES = R.STYLES                  # {id: public entry}
ENGINE = X.ENGINE                  # {id: engine entry}
PLATES_VERSION = R.PLATES_VERSION
DEFAULT_STYLE = R.DEFAULT_STYLE

STAGES = ("planned", "lab", "preview", "live")        # low to high; "retired" stands outside the ranking
STAGE_RANK = {s: i for i, s in enumerate(STAGES)}
PRICE_CLASSES = ("black", "art")
EYE_CLASSES = ("own", "dark_brown", "grey")
MAX_EYES = max(d["eyes"][1] for d in STYLES.values())     # 8

ENGINES_BUILT_EXTRA = set()        # tests only: engine modules to treat as built
_BUILT = {}
_override_source = None


# ----------------------------------------------------------------------------- ids, ranges
def _range(key):
    """"3" -> (3, 3), "4-8" -> (4, 8)."""
    a, _, b = str(key).partition("-")
    return int(a), int(b or a)


def _by_eyes(mapping, n, default=None):
    """The value of a range-keyed map ({"3": x, "4-8": y}) for n eyes."""
    for k, v in mapping.items():
        lo, hi = _range(k)
        if lo <= n <= hi:
            return v
    return default


def _num(n):
    return n if isinstance(n, int) and not isinstance(n, bool) else None


def ids():
    return tuple(STYLES)


def known(style_id):
    """Does the registry have this id at all (any stage)? Reading an old order accepts every known id."""
    return isinstance(style_id, str) and style_id in STYLES


def legacy_ids():
    """The six engine ids of today, in the order api/_lib/iris.py STYLES has always had."""
    return tuple(i for i, d in STYLES.items() if d["legacy"] == 1)


def is_legacy(style_id):
    return known(style_id) and STYLES[style_id]["legacy"] == 1


def names():
    """{id: brand name} of every id (a fresh dict)."""
    return {i: d["name"] for i, d in STYLES.items()}


def name_of(style_id):
    """The brand name (English in every language); an unknown id is returned as it came."""
    return STYLES[style_id]["name"] if known(style_id) else style_id


def slug_of(style_id):
    return STYLES[style_id]["slug"] if known(style_id) else None


def eyes_range(style_id):
    d = STYLES.get(style_id) if isinstance(style_id, str) else None
    return (d["eyes"][0], d["eyes"][1]) if d else None


def in_range(style_id, n):
    r = eyes_range(style_id)
    n = _num(n)
    return bool(r) and n is not None and r[0] <= n <= r[1]


# ----------------------------------------------------------------------------- stages
def ceiling(style_id, n):
    """The ceiling stage of the style for n eyes (the literal), or None when the id is unknown or takes no n eyes."""
    if not in_range(style_id, n):
        return None
    d = STYLES[style_id]
    return _by_eyes(d["stage_by_eyes"], n, d["stage"])


def effective_stage(ceil, override):
    """min(ceiling, override). The override can only lower: a stage above the ceiling is ignored, retired is final."""
    if ceil is None or ceil == "retired" or override not in STAGE_RANK:
        return ceil
    return ceil if STAGE_RANK[ceil] <= STAGE_RANK[override] else override


def set_override_source(fn):
    """The admin override (private storage, WP13a) plugs in here: fn(style_id, n) returns a stage or None. None clears it."""
    global _override_source
    _override_source = fn


def stage_of(style_id, n):
    """The effective stage for n eyes: the ceiling, lowered by the owner's override. None: not a style of n eyes."""
    c = ceiling(style_id, n)
    if c is None or _override_source is None:
        return c
    return effective_stage(c, _override_source(style_id, n))


def engine_built(module):
    """Is the engine module in the repository? legacy always; the v3 families once api/_lib/styles/<module> exists."""
    if module == "legacy" or module in ENGINES_BUILT_EXTRA:
        return True
    if module not in _BUILT:
        try:
            _BUILT[module] = importlib.util.find_spec(f"{__package__}.styles.{module}") is not None
        except (ImportError, ValueError):
            _BUILT[module] = False
    return _BUILT[module]


def _built(style_id):
    e = ENGINE.get(style_id)
    return bool(e) and bool(e["engine"]) and engine_built(e["engine"].get("module"))


def renderable(style_id, n=None):
    """Can the render path draw it? Known, its engine built, the eye count inside its range. The render path ignores stages
    (an order already paid for a style that was rolled back still renders); only checkout reads them."""
    return known(style_id) and _built(style_id) and (n is None or in_range(style_id, n))


def orderable(style_id, n):
    """Effective stage live for that id and eye count (ordering open and the gate are other questions)."""
    return stage_of(style_id, n) == "live" and _built(style_id)


def previewable(style_id, n, admin=False):
    """May a preview of it be drawn for n eyes? preview and live for everybody, lab only for the admin; planned and retired
    never. Its engine must be built."""
    s = stage_of(style_id, n)
    return (s in ("preview", "live") or (admin and s == "lab")) and _built(style_id)


def renderable_ids(n):
    """The ids the render path can draw for n eyes, in registry order."""
    return tuple(i for i in STYLES if renderable(i, n))


def orderable_ids(n):
    return tuple(i for i in STYLES if orderable(i, n))


def previewable_ids(n, admin=False):
    return tuple(i for i in STYLES if previewable(i, n, admin))


def orderable_max_eyes():
    """The largest eye count some style is orderable for (0 when nothing is): the landing and the buy card print it."""
    return max((n for n in range(1, MAX_EYES + 1) if orderable_ids(n)), default=0)


# ----------------------------------------------------------------------------- layouts
def layouts_for(style_id, n):
    """The layouts n eyes can take in this style, default first (empty: not a style of n eyes)."""
    if not in_range(style_id, n):
        return ()
    return tuple(STYLES[style_id]["layouts"][str(n)])


def default_layout(style_id, n):
    lay = layouts_for(style_id, n)
    return lay[0] if lay else None


def legacy_layouts_table():
    """{n: (layout, ...)} of the six legacy styles, which all take the same layouts (the build checks it; this refuses to guess)."""
    tables = {json.dumps(STYLES[i]["layouts"], sort_keys=True) for i in legacy_ids()}
    if len(tables) != 1:
        raise RuntimeError("the legacy styles of api/_lib/styles_registry.py do not share one layout table")
    first = STYLES[legacy_ids()[0]]["layouts"]
    return {int(k): tuple(v) for k, v in first.items()}


# ----------------------------------------------------------------------------- price class
def price_class(style_id):
    """black or art. An unknown id is art (as the comparison with one id was)."""
    return STYLES[style_id]["price_class"] if known(style_id) else "art"


def is_black(style_id):
    return price_class(style_id) == "black"


def class_style(cls):
    """A style a customer can buy in a price class, for the places that name one example (loss warnings, the admin's example
    totals): the first live style of the class in registry order, else the first style of it that has an engine entry."""
    pool = [i for i, d in STYLES.items() if d["price_class"] == cls and 1 >= d["eyes"][0]]
    live = [i for i in pool if ceiling(i, 1) == "live"]
    for group in (live, [i for i in pool if ceiling(i, 1) not in (None, "planned", "retired")], pool):
        if group:
            return group[0]
    raise KeyError(cls)


# ----------------------------------------------------------------------------- engine, gate, caps
def gate_policy(style_id):
    return STYLES[style_id]["gate"] if known(style_id) else None


def work_side(style_id, n):
    """The largest working copy of an eye for n eyes in this style, or None (no cap from the registry)."""
    if not in_range(style_id, n):
        return None
    return _by_eyes(STYLES[style_id]["work_side"], n, None)


def engine_for(style_id, n):
    """How n eyes of this style are drawn: {module, design, looks, clean, gate_rules, plates, atlas, canvases, steps, fill_side,
    work_side}, or None for an unknown id, a planned one (no engine) or an eye count it does not take."""
    e = ENGINE.get(style_id) if isinstance(style_id, str) else None
    if not e or not e["engine"] or not in_range(style_id, n):
        return None
    out = json.loads(json.dumps(e["engine"]))
    out["design"] = _by_eyes(e["design_by_eyes"], n, out["design"])
    out.setdefault("looks", {})
    out.setdefault("clean", 0)
    out.update(gate_rules=e["gate_rules"], plates=list(e["plates"]), atlas=list(e["atlas"]), canvases=list(e["canvases"]),
               steps=list(_by_eyes(e["steps"], n, ["art"])), fill_side=e["fill_side"], work_side=work_side(style_id, n))
    return out


# ----------------------------------------------------------------------------- tiles and the recommended tile
def set_class(profiles):
    """The colour class of a set of eyes for the recommended tile: grey if any eye is grey, else dark_brown if any is, else own.
    profiles: the eye profiles (their "cls"), or None before any exists."""
    cls = [p.get("cls") for p in profiles if isinstance(p, dict)] if isinstance(profiles, (list, tuple)) else []
    for c in ("grey", "dark_brown"):
        if c in cls:
            return c
    return "own"


def _problem(style_id, profiles):
    """Why this style cannot be used for these eyes, as the picker's code: gate (a hard rule failed), reseal (a hard style and
    an eye without a sealed gate value), bar_pupil (the infinity designs refuse a bar pupil), or None. Reads the profile fields of
    the engine plan: gate{lid|fill: {ok}}, pupil{cls}. No profiles at all: no information, nothing is held back."""
    if not isinstance(profiles, (list, tuple)) or not profiles:
        return None
    e = ENGINE[style_id]
    rule = e["gate_rules"]
    for p in profiles:
        p = p if isinstance(p, dict) else {}
        if STYLES[style_id]["gate"] == "hard":
            g = p.get("gate")
            if not isinstance(g, dict) or not isinstance(g.get(rule), dict):
                return "reseal"
            if g[rule].get("ok") is not True:
                return "gate"
        if e["engine"].get("module") == "collision" and e["engine"].get("design") == "infinity":
            if (p.get("pupil") or {}).get("cls") == "bar":
                return "bar_pupil"
    return None


def tiles_for(n, profiles=None, admin=False):
    """The tiles of n eyes, in tile order: [{id, name, slug, group, legacy, stage, available, why, layouts}]. The picker renders
    what this says and owns no style list. available is False with a why when the eyes cannot take the style (_problem)."""
    rows = []
    for i, d in STYLES.items():
        if d["tile_order"] <= 0 or not previewable(i, n, admin):
            continue
        why = _problem(i, profiles)
        rows.append({"id": i, "name": d["name"], "slug": d["slug"], "group": d["group"], "legacy": d["legacy"],
                     "stage": stage_of(i, n), "available": why is None, "why": why, "layouts": list(layouts_for(i, n))})
    rows.sort(key=lambda r: (r["legacy"], STYLES[r["id"]]["tile_order"]))
    return rows


def pick_for(n, profiles=None):
    """The recommended tile: among the tiles the customer can BUY now (live and available), the first whose pick lists the set's
    colour class, else DEFAULT_STYLE if it is one of them, else the first. None when nothing can be bought. The table is
    price blind: it reads the class and the stage, never the price."""
    buyable = [t for t in tiles_for(n, profiles) if t["stage"] == "live" and t["available"]]
    cls = set_class(profiles)
    for t in buyable:
        if cls in STYLES[t["id"]]["pick"]:
            return t["id"]
    if any(t["id"] == DEFAULT_STYLE for t in buyable):
        return DEFAULT_STYLE
    return buyable[0]["id"] if buyable else None


def public_catalogue():
    """What a customer's page may be told: only ids at preview or live (held and planned ids are never listed), each with the
    stage per eye count it has at those stages."""
    out = []
    for i, d in STYLES.items():
        stages = {}
        for n in range(d["eyes"][0], d["eyes"][1] + 1):
            s = stage_of(i, n)
            if s in ("preview", "live") and _built(i):
                stages[str(n)] = s
        if stages:
            out.append({"id": i, "name": d["name"], "slug": d["slug"], "group": d["group"], "eyes": list(d["eyes"]),
                        "stages": stages})
    return out


# ----------------------------------------------------------------------------- the registry hash
def canonical():
    """The text the registry hash is made of: both literals and the constants, JSON with sorted keys and no spaces (ASCII only,
    whole numbers only, so scripts/styles_source.mjs makes the very same text)."""
    return json.dumps({"schema": R.STYLES_SCHEMA, "pv": R.PLATES_VERSION, "default": R.DEFAULT_STYLE, "styles": R.STYLES,
                       "engine": X.ENGINE}, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def registry_hash():
    """The first 12 hex digits of the sha256 of canonical(): printed by the build, recorded in every plan."""
    return hashlib.sha256(canonical().encode("ascii")).hexdigest()[:12]
