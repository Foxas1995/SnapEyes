# -*- coding: utf-8 -*-
"""SnapEyes iris engine: detection, crop, glare removal, faithful enhancement, composition, storage.
Runs on Vercel Python functions (CPU) and locally. All Gemini calls go through generateContent REST."""
import os, io, json, base64, time, math, re, uuid, hmac, hashlib, threading
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

# fine-art finishing applied when the iris is placed on a background (free, deterministic, no model call)
POLISH_DETAIL = 0.70         # unsharp amount: deepens the shadows between the fibres (3-D relief)
POLISH_LIMBAL = 0.95         # how far the outer ring falls towards black (kills the grey crop haze)
POLISH_RIM = 0.45            # accent rim light on the limbus, so the iris sits inside the scene
POLISH_LIMBAL_START = 0.66   # radius (0-1 of the iris) where the outer ring starts falling to black
POLISH_EDGE_FEATHER = 0.16   # how softly the disk dissolves into the background instead of ending on a circle

# studio grade: the fine-art iris look - the iris fills the frame, pure black outside the limbus,
# sculpted local contrast. This is what a macro studio does in post, and none of it needs a model.
STUDIO_FILL = 0.94           # how much of the frame the iris disk occupies
STUDIO_LOCAL = 1.20          # local contrast (large-radius unsharp): sculpts the fibre relief
STUDIO_MICRO = 0.75          # micro contrast (small-radius unsharp): separates individual fibres
STUDIO_SAT = 0.42            # colour depth
STUDIO_SCLERA = 0.85         # how hard the pale sclera / eyelid is pushed out of the outer rim
STUDIO_TRIM = 0.92           # cut just inside the detected limbus: that last sliver is where lids and lashes live

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
    "it is: same framing, same size, same pupil, same colours, same fibres, same black background. The pupil is a "
    "black hole: leave it smooth and deep black, and never draw texture, window frames or shapes inside it. "
    "Photorealistic, no stylisation."
)
PROMPT_ENHANCE = (
    "Use the uploaded image as the sole reference. Perform a true high-resolution upscale and restoration of this "
    "isolated human iris on a black background while preserving the exact iris fibre pattern, crypts, furrows, "
    "pigment spots, colours, pupil size and position, framing, crop and black background. Enhance only genuine "
    "image detail: remove blur, noise, grain, compression artifacts and pixelation while remaining completely "
    "faithful to the source. Do not alter, regenerate, repaint, beautify, stylize, relight, recolor, reshape, "
    "add, remove or reinterpret any element. No generative fill, no hallucinated fibres or texture that is not "
    "visible in the source. The pupil is a black hole: keep it a smooth, even, deep black and never draw texture, "
    "reflections or shapes inside it. "
    "Bring out every fibre, crypt, furrow and pigment spot that is genuinely present in the "
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

BUDGET = 52.0    # seconds of work we allow inside the 60 s Vercel function (leaves room to encode the reply)
_LOCAL = threading.local()   # per-invocation deadline: one warm container can serve several requests at once

def deadline():
    return getattr(_LOCAL, "deadline", 0.0)

def time_left(default=BUDGET):
    d = deadline()
    return default if d <= 0 else d - time.time()

# ----------------------------------------------------------------------------- access control
ALLOWED_HOSTS = ("snapeyes.com", "www.snapeyes.com", "localhost", "127.0.0.1")
TICKET_TTL = 900             # a ticket minted by /api/analyze is good for 15 minutes

def _ticket_secret():
    """Server-only secret; never leaves the process and never appears in a response."""
    raw = os.environ.get("SNAPEYES_TICKET_SECRET", "").strip() or _key()
    return hashlib.sha256(("snapeyes-ticket-v1:" + raw).encode("utf-8")).digest()

def mint_ticket(kind="work", ttl=TICKET_TTL):
    exp = int(time.time()) + int(ttl)
    msg = kind + "." + str(exp)
    return msg + "." + hmac.new(_ticket_secret(), msg.encode(), hashlib.sha256).hexdigest()[:32]

def check_ticket(tok, kind="work"):
    try:
        k, exp_s, sig = str(tok or "").split(".", 2)
        if k != kind or int(exp_s) < time.time(): return False
        want = hmac.new(_ticket_secret(), (k + "." + exp_s).encode(), hashlib.sha256).hexdigest()[:32]
        return hmac.compare_digest(sig, want)
    except Exception:
        return False

def _host_of(value):
    m = re.match(r"^[a-z]+://([^/:]+)", str(value or "").strip(), re.I)
    return (m.group(1).lower() if m else "")

def origin_ok(req):
    """Block cross-origin drive-by billing. A browser always sends Origin on a cross-site POST, so an
    unknown Origin is rejected. An absent Origin (curl, server-to-server) is allowed here and stopped by
    the ticket check instead."""
    h = _host_of(req.headers.get("origin")) or _host_of(req.headers.get("referer"))
    return (not h) or h in ALLOWED_HOSTS or h.endswith(".vercel.app")

def json_content_type(req):
    """Requiring application/json forces a CORS preflight for cross-origin browser callers, and that
    preflight fails because we send no Access-Control-Allow-Origin header."""
    ct = str(req.headers.get("content-type") or "").split(";")[0].strip().lower()
    return ct == "application/json"

def _scrub(s):
    """No secret and no full request URL may ever reach the client or the logs."""
    s = re.sub(r"(key=|AIza)[A-Za-z0-9_\-]{10,}", r"\1***", s)
    for name in ("GEMINI_API_KEY", "BLOB_READ_WRITE_TOKEN"):
        v = os.environ.get(name, "").strip()
        if v: s = s.replace(v, "***")
    return s

def run(req, fn, gate=True):
    """Wrap a handler body: gate, parse JSON, run, serialise, catch errors."""
    t0 = time.time()
    _LOCAL.deadline = t0 + BUDGET
    try:
        if gate and not json_content_type(req):
            return send_json(req, 415, {"ok": False, "error": "Send application/json."})
        if gate and not origin_ok(req):
            return send_json(req, 403, {"ok": False, "error": "This API only serves snapeyes.com."})
        body = read_json(req)
        out = fn(body)
        out["ms"] = int((time.time() - t0) * 1000)
        send_json(req, 200, out)
    except PermissionError as e:
        print("snapeyes refused:", _scrub(repr(e))[:200], flush=True)
        send_json(req, 403, {"ok": False, "error": "This session expired. Please take the photo again.",
                             "ms": int((time.time() - t0) * 1000)})
    except ValueError as e:
        print("snapeyes bad input:", _scrub(repr(e))[:200], flush=True)
        send_json(req, 400, {"ok": False, "error": "We could not read that image. Try another photo.",
                             "ms": int((time.time() - t0) * 1000)})
    except Exception as e:  # noqa
        # detail goes to the Vercel log only; the caller gets a sentence, never internals
        print("snapeyes handler error:", _scrub(repr(e))[:600], flush=True)
        send_json(req, 500, {"ok": False, "error": "Something went wrong on our side. Please try again.",
                             "ms": int((time.time() - t0) * 1000)})

# ----------------------------------------------------------------------------- image helpers
MAX_PIXELS = 40_000_000      # ~40 MP: larger than any phone photo, so anything bigger is a memory attack
MAX_B64_CHARS = 9_000_000    # ~6.7 MB of image bytes; Vercel rejects the request body above ~4.5 MB anyway
Image.MAX_IMAGE_PIXELS = MAX_PIXELS

def b64_to_pil(s):
    if not isinstance(s, str) or not s: raise ValueError("no image supplied")
    if len(s) > MAX_B64_CHARS: raise ValueError("image too large")
    if "," in s[:64] and s.strip().startswith("data:"): s = s.split(",", 1)[1]
    im = Image.open(io.BytesIO(base64.b64decode(s)))
    w, h = im.size
    if w * h > MAX_PIXELS: raise ValueError("image too large")
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
    left = retries  # transient-error budget; dropping an unsupported config key does not consume it
    while True:
        # never wait past the invocation deadline: a killed function cannot run the handler's own fallback
        t = min(timeout, time_left(timeout))
        if t < 3: raise RuntimeError(last or f"{model}: out of time budget before the model call")
        # the key goes in a header, never in the URL: a requests exception stringifies the URL
        r = requests.post(f"{BASE}/models/{model}:generateContent", json=body, timeout=t,
                          headers={"x-goog-api-key": _key()})
        if r.status_code == 200: return r.json()
        last = f"{model} HTTP {r.status_code}: {r.text[:200]}"
        # each key is removed from gen_cfg, so each repair can happen at most once -> the loop always terminates
        if r.status_code == 400 and "imageConfig" in gen_cfg:
            gen_cfg = {k: v for k, v in gen_cfg.items() if k != "imageConfig"}; body["generationConfig"] = gen_cfg; continue
        if r.status_code == 400 and "thinkingConfig" in gen_cfg:
            gen_cfg = {k: v for k, v in gen_cfg.items() if k != "thinkingConfig"}; body["generationConfig"] = gen_cfg; continue
        # only retry when the sleep plus a real second attempt still fit in the budget
        if r.status_code in (429, 500, 503) and left > 0 and time_left(99) > 12:
            left -= 1; time.sleep(4); continue
        break
    raise RuntimeError(last)

def gemini_json(model, prompt, im):
    j = gemini(model, [{"text": prompt}, {"inlineData": {"mimeType": "image/jpeg", "data": pil_to_b64(im, "JPEG", 90)}}],
               {"responseMimeType": "application/json", "temperature": 0})
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

def iris_lock_ok(gray, cx, cy, r, margin=8.0):
    """Is this circle really centred on an iris? An iris holds a dark pupil in the middle and is itself darker
    than the sclera around it. Skin, an eyelid or a mis-detected box fails both tests, and every later stage
    would then be built on the wrong crop."""
    H, W = gray.shape
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    core = d < r * 0.30                      # the pupil lives here
    ring = (d > r * 0.55) & (d < r * 0.90)   # the coloured iris
    out = (d > r * 1.15) & (d < r * 1.55)    # sclera and lid
    if core.sum() < 20 or ring.sum() < 40: return False
    c, g_ring = float(gray[core].mean()), float(gray[ring].mean())
    if c > g_ring - margin: return False     # no dark pupil in the middle
    if out.sum() > 40 and g_ring > float(gray[out].mean()) + margin: return False  # iris brighter than the sclera
    return True

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
        m = core_np                     # fall back to the eroded core, never to an empty mask: discarding it
                                        # would leave the very worst glare untouched in the artwork
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

def pupil_fill(crop, pr_px, glare_hard=None, feather=0.22):
    """Rebuild the pupil as smooth darkness. A pupil reflects the room, so whatever a reflection covers there is
    not iris detail waiting to be restored - it is a hole, and the honest reconstruction is the dark it hid.
    Returns (image, how much of the pupil the reflection covered)."""
    S = crop.size[0]
    yy, xx = np.mgrid[0:S, 0:S]
    d = np.sqrt((xx - S / 2 + 0.5) ** 2 + (yy - S / 2 + 0.5) ** 2)
    inside = d < pr_px
    if pr_px < 4 or not inside.any(): return crop, 0.0
    g = (glare_hard > 0) if glare_hard is not None else np.zeros_like(inside)
    overlap = float(g[inside].mean())
    if overlap < 0.04: return crop, overlap
    arr = np.asarray(crop).astype(np.float32)
    # the true pupil colour is the darkest thing still visible inside it; the rim is only a fallback, and both
    # get clamped because a pupil is never bright and never coloured
    dark = inside & (~g)
    if int(dark.sum()) > 60:
        base = np.percentile(arr[dark], 12, axis=0)
    else:
        rim = inside & (d > pr_px * 0.7) & (~g)
        base = (np.percentile(arr[rim], 12, axis=0) if int(rim.sum()) > 60
                else np.array([10.0, 10.0, 14.0], dtype=np.float32))
    base = base * 0.45 + float(base.mean()) * 0.55      # a pupil is neutral, not tinted
    base = np.minimum(base, 30.0)                       # and never bright
    t = np.clip(d / max(pr_px, 1.0), 0, 1)
    fill = base[None, None, :] * (0.40 + 0.60 * t[..., None] ** 2)   # deepest in the centre, lifting towards the rim
    a = np.clip((pr_px - d) / max(pr_px * feather, 1.0), 0, 1)[..., None]
    return Image.fromarray(np.clip(arr * (1 - a) + fill * a, 0, 255).astype(np.uint8)), overlap

def drop_pupil(mask_hard, mask_soft, pr_px):
    """Take the pupil disk out of a glare mask, so the image model is only ever asked to rebuild iris."""
    S = mask_hard.shape[0]
    yy, xx = np.mgrid[0:S, 0:S]
    keep = np.sqrt((xx - S / 2 + 0.5) ** 2 + (yy - S / 2 + 0.5) ** 2) > pr_px * 1.04
    return (mask_hard * keep).astype(np.uint8), mask_soft * keep

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
_SR_LOCK = threading.Lock()        # the lazy build is not atomic: two racing invocations keep two arenas alive
_SR_GATE = threading.Semaphore(1)  # one x4 pass at a time: three concurrent runs exceed the 1024 MB function

def sr_x4(im):
    global _SR
    import onnxruntime as ort
    with _SR_LOCK:
        if _SR is None:
            so = ort.SessionOptions(); so.intra_op_num_threads = 2
            _SR = ort.InferenceSession(os.path.join(ASSETS, "models", "realesr_general_x4v3.onnx"), so, providers=["CPUExecutionProvider"])
    a = (np.asarray(im.convert("RGB")).astype(np.float32) / 255.0).transpose(2, 0, 1)[None]
    with _SR_GATE:
        y = _SR.run(None, {"input": a})[0][0]
    return Image.fromarray((np.clip(y, 0, 1).transpose(1, 2, 0) * 255).astype(np.uint8))

# ----------------------------------------------------------------------------- composition
def _font(name, size, weight=None):
    f = ImageFont.truetype(os.path.join(ASSETS, "fonts", name), size)
    if weight:
        try: f.set_variation_by_name(weight)
        except Exception: pass
    return f

def studio_grade(im, r_frac, out=1024, fill=None, local=None, micro=None, sat=None, sclera=None, trim=None):
    """Turn a masked iris square into the fine-art frame: limbus-tight, pure black outside, sculpted fibres.

    A phone crop carries a slice of sclera or eyelid at the bottom of the disk and sits small inside its frame.
    A studio print does neither: the iris is the whole picture. Everything here is arithmetic on the pixels the
    camera captured, so it deepens what is real instead of inventing what is not."""
    fill = STUDIO_FILL if fill is None else fill
    trim = STUDIO_TRIM if trim is None else trim
    local = STUDIO_LOCAL if local is None else local
    micro = STUDIO_MICRO if micro is None else micro
    sat = STUDIO_SAT if sat is None else sat
    sclera = STUDIO_SCLERA if sclera is None else sclera

    S = im.size[0]
    R = max(1.0, r_frac * S)
    yy, xx = np.mgrid[0:S, 0:S]
    rr = np.sqrt((xx - S / 2 + 0.5) ** 2 + (yy - S / 2 + 0.5) ** 2) / R
    arr = np.asarray(im.convert("RGB")).astype(np.float32)

    # 1. push the pale intruders out of the outer rim: sclera and eyelid are brighter and far less saturated
    #    than iris, so they can be identified without touching the iris itself
    if sclera > 0:
        mx, mn = arr.max(axis=2), arr.min(axis=2)
        satmap = (mx - mn) / np.maximum(mx, 1.0)
        lum = arr.mean(axis=2)
        ring = (rr > 0.72) & (rr < 1.12)
        if ring.any():
            iris_lum = float(np.median(lum[(rr > 0.35) & (rr < 0.70)])) if ((rr > 0.35) & (rr < 0.70)).any() else 90.0
            pale = ring & (lum > iris_lum * 1.18) & (satmap < 0.28)
            k = np.clip((lum - iris_lum * 1.10) / max(iris_lum * 0.5, 1.0), 0, 1) * sclera
            arr = arr * (1 - (pale * k)[..., None])

    # 2. sculpt: large-radius unsharp gives the fibres relief, small-radius separates them
    base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    big = np.asarray(base.filter(ImageFilter.GaussianBlur(max(2.0, S * 0.045)))).astype(np.float32)
    sml = np.asarray(base.filter(ImageFilter.GaussianBlur(max(1.0, S * 0.004)))).astype(np.float32)
    arr = arr + (arr - big) * local + (arr - sml) * micro

    # 3. colour depth, without shifting hue
    grey = arr.mean(axis=2, keepdims=True)
    arr = grey + (arr - grey) * (1.0 + sat)

    # 4. limbus-tight framing: scale the disk so it fills the requested share of the frame
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    Rt = R * trim
    side = int(round(2 * Rt))
    x0, y0 = int(round(S / 2 - Rt)), int(round(S / 2 - Rt))
    tight = Image.new("RGB", (side, side), (0, 0, 0))
    tight.paste(Image.fromarray(arr), (-x0, -y0))
    target = max(8, int(round(out * fill)))
    tight = tight.resize((target, target), Image.LANCZOS)

    # 5. pure black outside the limbus, with only a hairline of softness so the circle stays crisp
    a = disk_alpha(target, target / 2.0, 0.012)
    disk = (np.asarray(tight).astype(np.float32) * a[..., None])
    canvas = np.zeros((out, out, 3), dtype=np.float32)
    off = (out - target) // 2
    canvas[off:off + target, off:off + target] = disk
    return Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8))

