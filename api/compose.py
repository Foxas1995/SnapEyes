# -*- coding: utf-8 -*-
"""POST /api/compose: the free preview of the customer's own eyes in the styles of the studio. The server decides what the picker shows (the
catalogue's tiles, which one is recommended, which are held back and why) and makes every tile of a group in one call (compose API v3, work
package WP10; the page owns no list of styles).

Request (JSON; the page's old requests are all still accepted):
  sealed   [sealed, ...] 1-8 restored irises as /api/enhance sealed them ("sealed", or one of its "sealed_sizes"), in canvas order; opened here
           (api/_lib/preview.py), the page never holds them in the clear. Old pages: irises: [b64, ...] 1-8 enhanced iris squares (or iris: b64,
           the one-eye form), still accepted for one release; sealed wins when both are sent.
  style    one style id (the registry's: api/_lib/styles_registry.py; the legacy ids too; "pick": the recommended tile) OR
  styles   a batch: a list of ids (up to TILES_MAX), the tiles of one set of eyes made on ONE eye preparation. Exclusive with style. A list
           may be empty: the reply is then the tile list alone, which costs no pixel.
  size     the preview's long side: 1024 (the default of one style) or 480 (the default of a batch, a tile); nothing else (400): a customer never
           gets a larger preview than 1024 px
  layout, format ("artwork" | "wallpaper" | a canvas of the engine), names (a list of texts, or the old string "Anna;Max"), date, family_name,
  title (the AI-generated sample's label), pad, lang, market, retake (how many eyes of this set the page has replaced since its last compose)
  opts     {swap, rotate, look}: the three options the buyer may choose; any other key is a 400; one that does not apply (swap for other than two
           eyes, rotate for fewer than three, a look the style has not) is left out
  lab      true, with "Authorization: Bearer <admin key>": the laboratory styles too (the owner's admin page). Without a valid key it is nothing.
  unlock   a signed unlock ticket (nothing mints one yet): the clean render. Never for a batch.
  action   "help": a count of one click on the manual route of the retake state ({route: "manual", eyes, why}); no eyes needed.
Reply (one style): {ok, style, layout, layouts, format, count, width, height, image (JPEG b64), styles, qa, eyes, tiles, pick, size, opts, canvas,
design_used, fallback, plan8, engine {v, reg, pv}, selfcheck, timing}. A batch: {ok, batch, count, size, format, tiles, pick, styles, eyes, engine, timing}.
  plan8    the identity of the plan this picture is (api/_lib/styles/steps.py make_plan: the style, layout, options, the eyes' ids, the design and the
           seed key): checkout recomputes the plan from the sealed profiles and answers 409 plan_changed when the page's differs, so the page sends it back
  eyes     per eye {eye, eye_id, cls, pupil, gate {lid, fill}[, why]}: what the eye's seal says (api/_lib/preview.py seal v2, the profile measured at
           /api/enhance; true, false, or null = unknown: a version 1 seal, or a profile that was not measured; null for an old page's plain irises);
           why (only for an eye that fails a rule): the reason codes of the failing rules, which the retake state turns into its two sentences and its tip
  tiles    the tiles of these eyes in the server's order, the recommended one first: {id, name, slug, group, legacy, stage (live, preview or lab),
           available, why (gate, reseal or bar_pupil: the eyes cannot take it), layouts, eyes, price_class, looks, pick}; the tiles a batch made also
           carry image, width, height, layout, canvas, design_used, fallback and plan8. A tile that is not available is not drawn.
  pick     {id, reason}: the recommended tile (always one the customer can buy now: live and available; null when nothing can be bought) and the key of
           its reason line (null unless the pick was made for the eyes' colour class)
Refusals: 400 a request that is not one (unknown style, layout or option, a size that is not 1024 or 480, style and styles together); 422
style_unavailable {why: stage, eyes, gate, reseal, bar_pupil} for a style a customer may not have (laboratory, planned, retired, wrong number of eyes,
or eyes the style cannot take: the same one-style request that a batch reports as a tile; bar_pupil is also what the engine itself answers when it
finds a bar pupil the sealed profile did not show: its tile is then marked unavailable and the other tiles of the batch are still made); 422
too_many_styles {max}: the batch costs more than
TILES_BUDGET_S seconds; 503 busy_retry {retry_after}: another render holds the CPU or memory of this instance, or not enough time is left in the
call; 503 tiles_paused: this instance's ceiling of tiles for today is reached.
A style of the v3 engine (the registry's engine module is not "legacy": api/_lib/styles) is drawn by its family; the legacy styles by
api/_lib/iris.py as always. The words on the picture are the customer's own (names, date, family name) and nothing else; the watermark is
drawn over the clean render here and nowhere else (api/_lib/preview.py watermark: iris-anchored on every disc)."""
import os, sys, io, time, base64, threading, inspect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import BaseHTTPRequestHandler
from _lib import iris as L
from _lib import catalogue
from _lib import events as E   # the admin panel's usage events (no personal data)
from _lib import preview as P
from _lib import store         # Answer: the refusals that are not a 400, and _StatusReq, which gives them their status
from _lib import markets as MK
from _lib.styles import gate as GATE   # the restoration gate: the set-level result of the eyes of one request
from _lib.styles import guard as GUARD   # one heavy render at a time per instance, one memory budget
from _lib.styles import costs as COSTS   # what a preview and a batch of tiles cost, before any pixel is drawn

PREVIEW_SIZE = 1024          # longest side of the artwork this endpoint returns. Kept at 1024 when the iris preview
                             # went down to 800 px (2026-09-29): at 900 the footer line of a 21:9 row of four eyes
                             # drops from 9 to 8 px and no longer reads; the badge, title and names read at both
TILE_SIZE = 480              # a tile: about 35 KB
SIZES = (PREVIEW_SIZE, TILE_SIZE)     # the only sizes a customer can ask for
MAX_SIDE = 4096              # the 4K render is 4096 px: a larger image is not an iris this site made
MIN_SIDE = 64
WORK_SIDE = 2048             # a 1024 px preview never needs more than this, so a larger iris is shrunk on arrival.
                             # Up to 2048 px the preview is exactly what the engine makes of the iris as sent; a
                             # 3000-4096 px iris is graded from its 2048 px copy (a few levels off grading it whole,
                             # measured up to 19). The site sends the 1024 px squares /api/enhance returns.
MAX_TOTAL_B64 = 4_400_000    # Vercel refuses a request body over 4.5 MB before this code runs; this says it in words

