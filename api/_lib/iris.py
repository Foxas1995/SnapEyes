# -*- coding: utf-8 -*-
"""SnapEyes iris engine: detection, crop, glare removal, faithful enhancement, composition, storage.
Runs on Vercel Python functions (CPU) and locally. All Gemini calls go through generateContent REST."""
import os, io, json, base64, time, math, re, uuid
import numpy as np
import requests
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "_assets")
BASE = "https://generativelanguage.googleapis.com/v1beta"
VISION_MODEL = os.environ.get("SNAPEYES_VISION_MODEL", "gemini-3.8-flash")
IMAGE_MODEL = os.environ.get("SNAPEYES_IMAGE_MODEL", "gemini-3.1-flash-image")
GLARE_MIN_PCT = 0.4          # below this share of the iris we do not call the de-glare model
SR_MAX_SIDE = 600            # crops smaller than this get Real-ESRGAN x4 before the enhance step
FIDELITY_FLOOR = 0.75        # low-frequency SSIM below this = model drifted, fall back to the faithful upscale
WORK = 1024                  # working resolution of the iris square

STYLES = {
    "celestial_gold": {"bg": "bg_celestial_gold.jpg", "accent": (245, 197, 66), "title": "THE UNIVERSE WITHIN"},
    "deep_nebula": {"bg": "bg_deep_nebula.jpg", "accent": (129, 140, 248), "title": "DEEP NEBULA"},
    "emerald_aurora": {"bg": "bg_emerald_aurora.jpg", "accent": (52, 211, 153), "title": "EMERALD AURORA"},
    "obsidian_smoke": {"bg": "bg_obsidian_smoke.jpg", "accent": (203, 213, 225), "title": "OBSIDIAN SMOKE"},
    "supernova": {"bg": "bg_supernova.jpg", "accent": (251, 146, 60), "title": "SUPERNOVA"},
    "studio_black": {"bg": "bg_studio_black.jpg", "accent": (212, 175, 55), "title": "THE UNIVERSE WITHIN"},
}

PROMPT_VISION = (
    "Close-up or selfie photo containing a human eye. Return ONLY JSON, coordinates on a 0-1000 grid relative to the "
    "full image (x right, y down): "
    '{"found":true,"iris_box":[x1,y1,x2,y2],"pupil_box":[x1,y1,x2,y2],"glare_boxes":[[x1,y1,x2,y2],...],'
    '"iris_occluded_by_eyelids_percent":n,"sharpness":"sharp|soft|blurry","eye_open":true}. '
    "iris_box is the tight bounding box of the coloured iris (limbus to limbus). glare_boxes are bright specular "
    "reflections on the cornea inside the iris. If there is no human eye, return {\"found\":false}. Be precise."
)
PROMPT_DEGLARE = (
    "This is an isolated human iris on a black background. Remove ONLY the bright specular reflections (window/flash "
    "glare) and any eyelash shadows, reconstructing the underlying iris fibres so they match the surrounding texture. "
    "Match the sharpness and softness of the surrounding iris exactly: if the surrounding iris is soft or blurry, keep "
    "the rebuilt area equally soft, never sharper or more detailed than its neighbours. Keep everything else exactly as "
    "it is: same framing, same size, same pupil, same colours, same fibres, same black background. Photorealistic, no stylisation."
)
PROMPT_ENHANCE = (
    "Use the uploaded image as the sole reference. Perform a true high-resolution upscale and restoration of this "
    "isolated human iris on a black background while preserving the exact iris fibre pattern, crypts, furrows, "
    "pigment spots, colours, pupil size and position, framing, crop and black background. Enhance only genuine "
    "image detail: remove blur, noise, grain, compression artifacts and pixelation while remaining completely "
    "faithful to the source. Do not alter, regenerate, repaint, beautify, stylize, relight, recolor, reshape, "
    "add, remove or reinterpret any element. No generative fill, no hallucinated fibres or texture that is not "
    "visible in the source. Bring out every fibre, crypt, furrow and pigment spot that is genuinely present in the "
    "source, even if only faintly visible, so the restored iris looks crisp rather than blurry. Do not add or "
    "reconstruct any specular highlights, reflections, glossy spots or bubbles: the source contains none. Output a "
    "visually identical photograph, only sharper, cleaner and more detailed."
)
PROMPT_ARTISTIC = (
    "This is an isolated human iris on a black background, photographed with a phone. Produce a stunning macro "
    "photograph of THIS iris as if taken with a professional macro lens and ring light: razor sharp radial fibres, "
    "crypts and furrows, deep black pupil, rich but natural colours. Keep the same colours, the same pupil size and "
    "position, the same overall pattern and any pigment spots of this specific iris; do not change the framing or "
    "the black background. Photorealistic, no painting style, no text."
)

