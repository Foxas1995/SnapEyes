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

class ModelBusy(RuntimeError):
    """The Gemini model answered 429/503 (overloaded) on every attempt. run() answers 503 with a try-again line."""

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
    except ModelBusy as e:
        print("snapeyes model busy:", _scrub(repr(e))[:300], flush=True)
        send_json(req, 503, {"ok": False, "error": "Our studio is very busy right now. Please try again in a minute.",
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
        # only retry when the sleep plus a real second attempt still fit in the budget; each retry waits longer,
        # because a model under load answers 503 for a few seconds at a time
        if r.status_code in (429, 500, 503) and left > 0 and time_left(99) > 12:
            time.sleep(4 * (retries - left + 1)); left -= 1; continue
        break
    # the model itself was overloaded: the customer is told to try again in a minute, not that we broke
    if r.status_code in (429, 503): raise ModelBusy(last)
    raise RuntimeError(last)

def gemini_json(model, prompt, im):
    # the vision call is small and fast, so it can afford a second retry (4 s, then 8 s): on 2026-09-24 one
    # analyze answered 500 after a single retry because gemini-3.8-flash said "high demand" twice in a row
    j = gemini(model, [{"text": prompt}, {"inlineData": {"mimeType": "image/jpeg", "data": pil_to_b64(im, "JPEG", 90)}}],
               {"responseMimeType": "application/json", "temperature": 0}, retries=2)
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

LOCK_PUPIL_GAP = 8.0         # ring median minus the pupil core's darker quarter, grey levels
LOCK_SIDE_STEP = 40.0        # sclera band minus iris band, on the brighter of the two side sectors (medians)
LOCK_SIDES = ((-40, 40), (140, 220))   # the side sectors, degrees: eyelids never sit there

def _sector_median(gray, d, ang, r, a0, a1, lo, hi):
    sec = ((ang >= a0 + 360) | (ang < a1)) if a0 < 0 else ((ang >= a0) & (ang < a1))
    m = sec & (d >= lo * r) & (d < hi * r)
    return float(np.median(gray[m])) if m.sum() > 15 else None

def iris_lock_score(gray, cx, cy, r):
    """(locked, side step). Is this circle really centred on an iris?

    Two things only an iris circle has. A dark pupil in the middle: the ring's median against the darker quarter
    of the core, so a catchlight in the pupil cannot lift the core (the old mean read a near-black iris's pupil
    as 24.8 against a ring of 26.2 and refused a perfect circle) and a reflection over half the pupil cannot
    either. And a limbus: just outside the circle, on the left or the right side (lids never sit there), the
    sclera is clearly brighter than the iris just inside. A lash line or a lid crease also has a dark core, and
    the old whole-annulus sclera rule let it through (a circle on the owner's upper lid crease passed); what it
    lacks is that side step. Measured offline on 34 real iris circles, 9 real eyelid/skin circles and 398
    circles moved 1.5-2 radii off the iris (scratchpad wave-c/diag/lock_final.py): old 33/34, 1/9, 83/398;
    this 34/34, 0/9, 12/398. Real iris side steps 54-188, real wrong circles at most 15."""
    H, W = gray.shape
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    core = d < r * 0.30                      # the pupil lives here
    ring = (d > r * 0.55) & (d < r * 0.90)   # the coloured iris
    if core.sum() < 20 or ring.sum() < 40: return False, 0.0
    if float(np.median(gray[ring])) - float(np.percentile(gray[core], 25)) < LOCK_PUPIL_GAP:
        return False, 0.0                    # no dark pupil in the middle
    ang = (np.degrees(np.arctan2(yy - cy, xx - cx)) + 360.0) % 360.0
    steps = []
    for a0, a1 in LOCK_SIDES:
        o = _sector_median(gray, d, ang, r, a0, a1, 1.06, 1.30)
        i = _sector_median(gray, d, ang, r, a0, a1, 0.70, 0.94)
        if o is not None and i is not None: steps.append(o - i)
    step = max(steps) if steps else 0.0
    return step >= LOCK_SIDE_STEP, step

def iris_lock_ok(gray, cx, cy, r):
    return iris_lock_score(gray, cx, cy, r)[0]

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
DONOR_SOFT = 0.03            # eyelid fill only (mirror_prefill with extra donors): donor fade-out ramp, share of the side

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


def _rotation_donors(crop, m_img, ones, degrees):
    """(summed donor pixels x weight, summed weight) over rotations of the crop about its centre. A donor pixel's
    weight is 0 where the rotated mask covers it (it is glare or lid itself) or where the frame corner swung in."""
    cands, weights = [], []
    for deg in degrees:
        rot = np.asarray(crop.rotate(deg, resample=Image.BICUBIC)).astype(np.float32)
        rot_m = np.asarray(m_img.rotate(deg, resample=Image.BICUBIC)).astype(np.float32) / 255.0
        # rotation swings the frame corners in; those pixels are not iris and must not donate
        inside = np.asarray(ones.rotate(deg, resample=Image.BICUBIC)).astype(np.float32) / 255.0
        cands.append(rot)
        weights.append(np.clip(inside, 0, 1) * (1.0 - np.clip(rot_m, 0, 1)))
    C = np.stack(cands, 0)
    W = np.stack(weights, 0)[..., None]
    return (C * W).sum(0), W.sum(0)


def _ring_tone(arr, w, S):
    """Per radius (bins of 1% of the side, from the frame centre): the mean colour of the pixels with weight w that
    are not the black outside the disk, drawn back as an S x S x 3 image. Empty bins take their neighbours'."""
    ax = (np.arange(S) - S / 2 + 0.5) ** 2
    k = (np.sqrt(ax[None, :] + ax[:, None]) / max(1.0, 0.01 * S)).astype(np.int32)
    wt = (w * (arr.sum(-1) > 12.0)).ravel()
    nb = int(k.max()) + 1
    den = np.bincount(k.ravel(), wt, nb)
    has = den > 1.0
    out = np.empty((S, S, 3), np.float32)
    idx = np.arange(nb)
    for c in range(3):
        num = np.bincount(k.ravel(), arr[..., c].ravel() * wt, nb)
        prof = np.interp(idx, idx[has], num[has] / den[has]) if has.any() else np.zeros(nb)
        out[..., c] = prof[k]
    return out


def mirror_prefill(crop, feather, extra=()):
    """Fill the reflection from the same radius at a nearby angle.

    An iris is organised radially: brightness, colour and pigment change with distance from the pupil and stay
    comparatively steady around it. The earlier version donated from the point-mirrored side - same radius, opposite
    angle - so an eye with a darker sector across from the highlight got that darkness stamped exactly where the
    highlight had been. Rotating about the pupil centre keeps the radius exact while staying near in angle, and
    several offsets are averaged so a donor that is itself under glare simply does not vote.
    extra: further rotations, used only where every ROTATION_DONORS donor is itself masked (an eyelid can cover
    150 degrees of the rim, and there the fallback below would fill the lid with a blur of the lid); with them, the
    tone of pixels far from any clean one is matched to the clean iris at the same radius (_ring_tone), black
    pixels (outside the photo, where the client's square ran past its edge) never donate, and the donor set changes
    gradually: each donor fades out over DONOR_SOFT round the hole and the far donors join as the near ones' support
    fades (hard switches drew straight seams across a large lid fill, 26: seam step 17.1 -> 12.5, r3/softfill.py).
    Empty, the result is exactly the glare-only fill."""
    arr = np.asarray(crop).astype(np.float32)
    S = crop.size[0]
    a = np.clip(feather, 0.0, 1.0)[..., None]
    if extra:
        f = np.clip(feather, 0, 1).astype(np.float32)
        f = np.maximum(f, np.clip(2.0 * _blur_f(f, DONOR_SOFT * S / 2.0), 0.0, 1.0))   # only ever lowers a weight
        m_img = Image.fromarray((f * 255).astype(np.uint8))
        ones = Image.fromarray(np.where(arr.sum(-1) > 12.0, 255, 0).astype(np.uint8))
        del f
    else:
        m_img = Image.fromarray((np.clip(feather, 0, 1) * 255).astype(np.uint8))
        ones = Image.fromarray(np.full((S, S), 255, np.uint8))

    num, tot = _rotation_donors(crop, m_img, ones, ROTATION_DONORS)
    if extra:
        num2, tot2 = _rotation_donors(crop, m_img, ones, tuple(extra))
        wf = np.clip((0.7 - tot) / 0.7, 0.0, 1.0)
        num = num + num2 * wf
        tot = tot + tot2 * wf
        del num2, tot2, wf
    src = num / np.maximum(tot, 1e-3)
    del num
    blur = np.asarray(crop.filter(ImageFilter.GaussianBlur(S * 0.03))).astype(np.float32)
    src = np.where(tot < 0.35, blur, src)          # nowhere clean to borrow from

    # Match the donor to the local tone of the ring it lands in. The reference has to be measured from the
    # glare-free pixels only: blurring the original would fold the reflection's own brightness into the target
    # and pull the fill towards the very highlight being removed.
    rad = S * 0.05
    w = np.clip(1.0 - np.clip(feather, 0, 1), 0.0, 1.0)
    wb = _blur_f(w, rad)
    ok = wb > 0.02
    if extra:
        # An eyelid leaves pixels far from any clean one, where the old rule kept the donor's own tone: under an
        # upper lid that is often the lit lower iris from the far side, and it showed as a pale blob in the fill.
        # There the target is the mean tone of the clean iris at the same radius, blended in as local support fades.
        ring = _ring_tone(arr, w, S)
        t = np.clip(wb / 0.25, 0.0, 1.0)
        base_lo = np.stack([t * (_blur_f(arr[..., c] * w, rad) / np.maximum(wb, 1e-3)) + (1.0 - t) * ring[..., c]
                            for c in range(3)], -1)
        del ring, t
    else:
        base_lo = np.stack([np.where(ok, _blur_f(arr[..., c] * w, rad) / np.maximum(wb, 1e-3),
                                     _blur_f(src[..., c], rad)) for c in range(3)], -1)
    src_lo = np.stack([_blur_f(src[..., c], rad) for c in range(3)], -1)
    src = src + (base_lo - src_lo)
    return Image.fromarray(np.clip(arr * (1 - a) + src * a, 0, 255).astype(np.uint8))

PUPIL_HAZE_SIZE = (0.80, 1.10)  # the pupil read from colour counts only when its edge is this share of the vision
                                # pupil's radius: 0.84-1.06 on 6 of the 7 test photos where pupil_fill reads one (live
                                # 19: 0.94), 1.11 on 01 (a photo the quality gate stops as too dark)...
PUPIL_HAZE_SHIFT = 0.10         # ...and its centre this close to the vision pupil's (the frame centre), iris radii:
                                # 0.05-0.07 on live 19, 07, 08, 12. Further off, the vision box missed the pupil (18:
                                # 0.13) and the two fills join into one wide blob; the model redrew it centred and
                                # painted the uncovered side as a grey crescent that pupil_lock rightly leaves alone
PUPIL_HAZE_LIFT = 0.20          # ...and only when the photo, where that pupil lies past the vision fill (fill < 0.5,
                                # outside the glare mask), is lifted this share of the way from the fill tone to the
                                # iris just outside: a haze or a reflection left there. 0.33-0.54 on live 19, 07, 08,
                                # 12, 18 (teal or blue haze, a window); 0.07 on the dark rim of 19 at the e2e circle,
                                # which keeps HEAD's fill byte for byte
PUPIL_HAZE_FEATHER = 0.03       # that pupil's edge width (iris radii), centred on it: the photo's own blurred edge

def pupil_fill(crop, pr_px, glare_hard=None, feather=0.22, r_frac=None):
    """Rebuild the pupil as smooth darkness. A pupil reflects the room, so whatever a reflection covers there is
    not iris detail waiting to be restored - it is a hole, and the honest reconstruction is the dark it hid.
    The fill covers the vision pupil (pr_px, centred on the frame) and, when the brightness finds no pupil edge
    (pupil_circle None) but colour does (pupil_circle_chroma), that pupil too, out to its own edge, if it agrees with
    the vision pupil in size and place (PUPIL_HAZE_SIZE, PUPIL_HAZE_SHIFT) and still shows a haze or a reflection
    past the vision fill (PUPIL_HAZE_LIFT). A haze over the pupil (the sky or the room mirrored on the cornea, blue
    on live 19) is as bright as the iris' shadowed side and reaches past the feather, most where the vision circle
    sits off the pupil (live 19: the pupil 0.05 below it); the model painted that band as a ring of blue-grey iris,
    and pupil_lock could not take it back (no brightness circle on that input either). Where brightness reads the
    pupil, colour is not asked: a colourless reflection over the iris next to it pulls the colour circle out (13:
    0.37 against 0.31, 0.07 up). r_frac: the iris radius as a share of the crop side.
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
    a = np.clip((pr_px - d) / max(pr_px * feather, 1.0), 0, 1)
    R = (r_frac or iris_radius_frac()) * S
    pc = pupil_circle_chroma(crop, R / S) if pupil_circle(crop, R / S) is None else None
    if (pc is not None and PUPIL_HAZE_SIZE[0] <= pc[3] * R / pr_px <= PUPIL_HAZE_SIZE[1]
            and math.hypot(pc[0], pc[1]) <= PUPIL_HAZE_SHIFT):
        d2 = np.sqrt((xx - S / 2 + 0.5 - pc[0] * R) ** 2 + (yy - S / 2 + 0.5 - pc[1] * R) ** 2)
        a2 = np.clip((pc[3] * R - d2) / max(PUPIL_HAZE_FEATHER * R, 1.0) + 0.5, 0, 1)
        left = (a2 >= 1) & (a < 0.5) & ~g
        ring = (d2 > (pc[3] + 0.05) * R) & (d2 < (pc[3] + 0.20) * R) & (d < 0.9 * R) & ~g
        if int(left.sum()) > 60 and int(ring.sum()) > 60:
            y, tone = _lum3(arr)[..., 0], float(_lum3(base[None, :])[0, 0])
            if float(np.median(y[left])) - tone >= PUPIL_HAZE_LIFT * max(float(np.median(y[ring])) - tone, 1.0):
                a = np.maximum(a, a2)
    a = a[..., None]
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

# ----------------------------------------------------------------------------- eyelids
# An upper lid comes in from the top of the circle, a lower lid from the bottom: a cap of the disk cut off by a
# smooth, fairly flat margin, with skin, the lash line and hanging lashes on the rim side and the lid's shadow just
# below it. Everything here was fitted on the 27 licensed test photos plus the owner's crops and the site's sample
# eye, each re-cut exactly as the client sends it (TryApp.tsx: the unmasked 2 r pad square). Scratchpad
# wave-e/eyelid: annot/gt.json and r4/gt_extra.json (01, 10, 17, 20, the owner's 215106) hold hand-read lids,
# r4/sweep4.py gives the numbers quoted below.
LID_WORK = 160                   # the detector's working side: a lid is a large, smooth shape
LID_BLUR = 1.2                   # Lab blur at LID_WORK, px: fibre texture out, lid margins kept
LID_C0 = (-0.86, -0.05, 0.02)    # margin height on the centre line, iris radii. A lid reaching less than 0.14
                                 # into the circle stays out: the artwork keeps only 0.92 of it (STUDIO_TRIM), and
                                 # nearer the rim the dark limbal ring reads as a margin
LID_C1 = (-0.5, 0.51, 0.1)       # tilt (a head tilted up to ~25 degrees)
LID_C2 = (-0.1, 0.31, 0.1)       # bow. Lid margins are far flatter than the limbus: a curve following the limbal
                                 # ring would need ~0.55, so it is never a candidate
LID_BAND = 0.07                  # the colour step across a margin is read between two bands this wide
LID_EVAL_RIM = 0.90              # ...only inside this radius
LID_TOPK = 3                     # candidate margins kept per side
LID_HYST = 1.10                  # every plain bar below must be passed by this factor (10%): a margin sitting on a bar
                                 # flipped when the same photo was analysed again (13: 21% of the iris, then none)
LID_STEP_MIN = 7.0               # dE76 of the mean colour step across the margin
LID_REGION_DE = 10.0             # dE76 between the cap and the band of iris just below the margin
LID_REL_MAX = 0.45               # rim continuity (_lid_rim): step across the circle over the cap's arc / the same
LID_RIMCOV_MIN = 0.30            # step on the side sectors; or this share of the arc under 0.35 of it...
LID_CAP_DL = 8.0                 # ...either way with the cap at least this much L* above the iris below: a cap as light
                                 # as the iris over a partly covered rim was the sclera crescent and lashes of a circle
                                 # 6-8% high (15: dL 2.8-3.8); the real caps taken on the rim read dL 10-27 (r4 sweep)
LID_DARK_REL = 0.12              # a cap DARKER than the iris below it is taken only when the rim over its arc is almost
                                 # fully covered (rim median at most this). A dark cap is just as often the dark limbal
                                 # ring of a circle placed too high or too large (the sample eye 5-8% high: 0.21-0.28;
                                 # photo 03 8% high: 0.18); a real dark lid with lashes reads 0.02-0.04 (photo 08)
LID_THIN_C0 = -0.70              # a margin whose centre height is nearer the rim than this is a thin rim lid: the case
                                 # where a circle 5-8% off also puts a cap of real iris or limbus under a flat edge
LID_THIN_RIM = (0.20, 0.65, 10.0)   # a thin rim lid needs the rim median at most the first, this share covered AND
                                 # the cap this much L* above the iris below it (skin): the sample eye's circle 6% high
                                 # put its limbal ring under a flat edge with rim 0.18 / 1.0 but only 3.8-6.4 L* up...
LID_THIN_STRONG = (18.0, 23.0, 11.0, 0.40, 0.50)   # ...or a strong, clean margin: step, region dE, L* above the
                                 # iris, rim median at most, rim share covered at least (05's thin upper lid: 22.9, 28.5,
                                 # 13.5, 0.33, 0.60 put a red band in the artwork; the nearest lid-free candidate over the
                                 # sweep, the amber sample 8% high, read 19.1, 22.2, 12.9, 0.48, 0.16)
LID_SKIN_THIN = (18.0, 22.0, 18.0, 5.0)   # ...or strong skin: step, region dE, L* above the iris, and C* above the
                                 # side iris at the same radius (skin is pink; the sclera of an oversize circle is grey)
LID_SKIN = (15.0, 18.0, 15.0)    # no rim evidence needed for bright skin: step, region dE and L* above the iris
LID_DEEP_STEP = 14.5             # the margin that bounds a side's mask (its deepest accepted one), when it reaches past
                                 # LID_THIN_C0, must be a strong step (x LID_HYST: 15.95) or no lid is reported at all.
                                 # A weak step deep in the iris is not a lid margin over iris: it is the lower end of
                                 # lashes hanging over the iris (29: 8.4-10.6 over the sweep4 circles), a lid seen past
                                 # the iris by a circle too large for it, over its wet rim and reflections (21: 7.8-15.6),
                                 # or blur (10: 7.8-9.9). Filled down to it, the fill copied that texture (29: a plaid of
                                 # squares in both renders; 21: a grey band and a straight seam; wave-g/fix-engine/
                                 # resid29_v1_pct_rule.jpg: copied lashes). Real lid margins: 06 21.9-26.1, 26 16.6-19.9,
                                 # 17 18.0-18.3. sweep4: off on 21 in 82 of its 82 fired circles, 29 60 of 75, 10 48 of
                                 # 48, 27 3 of 3; 09 loses 5 of 83 and 19 7 of 75; no other photo changes
LID_DEEPEST = -0.25              # a margin reaching nearer the centre than this (within 0.7 r of the centre line) is not
                                 # a lid: a boundary across the pupil half is a reflection edge (02's sky: 20% real iris)
LID_LIMBUS_MIN = 0.92            # the side sectors' limbus (both sides) inside this: the circle is oversize, and what
                                 # a lid fill would borrow at the rim is sclera (22). No lid is then reported
LID_PUPIL_PAD = (1.15, 0.03)     # the pupil (x 1.15 + 0.03 iris radii) is not read: its edge is not a lid margin (23)
LID_RIM_SCALE = (1.00, 1.04)     # the rim test is read at the side sectors' limbus radius, clamped to this range: never
                                 # inside the circle (reading it at 0.93-0.95 on the sample eye with its circle 6-10%
                                 # too large masked 3.6-4.1% of real iris), at most 1.04 (the client's square reaches
                                 # 1.12 radii, and the outside band needs room)
LID_SHADOW = 0.06                # the mask always reaches this far (iris radii) below the margin: lash line, lashes
LID_SHADOW_THIN = 0.03           # ...below a lid taken by a thin-rim rule only this far (its margin line), with no shadow
                                 # band: with the circle 6-8% low the owner's lower lid (215106) and 20's put 0.06 and
                                 # the band onto real iris (dark crypts). A dark lid with lashes keeps both
LID_SHADOW_MAX = 0.30            # at most this far in all: in 0.03 strips per 0.1-wide column, it goes on while the
LID_SHADOW_DL = 10.0             # iris there is darker than the side sectors at the same radius by this much L* (the
LID_SHADOW_DC = 8.0              # lid's shadow) or greyer by this much C* (a brown eye's lash line: C* 2-8 vs 13-22)
LID_SHADOW_OPEN = 3              # ...and a reach must hold over this many neighbouring 0.1-wide columns
LID_SHADOW_PUPIL = (1.04, 0.02)  # the shadow band is read down to the pupil x 1.04 + 0.02, and never past it
LID_FEATHER = 0.012              # soft edge of the lid mask, share of the frame side
LID_ANGLES = 180                 # 2-degree bins for the rim continuity
LID_EXTRA_DONORS = (140, -140, 180)   # mirror_prefill donors further round, for a lid too wide for the near ones
LID_DRIFT_MAX = 20.0             # lid_drift of the fill above this: no clean iris to borrow from, the lid is left as
                                 # before (studio_grade's trim). The model's recoloured lid patches read 22-26
LID_DRIFT_ARC = 40.0             # lid_drift also compares the fill with the clean iris within this many degrees of the
                                 # lid at the same radius (the lid's own shadow), and keeps the smaller of the two


def _lid_lab(im, n):
    small = np.asarray(im.resize((n, n), Image.BOX if im.size[0] >= 2 * n else Image.LANCZOS), dtype=np.float32)
    lab = srgb_to_lab(small).astype(np.float32)
    return np.stack([_blur_f(lab[..., c], LID_BLUR) for c in range(3)], -1)


def _lid_curves():
    c0 = np.arange(*LID_C0); c1 = np.arange(*LID_C1); c2 = np.arange(*LID_C2)
    return np.stack(np.meshgrid(c0, c1, c2, indexing="ij"), -1).reshape(-1, 3)


def _lid_margins(lab, ys, xs, valid, G, r_frac=None):
    """Score of every candidate margin y = c0 + c1 x + c2 x^2 (in the side's own coordinates: the rim is at the
    top, y < curve is the lid side). Per column, the mean Lab in a LID_BAND band above the curve minus the one below
    it; the score is the length of the mean step (dE76) x sqrt(share of the columns the curve crosses inside
    LID_EVAL_RIM that were usable) x share of usable columns whose own step points the same way. A lid margin is one
    consistent step along its whole length; radial fibres, crypts and a lighting gradient are not. Per-column
    cumulative sums make all 2255 curves one set of gathers (every second column: the step is a mean anyway)."""
    n = lab.shape[0]
    v = valid.astype(np.float32)
    cols = np.arange(0, n, 2)
    lab_c, v_c, xs_c = lab[:, cols], v[:, cols], xs[cols]
    nc = len(cols)
    CS = np.concatenate([np.zeros((1, nc, 3), np.float32), np.cumsum(lab_c * v_c[..., None], 0, dtype=np.float32)], 0)
    CN = np.concatenate([np.zeros((1, nc), np.float32), np.cumsum(v_c, 0, dtype=np.float32)], 0)
    CS = CS.reshape(-1, 3); CN = CN.ravel()
    yb = (G[:, :1] + G[:, 1:2] * xs_c[None] + G[:, 2:3] * xs_c[None] ** 2).astype(np.float32)
    y0, dy = float(ys[0]), float(ys[1] - ys[0])
    ci = np.arange(nc)[None]

    def rows(y):
        # the rows whose centre lies above y, on the uniform grid ys (what searchsorted(ys, y) counts), as flat indices
        return np.clip(np.ceil((y - y0) / dy), 0, n).astype(np.int64) * nc + ci
    k0, k1, k2 = rows(yb - LID_BAND), rows(yb), rows(yb + LID_BAND)
    na = CN[k1] - CN[k0]; nb = CN[k2] - CN[k1]
    need = max(2.0, 0.6 * LID_BAND * (r_frac or iris_radius_frac()) * n)
    use = (na >= need) & (nb >= need)
    step = (CS[k1] - CS[k0]) / np.maximum(na, 1)[..., None] - (CS[k2] - CS[k1]) / np.maximum(nb, 1)[..., None]
    step *= use[..., None]
    ncol = use.sum(1)
    span = ((np.abs(xs_c)[None] < LID_EVAL_RIM)
            & (np.abs(yb) < np.sqrt(np.maximum(LID_EVAL_RIM ** 2 - xs_c[None] ** 2, 0)))).sum(1)
    mean = step.sum(1) / np.maximum(ncol, 1)[:, None]
    mag = np.sqrt((mean ** 2).sum(-1))
    unit = mean / np.maximum(mag, 1e-3)[:, None]
    agree = (((step * unit[:, None, :]).sum(-1) > 0.5 * mag[:, None]) & use).sum(1) / np.maximum(ncol, 1)
    return mag * np.sqrt(ncol / np.maximum(span, 1)) * agree * (ncol >= 3)


def _lid_rim(lab, rho, ang):
    """Per 2-degree angle: how different what lies just inside the circle (0.88-0.97) is from what lies just outside
    it (1.03-1.10), as a share of the same step on the side sectors (+-30 degrees round 0 and 180), where lids never
    reach and the limbus is always visible. Where the iris shows up to the circle there is a limbus: limbal ring
    inside, sclera or a lid margin outside. Where a lid covers the rim, the same skin and lashes run across it and the
    share is small. Needs the unmasked square the client sends; returns None when there is nothing outside the circle
    (a pre-masked crop), and then no lid is ever found by rim evidence."""
    lp = lab[..., 0]
    lstd = np.sqrt(np.maximum(_blur_f(lp * lp, 1.5) - _blur_f(lp, 1.5) ** 2, 0))
    f = np.concatenate([lab, lstd[..., None]], -1)
    NA = LID_ANGLES
    b = (ang // (360.0 / NA)).astype(int) % NA
    fi = np.full((NA, 4), np.nan, np.float32); fo = np.full((NA, 4), np.nan, np.float32)
    for m, dst in (((rho >= 0.88) & (rho < 0.97), fi), ((rho >= 1.03) & (rho < 1.10), fo)):
        bi, vals = b[m], f[m]
        order = np.argsort(bi, kind="stable"); bi, vals = bi[order], vals[order]
        cuts = np.searchsorted(bi, np.arange(NA + 1))
        for i in range(NA):
            if cuts[i + 1] > cuts[i]: dst[i] = np.median(vals[cuts[i]:cuts[i + 1]], 0)
    dark = ~(fo[:, 0] >= 3.0)                  # nothing outside the circle at this angle (a NaN counts as nothing)
    if dark.mean() > 0.85:
        return None
    fi = np.nanmedian(np.stack([np.roll(fi, s, 0) for s in range(-2, 3)]), 0)
    fo = np.nanmedian(np.stack([np.roll(fo, s, 0) for s in range(-2, 3)]), 0)
    step = np.sqrt(((fi - fo) ** 2).sum(-1))
    a = (np.arange(NA) + 0.5) * 360.0 / NA
    side = ((np.abs(((a + 180) % 360) - 180) <= 30) | (np.abs(a - 180) <= 30)) & ~dark
    if side.sum() < 6: return None
    ref = float(np.nanmedian(step[side]))
    if not np.isfinite(ref) or ref < 1e-3: return None
    return np.nan_to_num(step / ref, nan=9.0)


def _lid_side_limbus(lab, rho, ang):
    """The limbus radius on each side sector (+-30 degrees round 0 and 180, where lids never reach): the radius, in
    0.70-1.15 iris radii, where the median L* of 0.025-wide rings climbs the most (iris to sclera). [right, left];
    NaN where a side has too little to read."""
    lp = lab[..., 0]
    edges = np.arange(0.60, 1.20, 0.025)
    mid = edges[1:-1]
    out = []
    for c in (0.0, 180.0):
        sel = np.abs(((ang - c + 180) % 360) - 180) <= 30
        med = np.full(len(edges) - 1, np.nan)
        for i in range(len(edges) - 1):
            m = sel & (rho >= edges[i]) & (rho < edges[i + 1]) & (lp > 2.0)
            if m.sum() >= 4: med[i] = np.median(lp[m])
        g = np.diff(med)
        ok = np.isfinite(g) & (mid >= 0.70) & (mid <= 1.15)
        out.append(float(mid[ok][np.argmax(g[ok])]) if ok.any() else float("nan"))
    return out


def _lid_side_chroma(lab, lc, rho, sides, cut, inner_f):
    """Median C* of the cap's pixels (inner_f) minus the C* of the side sectors' iris at the same radius (median a*
    and b* per 0.05 ring; the cap, glare and pupil left out via cut). NaN when the sides give fewer than 2 rings."""
    edges = np.arange(0.25, 0.951, 0.05)
    prof = np.full((len(edges) - 1, 2), np.nan)
    for k in range(len(edges) - 1):
        sel = (rho >= edges[k]) & (rho < edges[k + 1]) & sides & ~cut
        if sel.sum() >= 6: prof[k] = np.median(lab[..., 1][sel]), np.median(lab[..., 2][sel])
    okb = np.isfinite(prof[:, 0])
    if okb.sum() < 2 or not inner_f.any(): return float("nan")
    mid = (edges[:-1] + 0.025)[okb]
    ra = np.interp(rho[inner_f], mid, prof[okb, 0]); rb = np.interp(rho[inner_f], mid, prof[okb, 1])
    return float(np.median(lc[inner_f] - np.hypot(ra, rb)))


def lid_geometry(crop, r_frac=None, glare_hard=None, debug=None, pupil_rho=None):
    """The eyelids in a square iris crop: [(side, xk, bk)], side "top" or "bottom". The lid is the part of the disk
    on the rim side of the curve through (xk, bk), in iris radii from the centre, x right, y down (for the bottom lid
    y is measured upwards): the accepted margins y = c0 + c1 x + c2 x^2, plus LID_SHADOW for the lash line, plus the
    lid's shadow where the iris below is darker than the side sectors. Empty = no lid.

    How a cap is found: per side the LID_TOPK strongest margins (_lid_margins, the pupil left out), each kept only
    when every bar is passed by LID_HYST:
      - the margin stays out of the pupil half (LID_DEEPEST), the step and the cap's difference from the iris just
        below it pass LID_STEP_MIN / LID_REGION_DE, and
      - a cap darker than the iris below needs the rim over its arc almost fully covered (LID_DARK_REL);
      - a thin rim lid (centre height at or nearer the rim than LID_THIN_C0) needs a covered rim (LID_THIN_RIM), a
        strong clean margin (LID_THIN_STRONG) or strong pink skin (LID_SKIN_THIN); it then masks only LID_SHADOW_THIN
        below its margin and grows no shadow band;
      - any other cap needs LID_CAP_DL of lightness over the iris and a covered rim (_lid_rim: the lid runs out
        across the circle, no limbus), or bright skin.
    No lid at all when both side limbi say the circle is oversize (LID_LIMBUS_MIN), nor when a side's deepest accepted
    margin reaches past the thin rim zone with a weak step (LID_DEEP_STEP: hanging lashes, or a circle reaching past
    the iris, not a lid margin over iris). The shadow band below a lid holds
    over LID_SHADOW_OPEN neighbouring columns and never reads past the pupil.
    Measured (wave-e/eyelid/r4, sweep4.py: the live analyze circle and pupil_r of all 36 photos, moved 1-8% up and
    down in 1% steps, 2-8% sideways, 2-12% larger or smaller, combined, and with the pupil 0.7-1.4x; 87 runs each):
    no mask at all on the 9 lid-free eyes (6 test photos, the owner's 215102 and 215120, the blue sample) nor on 13
    and the amber sample (957 runs); the owner's 215106 (a lower-lid sliver) fires 2 of 87 with at most 0.05% of the
    disk outside the hand-read lid inside 0.90 r; 15 fires 0 of 87 (round 3: 9, up to 9.5% of real iris). See
    lid_mask for coverage.
    crop: the square as the client sent it, NOT masked (the rim test reads outside the circle). r_frac: iris radius
    as a share of the side (iris_radius_frac(pad)). glare_hard: the glare mask at any size; those pixels are not
    read. pupil_rho: the pupil radius in iris radii (read from the crop when not given). debug: a list that collects
    the numbers behind each decision."""
    n = LID_WORK
    r_frac = r_frac or iris_radius_frac()
    lab = _lid_lab(crop, n)
    ax = (np.arange(n) - n / 2 + 0.5) / (r_frac * n)
    X, Y = np.meshgrid(ax, ax)
    rho = np.sqrt(X * X + Y * Y)
    ang = (np.degrees(np.arctan2(Y, X)) + 360.0) % 360.0
    glare = np.zeros((n, n), bool)
    if glare_hard is not None and np.any(glare_hard):
        glare = np.asarray(Image.fromarray(np.asarray(glare_hard, np.uint8)).resize((n, n), Image.BILINEAR)) > 60
    limbus = _lid_side_limbus(lab, rho, ang)
    if debug is not None:
        debug.append(dict(limbus=[round(v, 3) for v in limbus]))
    if all(np.isfinite(limbus)) and max(limbus) < LID_LIMBUS_MIN:
        return []
    pr = pupil_rho if pupil_rho else pupil_radius(np.clip(lab[..., 0] * 2.55, 0, 255), rho)
    pupil = rho < max(0.25, (pr or 0.0) * LID_PUPIL_PAD[0] + LID_PUPIL_PAD[1])
    valid = (rho < LID_EVAL_RIM) & ~pupil & ~glare
    # the rim test reads across the limbus the side sectors show, not across the analyze circle: a circle 5% too
    # small put both of its bands on the lid and hid a 40% lid (29)
    lf = [v for v in limbus if np.isfinite(v)]
    rs = float(np.clip(np.median(lf), *LID_RIM_SCALE)) if lf else 1.0
    rel = _lid_rim(lab, rho / rs, ang)
    G = _lid_curves()
    th = np.radians((np.arange(LID_ANGLES) + 0.5) * 360.0 / LID_ANGLES)
    lc = np.hypot(lab[..., 1], lab[..., 2])
    sides = (np.abs(((ang + 180) % 360) - 180) <= 35) | (np.abs(ang - 180) <= 35)
    xd = np.linspace(-0.7, 0.7, 29)
    H = LID_HYST
    accepted = []
    deepest = {}                   # side -> (c0, step) of its deepest accepted margin (LID_DEEP_STEP)
    for top in (True, False):
        if top:
            lab_s, Ys, val_s, glare_s, rho_s, pup_s = lab, Y, valid, glare, rho, pupil
        else:          # the bottom lid is the top lid of the frame flipped upside down
            lab_s, Ys, val_s, glare_s, rho_s, pup_s = lab[::-1], -Y[::-1], valid[::-1], glare[::-1], rho[::-1], pupil[::-1]
        sc = _lid_margins(lab_s, Ys[:, 0], X[0], val_s, G, r_frac)
        kept = []
        for i in np.argsort(-sc)[:600]:
            if sc[i] <= 0 or len(kept) >= LID_TOPK: break
            c = G[i]
            capm = (Ys < c[0] + c[1] * X + c[2] * X * X) & (rho_s < 0.97)
            if capm.sum() < 5 or any((capm & q).sum() / max((capm | q).sum(), 1) > 0.5 for q, _ in kept): continue
            kept.append((capm, i))
        for capm, i in kept:
            c = G[i]
            if float(np.max(c[0] + c[1] * xd + c[2] * xd * xd)) > LID_DEEPEST:
                if debug is not None:
                    debug.append(dict(side="top" if top else "bottom", c=[round(float(v), 2) for v in c], ok=False,
                                      why="deep"))
                continue
            yb = c[0] + c[1] * X + c[2] * X * X
            inner = capm & (rho_s < 0.93) & (rho_s > 0.25) & ~glare_s & ~pup_s
            below = (Ys >= yb) & (Ys < yb + 0.15) & (rho_s < 0.93) & (rho_s > 0.25) & ~glare_s & ~pup_s
            if inner.sum() < 8 or below.sum() < 8: continue
            a, b = lab_s[inner].mean(0), lab_s[below].mean(0)
            dE = float(np.sqrt(((a - b) ** 2).sum())); dL = float(a[0] - b[0])
            xr, yr = 0.97 * rs * np.cos(th), 0.97 * rs * np.sin(th)
            on = (yr if top else -yr) < c[0] + c[1] * xr + c[2] * xr * xr      # the cap's arc of the rim
            if rel is not None and on.any():
                r_med = float(np.median(rel[on])); r_cov = float((rel[on] < 0.35).mean())
            else:
                r_med, r_cov = 9.0, 0.0
            s = float(sc[i])
            dC = None
            thin = c[0] <= LID_THIN_C0 + 1e-6         # the grid's -0.70 is -0.6999...: it counts as thin (15)
            if s < LID_STEP_MIN * H or dE < LID_REGION_DE * H:
                ok, why = False, "weak"
            elif dL < 0:
                ok, why = r_med <= LID_DARK_REL / H, "dark"
            elif thin:
                ok, why = (r_med <= LID_THIN_RIM[0] / H and r_cov >= LID_THIN_RIM[1] * H
                           and dL >= LID_THIN_RIM[2] * H), "thin"
                if not ok and (s >= LID_THIN_STRONG[0] * H and dE >= LID_THIN_STRONG[1] * H
                               and dL >= LID_THIN_STRONG[2] * H and r_med <= LID_THIN_STRONG[3] / H
                               and r_cov >= LID_THIN_STRONG[4] * H):
                    ok, why = True, "thin strong"
                if not ok and s >= LID_SKIN_THIN[0] * H and dE >= LID_SKIN_THIN[1] * H and dL >= LID_SKIN_THIN[2] * H:
                    cap_f = capm if top else capm[::-1]
                    inner_f = inner if top else inner[::-1]
                    dC = _lid_side_chroma(lab, lc, rho, sides, cap_f | glare | pupil, inner_f)
                    ok, why = bool(dC >= LID_SKIN_THIN[3] * H), "thin skin"
            else:
                ok, why = (dL >= LID_CAP_DL * H and (r_med <= LID_REL_MAX / H or r_cov >= LID_RIMCOV_MIN * H)
                           or (s >= LID_SKIN[0] * H and dE >= LID_SKIN[1] * H and dL >= LID_SKIN[2] * H)), "cap"
            if debug is not None:
                debug.append(dict(side="top" if top else "bottom", c=[round(float(v), 2) for v in c],
                                  step=round(s, 1), dE=round(dE, 1), dL=round(dL, 1), rim=round(r_med, 2),
                                  rim_cov=round(r_cov, 2), dC=None if dC is None else round(dC, 1), why=why,
                                  ok=bool(ok)))
            if ok:
                accepted.append(("top" if top else "bottom", tuple(float(v) for v in c), why.startswith("thin")))
                sd = "top" if top else "bottom"
                if sd not in deepest or c[0] > deepest[sd][0]:
                    deepest[sd] = (float(c[0]), s)
    if not accepted:
        return []
    for sd, (c0_, s_) in deepest.items():
        if c0_ > LID_THIN_C0 + 1e-6 and s_ < LID_DEEP_STEP * H:
            if debug is not None:
                debug.append(dict(skip="weak deep margin", at=sd, c0=round(c0_, 2), step=round(s_, 1)))
            return []
    # the lid's shadow, column by column: below the lid's boundary, 0.03-high strips of iris darker than the side
    # sectors at the same radius (the sectors' own profile, lids and glare left out). A lash line is often thicker
    # at one corner, so the reach is read in 0.1-wide columns, smoothed, and drawn as a curve
    lp = lab[..., 0]
    lc = np.hypot(lab[..., 1], lab[..., 2])
    capall = np.zeros((n, n), bool)
    for side, c, _ in accepted:
        yb = c[0] + c[1] * X + c[2] * X * X
        capall |= (Y < yb) if side == "top" else (-Y < yb)
    sides = (np.abs(((ang + 180) % 360) - 180) <= 35) | (np.abs(ang - 180) <= 35)
    edges = np.arange(0.25, 0.951, 0.05)
    prof = np.full((len(edges) - 1, 2), np.nan)
    for i in range(len(edges) - 1):
        sel = (rho >= edges[i]) & (rho < edges[i + 1]) & sides & ~glare & ~capall & ~pupil
        if sel.sum() >= 8: prof[i] = np.median(lp[sel]), np.median(lc[sel])
    okb = np.isfinite(prof[:, 0])
    ref = None
    if okb.sum() >= 3:
        mid = (edges[:-1] + 0.025)[okb]
        ref = (np.interp(rho, mid, prof[okb, 0]), np.interp(rho, mid, prof[okb, 1]))
    # the shadow is read down to the pupil itself (the lid_mask disk), not to the padded pupil of the margin search:
    # a half-closed eye's lash tips hang to the pupil (26)
    pupil_x = rho < max(0.25, (pr or 0.0) * LID_SHADOW_PUPIL[0] + LID_SHADOW_PUPIL[1])
    xk = np.linspace(-1.0, 1.0, 81)
    xbins = np.arange(-0.9, 0.901, 0.1)
    out = []
    for side in ("top", "bottom"):
        caps = [c for s_, c, _ in accepted if s_ == side]
        if not caps: continue
        # a thin rim lid grows no shadow band: below a rim-thin margin the dark columns were the owner's crypts
        # (215106 with its circle 7-8% low), never a lid shadow
        grow = not all(t_ for s_, _, t_ in accepted if s_ == side)
        band = LID_SHADOW if grow else LID_SHADOW_THIN
        Ys = Y if side == "top" else -Y
        yu = np.max([c[0] + c[1] * X + c[2] * X * X for c in caps], 0) + band   # the lid plus its lash band
        reach = np.zeros(len(xbins) - 1)
        if ref is not None and grow:
            dev, devc = lp - ref[0], lc - ref[1]
            for j in range(len(xbins) - 1):
                colm = (X >= xbins[j]) & (X < xbins[j + 1]) & (rho < 0.95) & (rho > 0.3) & ~glare & ~pupil_x
                t, seen = 0.0, False
                # the band ends at the last strip darker (LID_SHADOW_DL) or greyer (LID_SHADOW_DC) than the sides, as
                # long as no strip before it is back within half of both (one wet, bright margin line between the
                # lashes and the shadow does not stop it)
                while t < LID_SHADOW_MAX - band - 1e-6:
                    strip = colm & (Ys >= yu + t) & (Ys < yu + t + 0.03)
                    if strip.sum() < 3:
                        if seen: break             # the pupil or a reflection ends the band: never read past it
                        t += 0.03; continue        # outside the circle at this column: look further in
                    seen = True
                    d, dc = float(np.median(dev[strip])), float(np.median(devc[strip]))
                    if d > -0.5 * LID_SHADOW_DL and dc > -0.5 * LID_SHADOW_DC: break
                    if d <= -LID_SHADOW_DL or (dc <= -LID_SHADOW_DC and d <= 0): reach[j] = t + 0.03
                    t += 0.03
            nb_ = np.maximum(np.concatenate([[0.0], reach[:-1]]), np.concatenate([reach[1:], [0.0]]))
            reach = np.minimum(reach, nb_ + 0.03)                                     # no lone spikes
            # a lid shadow runs along the lid: the reach must hold over LID_SHADOW_OPEN neighbouring columns
            # (a morphological opening). One or two columns reaching deeper follow dark crypts (215106, 15)
            k_ = LID_SHADOW_OPEN // 2
            win = lambda a, f: np.array([f(a[j:j + 2 * k_ + 1]) for j in range(len(reach))])
            reach = win(np.pad(win(np.pad(reach, k_, mode="edge"), np.min), k_, mode="edge"), np.max)
            reach = np.convolve(np.pad(reach, 2, mode="edge"), np.array([1, 2, 3, 2, 1]) / 9.0, "valid")  # smooth
        xc = 0.5 * (xbins[:-1] + xbins[1:])
        base = np.max([c[0] + c[1] * xk + c[2] * xk * xk for c in caps], 0) + band
        bk = base + np.interp(xk, xc, reach)
        if debug is not None:
            debug.append(dict(side=side, reach=[round(float(v), 2) for v in reach]))
        out.append((side, xk, bk))
    return out


def lid_mask(crop, r_px, glare_hard=None, size=None, debug=None, pupil_rho=None):
    """Eyelid skin, lash line, lashes and lid shadow inside the iris circle of a square crop, as the glare mask gives
    it: (hard uint8 0/255, feathered float32 0..1, pct of the iris disk). crop must be the UNMASKED square (see
    lid_geometry); r_px its iris radius in its own pixels; size the side of the masks returned (default the crop's):
    the lids are found once on a small copy and drawn at whatever size the caller works at. The mask stops at the
    circle (1.02 radii) and never enters the inner 0.25, nor the pupil (pupil_rho x 1.04 iris radii, the disk
    drop_pupil takes out), so pct is final: masked pixels inside the circle over the circle's pixels. No lid: all-zero
    masks and 0.0. Measured at the live analyze circle (wave-e/eyelid/r4, sweep4.py): found on 7 of the 24 photos
    with a hand-read lid (01, 05, 06, 08, 09, 19, 26); left alone, as before: thin rim lids (02, 07, 15, 16, 17, 20,
    25, 30, the owner's 215106 and 215208), lashes over a reflection or without a lid edge (11, 23, 27), a weak margin
    deep in the iris (LID_DEEP_STEP: 29's hanging lashes, 21's circle past the iris, the blurred 10) and the oversize
    circle of 22."""
    S = int(size or crop.size[0])
    geom = lid_geometry(crop, r_px / float(crop.size[0]), glare_hard, debug, pupil_rho)
    if not geom:
        return np.zeros((S, S), np.uint8), np.zeros((S, S), np.float32), 0.0
    R = r_px / float(crop.size[0]) * S
    ax = (np.arange(S) - S / 2 + 0.5) / R
    X, Y = np.meshgrid(ax, ax)
    rho = np.sqrt(X * X + Y * Y)
    m = np.zeros((S, S), bool)
    for side, xk, bk in geom:
        yb = np.interp(ax, xk, bk)[None, :]              # the lid's lower boundary, per column
        m |= (Y < yb) if side == "top" else (-Y < yb)
    keep = rho > max(0.25, (pupil_rho or 0.0) * 1.04)
    m &= (rho < 1.02) & keep
    del X, Y
    disk = rho < 1.0
    pct = 100.0 * float((m & disk).sum()) / max(1.0, float(disk.sum()))
    # soft edge outwards only: the whole cap is replaced, and the fill fades into the iris over ~2 LID_FEATHER
    soft = np.clip(2.0 * _blur_f(m.astype(np.float32), max(1.0, LID_FEATHER * S / 2.0)), 0.0, 1.0)
    soft = (np.maximum(soft, m.astype(np.float32)) * keep).astype(np.float32)
    return (m * 255).astype(np.uint8), soft, pct


def lid_drift(crop, im, lid_hard, glare_hard, r_px):
    """How far `im` (the repaired crop) moved the colour of the lid area away from the iris' own colour: per 0.05
    band of radius, dE76 between im's median Lab inside the lid mask and the crop's median Lab of clean iris (no
    lid, no glare), or the clean iris within LID_DRIFT_ARC degrees of the lid when that is nearer, averaged over the
    bands weighted by lid pixels. The fill is borrowed from those same radii, so an honest repair stays near them.
    Measured (wave-e/eyelid drift.py): the model's lid patches read 5.2-16.7 where they looked right and 22.1 / 26.4
    where they recoloured the area (09); /api/deglare uses it as a guard on its own fill (r3/prefill3.py and
    r4/art4.py list the values)."""
    S0 = crop.size[0]
    S = min(S0, 512)                     # medians of whole bands: a half-size copy reads the same and costs a quarter
    k = S / float(S0)
    ax = (np.arange(S) - S / 2 + 0.5) / max(1.0, r_px * k)
    rho = np.sqrt(ax[None, :] ** 2 + ax[:, None] ** 2)
    blur = ImageFilter.GaussianBlur(3 * k)
    a = srgb_to_lab(np.asarray(crop.resize((S, S), Image.BOX).filter(blur), dtype=np.float32))
    b = srgb_to_lab(np.asarray(im.resize((S, S), Image.BOX).filter(blur), dtype=np.float32))
    lid = np.asarray(Image.fromarray(np.asarray(lid_hard, np.uint8)).resize((S, S), Image.NEAREST)) > 0
    clean = ~lid
    if glare_hard is not None:
        clean &= ~(np.asarray(Image.fromarray(np.asarray(glare_hard, np.uint8)).resize((S, S), Image.NEAREST)) > 0)
    # 2-degree bins of angle, for the clean iris right next to the lid at the same radius
    abin = ((np.degrees(np.arctan2(ax[:, None], ax[None, :])) + 360.0) % 360.0 / 2.0).astype(int) % 180
    near = int(LID_DRIFT_ARC / 2)
    tot, acc = 0, 0.0
    for r0 in np.arange(0.30, 0.95, 0.05):
        band = (rho >= r0) & (rho < r0 + 0.05)
        pl, cl = band & lid, band & clean
        if pl.sum() < 50 * k * k or cl.sum() < 50 * k * k: continue
        fill = np.median(b[pl], 0)
        de = float(np.sqrt(((fill - np.median(a[cl], 0)) ** 2).sum()))
        # ...or against the iris beside the lid (within LID_DRIFT_ARC of it): a lid casts its shadow on the iris round
        # it, and a fill as dark as that shadow is honest (05: 23 against the whole ring, 4-9 L* against 20-23)
        occ = np.zeros(180, bool); occ[np.unique(abin[pl])] = True
        grow = np.zeros(180, bool)
        for s_ in range(-near, near + 1): grow |= np.roll(occ, s_)
        cn = cl & grow[abin]
        if cn.sum() >= 50 * k * k:
            de = min(de, float(np.sqrt(((fill - np.median(a[cn], 0)) ** 2).sum())))
        acc += de * float(pl.sum()); tot += float(pl.sum())
    return acc / tot if tot else 0.0


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

# ----------------------------------------------------------------------------- pupil lock
# The image model draws the pupil at the size it expects, not the size the photo shows. On the 27 wave-c test
# renders it shrank 4 of the 7 pupils of 0.37 of the iris radius or wider (23: 0.72 -> 0.32, 24: 0.53 -> 0.40,
# 19: 0.39 -> 0.32, 12: 0.40 -> 0.34), none of the 15 narrower ones by more than 0.03, and filled the gap with iris
# the photo does not show (grey on 23: chroma_lock gives it the pupil's colourless chroma). Four renders of the
# owner's 215102 did the same (0.48-0.49 -> 0.30, 0.40, 0.40, 0.43). pupil_lock() puts the photo's pupil back.
PUPIL_LOCK_SIDE = 256        # both images are measured on a copy this size, so a 4096 master reads like its preview
PUPIL_LOCK_SECTORS = 24      # 15-degree sectors, each finds its own pupil edge; one circle is fitted through them
PUPIL_LOCK_EDGE = 0.35       # the edge: where a sector's median climbs this share of the way from the pupil to the iris
PUPIL_LOCK_EDGE_HI = 0.60    # second try when that fails: a room reflected in the top of a pupil sits over the first
                             # level (the owner's 215102: pupil 19, reflection 52, iris 107) and moves those edges in
PUPIL_LOCK_TRUE = 0.50       # the restored disk ends where the photo's edge is half way up: under an even blur the
                             # true edge (0.011-0.028 outside the PUPIL_LOCK_EDGE circle on 12, 19, 23, 24; capped at 0.03)
PUPIL_LOCK_FIT = 0.02        # a circle counts only when half of the sector edges lie this close to it (iris radii):
                             # accepted fits read 0.018 at most, circles pulled by a reflection (215102) or a lid
                             # shadow (26, 09) 0.030-0.049
PUPIL_LOCK_CONTRAST = 25.0   # iris minus pupil, grey levels: below this the pupil is not measured (as pupil_radius)
PUPIL_LOCK_RIM = 0.03        # the render is judged on the photo's pupil this far inside its edge...
PUPIL_LOCK_SHARE = 0.06      # ...and corrected only when it shows iris over more than this share of it,
PUPIL_LOCK_BAND = 0.06       # all the way round: in each of the PUPIL_LOCK_SECTORS sectors of the band this deep
PUPIL_LOCK_EVEN = 0.35       # inside its edge, iris over at least this share. A shrunk pupil leaves iris all round
                             # (lowest sector 0.43-0.93 on the 11 renders locked); a circle that sits off the pupil
                             # leaves a crescent: 0.00 on 26, 07, 09 and the owner's 215102 (the builder's circles),
                             # and at most 0.27 when a correct render's circle is moved 0.03-0.08 and grown to touch it
PUPIL_LOCK_TOL = 0.04        # its own pupil is at least this much smaller (iris radii)...
PUPIL_LOCK_INSIDE = 0.02     # ...and lies inside the photo's, to this much. Not the same centre: a model that shrinks
                             # a pupil also centres it (23 by 0.06), and an off-centre photo pupil must still count.
PUPIL_LOCK_FEATHER = 0.006   # width of the restored edge (iris radii): 3 px at 1024, 11 px on the 4096 master, as
                             # crisp as the model's own pupil edge there
PUPIL_LOCK_RUFF = 0.03       # just outside that edge the render is kept no brighter, against its iris, than the photo
                             # is there against its own, fading out over this width (iris radii): it darkens the band of
                             # the model's colourless fibres a blurred photo edge leaves round the disk (12, 19: L* 33 -> 26)
PUPIL_LOCK_TONE_MAX = 30.0   # the restored pupil is never lighter than this (the ceiling pupil_fill uses)

def _lock_lum(im):
    im = im if im.mode == "RGB" else im.convert("RGB")
    return _lum3(np.asarray(im.resize((PUPIL_LOCK_SIDE, PUPIL_LOCK_SIDE), Image.BOX)))[..., 0]

def _pupil_edges(rows, thr):
    """Each sector's pupil edge (iris radii) at brightness thr, from its radial medians; NaN where none."""
    e = np.full(len(rows), np.nan)
    for k, m in enumerate(rows):
        up = np.nan_to_num(m, nan=-1.0) > thr
        hit = np.nonzero(up[:-1] & up[1:])[0]
        if not len(hit):
            continue
        i = int(hit[0]); r = (i + 0.5) * 0.02
        if i > 0 and m[i - 1] == m[i - 1] and m[i] > m[i - 1]:
            r = (i - 0.5 + (thr - m[i - 1]) / (m[i] - m[i - 1])) * 0.02    # between this bin's centre and the last
        e[k] = r
    return e

def _pupil_fit(e):
    """Circle through the sector edges e, refitted without the sectors a lash, a lid or a glint moved:
    (cx, cy, rho, sectors kept, median distance of all the edges from it) or None."""
    ns = len(e); ok = e == e
    if ok.sum() < ns // 2:
        return None
    t = ((np.arange(ns) + 0.5) / ns * 2 * math.pi - math.pi)[ok]
    p = np.c_[e[ok] * np.cos(t), e[ok] * np.sin(t)]; keep = np.ones(len(p), bool)
    for _ in range(4):
        q = p[keep]
        sol = np.linalg.lstsq(np.c_[2 * q, np.ones(len(q))], (q ** 2).sum(1), rcond=None)[0]
        cx, cy = float(sol[0]), float(sol[1]); rho = math.sqrt(max(float(sol[2]) + cx * cx + cy * cy, 1e-9))
        res = np.abs(np.hypot(p[:, 0] - cx, p[:, 1] - cy) - rho)
        keep = res <= max(0.03, 2.5 * float(np.median(res[keep])))
        if keep.sum() < ns // 2:
            return None
    return cx, cy, rho, int(keep.sum()), float(np.median(res))

def pupil_circle(lum, r_frac=None):
    """(cx, cy, rho, edge) of the dark pupil of a square iris image (or its _lock_lum luminance), in iris radii from
    the frame centre, or None when there is no dark centre with a clear, round edge. Unlike pupil_radius() it reads
    out to 0.94 of the iris, so a wide pupil with a thin ring is measured too, and it finds an off-centre pupil (30:
    0.12 right, 0.10 up). rho: where each sector's median brightness climbs PUPIL_LOCK_EDGE of the way from the
    pupil core to the iris; edge: the same circle at PUPIL_LOCK_TRUE. When the rho edges do not make one circle
    (PUPIL_LOCK_FIT), the edges at PUPIL_LOCK_EDGE_HI are tried, which a reflection inside the pupil does not
    reach, and that circle steps back in by the usual distance between the levels; if they do not make one circle
    either, None: a lid shadow is not a pupil."""
    if isinstance(lum, Image.Image):
        lum = _lock_lum(lum)
    r_frac = r_frac or iris_radius_frac()
    n = lum.shape[0]
    ax = (np.arange(n) - n / 2 + 0.5) / (r_frac * n)
    rr = np.sqrt(ax[None, :] ** 2 + ax[:, None] ** 2)
    ins = rr < 0.94
    v, b = lum[ins], (rr[ins] / 0.02).astype(np.int32)
    s = ((np.arctan2(ax[:, None], ax[None, :])[ins] + math.pi) / (2 * math.pi) * PUPIL_LOCK_SECTORS).astype(np.int32)
    s %= PUPIL_LOCK_SECTORS
    nb, ns = 47, PUPIL_LOCK_SECTORS
    o = np.argsort(b, kind="stable"); bs, vs = b[o], v[o]
    cut = np.searchsorted(bs, np.arange(nb + 1))
    med = np.array([np.median(vs[cut[i]:cut[i + 1]]) if cut[i + 1] - cut[i] > 12 else np.nan for i in range(nb)])
    near = rr[ins] < 0.25
    if not near.any() or np.isnan(med[10:]).all():
        return None
    core, iris = float(np.percentile(v[near], 10)), float(np.nanpercentile(med[10:], 90))
    if core > 45.0 or iris - core < PUPIL_LOCK_CONTRAST:
        return None
    o = np.argsort(s * nb + b, kind="stable"); ks, vs = (s * nb + b)[o], v[o]
    cut = np.searchsorted(ks, np.arange(ns * nb + 1))
    rows = [np.array([np.median(vs[cut[k * nb + i]:cut[k * nb + i + 1]]) if cut[k * nb + i + 1] - cut[k * nb + i] >= 3
                      else np.nan for i in range(nb)]) for k in range(ns)]
    e = _pupil_edges(rows, core + PUPIL_LOCK_EDGE * (iris - core))
    et = _pupil_edges(rows, core + PUPIL_LOCK_TRUE * (iris - core))
    fit = _pupil_fit(e)
    if fit is None or fit[4] > PUPIL_LOCK_FIT:
        e2 = _pupil_edges(rows, core + PUPIL_LOCK_EDGE_HI * (iris - core))
        f2, gap = _pupil_fit(e2), e2 - e
        if f2 is None or f2[4] > PUPIL_LOCK_FIT or f2[3] < 3 * ns // 4 or (gap == gap).sum() < ns // 2:
            return None
        fit = (f2[0], f2[1], f2[2] - float(np.nanpercentile(gap, 25)))   # a reflection sector only widens the gap
        edge = f2[2] - float(np.nanpercentile(e2 - et, 25)) if ((e2 - et) == (e2 - et)).sum() >= ns // 2 else fit[2]
    else:
        edge = fit[2] + float(np.nanmedian(et - e)) if ((et - e) == (et - e)).sum() >= ns // 2 else fit[2]
    cx, cy, rho = fit[:3]
    if not 0.08 <= rho <= 0.95 or math.hypot(cx, cy) > 0.25:
        return None
    return cx, cy, rho, max(rho, min(edge, rho + 0.03))     # a slow climb is a dark inner iris, not the pupil

PUPIL_HAZE_GAIN = 3.0        # colour pupil map: a*b* distance from the pupil's colour, x this, as grey levels, so the
                             # contrast floor (PUPIL_LOCK_CONTRAST 25) asks for an iris 8.3 chroma units off the pupil

def pupil_circle_chroma(im, r_frac=None):
    """pupil_circle() read from colour instead of brightness, on a square iris image. A haze over the pupil (the sky or
    the room mirrored on the cornea: live 19 and wave-c 07, 08, 12, blue or teal) is as bright as the iris in a lid's
    shadow, so the brightness edges scatter and pupil_circle() finds none, but it is colourless or cool while the iris
    keeps its pigment's hue even in shadow (19: a* 0 and b* -5 in the haze, a* +13 in the shadowed iris above it,
    +27 below). The map is every pixel's (a*, b*) distance from the median colour of the frame centre (inside 0.25
    iris radii), x PUPIL_HAZE_GAIN. Small pupils, whose colour does not hold that centre, read None (06, 21, 29)."""
    r_frac = r_frac or iris_radius_frac()
    n = PUPIL_LOCK_SIDE
    lab = srgb_to_lab(np.asarray(im.convert("RGB").resize((n, n), Image.BOX)))
    ax = (np.arange(n) - n / 2 + 0.5) / (r_frac * n)
    c = np.sqrt(ax[None, :] ** 2 + ax[:, None] ** 2) < 0.25
    a0, b0 = float(np.median(lab[..., 1][c])), float(np.median(lab[..., 2][c]))
    return pupil_circle(np.clip(np.hypot(lab[..., 1] - a0, lab[..., 2] - b0) * PUPIL_HAZE_GAIN, 0, 255), r_frac)

def pupil_lock(out, src, r_frac=None):
    """Keep the photo's pupil in the model's render: the model may sculpt the iris, it may not paint iris where the
    photo shows the pupil. src is the image the model was given. Only when the render shows iris over more than
    PUPIL_LOCK_SHARE of the photo's pupil, all the way round it (PUPIL_LOCK_EVEN), and its own pupil is
    PUPIL_LOCK_TOL smaller and inside the photo's (PUPIL_LOCK_INSIDE), is that disk, out to the photo's true edge,
    taken back to the render's own pupil black (never lighter than PUPIL_LOCK_TONE_MAX) over a PUPIL_LOCK_FEATHER
    edge, with the PUPIL_LOCK_RUFF band outside it; pixels already darker keep their value. Any other render is
    returned as it came, the same object."""
    r_frac = r_frac or iris_radius_frac()
    ys = _lock_lum(src)
    photo = pupil_circle(ys, r_frac)
    if photo is None:
        return out
    cx, cy, rho, edge = photo
    y = _lock_lum(out)
    ax = (np.arange(PUPIL_LOCK_SIDE) - PUPIL_LOCK_SIDE / 2 + 0.5) / (r_frac * PUPIL_LOCK_SIDE)
    d = np.sqrt((ax[None, :] - cx) ** 2 + (ax[:, None] - cy) ** 2)
    disk = d < rho - PUPIL_LOCK_RIM
    ring = (d > rho + 0.05) & (np.sqrt(ax[None, :] ** 2 + ax[:, None] ** 2) < 0.90)
    if disk.sum() < 20 or ring.sum() < 50:
        return out
    lo = float(np.percentile(y[disk], 5))
    lit = y > lo + 0.5 * max(float(np.median(y[ring])) - lo, 20.0)
    painted = lit[disk]
    share = float(painted.mean())
    if share <= PUPIL_LOCK_SHARE:
        return out
    band, ns = (d > rho - PUPIL_LOCK_BAND) & (d < rho), PUPIL_LOCK_SECTORS
    sec = ((np.arctan2(ax[:, None] - cy, ax[None, :] - cx) + math.pi) / (2 * math.pi) * ns).astype(np.int32)[band] % ns
    even = float(np.min(np.bincount(sec, weights=lit[band].astype(np.float64), minlength=ns) / np.maximum(np.bincount(sec, minlength=ns), 1)))
    if even < PUPIL_LOCK_EVEN:
        return out
    own = pupil_circle(y, r_frac)
    if own is not None and (own[2] > rho - PUPIL_LOCK_TOL
                            or math.hypot(own[0] - cx, own[1] - cy) + own[2] > rho + PUPIL_LOCK_INSIDE):
        return out
    dark = y[disk][~painted]
    tone = min(float(np.median(dark)) if dark.size > 20 else lo, PUPIL_LOCK_TONE_MAX)
    pcore, pring = float(np.percentile(ys[disk], 10)), float(np.median(ys[ring]))
    S = out.size[0]; R = r_frac * S; w, wr = max(PUPIL_LOCK_FEATHER * R, 1.5), PUPIL_LOCK_RUFF * R
    x0, y0, ep = S / 2 + cx * R, S / 2 + cy * R, edge * R
    c0, r0 = max(0, int(x0 - ep - wr) - 1), max(0, int(y0 - ep - wr) - 1)
    c1, r1 = min(S, int(math.ceil(x0 + ep + wr)) + 2), min(S, int(math.ceil(y0 + ep + wr)) + 2)
    blk = np.array(out.convert("RGB").crop((c0, r0, c1, r1)))
    k = src.size[0] / S                    # the photo, sampled on the render's pixels (the 4096 master's is 1024)
    sp = np.asarray(src.convert("RGB").resize((c1 - c0, r1 - r0), Image.BILINEAR, box=(c0 * k, r0 * k, c1 * k, r1 * k)))
    dx2 = (np.arange(c0, c1) + 0.5 - x0) ** 2
    for a0, a1 in _row_chunks(r1 - r0, c1 - c0):
        dd = np.sqrt(dx2[None, :] + ((np.arange(r0 + a0, r0 + a1) + 0.5 - y0) ** 2)[:, None])
        a = 0.5 - 0.5 * np.cos(np.clip((ep + w / 2 - dd) / w, 0.0, 1.0) * math.pi)
        q = np.clip((_lum3(sp[a0:a1])[..., 0] - pcore) / max(pring - pcore, 1.0), 0.0, 1.0)   # the photo: 0 pupil, 1 iris
        a = np.maximum(a, (0.5 + 0.5 * np.cos(np.clip((dd - ep) / wr, 0.0, 1.0) * math.pi)) * (1.0 - q))
        f = blk[a0:a1].astype(np.float32)
        blk[a0:a1] = np.clip(f - a[..., None] * np.maximum(f - tone, 0.0) + 0.5, 0, 255).astype(np.uint8)
    res = out.convert("RGB")               # a copy: the render passed in is not changed
    res.paste(Image.fromarray(blk), (c0, r0))
    print("snapeyes pupil lock " + json.dumps({"photo": [round(cx, 3), round(cy, 3), round(rho, 3)], "edge": round(edge, 3),
                                               "painted_share": round(share, 3), "lowest_sector": round(even, 2), "tone": round(tone, 1),
                                               "render_rho": None if own is None else round(own[2], 3)}), flush=True)
    return res

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

CHROMA_LIFT_CAP = 2.5        # the photo's chroma is scaled by the model's local brightness lift, at most this much
CHROMA_LIFT_SIGMA = 6 / 1024  # low-pass for that lift, as a share of the side (6 px on a 1024 render)
CHROMA_DARK = (50.0, 90.0)    # photo luma (low-passed) where the scaling applies fully / not at all: darkness
                              # compresses a photo's chroma, a normally lit photo already has its true colour
REFL_BLUE = (4.0, 10.0)       # Cb/Cr units towards blue-cyan beyond the radial median: none below, full above
REFL_LIFT = (6.0, 20.0)       # luma above the radial median: a reflection always adds light
REFL_IRIS_BLUE = (-2.0, 4.0)  # the iris's own blue-cyan lean: full correction at or below the first, none above the second
# The rest of a reflection on the lid-shaded top (_shaded_reflection). Each pair: none at or below, full at or above.
REFL_SHADE = (0.0, 6.0)          # the pixel's own blue-cyan lean, (Cb - Cr) / sqrt 2
REFL_SHADE_LIGHT = (-2.0, 0.0)   # the lit core's lean minus the pixel's: a veil is never bluer than the light it comes from
REFL_SHADE_TOP = (0.0, 0.5)      # cosine of the pixel's angle from 12 o'clock: none at 3 and 9 o'clock, full from 10 to 2
REFL_SHADE_RR = (0.40, 0.48)     # its radius: a rendered pupil larger than the photo's stays out (test photo 13)
REFL_SHADE_DARK = (-10.0, -4.0)  # its luma against the median of its radius
REFL_SHADE_CORE = (0.65, 0.85)   # its luma as a share of the iris's median: the photo's pupil edge stays out
REFL_SHADE_IRIS = (-14.0, -8.0)  # the lean of the iris's warmer half: full at or below the first, none above the second
REFL_SHADE_SEED = 24.0           # the lit core: a patch (2% of the side) this much brighter than its radius, and bluer


def _radial_median(plane, rr, mask, edges):
    """Median of `plane` in each radial band (under `mask`), interpolated back onto every pixel."""
    cs, ms = [], []
    for a, b in zip(edges[:-1], edges[1:]):
        sel = mask & (rr >= a) & (rr < b)
        if sel.sum() > 30:
            cs.append((a + b) / 2); ms.append(float(np.median(plane[sel])))
    if len(cs) < 2:
        return np.full(plane.shape, float(np.median(plane[mask])) if mask.any() else 0.0, np.float32)
    return np.interp(rr, cs, ms).astype(np.float32)


def reflection_chroma(y, cb, cr, r_frac=None):
    """How much of each pixel's colour is a reflection of the room rather than the iris, 0..1.

    A window or the sky mirrored on the cornea adds light and pulls the colour towards blue-cyan (or towards
    neutral, which on a brown or green iris is the same direction). chroma_lock copied that colour into the
    artwork as blue and violet fibres (6 of 27 licensed test photos). Pigment is the opposite case: the yellow
    and amber patches of a light eye are also brighter than their surroundings, but they sit on the yellow-red
    side, so they are never touched. Judged against the median of the same radius, so an iris whose colour
    changes from the pupil outwards (a brown ring around a green iris) is not mistaken for a reflection."""
    S = y.shape[0]
    r_frac = r_frac or iris_radius_frac()
    yy, xx = np.ogrid[0:S, 0:S]
    rr = (np.sqrt((xx - S / 2 + 0.5) ** 2 + (yy - S / 2 + 0.5) ** 2) / (r_frac * S)).astype(np.float32)
    iris = (rr > 0.30) & (rr < 0.98)
    edges = np.arange(0.30, 1.00, 0.05)
    dcb = cb - _radial_median(cb, rr, iris, edges)
    dcr = cr - _radial_median(cr, rr, iris, edges)
    lift = y - _radial_median(y, rr, iris, edges)
    blue = (dcb - dcr) / np.sqrt(2.0)                 # projection on the blue-cyan direction (Cb up, Cr down)
    b0, b1 = REFL_BLUE; l0, l1 = REFL_LIFT
    # judged only inside 0.90 of the radius: beyond it lie the pale limbus and sclera, which the artwork trims
    tb = np.clip((blue - b0) / (b1 - b0), 0, 1) * ((rr > 0.30) & (rr < 0.90))
    lit = np.clip((lift - l0) / (l1 - l0), 0, 1)
    w = tb * np.maximum(lit, _shaded_reflection(y, cb, cr, rr, lift, tb))
    # On a blue or grey-blue iris a bluer, brighter patch is as likely its own light fibres as a reflection, and a
    # blue reflection does no harm there anyway. Measured along the same blue-cyan axis: 27 brown test eyes read
    # -47 to -2, the owner's blue-green eye in daylight +18, the site's sample eye +11. Full correction at -2 and
    # below, none from +4 up.
    core = (rr > 0.35) & (rr < 0.88)
    if core.any():
        iris_blue = float((np.median(cb[core]) - np.median(cr[core])) / np.sqrt(2.0))
        w = w * float(np.clip((REFL_IRIS_BLUE[1] - iris_blue) / (REFL_IRIS_BLUE[1] - REFL_IRIS_BLUE[0]), 0.0, 1.0))
    # a reflection is a soft patch, not a pixel: smooth the weight so fibres inside it are treated alike
    return np.clip(_blur_f(w.astype(np.float32), max(1.0, S * 0.006)) * 1.3, 0, 1), rr, iris, edges


def _shaded_reflection(y, cb, cr, rr, lift, tb, n=128):
    """The rest of a reflection that lies on the lid-shaded top of the iris, 0..1. Test photo 14: a lamp over the upper
    half kept 40% of it blue, because only its lit core is brighter than the median of its radius. The rest counts
    as the same reflection when it leans blue-cyan in absolute terms (on an iris that is warm on its warmer half), is
    no bluer than that lit core, and is connected to it through pixels that are the same. A blue sector of the iris
    itself (sectoral heterochromia) is left as before unless it touches a lit core at least as blue as it is. The
    patch-scale tests run on an n x n grid (a reflection is a patch, and it keeps the cost to a few hundredths of a s)."""
    S = y.shape[0]
    ramp = lambda v, a: np.clip((v - a[0]) / (a[1] - a[0]), 0, 1)
    lo = lambda a: _resize_plane(a, n, Image.BOX)
    def grid(m):                      # centred coordinates on an m x m grid: x to the right, y up
        yy, xx = np.ogrid[0:m, 0:m]
        return xx - m / 2 + 0.5, m / 2 - 0.5 - yy
    xl, yl = grid(n)
    top_lo = ramp(yl / np.maximum(np.hypot(xl, yl), 1e-6), REFL_SHADE_TOP)
    seed = (_blur_f(lo(lift), n * 0.02) > REFL_SHADE_SEED) & (_blur_f(lo(tb), n * 0.02) > 0.5) & (top_lo > 0)
    core = lo(((rr > 0.35) & (rr < 0.88)).astype(np.float32)) > 0.5
    if not (core.any() and seed.any()):
        return np.zeros_like(y)
    lean = (cb - cr) / np.sqrt(2.0)
    lean_lo = lo(lean)
    sec = (np.floor(np.arctan2(xl, yl) / (np.pi / 6)) % 12).astype(np.int8)
    med = sorted(float(np.median(lean_lo[core & (sec == k)])) for k in range(12) if (core & (sec == k)).any())
    warm = float(np.median(med[:max(1, len(med) // 2)]))   # the warmer half of 12 sectors: a reflection may cover the rest
    gate = float(np.clip((REFL_SHADE_IRIS[1] - warm) / (REFL_SHADE_IRIS[1] - REFL_SHADE_IRIS[0]), 0.0, 1.0))
    if gate <= 0.0:
        return np.zeros_like(y)
    light = float(np.median(lean_lo[seed]))                # the lit core shows the light's own colour best
    x, yup = grid(S)
    top = ramp(yup / np.maximum(np.hypot(x, yup), 1e-6), REFL_SHADE_TOP)
    own = ramp(lean, REFL_SHADE) * ramp(light - lean, REFL_SHADE_LIGHT) * ramp(rr, REFL_SHADE_RR) * top
    ok = lo(tb * own) > 0.5
    g = seed & ok
    for _ in range(4 * n):            # grow the lit cores through the connected pixels that may be their veil
        h = _grow_mask(g, 3) & ok
        if (h == g).all():
            break
        g = h
    joined = np.clip(_resize_plane(g.astype(np.float32), S, Image.BILINEAR), 0, 1)
    core_y = max(1.0, float(np.median(lo(y)[core])))
    return own * joined * gate * ramp(lift, REFL_SHADE_DARK) * ramp(y / core_y, REFL_SHADE_CORE)


CHROMA_STATS_SIDE = 1024     # the colour correction maps are computed at most at this size, then stretched


def _chroma_maps(Y, Ys, CB, CR, r_frac=None):
    """(reflection weight or None, iris Cb and Cr of each radius or None, chroma gain), all at the planes' size."""
    w, rr, iris, edges = reflection_chroma(Ys, CB, CR, r_frac)
    if float(w.max()) > 0.01:
        keep = iris & (w < 0.05)
        mcb, mcr = _radial_median(CB, rr, keep, edges), _radial_median(CR, rr, keep, edges)
    else:
        w = mcb = mcr = None
    sig = max(1.0, Y.shape[0] * CHROMA_LIFT_SIGMA)
    Ys_lo = _blur_f(Ys, sig)
    k = np.clip((_blur_f(Y, sig) + 4.0) / (Ys_lo + 4.0), 1.0, CHROMA_LIFT_CAP)
    # only where the photo itself is dark: a well-lit photo already carries its true colour, and scaling it by the
    # model's brightening over-saturated the owner's own eye (ring C 13.6 -> 21.8 against about 17 in his sharp shot)
    d0, d1 = CHROMA_DARK
    k = 1.0 + (k - 1.0) * np.clip((d1 - Ys_lo) / max(d1 - d0, 1e-3), 0.0, 1.0)
    return w, mcb, mcr, k.astype(np.float32)


def chroma_lock(ai, src, blur=1.6, amount=1.0, r_frac=None):
    """Keep the structure the model restored, put the client's real colour back.

    The model may move luminance, because that is where the fibres live. It may not move colour, because colour
    is the one thing the client can check against a mirror. Measured on a weak photo the model drifted Cb by
    -10 and Cr by +7 and desaturated by 30%; after this lock the drift is under one unit. The chroma planes are
    blurred slightly so a sub-pixel drift in the model's output cannot show up as colour fringing.

    Two corrections on top (owner decision 2026-09-23, after the 30-photo licensed test set):
    - where the model lifted the brightness, the photo's chroma is scaled by the same local lift (only up, capped),
      because a dark brown iris kept at its dim photo's absolute chroma but rendered brighter reads grey
      (a test eye went from 1.3% to 48.7% colourless ring; with the scaling 9.7%, lightness unchanged);
    - colour that a reflection of the room put on the cornea is replaced by the iris colour of the same radius."""
    if src.size != ai.size:
        src = src.resize(ai.size, Image.LANCZOS)
    y, cb_ai, cr_ai = ai.convert("YCbCr").split()
    ys, cb, cr = src.convert("YCbCr").split()
    if blur:
        cb = cb.filter(ImageFilter.GaussianBlur(blur))
        cr = cr.filter(ImageFilter.GaussianBlur(blur))
    # The correction maps are smooth by construction (blurred weights, radial medians, a low-passed lift), so on a
    # 4096 master they are worked out on a 1024 copy and stretched back: 8.5 s and 1.1 GB became a fraction of that,
    # and a 1024 preview is computed exactly as before.
    f32 = lambda im: np.asarray(im).astype(np.float32)
    if ai.size[0] > CHROMA_STATS_SIDE:
        n = (CHROMA_STATS_SIDE, CHROMA_STATS_SIDE)
        sm = lambda im: f32(im.resize(n, Image.BILINEAR))
        maps = _chroma_maps(sm(y), sm(ys), sm(cb), sm(cr), r_frac)
        up = lambda a: None if a is None else np.asarray(Image.fromarray(a.astype(np.float32), mode="F").resize(ai.size, Image.BILINEAR), dtype=np.float32)
        w, mcb, mcr, k = (up(a) for a in maps)
    else:
        w, mcb, mcr, k = _chroma_maps(f32(y), f32(ys), f32(cb), f32(cr), r_frac)
    CB, CR = f32(cb), f32(cr)
    if w is not None:          # 1. reflections: the photo's colour there is the room's, so take the iris colour of that radius
        CB += (mcb - CB) * w
        CR += (mcr - CR) * w
    CB = 128.0 + (CB - 128.0) * k   # 2. the photo's colourfulness, kept where the model lifted a dark photo
    CR = 128.0 + (CR - 128.0) * k
    cb = Image.fromarray(np.clip(CB, 0, 255).astype(np.uint8))
    cr = Image.fromarray(np.clip(CR, 0, 255).astype(np.uint8))
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