TILES_MAX = 8                # styles in one batch
TILES_BUDGET_S = 40.0        # a batch whose estimated seconds (prep plus the tiles, at the slow factor) pass this is refused: 422 too_many_styles
TILES_DAY_MAX = 800          # tiles one instance makes per UTC day (SNAPEYES_TILES_DAY_MAX): a batch is up to 30 times the work of an old compose and
                             # the Hobby plan allows 4 hours of CPU a month (decision 23); past it 503 tiles_paused until 00:00 UTC
TILE_FALLBACK_S = 4.0        # the estimate of one tile whose cost table has no row (a style the table cannot price is a style to be careful with)
LEGACY_PREVIEW_S = 1.3       # the legacy engine's own 1024 px preview, warm (the plan, section 2.8): it has no row in the cost table
LEGACY_TILE_S = 0.6          # and a 480 px tile of it
OPT_KEYS = ("swap", "rotate", "look")
PICK = "pick"                # the style id that means "the recommended tile"
RETAKE_MAX = 8

# ----------------------------------------------------------------------------- the customer's sentences of the new refusals
WORDS = {
    "stage": {"en": "This style is not open yet.", "de": "Dieser Stil ist noch nicht geöffnet.",
              "lt": "Šis stilius dar neatidarytas.", "hu": "Ez a stílus még nem nyílt meg."},
    "eyes": {"en": "This style is not made for this number of eyes.", "de": "Dieser Stil ist für diese Anzahl von Augen nicht gemacht.",
             "lt": "Šis stilius nekuriamas tokiam akių skaičiui.", "hu": "Ez a stílus nem ennyi szemhez készül."},
    "gate": {"en": "This style needs a cleaner iris. Please retake the photo of the eye.",
             "de": "Dieser Stil braucht eine sauberere Iris. Bitte fotografieren Sie das Auge erneut.",
             "lt": "Šiam stiliui reikia švaresnės rainelės. Nufotografuokite akį dar kartą.",
             "hu": "Ehhez a stílushoz tisztább íriszre van szükség. Kérjük, fotózd le újra a szemet."},
    "reseal": {"en": "Please make the preview of this eye again.", "de": "Bitte erstellen Sie die Vorschau dieses Auges erneut.",
               "lt": "Sukurkite šios akies peržiūrą iš naujo.", "hu": "Kérjük, készítsd el újra ennek a szemnek az előnézetét."},
    "bar_pupil": {"en": "This style does not suit this pupil shape.", "de": "Dieser Stil passt nicht zu dieser Pupillenform.",
                  "lt": "Šis stilius netinka tokiai vyzdžio formai.", "hu": "Ez a stílus nem illik ehhez a pupillaformához."},
    "too_many_styles": {"en": "That is too many styles at once. Ask for fewer.", "de": "Das sind zu viele Stile auf einmal. Bitte fragen Sie weniger an.",
                        "lt": "Per daug stilių vienu metu. Paprašykite mažiau.", "hu": "Túl sok stílus egyszerre. Kérj kevesebbet."},
    "busy_retry": {"en": "We are busy for a moment. Please try again shortly.", "de": "Wir sind gerade ausgelastet. Bitte versuchen Sie es gleich erneut.",
                   "lt": "Šiuo metu esame užimti. Pabandykite netrukus dar kartą.", "hu": "Egy pillanatra elfoglaltak vagyunk. Kérjük, próbáld újra hamarosan."},
    "tiles_paused": {"en": "We are not making more previews today. Please try again later.",
                     "de": "Heute erstellen wir keine weiteren Vorschauen. Bitte versuchen Sie es später erneut.",
                     "lt": "Šiandien daugiau peržiūrų nekuriame. Pabandykite vėliau.",
                     "hu": "Ma már nem készítünk több előnézetet. Kérjük, próbáld később újra."},
}


def _say(key, lang=None):
    row = WORDS[key]
    return row.get(lang or L.page_lang(), row["en"])


def _refuse(status, reason, key, retry=False, retry_after=None, **extra):
    return store.Answer(status, reason, _say(key), retry, retry_after, **extra)


def _text(v, n):
    return v[:n] if isinstance(v, str) else ""

def _choice(v, options, default):
    """v when it is one of options (strings), else default: a list, a dict or a number never reaches a lookup."""
    return v if isinstance(v, str) and v in options else default

def _pad(v):
    """The crop padding the client used (1.12). Clamped: a tiny pad would ask for a frame of any size."""
    try:
        p = float(v) if v not in (None, "") else 1.12
    except (TypeError, ValueError):
        p = 1.12
    return min(2.0, max(1.0, p)) if p == p else 1.12

def _int(v, lo, hi, default=0):
    """v as a whole number between lo and hi, else default (a counter that is not one is no counter)."""
    return v if isinstance(v, int) and not isinstance(v, bool) and lo <= v <= hi else default


# ----------------------------------------------------------------------------- the eyes of a request
def _open(body):
    """(raw, metas, plains): the eyes of a request before any image is decoded. raw: the base64 text of each eye (a seal opened, or as sent), metas:
    per eye what its seal said (preview.unseal_full's meta: v, kind, eye_id, profile; None for an old page's plain irises), plains: the bytes of each
    seal's image (None for plain irises: their bytes are decoded from raw). Every refusal here is a ClientError."""
    raw = body.get("sealed")
    sealed = isinstance(raw, list) and len(raw) > 0     # the sealed form wins whenever it is sent
    if not sealed:
        raw = body.get("irises")
        if (raw is None or (isinstance(raw, list) and not raw)) and body.get("iris") is not None:
            raw = [body.get("iris")]      # the one-eye form, also when a client sends it next to an empty list
    if not isinstance(raw, list) or not 1 <= len(raw) <= L.MULTI_MAX:
        raise L.ClientError(f"Send between 1 and {L.MULTI_MAX} iris images.")
    if not all(isinstance(s, str) and s for s in raw):
        raise L.ClientError("Each iris image must be sent as base64 text.")
    if sum(len(s) for s in raw) > MAX_TOTAL_B64:
        raise L.ClientError("Those images are too large together. Send each one at 1024 pixels.")
    metas = [None] * len(raw)
    plains = None
    if sealed:
        try:
            opened = [P.unseal_full(s) for s in raw]
        except P.SealError as e:
            raise L.ClientError(P.refusal(e)) from None
        plains = [plain for plain, _ in opened]
        raw = [base64.b64encode(plain).decode("ascii") for plain in plains]
        metas = [meta for _, meta in opened]
    return raw, metas, plains


