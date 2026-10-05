# -*- coding: utf-8 -*-
"""The style catalogue: the helpers every other module asks instead of keeping its own list of style ids, names, layouts or
price rules. The data is api/_lib/styles_registry.py (public: ids, names, eye counts, layouts, stages, price class, gate policy,
pick, work_side) and api/_lib/styles_engine.py (how each style is drawn; Python only). Importing this module reads no storage, no network
and no engine: it is cheap and safe in every function (enhance, checkout, the webhook). Only stage_of reads something, and only the one
small object of the owner's overrides, through a 30 s cache (api/_lib/stage_overrides.py; imported on first use).

Stages (styles_registry.py explains them). The literal is the CEILING. The effective stage is the lower of the ceiling and an
override the owner sets in the admin page (stage_of, WP13a: ops/styles/overrides.json). It can only lower; a stage above the ceiling is
ignored. FAILING CLOSED where money is involved: a storage error is never read as "no override". orderable and orderable_ids are strict
(they let the storage error out: the checkout answers 503 storage_busy); stage_of without strict, the tile list, the public catalogue and
every page-facing answer fall back to the ceiling capped at preview, never live. No storage on the deployment at all is no error: there is
nothing to override. set_override_source(None) is "no overrides" (the literal alone); set_override_source(fn) a test's own.
EFFECTIVE_DEFAULT is the stage a style of the v3 engine has until the owner's tick records another: None today (the ceiling alone decides);
the cutover (WP18) raises ceilings to live and sets this to "preview", so that only the owner's recorded tick in the admin page makes a style
orderable. The six legacy ids are never held to it. A style whose engine module is not in the repository (engine_built) is never routed to,
whatever its stage says: a planned or laboratory id can exist before its engine does.

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
from . import layout_names as LN

STYLES = R.STYLES                  # {id: public entry}
ENGINE = X.ENGINE                  # {id: engine entry}
LAYOUT_NAMES = LN.LAYOUT_NAMES     # {layout id: {en, de, lt, hu}}: the words (api/_lib/layout_names.py)
LAYOUT_LANGS = ("en", "de", "lt", "hu")
PLATES_VERSION = R.PLATES_VERSION
DEFAULT_STYLE = R.DEFAULT_STYLE

STAGES = ("planned", "lab", "preview", "live")        # low to high; "retired" stands outside the ranking
STAGE_RANK = {s: i for i, s in enumerate(STAGES)}
PRICE_CLASSES = ("black", "art")
EYE_CLASSES = ("own", "dark_brown", "grey")
MAX_EYES = max(d["eyes"][1] for d in STYLES.values())     # 8

ENGINES_BUILT_EXTRA = set()        # tests only: engine modules to treat as built
EFFECTIVE_DEFAULT = None           # the stage a v3 style has until the owner's tick records another (None: the ceiling decides; WP18 sets "preview")
FALLBACK_STAGE = "preview"         # what a style is capped at when the owner's overrides cannot be read (never live)
_BUILT = {}


def _store_source(style_id, n):
    """The default override source: the owner's overrides in private storage (api/_lib/stage_overrides.py), read through a 30 s cache. Raises
    StorageError when they cannot be read."""
    from . import stage_overrides as SO
    return SO.source(style_id, n)


_override_source = _store_source


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
    """Where the owner's override comes from: fn(style_id, n) returns a stage or None (it may raise: stage_of fails closed). The default is
    the owner's object in private storage (_store_source); None means no overrides at all (the literal alone), which is what the tests of the
    registry use."""
    global _override_source
    _override_source = fn


def stage_with(style_id, n, override, ceil=None):
    """The effective stage the style WOULD have for n eyes under this override (None: none): the lower of the ceiling and the override, where
    no override means EFFECTIVE_DEFAULT for a style of the v3 engine (never for a legacy id). The one place that rule is written: stage_of reads
    it, and the admin action's before and after read it too."""
    c = ceiling(style_id, n) if ceil is None else ceil
    if c is None:
        return None
    if override is None and EFFECTIVE_DEFAULT and not is_legacy(style_id):
        override = EFFECTIVE_DEFAULT
    return effective_stage(c, override)


