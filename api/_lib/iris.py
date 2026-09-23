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
STUDIO_LOCAL = 0.30          # local contrast (large-radius unsharp): sculpts the fibre relief.
                             # Measured against eleven professional prints, 1.20 ran 2.0-2.6x their
                             # angular contrast and burned 7% of the iris to the rails.
STUDIO_MICRO = 0.75          # micro contrast (small-radius unsharp): separates individual fibres
STUDIO_SAT = 0.18            # colour depth. The sculpting runs on luminance, so this number is the only
                             # thing that moves colour: 0.18 lands about 7% above the source, which reads
                             # as depth rather than as a filter.
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
    "Photographed with a 100mm f/2.8 macro lens under a cross-polarised ring flash, so there is zero corneal "
    "glare. Render this isolated human iris to that standard: razor-sharp trabecular meshwork, Fuchs crypts, "
    "contraction furrows and radial collarette fibres, a deep velvet black pupil, authentic natural melanin "
    "saturation, luxury fine-art print. Keep this person's colours, pupil size and position, overall pattern "
    "and any pigment spots; do not change the framing or the black background. Photorealistic macro "
    "photograph, no painting style, no text, no added highlights or reflections."
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

# This project's own Vercel hosts, as exact names only. "Anything on .vercel.app" used to pass, and anyone
# can deploy there. No pattern is safe either: a .vercel.app name goes to whoever creates a project of that
# name first, so "snap-eyes-<anything>-foxas1995s-projects" can be registered by a stranger. These two are
# this project's production aliases (snap-eyes.vercel.app serves the same /api/health commit as
# snapeyes.com). A preview or branch page calls its own deployment's API, and that host comes from
# VERCEL_URL / VERCEL_BRANCH_URL in _deployment_hosts().
OWN_VERCEL_HOSTS = ("snap-eyes.vercel.app", "snap-eyes-foxas1995s-projects.vercel.app")

def _deployment_hosts():
    """The hosts Vercel says this very deployment answers on (empty locally)."""
    return {_host_of("https://" + os.environ.get(k, "").strip())
            for k in ("VERCEL_URL", "VERCEL_BRANCH_URL", "VERCEL_PROJECT_PRODUCTION_URL")} - {""}

def origin_ok(req):
    """Block cross-origin drive-by billing. A browser always sends Origin on a cross-site POST, so an
    unknown Origin is rejected. An absent Origin (curl, server-to-server) is allowed here and stopped by
    the ticket check instead."""
    h = _host_of(req.headers.get("origin")) or _host_of(req.headers.get("referer"))
    return (not h) or h in ALLOWED_HOSTS or h in OWN_VERCEL_HOSTS or h in _deployment_hosts()

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

def fibre_detail(im, r_frac=None, size=768):
    """How much real fibre texture this crop carries, measured where the fibres actually are.

    laplacian_var() judges a 256px copy of the whole square, so it cannot tell a sharp iris from a soft one
    and it counts eyelashes and skin at the edge. Measured on four real photos of the same eye, it ranked the
    softest frame highest purely because that frame was the largest. This measures the energy in the fibre
    band inside the iris ring only, at a fixed working size, so two photos taken at different distances are
    directly comparable."""
    r_frac = r_frac or iris_radius_frac()
    g = to_gray(im.resize((size, size), Image.LANCZOS))
    blur = np.asarray(Image.fromarray(g.astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.0))).astype(np.float32)
    hi = g - blur
    yy, xx = np.mgrid[0:size, 0:size]
    d = np.sqrt((xx - size / 2) ** 2 + (yy - size / 2) ** 2) / (r_frac * size)
    ring = (d > 0.30) & (d < 0.92)
    return float(hi[ring].std()) if ring.any() else 0.0

FIBRE_RING = (0.30, 0.92)    # the fibre ring, as a share of the iris radius: inside is pupil, outside limbus and lids
FIBRE_BAND = (1.2, 3.5)      # difference-of-Gaussians sigmas at the 768 working size
FIBRE_GLARE_GROW = 15        # MaxFilter window at 768 around the glare mask: the rim of a reflection is a band-pass edge too
FIBRE_SECTOR_MIN = 0.15      # a 45-degree sector only votes if this share of its ring survives the glare mask

def _grow_mask(m, k):
    """Square dilation of a boolean mask with a k x k window (k odd). Same result as PIL MaxFilter(k) on a
    0/255 mask, done as two 1-D passes because PIL's rank filter costs ~0.3 s at 768."""
    r = k // 2
    out = m
    for ax in (0, 1):
        p = np.pad(out, [(r, r) if a == ax else (0, 0) for a in (0, 1)])
        n = out.shape[ax]
        acc = np.zeros_like(out)
        for s in range(k):
            acc |= np.take(p, np.arange(s, s + n), axis=ax)
        out = acc
    return out

