# -*- coding: utf-8 -*-
"""POST /api/compose
  {sealed: [sealed, ...] 1-8 restored irises as /api/enhance sealed them ("sealed", or one of its "sealed_sizes"),
   in canvas order; opened here (api/_lib/preview.py), the page never holds them in the clear.
   Old pages: irises: [b64, ...] 1-8 enhanced iris squares (or iris: b64, the one-eye form), still accepted for one
   release; sealed wins when both are sent.
   layout, format ("artwork" | "wallpaper"), style, title, names, pad, unlock}
Places the eyes on the chosen style background with typography and (unless unlocked) a preview watermark, whose words
are drawn iris.WATERMARK_IRIS times as strong on every iris disc (the slider's display copy strength), so neither the
artwork box nor its "Save preview" file is a clean iris.
Reply: {ok, style, layout, layouts, format, count, width, height, image (JPEG b64), styles, qa, eyes}
eyes: one entry per eye, {eye, eye_id, cls, pupil, gate {lid, fill}}: what the eye's seal says (api/_lib/preview.py seal v2, the
profile measured at /api/enhance): the eye id, the colour class, the pupil class and the ok of each restoration gate rule (true,
false, or null = unknown: a version 1 seal, or a profile that was not measured; and null for an old page's plain irises). The page
ignores it (the picker work package reads it); the compose event carries the set-level gate.
A style of the v3 engine (the registry's engine module is not "legacy": api/_lib/styles) is drawn by that engine, one eye of the singles
family so far, and only while its effective stage lets a customer see it (preview or live; a laboratory style is the admin page's:
api/_lib/ops.py styles_lab). The picture is the engine's clean render with the same preview watermark, and the reply has the same fields
(format is "artwork" or "wallpaper" as asked; canvas, the engine's own canvas id, is added). The seed of a picture is the bytes of the iris
it was made from (the engine's step A), so the same restored iris gives the same picture every time."""
import os, sys, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import BaseHTTPRequestHandler
from _lib import iris as L
from _lib import catalogue
from _lib import events as E   # the admin panel's usage events (no personal data)
from _lib import preview as P
from _lib.styles import gate as GATE   # the restoration gate: the set-level result of the eyes of one request

PREVIEW_SIZE = 1024          # longest side of the artwork this endpoint returns. Kept at 1024 when the iris preview
                             # went down to 800 px (2026-09-29): at 900 the footer line of a 21:9 row of four eyes
                             # drops from 9 to 8 px and no longer reads; the badge, title and names read at both
MAX_SIDE = 4096              # the 4K render is 4096 px: a larger image is not an iris this site made
MIN_SIDE = 64
WORK_SIDE = 2048             # a 1024 px preview never needs more than this, so a larger iris is shrunk on arrival.
                             # Up to 2048 px the preview is exactly what the engine makes of the iris as sent; a
                             # 3000-4096 px iris is graded from its 2048 px copy (a few levels off grading it whole,
                             # measured up to 19). The site sends the 1024 px squares /api/enhance returns.
MAX_TOTAL_B64 = 4_400_000    # Vercel refuses a request body over 4.5 MB before this code runs; this says it in words

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

def _irises(body):
    """The iris squares of a request (the form every caller used before the eye profile): _irises_full(body)[0]."""
    return _irises_full(body)[0]

def _irises_full(body):
    """(squares, metas, raws): the iris squares of a request, per eye what its seal said (preview.unseal_full's meta: v, kind, eye_id,
    profile; None for an old page's plain irises) and the bytes of the image as it was sent (opened from its seal, or decoded): the engine
    of the v3 styles seeds from them and builds its own eye from them, so every byte is the very one the eye id was made from."""
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

def _eyes_reply(metas):
    """The reply's "eyes": what each eye's seal says (see the module text)."""
    rows = []
    for i, m in enumerate(metas, 1):
        prof = m.get("profile") if isinstance(m, dict) else None
        ok = {r: (prof.gate(r)["ok"] if prof is not None else None) for r in GATE.RULES}
        rows.append({"eye": i, "eye_id": m.get("eye_id") if isinstance(m, dict) else None,
                     "cls": prof.cls if prof is not None else None, "pupil": prof.pupil_cls if prof is not None else None, "gate": ok})
    return rows

def _gate_code(style, n, metas):
    """The set-level gate code of the request for the event: ok, unknown, or the reason code of the first failing eye, under the rule
    set the style's engine entry names (the collision rule when the style has none)."""
    rule = ((catalogue.engine_for(style, n) or {}).get("gate_rules")) or "lid"
    r = GATE.set_result([(m or {}).get("profile") for m in metas], rule)
    return "ok" if r["ok"] is True else ("unknown" if r["ok"] is None else r["first"]["why"])

TEXT_RAW_MAX = 1000          # characters of one customer text field that are read at all (the preview keeps 60 of the names and 20 of the date): the body
                             # may be 4 MB, and cleaning it letter by letter cost 7.5 s of CPU before the picture was drawn (the legacy path cuts first)
TEXT_PARTS_MAX = 16          # parts of a names list that are read (the old wire form holds one name per eye, eight at most)

def _engine_text(value, limit=None):
    """The customer's names as the v3 engine draws them: cleaned, the names as one lockup line, and without a letter the artwork font
    cannot draw (it would print as an empty box; checkout refuses such a name, a free preview just leaves the letter out). The names come as
    text ("Anna;Max") or as a list of texts, anything else is no names; only the first TEXT_RAW_MAX characters of a field are read."""
    from _lib.styles import text as TX
    if isinstance(value, (list, tuple)):
        value = [v[:TEXT_RAW_MAX] for v in value[:TEXT_PARTS_MAX] if isinstance(v, str)]
    elif isinstance(value, str):
        value = value[:TEXT_RAW_MAX]
    else:
        return ""
    parts = [p for p in (TX.clean("".join(ch for ch in n if not TX.unsupported(ch))) for n in TX.split_names(value)) if p]
    out = TX.lockup(parts)
    return out[:limit] if limit else out

