# -*- coding: utf-8 -*-
"""How each style of api/_lib/styles_registry.py is drawn: read by Python only (api/_lib/catalogue.py engine_for), never imported
by the site, so none of it reaches the public JavaScript bundle. Keyed by the very ids of the public literal (the build checks that
the two have exactly the same ids). Same rules for the literal as the public file: JSON inside Python, double quotes, 1 and 0,
{} for nothing, ASCII, whole numbers, nothing after it.
Fields of an entry (all are required):
  engine         {} while the style is planned (an id reserved, nothing to draw); else {module, design[, looks][, clean]}:
                   module  singles | collision | universe | legacy: the engine family. Only legacy exists in the repository until the
                           engine packages land (catalogue.engine_built tells whether a module is there: a style whose module is
                           not built is never routed to, whatever its stage says)
                   design  the engine's own key for the look
                   looks   {look: stage}: looks inside one style (Universe: echo, vortex, deepfield, starfield); a look never
                           has a higher stage than its style
                   clean   1 for the clean variant (no matter around the iris)
  design_by_eyes  {"3": "trio", "4-8": "family"}: another design of the same module for an eye range ({} when one design serves all)
  canvases       canvas ratios the engine can draw, the default first; the PAID file is the default canvas at 4096 px on its long
                 side, as one JPEG (the terms and the consent note say one image file); the others are admin laboratory and later
  gate_rules     lid | fill: which calibrated rule set the restoration gate runs for this style (both run on the canonical 256 grade)
  plates         plate families read at run time (1K in the bundle, 4K in private storage), by plate-registry family id
  atlas          atlases read at run time: chips | drops
  steps          {} : the default master plan is one art step; a range-keyed list of step kinds (prep, art, scene, finish, bands) only
                 as a hint for the reserve split of the plan
  fill_side      0, or the largest working copy of a soft background fill (at most 1536)
  wave           informational: R1 R2 R3 (the design brief's releases) or legacy
"""
ENGINE = {
    "solo.clean": {
        "engine": {"module": "singles", "design": "clean"},
        "design_by_eyes": {},
        "canvases": ["1:1", "4:5", "9:19.5"],
        "gate_rules": "lid",
        "plates": [],
        "atlas": [],
        "steps": {},
        "fill_side": 0,
        "wave": "R1"
    },
    "solo.powder": {
        "engine": {"module": "singles", "design": "powder"},
        "design_by_eyes": {},
        "canvases": ["1:1", "4:5", "9:19.5"],
        "gate_rules": "lid",
        "plates": ["P-SN-CLOUD"],
        "atlas": ["chips"],
        "steps": {},
        "fill_side": 0,
        "wave": "R2"
    },
    "solo.universe": {
        "engine": {"module": "universe", "design": "echo", "looks": {"echo": "live", "vortex": "live", "deepfield": "lab", "starfield": "lab"}},
        "design_by_eyes": {},
        "canvases": ["1:1", "4:5", "9:19.5"],
        "gate_rules": "fill",
        "plates": ["P-DN-SPIRAL", "P-UV-DUST", "P-UV-MILKY"],
        "atlas": ["chips"],
        "steps": {},
        "fill_side": 1024,
        "wave": "R2"
    },
    "solo.splash": {
        "engine": {"module": "singles", "design": "splash"},
        "design_by_eyes": {},
        "canvases": ["1:1", "4:5", "9:19.5"],
        "gate_rules": "lid",
        "plates": ["P-SP-CROWN"],
        "atlas": ["drops"],
        "steps": {},
        "fill_side": 0,
        "wave": "R2"
    },
    "solo.elements": {
        "engine": {"module": "singles", "design": "elements"},
        "design_by_eyes": {},
        "canvases": ["1:1", "4:5", "9:19.5"],
        "gate_rules": "lid",
        "plates": ["P-EL-FLAME", "P-SP-CROWN"],
        "atlas": ["drops"],
        "steps": {},
        "fill_side": 0,
        "wave": "R2"
    },
    "solo.radiance": {
        "engine": {"module": "singles", "design": "radiance"},
        "design_by_eyes": {},
        "canvases": ["1:1", "4:5", "9:19.5"],
        "gate_rules": "lid",
        "plates": [],
        "atlas": [],
        "steps": {},
        "fill_side": 0,
        "wave": "R2"
    },
    "solo.gold": {
        "engine": {"module": "singles", "design": "gold"},
        "design_by_eyes": {},
        "canvases": ["1:1", "4:5", "9:19.5"],
        "gate_rules": "lid",
        "plates": [],
        "atlas": [],
        "steps": {},
        "fill_side": 0,
        "wave": "R2"
    },
    "duo.collision_infinity": {
        "engine": {"module": "collision", "design": "infinity"},
        "design_by_eyes": {},
        "canvases": ["3:2", "5:4", "1:1", "4:5", "9:19.5"],
        "gate_rules": "lid",
        "plates": ["P-SN-CLOUD", "P-CX-JET"],
        "atlas": ["chips"],
        "steps": {},
        "fill_side": 1536,
        "wave": "R1"
    },
    "duo.clean": {
        "engine": {"module": "collision", "design": "infinity", "clean": 1},
        "design_by_eyes": {},
        "canvases": ["3:2", "5:4", "1:1", "4:5", "9:19.5"],
        "gate_rules": "lid",
        "plates": [],
        "atlas": [],
        "steps": {},
        "fill_side": 1536,
        "wave": "R1"
    },
    "duo.kiss_collision": {
        "engine": {"module": "collision", "design": "kiss"},
        "design_by_eyes": {},
        "canvases": ["3:2", "5:4", "1:1", "4:5", "9:19.5"],
        "gate_rules": "lid",
        "plates": ["P-CX-JET", "P-CX-RIVER"],
        "atlas": ["chips"],
        "steps": {},
        "fill_side": 1536,
        "wave": "R1"
    },
    "duo.universe": {
        "engine": {"module": "universe", "design": "echo"},
        "design_by_eyes": {},
        "canvases": ["3:2", "5:4", "1:1", "4:5"],
        "gate_rules": "fill",
        "plates": [],
        "atlas": ["chips"],
        "steps": {},
        "fill_side": 1024,
        "wave": "R2"
    },
    "duo.reflection": {
        "engine": {},
        "design_by_eyes": {},
        "canvases": ["3:2"],
        "gate_rules": "lid",
        "plates": ["P-SP-CROWN"],
        "atlas": ["drops"],
        "steps": {},
        "fill_side": 0,
        "wave": "R2"
    },
    "duo.radiance": {
        "engine": {},
        "design_by_eyes": {},
        "canvases": ["3:2"],
        "gate_rules": "lid",
        "plates": [],
        "atlas": [],
        "steps": {},
        "fill_side": 0,
        "wave": "R2"
    },
    "duo.gold": {
        "engine": {},
        "design_by_eyes": {},
        "canvases": ["3:2"],
        "gate_rules": "lid",
        "plates": [],
        "atlas": [],
        "steps": {},
        "fill_side": 0,
        "wave": "R2"
    },
    "grp.collision": {
        "engine": {"module": "collision", "design": "family"},
        "design_by_eyes": {"3": "trio", "4-8": "family"},
        "canvases": ["3:2", "1:1", "5:4", "4:5"],
        "gate_rules": "lid",
        "plates": ["P-SN-CLOUD", "P-CX-JET"],
        "atlas": ["chips"],
        "steps": {},
        "fill_side": 1536,
        "wave": "R1"
    },
    "grp.chain": {
        "engine": {"module": "collision", "design": "chain"},
        "design_by_eyes": {},
        "canvases": ["3:2", "3:1", "9:19.5"],
        "gate_rules": "lid",
        "plates": ["P-SN-CLOUD", "P-CX-JET"],
        "atlas": ["chips"],
        "steps": {},
        "fill_side": 1536,
        "wave": "R2"
    },
    "grp.universe": {
        "engine": {"module": "universe", "design": "echo"},
        "design_by_eyes": {},
        "canvases": ["1:1", "3:2"],
        "gate_rules": "fill",
        "plates": [],
        "atlas": ["chips"],
        "steps": {},
        "fill_side": 1024,
        "wave": "R2"
    },
    "grp.reflection": {
        "engine": {},
        "design_by_eyes": {},
        "canvases": ["3:2", "3:1"],
        "gate_rules": "lid",
        "plates": ["P-SP-CROWN"],
        "atlas": ["drops"],
        "steps": {},
        "fill_side": 0,
        "wave": "R2"
    },
    "grp.radiance": {
        "engine": {},
        "design_by_eyes": {},
        "canvases": ["3:2", "1:1"],
        "gate_rules": "lid",
        "plates": [],
        "atlas": [],
        "steps": {},
        "fill_side": 0,
        "wave": "R2"
    },
    "grp.clean": {
        "engine": {},
        "design_by_eyes": {},
        "canvases": ["3:2", "1:1"],
        "gate_rules": "lid",
        "plates": [],
        "atlas": [],
        "steps": {},
        "fill_side": 0,
        "wave": "R2"
    },
    "pet.solo": {
        "engine": {},
        "design_by_eyes": {},
        "canvases": ["1:1"],
        "gate_rules": "lid",
        "plates": [],
        "atlas": ["chips"],
        "steps": {},
        "fill_side": 0,
        "wave": "R3"
    },
    "pet.clean": {
        "engine": {},
        "design_by_eyes": {},
        "canvases": ["1:1"],
        "gate_rules": "lid",
        "plates": [],
        "atlas": [],
        "steps": {},
        "fill_side": 0,
        "wave": "R3"
    },
    "celestial_gold": {
        "engine": {"module": "legacy", "design": "celestial_gold"},
        "design_by_eyes": {},
        "canvases": ["artwork", "wallpaper"],
        "gate_rules": "lid",
        "plates": [],
        "atlas": [],
        "steps": {},
        "fill_side": 0,
        "wave": "legacy"
    },
    "deep_nebula": {
        "engine": {"module": "legacy", "design": "deep_nebula"},
        "design_by_eyes": {},
        "canvases": ["artwork", "wallpaper"],
        "gate_rules": "lid",
        "plates": [],
        "atlas": [],
        "steps": {},
        "fill_side": 0,
        "wave": "legacy"
    },
    "emerald_aurora": {
        "engine": {"module": "legacy", "design": "emerald_aurora"},
        "design_by_eyes": {},
        "canvases": ["artwork", "wallpaper"],
        "gate_rules": "lid",
        "plates": [],
        "atlas": [],
        "steps": {},
        "fill_side": 0,
        "wave": "legacy"
    },
    "obsidian_smoke": {
        "engine": {"module": "legacy", "design": "obsidian_smoke"},
        "design_by_eyes": {},
        "canvases": ["artwork", "wallpaper"],
        "gate_rules": "lid",
        "plates": [],
        "atlas": [],
        "steps": {},
        "fill_side": 0,
        "wave": "legacy"
    },
    "supernova": {
        "engine": {"module": "legacy", "design": "supernova"},
        "design_by_eyes": {},
        "canvases": ["artwork", "wallpaper"],
        "gate_rules": "lid",
        "plates": [],
        "atlas": [],
        "steps": {},
        "fill_side": 0,
        "wave": "legacy"
    },
    "studio_black": {
        "engine": {"module": "legacy", "design": "studio_black"},
        "design_by_eyes": {},
        "canvases": ["artwork", "wallpaper"],
        "gate_rules": "lid",
        "plates": [],
        "atlas": [],
        "steps": {},
        "fill_side": 0,
        "wave": "legacy"
    }
}
