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
    out = L.compose(im, style=style, title=(body.get("title") or "")[:40] or None, names=(body.get("names") or "")[:60],
                    watermark=bool(body.get("watermark", True)), r_frac=L.iris_radius_frac(float(body.get("pad") or 1.12)))
    return {"ok": True, "style": style, "image": L.pil_to_b64(out, "JPEG", 90), "styles": list(L.STYLES.keys())}

def handle(req): L.run(req, compose)

class handler(BaseHTTPRequestHandler):
    def do_POST(self): handle(self)
