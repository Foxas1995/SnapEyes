# -*- coding: utf-8 -*-
"""POST /api/compose
  {irises: [b64, ...] 1-8 enhanced iris squares, in canvas order  (or iris: b64, the one-eye form, still accepted),
   layout, format ("artwork" | "wallpaper"), style, title, names, pad, unlock}
Places the eyes on the chosen style background with typography and (unless unlocked) a preview watermark.
Reply: {ok, style, layout, layouts, format, count, width, height, image (JPEG b64), styles, qa}"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import BaseHTTPRequestHandler
from _lib import iris as L

PREVIEW_SIZE = 1024          # longest side of the artwork this endpoint returns
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
    raw = body.get("irises")
    if (raw is None or (isinstance(raw, list) and not raw)) and body.get("iris") is not None:
        raw = [body.get("iris")]          # the one-eye form, also when a client sends it next to an empty list
    if not isinstance(raw, list) or not 1 <= len(raw) <= L.MULTI_MAX:
        raise L.ClientError(f"Send between 1 and {L.MULTI_MAX} iris images.")
    if not all(isinstance(s, str) and s for s in raw):
        raise L.ClientError("Each iris image must be sent as base64 text.")
    if sum(len(s) for s in raw) > MAX_TOTAL_B64:
        raise L.ClientError("Those images are too large together. Send each one at 1024 pixels.")
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
    return out

def compose(body):
    if not isinstance(body, dict):
        raise L.ClientError("Send a JSON object.")
    ims = _irises(body)
    n = len(ims)
    style = _choice(body.get("style"), L.STYLES, "celestial_gold")
    layout = L.multi_layout(n, _choice(body.get("layout"), L.layouts_for(n), None))
    fmt = _choice(body.get("format"), L.FORMATS, L.FORMATS[0])
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
    return {"ok": True, "style": style, "layout": layout, "layouts": list(L.layouts_for(n)), "format": fmt,
            "count": n, "width": out.size[0], "height": out.size[1], "image": L.pil_to_b64(out, "JPEG", 90),
            "styles": list(L.STYLES.keys()), "qa": qa}

def handle(req): L.run(req, compose)

class handler(BaseHTTPRequestHandler):
    def do_POST(self): handle(self)