def _irises(body):
    """The iris squares of a request (the form every caller used before the eye profile): _irises_full(body)[0]."""
    return _irises_full(body)[0]

def _irises_full(body, opened=None):
    """(squares, metas, raws): the iris squares of a request (decoded, cut square, shrunk to WORK_SIDE), per eye what its seal said (preview.unseal_full's
    meta: v, kind, eye_id, profile; None for an old page's plain irises) and the bytes of the image as it was sent (opened from its seal, or decoded):
    the engine of the v3 styles seeds from them and builds its own eye from them, so every byte is the very one the eye id was made from.
    opened: what _open(body) already made of the same body (the seals are opened once)."""
    raw, metas, plains = opened or _open(body)
    out = []
    for s in raw:
        im = L.b64_to_pil(s, max_side=MAX_SIDE)
        side = min(im.size)
        if side < MIN_SIDE:
            raise L.ClientError(f"Each iris image must be at least {MIN_SIDE} pixels.")
        im = im.crop((0, 0, side, side))
        if side > WORK_SIDE:
            im = im.resize((WORK_SIDE, WORK_SIDE), L.Image.LANCZOS)
        out.append(im)
    if plains is None:
        plains = [base64.b64decode(s.split(",", 1)[1] if (s.strip().startswith("data:") and "," in s[:64]) else s) for s in raw]
    return out, metas, plains


def _plains(raw, plains):
    """The bytes of each eye as sent, each checked from its header alone (nothing is decoded: the engine's own eye does that once): an image of a
    readable kind, not above MAX_PIXELS, between MIN_SIDE and MAX_SIDE pixels. The same refusals b64_to_pil and _irises_full make."""
    if plains is None:
        plains = []
        for s in raw:
            if len(s) > L.MAX_B64_CHARS:
                raise ValueError("image too large")
            try:
                plains.append(base64.b64decode(s.split(",", 1)[1] if (s.strip().startswith("data:") and "," in s[:64]) else s))
            except ValueError:
                raise ValueError("not a readable image") from None
    for b in plains:
        try:
            w, h = L.Image.open(io.BytesIO(b)).size
        except (OSError, SyntaxError, L.Image.DecompressionBombError):
            raise ValueError("not a readable image") from None
        if w * h > L.MAX_PIXELS:
            raise ValueError("image too large")
        if max(w, h) > MAX_SIDE:
            raise L.ClientError(f"Each image may be at most {MAX_SIDE} pixels on its longer side.")
        if min(w, h) < MIN_SIDE:
            raise L.ClientError(f"Each iris image must be at least {MIN_SIDE} pixels.")
    return plains


def _eyes_reply(metas):
    """The reply's "eyes": what each eye's seal says (see the module text)."""
    rows = []
    for i, m in enumerate(metas, 1):
        prof = m.get("profile") if isinstance(m, dict) else None
        ok = {r: (prof.gate(r)["ok"] if prof is not None else None) for r in GATE.RULES}
        row = {"eye": i, "eye_id": m.get("eye_id") if isinstance(m, dict) else None,
               "cls": prof.cls if prof is not None else None, "pupil": prof.pupil_cls if prof is not None else None, "gate": ok}
        if prof is not None and False in ok.values():
            row["why"] = [c for r in GATE.RULES if ok[r] is False for c in prof.gate(r)["why"]]       # the reason codes of the failing rules, for the retake state
        rows.append(row)
    return rows

def _recs(metas):
    """The profile records the catalogue reads (cls, pupil, gate per rule) of each eye: {} for an eye with no sealed profile (its gate is unknown)."""
    return [(m.get("profile").rec if isinstance(m, dict) and m.get("profile") is not None else {}) for m in metas]

def _gate_code(style, n, metas):
    """The set-level gate code of the request for the event: ok, unknown, or the reason code of the first failing eye, under the rule
    set the style's engine entry names (the collision rule when the style has none)."""
    rule = ((catalogue.engine_for(style, n) or {}).get("gate_rules")) or "lid"
    r = GATE.set_result([(m or {}).get("profile") for m in metas], rule)
    return "ok" if r["ok"] is True else ("unknown" if r["ok"] is None else r["first"]["why"])


# ----------------------------------------------------------------------------- the customer's words
TEXT_RAW_MAX = 1000          # characters of one customer text field that are read at all (the preview keeps 60 of the names and 20 of the date): the body
                             # may be 4 MB, and cleaning it letter by letter cost 7.5 s of CPU before the picture was drawn (the legacy path cuts first)
TEXT_PARTS_MAX = 16          # parts of a names list that are read (the old wire form holds one name per eye, eight at most)
NAMES_CUT = 60               # characters of the names line the preview keeps; the paid file cuts at the same place (styles/steps.py master_words)
DATE_CUT = 20

def _engine_text(value, limit=None):
    """The customer's names as the v3 engine draws them: cleaned, the names as one lockup line, and without a letter the artwork font
    cannot draw (it would print as an empty box; checkout refuses such a name, a free preview just leaves the letter out). The names come as
    text ("Anna;Max") or as a list of texts, anything else is no names; only the first TEXT_RAW_MAX characters of a field are read."""
    from _lib.styles import text as TX
    out = TX.lockup(_engine_names(value, None))
    return out[:limit] if limit else out

def _engine_names(value, limit=NAMES_CUT):
    """The names as a LIST of cleaned names (what a family that draws one name per eye reads; the singles family joins them into its lockup), each
    without a letter the font cannot draw; the list is cut where its lockup would pass limit characters (the last name may be cut short)."""
    from _lib.styles import text as TX
    if isinstance(value, (list, tuple)):
        value = [v[:TEXT_RAW_MAX] for v in value[:TEXT_PARTS_MAX] if isinstance(v, str)]
    elif isinstance(value, str):
        value = value[:TEXT_RAW_MAX]
    else:
        return []
    parts = [p for p in (TX.clean("".join(ch for ch in n if not TX.unsupported(ch))) for n in TX.split_names(value)) if p]
    if not limit:
        return parts
    out, used = [], 0
    for p in parts:
        room = limit - used - (len(TX.LOCKUP_JOIN) if out else 0)
        if room <= 0:
            break
        out.append(p[:room])
        used += len(out[-1]) + (len(TX.LOCKUP_JOIN) if len(out) > 1 else 0)
        if len(p) > room:
            break
    return out

