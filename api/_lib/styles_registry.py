# -*- coding: utf-8 -*-
"""The styles snapeyes.com knows: THE ONE PLACE that says which style ids exist, what they are called, how many eyes each takes,
which layouts, which price class, which stage and which gate policy. Nothing else holds a list of style ids, a style name or a
layout table (api/_lib/catalogue.py reads this file for the server; src/shared/styles.ts reads it for every page).

Read by the server (api/_lib/catalogue.py: validation, names, price class, stages, layouts, tiles, the recommended tile) AND by
the site's build (src/shared/styles.ts imports this very file as text with Vite's ?raw and parses the STYLES literal below as
JSON, exactly as src/shared/markets.ts does with api/_lib/markets.py). The build refuses to finish when the literal is not plain
JSON, when a rule below is broken, or when another file holds its own copy of a style id, a style name key or a price rule
(scripts/check_styles.mjs, run by vite.config.ts on every build; `npm run check:styles` runs it alone). The build prints the
registry hash (12 hex digits of the sha256 of both literals in canonical form: this file's and api/_lib/styles_engine.py's).

THIS FILE SHIPS IN THE PUBLIC JAVASCRIPT BUNDLE (the page imports it as text). It therefore holds only what a page may know:
ids, names, slugs, eye counts, layouts, stages, price class, gate policy, pick and work_side. Everything about how an engine
draws a style (module, design, looks, plates, atlases, gate rule set, canvases, fill size, step hints) is in
api/_lib/styles_engine.py, keyed by the same ids and read by Python only. Held and planned ids and names are readable in this
file; "hidden from customers" is a statement about the interface, not about the source.

Why a .py file with a JSON literal and not a .json file: the build already parses api/_lib/markets.py the same way, and a .py
file is not in the way of vercel.json excludeFiles (which names *.json).

Rules for the literal (JSON inside Python): double quotes only, no trailing commas, no comments inside it, no true/false/null
(use 1 and 0, and {} or [] for nothing), ASCII only, whole numbers only, and nothing after it in this file. The constants above it
are single lines of the form NAME = value.
  STYLES_SCHEMA   1: the shape of an entry (this list of fields)
  PLATES_VERSION  the version of the plate library a render may pick from (a plate added later never changes an older pick)
  DEFAULT_STYLE   the style a preview falls back to when a request names none the server knows
Fields of an entry (all are required):
  id           the key. A v3 id is group.name (solo.powder, duo.kiss_collision, grp.collision); the six styles of today keep their
               bare ids (celestial_gold, studio_black, ...), carry legacy 1, and leave at the v3 cutover (stage retired). Legacy ids
               are read by old orders and stay separate ids: no aliasing of engines
  group        solo | duo | grp | pet  (the tab of the picker: one eye, two eyes, three or more eyes; pet only reserves a group)
  slug         file name part of tile images and download names (letters, digits and hyphens). Unique, except that a legacy id and a
               v3 id of the same name may share one (the cutover then shows the new picture under the same file name)
  name         the proper name printed in Stripe line items, e-mails, the terms and the owner's panel; English in every language
  legacy       1 for the six engine ids of today (api/_lib/iris.py), else 0
  eyes         [min, max] eyes the style accepts, inside 1 to 8
  layouts      per eye count of that range, the layout ids that count can take, the default first
  stage        the CEILING of the style: planned (id reserved, no engine) | lab (admin laboratory only, hidden from customers) |
               preview (/try may draw it, the buy card says soon, checkout refuses) | live (orderable) | retired (renders for orders
               already made and the admin recompose, never offered). The effective stage is the lower of this and the owner's
               override in the admin page (catalogue.stage_of); the literal is raised only in a reviewed change
  stage_by_eyes  {"3": "live", "4-8": "preview"}: the ceiling for an eye range where it differs from stage (missing: stage)
  price_class  black | art: what price_cents and priceMinor read for ONE eye (two or more eyes are style independent). One predicate,
               catalogue.is_black / styles.ts isBlack, replaces every comparison with a style id
  gate         none | advisory | hard: what happens when the restoration gate fails for an eye (advisory: a note, the buy button
               stays; hard: the style is withheld for that eye set)
  pick         eye classes (own | dark_brown | grey) for which this style is the recommended tile
  reason       for each class in pick, the key of the line printed under the recommended tile (copy files)
  tile_order   position in the tile list of its group (1 first; 0 not in the list). Unique per group, among legacy ids and among v3 ids
  work_side    {"1": 4096, "3": 4096, "4-8": 2048}: the largest working copy of an eye the engine may use, per eye range (the render
               memory guard reads it); {} for the legacy engine, which has its own limits
  accent       the picker's swatch colour [r, g, b] of a legacy style, [] for none (studio_black is bare) and for every v3 id
"""
STYLES_SCHEMA = 1
PLATES_VERSION = 1
DEFAULT_STYLE = "celestial_gold"
STYLES = {
    "solo.clean": {
        "group": "solo",
        "slug": "clean-iris",
        "name": "Clean Iris",
        "legacy": 0,
        "eyes": [1, 1],
        "layouts": {"1": ["single"]},
        "stage": "lab",
        "stage_by_eyes": {},
        "price_class": "black",
        "gate": "advisory",
        "pick": [],
        "reason": {},
        "tile_order": 6,
        "work_side": {"1": 4096},
        "accent": []
    },
    "solo.powder": {
        "group": "solo",
        "slug": "powder-burst",
        "name": "Powder Burst",
        "legacy": 0,
        "eyes": [1, 1],
        "layouts": {"1": ["single"]},
        "stage": "lab",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "advisory",
        "pick": ["own"],
        "reason": {"own": "reason.solo_powder.own"},
        "tile_order": 1,
        "work_side": {"1": 4096},
        "accent": []
    },
    "solo.universe": {
        "group": "solo",
        "slug": "universe",
        "name": "Universe",
        "legacy": 0,
        "eyes": [1, 1],
        "layouts": {"1": ["single"]},
        "stage": "lab",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "hard",
        "pick": [],
        "reason": {},
        "tile_order": 2,
        "work_side": {"1": 4096},
        "accent": []
    },
    "solo.splash": {
        "group": "solo",
        "slug": "splash",
        "name": "Splash",
        "legacy": 0,
        "eyes": [1, 1],
        "layouts": {"1": ["single"]},
        "stage": "lab",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "advisory",
        "pick": [],
        "reason": {},
        "tile_order": 3,
        "work_side": {"1": 4096},
        "accent": []
    },
    "solo.elements": {
        "group": "solo",
        "slug": "elements",
        "name": "Elements",
        "legacy": 0,
        "eyes": [1, 1],
        "layouts": {"1": ["single"]},
        "stage": "lab",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "advisory",
        "pick": [],
        "reason": {},
        "tile_order": 0,
        "work_side": {"1": 4096},
        "accent": []
    },
    "solo.radiance": {
        "group": "solo",
        "slug": "radiance",
        "name": "Radiance",
        "legacy": 0,
        "eyes": [1, 1],
        "layouts": {"1": ["single"]},
        "stage": "lab",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "advisory",
        "pick": ["grey"],
        "reason": {"grey": "reason.solo_radiance.grey"},
        "tile_order": 5,
        "work_side": {"1": 4096},
        "accent": []
    },
    "solo.gold": {
        "group": "solo",
        "slug": "celestial-gold",
        "name": "Celestial Gold",
        "legacy": 0,
        "eyes": [1, 1],
        "layouts": {"1": ["single"]},
        "stage": "lab",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "advisory",
        "pick": ["dark_brown"],
        "reason": {"dark_brown": "reason.solo_gold.dark_brown"},
        "tile_order": 4,
        "work_side": {"1": 4096},
        "accent": []
    },
    "duo.collision_infinity": {
        "group": "duo",
        "slug": "collision-infinity",
        "name": "Collision Infinity",
        "legacy": 0,
        "eyes": [2, 2],
        "layouts": {"2": ["pair"]},
        "stage": "lab",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "hard",
        "pick": ["own"],
        "reason": {"own": "reason.duo_collision_infinity.own"},
        "tile_order": 2,
        "work_side": {"2": 2048},
        "accent": []
    },
    "duo.clean": {
        "group": "duo",
        "slug": "clean-infinity",
        "name": "Clean Infinity",
        "legacy": 0,
        "eyes": [2, 2],
        "layouts": {"2": ["pair"]},
        "stage": "lab",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "hard",
        "pick": [],
        "reason": {},
        "tile_order": 3,
        "work_side": {"2": 2048},
        "accent": []
    },
    "duo.kiss_collision": {
        "group": "duo",
        "slug": "kiss-collision",
        "name": "Kiss Collision",
        "legacy": 0,
        "eyes": [2, 2],
        "layouts": {"2": ["pair"]},
        "stage": "lab",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "hard",
        "pick": ["own", "dark_brown", "grey"],
        "reason": {"own": "reason.duo_kiss_collision.own", "dark_brown": "reason.duo_kiss_collision.dark_brown", "grey": "reason.duo_kiss_collision.grey"},
        "tile_order": 1,
        "work_side": {"2": 2048},
        "accent": []
    },
    "duo.universe": {
        "group": "duo",
        "slug": "universe-duo",
        "name": "Universe",
        "legacy": 0,
        "eyes": [2, 2],
        "layouts": {"2": ["pair"]},
        "stage": "lab",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "hard",
        "pick": [],
        "reason": {},
        "tile_order": 0,
        "work_side": {"2": 2048},
        "accent": []
    },
    "duo.reflection": {
        "group": "duo",
        "slug": "reflection",
        "name": "Reflection",
        "legacy": 0,
        "eyes": [2, 2],
        "layouts": {"2": ["pair"]},
        "stage": "planned",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "hard",
        "pick": [],
        "reason": {},
        "tile_order": 0,
        "work_side": {"2": 2048},
        "accent": []
    },
    "duo.radiance": {
        "group": "duo",
        "slug": "radiance-duo",
        "name": "Radiance Duo",
        "legacy": 0,
        "eyes": [2, 2],
        "layouts": {"2": ["pair"]},
        "stage": "planned",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "advisory",
        "pick": [],
        "reason": {},
        "tile_order": 0,
        "work_side": {"2": 2048},
        "accent": []
    },
    "duo.gold": {
        "group": "duo",
        "slug": "celestial-gold-duo",
        "name": "Celestial Gold Duo",
        "legacy": 0,
        "eyes": [2, 2],
        "layouts": {"2": ["pair"]},
        "stage": "planned",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "advisory",
        "pick": [],
        "reason": {},
        "tile_order": 0,
        "work_side": {"2": 2048},
        "accent": []
    },
    "grp.collision": {
        "group": "grp",
        "slug": "family-colours",
        "name": "Family Colours",
        "legacy": 0,
        "eyes": [3, 8],
        "layouts": {"3": ["trio", "diag"], "4": ["zigzag", "cluster", "ring", "brick"], "5": ["brick", "ring", "flower"], "6": ["brick", "ring", "flower"], "7": ["ring", "flower", "brick"], "8": ["ring", "brick", "flower"]},
        "stage": "lab",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "hard",
        "pick": ["own", "dark_brown", "grey"],
        "reason": {"own": "reason.grp_collision.own", "dark_brown": "reason.grp_collision.dark_brown", "grey": "reason.grp_collision.grey"},
        "tile_order": 1,
        "work_side": {"3": 4096, "4-8": 2048},
        "accent": []
    },
    "grp.chain": {
        "group": "grp",
        "slug": "infinity-chain",
        "name": "Infinity Chain",
        "legacy": 0,
        "eyes": [3, 6],
        "layouts": {"3": ["chain"], "4": ["chain"], "5": ["chain"], "6": ["chain"]},
        "stage": "lab",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "hard",
        "pick": [],
        "reason": {},
        "tile_order": 0,
        "work_side": {"3-6": 2048},
        "accent": []
    },
    "grp.universe": {
        "group": "grp",
        "slug": "universe-family",
        "name": "Universe",
        "legacy": 0,
        "eyes": [3, 6],
        "layouts": {"3": ["trio"], "4": ["zigzag"], "5": ["brick", "ring"], "6": ["brick", "ring"]},
        "stage": "lab",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "hard",
        "pick": [],
        "reason": {},
        "tile_order": 0,
        "work_side": {"3-6": 2048},
        "accent": []
    },
    "grp.reflection": {
        "group": "grp",
        "slug": "reflection-family",
        "name": "Reflection",
        "legacy": 0,
        "eyes": [3, 6],
        "layouts": {"3": ["row"], "4": ["row"], "5": ["row"], "6": ["row"]},
        "stage": "planned",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "hard",
        "pick": [],
        "reason": {},
        "tile_order": 0,
        "work_side": {"3-6": 2048},
        "accent": []
    },
    "grp.radiance": {
        "group": "grp",
        "slug": "radiance-family",
        "name": "Radiance",
        "legacy": 0,
        "eyes": [3, 8],
        "layouts": {"3": ["trio"], "4": ["zigzag"], "5": ["brick"], "6": ["brick"], "7": ["ring"], "8": ["ring"]},
        "stage": "planned",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "advisory",
        "pick": [],
        "reason": {},
        "tile_order": 0,
        "work_side": {"3": 4096, "4-8": 2048},
        "accent": []
    },
    "grp.clean": {
        "group": "grp",
        "slug": "clean-family",
        "name": "Clean Family",
        "legacy": 0,
        "eyes": [3, 8],
        "layouts": {"3": ["trio"], "4": ["zigzag"], "5": ["brick"], "6": ["brick"], "7": ["ring"], "8": ["ring"]},
        "stage": "planned",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "hard",
        "pick": [],
        "reason": {},
        "tile_order": 2,
        "work_side": {"3": 4096, "4-8": 2048},
        "accent": []
    },
    "pet.solo": {
        "group": "pet",
        "slug": "pet-solo",
        "name": "Pet Solo",
        "legacy": 0,
        "eyes": [1, 1],
        "layouts": {"1": ["single"]},
        "stage": "planned",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "hard",
        "pick": [],
        "reason": {},
        "tile_order": 0,
        "work_side": {"1": 4096},
        "accent": []
    },
    "pet.clean": {
        "group": "pet",
        "slug": "pet-clean-iris",
        "name": "Clean Iris",
        "legacy": 0,
        "eyes": [1, 1],
        "layouts": {"1": ["single"]},
        "stage": "planned",
        "stage_by_eyes": {},
        "price_class": "black",
        "gate": "hard",
        "pick": [],
        "reason": {},
        "tile_order": 0,
        "work_side": {"1": 4096},
        "accent": []
    },
    "celestial_gold": {
        "group": "solo",
        "slug": "celestial-gold",
        "name": "Celestial Gold",
        "legacy": 1,
        "eyes": [1, 8],
        "layouts": {"1": ["single"], "2": ["duo", "fusion"], "3": ["triangle", "row"], "4": ["grid", "row"], "5": ["galaxy"], "6": ["galaxy"], "7": ["galaxy"], "8": ["galaxy"]},
        "stage": "live",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "none",
        "pick": [],
        "reason": {},
        "tile_order": 2,
        "work_side": {},
        "accent": [245, 197, 66]
    },
    "deep_nebula": {
        "group": "solo",
        "slug": "deep-nebula",
        "name": "Deep Nebula",
        "legacy": 1,
        "eyes": [1, 8],
        "layouts": {"1": ["single"], "2": ["duo", "fusion"], "3": ["triangle", "row"], "4": ["grid", "row"], "5": ["galaxy"], "6": ["galaxy"], "7": ["galaxy"], "8": ["galaxy"]},
        "stage": "live",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "none",
        "pick": [],
        "reason": {},
        "tile_order": 3,
        "work_side": {},
        "accent": [129, 140, 248]
    },
    "emerald_aurora": {
        "group": "solo",
        "slug": "emerald-aurora",
        "name": "Emerald Aurora",
        "legacy": 1,
        "eyes": [1, 8],
        "layouts": {"1": ["single"], "2": ["duo", "fusion"], "3": ["triangle", "row"], "4": ["grid", "row"], "5": ["galaxy"], "6": ["galaxy"], "7": ["galaxy"], "8": ["galaxy"]},
        "stage": "live",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "none",
        "pick": [],
        "reason": {},
        "tile_order": 4,
        "work_side": {},
        "accent": [52, 211, 153]
    },
    "obsidian_smoke": {
        "group": "solo",
        "slug": "obsidian-smoke",
        "name": "Obsidian Smoke",
        "legacy": 1,
        "eyes": [1, 8],
        "layouts": {"1": ["single"], "2": ["duo", "fusion"], "3": ["triangle", "row"], "4": ["grid", "row"], "5": ["galaxy"], "6": ["galaxy"], "7": ["galaxy"], "8": ["galaxy"]},
        "stage": "live",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "none",
        "pick": [],
        "reason": {},
        "tile_order": 5,
        "work_side": {},
        "accent": [203, 213, 225]
    },
    "supernova": {
        "group": "solo",
        "slug": "supernova",
        "name": "Supernova",
        "legacy": 1,
        "eyes": [1, 8],
        "layouts": {"1": ["single"], "2": ["duo", "fusion"], "3": ["triangle", "row"], "4": ["grid", "row"], "5": ["galaxy"], "6": ["galaxy"], "7": ["galaxy"], "8": ["galaxy"]},
        "stage": "live",
        "stage_by_eyes": {},
        "price_class": "art",
        "gate": "none",
        "pick": [],
        "reason": {},
        "tile_order": 6,
        "work_side": {},
        "accent": [251, 146, 60]
    },
    "studio_black": {
        "group": "solo",
        "slug": "studio-black",
        "name": "Studio Black",
        "legacy": 1,
        "eyes": [1, 8],
        "layouts": {"1": ["single"], "2": ["duo", "fusion"], "3": ["triangle", "row"], "4": ["grid", "row"], "5": ["galaxy"], "6": ["galaxy"], "7": ["galaxy"], "8": ["galaxy"]},
        "stage": "live",
        "stage_by_eyes": {},
        "price_class": "black",
        "gate": "none",
        "pick": [],
        "reason": {},
        "tile_order": 1,
        "work_side": {},
        "accent": []
    }
}