def stage_of(style_id, n, strict=False):
    """The effective stage for n eyes: the ceiling, lowered by the owner's override. None: not a style of n eyes. When the overrides cannot
    be read the stage is the ceiling capped at FALLBACK_STAGE (preview): a page is still served, nothing is ever LIVE on a guess. strict: the
    storage error is raised instead (for the places where money is involved: orderable, orderable_ids)."""
    c = ceiling(style_id, n)
    if c is None or (_override_source is None and not EFFECTIVE_DEFAULT):
        return c
    try:
        ov = _override_source(style_id, n) if _override_source is not None else None
    except Exception:  # noqa: whatever failed, the owner's switch is unknown: closed
        if strict:
            raise
        return effective_stage(c, FALLBACK_STAGE)
    return stage_with(style_id, n, ov, c)


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
    (an order already paid for a style that was rolled back still renders); only checkout reads them. Which function draws it is
    not decided here: master_compose draws the legacy engine's styles only until the master plan lands, and refuses the rest."""
    return known(style_id) and _built(style_id) and (n is None or in_range(style_id, n))


def orderable(style_id, n, strict=True):
    """Effective stage live for that id and eye count (ordering open and the gate are other questions). Strict by default: it is the question
    the checkout asks, so a storage error that hides the owner's switch is raised (503 storage_busy), never read as live. strict=False reads
    it as the page-facing stage_of does (capped at preview on an error: not orderable)."""
    return stage_of(style_id, n, strict) == "live" and _built(style_id)


def previewable(style_id, n, admin=False):
    """May a preview of it be drawn for n eyes? preview and live for everybody, lab only for the admin; planned and retired
    never. Its engine must be built."""
    s = stage_of(style_id, n)
    return (s in ("preview", "live") or (admin and s == "lab")) and _built(style_id)


def renderable_ids(n):
    """The ids the render path can draw for n eyes, in registry order."""
    return tuple(i for i in STYLES if renderable(i, n))


def orderable_ids(n, strict=True):
    """The ids a customer can order for n eyes (strict as orderable: the checkout's own question)."""
    return tuple(i for i in STYLES if orderable(i, n, strict))


def previewable_ids(n, admin=False):
    return tuple(i for i in STYLES if previewable(i, n, admin))


def orderable_max_eyes():
    """The largest eye count some style is orderable for (0 when nothing is): the landing and the buy card print it (a page-facing number: not strict)."""
    return max((n for n in range(1, MAX_EYES + 1) if orderable_ids(n, strict=False)), default=0)


# ----------------------------------------------------------------------------- layouts
def layouts_for(style_id, n):
    """The layouts n eyes can take in this style, default first (empty: not a style of n eyes)."""
    if not in_range(style_id, n):
        return ()
    return tuple(STYLES[style_id]["layouts"][str(n)])


def default_layout(style_id, n):
    lay = layouts_for(style_id, n)
    return lay[0] if lay else None


def layout_ids():
    """Every layout id that has a word (the vocabulary: the ids of the registry's styles, legacy and v3), in the file's order."""
    return tuple(LAYOUT_NAMES)