def reflection_core(crop, r_px, boxes):
    """The reflection itself, for measuring how much of the iris it hides: bright, unsaturated pixels inside the
    vision model's glare boxes (the in-box rule of glare_mask, eroded the same way), with none of glare_mask's
    halo or dilation. glare_mask() is built generous for inpainting, and on a pale or brightly exposed iris it
    grows over bright fibres: +1/3 EV took the site's sharp sample eye from 15% to 28% of the ring with the same
    single reflection. Tied to the boxes, the reading follows the reflection, not the exposure. No box, no reflection."""
    S = crop.size[0]
    boxed = _box_mask(S, boxes)
    if not boxed.any(): return boxed
    hsv = np.asarray(crop.convert("HSV")).astype(np.int16)
    v, s = hsv[..., 2], hsv[..., 1]
    yy, xx = np.mgrid[0:S, 0:S]
    dist = np.sqrt((xx - S / 2) ** 2 + (yy - S / 2) ** 2)
    _, thr = _glare_v_threshold(v, dist, r_px)
    core = boxed & (dist < r_px * 0.93) & (v > thr - 15) & (s < 110)
    return np.asarray(Image.fromarray((core * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3))) > 0

def fibre_measure(crop, r_frac=None, size=768, boxes=None):
    """Glare-robust fibre detail of a square iris crop: (fibre_score, glare_on_fibres_pct).

    fibre_detail() can be fooled. A crisp reflection is the sharpest thing in a soft photo: a painted 12%
    window glint lifted a soft frame from 4.57 to 6.04, past the old 'good' line. One bright sector (lashes,
    a glint) also moves a whole-ring number. So the glare mask is cut out first (grown, because its rim is
    an edge too), only the fibre band survives (a DoG: finer than 1.2 px is sensor noise and JPEG, coarser
    than 3.5 px is shading and the pupil), and the score is the median over eight 45-degree sectors, so no
    single sector carries it. This band alone is blind to the finest fibres: a x4 digital zoom or a blurred
    frame run through an unsharp mask keeps most of its energy here, so the caller also checks fibre_detail()
    (see analyze.py) before calling a photo good.
    Everything runs on one working copy of `size` px, so the reading does not depend on how large the iris
    was in the photo: the glare mask's filters are fixed pixel windows, and on the crop's own grid the same
    reflection read 10.5% of the ring on a 187 px crop and 18.5% on a 1249 px one. It also keeps the cost
    flat, 0.3-0.4 s for any crop from 320 to 1792 px, instead of growing with the crop.
    boxes: vision glare boxes in crop pixels. glare_on_fibres_pct: share of the fibre ring hidden by the
    reflections the vision model reported (reflection_core), so no box means 0."""
    r_frac = r_frac or iris_radius_frac()
    S = crop.size[0]
    work = crop if S == size else crop.resize((size, size), Image.LANCZOS)
    wboxes = [[c * size / float(S) for c in b] for b in (boxes or [])]
    # the generous inpainting mask only decides which pixels the score ignores: it also catches a reflection
    # the vision model missed, and throwing away a few bright fibres only ever lowers the score
    hard, _, _ = glare_mask(work, r_frac * size, wboxes)
    grown = _grow_mask(hard > 0, FIBRE_GLARE_GROW)
    reflection = reflection_core(work, r_frac * size, wboxes)
    g = Image.fromarray(to_gray(work).astype(np.uint8))
    band = (np.asarray(g.filter(ImageFilter.GaussianBlur(FIBRE_BAND[0]))).astype(np.float32)
            - np.asarray(g.filter(ImageFilter.GaussianBlur(FIBRE_BAND[1]))).astype(np.float32))
    yy, xx = np.mgrid[0:size, 0:size]
    d = np.sqrt((xx - size / 2) ** 2 + (yy - size / 2) ** 2) / (r_frac * size)
    ang = (np.degrees(np.arctan2(yy - size / 2, xx - size / 2)) + 360.0) % 360.0
    ring = (d > FIBRE_RING[0]) & (d < FIBRE_RING[1])
    glare_pct = 100.0 * float(reflection[ring].mean()) if ring.any() else 0.0
    keep = ring & ~grown
    sectors = []
    for a0 in range(0, 360, 45):
        sec = ring & (ang >= a0) & (ang < a0 + 45)
        k = keep & sec
        if k.sum() >= max(500, FIBRE_SECTOR_MIN * sec.sum()):
            sectors.append(float(band[k].std()))
    return (float(np.median(sectors)) if sectors else 0.0), glare_pct

def fibre_score(crop, r_frac=None, size=768, boxes=None):
    """The glare-robust fibre detail alone; see fibre_measure()."""
    return fibre_measure(crop, r_frac, size, boxes)[0]

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
        # each key is removed from gen_cfg, so each repair can happen at most once -> the loop always terminates.
        # An explicit imageSize is never dropped: without imageConfig the model answers at its 1K default, so a
        # 4K order would quietly come back at 1K. That case falls through and raises instead.
        sized = "imageSize" in (gen_cfg.get("imageConfig") or {})
        if r.status_code == 400 and "imageConfig" in gen_cfg and not sized:
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
def _box_mask(S, boxes):
    """Union of the vision glare boxes (crop pixels) on an S x S grid, each grown a little because the model
    usually marks only the brightest core. Clamped to the grid BEFORE slicing: a box above or left of the crop
    (a glint on the sclera, the skin or the other eye) would otherwise give a negative slice stop, which Python
    counts from the far end, and mark most of the iris. Boxes that miss the grid, or are not finite, add nothing."""
    m = np.zeros((S, S), bool)
    for b in (boxes or []):
        try:
            x1, y1, x2, y2 = [int(round(float(c))) for c in b]
        except (TypeError, ValueError, OverflowError):
            continue
        g = max(4, int(0.25 * max(x2 - x1, y2 - y1)))
        xa, xb, ya, yb = max(0, x1 - g), min(S, x2 + g), max(0, y1 - g), min(S, y2 + g)
        if xb > xa and yb > ya: m[ya:yb, xa:xb] = True
    return m