def _engine_date(value, limit=None):
    """The customer's date as the v3 engine draws it: one cleaned line, as typed (a semicolon or a line break does not separate dates: the paid
    file draws TX.clean(date) as well), without a letter the artwork font cannot draw. Only the first TEXT_RAW_MAX characters are read."""
    from _lib.styles import text as TX
    if not isinstance(value, str):
        return ""
    out = TX.clean("".join(ch for ch in value[:TEXT_RAW_MAX] if not TX.unsupported(ch)))
    return out[:limit] if limit else out

def _legacy_names(value):
    """The names of a legacy preview: the old string cut at 60 characters; a list (the new wire form) is joined with the old separator first."""
    if isinstance(value, (list, tuple)):
        value = ";".join(v[:TEXT_RAW_MAX] for v in value[:TEXT_PARTS_MAX] if isinstance(v, str))
    return _text(value, NAMES_CUT)


def _engine_canvas(style, n, fmt_in):
    """(engine entry, the canvas id asked for or None, the legacy format word) of a request for a v3 style: a canvas id of the engine, or "wallpaper"
    read as the phone canvas where the engine draws one. None when the request asks for no canvas of its own: the family then draws its own default
    canvas (the registry's list is not in the order of the family's defaults: the trio's is 1:1, its list begins with 3:2), which is also the canvas the
    master plan resolves, so the preview and the paid file have the same canvas. The reply names the canvas that was drawn (the Preview's fmt)."""
    eng = catalogue.engine_for(style, n)
    canvases = eng["canvases"]
    canvas = fmt_in if isinstance(fmt_in, str) and fmt_in in canvases else ("9:19.5" if fmt_in == "wallpaper" and "9:19.5" in canvases else None)
    return eng, canvas, ("wallpaper" if canvas == "9:19.5" else "artwork")


# ----------------------------------------------------------------------------- the request
def _opts(v):
    """The options a request names, checked for their kind: {swap: bool, rotate: 0 to 7, look: a short code}. Any other key, or a value of another
    kind, is a 400 (the text never echoes what was sent)."""
    if v is None:
        return {}
    if not isinstance(v, dict):
        raise L.ClientError("opts is an object.")
    if set(v) - set(OPT_KEYS):
        raise L.ClientError(f"Unknown option: the options are {', '.join(OPT_KEYS)}.")
    out = {}
    if "swap" in v:
        if not isinstance(v["swap"], bool):
            raise L.ClientError("The option swap is true or false.")
        out["swap"] = v["swap"]
    if "rotate" in v:
        if not isinstance(v["rotate"], int) or isinstance(v["rotate"], bool) or not 0 <= v["rotate"] <= 7:
            raise L.ClientError("The option rotate is a whole number from 0 to 7.")
        out["rotate"] = v["rotate"]
    if "look" in v:
        if not isinstance(v["look"], str) or not 1 <= len(v["look"]) <= 24 or not all(c.islower() or c.isdigit() or c == "_" for c in v["look"]):
            raise L.ClientError("The option look is the code of a look.")
        out["look"] = v["look"]
    return out


def _request(body):
    """The cheap, checked part of a request: what was asked for, no pixel touched. Every refusal here is a ClientError (400) or a refusal of the
    batch's size (422)."""
    one, many = body.get("style"), body.get("styles")
    if one is not None and many is not None:
        raise L.ClientError("Send style or styles, not both.")
    if many is not None:
        if not isinstance(many, list):
            raise L.ClientError("styles is a list of style ids.")
        if len(many) > TILES_MAX:                       # before its items are looked at: a list of a million is cut off at once
            raise _refuse(422, "too_many_styles", "too_many_styles", False, None, max=TILES_MAX)
        if not all(isinstance(s, str) for s in many):
            raise L.ClientError("styles is a list of style ids.")
        if len(set(many)) != len(many):
            raise L.ClientError("Ask for each style once.")
        styles = list(many)
    else:
        if one is not None and not isinstance(one, str):
            raise L.ClientError("style is a style id.")
        styles = [one or catalogue.DEFAULT_STYLE]
    size = body.get("size")
    if size is None:
        size = TILE_SIZE if many is not None else PREVIEW_SIZE
    elif not isinstance(size, int) or isinstance(size, bool) or size not in SIZES:
        raise L.ClientError(f"size is {PREVIEW_SIZE} or {TILE_SIZE}.")
    layout = body.get("layout")
    if layout is not None and not isinstance(layout, str):
        raise L.ClientError("layout is a layout id.")
    market = body.get("market")
    lang = body.get("lang") if body.get("lang") in L.PAGE_LANGS else "en"
    return {"batch": many is not None, "styles": styles, "size": size, "layout": layout or None, "opts": _opts(body.get("opts")),
            "fmt": body.get("format"), "names": body.get("names"), "date": body.get("date"), "family": body.get("family_name"),
            "title": _text(body.get("title"), 40), "lang": lang, "market": market if isinstance(market, str) and market in MK.MARKETS else None,
            "retake": _int(body.get("retake"), 0, RETAKE_MAX), "lab": body.get("lab") is True}


def _bearer(req):
    h = str(req.headers.get("authorization") or "")
    return h[7:].strip() if h[:7].lower() == "bearer " else ""


def _is_admin(bearer):
    """Is this a valid admin key? Looked at only when a request says lab: true (the admin module is imported on use)."""
    if not bearer:
        return False
    try:
        from _lib import ops
        return bool(ops.check_admin_key(bearer))
    except Exception:  # noqa: a check that cannot run is a refusal
        return False


def _tile_opts(opts, style, n, admin):
    """The options that apply to this style for n eyes (swap for two, rotate for three or more, a look the style has), as the seed key reads them:
    the others are left out. A look the style has but a customer may not see yet is a 422 (stage); a look the style does not have is dropped."""
    out = {}
    if "swap" in opts and n == 2:
        out["swap"] = opts["swap"]
    if "rotate" in opts and n >= 3:
        out["rotate"] = opts["rotate"] % n
    if "look" in opts:
        looks = (catalogue.engine_for(style, n) or {}).get("looks") or {}
        if opts["look"] in looks:
            if opts["look"] not in catalogue.looks_for(style, n, admin):
                raise _refuse(422, "style_unavailable", "stage", False, None, why="stage", style=style, look=opts["look"])
            out["look"] = opts["look"]
    return out


