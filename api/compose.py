# -*- coding: utf-8 -*-
"""POST /api/compose  {iris: b64 enhanced iris square, style, title, names, watermark, pad}
Places the iris on the chosen style background with typography and (optionally) a preview watermark."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import BaseHTTPRequestHandler
from _lib import iris as L

def compose(body):
    im = L.b64_to_pil(body["iris"])
    s = min(im.size); im = im.crop((0, 0, s, s))
    style = body.get("style") or "celestial_gold"
    if style not in L.STYLES: style = "celestial_gold"
    # the watermark is the only thing separating a preview from the product, so the caller does not get to
    # turn it off: only a server-signed unlock ticket can, and nothing mints one yet
    clean = L.check_ticket(body.get("unlock"), kind="unlock")
    keep = {}
    out = L.compose(im, style=style, title=(body.get("title") or "")[:40] or None, names=(body.get("names") or "")[:60],
                    watermark=not clean, r_frac=L.iris_radius_frac(float(body.get("pad") or 1.12)), keep=keep)
    # colour QA on the graded disk itself (before background, glow and watermark): is the pupil core neutral?
    # The ring colour was already checked in /api/enhance. Logged, never blocking.
    qa = L.colour_qa("compose", graded=keep.get("graded"))
    return {"ok": True, "style": style, "image": L.pil_to_b64(out, "JPEG", 90), "styles": list(L.STYLES.keys()), "qa": qa}

def handle(req): L.run(req, compose)

class handler(BaseHTTPRequestHandler):
    def do_POST(self): handle(self)