# ----------------------------------------------------------------------------- http helpers
def read_json(req):
    n = int(req.headers.get("content-length") or 0)
    raw = req.rfile.read(n) if n else b"{}"
    return json.loads(raw.decode("utf-8") or "{}")

def send_json(req, status, obj):
    data = b"" if obj is None else json.dumps(obj).encode("utf-8")
    req.send_response(status)
    req.send_header("Content-Type", "application/json; charset=utf-8")
    req.send_header("Cache-Control", "no-store")
    req.send_header("Content-Length", str(len(data)))
    req.end_headers()
    if data: req.wfile.write(data)

def run(req, fn):
    """Wrap a handler body: parse JSON, run, serialise, catch errors."""
    t0 = time.time()
    try:
        body = read_json(req)
        out = fn(body)
        out["ms"] = int((time.time() - t0) * 1000)
        send_json(req, 200, out)
    except Exception as e:  # noqa
        send_json(req, 500, {"ok": False, "error": str(e)[:400], "ms": int((time.time() - t0) * 1000)})

# ----------------------------------------------------------------------------- image helpers
def b64_to_pil(s):
    if "," in s[:64] and s.strip().startswith("data:"): s = s.split(",", 1)[1]
    im = Image.open(io.BytesIO(base64.b64decode(s)))
    try: im = ImageOps.exif_transpose(im)
    except Exception: pass
    return im.convert("RGB")

def pil_to_b64(im, fmt="JPEG", q=92):
    buf = io.BytesIO()
    if fmt.upper() == "JPEG": im.convert("RGB").save(buf, "JPEG", quality=q, subsampling=0)
    else: im.save(buf, fmt)
    return base64.b64encode(buf.getvalue()).decode()

def pil_bytes(im, fmt="JPEG", q=92):
    buf = io.BytesIO(); im.convert("RGB").save(buf, fmt, quality=q) if fmt == "JPEG" else im.save(buf, fmt); return buf.getvalue()

def to_gray(im):
    return np.asarray(im.convert("L"), dtype=np.float32)

def laplacian_var(im, size=256):
    """Sharpness proxy (variance of Laplacian) on a normalised size, so values are comparable across photos."""
    g = to_gray(im.resize((size, size), Image.LANCZOS))
    lap = -4 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:]
    return float(lap.var())

# ----------------------------------------------------------------------------- gemini
def _key():
    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if not k:
        p = r"C:\kuriam\.gemini-key"
        if os.path.exists(p): k = open(p, encoding="utf-8").read().strip()
    if not k: raise RuntimeError("GEMINI_API_KEY is not configured")
    return k