# ----------------------------------------------------------------------------- what a request costs
def _cost_key(style, n, look=None):
    e = catalogue.engine_for(style, n)
    try:
        return COSTS.cost_key(e, "dark", look) if e and e.get("module") != "legacy" else None
    except COSTS.NoCost:
        return None


def _need(styles, n, size, opts=None, factor=None):
    """(seconds, megabytes) one call needs to make these styles as a batch on one eye preparation, at the slow factor: the cost table's
    tiles_need for the styles of the v3 engine, a flat estimate for a legacy style (no row) or a design the table has no row for."""
    F = COSTS.slow_factor() if factor is None else float(factor)
    keys, extra, mb = [], 0.0, 0.0
    for s in styles:
        look = ((opts or {}).get(s) or {}).get("look")
        k = _cost_key(s, n, look)
        if k is None:
            extra += F * ((LEGACY_PREVIEW_S if size >= PREVIEW_SIZE else LEGACY_TILE_S) if catalogue.is_legacy(s) else TILE_FALLBACK_S)
            mb = max(mb, 300.0)
            continue
        try:
            keys.append(k)
            mb = max(mb, float(COSTS._row(COSTS.PREVIEW, k, n)[4]))
        except COSTS.NoCost:
            keys.pop()
            extra += F * TILE_FALLBACK_S
            mb = max(mb, 700.0)
    sec = extra
    if keys:
        sec += COSTS.tiles_need(keys, n, size, F) if len(keys) > 1 or size < PREVIEW_SIZE else COSTS.preview_need(keys[0], n, size, F)
    return sec, mb * COSTS.LINUX_ALLOWANCE + 20.0 * n


_DAY = {"day": "", "tiles": 0}
_DAY_LOCK = threading.Lock()


def _utc_day():
    return time.strftime("%Y-%m-%d", time.gmtime())


def _tiles_room(k):
    """Charge k tiles to today's ceiling of this instance; False when they do not fit (nothing is charged then). A request that ends up drawing
    fewer gives the rest back (_tiles_refund): the ceiling counts pictures made, not requests tried."""
    try:
        cap = int(os.environ.get("SNAPEYES_TILES_DAY_MAX", "").strip() or TILES_DAY_MAX)
    except ValueError:
        cap = TILES_DAY_MAX
    cap = max(1, min(cap, 1_000_000))
    day = _utc_day()
    with _DAY_LOCK:
        if _DAY["day"] != day:
            _DAY["day"], _DAY["tiles"] = day, 0
        if _DAY["tiles"] + k > cap:
            return False
        _DAY["tiles"] += k
        return True


def _tiles_refund(k, day):
    """Give k tiles back to the ceiling of `day` (the UTC day they were charged on: after midnight the counter is another day's and is left alone)."""
    with _DAY_LOCK:
        if k > 0 and _DAY["day"] == day:
            _DAY["tiles"] = max(0, _DAY["tiles"] - k)


def _until_midnight():
    now = time.gmtime()
    return int(86400 - (now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec))


_HASH = []


def _engine_facts():
    """{v, reg, pv}: the engine version, the registry hash and the plates version a picture was made under (also what the plan records)."""
    if not _HASH:
        _HASH.append(catalogue.registry_hash())
    from _lib import styles as ST
    return {"v": ST.ENGINE_V, "reg": _HASH[0], "pv": catalogue.PLATES_VERSION}


# ----------------------------------------------------------------------------- one preview of a style of the v3 engine
def _eyes_for(plains, metas, styles, n):
    """The eye objects of the engine (api/_lib/styles/core.py Iris) for these styles: one set, cut at the smallest working copy the styles allow
    (the registry's work_side caps pairs, families and chains further than a preview's 2048)."""
    from _lib.styles import core as SCORE
    side = min([WORK_SIDE] + [w for w in (catalogue.work_side(s, n) for s in styles) if w])
    eyes = []
    for i, raw in enumerate(plains, 1):
        meta = metas[i - 1] if isinstance(metas[i - 1], dict) else {}
        try:
            eyes.append(SCORE.Iris(raw, f"compose{i}", max_side=side, eye_id=meta.get("eye_id")))
        except (OSError, SyntaxError, L.Image.DecompressionBombError):
            raise ValueError("not a readable image") from None
    return eyes


def _spec(style, n, eyes, metas, req, canvas, layout, opts):
    """The spec the engine reads (api/_lib/styles/__init__.py): the style, the layout, the canvas, the customer's words (names as a list: a family that
    draws one name per eye reads it so; the singles family joins it into its lockup), the options, the eyes' ids and their sealed profiles."""
    return {"style": style, "layout": layout, "eyes": n, "canvas": canvas, "names": _engine_names(req["names"]), "date": _engine_date(req["date"], DATE_CUT),
            "family_name": _engine_date(req["family"], 24), "opts": opts, "eye_ids": [e.eye_id for e in eyes], "profiles": [(m or {}).get("profile") for m in metas],
            "lang": req["lang"]}


def _layout_for(style, n, wanted, strict):
    """(layout, layouts) of the style for n eyes: the layout asked for when the style takes it, else the style's own default. strict: a layout the
    style does not take is a 400 (one style asked for), else (a batch) it simply does not apply to this style."""
    layouts = catalogue.layouts_for(style, n)
    if wanted and wanted not in layouts and strict:
        raise L.ClientError("Unknown layout for this style.")
    return (wanted if wanted in layouts else layouts[0]), layouts


def _drawn(pv, plan):
    """(design_used, fallback) of a picture: what the preview itself reports (the design it drew, the fallback its render took), else what the plan says
    (resolve: no pixels)."""
    d = (getattr(pv, "design", None) if pv is not None else None) or (plan or {}).get("design_used")
    f = ((getattr(pv, "log", None) or {}).get("fallback") if pv is not None else None) or (plan or {}).get("fallback")
    return d, (f if isinstance(f, str) and f else None)


def _bar_refusal(e):
    """True for an engine's refusal of eyes it does not draw: the collision family raises NotOffered (a ValueError that carries why == "bar_pupil")
    when an iris of the set has a horizontal bar pupil, whatever the sealed profile said (a profile is the page's measurement at enhance; the engine
    measures again on the very pixels). Told by its why, so that compose imports no family."""
    return isinstance(e, ValueError) and getattr(e, "why", None) == "bar_pupil"