def _glare_v_threshold(v, dist, r_px):
    """Brightness a specular core must pass: well above this iris's own median (pupil left out), never below 200."""
    ring = (dist < r_px * 0.93) & (dist > r_px * 0.42)
    med_v = float(np.median(v[ring])) if ring.any() else 128.0
    return med_v, max(200.0, med_v + 45.0)

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
    med_v, thr = _glare_v_threshold(v, dist, r_px)
    core = ((v > thr) & (s < 100)) & inside
    core |= _box_mask(S, extra_boxes) & inside & (v > thr - 15) & (s < 110)
    core_img = Image.fromarray((core * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3))
    core_np = np.asarray(core_img) > 0
    area = max(1.0, float(inside.sum()))
    # contrast-adaptive halo: a pale, blurry iris hides its reflection halo in a few brightness units,
    # a crisp high-contrast iris would swallow bright fibres with the same rule
    rest = ring & ~core_np
    sd = float(v[rest].std()) if rest.any() else 30.0
    halo_thr = med_v + float(np.clip(0.5 * sd, 10.0, 28.0))
    near_px = int(S * (0.05 if sd < 40 else 0.03)) | 1
    # _grow_mask is pixel-identical to PIL MaxFilter on a mask (checked on 84 random masks, borders included),
    # and a 39 px window at 768 costs 0.1 s instead of 1.4 s
    near = _grow_mask(core_np, near_px)
    halo = near & (dist < r_px * 0.97) & (v > halo_thr) & (s < 120)
    m = core_np | halo
    if m.sum() / area > 0.25:           # a real reflection never covers a quarter of the iris: halo grew into bright fibres
        m = core_np                     # fall back to the eroded core, never to an empty mask: discarding it
                                        # would leave the very worst glare untouched in the artwork
    mi = Image.fromarray((_grow_mask(m, 9) * 255).astype(np.uint8))
    hard = np.asarray(mi)
    feather = np.asarray(mi.filter(ImageFilter.GaussianBlur(5))).astype(np.float32) / 255.0
    pct = 100.0 * float((hard > 0).sum()) / area
    return hard, feather, pct

ROTATION_DONORS = (24, -24, 48, -48, 78, -78, 110, -110)

def _box1(a, r, ax):
    """Running mean of width 2r+1 along one axis, reflect-padded, via a cumulative sum."""
    n = a.shape[ax]
    r = int(min(r, max(n - 1, 1)))
    lo = np.take(a, np.arange(r - 1, -1, -1), axis=ax)
    hi = np.take(a, np.arange(n - 1, n - r - 1, -1), axis=ax)
    b = np.concatenate([lo, a, hi], axis=ax)
    cs = np.cumsum(b, axis=ax, dtype=np.float64)
    cs = np.concatenate([np.zeros_like(np.take(cs, [0], axis=ax)), cs], axis=ax)
    top = np.take(cs, np.arange(2 * r + 1, 2 * r + 1 + n), axis=ax)
    bot = np.take(cs, np.arange(0, n), axis=ax)
    return ((top - bot) / (2 * r + 1)).astype(np.float32)


def _blur_f(plane, rad):
    """Gaussian-equivalent blur that stays in floating point. PIL cannot blur a float plane, and a weight map
    quantised to 256 steps divides badly, so three box passes stand in for the Gaussian."""
    a = plane.astype(np.float32)
    r = max(1, int(round(rad)))
    for _ in range(3):
        a = _box1(_box1(a, r, 0), r, 1)
    return a


def mirror_prefill(crop, feather):
    """Fill the reflection from the same radius at a nearby angle.

    An iris is organised radially: brightness, colour and pigment change with distance from the pupil and stay
    comparatively steady around it. The earlier version donated from the point-mirrored side - same radius, opposite
    angle - so an eye with a darker sector across from the highlight got that darkness stamped exactly where the
    highlight had been. Rotating about the pupil centre keeps the radius exact while staying near in angle, and
    several offsets are averaged so a donor that is itself under glare simply does not vote."""
    arr = np.asarray(crop).astype(np.float32)
    S = crop.size[0]
    a = np.clip(feather, 0.0, 1.0)[..., None]
    m_img = Image.fromarray((np.clip(feather, 0, 1) * 255).astype(np.uint8))
    ones = Image.fromarray(np.full((S, S), 255, np.uint8))

    cands, weights = [], []
    for deg in ROTATION_DONORS:
        rot = np.asarray(crop.rotate(deg, resample=Image.BICUBIC)).astype(np.float32)
        rot_m = np.asarray(m_img.rotate(deg, resample=Image.BICUBIC)).astype(np.float32) / 255.0
        # rotation swings the frame corners in; those pixels are not iris and must not donate
        inside = np.asarray(ones.rotate(deg, resample=Image.BICUBIC)).astype(np.float32) / 255.0
        cands.append(rot)
        weights.append(np.clip(inside, 0, 1) * (1.0 - np.clip(rot_m, 0, 1)))
    C = np.stack(cands, 0)
    W = np.stack(weights, 0)[..., None]

    tot = W.sum(0)
    src = (C * W).sum(0) / np.maximum(tot, 1e-3)
    blur = np.asarray(crop.filter(ImageFilter.GaussianBlur(S * 0.03))).astype(np.float32)
    src = np.where(tot < 0.35, blur, src)          # nowhere clean to borrow from

    # Match the donor to the local tone of the ring it lands in. The reference has to be measured from the
    # glare-free pixels only: blurring the original would fold the reflection's own brightness into the target
    # and pull the fill towards the very highlight being removed.
    rad = S * 0.05
    w = np.clip(1.0 - np.clip(feather, 0, 1), 0.0, 1.0)
    wb = _blur_f(w, rad)
    ok = wb > 0.02
    base_lo = np.stack([np.where(ok, _blur_f(arr[..., c] * w, rad) / np.maximum(wb, 1e-3),
                                 _blur_f(src[..., c], rad)) for c in range(3)], -1)
    src_lo = np.stack([_blur_f(src[..., c], rad) for c in range(3)], -1)
    src = src + (base_lo - src_lo)
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

