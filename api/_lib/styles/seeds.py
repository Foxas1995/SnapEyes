# -*- coding: utf-8 -*-
"""styles.seeds: the one place where the seed of an artwork is made (work package WP5B, decision C9, step B of the seed change).

Until WP5B an engine seeded its pictures from the BYTES of the iris it was given (the prototype's seed_for: sha256 of the iris bytes, the eye
index, the design and the canvas). That made a preview and its paid file differ whenever they were made from different bytes of the same eye (a
768 px copy against a 4096 px master), made the plate a plate style picks unknowable before the render, and let a change of canvas re-roll the
powder. The seed of an artwork is now a function of WHICH eyes it shows and WHICH picture was asked for, and of nothing else:

    seed = first 8 bytes of sha256(canonical JSON of {seed: 2, eyes: [eye_id, ...], key: {style, design_used, bg, clean, layout, opts, pv}})

  eye_id      the 16 hex digits of the sealed profile (api/_lib/preview.py: the sha256 of the clean 1024 px preview bytes the eye was
              restored to). The preview, the order's draft and the master of one eye all carry the same id, so all three seed alike.
  key         the plan's seed_key (resolve() of the family makes it): the registry id of the style, the design it draws with, the ground
              ("dark" or "universe"), the clean flag, the layout id, the three options the buyer may choose (swap, rotate, look) and the plates
              version (pv). The design and the ground are in it because a fallback (Infinity to Kiss geometry, a stack of two irises) must
              re-roll in the same way in the preview and in the master (review ED29).
  NOT in it   the names, the date, the canvas size, the canvas ratio, the eye pixels, the machine, the clock. A typo in a name must never
              reshuffle the powder; a 1024 px preview and a 4096 px master draw the same seed.

The plate registry is append-only and every pick takes the pv of the key (api/_lib/styles/plates.py): a plate added later never changes the
plate an older order picks, and a retired plate still answers an old pv.

seed_for_key() refuses anything that is not what it says (no eyes, an unknown field of the key, a missing one, a value of the wrong kind) rather
than hash a guess: a seed that quietly ignored a field would be a picture that quietly ignored a choice.

The prototype's formula stays in styles/core.py (seed_for) because the collision and universe families are still ported with it (their own step
B), and the singles keep it behind one lab option (opts seed_mode "legacy": the admin laboratory shows the boards as they were before the change,
and the golden suite proves that this is the ONLY thing step B changed).
"""
from __future__ import annotations

import hashlib
import json
import re

SEED_VERSION = 2                                     # 1 is the prototype's seed_for (iris bytes, eye index, design, canvas)
KEY_FIELDS = ("style", "design_used", "bg", "clean", "layout", "opts", "pv")
OPT_FIELDS = ("swap", "rotate", "look")              # the three options the buyer may choose
EYE_ID = re.compile(r"[0-9a-f]{16}")


def is_eye_id(value):
    return isinstance(value, str) and EYE_ID.fullmatch(value) is not None


def clean_key(key):
    """The seed key in its canonical form: exactly KEY_FIELDS, strings for style, design_used, bg and layout, a bool for clean, the three options
    (None when unset), pv a whole number. ValueError for anything else."""
    if not isinstance(key, dict):
        raise ValueError("a seed key is a dict")
    extra = sorted(set(key) - set(KEY_FIELDS))
    missing = [k for k in KEY_FIELDS if k not in key]
    if extra or missing:
        raise ValueError(f"a seed key has exactly the fields {', '.join(KEY_FIELDS)} (unknown: {extra}, missing: {missing})")
    for k in ("style", "design_used", "bg", "layout"):
        if not isinstance(key[k], str) or not key[k]:
            raise ValueError(f"seed key field {k} is a non-empty text")
    pv = key["pv"]
    if isinstance(pv, bool) or not isinstance(pv, int) or pv < 0:
        raise ValueError("seed key field pv is a whole number (the plates version)")
    opts = key["opts"]
    if not isinstance(opts, dict) or set(opts) - set(OPT_FIELDS):
        raise ValueError(f"seed key field opts holds only {', '.join(OPT_FIELDS)}")
    for k, v in opts.items():
        if v is not None and not isinstance(v, (str, int, bool)):
            raise ValueError(f"seed key option {k} is text, a whole number, a bool or unset")
    return {"style": key["style"], "design_used": key["design_used"], "bg": key["bg"], "clean": bool(key["clean"]), "layout": key["layout"],
            "opts": {k: opts.get(k) for k in OPT_FIELDS}, "pv": pv}


def seed_for_key(eye_ids, key):
    """The 64 bit seed of one artwork (see the module text). eye_ids: the 16 hex ids of its eyes in canvas order (at least one)."""
    if not isinstance(eye_ids, (list, tuple)) or not eye_ids or not all(is_eye_id(i) for i in eye_ids):
        raise ValueError("a seed needs the 16 hex digit id of every eye (the id of the sealed profile)")
    body = {"seed": SEED_VERSION, "eyes": list(eye_ids), "key": clean_key(key)}
    data = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return int.from_bytes(hashlib.sha256(data).digest()[:8], "big")