def _engine_date(value, limit=None):
    """The customer's date as the v3 engine draws it: one cleaned line, as typed (a semicolon or a line break does not separate dates: the paid
    file draws TX.clean(date) as well), without a letter the artwork font cannot draw. Only the first TEXT_RAW_MAX characters are read."""
    from _lib.styles import text as TX
    if not isinstance(value, str):
        return ""
    out = TX.clean("".join(ch for ch in value[:TEXT_RAW_MAX] if not TX.unsupported(ch)))
    return out[:limit] if limit else out

def _engine_canvas(style, n, fmt_in):
    """(engine entry, the canvas id, the legacy format word) of a request for a v3 style: the format asked ("artwork", "wallpaper" or a canvas id
    of the engine) read as a canvas the engine draws, else its own default."""
    eng = catalogue.engine_for(style, n)
    canvases = eng["canvases"]
    canvas = fmt_in if fmt_in in canvases else ("9:19.5" if fmt_in == "wallpaper" and "9:19.5" in canvases else canvases[0])
    return eng, canvas, ("wallpaper" if canvas == "9:19.5" else "artwork")

def _compose_engine(body, style, n, metas, raws, layouts, clean):
    """One eye of a v3 style, drawn by the engine of api/_lib/styles: the clean render, then the preview watermark (unless a signed unlock
    ticket says the file is paid for: nothing mints one yet), the colour QA on the graded frame, the event and the reply of compose()."""
    if n != 1:
        raise L.ClientError("That style draws one eye.")
    from _lib import styles as ST
    from _lib.styles import core as SCORE
    _eng, canvas, word = _engine_canvas(style, n, body.get("format"))
    meta = metas[0] if isinstance(metas[0], dict) else {}
    eye = SCORE.Iris(raws[0], "compose", max_side=WORK_SIDE, eye_id=meta.get("eye_id"))
    spec = {"style": style, "layout": layouts[0], "eyes": n, "canvas": canvas, "names": _engine_text(body.get("names"), 60),
            "date": _engine_date(body.get("date"), 20), "profiles": [meta.get("profile")]}
    pv = ST.preview([eye], spec, size=PREVIEW_SIZE, watermark=not clean)
    qa = L.colour_qa("compose", graded=L.Image.fromarray(pv.graded[0]))
    E.record("compose", style=style, eyes=n, layout=layouts[0], format=word, clean=bool(clean), qa_ok=bool(qa.get("ok")),
             gate=_gate_code(style, n, metas))
    return {"ok": True, "style": style, "layout": layouts[0], "layouts": list(layouts), "format": word, "canvas": canvas,
            "count": n, "width": pv.img.size[0], "height": pv.img.size[1], "image": L.pil_to_b64(pv.img, "JPEG", 90),
            "styles": list(catalogue.previewable_ids(n)), "qa": qa, "eyes": _eyes_reply(metas)}

def compose(body):
    if not isinstance(body, dict):
        raise L.ClientError("Send a JSON object.")
    ims, metas, raws = _irises_full(body)
    n = len(ims)
    style = _choice(body.get("style"), catalogue.previewable_ids(n), catalogue.DEFAULT_STYLE)
    layouts = catalogue.layouts_for(style, n)
    layout = _choice(body.get("layout"), layouts, None) or layouts[0]
    fmt = _choice(body.get("format"), L.FORMATS, L.FORMATS[0])
    if not catalogue.is_legacy(style):
        # a style of the v3 engine (previewable_ids lists only those a customer may see and whose engine is in the repository)
        return _compose_engine(body, style, n, metas, raws, layouts, L.check_ticket(body.get("unlock"), kind="unlock"))
    # the watermark is the only thing separating a preview from the product, so the caller does not get to
    # turn it off: only a server-signed unlock ticket can, and nothing mints one yet
    clean = L.check_ticket(body.get("unlock"), kind="unlock")
    keep = {}
    out = L.compose_multi(ims, style=style, title=_text(body.get("title"), 40) or None, names=_text(body.get("names"), 60),
                          watermark=not clean, r_frac=L.iris_radius_frac(_pad(body.get("pad"))), size=PREVIEW_SIZE,
                          layout=layout, fmt=fmt, keep=keep)
    # colour QA on the graded disks themselves (before background, glow and watermark): is the pupil core neutral?
    # The ring colour was already checked in /api/enhance. Logged, never blocking.
    graded = keep.get("graded")
    if isinstance(graded, list):
        eyes = [L.colour_qa(f"compose eye {i + 1}/{n}", graded=g) for i, g in enumerate(graded)]
        qa = {"ok": all(q["ok"] for q in eyes), "eyes": eyes}
    else:
        qa = L.colour_qa("compose", graded=graded)
    E.record("compose", style=style, eyes=n, layout=layout, format=fmt, clean=bool(clean), qa_ok=bool(qa.get("ok")),
             gate=_gate_code(style, n, metas))
    return {"ok": True, "style": style, "layout": layout, "layouts": list(layouts), "format": fmt,
            "count": n, "width": out.size[0], "height": out.size[1], "image": L.pil_to_b64(out, "JPEG", 90),
            "styles": list(catalogue.previewable_ids(n)), "qa": qa, "eyes": _eyes_reply(metas)}

def handle(req): L.run(req, compose)

class handler(BaseHTTPRequestHandler):
    def do_POST(self): handle(self)