def _takes_check(style, n):
    """Does the family of this style take preview(check=...)? Read from its signature, never learnt by a TypeError: a TypeError raised INSIDE a render
    is a bug that must be seen, not a reason to draw the picture a second time."""
    from _lib import styles as ST
    try:
        params = inspect.signature(ST.family(catalogue.engine_for(style, n)["module"]).preview).parameters
    except Exception:  # noqa: a family that cannot be read is drawn without the keyword (and ST.preview says what is wrong with it)
        return False
    return "check" in params or any(p.kind is p.VAR_KEYWORD for p in params.values())


def _plan(style, spec, profiles):
    from _lib import styles as ST
    try:
        return ST.resolve(spec, profiles)
    except Exception:  # noqa: a plan that cannot be made does not stop the preview; the reply then says nothing of design_used
        return {}


def _plan8(style, n, layout, opts, eye_ids, metas):
    """The plan identity of this picture (steps.make_plan: pure, no pixel, no storage), or None when no plan can be made (the reply then says nothing)."""
    try:
        from _lib.styles import steps as SP
        eyes = [{"eye_id": i, "profile": (m or {}).get("profile").rec if isinstance(m, dict) and m.get("profile") is not None else None}
                for i, m in zip(eye_ids, metas)]
        return SP.make_plan({"style": style, "layout": layout, "eyes": n, "opts": opts}, eyes)["plan8"]
    except Exception:  # noqa
        return None


def _qa_of(pv):
    graded = pv.graded
    if isinstance(graded, list) and len(graded) > 1:
        eyes = [L.colour_qa(f"compose eye {i + 1}/{len(graded)}", graded=L.Image.fromarray(g)) for i, g in enumerate(graded)]
        return {"ok": all(q["ok"] for q in eyes), "eyes": eyes}
    return L.colour_qa("compose", graded=L.Image.fromarray(graded[0]))


def _selfcheck_of(pv):
    sc = getattr(pv, "selfcheck", None)
    if not isinstance(sc, dict):
        return None
    return {"ok": bool(sc.get("ok")), "failed": sorted(k for k, c in (sc.get("checks") or {}).items() if isinstance(c, dict) and not c.get("ok", True))}


def _jpeg(img, q=90):
    return L.pil_to_b64(img, "JPEG", q)


# ----------------------------------------------------------------------------- the reply's shared parts
def _pick_reply(cat):
    return {"id": cat["pick"], "reason": cat["reason"]} if cat["pick"] else None


def _event_fields(req, style, n, layout, fmt, size, gate, qa_ok, pick_id, look, fallback, clean=False, tile=False):
    f = {"style": style, "eyes": n, "layout": layout, "format": fmt, "clean": bool(clean), "gate": gate, "size": size,
         "stage": catalogue.stage_of(style, n), "pick": style == pick_id, "retake": req["retake"], "lang": req["lang"]}
    if qa_ok is not None:
        f["qa_ok"] = bool(qa_ok)
    if tile:
        f["tile"] = True
    if look:
        f["look"] = look
    if fallback:
        f["fallback"] = fallback
    if req["market"]:
        f["market"] = req["market"]
    return f


