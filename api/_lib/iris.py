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

class ClientError(ValueError):
    """Bad input the caller can fix. Its message is written for the customer and is returned as is, so it
    must never carry internals or echo what the caller sent."""

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
        if not isinstance(body, dict):   # [], "x", 5 or null parse as JSON too; every endpoint takes an object
            raise ClientError("Send a JSON object.")
        out = fn(body)
        out["ms"] = int((time.time() - t0) * 1000)
        send_json(req, 200, out)
    except ClientError as e:
        print("snapeyes client error:", _scrub(repr(e))[:200], flush=True)
        send_json(req, 400, {"ok": False, "error": str(e), "ms": int((time.time() - t0) * 1000)})
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

def b64_to_pil(s, max_side=None):
    """max_side: refuse (ClientError) an image whose longer side exceeds this, checked from the header before
    a single pixel is decoded. A flat 6000 px JPEG compresses to almost nothing, so the byte cap alone does
    not bound the memory a request can cost."""
    if not isinstance(s, str) or not s: raise ValueError("no image supplied")
    if len(s) > MAX_B64_CHARS: raise ValueError("image too large")
    if "," in s[:64] and s.strip().startswith("data:"): s = s.split(",", 1)[1]
    try:
        im = Image.open(io.BytesIO(base64.b64decode(s)))
    except (OSError, SyntaxError, Image.DecompressionBombError) as e:   # not an image: the caller's 400, not our 500
        raise ValueError("not a readable image") from e
    w, h = im.size
    if w * h > MAX_PIXELS: raise ValueError("image too large")
    if max_side and max(w, h) > max_side:
        raise ClientError(f"Each image may be at most {int(max_side)} pixels on its longer side.")
    try: im = ImageOps.exif_transpose(im)
    except Exception: pass
    try:
        return im.convert("RGB")
    except (OSError, SyntaxError) as e:     # a truncated file fails here, when the pixels are first decoded
        raise ValueError("not a readable image") from e

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

CHUNK_PX = 1 << 20           # pixels per row band in the full-frame loops (~12 MB per float32 RGB temporary)