def gemini(model, parts, gen_cfg, timeout=55, retries=1):
    body = {"contents": [{"role": "user", "parts": parts}], "generationConfig": gen_cfg}
    last = ""
    for attempt in range(retries + 1):
        r = requests.post(f"{BASE}/models/{model}:generateContent?key={_key()}", json=body, timeout=timeout)
        if r.status_code == 200: return r.json()
        last = f"{model} HTTP {r.status_code}: {r.text[:200]}"
        if r.status_code == 400 and "imageConfig" in gen_cfg:
            gen_cfg = {k: v for k, v in gen_cfg.items() if k != "imageConfig"}; body["generationConfig"] = gen_cfg; continue
        if r.status_code == 400 and "thinkingConfig" in gen_cfg:
            gen_cfg = {k: v for k, v in gen_cfg.items() if k != "thinkingConfig"}; body["generationConfig"] = gen_cfg; continue
        if r.status_code in (429, 500, 503) and attempt < retries: time.sleep(4); continue
        break
    raise RuntimeError(last)

def gemini_json(model, prompt, im):
    j = gemini(model, [{"text": prompt}, {"inlineData": {"mimeType": "image/jpeg", "data": pil_to_b64(im, "JPEG", 90)}}],
               {"responseMimeType": "application/json", "temperature": 0}, timeout=60)
    txt = "".join(p.get("text", "") for p in j["candidates"][0]["content"]["parts"])
    try: return json.loads(txt)
    except Exception:
        m = re.search(r"\{.*\}", txt, re.S)
        return json.loads(m.group(0)) if m else {}

def gemini_image(prompt, im, size=None, thinking=None, model=None):
    cfg = {"responseModalities": ["IMAGE", "TEXT"], "imageConfig": {"aspectRatio": "1:1"}}
    if size: cfg["imageConfig"]["imageSize"] = size
    if thinking: cfg["thinkingConfig"] = {"thinkingLevel": thinking}
    j = gemini(model or IMAGE_MODEL, [{"text": prompt}, {"inlineData": {"mimeType": "image/png", "data": pil_to_b64(im, "PNG")}}], cfg)
    for p in j["candidates"][0]["content"]["parts"]:
        if "inlineData" in p:
            return Image.open(io.BytesIO(base64.b64decode(p["inlineData"]["data"]))).convert("RGB")
    raise RuntimeError("image model returned no image")

# ----------------------------------------------------------------------------- iris geometry
def refine_circle(gray, cx, cy, r0):
    """Daugman-style limbus fit: maximise the radial intensity gradient (dark iris -> bright sclera) on the left and
    right sectors, ignoring the eyelid sectors. gray is float32 HxW, coordinates in its pixels."""
    H, W = gray.shape
    ang = np.deg2rad(np.concatenate([np.arange(-55, 56, 3), np.arange(125, 236, 3)]))
    ca, sa = np.cos(ang), np.sin(ang)
    radii = np.arange(max(6.0, r0 * 0.82), r0 * 1.22, max(1.0, r0 / 120))
    best = (cx, cy, r0, -1e9)
    for dx in np.linspace(-0.1 * r0, 0.1 * r0, 7):
        for dy in np.linspace(-0.1 * r0, 0.1 * r0, 7):
            xs = (cx + dx) + np.outer(radii, ca); ys = (cy + dy) + np.outer(radii, sa)
            ok = (xs >= 0) & (xs <= W - 1) & (ys >= 0) & (ys <= H - 1)
            xi = np.clip(xs, 0, W - 1).astype(int); yi = np.clip(ys, 0, H - 1).astype(int)
            prof = np.where(ok, gray[yi, xi], np.nan)
            if np.isnan(prof).mean() > 0.3: continue
            m = np.nanmean(prof, axis=1)
            m = np.convolve(m, np.ones(3) / 3, mode="same")
            d = np.gradient(m)
            d[:2] = -1e9; d[-2:] = -1e9
            k = int(np.argmax(d))
            if d[k] > best[3]: best = (cx + dx, cy + dy, float(radii[k]), float(d[k]))
    return best[0], best[1], best[2]