def compose(iris, style="celestial_gold", title=None, names="", watermark=True, r_frac=None, size=1024):
    st = STYLES.get(style, STYLES["celestial_gold"])
    bg = Image.open(os.path.join(ASSETS, "bg", st["bg"])).convert("RGB").resize((size, size), Image.LANCZOS)
    canvas = np.asarray(bg).astype(np.float32)
    r_frac = r_frac or iris_radius_frac()
    # iris disk with feathered edge; the iris square is assumed centred with radius r_frac*side
    acc = np.array(st["accent"], dtype=np.float32)
    # Studio Black is the bare fine-art print the reference galleries sell: the iris fills the frame on
    # pure black, with nothing else in the picture. The other styles keep the iris large but leave room
    # for the scene and the typography.
    bare = style == "studio_black"
    Sd = int(size * (0.96 if bare else 0.80))
    graded = studio_grade(iris, r_frac, out=Sd)
    arr = np.asarray(graded).astype(np.float32)
    Rg = max(1.0, Sd * STUDIO_FILL / 2.0)
    jy, jx = np.mgrid[0:Sd, 0:Sd]
    rr = np.sqrt((jx - Sd / 2 + 0.5) ** 2 + (jy - Sd / 2 + 0.5) ** 2) / Rg
    cx, cy = size // 2, int(size * (0.5 if bare else 0.44))
    if not bare:
        # a thin accent highlight on the limbus, strongest towards the upper left, so the iris sits inside
        # the scene instead of being pasted on top of it
        ang = np.arctan2(jy - Sd / 2, jx - Sd / 2)
        rim = np.exp(-((rr - 0.985) / 0.045) ** 2) * (0.55 + 0.45 * np.cos(ang + 2.4))
        arr = np.clip(arr + acc * rim[..., None] * POLISH_RIM, 0, 255)
        # soft accent glow behind the iris
        yy, xx = np.mgrid[0:size, 0:size]
        dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / Rg
        glow = np.clip(1.6 - dist, 0, 1) ** 2 * 0.45
        canvas = canvas * (1 - glow[..., None] * 0.55) + acc * glow[..., None] * 0.55
    alpha = disk_alpha(Sd, Rg, 0.015 if bare else 0.05)
    x0, y0 = cx - Sd // 2, cy - Sd // 2
    x0, y0 = max(0, min(x0, size - Sd)), max(0, min(y0, size - Sd))
    region = canvas[y0:y0 + Sd, x0:x0 + Sd]
    canvas[y0:y0 + Sd, x0:x0 + Sd] = region * (1 - alpha[..., None]) + arr * alpha[..., None]
    out = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(out)
    if not bare:
        t = (title or st["title"]).upper()
        ft = _font("Cinzel.ttf", int(size * 0.042), "Bold"); fn = _font("PlusJakartaSans.ttf", int(size * 0.026), "Regular"); fs = _font("PlusJakartaSans.ttf", int(size * 0.014), "Medium")
        d.text((size / 2, size * 0.86), t, font=ft, fill=st["accent"], anchor="mm")
        if names: d.text((size / 2, size * 0.905), names, font=fn, fill=(240, 243, 250), anchor="mm")
        d.text((size / 2, size * 0.945), "SNAPEYES MASTER ART  ·  300 DPI ARCHIVAL EDITION", font=fs, fill=(150, 155, 170), anchor="mm")
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
def safe_segment(v, n=40):
    """A caller-controlled string never reaches a storage path unfiltered."""
    return re.sub(r"[^A-Za-z0-9_-]", "", str(v or ""))[:n] or "anon"

def store(pathname, data, content_type):
    token = os.environ.get("BLOB_READ_WRITE_TOKEN", "").strip()
    if not token: return None
    if time_left(99) < 6: return None   # a slow blob write must never kill a function that already paid for a generation
    try:
        r = requests.put(f"https://blob.vercel-storage.com/{pathname}", data=data, timeout=6,
                         headers={"authorization": f"Bearer {token}", "x-api-version": "7", "x-content-type": content_type,
                                  "x-add-random-suffix": "0", "x-cache-control-max-age": "31536000"})
        if r.status_code in (200, 201): return r.json().get("url")
    except Exception:
        pass
    return None

def new_id():
    return time.strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:10]