def layout_name(lang, layout_id, default=""):
    """The word for a layout in a language, as the e-mails and the order page print it ("Side by side", "Nebeneinander", "Greta",
    "Egymás mellett"). lang is en, de, lt or hu (any other reads English); `default` is returned for an id with no word, which is
    "" unless the caller wants the raw id: an e-mail prints no layout row for an unknown layout, as it always did."""
    row = LAYOUT_NAMES.get(layout_id) if isinstance(layout_id, str) else None
    if not row:
        return default
    return row.get(lang if lang in LAYOUT_LANGS else "en", default)


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
    an eye without a sealed gate value), bar_pupil (the collision family refuses a bar pupil in EVERY design, Infinity, Kiss, the
    Trio, the Family and the Chain: its engine raises NotOffered for any set that holds a horizontal bar, brief 3.1 and D17; the
    first version of this check named the infinity designs only, so Kiss, Family and Chain showed a tile that could not be drawn),
    or None. Reads the profile fields of the engine plan: gate{lid|fill: {ok}}, pupil{cls}. No profiles at all: no information,
    nothing is held back."""
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
        if e["engine"].get("module") == "collision" and (p.get("pupil") or {}).get("cls") == "bar":
            return "bar_pupil"
    return None


def looks_for(style_id, n, admin=False):
    """{look: stage} of the looks a customer may choose inside a style for n eyes (the Universe chips): the style's own looks at their stage
    (never above the stage of the style itself), only preview and live ones, lab ones too for the admin. {} for a style with no looks."""
    e = engine_for(style_id, n)
    st = stage_of(style_id, n)
    out = {}
    for look, stage in ((e or {}).get("looks") or {}).items():
        eff = effective_stage(st, stage)
        if eff in ("preview", "live") or (admin and eff == "lab"):
            out[look] = eff
    return out


LOOK_NAMES = {"echo": "Echo", "vortex": "Vortex", "deepfield": "Deep Field", "starfield": "Starfield"}      # the proper names of the Universe looks (English in every language)


def look_name(look):
    """The proper name of a look ("Vortex"); an unknown code is returned as it came."""
    return LOOK_NAMES.get(look, look) if isinstance(look, str) else ""


def default_look(style_id, n):
    """The look a style of n eyes draws when the customer chooses none (its engine design when that is one of its looks, else its first look), or None for
    a style with no looks."""
    e = engine_for(style_id, n)
    looks = (e or {}).get("looks") or {}
    if not looks:
        return None
    return e["design"] if e["design"] in looks else next(iter(looks))


def look_of(style_id, n, opts=None):
    """The look an order of this style draws: the one in its (applied) options, else the style's default; None for a style with no looks."""
    d = default_look(style_id, n)
    look = (opts or {}).get("look") if isinstance(opts, dict) else None
    return look if d is not None and look in ((engine_for(style_id, n) or {}).get("looks") or {}) else d


def look_orderable(style_id, n, opts=None):
    """May the look an order draws be bought now: a style with no looks always, else the look must be live (looks_for: never above the stage of
    the style itself, so a storage error that capped the style at preview caps its looks too)."""
    look = look_of(style_id, n, opts)
    return look is None or looks_for(style_id, n).get(look) == "live"


def applied_opts(style_id, n, opts):
    """The options of a request that APPLY to this style for n eyes, in the form the seed key and the plan read them (swap for two eyes, rotate modulo n
    for three or more, a look the style has; every other key is left out): the very rule api/compose.py _tile_opts follows for a preview, so that a
    checkout and a preview of the same choice make the same plan (the page's plan8 is compared with the server's at checkout; a test holds the two
    functions equal). Pure: it reads the options and the engine entry, never a stage."""
    opts = opts if isinstance(opts, dict) else {}
    out = {}
    if "swap" in opts and n == 2:
        out["swap"] = opts["swap"]
    if "rotate" in opts and n >= 3:
        out["rotate"] = opts["rotate"] % n
    if "look" in opts and opts["look"] in ((engine_for(style_id, n) or {}).get("looks") or {}):
        out["look"] = opts["look"]
    return out


def style_label(style_id, n, opts=None):
    """The style as an order prints it (the Stripe line item, the confirmation e-mail): its brand name, and for a style with looks the look, because the
    look is a different product ("Universe, Vortex"); English in every language, as the brand names are."""
    d = STYLES.get(style_id) if isinstance(style_id, str) else None
    if not d:
        return str(style_id)
    look = look_of(style_id, n, opts) if not d["legacy"] and in_range(style_id, n) else None
    return d["name"] + (f", {look_name(look)}" if look else "")