def disk_alpha(S, r, feather=0.035):
    yy, xx = np.mgrid[0:S, 0:S]
    d = np.sqrt((xx - S / 2 + 0.5) ** 2 + (yy - S / 2 + 0.5) ** 2) / r
    a = np.clip((1 - d) / feather, 0, 1)
    return 0.5 - 0.5 * np.cos(a * math.pi)

def circular_crop(im, cx, cy, r, pad=1.12, feather=0.035):
    """Square crop around (cx,cy) of side 2*r*pad with everything outside the iris disk faded to black."""
    S = int(round(2 * r * pad))
    x0, y0 = int(round(cx - S / 2)), int(round(cy - S / 2))
    crop = Image.new("RGB", (S, S), (0, 0, 0)); crop.paste(im, (-x0, -y0))
    arr = np.asarray(crop).astype(np.float32) * disk_alpha(S, r, feather)[..., None]
    return Image.fromarray(arr.astype(np.uint8))

def iris_radius_frac(pad=1.12):
    return 1.0 / (2 * pad)

def mask_disk(square, pad=1.12, feather=0.035):
    """Apply the iris disk mask to a plain square crop coming from the client (everything outside fades to black)."""
    S = square.size[0]
    arr = np.asarray(square.convert("RGB")).astype(np.float32) * disk_alpha(S, iris_radius_frac(pad) * S, feather)[..., None]
    return Image.fromarray(arr.astype(np.uint8))

# ----------------------------------------------------------------------------- glare
def glare_mask(crop, r_px, extra_boxes=None):
    """Specular highlights inside the iris: a bright unsaturated core (relative to the iris itself, plus any boxes the
    vision model reported) grown into the soft halo around it. Returns (hard uint8 mask, feathered float mask, pct)."""
    S = crop.size[0]
    hsv = np.asarray(crop.convert("HSV")).astype(np.int16)
    v, s = hsv[..., 2], hsv[..., 1]
    yy, xx = np.mgrid[0:S, 0:S]
    dist = np.sqrt((xx - S / 2) ** 2 + (yy - S / 2) ** 2)
    inside = dist < r_px * 0.93
    ring = inside & (dist > r_px * 0.42)                      # iris statistics without the dark pupil
    med_v = float(np.median(v[ring])) if ring.any() else 128.0
    thr = max(200.0, med_v + 45.0)
    core = ((v > thr) & (s < 100)) & inside
    for b in (extra_boxes or []):
        x1, y1, x2, y2 = [int(round(c)) for c in b]
        g = max(4, int(0.25 * max(x2 - x1, y2 - y1)))         # grow the reported box a little, it usually marks only the brightest core
        sub = np.zeros_like(core); sub[max(0, y1 - g):min(S, y2 + g), max(0, x1 - g):min(S, x2 + g)] = True
        core |= sub & inside & (v > thr - 15) & (s < 110)
    core_img = Image.fromarray((core * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3))
    core_np = np.asarray(core_img) > 0
    area = max(1.0, float(inside.sum()))
    # contrast-adaptive halo: a pale, blurry iris hides its reflection halo in a few brightness units,
    # a crisp high-contrast iris would swallow bright fibres with the same rule
    rest = ring & ~core_np
    sd = float(v[rest].std()) if rest.any() else 30.0
    halo_thr = med_v + float(np.clip(0.5 * sd, 10.0, 28.0))
    near_px = int(S * (0.05 if sd < 40 else 0.03)) | 1
    near = np.asarray(core_img.filter(ImageFilter.MaxFilter(near_px))) > 0
    halo = near & (dist < r_px * 0.97) & (v > halo_thr) & (s < 120)
    m = core_np | halo
    if m.sum() / area > 0.25:           # a real reflection never covers a quarter of the iris: halo grew into bright fibres
        m = core_np
    if m.sum() / area > 0.25:
        m = np.zeros_like(m)
    mi = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))
    hard = np.asarray(mi)
    feather = np.asarray(mi.filter(ImageFilter.GaussianBlur(5))).astype(np.float32) / 255.0
    pct = 100.0 * float((hard > 0).sum()) / area
    return hard, feather, pct