# ----------------------------------------------------------------------------- one style
def _one_engine(req, style, n, plains, metas, cat, admin, clean, t0):
    """One style of the v3 engine at req['size']: the clean render, the plan, then the preview watermark (unless a signed unlock ticket says the file is
    paid for: nothing mints one yet), the colour QA on the graded frame, the event and the reply."""
    from _lib import styles as ST
    layout, layouts = _layout_for(style, n, req["layout"], True)
    eng, canvas, word = _engine_canvas(style, n, req["fmt"])
    opts = _tile_opts(req["opts"], style, n, admin)
    size = req["size"]
    need, mb = _need([style], n, size, {style: opts})
    left = L.time_left()
    if need > left - 1.0:
        raise _refuse(503, "busy_retry", "busy_retry", True, 3)
    t_eyes = time.time()
    eyes = _eyes_for(plains, metas, [style], n)
    spec = _spec(style, n, eyes, metas, req, canvas, layout, opts)
    plan = _plan(style, spec, spec["profiles"])
    kw = {"check": True} if size >= PREVIEW_SIZE and _takes_check(style, n) else {}       # the self check of a 1024 px preview, for the families that have one
    try:
        with GUARD.slot(est_mb=mb, est_s=need, left=left):
            t_draw = time.time()
            pv = ST.preview(eyes, spec, size=size, **kw)
            t_done = time.time()
    except GUARD.Busy as b:
        raise _refuse(503, "busy_retry", "busy_retry", True, max(2, min(20, int(-(-(b.eta_s if b.eta_s is not None else 3.0) // 1))))) from None
    except ValueError as e:
        if _bar_refusal(e):                           # the engine's own look at the pixels refused what the sealed profile let through: the tile's own answer
            raise _refuse(422, "style_unavailable", "bar_pupil", False, None, why="bar_pupil", style=style) from None
        raise
    img = pv.img if clean else ST.watermarked(pv, req["lang"], note=req["title"] or None, n_eyes=n)
    qa = _qa_of(pv)
    design, fallback = _drawn(pv, plan)
    canvas = pv.fmt or canvas or eng["canvases"][0]
    word = "wallpaper" if canvas == "9:19.5" else "artwork"
    pick_id = cat["pick"]
    if not admin:
        E.record("compose", tiles=1, **_event_fields(req, style, n, layout, word, size, _gate_code(style, n, metas), qa.get("ok"), pick_id,
                                                    opts.get("look"), fallback, clean))
    return {"ok": True, "style": style, "layout": layout, "layouts": list(layouts), "format": word, "canvas": canvas,
            "count": n, "width": img.size[0], "height": img.size[1], "image": _jpeg(img),
            "styles": list(catalogue.previewable_ids(n, admin)), "qa": qa, "eyes": _eyes_reply(metas), "tiles": cat["tiles"], "pick": _pick_reply(cat),
            "size": size, "opts": opts, "design_used": design, "fallback": fallback, "plan8": _plan8(style, n, layout, opts, spec["eye_ids"], metas),
            "engine": _engine_facts(), "selfcheck": _selfcheck_of(pv),
            "timing": {"eyes_ms": int((t_draw - t_eyes) * 1000), "render_ms": int((t_done - t_draw) * 1000), "total_ms": int((time.time() - t0) * 1000)}}


def _one_legacy(req, style, n, body, opened, metas, cat, admin, clean, t0):
    """One style of the legacy engine (api/_lib/iris.py), as it has always been made: same picture, same fields, and the additive ones of the v3 reply."""
    ims, _metas, _raws = _irises_full(body, opened)
    layout, layouts = _layout_for(style, n, req["layout"], True)
    fmt = _choice(req["fmt"], L.FORMATS, L.FORMATS[0])
    size = req["size"]
    # the watermark is the only thing separating a preview from the product, so the caller does not get to
    # turn it off: only a server-signed unlock ticket can, and nothing mints one yet
    keep = {}
    out = L.compose_multi(ims, style=style, title=_text(body.get("title"), 40) or None, names=_legacy_names(body.get("names")),
                          watermark=not clean, r_frac=L.iris_radius_frac(_pad(body.get("pad"))), size=size,
                          layout=layout, fmt=fmt, keep=keep)
    # colour QA on the graded disks themselves (before background, glow and watermark): is the pupil core neutral?
    # The ring colour was already checked in /api/enhance. Logged, never blocking.
    graded = keep.get("graded")
    if isinstance(graded, list):
        eyes = [L.colour_qa(f"compose eye {i + 1}/{n}", graded=g) for i, g in enumerate(graded)]
        qa = {"ok": all(q["ok"] for q in eyes), "eyes": eyes}
    else:
        qa = L.colour_qa("compose", graded=graded)
    if not admin:
        E.record("compose", tiles=1, **_event_fields(req, style, n, layout, fmt, size, _gate_code(style, n, metas), qa.get("ok"), cat["pick"], None, None, clean))
    return {"ok": True, "style": style, "layout": layout, "layouts": list(layouts), "format": fmt,
            "count": n, "width": out.size[0], "height": out.size[1], "image": _jpeg(out),
            "styles": list(catalogue.previewable_ids(n, admin)), "qa": qa, "eyes": _eyes_reply(metas), "tiles": cat["tiles"], "pick": _pick_reply(cat),
            "size": size, "opts": {}, "design_used": style, "fallback": None, "plan8": _plan8(style, n, layout, {}, [(m or {}).get("eye_id") or "" for m in metas], metas),
            "engine": _engine_facts(), "selfcheck": None,
            "timing": {"total_ms": int((time.time() - t0) * 1000)}}


# ----------------------------------------------------------------------------- a batch of tiles
def _batch(req, styles, n, body, opened, cat, admin, t0):
    """The tiles of several styles on ONE eye preparation. styles: the ids asked for, already resolved ("pick" is the recommended id) and known to be
    previewable. A style the eyes cannot take is reported on its tile (available false, why), never drawn. The cost of the whole call is estimated
    before a pixel is drawn (422 too_many_styles) and the call takes the heavy render slot of the instance."""
    from _lib import styles as ST
    raw, metas, plains = opened
    rows = {r["id"]: r for r in cat["tiles"]}
    for s in styles:                                  # a style the list leaves out (held, no tile slot) still has a row for its own tile
        if s not in rows:
            r = catalogue.tile_row(s, n, _recs(metas), admin)
            r["pick"] = False
            cat["tiles"].append(r)
            rows[s] = r
    draw = [s for s in styles if rows[s]["available"]]
    opts = {s: _tile_opts(req["opts"], s, n, admin) for s in draw}
    size = req["size"]
    fit = 0
    for k in range(1, len(draw) + 1):
        if _need(draw[:k], n, size, opts)[0] > TILES_BUDGET_S:
            break
        fit = k
    if fit < len(draw):
        raise _refuse(422, "too_many_styles", "too_many_styles", False, None, max=fit)
    need, mb = _need(draw, n, size, opts) if draw else (0.0, 0.0)
    left = L.time_left()
    if draw and need > left - 1.0:
        raise _refuse(503, "busy_retry", "busy_retry", True, 3)
    charged, charged_on = 0, _utc_day()
    if draw and not admin:
        if not _tiles_room(len(draw)):
            raise _refuse(503, "tiles_paused", "tiles_paused", True, min(3600, max(60, _until_midnight())))
        charged = len(draw)
    made, timing, refused = {}, {}, set()
    spent = 0                                         # the tiles the call really drew: the ceiling keeps only those (a busy answer or a failure draws none)
    t_eyes = time.time()
    if draw:
        legacy = [s for s in draw if catalogue.is_legacy(s)]
        v3 = [s for s in draw if not catalogue.is_legacy(s)]
        try:
            with GUARD.slot(est_mb=mb, est_s=need, left=left):
                if v3:
                    eyes = _eyes_for(_plains(raw, plains), metas, v3, n)
                    specs = {}
                    for s in v3:
                        layout, _lay = _layout_for(s, n, req["layout"], False)
                        _e, canvas, word = _engine_canvas(s, n, req["fmt"])
                        specs[s] = _spec(s, n, eyes, metas, req, canvas, layout, opts[s])
                    # the spec of each style is its own (its layout, its canvas, its options): the first is the base and what differs goes per style. A family
                    # draws the tiles() of a style at the layout and canvas of its own defaults, so when the request names a layout or a format the styles
                    # are drawn one by one with theirs
                    base = dict(specs[v3[0]])
                    per_style = {s: {k: v for k, v in sp.items() if k != "style" and base.get(k) != v} for s, sp in specs.items()}
                    if req["layout"] or req["fmt"]:
                        for s in v3:
                            per_style[s].update(layout=specs[s]["layout"], canvas=specs[s]["canvas"])
                    # one call of styles.tiles per engine family, each with the very base and per_style dicts of the whole call (what tiles() does with them
                    # is per family anyway): a family that refuses these eyes (the collision family, a bar pupil the profile did not show) refuses its own
                    # tiles only, the other families' tiles of the batch are still made
                    groups = {}
                    for s in v3:
                        groups.setdefault(catalogue.engine_for(s, n)["module"], []).append(s)
                    pvs = {}
                    for ids in groups.values():
                        try:
                            pvs.update(ST.tiles(eyes, ids, base, size=size, per_style={s: per_style[s] for s in ids}))
                        except ValueError as e:
                            if not _bar_refusal(e):
                                raise
                            refused.update(ids)
                            continue
                        spent += len(ids)
                    for s in v3:
                        if s in refused:
                            continue
                        t_w = time.time()
                        pv = pvs[s]
                        made[s] = {"img": ST.watermarked(pv, req["lang"], note=req["title"] or None, n_eyes=n), "spec": specs[s], "plan": _plan(s, specs[s], specs[s]["profiles"]),
                                   "layout": specs[s]["layout"], "canvas": pv.fmt or specs[s]["canvas"] or catalogue.engine_for(s, n)["canvases"][0], "pv": pv}
                        timing[s] = int(((pv.times or {}).get("total", 0.0) + (time.time() - t_w)) * 1000)      # the design's own render and its watermark
                if legacy:
                    ims = _irises_full(body, opened)[0]
                    for s in legacy:
                        t_l = time.time()
                        layout, _lay = _layout_for(s, n, req["layout"], False)
                        out = L.compose_multi(ims, style=s, title=_text(body.get("title"), 40) or None, names=_legacy_names(body.get("names")), watermark=True,
                                              r_frac=L.iris_radius_frac(_pad(body.get("pad"))), size=size, layout=layout,
                                              fmt=_choice(req["fmt"], L.FORMATS, L.FORMATS[0]))
                        made[s] = {"img": out, "spec": None, "plan": {"design_used": s, "fallback": None}, "layout": layout, "pv": None,
                                   "canvas": _choice(req["fmt"], L.FORMATS, L.FORMATS[0])}
                        timing[s] = int((time.time() - t_l) * 1000)
                        spent += 1
        except GUARD.Busy as b:
            raise _refuse(503, "busy_retry", "busy_retry", True, max(2, min(20, int(-(-(b.eta_s if b.eta_s is not None else 3.0) // 1))))) from None
        finally:
            _tiles_refund(charged - spent, charged_on)    # a busy answer, a refusal by the engine or a failure before the tiles were drawn costs the day nothing
    for s in refused:                                    # an engine's own refusal of a tile the profile let through: the tile says so, as a tile the profile held back would
        rows[s].update(available=False, why="bar_pupil", pick=False)
    if cat["pick"] in refused:
        cat["pick"] = catalogue.pick_for(n, _recs(metas), skip=refused)
        cat["reason"] = catalogue.pick_reason(cat["pick"], catalogue.set_class(_recs(metas)))
        for r in cat["tiles"]:
            r["pick"] = r["id"] == cat["pick"]
        cat["tiles"].sort(key=lambda r: not r["pick"])
    for s, m in made.items():
        r = rows[s]
        design, fallback = _drawn(m["pv"], m["plan"])
        ids = m["spec"]["eye_ids"] if m["spec"] else [(x or {}).get("eye_id") or "" for x in metas]
        r.update(image=_jpeg(m["img"]), width=m["img"].size[0], height=m["img"].size[1], layout=m["layout"], canvas=m["canvas"], design_used=design, fallback=fallback,
                 plan8=_plan8(s, n, m["layout"], opts.get(s) or {}, ids, metas))
    if made and not admin:
        pick_id = cat["pick"]
        gate = {s: _gate_code(s, n, metas) for s in made}
        fields = [_event_fields(req, s, n, made[s]["layout"], "artwork", size, gate[s], None, pick_id, opts.get(s, {}).get("look"), (rows[s].get("fallback")), False, True)
                  for s in made]
        for f, s in zip(fields, made):
            f["ms"] = timing.get(s)
        fields[0]["tiles"] = len(made)                # the request is counted once: by its first event
        E.record_many("compose", fields)
    return {"ok": True, "batch": True, "count": n, "size": size, "format": _choice(req["fmt"], L.FORMATS, L.FORMATS[0]),
            "tiles": cat["tiles"], "pick": _pick_reply(cat), "styles": list(catalogue.previewable_ids(n, admin)), "eyes": _eyes_reply(metas),
            "engine": _engine_facts(), "timing": {"tiles_ms": timing, "total_ms": int((time.time() - t0) * 1000), "eyes_ms": int((time.time() - t_eyes) * 1000)}}


# ----------------------------------------------------------------------------- the help beacon
def _help(body):
    """One click on the manual route of the retake state (e-mail your best photos, the owner looks at them): a count and nothing else."""
    if body.get("route") != "manual":
        raise L.ClientError("route is manual.")
    why = body.get("why")
    why = why if isinstance(why, str) and 1 <= len(why) <= 40 and all(c.islower() or c.isdigit() or c in "_.-" for c in why) and (why[0].islower() or why[0].isdigit()) else "unknown"
    lang = body.get("lang") if body.get("lang") in L.PAGE_LANGS else "en"
    E.record("help", route="manual", eyes=_int(body.get("eyes"), 1, L.MULTI_MAX, 1), why=why, lang=lang, _wait=0.5)
    return {"ok": True, "counted": True}


# ----------------------------------------------------------------------------- the handler
def compose(body, bearer=""):
    if not isinstance(body, dict):
        raise L.ClientError("Send a JSON object.")
    if body.get("action") == "help":
        return _help(body)
    t0 = time.time()
    raw, metas, plains = _open(body)
    n = len(raw)
    req = _request(body)
    admin = req["lab"] and _is_admin(bearer)
    recs = _recs(metas)
    cat = catalogue.tile_list(n, recs, admin)
    # the styles asked for: "pick" is the recommended tile; an id that is not the registry's is a 400, one a customer may not have a 422
    styles = []
    for s in req["styles"]:
        if s == PICK:
            if not cat["pick"]:
                raise _refuse(422, "style_unavailable", "stage", False, None, why="stage", style=PICK)
            s = cat["pick"]
        why = catalogue.why_unavailable(s, n, recs, admin)
        if why == "unknown":
            raise L.ClientError("Unknown style.")
        if why in ("stage", "eyes"):
            raise _refuse(422, "style_unavailable", why, False, None, why=why, style=s)
        if why and not req["batch"]:
            raise _refuse(422, "style_unavailable", why, False, None, why=why, style=s)
        if s not in styles:                             # "pick" may name a style that was asked for by its id too
            styles.append(s)
    clean = (not req["batch"]) and L.check_ticket(body.get("unlock"), kind="unlock")
    if req["batch"]:
        return _batch(req, styles, n, body, (raw, metas, plains), cat, admin, t0)
    style = styles[0]
    if catalogue.is_legacy(style):
        return _one_legacy(req, style, n, body, (raw, metas, plains), metas, cat, admin, clean, t0)
    return _one_engine(req, style, n, _plains(raw, plains), metas, cat, admin, clean, t0)


def handle(req):
    box = store._StatusReq(req)
    bearer = _bearer(req)

    def wrapped(body):
        try:
            return compose(body, bearer)
        except store.Answer as a:                 # a refusal that is not a 400: the reply carries its own status
            box.status, box.retry_after = a.status, a.retry_after
            return dict(a.body)
    L.run(box, wrapped)


class handler(BaseHTTPRequestHandler):
    def do_POST(self): handle(self)
