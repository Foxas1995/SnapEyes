# -*- coding: utf-8 -*-
"""End-to-end test of the API flow the browser performs, against the local dev API (or a deployed URL).
python scripts/test_flow.py <photo> [base_url]  -> writes outputs next to the photo in ./flowtest/"""
import os, sys, io, json, time, base64
import requests
from PIL import Image, ImageOps

args = [a for a in sys.argv[1:] if not a.startswith("--")]
photo = args[0]; base = args[1] if len(args) > 1 else "http://localhost:5050"
out = os.path.join(os.path.dirname(os.path.abspath(photo)), "flowtest"); os.makedirs(out, exist_ok=True)
tag = os.path.splitext(os.path.basename(photo))[0]
def b64(im, fmt="JPEG", q=92):
    b = io.BytesIO(); im.save(b, fmt, quality=q) if fmt == "JPEG" else im.save(b, fmt); return base64.b64encode(b.getvalue()).decode()
def dec(s): return Image.open(io.BytesIO(base64.b64decode(s))).convert("RGB")
def post(path, payload):
    t = time.time(); r = requests.post(base + path, json=payload, timeout=180); j = r.json(); j["_t"] = round(time.time() - t, 1); return j

orig = ImageOps.exif_transpose(Image.open(photo)).convert("RGB"); W, H = orig.size
small = orig.copy(); small.thumbnail((1600, 1600), Image.LANCZOS)
a = post("/api/analyze", {"image": b64(small, "JPEG", 90), "origWidth": W, "origHeight": H})
print("analyze:", json.dumps({k: v for k, v in a.items() if k != "preview"})[:600])
if not a.get("ok"): sys.exit(1)
cx, cy, r = a["iris"]["cx"] * W, a["iris"]["cy"] * H, a["iris"]["r"] * W
S = int(2 * r * a["pad"]); x0, y0 = int(cx - S / 2), int(cy - S / 2)
crop = Image.new("RGB", (S, S)); crop.paste(orig, (-x0, -y0))
if S > 1400: crop = crop.resize((1400, 1400), Image.LANCZOS)
crop.save(os.path.join(out, f"{tag}_0_clientcrop.jpg"), quality=95)
d = post("/api/deglare", {"crop": b64(crop, "JPEG", 95), "pad": a["pad"], "glare_boxes": a.get("glare_boxes_crop", [])})
print("deglare:", {k: v for k, v in d.items() if k != "crop"}); dec(d["crop"]).save(os.path.join(out, f"{tag}_1_deglared.jpg"), quality=95)
e = post("/api/enhance", {"crop": d["crop"], "mode": "faithful", "pad": a["pad"], "session": "test-" + tag, "consent": True, "meta": a["quality"]})
print("enhance faithful:", {k: v for k, v in e.items() if k != "image"}); dec(e["image"]).save(os.path.join(out, f"{tag}_2_faithful.jpg"), quality=95)
c = post("/api/compose", {"iris": e["image"], "style": "celestial_gold", "names": "Mantas", "watermark": True, "pad": a["pad"]})
print("compose:", {k: v for k, v in c.items() if k != "image"}); dec(c["image"]).save(os.path.join(out, f"{tag}_3_art_celestial.jpg"), quality=95)
c2 = post("/api/compose", {"iris": e["image"], "style": "deep_nebula", "names": "Mantas", "watermark": False, "pad": a["pad"]})
dec(c2["image"]).save(os.path.join(out, f"{tag}_3_art_nebula_clean.jpg"), quality=95)
if "--artistic" in sys.argv:
    ar = post("/api/enhance", {"crop": d["crop"], "mode": "artistic", "pad": a["pad"]})
    print("enhance artistic:", {k: v for k, v in ar.items() if k != "image"}); dec(ar["image"]).save(os.path.join(out, f"{tag}_2_artistic.jpg"), quality=95)
print("done ->", out)