def soft_shoulders(arr, toe=18.0, shoulder=208.0, lo=2.0, hi=253.0):
    """Roll the tails off instead of clipping them.

    Sculpting pushes some fibres past the rails, and a clipped fibre is not contrast, it is destroyed detail.
    Measured in the true iris ring, the shipping grade clipped 7.1% of it; eleven professional prints clip
    0.00-0.03%. This maps everything above the shoulder and below the toe asymptotically towards the limits,
    so nothing ever lands on them and the midtones are untouched."""
    out = arr.copy()
    hiM = arr > shoulder
    if hiM.any():
        span = max(hi - shoulder, 1e-3)
        out[hiM] = shoulder + span * (1.0 - np.exp(-(arr[hiM] - shoulder) / span))
    loM = arr < toe
    if loM.any():
        span = max(toe - lo, 1e-3)
        out[loM] = toe - span * (1.0 - np.exp(-(toe - arr[loM]) / span))
    return out

def chroma_lock(ai, src, blur=1.6, amount=1.0):
    """Keep the structure the model restored, put the client's real colour back.

    The model may move luminance, because that is where the fibres live. It may not move colour, because colour
    is the one thing the client can check against a mirror. Measured on a weak photo the model drifted Cb by
    -10 and Cr by +7 and desaturated by 30%; after this lock the drift is under one unit. The chroma planes are
    blurred slightly so a sub-pixel drift in the model's output cannot show up as colour fringing."""
    if src.size != ai.size:
        src = src.resize(ai.size, Image.LANCZOS)
    y, cb_ai, cr_ai = ai.convert("YCbCr").split()
    _, cb, cr = src.convert("YCbCr").split()
    if blur:
        cb = cb.filter(ImageFilter.GaussianBlur(blur))
        cr = cr.filter(ImageFilter.GaussianBlur(blur))
    if amount < 1.0:
        cb = Image.blend(cb_ai, cb, amount)
        cr = Image.blend(cr_ai, cr, amount)
    return Image.merge("YCbCr", (y, cb, cr)).convert("RGB")

DARK_BLEND = 24.0        # below this luminance a colour ratio is noise, so the lift is applied as an offset
PUPIL_EDGE_FRAC = 0.25
PUPIL_DARK = (10.0, 30.0)   # pupil colour: full neutral below the first luminance, none above the second
PUPIL_FLAT = (0.50, 0.85)   # reflections in the pupil below the first share of the iris brightness are flattened fully, above the second not at all


SCLERA_RAMP = (0.70, 0.84)    # the intruder test fades in across this band of the iris radius
LID_SECTORS = 48              # 7.5 degree arcs of the outer band, each judged as lid or iris
LID_BRIGHT = (1.30, 1.55)     # an arc's median brightness vs its radius: iris arcs stay below the first


