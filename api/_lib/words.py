# -*- coding: utf-8 -*-
"""words: the customer's own words and choices on an order, as the order record, the Stripe metadata and the e-mails carry them (work package WP12).

Numpy free and light on purpose: pay.py, the webhook, the admin and every reader of a paid order import it, and none of them should load the engine
for it. The engine's own cleaning (api/_lib/styles/text.py: NFC, the font check, the lockup line) is used only where an order is CREATED for a style of
the v3 engine (pay.spec_from); everything here is the LENIENT reading, which never raises and never refuses an order that was paid for.

  names     a LIST of strings: at most NAMES_MAX names of NAME_MAX characters, NAMES_TOTAL_MAX in all (C16). The wire forms that are still read: the old string
            "Anna;Max" (a semicolon or a line break separates), a list, and the JSON text of a list (the Stripe metadata of a session made by this code)
  date      one line of at most DATE_MAX characters
  opts      {swap: bool, rotate: 0 to 7, look: a short code}: the options that APPLY to the style (api/_lib/catalogue.py applied_opts)

The Stripe metadata carries names and opts as ONE short string each (meta_names, meta_opts): `store.json_bytes` is ensure_ascii=True and spends six
characters on every non-ASCII letter, so a list of eight names in Lithuanian or Hungarian would pass Stripe's 500 character limit; these are written
with ensure_ascii=False and compact separators, and at most META_MAX characters (a name list that would be longer loses its last names: it cannot be
with the limits above, which a test proves for eight names of 24 non-ASCII letters).
"""
from __future__ import annotations

import json
import re

NAME_MAX = 24            # characters in one name
NAMES_TOTAL_MAX = 200    # characters in all names of one order
DATE_MAX = 20
NAMES_MAX = 8            # one name per eye
RAW_MAX = 1000           # characters of one text field that are read at all (a body may be 4 MB)
PARTS_MAX = 16           # parts of a names list that are read
META_MAX = 480           # characters of one Stripe metadata value this code writes (Stripe's own limit is 500)
LOCKUP_MAX = NAMES_MAX * NAME_MAX + (NAMES_MAX - 1) * 3      # 213: the longest legal names line of the artwork (eight names of 24 letters, " . " between): the preview and the
                                                             # paid file both cut the lockup here (api/compose.py NAMES_CUT, api/_lib/styles/steps.py master_words)
OPT_KEYS = ("swap", "rotate", "look")

_CONTROL = re.compile("[" + re.escape("".join(chr(c) for c in list(range(0x00, 0x20)) + list(range(0x7F, 0xA0)) + list(range(0x200B, 0x2010))
                                              + list(range(0x2028, 0x202F)) + list(range(0x2060, 0x2065)) + [0xFEFF])) + "]")
_SPACES = re.compile(r"\s+")
_SPLIT = re.compile(r"[;\n]")
_LOOK = re.compile(r"^[a-z0-9_]{1,24}$")


def clean(s):
    """One text as the record keeps it: control and zero width characters out, runs of white space one space, trimmed. Not text: ''."""
    return _SPACES.sub(" ", _CONTROL.sub("", s)).strip() if isinstance(s, str) else ""


def _parts(value):
    """The raw parts of a names value in any wire form (a list, the JSON text of a list, the old string): cleaned, empty ones dropped, nothing cut yet."""
    if isinstance(value, str):
        value = value[:RAW_MAX]
        t = value.strip()
        if t.startswith("[") and t.endswith("]"):
            try:
                got = json.loads(t)
            except ValueError:
                got = None
            if isinstance(got, list):
                value = got
        if isinstance(value, str):
            value = _SPLIT.split(value)
    if not isinstance(value, (list, tuple)):
        return []
    return [p for p in (clean(v[:RAW_MAX]) for v in list(value)[:PARTS_MAX] if isinstance(v, str)) if p]


def names_list(value, per=None, total=NAMES_TOTAL_MAX):
    """The names of an order as a list, read leniently from any wire form: each cut at `per` characters (None: not cut, an order made before the limits
    existed may hold a name of 60), the whole list at `total` characters (the last name that does not fit is cut short). Never raises."""
    out, used = [], 0
    for p in _parts(value):
        p = p[:per] if per else p
        room = total - used
        if room <= 0:
            break
        out.append(p[:room])
        used += len(out[-1])
        if len(p) > room:
            break
    return out


def names_text(value):
    """The names for a sentence or an e-mail row: "Anna, Max" (a name list), or the old string as it was; '' for none."""
    if isinstance(value, str):
        return clean(value)
    return ", ".join(names_list(value))


def names_wire(value):
    """The names in the old wire form the legacy composer reads: "Anna;Max" (one string, a semicolon between), cut at the total."""
    if isinstance(value, str):
        return clean(value)[:NAMES_TOTAL_MAX]
    return ";".join(names_list(value))[:NAMES_TOTAL_MAX]


def meta_names(value):
    """The names as one Stripe metadata value: the compact JSON of the list (ensure_ascii False), '' for none (an empty value would unset the key).
    At most META_MAX characters: a list that is longer loses names from the end."""
    if isinstance(value, str):
        return clean(value)[:NAMES_TOTAL_MAX]          # a spec of the old form (a recorded one): the text as it was, as the metadata always held it
    names = names_list(value)
    while names:
        s = json.dumps(names, ensure_ascii=False, separators=(",", ":"))
        if len(s) <= META_MAX:
            return s
        names = names[:-1]
    return ""


def date_clean(value, limit=DATE_MAX):
    """The date line of an order: one cleaned line (the old semicolon is no separator), cut at the limit; '' for none."""
    return clean(value[:RAW_MAX] if isinstance(value, str) else None)[:limit]


def opts_read(value):
    """The options of an order from any wire form (a dict, or the compact JSON text of one), leniently: only the three known keys with values of the
    right kind survive; anything else is dropped. Never raises."""
    if isinstance(value, str):
        try:
            value = json.loads(value[:RAW_MAX]) if value.strip() else {}
        except ValueError:
            value = {}
    if not isinstance(value, dict):
        return {}
    out = {}
    if isinstance(value.get("swap"), bool):
        out["swap"] = value["swap"]
    r = value.get("rotate")
    if isinstance(r, int) and not isinstance(r, bool) and 0 <= r <= 7:
        out["rotate"] = r
    lk = value.get("look")
    if isinstance(lk, str) and _LOOK.match(lk):
        out["look"] = lk
    return out


def meta_opts(opts):
    """The options as one Stripe metadata value: compact JSON with sorted keys, '' for none."""
    o = opts_read(opts)
    return json.dumps(o, sort_keys=True, separators=(",", ":")) if o else ""