def mirror_prefill(crop, feather):
    """Replace the masked area with the point-mirrored iris (through the pupil centre) so the reflection is already
    gone before the image model refines the seam. Radial iris texture is roughly point-symmetric at low frequencies."""
    arr = np.asarray(crop).astype(np.float32)
    mirror = arr[::-1, ::-1]
    a = feather[..., None]
    a_m = feather[::-1, ::-1][..., None]
    # where the mirrored source is itself masked, fall back to a heavily blurred version of the iris
    blur = np.asarray(crop.filter(ImageFilter.GaussianBlur(crop.size[0] * 0.03))).astype(np.float32)
    src = mirror * (1 - a_m) + blur * a_m
    return Image.fromarray(np.clip(arr * (1 - a) + src * a, 0, 255).astype(np.uint8))

def composite(base, patch, alpha):
    a = alpha[..., None]
    out = np.asarray(base).astype(np.float32) * (1 - a) + np.asarray(patch.resize(base.size, Image.LANCZOS)).astype(np.float32) * a
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

# ----------------------------------------------------------------------------- fidelity
def _box_mean(a, k):
    p = k // 2
    ap = np.pad(a, p, mode="reflect")
    c = np.cumsum(np.cumsum(ap, axis=0), axis=1)
    c = np.pad(c, ((1, 0), (1, 0)))
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)

def ssim_lowfreq(a_im, b_im, r_frac, sigma=2.0, k=7):
    """Structural similarity after blurring both images to the detail level of the source. 1.0 = same structure."""
    S = min(a_im.size[0], 512)
    a = to_gray(a_im.resize((S, S), Image.LANCZOS).filter(ImageFilter.GaussianBlur(sigma)))
    b = to_gray(b_im.resize((S, S), Image.LANCZOS).filter(ImageFilter.GaussianBlur(sigma)))
    mu_a, mu_b = _box_mean(a, k), _box_mean(b, k)
    va = _box_mean(a * a, k) - mu_a ** 2; vb = _box_mean(b * b, k) - mu_b ** 2; cov = _box_mean(a * b, k) - mu_a * mu_b
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    smap = ((2 * mu_a * mu_b + c1) * (2 * cov + c2)) / ((mu_a ** 2 + mu_b ** 2 + c1) * (va + vb + c2))
    yy, xx = np.mgrid[0:S, 0:S]
    inside = np.sqrt((xx - S / 2) ** 2 + (yy - S / 2) ** 2) < r_frac * S * 0.95
    return float(smap[inside].mean())

# ----------------------------------------------------------------------------- super-resolution (Real-ESRGAN general x4v3, ONNX, CPU)
_SR = None
def sr_x4(im):
    global _SR
    import onnxruntime as ort
    if _SR is None:
        so = ort.SessionOptions(); so.intra_op_num_threads = 2
        _SR = ort.InferenceSession(os.path.join(ASSETS, "models", "realesr_general_x4v3.onnx"), so, providers=["CPUExecutionProvider"])
    a = (np.asarray(im.convert("RGB")).astype(np.float32) / 255.0).transpose(2, 0, 1)[None]
    y = _SR.run(None, {"input": a})[0][0]
    return Image.fromarray((np.clip(y, 0, 1).transpose(1, 2, 0) * 255).astype(np.uint8))

# ----------------------------------------------------------------------------- composition
def _font(name, size, weight=None):
    f = ImageFont.truetype(os.path.join(ASSETS, "fonts", name), size)
    if weight:
        try: f.set_variation_by_name(weight)
        except Exception: pass
    return f