def pale_intruders(arr, rr):
    """How much of each pixel is eyelid skin or sclera reaching into the frame, 0..1.

    The earlier test compared everything beyond 0.72 of the radius with the INNER iris and switched on with a
    hard edge. A light eye whose outer fibres are cream then had its whole outer ring darkened, with a visible
    circle where the test began - the first thing a customer would notice. Brightness alone cannot separate a
    lid from a cream patch: measured on real irises, the brightest patches reach 1.4-1.5x the median of their own
    radius, and a lid is about 1.7x. What does separate them is shape. A lid comes in from outside and covers a
    broad arc right up to the edge of the frame; a patch of pale fibres is local. So a sector of the outer band
    has to read as lid first, and only inside such sectors are the brighter pixels pushed out, fading in over a
    band of radius instead of starting at a line."""
    S = arr.shape[0]
    mx, mn = arr.max(axis=2), arr.min(axis=2)
    sat = (mx - mn) / np.maximum(mx, 1.0)
    lum = arr.mean(axis=2)
    rad = max(1.0, S * 0.025)
    lum_b, sat_b = _blur_f(lum, rad), _blur_f(sat, rad)

    centres, ml, ms = [], [], []
    for a in np.arange(0.40, 1.00, 0.04):
        sel = (rr >= a) & (rr < a + 0.04)
        if sel.sum() > 40:
            centres.append(a + 0.02); ml.append(float(np.median(lum_b[sel]))); ms.append(float(np.median(sat_b[sel])))
    if len(centres) < 3:
        return np.zeros_like(lum)
    # A heavy lid can own a whole radius, so the reference may not climb above the iris because of it. The iris
    # reference is the BRIGHTEST inner radius: the innermost bins can still be pupil on a dilated eye, which is
    # exactly how the old test mistook a light outer ring for sclera. Outer radii of a real iris are no brighter
    # than its brightest inner one, since the limbal ring darkens towards the edge.
    inner = max(m for c, m in zip(centres, ml) if c < 0.80)
    ml = np.minimum(np.array(ml), inner * 1.10)
    ref_l = np.interp(rr, centres, ml).astype(np.float32)
    ref_s = np.interp(rr, centres, ms).astype(np.float32)
    ratio = lum_b / np.maximum(ref_l, 1.0)
    sratio = sat_b / np.maximum(ref_s, 1e-3)

    # which arcs of the outer band read as lid: broad, bright, and no more colourful than the iris there
    yy, xx = np.mgrid[0:S, 0:S]
    ang = (np.degrees(np.arctan2(yy - S / 2 + 0.5, xx - S / 2 + 0.5)) + 360.0) % 360.0
    step = 360.0 / LID_SECTORS
    band = (rr > 0.82) & (rr < 0.94)
    gate = np.zeros(LID_SECTORS, np.float32)
    for i in range(LID_SECTORS):
        sel = band & (ang >= i * step) & (ang < (i + 1) * step)
        if sel.sum() > 20:
            r_ = float(np.median(ratio[sel])); s_ = float(np.median(sratio[sel]))
            gate[i] = np.clip((r_ - LID_BRIGHT[0]) / (LID_BRIGHT[1] - LID_BRIGHT[0]), 0, 1) * np.clip((1.05 - s_) / 0.25, 0, 1)
    gate = np.maximum(gate, 0.5 * (np.roll(gate, 1) + np.roll(gate, -1)) * (gate > 0))   # close pinholes inside a lid
    g = np.interp(ang, np.arange(LID_SECTORS) * step + step / 2, gate, period=360.0)

    brighter = np.clip((ratio - 1.12) / 0.30, 0.0, 1.0)
    lo, hi = SCLERA_RAMP
    ramp = np.clip((rr - lo) / (hi - lo), 0.0, 1.0)
    return (brighter * g * ramp).astype(np.float32)


def pupil_radius(lum, rr):
    """Where the pupil ends, in units of the iris radius, read from the image: the first radius at which the
    median brightness climbs halfway from the centre to the iris. None if the centre is not dark."""
    edges = np.arange(0.0, 0.86, 0.02)
    meds = []
    for a, b in zip(edges[:-1], edges[1:]):
        sel = (rr >= a) & (rr < b)
        meds.append(float(np.median(lum[sel])) if sel.sum() > 12 else np.nan)
    meds = np.array(meds)
    core = np.nanmedian(meds[:4])
    iris = np.nanmedian(meds[(edges[:-1] >= 0.6) & (edges[:-1] < 0.84)])
    if not np.isfinite(core) or not np.isfinite(iris) or core > 45.0 or iris - core < 25.0:
        return None
    # a quarter of the way up, not half: on a brown eye with a darker collarette, halfway counted that iris
    # tissue as pupil and greyed it. Erring small only leaves a sliver of rim untouched, which is harmless.
    half = core + PUPIL_EDGE_FRAC * (iris - core)
    above = np.where(meds > half)[0]
    if not len(above):
        return None
    return float(np.clip(edges[above[0]], 0.10, 0.72))


def neutral_pupil(arr, rr, tone):
    """The pupil is a hole, not a surface. Take its colour out, and flatten whatever it reflected.

    `tone` is the neutral luminance the pupil should sit at. Two jobs:
    1. colour: what a phone records in a pupil is sensor noise, and every professional print measured is neutral
       there; gated on darkness so the pigmented ruff keeps its colour.
    2. reflections: a pupil mirrors the room - a window, furniture, the person holding the phone - and the image
       model renders that faithfully. None of it belongs to the eye, so inside the pupil anything brighter than
       its own dark floor is pulled down to it. Gated on brightness relative to the iris, so if the edge estimate
       ever overshoots into iris tissue that tissue is left alone, and the very brightest speck survives as a
       natural catchlight."""
    lum = tone
    rho = pupil_radius(lum, rr)
    if rho is None:
        return arr
    inside = np.clip((rho * 1.04 - rr) / max(rho * 0.10, 1e-3), 0.0, 1.0)      # soft edge at the pupil rim
    lo, hi = PUPIL_DARK
    dark = np.clip((hi - lum) / (hi - lo), 0.0, 1.0)
    w = inside * dark

    core = rr < 0.8 * rho
    ring = (rr > 0.60) & (rr < 0.84)
    if core.sum() > 20 and ring.any():
        floor = float(np.percentile(lum[core], 15))
        iris_med = float(np.median(lum[ring]))
        rim = np.clip((rho - rr) / max(rho * 0.10, 1e-3), 0.0, 1.0)             # full inside 0.9 rho, none at the rim
        not_iris = np.clip((PUPIL_FLAT[1] * iris_med - lum) / ((PUPIL_FLAT[1] - PUPIL_FLAT[0]) * iris_med), 0.0, 1.0)
        flat = rim * not_iris
        lum = lum - flat * np.maximum(lum - floor, 0.0)
        w = np.maximum(w, flat)

    w = w[..., None]
    return arr * (1.0 - w) + lum[..., None] * w