def _row_chunks(n, width, px=CHUNK_PX):
    """(start, stop) row bands of about px pixels. Every per-pixel step is applied band by band with the very
    same numpy expression it had on the whole frame, so the result is identical and only the temporaries
    shrink: at 4096 px a whole-frame float64 RGB temporary is 400 MB, a band is 25 MB."""
    step = max(8, int(px // max(int(width), 1)))
    for r0 in range(0, int(n), step):
        yield r0, min(int(n), r0 + step)

def _radius_grid(S, R, rows=None):
    """Distance of every pixel from the centre of an S x S frame in units of R (float64). The same numbers
    np.mgrid produced, built from one 1-D axis, so no integer grids are allocated. rows=(start, stop) gives a band."""
    y0, y1 = (0, S) if rows is None else rows
    ax = (np.arange(S) - S / 2 + 0.5) ** 2
    return np.sqrt(ax[None, :] + ax[y0:y1, None]) / R

def disk_alpha(S, r, feather=0.035, rows=None):
    """Soft disk of radius r centred in an S x S frame; rows=(start, stop) returns only that band."""
    a = np.clip((1 - _radius_grid(S, r, rows)) / feather, 0, 1)
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

BOX_LANE_BYTES = 1 << 21     # float64 scratch per block of rows in _box1 along the rows (2 MB)
BOX_COLUMNS = 64             # columns per block in _box1 down the columns: keeps the block in cache

def _box1(a, r, ax):
    """Running mean of width 2r+1 along one axis of a 2-D plane, reflect-padded, via a float64 cumulative sum.

    Worked in blocks of lanes, so the float64 scratch is a couple of megabytes instead of two copies of the
    whole plane (at 4096 px the old version held ~0.5 GB and spent 0.5 s per call in np.take copies). Every
    lane is padded, summed and differenced in exactly the same order as before, so the result is bit-identical
    (checked on random planes, r = 0 .. n and 1-pixel planes included)."""
    n = a.shape[ax]
    r = int(min(r, max(n - 1, 1)))
    k = 2 * r + 1
    out = np.empty(a.shape, np.float32)
    if ax == 1:
        step = max(1, BOX_LANE_BYTES // (8 * (n + k)))
        buf = np.empty((min(step, a.shape[0]), n + k), np.float64)
        cs = np.empty_like(buf)
        for l0 in range(0, a.shape[0], step):
            l1 = min(a.shape[0], l0 + step)
            b, c, blk = buf[:l1 - l0], cs[:l1 - l0], a[l0:l1]
            b[:, 0] = 0.0
            b[:, 1:r + 1] = blk[:, :r][:, ::-1]
            b[:, r + 1:r + 1 + n] = blk
            b[:, r + 1 + n:] = blk[:, ::-1][:, :r]
            np.cumsum(b, axis=1, out=c)
            np.subtract(c[:, 2 * r + 1:2 * r + 1 + n], c[:, 0:n], out=b[:, :n])
            b[:, :n] /= k
            out[l0:l1] = b[:, :n]
    else:
        m = a.shape[1]
        buf = np.empty((n + k, min(BOX_COLUMNS, max(m, 1))), np.float64)
        cs = np.empty_like(buf)
        for c0 in range(0, m, BOX_COLUMNS):
            c1 = min(m, c0 + BOX_COLUMNS)
            b, c, blk = buf[:, :c1 - c0], cs[:, :c1 - c0], a[:, c0:c1]
            b[0] = 0.0
            b[1:r + 1] = blk[:r][::-1]
            b[r + 1:r + 1 + n] = blk
            b[r + 1 + n:] = blk[::-1][:r]
            np.cumsum(b, axis=0, out=c)
            np.subtract(c[2 * r + 1:2 * r + 1 + n], c[0:n], out=b[:n])
            b[:n] /= k
            out[:, c0:c1] = b[:n]
    return out


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

_W_LUM = np.array([0.299, 0.587, 0.114], dtype=np.float32)

def _lum3(a):
    """(a * W_LUM).sum(axis=2, keepdims=True) for RGB pixels (float32, or uint8 taken as float32), without
    numpy's slow reduction over a length-3 axis. numpy sums that axis as (r + g) + b; so does this, with
    the same float32 products, so the result is bit-identical (the 1024 px regression renders prove it)."""
    ch = [a[..., i] if a.dtype == np.float32 else a[..., i].astype(np.float32) for i in range(3)]
    return ((ch[0] * _W_LUM[0] + ch[1] * _W_LUM[1]) + ch[2] * _W_LUM[2])[..., None]

def _soft_shoulders_inplace(arr, toe=18.0, shoulder=208.0, lo=2.0, hi=253.0):
    """soft_shoulders() written into arr itself. The two masks cannot overlap (a value above the shoulder
    stays above it), so each pixel gets exactly the number the copying version gives."""
    hiM = arr > shoulder
    if hiM.any():
        span = max(hi - shoulder, 1e-3)
        arr[hiM] = shoulder + span * (1.0 - np.exp(-(arr[hiM] - shoulder) / span))
    loM = arr < toe
    if loM.any():
        span = max(toe - lo, 1e-3)
        arr[loM] = toe - span * (1.0 - np.exp(-(toe - arr[loM]) / span))
    return arr

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
PUPIL_STATS_RR = 0.86       # the pupil measurements (pupil_radius, _pupil_params) read nothing beyond 0.84 of the iris radius


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
    band of radius instead of starting at a line.

    arr: S x S x 3 pixels (uint8 or float32), rr: _radius_grid() of the frame. Returns a float32 S x S map."""
    p = _pale_intruders(arr, rr)
    return np.zeros(arr.shape[:2], np.float32) if p is None else p


PALE_MAP_MAX = 1024           # the lid map is a heavily blurred field (2.5% of the frame): when the graded output is
                             # larger than this, a frame above this side has it measured on a box-averaged copy this
                             # size and scaled back up. At 4096 px that is 0.8 s instead of 5.5 s. A preview-sized
                             # output (<= this) always gets the exact map, whatever the input size: the reduced one
                             # moved a 1024 artwork from a 1025 px input by up to 11 levels.

def _resize_plane(p, n, resample):
    """A float32 plane resized to n x n in PIL mode F: BOX to average down, BILINEAR to scale back up."""
    return np.asarray(Image.fromarray(np.ascontiguousarray(p, dtype=np.float32)).resize((n, n), resample), dtype=np.float32)


def _pale_intruders(arr, rr=None, R=None, reduce=True):
    """pale_intruders() that returns None when no arc of the outer band reads as lid, which is the usual case.
    The map would then be all zeros and pushing zeros out changes nothing, so studio_grade skips the step.
    Statistics are taken on 1-D pixel lists instead of full-frame masks, and the full-frame part runs in row
    bands; every number is computed with the expression the whole-frame version used.
    rr: the frame's _radius_grid(), or R (iris radius in pixels) to let this build its own. Only with R and
    reduce does a frame larger than PALE_MAP_MAX get the reduced-size measurement."""
    S = arr.shape[0]
    lum = np.empty((S, S), np.float32)
    sat = np.empty((S, S), np.float32)
    exact_ints = arr.dtype == np.uint8
    for r0, r1 in _row_chunks(S, S):
        if exact_ints:
            # uint8 pixels: max, min and the channel sum are exact integers, so taking them per channel in
            # integer arithmetic gives the very floats arr.astype(float32).max/min/mean(axis=2) gave, without
            # numpy's slow reductions over a length-3 axis (1.1 s of the 4096 px grade)
            a8 = arr[r0:r1]
            r_, g_, b_ = a8[..., 0], a8[..., 1], a8[..., 2]
            mx = np.maximum(np.maximum(r_, g_), b_).astype(np.float32)
            mn = np.minimum(np.minimum(r_, g_), b_).astype(np.float32)
            lum[r0:r1] = (r_.astype(np.uint16) + g_ + b_).astype(np.float32) / 3
        else:
            a = np.asarray(arr[r0:r1], dtype=np.float32)
            mx, mn = a.max(axis=2), a.min(axis=2)
            lum[r0:r1] = a.mean(axis=2)
        sat[r0:r1] = (mx - mn) / np.maximum(mx, 1.0)
    full = S                         # the frame the map is returned at
    if R is not None and reduce and S > PALE_MAP_MAX:
        S = PALE_MAP_MAX             # from here on S is the side the map is measured at
        lum = _resize_plane(lum, S, Image.BOX)
        sat = _resize_plane(sat, S, Image.BOX)
    if rr is None or S != full:
        rr = _radius_grid(S, R * S / full)
    rad = max(1.0, S * 0.025)
    if S != full:
        # the box width the full frame would blur with, scaled down, to the nearest odd width: rounding 0.025 S
        # at the small size instead widened the blur 3%, and the lid test's medians moved enough to change the
        # map by up to 0.05 (11 levels on a white pixel, measured on a real 4K render); matched it is 0.017
        want = (2 * max(1, int(round(max(1.0, full * 0.025)))) + 1) * S / full
        rad = float(max(1, int(round((want - 1) / 2))))
    lum_b = _blur_f(lum, rad); del lum
    sat_b = _blur_f(sat, rad); del sat

    starts = np.arange(0.40, 1.00, 0.04)
    span = (rr >= starts[0]) & (rr < starts[-1] + 0.04)      # every pixel any of the bins below can hold
    r_1d, l_1d, s_1d = rr[span], lum_b[span], sat_b[span]
    del span
    centres, ml, ms = [], [], []
    for a in starts:
        sel = (r_1d >= a) & (r_1d < a + 0.04)
        if sel.sum() > 40:
            centres.append(a + 0.02); ml.append(float(np.median(l_1d[sel]))); ms.append(float(np.median(s_1d[sel])))
    del r_1d, l_1d, s_1d
    if len(centres) < 3:
        return None
    # A heavy lid can own a whole radius, so the reference may not climb above the iris because of it. The iris
    # reference is the BRIGHTEST inner radius: the innermost bins can still be pupil on a dilated eye, which is
    # exactly how the old test mistook a light outer ring for sclera. Outer radii of a real iris are no brighter
    # than its brightest inner one, since the limbal ring darkens towards the edge.
    inner = max(m for c, m in zip(centres, ml) if c < 0.80)
    ml = np.minimum(np.array(ml), inner * 1.10)

    # which arcs of the outer band read as lid: broad, bright, and no more colourful than the iris there
    by, bx = np.nonzero((rr > 0.82) & (rr < 0.94))
    rb = rr[by, bx]
    ratio_b = lum_b[by, bx] / np.maximum(np.interp(rb, centres, ml).astype(np.float32), 1.0)
    sratio_b = sat_b[by, bx] / np.maximum(np.interp(rb, centres, ms).astype(np.float32), 1e-3)
    ang_b = (np.degrees(np.arctan2(by - S / 2 + 0.5, bx - S / 2 + 0.5)) + 360.0) % 360.0
    del by, bx, rb, sat_b
    step = 360.0 / LID_SECTORS
    gate = np.zeros(LID_SECTORS, np.float32)
    for i in range(LID_SECTORS):
        sel = (ang_b >= i * step) & (ang_b < (i + 1) * step)
        if sel.sum() > 20:
            r_ = float(np.median(ratio_b[sel])); s_ = float(np.median(sratio_b[sel]))
            gate[i] = np.clip((r_ - LID_BRIGHT[0]) / (LID_BRIGHT[1] - LID_BRIGHT[0]), 0, 1) * np.clip((1.05 - s_) / 0.25, 0, 1)
    gate = np.maximum(gate, 0.5 * (np.roll(gate, 1) + np.roll(gate, -1)) * (gate > 0))   # close pinholes inside a lid
    if not gate.any():
        return None

    out = np.empty((S, S), np.float32)
    lo, hi = SCLERA_RAMP
    sect = np.arange(LID_SECTORS) * step + step / 2
    for r0, r1 in _row_chunks(S, S):
        rc = rr[r0:r1]
        ratio = lum_b[r0:r1] / np.maximum(np.interp(rc, centres, ml).astype(np.float32), 1.0)
        # the angle is taken on full contiguous planes, as before: a broadcast view could take a different
        # (scalar instead of vector) arctan2 loop on some CPUs
        dy = np.empty(rc.shape); dy[:] = (np.arange(r0, r1) - S / 2 + 0.5)[:, None]
        dx = np.empty(rc.shape); dx[:] = (np.arange(S) - S / 2 + 0.5)[None, :]
        ang = (np.degrees(np.arctan2(dy, dx)) + 360.0) % 360.0
        g = np.interp(ang, sect, gate, period=360.0)
        brighter = np.clip((ratio - 1.12) / 0.30, 0.0, 1.0)
        ramp = np.clip((rc - lo) / (hi - lo), 0.0, 1.0)
        out[r0:r1] = (brighter * g * ramp).astype(np.float32)
    if S != full:
        out = _resize_plane(out, full, Image.BILINEAR)
    return out


def pupil_radius(lum, rr):
    """Where the pupil ends, in units of the iris radius, read from the image: the first radius at which the
    median brightness climbs halfway from the centre to the iris. None if the centre is not dark.
    The 0.02 bins are consecutive edges of one arange, so each pixel belongs to exactly one bin: searchsorted
    finds it with the same >= / < comparisons the per-bin masks made, in one pass instead of 42."""
    edges = np.arange(0.0, 0.86, 0.02)
    within = rr < edges[-1]
    r_1d, l_1d = rr[within], lum[within]
    del within
    k = (np.searchsorted(edges, r_1d, side="right") - 1).astype(np.int16)
    counts = np.bincount(k, minlength=len(edges) - 1)
    l_sorted = l_1d[np.argsort(k, kind="stable")]
    meds = np.full(len(edges) - 1, np.nan)
    pos = 0
    for i, c in enumerate(counts[:len(edges) - 1]):
        if c > 12:
            meds[i] = float(np.median(l_sorted[pos:pos + c]))
        pos += int(c)
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
    pp = _pupil_params(tone, rr)
    return arr if pp is None else _pupil_apply(arr, rr, tone, pp)


def _pupil_params(tone, rr):
    """The whole-frame measurements neutral_pupil() needs: (rho, floor, iris_med), or None without a pupil.
    floor and iris_med are None when the core or ring is too small to measure (then nothing is flattened)."""
    rho = pupil_radius(tone, rr)
    if rho is None:
        return None
    floor = iris_med = None
    core = rr < 0.8 * rho
    ring = (rr > 0.60) & (rr < 0.84)
    if core.sum() > 20 and ring.any():
        floor = float(np.percentile(tone[core], 15))
        iris_med = float(np.median(tone[ring]))
    return rho, floor, iris_med


def _pupil_apply(arr, rr, tone, pp):
    """The per-pixel half of neutral_pupil(), for any block of pixels. Outside rr < 1.04 rho it returns arr
    unchanged (as float64), which is why studio_grade only runs it on the pupil's bounding box."""
    rho, floor, iris_med = pp
    lum = tone
    inside = np.clip((rho * 1.04 - rr) / max(rho * 0.10, 1e-3), 0.0, 1.0)      # soft edge at the pupil rim
    lo, hi = PUPIL_DARK
    dark = np.clip((hi - lum) / (hi - lo), 0.0, 1.0)
    w = inside * dark
    if floor is not None:
        rim = np.clip((rho - rr) / max(rho * 0.10, 1e-3), 0.0, 1.0)             # full inside 0.9 rho, none at the rim
        not_iris = np.clip((PUPIL_FLAT[1] * iris_med - lum) / ((PUPIL_FLAT[1] - PUPIL_FLAT[0]) * iris_med), 0.0, 1.0)
        flat = rim * not_iris
        lum = lum - flat * np.maximum(lum - floor, 0.0)
        w = np.maximum(w, flat)
    w = w[..., None]
    return arr * (1.0 - w) + lum[..., None] * w


def studio_ease(im, r_frac):
    """0..1: how much of the studio sculpting this iris gets. 0 at professional fibre detail, 1 on a soft crop."""
    have = fibre_detail(im, r_frac)
    return float(np.clip((9.0 - have) / 6.0, 0.0, 1.0))


def studio_grade(im, r_frac, out=1024, fill=None, local=None, micro=None, sat=None, sclera=None, trim=None):
    """Turn a masked iris square into the fine-art frame: limbus-tight, pure black outside, sculpted fibres.

    A phone crop carries a slice of sclera or eyelid at the bottom of the disk and sits small inside its frame.
    A studio print does neither: the iris is the whole picture. Everything here is arithmetic on the pixels the
    camera captured, so it deepens what is real instead of inventing what is not.

    Cost: only the square around the trimmed disk ever reaches the output, so steps 2-3 run on that window
    alone (two thirds of the frame); the blurs that feed them still see the whole frame. Every per-pixel step
    runs in row bands (_row_chunks) with the same expression it had on the whole frame, so the picture is
    bit-identical to the whole-frame version whenever out <= PALE_MAP_MAX (every preview), whatever the input
    size. Only a larger output from an input above PALE_MAP_MAX (the 4096 px renders) has its lid map measured
    on a reduced copy.
    At 4096 px: ~5 s and ~0.5 GB instead of ~25 s and 2.7 GB."""
    fill = STUDIO_FILL if fill is None else fill
    # the studio macro render already arrives razor sharp. Sharpening it again is what produced the
    # speckled dark pixels the owner spotted, so the sculpting is scaled down by how much fibre detail
    # the input already carries: none of it at professional levels, all of it on a soft crop.
    if local is None or micro is None:
        ease = studio_ease(im, r_frac)
        local = STUDIO_LOCAL * ease if local is None else local
        micro = STUDIO_MICRO * ease if micro is None else micro
    trim = STUDIO_TRIM if trim is None else trim
    sat = STUDIO_SAT if sat is None else sat
    sclera = STUDIO_SCLERA if sclera is None else sclera

    S = im.size[0]
    R = max(1.0, r_frac * S)
    src_im = im if im.mode == "RGB" else im.convert("RGB")
    src = np.asarray(src_im)                     # uint8; the float32 pixels are rebuilt band by band from it

    # The window: the square around the disk cut at trim x the limbus (step 4), widened if need be to the
    # radius the pupil statistics read (PUPIL_STATS_RR), clipped to the frame. It is the same range for rows and
    # columns; every pixel outside it is thrown away by step 4 and read by nothing. At the default trim it is
    # exactly the step-4 square.
    Rt = R * trim
    side = int(round(2 * Rt))
    x0 = y0 = int(round(S / 2 - Rt))
    w0 = max(0, min(x0, int(math.floor(S / 2 - PUPIL_STATS_RR * R))))
    w1 = min(S, max(x0 + side, int(math.ceil(S / 2 + PUPIL_STATS_RR * R))))
    n = w1 - w0
    ax = (np.arange(S) - S / 2 + 0.5) ** 2       # rr of any block is sqrt(ax[cols] + ax[rows]) / R, as _radius_grid

    # 1. push the pale intruders out of the outer rim: sclera and eyelid are brighter and far less saturated
    #    than iris, so they can be identified without touching the iris itself. No lid found = nothing to do.
    pale = _pale_intruders(src, R=R, reduce=out > PALE_MAP_MAX) if sclera > 0 else None

    def pixels(r0, r1, c0=w0, c1=w1):
        """The float32 pixels of rows r0..r1, columns c0..c1 after step 1 (absolute frame indices)."""
        a = src[r0:r1, c0:c1].astype(np.float32)
        if pale is not None:
            a = a * (1.0 - pale[r0:r1, c0:c1] * sclera)[..., None]
        return a

    # 2. sculpt: large-radius unsharp gives the fibres relief, small-radius separates them. This runs on
    #    luminance alone - applied per channel it would pull the channels apart and quietly saturate the
    #    whole iris, which is not enhancement, it is a colour cast. The blurs see the whole frame.
    if pale is None:
        base = src_im                             # step 1 changed nothing: the pixels are the input's own
    else:
        b8 = np.empty(src.shape, np.uint8)
        for r0, r1 in _row_chunks(S, S):
            b8[r0:r1] = np.clip(pixels(r0, r1, 0, S), 0, 255).astype(np.uint8)
        base = Image.fromarray(b8)
        del b8

    def lum_of(img):
        """Luminance of the window of a blurred frame."""
        a8 = np.asarray(img)
        p = np.empty((n, n, 1), np.float32)
        for r0, r1 in _row_chunks(n, n):
            p[r0:r1] = _lum3(a8[w0 + r0:w0 + r1, w0:w1])
        return p

    big = lum_of(base.filter(ImageFilter.GaussianBlur(max(2.0, S * 0.045))))
    sml = lum_of(base.filter(ImageFilter.GaussianBlur(max(1.0, S * 0.004))))
    del base
    lum_all = np.empty((n, n, 1), np.float32)     # luminance of the step-1 pixels of the window, used twice below
    sculpted = np.empty((n, n, 1), np.float32)
    for r0, r1 in _row_chunks(n, n):
        lum = _lum3(pixels(w0 + r0, w0 + r1)) if pale is not None else _lum3(src[w0 + r0:w0 + r1, w0:w1])
        lum_all[r0:r1] = lum
        sculpted[r0:r1] = soft_shoulders(lum + (lum - big[r0:r1]) * local + (lum - sml[r0:r1]) * micro)
    del big, sml

    # 3b (measured first, applied below). The pupil is a hole, not a surface: the colour a phone records there
    #     is sensor noise and a reflection of the room, and every professional print measured is neutral there.
    #     Found from the image itself and gated on darkness, so the pigmented ruff and any iris crypt keep their
    #     colour. Its tone is the luminance before the per-channel guard, which would otherwise lift a black hole
    #     to dark grey. It can only change pixels with rr < 1.04 rho, so it runs on that bounding box alone.
    #     Its statistics only read rr < 0.84, which lies inside the window, so the window gives the same numbers.
    tone = sculpted[..., 0]
    rr = np.sqrt(ax[None, w0:w1] + ax[w0:w1, None]) / R
    pp = _pupil_params(tone, rr)
    box = None
    if pp is not None:
        near = np.nonzero(np.abs(np.arange(w0, w1) - S / 2 + 0.5) <= pp[0] * 1.04 * R + 2.0)[0]
        if len(near):
            box = (int(near[0]), int(near[-1]) + 1)          # window indices

    graded = np.empty((n, n, 3), np.uint8)
    for r0, r1 in _row_chunks(n, n):
        a = pixels(w0 + r0, w0 + r1)
        lum = lum_all[r0:r1]
        sc = sculpted[r0:r1]
        # Midtones take the new luminance as a ratio, which keeps every pixel's colour proportions intact. Near
        # black that ratio stops meaning anything: the toe lifts a pupil of luminance 0.9 to 7.5, and a ratio of
        # 8 multiplies whatever faint tint the sensor left there into a navy disc. So dark pixels take the same
        # luminance change as a neutral offset instead, and the two blend smoothly across the shadows.
        #   a = t * (a * ratio) + (1 - t) * (a + (sc - lum)), evaluated in place with the same operand order
        ratio = sc / np.maximum(lum, 1.0)
        t = np.clip(lum / DARK_BLEND, 0.0, 1.0)
        mid = a * ratio
        mid *= t
        a += sc - lum
        a *= 1.0 - t
        a += mid
        del mid, ratio, t
        _soft_shoulders_inplace(a)   # per channel: keeps a saturated dark fibre off zero once saturation is added
        # 3. colour depth, on its own knob, so the number means what it says:  a = grey + (a - grey) * (1 + sat)
        grey = _lum3(a)
        a -= grey
        a *= 1.0 + sat
        a += grey
        if box is not None:
            b0, b1 = max(r0, box[0]), min(r1, box[1])
            if b0 < b1:
                c0, c1 = box
                blk = _pupil_apply(a[b0 - r0:b1 - r0, c0:c1], rr[b0:b1, c0:c1], tone[b0:b1, c0:c1], pp)
                a[b0 - r0:b1 - r0, c0:c1] = np.clip(blk, 0, 255).astype(np.uint8)
        np.clip(a, 0, 255, out=a)
        graded[r0:r1] = a.astype(np.uint8)
    del sculpted, lum_all, tone, pale, rr

    # 4. limbus-tight framing: scale the disk so it fills the requested share of the frame. The window is the
    #    trimmed square itself unless that square reaches past the frame (a large r_frac: that part stays
    #    black) or a small trim made the window wider than it.
    if (w0, w1) == (x0, x0 + side):
        tight = Image.fromarray(graded)
    else:
        a0, a1 = max(x0, w0), min(x0 + side, w1)      # rows = columns: the part of the square inside the window
        t = np.zeros((side, side, 3), np.uint8)
        if a0 < a1:
            t[a0 - y0:a1 - y0, a0 - x0:a1 - x0] = graded[a0 - w0:a1 - w0, a0 - w0:a1 - w0]
        tight = Image.fromarray(t)
        del t
    del graded
    target = max(8, int(round(out * fill)))
    t8 = np.asarray(tight.resize((target, target), Image.LANCZOS))
    del tight

    # 5. pure black outside the limbus, with only a hairline of softness so the circle stays crisp
    res = np.zeros((out, out, 3), np.uint8)
    off = (out - target) // 2
    for r0, r1 in _row_chunks(target, target):
        disk = t8[r0:r1].astype(np.float32) * disk_alpha(target, target / 2.0, 0.012, rows=(r0, r1))[..., None]
        res[off + r0:off + r1, off:off + target] = np.clip(disk.astype(np.float32), 0, 255).astype(np.uint8)
    return Image.fromarray(res)

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

ARTWORK_FOOTER = "SNAPEYES  ·  PRECISION IRIS ART"    # the small signature line under the names. The product
                                                        # is the digital file: nothing on it may speak of a print
CAPTION_MAX_W = 0.90         # no caption line is wider than this share of the artwork's width

def _fitted_font(d, text, name, size, weight, max_w):
    """The font at size, or smaller until text is at most max_w px wide. A line that already fits keeps its
    size exactly, so only a title or names line that would run off the artwork changes."""
    f = _font(name, size, weight)
    w = d.textlength(text, font=f) if text else 0.0
    while w > max_w and size > 6:
        size = max(6, min(size - 1, int(size * max_w / w)))
        f = _font(name, size, weight)
        w = d.textlength(text, font=f)
    return f

def _caption(out, st, title, names, cx, y_title, y_names, y_footer, u):
    """Title, names line and signature, centred on cx. u is the type scale (the side of a square artwork). The
    title and the names line are made smaller when they would be wider than CAPTION_MAX_W of the artwork (a
    40-character title is 1068 px at the 1024 px artwork's type size)."""
    d = ImageDraw.Draw(out)
    t = (title or st["title"]).upper()
    max_w = CAPTION_MAX_W * out.size[0]
    ft = _fitted_font(d, t, "Cinzel.ttf", int(u * 0.042), "Bold", max_w)
    fs = _font("PlusJakartaSans.ttf", int(u * 0.014), "Medium")
    d.text((cx, y_title), t, font=ft, fill=st["accent"], anchor="mm")
    if names:
        fn = _fitted_font(d, names, "PlusJakartaSans.ttf", int(u * 0.026), "Regular", max_w)
        d.text((cx, y_names), names, font=fn, fill=(240, 243, 250), anchor="mm")
    d.text((cx, y_footer), ARTWORK_FOOTER, font=fs, fill=(150, 155, 170), anchor="mm")

WATERMARK_ANGLE = -18

def _watermark_layer(W, H, u):
    """The rotated text tile for a W x H artwork. Defined as: draw the tile on a 2W x 2H layer, rotate it
    WATERMARK_ANGLE degrees about its centre (bicubic), crop the central W x H. Built here without the 2W x 2H
    layer: only the window the rotation can sample is drawn (rows of text start on their own grid, so the
    glyphs land on the same pixels), and it is mapped straight into W x H with the matrix PIL.rotate builds,
    shifted to the crop corner. Bit-identical to rotate+crop at 1024, 1024x683, 819x1024, 2048 and 4096 px
    (checked); at 4096 it is 1.6 s and ~110 MB instead of 6.3 s and ~540 MB."""
    ang = -math.radians(WATERMARK_ANGLE % 360.0)
    a, b = round(math.cos(ang), 15), round(math.sin(ang), 15)
    d, e = round(-math.sin(ang), 15), round(math.cos(ang), 15)
    c = a * (-W) + b * (-H) + W                  # rotation about the layer centre (W, H), as PIL.rotate does
    f = d * (-W) + e * (-H) + H
    c += a * (W // 2) + b * (H // 2)             # the output starts at the crop corner
    f += d * (W // 2) + e * (H // 2)
    corners = [(a * (x + 0.5) + b * (y + 0.5) + c, d * (x + 0.5) + e * (y + 0.5) + f) for x in (0, W) for y in (0, H)]
    sx1 = min(2 * W, int(math.ceil(max(p[0] for p in corners))) + 4)
    sy0 = max(0, int(math.floor(min(p[1] for p in corners))) - 4)
    sy1 = min(2 * H, int(math.ceil(max(p[1] for p in corners))) + 4)
    step_y, step_x = int(u * 0.3), int(u * 0.7)
    wy0 = (sy0 // step_y) * step_y               # start on a text row, so no row is cut off at the top
    layer = Image.new("RGBA", (max(1, sx1), max(1, sy1 - wy0)), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    fw = _font("PlusJakartaSans.ttf", int(u * 0.036), "Bold")
    for y in range(0, H * 2, step_y):
        if y + step_y < wy0 or y > sy1:
            continue
        for x in range(0, W * 2, step_x):
            ld.text((x + (y // step_y % 2) * u * 0.35, y - wy0), "SNAPEYES.COM  ·  PREVIEW", font=fw, fill=(255, 255, 255, 40))
    return layer.transform((W, H), Image.AFFINE, (a, b, c, d, e, f - wy0), resample=Image.BICUBIC)

WATERMARK_BADGE = "WATERMARKED PREVIEW  ·  UNLOCK FULL SIZE"

def _watermark(out, accent, u, tile_u=None):
    """The preview watermark: a faint rotated tile of SNAPEYES.COM PREVIEW over the whole artwork and a badge
    at the top centre. u is the badge scale; for the square single-eye artwork it is the side. tile_u is the
    tile's scale, u when not given. The badge's pill is cut to its measured text plus a margin, so the words
    stay inside it on every canvas (a fixed 0.28 u pill left 40 px of text outside each end at 1024)."""
    W, H = out.size
    layer = _watermark_layer(W, H, tile_u or u)
    out = Image.alpha_composite(out.convert("RGBA"), layer).convert("RGB")
    del layer
    d = ImageDraw.Draw(out); fp = _font("PlusJakartaSans.ttf", int(u * 0.016), "Bold")
    half = min(W / 2.0 - 2.0, d.textlength(WATERMARK_BADGE, font=fp) / 2.0 + u * 0.022)
    d.rounded_rectangle((W / 2.0 - half, u * 0.03, W / 2.0 + half, u * 0.07), radius=int(u * 0.02), fill=(0, 0, 0, 200), outline=accent)
    d.text((W / 2, u * 0.05), WATERMARK_BADGE, font=fp, fill=accent, anchor="mm")
    return out

BG_4K_FROM = 1024            # a canvas whose longest side is above this takes its background from bg/4k/

def _style_bg(st, W, H):
    """The style background filling W x H: scaled to cover, centre-cropped. A square is the plain resize.
    Up to BG_4K_FROM px it is the 1024 px file (so every preview is what it always was); above it, the 4096 px
    copy in bg/4k/ when there is one, reduced to the canvas instead of the 1024 px file blown up 4x, which
    smeared every star into a blob next to the crisp iris fibres. Those copies were made once, offline, from the
    1024 px files: Real-ESRGAN x4 luminance with the colour of the LANCZOS 4x, channel means matched to the
    1024 px file. Studio Black is pure black and has none: at any size it is the same black."""
    s = max(W, H)
    path = os.path.join(ASSETS, "bg", st["bg"])
    if s > BG_4K_FROM and os.path.exists(os.path.join(ASSETS, "bg", "4k", st["bg"])):
        path = os.path.join(ASSETS, "bg", "4k", st["bg"])
    bg = Image.open(path).convert("RGB")
    bg = bg.resize((s, s), Image.LANCZOS)
    if (W, H) != (s, s):
        bg = bg.crop(((s - W) // 2, (s - H) // 2, (s - W) // 2 + W, (s - H) // 2 + H))
    return np.asarray(bg)

def _rim_light(arr, acc, jy, jx, Sd, rr):
    """A thin accent highlight on the limbus, strongest towards the upper left, so the iris sits inside the
    scene instead of being pasted on top of it. jy, jx: pixel indices of the block inside its Sd frame."""
    dy = np.empty(rr.shape); dy[:] = jy - Sd / 2      # full contiguous planes, like the old mgrid ones
    dx = np.empty(rr.shape); dx[:] = jx - Sd / 2
    ang = np.arctan2(dy, dx)
    rim = np.exp(-((rr - 0.985) / 0.045) ** 2) * (0.55 + 0.45 * np.cos(ang + 2.4))
    return np.clip(arr + acc * rim[..., None] * POLISH_RIM, 0, 255)

def _alpha_from_rr(rr, feather):
    """disk_alpha() from an already computed radius grid (rr in units of the disk radius)."""
    a = np.clip((1 - rr) / feather, 0, 1)
    return 0.5 - 0.5 * np.cos(a * math.pi)

def _paste_disk(canvas, r0, r1, g8, Sd, Rg, x0, y0, feather, acc):
    """Composite the graded disk (an Sd x Sd frame placed at x0, y0) into canvas rows r0..r1 in place:
    region * (1 - alpha) + arr * alpha, after the accent rim light when acc is given (non-bare styles)."""
    d0, d1 = max(r0, y0), min(r1, y0 + Sd)
    if d0 >= d1:
        return
    jr = (d0 - y0, d1 - y0)
    arr = g8[jr[0]:jr[1]].astype(np.float32)
    rr = _radius_grid(Sd, Rg, jr)
    if acc is not None:
        arr = _rim_light(arr, acc, np.arange(jr[0], jr[1])[:, None], np.arange(Sd)[None, :], Sd, rr)
    alpha = _alpha_from_rr(rr, feather)[..., None]
    region = canvas[d0 - r0:d1 - r0, x0:x0 + Sd]
    mixed = region * (1 - alpha)
    mixed += arr * alpha
    canvas[d0 - r0:d1 - r0, x0:x0 + Sd] = mixed

def compose(iris, style="celestial_gold", title=None, names="", watermark=True, r_frac=None, size=1024, keep=None):
    """The single-eye artwork: a size x size square. The canvas is rendered in row bands with the same
    per-pixel expressions as the whole-canvas version, so the banding itself changes no pixel at any size; the
    float64 canvas and its glow planes (~2 GB at 4096 px) are never held whole. studio_grade is exact for every
    preview-sized disc (see PALE_MAP_MAX). Above BG_4K_FROM px the background comes from the 4096 px file
    (_style_bg)."""
    st = STYLES.get(style, STYLES["celestial_gold"])
    bg8 = _style_bg(st, size, size)
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
    g8 = np.asarray(graded)
    Rg = max(1.0, Sd * STUDIO_FILL / 2.0)
    cx, cy = size // 2, int(size * (0.5 if bare else 0.44))
    x0, y0 = cx - Sd // 2, cy - Sd // 2
    x0, y0 = max(0, min(x0, size - Sd)), max(0, min(y0, size - Sd))
    feather = 0.015 if bare else 0.05
    out8 = np.empty((size, size, 3), np.uint8)
    for r0, r1 in _row_chunks(size, size):
        canvas = bg8[r0:r1].astype(np.float32)
        if not bare:
            # soft accent glow behind the iris:  canvas * (1 - g * 0.55) + acc * g * 0.55, same operand order
            dist = np.sqrt((np.arange(size)[None, :] - cx) ** 2 + (np.arange(r0, r1)[:, None] - cy) ** 2) / Rg
            g = (np.clip(1.6 - dist, 0, 1) ** 2 * 0.45)[..., None]
            lit = acc * g
            lit *= 0.55
            canvas = canvas * (1 - g * 0.55)
            canvas += lit
            del dist, g, lit
        _paste_disk(canvas, r0, r1, g8, Sd, Rg, x0, y0, feather, None if bare else acc)
        np.clip(canvas, 0, 255, out=canvas)
        out8[r0:r1] = canvas.astype(np.uint8)
    del bg8
    out = Image.fromarray(out8)
    del out8
    if not bare:
        _caption(out, st, title, names, size / 2, size * 0.86, size * 0.905, size * 0.945, size)
    if watermark:
        out = _watermark(out, st["accent"], size)
    return out

# ----------------------------------------------------------------------------- several eyes on one artwork
MULTI_MAX = 8                # eyes on one artwork
LAYOUTS = {1: ("single",), 2: ("duo", "fusion"), 3: ("triangle", "row"), 4: ("grid", "row"),
           5: ("galaxy",), 6: ("galaxy",), 7: ("galaxy",), 8: ("galaxy",)}   # the first one is the default
FORMATS = ("artwork", "wallpaper")   # the canvas: the artwork's own shape (multi_canvas), or a phone screen
MULTI_GAP = 0.06             # space between two neighbouring discs, as a share of the disc diameter
FUSION_OVERLAP = 0.18        # "fusion": the two discs share this much of their diameter
MULTI_SIDE = 0.05            # canvas margins, as a share of the shorter canvas side u
MULTI_TOP = 0.085            # clear of the preview badge (0.03-0.07 of the type scale)
MULTI_CAPTION = 0.185        # the caption band compose() uses: title at 0.14 type scale above the bottom edge
TYPE_WIDE = 0.66             # the type scale is never below this share of the longest side: scaled to the short
                             # side alone, a 21:9 row set its names line at 11 px and its footer at 6 px in a
                             # 1024 px preview. It changes only the rows and the wallpaper (u is larger elsewhere)
WM_DISC = 1.33               # the preview tile is scaled to at most this x the disc diameter: the single-eye
                             # artwork's own ratio (1024 px side, 770 px disc), so each of eight small discs
                             # carries as many rows of the tile as one big eye does, not a gap between two rows
WALL_ASPECT = 9.0 / 19.5     # "wallpaper": a portrait phone screen, width / height
WALL_TOP = 0.20              # wallpaper: the top fifth is left to the lock-screen clock
WALL_FOOT = 0.06             # wallpaper: kept clear under the caption for the home bar and the lock-screen buttons
WALL_FOOT_BARE = 0.12        # wallpaper without text (Studio Black): the same buttons

def layouts_for(n):
    """The layouts n eyes can take, default first."""
    return LAYOUTS.get(int(n), ())

def multi_format(fmt=None):
    """The canvas format: "artwork" when fmt is None, else fmt if it is one of FORMATS."""
    if fmt is None:
        return FORMATS[0]
    if fmt not in FORMATS:
        raise ValueError(f"the format is one of {', '.join(FORMATS)}, not {fmt!r}")
    return fmt

def multi_layout(n, layout=None):
    """The layout n eyes will use: the default for n when layout is None, else layout if n can take it."""
    options = layouts_for(n)
    if not options:
        raise ValueError(f"an artwork holds 1 to {MULTI_MAX} eyes, not {n}")
    if layout is None:
        return options[0]
    if layout not in options:
        raise ValueError(f"{n} eyes can use {', '.join(options)}, not {layout!r}")
    return layout

def multi_canvas(n, layout=None, size=1024, fmt=None):
    """(W, H) of the artwork for n eyes: longest side = size. As an "artwork", side-by-side layouts are
    landscape (the pairs 3:2, rows 2:1 and 21:9) and stacked ones 4:5 portrait. These shapes are made to be
    looked at whole: a phone screen (9:19.5) cut from the middle of them loses eyes, since a pair is wider than
    the screen. The "wallpaper" format is that phone screen itself, WALL_ASPECT portrait for every layout, with
    the eyes laid out for it (see _arrangement) and the lock-screen clock and buttons left clear."""
    layout = multi_layout(n, layout)
    if multi_format(fmt) == "wallpaper":
        return max(8, int(round(size * WALL_ASPECT))), size
    if layout == "single": a, b = 1, 1
    elif layout in ("duo", "fusion"): a, b = 3, 2
    elif layout == "row": a, b = (2, 1) if n == 3 else (21, 9)
    else: a, b = 4, 5                                       # triangle, grid, galaxy
    return (size, max(8, int(round(size * b / a)))) if a >= b else (max(8, int(round(size * a / b))), size)

def _fit(pts, bw, bh):
    """Scale (disc diameter in px) at which unit discs centred on pts fill a bw x bh box, and their bbox centre."""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    w, h = max(xs) - min(xs) + 1.0, max(ys) - min(ys) + 1.0
    return min(bw / w, bh / h), ((max(xs) + min(xs)) / 2.0, (max(ys) + min(ys)) / 2.0)

def _ring(k, radius, start):
    """k unit-disc centres on a circle, clockwise from start degrees (-90 = the top)."""
    return [(radius * math.cos(math.radians(start + 360.0 * i / k)), radius * math.sin(math.radians(start + 360.0 * i / k)))
            for i in range(k)]

def _honeycombs(n):
    """Row counts of the symmetric honeycomb clusters of n discs: at least two rows, next rows differing by one
    disc (so each row sits in the gaps of the last), the same read from either end, at most 4 in a row.
    5 -> (2,1,2); 7 -> (1,2,1,2,1), (2,3,2); 8 -> (2,1,2,1,2), (3,2,3); 6 has none."""
    found = []
    def grow(rows, left):
        if left == 0:
            if len(rows) >= 2 and rows == rows[::-1]:
                found.append(tuple(rows))
            return
        for c in ((rows[-1] - 1, rows[-1] + 1) if rows else range(1, 5)):
            if 1 <= c <= min(4, left):
                grow(rows + [c], left - c)
    grow([], n)
    return found

def _cluster(n, bw, bh):
    """The "galaxy" for n (5-8) eyes: of the balanced clusters below, the one whose discs come out largest in a
    bw x bh box; on a tie, the earlier one. In order: one eye in the middle and the rest on a ring as tight as
    their neighbours allow (each ring turned two ways); a ring of all n; the symmetric honeycombs, as rows and
    as columns; the full grids. In the 4:5 artwork that is the ring-and-centre for 5 and 7, a ring of six for 6
    (a centre and five around it gave smaller eyes than seven do) and a honeycomb of three columns (3-2-3) for 8,
    so 6, 7 and 8 eyes all get the same disc size (1029 px at 4096); in the narrow wallpaper it is a 2-1-2
    honeycomb for 5, grids of two columns for 6 and 8 and the ring-and-centre for 7. Eye order: the middle
    first, then clockwise from the top; rows or columns in reading order."""
    p = 1.0 + MULTI_GAP
    cands = []
    k = n - 1
    if k >= 2:
        dc = max(p, p / (2.0 * math.sin(math.pi / k)))
        cands += [[(0.0, 0.0)] + _ring(k, dc, start) for start in (-90.0, -90.0 + 180.0 / k)]
    rn = p / (2.0 * math.sin(math.pi / n))
    cands += [_ring(n, rn, start) for start in (-90.0, -90.0 + 180.0 / n)]
    h = p * math.sqrt(3.0) / 2.0
    for rows in _honeycombs(n):
        pts = [((j - (c - 1) / 2.0) * p, i * h) for i, c in enumerate(rows) for j in range(c)]
        cands += [pts, [(y, x) for x, y in pts]]
    for c in range(2, n):
        if n % c == 0 and n // c >= 2:
            cands.append([((j - (c - 1) / 2.0) * p, i * p) for i in range(n // c) for j in range(c)])
    best = None
    for pts in cands:
        s = _fit(pts, bw, bh)[0]
        if best is None or s > best[0] * (1.0 + 1e-9):
            best = (s, pts)
    return best[1]

def _arrangement(n, layout, bw, bh, wallpaper=False):
    """Disc centres for unit-diameter discs, in eye order. Rows run left to right; the triangle puts the first
    eye on top; the grid is row by row; the galaxy is _cluster(). On a wallpaper the pair, the fusion and the
    row stand upright (top to bottom), so they fit a phone screen; the triangle, the grid and the galaxy
    already do (the galaxy picks its cluster for the narrow box)."""
    p = 1.0 + MULTI_GAP
    if layout == "single":
        pts = [(0.0, 0.0)]
    elif layout == "duo":
        pts = [(-p / 2, 0.0), (p / 2, 0.0)]
    elif layout == "fusion":
        q = 1.0 - FUSION_OVERLAP
        pts = [(-q / 2, 0.0), (q / 2, 0.0)]
    elif layout == "row":
        pts = [((i - (n - 1) / 2.0) * p, 0.0) for i in range(n)]
    elif layout == "triangle":
        h = p * math.sqrt(3.0) / 2.0
        pts = [(0.0, 0.0), (-p / 2, h), (p / 2, h)]
    elif layout == "grid":
        pts = [(-p / 2, -p / 2), (p / 2, -p / 2), (-p / 2, p / 2), (p / 2, p / 2)]
    else:
        return _cluster(n, bw, bh)
    if wallpaper and layout in ("duo", "fusion", "row"):
        pts = [(y, x) for x, y in pts]
    return pts

class _Disc:
    """One graded eye on the canvas: its Sd x Sd graded frame g8 placed at (x0, y0), visible radius Rg."""
    __slots__ = ("g8", "Sd", "Rg", "x0", "y0", "cx", "cy")
    def __init__(self, g8, x0, y0):
        self.g8, self.Sd = g8, g8.shape[0]
        self.Rg = max(1.0, self.Sd * STUDIO_FILL / 2.0)
        self.x0, self.y0 = x0, y0
        self.cx, self.cy = x0 + self.Sd / 2.0, y0 + self.Sd / 2.0

def _grade_disc(iris, r_frac, Sd):
    """studio_grade() for one disc drawn in an Sd x Sd frame. The sculpting strength is read from the iris as
    it came in (a shrunken copy reads softer and would be sharpened harder than the same eye alone), then the
    iris is brought down to 1.5x the pixels its disc can show before grading: the grade is scale-free, and
    five 4096 px irises then cost what five disc-sized ones do."""
    iris = iris if iris.mode == "RGB" else iris.convert("RGB")
    ease = studio_ease(iris, r_frac)
    target = max(8, int(round(Sd * STUDIO_FILL)))
    need = int(math.ceil(1.5 * target / (2.0 * r_frac * STUDIO_TRIM)))
    src = iris if iris.size[0] <= need else iris.resize((need, need), Image.LANCZOS)
    return studio_grade(src, r_frac, out=Sd, local=STUDIO_LOCAL * ease, micro=STUDIO_MICRO * ease)

def _smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)

def _discs_band(canvas, r0, r1, discs, feather, acc, fusion):
    """Composite every disc that reaches canvas rows r0..r1 into that band, in place. Each disc is compose()'s
    disc: its graded frame, compose()'s rim light when acc is given, and its feathered alpha. Discs that touch
    share the few feathered pixels between them by weight. For "fusion" the two discs are cross-faded where they
    overlap, so the fibres of both eyes meet in the middle instead of one disc lying on top of the other. With
    d0, d1 how deep a pixel lies inside each disc (0 outside it), eye 0 gets smoothstep(d0 / (d0 + d1)) and eye
    1 the rest: the whole of the other eye on either disc's edge, half and half along the middle line of the
    lens, and in between a fade across the lens as wide as it is at that height. The fade follows the lens
    shape in any direction (the upright wallpaper fusion too). A left-to-right fade put 30-50% of the other eye
    right on the rim near the lens tips: a 38-level step between two neighbouring pixels on flat test discs.
    Near the tips the lens is only a few pixels wide, so a steep fade there is the geometry, not a seam."""
    W = canvas.shape[1]
    hit = [d for d in discs if d.y0 < r1 and d.y0 + d.Sd > r0]
    if not hit:
        return
    h = r1 - r0
    num = np.zeros((h, W, 3), np.float32)
    den = np.zeros((h, W), np.float32)
    shows = np.ones((h, W), np.float32)           # product of (1 - alpha): how much of the background shows
    ca, sa = math.cos(2.4), math.sin(2.4)
    for d in hit:
        ya, yb = max(r0, d.y0), min(r1, d.y0 + d.Sd)
        xa, xb = max(0, d.x0), min(W, d.x0 + d.Sd)
        if xa >= xb:
            continue
        dy = (np.arange(ya - d.y0, yb - d.y0, dtype=np.float32) + np.float32(0.5 - d.Sd / 2.0))[:, None]
        dx = (np.arange(xa - d.x0, xb - d.x0, dtype=np.float32) + np.float32(0.5 - d.Sd / 2.0))[None, :]
        r = np.sqrt(dx * dx + dy * dy)
        rr = r / np.float32(d.Rg)
        a = _alpha_from_rr(rr, feather).astype(np.float32)
        c = d.g8[ya - d.y0:yb - d.y0, xa - d.x0:xb - d.x0].astype(np.float32)
        if acc is not None:
            # compose()'s accent rim on the limbus, strongest towards the upper left; cos(angle + 2.4) is taken
            # from dx, dy directly instead of through arctan2
            cosang = (dx * np.float32(ca) - dy * np.float32(sa)) / np.maximum(r, np.float32(1e-3))
            rim = np.exp(-((rr - np.float32(0.985)) / np.float32(0.045)) ** 2) * (np.float32(0.55) + np.float32(0.45) * cosang)
            c += acc * (rim * np.float32(POLISH_RIM))[..., None]
            np.clip(c, 0, 255, out=c)
        w = a
        if fusion:
            o = discs[1] if d is discs[0] else discs[0]
            ox = (np.arange(xa, xb, dtype=np.float32) + np.float32(0.5 - (o.x0 + o.Sd / 2.0)))[None, :]
            oy = (np.arange(ya, yb, dtype=np.float32) + np.float32(0.5 - (o.y0 + o.Sd / 2.0)))[:, None]
            deep = np.maximum(np.float32(d.Rg) - r, np.float32(0.0))
            other = np.maximum(np.float32(o.Rg) - np.sqrt(ox * ox + oy * oy), np.float32(0.0))
            w = _smoothstep(deep / np.maximum(deep + other, np.float32(1e-6))).astype(np.float32)
            del ox, oy, deep, other
        sl = (slice(ya - r0, yb - r0), slice(xa, xb))
        num[sl] += w[..., None] * c
        den[sl] += w
        shows[sl] *= 1.0 - a
    # the weights only say how the discs share a pixel, the alphas how much of it they cover. Where no disc has
    # weight, every alpha is 0 too (both vanish on a disc's edge), so the cover is 0 there and the tiny floor
    # only keeps the division finite.
    cover = (1.0 - shows)[..., None]
    col = num / np.maximum(den, np.float32(1e-30))[..., None]
    canvas *= 1.0 - cover
    canvas += col * cover

def _glow_band(canvas, r0, r1, discs, acc):
    """compose()'s soft accent glow behind each disc, clip(1.6 - d/Rg, 0, 1)^2 * 0.45, joined as 1 - prod(1 - g)
    so two glows that meet add up smoothly instead of creasing. In place."""
    W = canvas.shape[1]
    keep = None
    for d in discs:
        reach = 1.6 * d.Rg
        ya, yb = max(r0, int(d.cy - reach) - 1), min(r1, int(d.cy + reach) + 2)
        xa, xb = max(0, int(d.cx - reach) - 1), min(W, int(d.cx + reach) + 2)
        if ya >= yb or xa >= xb:
            continue
        dy = (np.arange(ya, yb, dtype=np.float32) + np.float32(0.5 - d.cy))[:, None]
        dx = (np.arange(xa, xb, dtype=np.float32) + np.float32(0.5 - d.cx))[None, :]
        g = np.clip(np.float32(1.6) - np.sqrt(dx * dx + dy * dy) / np.float32(d.Rg), 0, 1) ** 2 * np.float32(0.45)
        if keep is None:
            keep = np.ones((r1 - r0, W), np.float32)
        keep[ya - r0:yb - r0, xa:xb] *= 1.0 - g
    if keep is None:
        return
    g = (1.0 - keep)[..., None] * np.float32(0.55)
    canvas *= 1.0 - g
    canvas += acc * g

def compose_multi(irises, style="celestial_gold", names="", title=None, watermark=True, r_frac=None, size=1024,
                  layout=None, fmt=None, keep=None):
    """The artwork for 1-8 eyes. irises: masked iris squares, the input compose() takes, in the order they go on
    the canvas. One eye as an "artwork" is exactly compose(). More eyes: each is graded on its own
    (studio_grade) and placed by layout (see LAYOUTS, _arrangement): "duo" two discs side by side, "fusion" two
    discs overlapping by FUSION_OVERLAP and cross-faded where they meet, "triangle" or "row" for three, "grid"
    (2 x 2) or "row" for four, "galaxy" for five to eight (_cluster). fmt: "artwork" (default) or "wallpaper", a
    9:19.5 phone screen (see multi_canvas). The canvas is multi_canvas(): its longest side is size. Styles, glow,
    rim light, title, names line and watermark are compose()'s own; the type is scaled to the shorter canvas
    side but never below TYPE_WIDE of the longest one, the watermark tile to the discs (WM_DISC); Studio Black
    stays bare (no text). Deterministic. keep: gets "graded", the list of graded discs, for the colour QA."""
    irises = list(irises or [])
    n = len(irises)
    layout = multi_layout(n, layout)
    wall = multi_format(fmt) == "wallpaper"
    if n == 1 and not wall:
        return compose(irises[0], style=style, title=title, names=names, watermark=watermark, r_frac=r_frac,
                       size=size, keep=keep)
    st = STYLES.get(style, STYLES["celestial_gold"])
    bare = style == "studio_black"
    r_frac = r_frac or iris_radius_frac()
    W, H = multi_canvas(n, layout, size, fmt)
    u = min(W, H)
    ut = max(float(u), TYPE_WIDE * max(W, H))             # the type scale: caption and badge
    lift = WALL_FOOT * H if wall and not bare else 0.0    # the caption band sits this far above the bottom edge
    if bare:
        top, bottom = (WALL_TOP * H, WALL_FOOT_BARE * H) if wall else (MULTI_SIDE * u, MULTI_SIDE * u)
    else:
        top, bottom = (WALL_TOP * H if wall else MULTI_TOP * ut), MULTI_CAPTION * ut + lift
    bx0, bx1, by0, by1 = MULTI_SIDE * u, W - MULTI_SIDE * u, top, H - bottom
    pts = _arrangement(n, layout, bx1 - bx0, by1 - by0, wall)
    dia, (mx, my) = _fit(pts, bx1 - bx0, by1 - by0)
    Sd = max(8, int(round(dia / STUDIO_FILL)))            # the graded frame whose visible disc is dia across
    discs = []
    for im, (px, py) in zip(irises, pts):
        cx, cy = (bx0 + bx1) / 2.0 + (px - mx) * dia, (by0 + by1) / 2.0 + (py - my) * dia
        g = _grade_disc(im, r_frac, Sd)
        discs.append(_Disc(np.asarray(g), int(round(cx - Sd / 2.0)), int(round(cy - Sd / 2.0))))
        if keep is not None:
            keep.setdefault("graded", []).append(g)
        del g
    acc = np.array(st["accent"], dtype=np.float32)
    feather = 0.015 if bare else 0.05
    bg8 = _style_bg(st, W, H)
    out8 = np.empty((H, W, 3), np.uint8)
    for r0, r1 in _row_chunks(H, W):
        canvas = bg8[r0:r1].astype(np.float32)
        if not bare:
            _glow_band(canvas, r0, r1, discs, acc)
        _discs_band(canvas, r0, r1, discs, feather, None if bare else acc, layout == "fusion")
        np.clip(canvas, 0, 255, out=canvas)
        out8[r0:r1] = canvas.astype(np.uint8)
    del bg8, discs
    out = Image.fromarray(out8)
    del out8
    if not bare:
        _caption(out, st, title, names, W / 2.0, H - lift - 0.14 * ut, H - lift - 0.095 * ut, H - lift - 0.055 * ut, ut)
    if watermark:
        out = _watermark(out, st["accent"], ut, tile_u=min(float(u), WM_DISC * dia))
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