def compose(iris, style="celestial_gold", title=None, names="", watermark=True, r_frac=None, size=1024):
    st = STYLES.get(style, STYLES["celestial_gold"])
    bg = Image.open(os.path.join(ASSETS, "bg", st["bg"])).convert("RGB").resize((size, size), Image.LANCZOS)
    canvas = np.asarray(bg).astype(np.float32)
    r_frac = r_frac or iris_radius_frac()
    # iris disk with feathered edge; the iris square is assumed centred with radius r_frac*side
    Sd = int(size * 0.56); ir = iris.resize((Sd, Sd), Image.LANCZOS)
    alpha = disk_alpha(Sd, r_frac * Sd * 0.985, 0.05)
    cx, cy = size // 2, int(size * 0.455)
    # soft accent glow behind the iris
    yy, xx = np.mgrid[0:size, 0:size]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (r_frac * Sd)
    glow = np.clip(1.6 - dist, 0, 1) ** 2 * 0.45
    acc = np.array(st["accent"], dtype=np.float32)
    canvas = canvas * (1 - glow[..., None] * 0.55) + acc * glow[..., None] * 0.55
    x0, y0 = cx - Sd // 2, cy - Sd // 2
    region = canvas[y0:y0 + Sd, x0:x0 + Sd]
    canvas[y0:y0 + Sd, x0:x0 + Sd] = region * (1 - alpha[..., None]) + np.asarray(ir).astype(np.float32) * alpha[..., None]
    out = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(out)
    t = (title or st["title"]).upper()
    ft = _font("Cinzel.ttf", int(size * 0.042), "Bold"); fn = _font("PlusJakartaSans.ttf", int(size * 0.026), "Regular"); fs = _font("PlusJakartaSans.ttf", int(size * 0.014), "Medium")
    d.text((size / 2, size * 0.80), t, font=ft, fill=st["accent"], anchor="mm")
    if names: d.text((size / 2, size * 0.845), names, font=fn, fill=(240, 243, 250), anchor="mm")
    d.text((size / 2, size * 0.885), "SNAPEYES MASTER ART  ·  300 DPI ARCHIVAL EDITION", font=fs, fill=(150, 155, 170), anchor="mm")
    if watermark:
        layer = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
        fw = _font("PlusJakartaSans.ttf", int(size * 0.036), "Bold")
        for y in range(0, size * 2, int(size * 0.3)):
            for x in range(0, size * 2, int(size * 0.7)):
                ld.text((x + (y // int(size * 0.3) % 2) * size * 0.35, y), "SNAPEYES.COM  ·  PREVIEW", font=fw, fill=(255, 255, 255, 40))
        layer = layer.rotate(-18, resample=Image.BICUBIC).crop((size // 2, size // 2, size // 2 + size, size // 2 + size))
        out = Image.alpha_composite(out.convert("RGBA"), layer).convert("RGB")
        d = ImageDraw.Draw(out); fp = _font("PlusJakartaSans.ttf", int(size * 0.016), "Bold")
        d.rounded_rectangle((size * 0.36, size * 0.03, size * 0.64, size * 0.07), radius=int(size * 0.02), fill=(0, 0, 0, 200), outline=st["accent"])
        d.text((size / 2, size * 0.05), "WATERMARKED PREVIEW  ·  UNLOCK 4K", font=fp, fill=st["accent"], anchor="mm")
    return out

# ----------------------------------------------------------------------------- storage (Vercel Blob REST; silently skipped when not configured)
def store(pathname, data, content_type):
    token = os.environ.get("BLOB_READ_WRITE_TOKEN", "").strip()
    if not token: return None
    try:
        r = requests.put(f"https://blob.vercel-storage.com/{pathname}", data=data, timeout=30,
                         headers={"authorization": f"Bearer {token}", "x-api-version": "7", "x-content-type": content_type,
                                  "x-add-random-suffix": "0", "x-cache-control-max-age": "31536000"})
        if r.status_code in (200, 201): return r.json().get("url")
    except Exception:
        pass
    return None

def new_id():
    return time.strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:10]