def studio_grade(im, r_frac, out=1024, fill=None, local=None, micro=None, sat=None, sclera=None, trim=None):
    """Turn a masked iris square into the fine-art frame: limbus-tight, pure black outside, sculpted fibres.

    A phone crop carries a slice of sclera or eyelid at the bottom of the disk and sits small inside its frame.
    A studio print does neither: the iris is the whole picture. Everything here is arithmetic on the pixels the
    camera captured, so it deepens what is real instead of inventing what is not."""
    fill = STUDIO_FILL if fill is None else fill
    # the studio macro render already arrives razor sharp. Sharpening it again is what produced the
    # speckled dark pixels the owner spotted, so the sculpting is scaled down by how much fibre detail
    # the input already carries: none of it at professional levels, all of it on a soft crop.
    if local is None or micro is None:
        have = fibre_detail(im, r_frac)
        ease = float(np.clip((9.0 - have) / 6.0, 0.0, 1.0))
        local = STUDIO_LOCAL * ease if local is None else local
        micro = STUDIO_MICRO * ease if micro is None else micro
    trim = STUDIO_TRIM if trim is None else trim
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
        arr = arr * (1.0 - pale_intruders(arr, rr) * sclera)[..., None]

    # 2. sculpt: large-radius unsharp gives the fibres relief, small-radius separates them. This runs on
    #    luminance alone - applied per channel it would pull the channels apart and quietly saturate the
    #    whole iris, which is not enhancement, it is a colour cast.
    base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    W_LUM = np.array([0.299, 0.587, 0.114], dtype=np.float32)
    lum = (arr * W_LUM).sum(axis=2, keepdims=True)
    big = (np.asarray(base.filter(ImageFilter.GaussianBlur(max(2.0, S * 0.045)))).astype(np.float32) * W_LUM).sum(axis=2, keepdims=True)
    sml = (np.asarray(base.filter(ImageFilter.GaussianBlur(max(1.0, S * 0.004)))).astype(np.float32) * W_LUM).sum(axis=2, keepdims=True)
    sculpted = soft_shoulders(lum + (lum - big) * local + (lum - sml) * micro)
    # Midtones take the new luminance as a ratio, which keeps every pixel's colour proportions intact. Near
    # black that ratio stops meaning anything: the toe lifts a pupil of luminance 0.9 to 7.5, and a ratio of
    # 8 multiplies whatever faint tint the sensor left there into a navy disc. So dark pixels take the same
    # luminance change as a neutral offset instead, and the two blend smoothly across the shadows.
    ratio = sculpted / np.maximum(lum, 1.0)
    t = np.clip(lum / DARK_BLEND, 0.0, 1.0)
    arr = t * (arr * ratio) + (1.0 - t) * (arr + (sculpted - lum))
    arr = soft_shoulders(arr)      # per channel: keeps a saturated dark fibre off zero once saturation is added

    # 3. colour depth, on its own knob, so the number means what it says
    grey = (arr * W_LUM).sum(axis=2, keepdims=True)
    arr = grey + (arr - grey) * (1.0 + sat)

    # 3b. the pupil is a hole, not a surface: the colour a phone records there is sensor noise and a reflection
    #     of the room, and every professional print measured is neutral there. Found from the image itself and
    #     gated on darkness, so the pigmented ruff and any iris crypt keep their colour. Its tone is taken from
    #     the luminance before the per-channel guard, which would otherwise lift a black hole to dark grey.
    arr = neutral_pupil(arr, rr, sculpted[..., 0])

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

# ----------------------------------------------------------------------------- colour QA
QA_RING = (0.45, 0.90)       # iris ring for the colour check: clear of most pupils and of the limbal shadow
QA_SIZE = 256                # both images are compared at this size...
QA_BLUR = 2.0                # ...after a light blur: the model redraws fibres, and a fibre moved by a pixel is not a colour change
QA_RING_DE00_MAX = 10.0      # median ring dE00 above this = the render no longer looks like the photo's eye colour.
                             # Measured 2026-09-23 on ten real renders: with lightness held equal, every render
                             # after chroma_lock is within 0.6-1.3 of its source (3.2-5.9 before the lock), so
                             # what is left is the model relighting the iris: 215120 moved L* -1.6 (2.8, reads
                             # true), 215102 +13.9 (13.2) and 215208 +18.0 (16.0) came back visibly paler
PUPIL_NEUTRAL_MAX = 1.5      # |Cb| and |Cr| of the pupil core: every professional print measured sits inside this

def srgb_to_lab(rgb):
    """sRGB (0-255, any shape ending in 3) to CIELAB, D65 / 2 degree: the same conversion as skimage.color.rgb2lab."""
    c = np.asarray(rgb, dtype=np.float64) / 255.0
    lin = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    xyz = lin @ np.array([[0.412453, 0.357580, 0.180423],
                          [0.212671, 0.715160, 0.072169],
                          [0.019334, 0.119193, 0.950227]]).T
    xyz = xyz / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16.0 / 116.0)
    return np.stack([116.0 * f[..., 1] - 16.0, 500.0 * (f[..., 0] - f[..., 1]), 200.0 * (f[..., 1] - f[..., 2])], -1)

