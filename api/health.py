# -*- coding: utf-8 -*-
"""GET /api/health - shows which pieces are configured on this deployment (no secrets)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import BaseHTTPRequestHandler
from _lib import iris as L

def handle(req):
    info = {"ok": True, "gemini_key": bool(os.environ.get("GEMINI_API_KEY", "").strip()),
            "blob_store": bool(os.environ.get("BLOB_READ_WRITE_TOKEN", "").strip()),
            "vision_model": L.VISION_MODEL, "image_model": L.IMAGE_MODEL,
            "sr_model": os.path.exists(os.path.join(L.ASSETS, "models", "realesr_general_x4v3.onnx")),
            "styles": list(L.STYLES.keys())}
    L.send_json(req, 200, info)

class handler(BaseHTTPRequestHandler):
    def do_GET(self): handle(self)
