# -*- coding: utf-8 -*-
"""End-to-end test of the API flow the browser performs, against the local dev API (or a deployed URL).
python scripts/test_flow.py <photo> [base_url]  -> writes outputs next to the photo in ./flowtest/"""
import os, sys, io, json, time, base64
import requests
from PIL import Image, ImageOps
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api"))
from _lib import catalogue     # the style ids come from api/_lib/styles_registry.py
# the first two one-eye styles a customer can preview (the six legacy ids are retired since the cutover and the public compose refuses them)
STYLE_A, STYLE_B = [i for i in catalogue.ids() if not catalogue.is_legacy(i) and catalogue.previewable(i, 1)][:2]

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
TICKET = a.get("ticket")
d = post("/api/deglare", {"crop": b64(crop, "JPEG", 95), "pad": a["pad"], "ticket": TICKET, "pupil_r": a.get("pupil_r"), "glare_boxes": a.get("glare_boxes_crop", [])})
print("deglare:", {k: v for k, v in d.items() if k != "crop"}); dec(d["crop"]).save(os.path.join(out, f"{tag}_1_deglared.jpg"), quality=95)
e = post("/api/enhance", {"crop": d["crop"], "mode": "artistic", "pad": a["pad"], "ticket": TICKET, "session": "test-" + tag, "consent": True, "meta": a["quality"]})
# image is the watermarked 800 px display copy /try shows; the clean restoration comes back only sealed (api/_lib/preview.py)
print("enhance studio macro:", {k: v for k, v in e.items() if k not in ("image", "sealed", "sealed_sizes")}); dec(e["image"]).save(os.path.join(out, f"{tag}_2_studio_display.jpg"), quality=95)
IRIS = {"sealed": [e["sealed"]]} if e.get("sealed") else {"iris": e["image"]}   # an older server: the clean image itself
c = post("/api/compose", {**IRIS, "style": STYLE_A, "names": "Mantas", "pad": a["pad"]})
print("compose:", {k: v for k, v in c.items() if k != "image"}); dec(c["image"]).save(os.path.join(out, f"{tag}_3_art_celestial.jpg"), quality=95)
# the watermark is not the caller's to turn off (only an unlock ticket does): this preview is watermarked too
c2 = post("/api/compose", {**IRIS, "style": STYLE_B, "names": "Mantas", "pad": a["pad"]})
dec(c2["image"]).save(os.path.join(out, f"{tag}_3_art_nebula.jpg"), quality=95)
if "--artistic" in sys.argv:
    ar = post("/api/enhance", {"crop": d["crop"], "mode": "artistic", "pad": a["pad"], "ticket": TICKET})
    print("enhance artistic:", {k: v for k, v in ar.items() if k not in ("image", "sealed", "sealed_sizes")}); dec(ar["image"]).save(os.path.join(out, f"{tag}_2_artistic_display.jpg"), quality=95)
print("done ->", out)