def ciede2000(lab1, lab2):
    """CIEDE2000 colour difference (kL = kC = kH = 1; Sharma, Wu and Dalal 2005), vectorised over any shape
    ending in 3. numpy only, so the deployed function does not need scikit-image."""
    L1, a1, b1 = np.moveaxis(np.asarray(lab1, np.float64), -1, 0)
    L2, a2, b2 = np.moveaxis(np.asarray(lab2, np.float64), -1, 0)
    p7 = 25.0 ** 7
    c7 = ((np.hypot(a1, b1) + np.hypot(a2, b2)) / 2.0) ** 7
    G = 0.5 * (1.0 - np.sqrt(c7 / (c7 + p7)))
    a1p, a2p = (1.0 + G) * a1, (1.0 + G) * a2
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p, h2p = np.arctan2(b1, a1p) % (2 * np.pi), np.arctan2(b2, a2p) % (2 * np.pi)
    grey = (C1p * C2p) == 0                              # a hue difference means nothing for a neutral colour
    dLp, dCp = L2 - L1, C2p - C1p
    dhp = h2p - h1p
    dhp = np.where(dhp > np.pi, dhp - 2 * np.pi, np.where(dhp < -np.pi, dhp + 2 * np.pi, dhp))
    dhp = np.where(grey, 0.0, dhp)
    dHp = 2.0 * np.sqrt(C1p * C2p) * np.sin(dhp / 2.0)
    Lbp, Cbp, hs = (L1 + L2) / 2.0, (C1p + C2p) / 2.0, h1p + h2p
    hbp = np.where(np.abs(h1p - h2p) <= np.pi, hs / 2.0, np.where(hs < 2 * np.pi, (hs + 2 * np.pi) / 2.0, (hs - 2 * np.pi) / 2.0))
    hbp = np.where(grey, hs, hbp)
    T = (1.0 - 0.17 * np.cos(hbp - np.radians(30.0)) + 0.24 * np.cos(2.0 * hbp)
         + 0.32 * np.cos(3.0 * hbp + np.radians(6.0)) - 0.20 * np.cos(4.0 * hbp - np.radians(63.0)))
    dtheta = np.radians(30.0) * np.exp(-(((np.degrees(hbp) - 275.0) / 25.0) ** 2))
    cb7 = Cbp ** 7
    RT = -np.sin(2.0 * dtheta) * 2.0 * np.sqrt(cb7 / (cb7 + p7))
    SL = 1.0 + 0.015 * (Lbp - 50.0) ** 2 / np.sqrt(20.0 + (Lbp - 50.0) ** 2)
    SC = 1.0 + 0.045 * Cbp
    SH = 1.0 + 0.015 * Cbp * T
    return np.sqrt((dLp / SL) ** 2 + (dCp / SC) ** 2 + (dHp / SH) ** 2 + RT * (dCp / SC) * (dHp / SH))

def qa_colour(result, source, r_frac=None, parts=False):
    """Median CIEDE2000 over the iris ring between a result and the source crop it was made from (both
    square iris crops with the same framing). chroma_lock keeps the hue, so what this mostly sees is the
    model moving the tone of the whole iris - a change a customer can check in a mirror.
    parts=True also returns (median dE00 with lightness held equal, median L* shift), which say why."""
    r_frac = r_frac or iris_radius_frac()
    n = QA_SIZE
    def prep(im):
        return np.asarray(im.convert("RGB").resize((n, n), Image.LANCZOS).filter(ImageFilter.GaussianBlur(QA_BLUR)))
    yy, xx = np.mgrid[0:n, 0:n]
    rr = np.sqrt((xx - n / 2 + 0.5) ** 2 + (yy - n / 2 + 0.5) ** 2) / (r_frac * n)
    ring = (rr > QA_RING[0]) & (rr < QA_RING[1])
    a, b = srgb_to_lab(prep(result)[ring]), srgb_to_lab(prep(source)[ring])
    de = float(np.median(ciede2000(a, b)))
    if not parts:
        return de
    same_l = a.copy(); same_l[:, 0] = b[:, 0]
    return de, float(np.median(ciede2000(same_l, b))), float(np.median(a[:, 0] - b[:, 0]))

def pupil_core_chroma(graded, fill=None, trim=None):
    """(Y, Cb, Cr) of the pupil core of a studio_grade() disk, or None when no dark pupil is found. The core
    and the pupil edge are found exactly as neutral_pupil() finds them, with the radius mapped back from the
    graded frame (disk = fill of the frame, cut at trim of the iris radius) to the source iris."""
    fill = STUDIO_FILL if fill is None else fill
    trim = STUDIO_TRIM if trim is None else trim
    im = graded.convert("RGB")
    if im.size[0] > 512:
        im = im.resize((512, 512), Image.BOX)             # area average: the core mean is unchanged, the test is faster
    n = im.size[0]
    yy, xx = np.mgrid[0:n, 0:n]
    rr = np.sqrt((xx - n / 2 + 0.5) ** 2 + (yy - n / 2 + 0.5) ** 2) / (n * fill / 2.0) * trim
    ycc = np.asarray(im.convert("YCbCr")).astype(np.float32)
    rho = pupil_radius(ycc[..., 0], rr)
    if rho is None:
        return None
    core = rr < 0.8 * rho
    if core.sum() < 12:
        return None
    return float(ycc[..., 0][core].mean()), float(ycc[..., 1][core].mean()) - 128.0, float(ycc[..., 2][core].mean()) - 128.0