def tile_row(style_id, n, profiles=None, admin=False):
    """The tile of one style for n eyes: {id, name, slug, group, legacy, stage, available, why, layouts, eyes, price_class, looks, gate, rule}. available
    is False with a why when the eyes cannot take the style (_problem); looks is {look: stage} (looks_for); eyes is n, the count the tile is for; gate is
    the style's gate policy (none, advisory or hard) and rule the rule set it reads (lid or fill): the picker (src/try/picker.ts, WP11) needs them to say
    WHICH eye to retake for a tile that is held back, and whether a failing eye only warns (advisory) or blocks (hard); the engine's own entry is Python
    only, so the page cannot read the rule anywhere else."""
    d = STYLES[style_id]
    why = _problem(style_id, profiles)
    return {"id": style_id, "name": d["name"], "slug": d["slug"], "group": d["group"], "legacy": d["legacy"],
            "stage": stage_of(style_id, n), "available": why is None, "why": why, "layouts": list(layouts_for(style_id, n)),
            "eyes": n, "price_class": d["price_class"], "looks": looks_for(style_id, n, admin),
            "gate": d["gate"], "rule": ENGINE[style_id]["gate_rules"]}


def tiles_for(n, profiles=None, admin=False):
    """The tiles of n eyes, in tile order (tile_row each): the styles with a tile slot (tile_order above 0) a customer may see, the laboratory ones
    too for the admin. The picker renders what this says and owns no style list."""
    rows = [tile_row(i, n, profiles, admin) for i, d in STYLES.items() if d["tile_order"] > 0 and previewable(i, n, admin)]
    rows.sort(key=lambda r: (r["legacy"], STYLES[r["id"]]["tile_order"]))
    return rows


def why_unavailable(style_id, n, profiles=None, admin=False):
    """Why a customer cannot have a preview of this style for these eyes, as a code, or None when they can: unknown (not an id of the registry),
    eyes (the style does not take n eyes), stage (planned, retired, a laboratory style for a customer, or its engine is not in the repository),
    or what the eyes themselves say (_problem: gate, reseal, bar_pupil). The compose endpoint refuses on the first three (400 for unknown, 422
    style_unavailable for the others); the last three it reports on the tile (available false, why)."""
    if not known(style_id):
        return "unknown"
    if not in_range(style_id, n):
        return "eyes"
    if not previewable(style_id, n, admin):
        return "stage"
    return _problem(style_id, profiles)


def pick_reason(style_id, cls):
    """The key of the reason line of the recommended tile (the copy files hold the words by key), or None: the line is the style's answer to the
    set's colour class and only when the style's own pick table lists that class. A pick that came from the fallback (the default style, the
    first buyable tile) has no reason line: 'Silver light for grey eyes' is never said of a style that was not chosen for grey eyes."""
    d = STYLES.get(style_id) if isinstance(style_id, str) else None
    if not d or cls not in d["pick"]:
        return None
    return d["reason"].get(cls)


def tile_list(n, profiles=None, admin=False):
    """What the picker is told for n eyes (one call, no pixels): {tiles, pick, reason}. tiles is tiles_for() with the recommended tile moved to
    position 1 and every tile carrying pick (true on that one only); pick is its id (or None when nothing can be bought) and reason the key of
    its reason line (or None). The recommended tile is the pick_for() answer: always a tile the customer can buy now (live and available)."""
    rows = tiles_for(n, profiles, admin)
    pid = pick_for(n, profiles)
    for r in rows:
        r["pick"] = r["id"] == pid
    rows.sort(key=lambda r: not r["pick"])                 # stable: the pick first, the rest in tile order
    return {"tiles": rows, "pick": pid, "reason": pick_reason(pid, set_class(profiles))}


def pick_for(n, profiles=None, skip=()):
    """The recommended tile: among the tiles the customer can BUY now (live and available), the first whose pick lists the set's
    colour class, else DEFAULT_STYLE if it is one of them, else the first. None when nothing can be bought. The table is
    price blind: it reads the class and the stage, never the price. skip: ids the engine itself refused when it came to draw them (a
    refusal the profile did not predict, api/compose.py): they are no longer buyable for these eyes."""
    buyable = [t for t in tiles_for(n, profiles) if t["stage"] == "live" and t["available"] and t["id"] not in skip]
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