def pupil_neutral(graded, fill=None, trim=None):
    """Is the pupil core of a graded disk colour-neutral (|Cb|, |Cr| <= 1.5)? None when no pupil is found."""
    c = pupil_core_chroma(graded, fill, trim)
    return None if c is None else bool(abs(c[1]) <= PUPIL_NEUTRAL_MAX and abs(c[2]) <= PUPIL_NEUTRAL_MAX)

def colour_qa(stage, result=None, source=None, r_frac=None, graded=None):
    """Colour QA for one stage of the chain: logged and returned, never raised and never blocking, because
    there are no orders to hold yet. ok is true only when something was measured and nothing measured failed."""
    try:
        de, note = None, ""
        if result is not None and source is not None:
            de, hue_only, dl = qa_colour(result, source, r_frac, parts=True)
            note += f" colour-only dE00 {hue_only:.2f} lightness shift {dl:+.1f}"
        core = None if graded is None else pupil_core_chroma(graded)
        pn = None if core is None else bool(abs(core[1]) <= PUPIL_NEUTRAL_MAX and abs(core[2]) <= PUPIL_NEUTRAL_MAX)
        ok = (de is not None or pn is not None) and (de is None or de <= QA_RING_DE00_MAX) and pn is not False
        qa = {"ring_de00": None if de is None else round(de, 2), "pupil_neutral": pn, "ok": bool(ok)}
        if core is not None:
            note += f" pupil core Y {core[0]:.1f} Cb {core[1]:+.2f} Cr {core[2]:+.2f}"
    except Exception as e:  # noqa: a QA fault must never cost the customer their picture
        qa = {"ring_de00": None, "pupil_neutral": None, "ok": False}
        note = " qa error " + _scrub(repr(e))[:160]
    print("snapeyes qa", stage, json.dumps(qa) + note, flush=True)
    return qa

# ----------------------------------------------------------------------------- lamp cast at capture
SCLERA_RING = (1.15, 1.55)   # just outside the limbus, in iris radii: sclera to the sides, lids above and below
SCLERA_SIDES = 0.60          # only |sin(angle)| below this: the left and right wedges, where the sclera is
SCLERA_TOP = 70              # of those, the pixels at or above this luminance percentile...
SCLERA_BLOWN = 245           # ...that are not blown to white (a glint on the tear film has no colour left)...
SCLERA_MAX_SAT = 0.75        # ...and, of those, the less saturated half: the white of the eye, not skin or lashes

def sclera_pixels(im, cx, cy, r):
    """RGB of the white of the eye beside the iris (N x 3 float), or None when too little is visible.
    cx, cy, r in pixels of im. The saturation gate is relative on purpose: under a strong lamp the sclera
    itself is saturated and its red channel clips, and a fixed 'low saturation, unclipped' rule then throws
    away exactly the pixels that show the cast. A clipped channel only understates the cast."""
    W, H = im.size
    R = SCLERA_RING[1] * r
    x0, y0, x1, y1 = max(0, int(cx - R)), max(0, int(cy - R)), min(W, int(cx + R) + 1), min(H, int(cy + R) + 1)
    if x1 - x0 < 8 or y1 - y0 < 8:
        return None
    a = np.asarray(im.crop((x0, y0, x1, y1)).convert("RGB")).astype(np.float32)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    dx, dy = xx - cx, yy - cy
    d = np.sqrt(dx ** 2 + dy ** 2) / max(r, 1.0)
    band = (d >= SCLERA_RING[0]) & (d <= SCLERA_RING[1]) & (np.abs(dy) < SCLERA_SIDES * np.maximum(d * r, 1.0))
    px = a[band]
    if len(px) < 200:
        return None
    mx, mn = px.max(1), px.min(1)
    lum = px @ np.array([0.299, 0.587, 0.114], np.float32)
    sat = (mx - mn) / np.maximum(mx, 1.0)
    bright = (lum >= np.percentile(lum, SCLERA_TOP)) & (mn < SCLERA_BLOWN) & (sat < SCLERA_MAX_SAT)
    if bright.sum() < max(60, 0.03 * len(px)):
        return None
    sel = bright & (sat <= np.median(sat[bright]))
    return px[sel]

def sclera_tint(im, cx, cy, r):
    """CIELAB of the white of the eye beside the iris: {"L", "a", "b", "n"}, or None when too little is visible.
    A healthy sclera is a slightly warm white, so a strong b* either way is the light, not the eye."""
    px = sclera_pixels(im, cx, cy, r)
    if px is None:
        return None
    L_, a_, b_ = srgb_to_lab(np.median(px, axis=0))
    return {"L": float(L_), "a": float(a_), "b": float(b_), "n": int(len(px))}

def compose(iris, style="celestial_gold", title=None, names="", watermark=True, r_frac=None, size=1024, keep=None):
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
    if keep is not None:
        keep["graded"] = graded   # handed back for the colour QA; changes nothing in the picture
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
        d.text((size / 2, size * 0.945), "SNAPEYES  ·  FINE ART IRIS PRINT", font=fs, fill=(150, 155, 170), anchor="mm")
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
        d.text((size / 2, size * 0.05), "WATERMARKED PREVIEW  ·  UNLOCK FULL SIZE", font=fp, fill=st["accent"], anchor="mm")
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
