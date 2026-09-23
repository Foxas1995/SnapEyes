# -*- coding: utf-8 -*-
"""POST /api/analyze  {image: b64 (<=1600px), origWidth, origHeight, device: {...} (optional), study: {...} (optional)}
Finds the iris, refines the limbus circle, measures size and sharpness, returns the crop geometry for the client.
device / study: capture telemetry, cut down by telemetry() and written to the "snapeyes capture" log line only."""
import os, sys, re, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import BaseHTTPRequestHandler
import numpy as np
from PIL import Image
from _lib import iris as L

# ---- capture targets: ONE block. The verdict, the tips and the "targets" the capture screen shows all read
# these, so the numbers a customer is told can never disagree with the numbers that judge the photo.
MIN_DIAMETER_PX = 280        # iris diameter in the original photo: below this nothing is better than 'weak'
GOOD_DIAMETER_PX = 420       # the floor for 'good'. Only a floor: detail is judged by band-pass energy, never
                             # by pixel count, because an iPhone macro crops and upscales
# fibre_score lines (glare-masked band-pass, iris.fibre_measure), placed where the old fibre_detail lines
# fall on a blur sweep of the owner's Gemini studio renders resampled to capture sizes: of 72 points, those
# the old rule called weak score at most 4.55, those it did not call good at most 7.45. They are not what
# keeps the verdict from getting looser: the old rule itself does that (fibre_basis).
FIBRE_OK = 4.6               # needed for 'ok'
FIBRE_GOOD = 7.5             # and for 'good'
# the old rule's lines on fibre_detail (whole-ring high-pass, blind to glare, but it sees the finest fibres)
OLD_FIBRE_OK, OLD_FIBRE_GOOD = 2.2, 6.0
DETAIL_OK, DETAIL_GOOD = 40, 70    # the same two lines on the customer's 0-100 Detail scale
# fibre_basis -> Detail, piecewise linear and strictly rising, so Detail crosses DETAIL_OK / DETAIL_GOOD
# exactly where the verdict crosses FIBRE_OK / FIBRE_GOOD. 12.0 = a razor sharp capture (the stock sample
# eyes measure 11.1-11.4, the sharpest studio render 12.4) is 100; above it Detail stays 100.
DETAIL_CURVE = ((0.0, 0), (FIBRE_OK, DETAIL_OK), (FIBRE_GOOD, DETAIL_GOOD), (12.0, 100))
# share of the fibre ring hidden by the reflections the vision model reported (iris.reflection_core, the
# reflection itself without the inpainting halo; 0 without a vision box). The site's sample eye, sharp with
# one window reflection, reads 3.3% (2.8-4.7% from -2/3 to +1 EV) and the same at every iris size; the amber
# sample, a larger window, reads 6.6% (4.8-8.5%). A window painted over 2 / 6 / 12% of the iris area of a
# reflection-free photo reads 2.2 / 6.3 / 13.3%.
GLARE_OK_PCT = 5.0           # above this the verdict is capped at 'ok'
GLARE_WEAK_PCT = 12.0        # above this at 'weak': about an eighth of the fibres would be invented
OCCL_GOOD_PCT, OCCL_OK_PCT = 25, 40   # eyelid cover the vision model reports, for 'good' and 'ok'
# lamp cast, read from the white of the eye beside the iris (CIELAB of the sclera, iris.sclera_tint). A healthy
# sclera is a slightly warm white; a red one is the eye itself (irritation), so red never counts as the light.
LAMP_WARM_B = 24.0           # b* above this: a warm lamp
LAMP_COOL_AB = -15.0         # a* + b* below this: a cold or cyan light (a sclera is never blue-green by itself)
LAMP_MESSAGE = "Lamp light is tinting your eye colour. Daylight from a window gives truer colour."
MAX_SHOTS = 5                # how many frames the capture screen collects before it picks the best
TARGETS = {"detail_good": DETAIL_GOOD, "detail_ok": DETAIL_OK, "min_diameter_px": MIN_DIAMETER_PX,
           "good_diameter_px": GOOD_DIAMETER_PX, "max_shots": MAX_SHOTS}

def old_rule_cap(fibre):
    """fibre_detail on the fibre_score scale: OLD_FIBRE_OK lands on FIBRE_OK and OLD_FIBRE_GOOD on FIBRE_GOOD,
    straight lines between and above them, through 0 below. Held strictly under a line wherever the old
    value was under it, so float rounding can never carry a photo past a line the old rule refused."""
    slope = (FIBRE_GOOD - FIBRE_OK) / (OLD_FIBRE_GOOD - OLD_FIBRE_OK)
    if fibre >= OLD_FIBRE_GOOD: return FIBRE_GOOD + (fibre - OLD_FIBRE_GOOD) * slope
    if fibre >= OLD_FIBRE_OK: return min(FIBRE_OK + (fibre - OLD_FIBRE_OK) * slope, float(np.nextafter(FIBRE_GOOD, 0)))
    return min(max(fibre, 0.0) * FIBRE_OK / OLD_FIBRE_OK, float(np.nextafter(FIBRE_OK, 0)))

def fibre_basis(fscore, fibre):
    """The number the verdict, the tips and Detail read: the glare-masked band-pass score, capped by the old
    rule. The band-pass alone is blind to the finest fibres: a x4 digital zoom of a stock eye read 8.52 and a
    blurred frame run through an unsharp mask 10.77, against 10.79 for the clean eye, while fibre_detail saw
    the loss (4.87 and 5.82 against 10.52). A glint or sensor noise lifts fibre_detail, and the min() ignores
    a lift, so a reflection still cannot carry a soft photo, and no verdict is looser than the old rule by
    construction."""
    return min(fscore, old_rule_cap(fibre))

def detail_score(basis):
    """Customer-facing 0-100 Detail. Floored, so a photo just short of a line never shows the line's number."""
    xs, ys = zip(*DETAIL_CURVE)
    return int(math.floor(float(np.interp(basis, xs, ys))))

def verdict_for(locked, diam, fscore, fibre, glare_pct, occl):
    """Detail decides; the lock, the size and the eyelids are floors, and a reflection over the fibres is a cap.
    Takes both fibre measures and applies the old-rule cap itself, so no caller can judge on the band-pass alone."""
    basis = fibre_basis(fscore, fibre)
    if not locked: return "weak"
    if diam >= GOOD_DIAMETER_PX and basis >= FIBRE_GOOD and occl <= OCCL_GOOD_PCT: v = "good"
    elif diam >= MIN_DIAMETER_PX and basis >= FIBRE_OK and occl <= OCCL_OK_PCT: v = "ok"
    else: v = "weak"
    if glare_pct > GLARE_WEAK_PCT: return "weak"
    if glare_pct > GLARE_OK_PCT and v == "good": return "ok"
    return v

def lamp_cast(tint):
    """True when the sclera shows a strong warm, cold or cyan cast. No sclera visible = no claim."""
    return bool(tint) and (tint["b"] > LAMP_WARM_B or tint["a"] + tint["b"] < LAMP_COOL_AB)

# ---- optional capture telemetry: the "device" (camera facts) and "study" (capture-study arm) objects the capture
# screen sends. They are only written to the "snapeyes capture" log line: never stored, never sent back. Whatever
# arrives is cut down to plain values first, because a log line is no place for a stranger's payload.
TELEMETRY_KEYS = 24          # fields kept per object (and per nested object)
TELEMETRY_TEXT = 80          # characters kept per text value (an EXIF lens name is ~50)...
TELEMETRY_UA = 300           # ...except device.ua, which the capture screen already cuts to 300: the browser
                             # name (Safari, CriOS, Chrome) sits near the end of a user agent
TELEMETRY_LIST = 8           # items kept per list (zoom range, resolutions)
TELEMETRY_JSON = 1500        # an object still longer than this once cut down is replaced by {"dropped": "too_large"}
TELEMETRY_KEY = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,31}$")

def _tvalue(v, depth, text=TELEMETRY_TEXT):
    if v is None or isinstance(v, bool):
        return v
    if isinstance(v, int):
        return v if abs(v) <= 10 ** 9 else None
    if isinstance(v, float):
        return round(v, 4) if math.isfinite(v) and abs(v) <= 1e9 else None
    if isinstance(v, str):
        return "".join(c for c in v[:text * 2] if c.isprintable())[:text]
    if isinstance(v, list):   # plain values only; an object or list inside a list is dropped
        return [_tvalue(x, depth + 1) for x in v[:TELEMETRY_LIST] if x is None or isinstance(x, (bool, int, float, str))]
    if isinstance(v, dict) and depth < 1:
        return telemetry(v, depth + 1)
    return None

def telemetry(v, depth=0):
    """A plain, bounded copy of a telemetry object (one level of nesting), or None when it is not an object.
    The capture screen sends device = {ua, w, h, source} and study = {session, eye, shot, photos, source, light,
    comfort}; any other plain field passes the same way, so the screen can add one without a server change."""
    if not isinstance(v, dict):
        return None
    out = {}
    for k, x in list(v.items())[:TELEMETRY_KEYS * 4]:
        if len(out) >= TELEMETRY_KEYS:
            break
        if isinstance(k, str) and TELEMETRY_KEY.fullmatch(k):
            out[k] = _tvalue(x, depth, TELEMETRY_UA if (k == "ua" and depth == 0) else TELEMETRY_TEXT)
    if depth == 0 and len(json.dumps(out)) > TELEMETRY_JSON:
        return {"dropped": "too_large"}
    return out

def analyze(body):
    device, study = telemetry(body.get("device")), telemetry(body.get("study"))
    im = L.b64_to_pil(body["image"])
    W, H = im.size
    ow, oh = int(body.get("origWidth") or W), int(body.get("origHeight") or H)
    scale = ow / float(W)
    v = L.gemini_json(L.VISION_MODEL, L.PROMPT_VISION, im)
    if not v or v.get("found") is False or "iris_box" not in v:
        return {"ok": False, "reason": "no_eye", "targets": TARGETS,
                "message": "We could not find an eye in this photo. Fill the frame with one open eye and try again."}
    box = v.get("iris_box")
    ok_box = (isinstance(box, (list, tuple)) and len(box) == 4
              and all(isinstance(c, (int, float)) and c == c and abs(c) < 1e6 for c in box)
              and box[2] > box[0] and box[3] > box[1])
    if not ok_box:
        return {"ok": False, "reason": "no_eye", "targets": TARGETS,
                "message": "We could not find an eye in this photo. Fill the frame with one open eye and try again."}
    x1, y1, x2, y2 = box
    bx = [x1 * W / 1000, y1 * H / 1000, x2 * W / 1000, y2 * H / 1000]
    cx, cy = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
    r0 = ((bx[2] - bx[0]) + (bx[3] - bx[1])) / 4
    # the pupil is the one landmark a model gets right in a tight close-up: the iris is concentric with it,
    # so centring on the pupil survives an iris box that drifted onto the eyelid or the sclera
    pbox = v.get("pupil_box")
    pupil_px = None
    if (isinstance(pbox, (list, tuple)) and len(pbox) == 4
            and all(isinstance(c, (int, float)) and c == c for c in pbox)
            and pbox[2] > pbox[0] and pbox[3] > pbox[1]):
        px = ((pbox[0] + pbox[2]) / 2) * W / 1000
        py = ((pbox[1] + pbox[3]) / 2) * H / 1000
        prr = ((pbox[2] - pbox[0]) * W / 1000 + (pbox[3] - pbox[1]) * H / 1000) / 4
        # only trust it when it is plausibly a pupil inside this iris
        if prr < r0 * 0.75 and ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5 < r0 * 1.1:
            cx, cy, pupil_px = px, py, prr
    # refine on a working copy where the iris radius is ~120px
    f = min(1.0, 120.0 / max(r0, 1))
    g = L.to_gray(im.resize((max(8, int(W * f)), max(8, int(H * f))), Image.LANCZOS))
    rcx, rcy, rr = L.refine_circle(g, cx * f, cy * f, r0 * f)
    cx, cy, r = rcx / f, rcy / f, rr / f
    # sanity: a real iris is darker in the middle (pupil) than in its own ring. If it is not, the circle
    # landed on skin, sclera or an eyelid, and everything downstream would be built on a wrong crop.
    locked = L.iris_lock_ok(g, rcx, rcy, rr)
    crop = L.circular_crop(im, cx, cy, r)
    sharp = L.laplacian_var(crop)
    pad = 1.12; Sc = 2 * r * pad; ox, oy = cx - Sc / 2, cy - Sc / 2
    boxes = []
    for b in (v.get("glare_boxes") or []):
        try:
            gx1, gy1, gx2, gy2 = b
            bb = [(gx1 * W / 1000 - ox) / Sc, (gy1 * H / 1000 - oy) / Sc, (gx2 * W / 1000 - ox) / Sc, (gy2 * H / 1000 - oy) / Sc]
            # these now also feed the glare mask, where a NaN would raise; they were never valid JSON for the client either.
            # A box that misses the crop square (a glint on the sclera, the skin, the other eye) hides no fibre.
            if (all(math.isfinite(c) for c in bb) and bb[2] > bb[0] and bb[3] > bb[1]
                    and bb[2] > 0 and bb[3] > 0 and bb[0] < 1 and bb[1] < 1):
                boxes.append(bb)
        except Exception:
            pass
    # the whole-ring high-pass energy, blind to glare but the one measure that sees the finest fibres. The
    # owner's four real photos read 0.98-1.66 here (the 4.11 once quoted was a crop that had landed on the eyelid).
    fibre = L.fibre_detail(crop)
    # the fibre band with the reflections cut out, median over eight sectors, so a crisp glint cannot lift a
    # soft photo and the verdict does not hang on the pixel count; capped by the old rule (fibre_basis)
    fscore, glare_fib = L.fibre_measure(crop, boxes=[[c * crop.size[0] for c in b] for b in boxes])
    basis = fibre_basis(fscore, fibre)
    detail = detail_score(basis)
    diam_orig = 2 * r * scale
    occl = float(v.get("iris_occluded_by_eyelids_percent") or 0)
    label = str(v.get("sharpness") or "")
    verdict = verdict_for(locked, diam_orig, fscore, fibre, glare_fib, occl)
    glare_capped = verdict != verdict_for(locked, diam_orig, fscore, fibre, 0.0, occl)
    # the pupil, as a fraction of the square crop: a reflection landing here is rebuilt as darkness,
    # never handed to the image model
    pupil_r = None
    pb = v.get("pupil_box")
    if (isinstance(pb, (list, tuple)) and len(pb) == 4
            and all(isinstance(c, (int, float)) and c == c for c in pb) and pb[2] > pb[0] and pb[3] > pb[1]):
        pr = ((pb[2] - pb[0]) * W / 1000 + (pb[3] - pb[1]) * H / 1000) / 4
        pupil_r = max(0.04, min(0.34, pr / Sc))
    tips = []
    if diam_orig < GOOD_DIAMETER_PX:
        tips.append(f"Move closer or use 2x zoom: the iris is {int(diam_orig)} px, we want {GOOD_DIAMETER_PX} px or more.")
    if basis < FIBRE_GOOD: tips.append("The fibres are not resolved yet. Tap the iris on screen so it locks focus, "
                                       "hold the phone against something steady, and shoot again.")
    if occl > OCCL_GOOD_PCT: tips.append("Open the eye wide (lift the eyelid with a finger) so the whole iris is visible.")
    # a reflection sitting on the pupil hides nothing recoverable: say so instead of pretending to restore it
    on_pupil = False
    if pupil_r and v.get("glare_boxes"):
        pcx, pcy = (pb[0] + pb[2]) / 2, (pb[1] + pb[3]) / 2
        prad = max(pb[2] - pb[0], pb[3] - pb[1]) / 2
        for gb in v["glare_boxes"]:
            try:
                gcx, gcy = (gb[0] + gb[2]) / 2, (gb[1] + gb[3]) / 2
                if ((gcx - pcx) ** 2 + (gcy - pcy) ** 2) ** 0.5 < prad: on_pupil = True
            except Exception: pass
    if on_pupil:
        tips.append("The reflection sits on your pupil. Tilt your head or move the light to the side, or we will "
                    "have to rebuild the pupil as plain darkness.")
    elif v.get("glare_boxes"): tips.append("A reflection was found; we will remove it automatically.")
    if glare_fib > GLARE_OK_PCT:
        tips.append("A reflection covers part of the iris fibres, and what it hides has to be rebuilt. Turn so the "
                    "window or lamp is off to one side rather than straight in front of you.")
    if label != "sharp" or basis < FIBRE_GOOD:
        tips.append("This came out soft. Use the back camera at 2x, tap the iris to focus, and keep the phone "
                    "steady; front cameras cannot focus at this distance at all.")
    if not locked:
        tips.insert(0, "We could not lock onto the round edge of your iris. Centre one eye in the frame with a "
                       "little space around it, and keep the eyelid out of the way.")
    # These say how much of the artwork will be the customer's own fibre detail. The product is a digital file,
    # so no word here may promise or imply a physical print.
    msg = {"good": "Great capture. Your own fibres are sharp enough to carry the full-size artwork.",
           "ok": "This will make a beautiful artwork. A closer or steadier shot would keep more of your own fibre detail.",
           "weak": "Small or soft, so more of the fine detail gets rebuilt. Closer and steadier gives a truer artwork."}[verdict]
    if glare_capped:
        msg = {"ok": "This will make a beautiful artwork. A shot without the reflection on your iris would keep more of your own fibre detail.",
               "weak": "A reflection covers too much of your iris, so the fibres under it would be rebuilt. Move the light to one side and shoot again."}[verdict]
    if not locked:
        msg = "We found an eye but could not lock onto the iris edge, so the crop would be off. Please take another photo."
    # the white of the eye shows the colour of the light: a strong cast here is on the iris too, and the
    # colour lock later keeps whatever colour the photo has. Only judged on a locked circle.
    tint = L.sclera_tint(im, cx, cy, r) if locked else None
    lamp = lamp_cast(tint)
    capture = {"verdict": verdict, "detail": detail, "fibre_score": round(fscore, 2),
               "fibre": round(fibre, 2), "basis": round(basis, 2), "glare_on_fibres_pct": round(glare_fib, 1), "diameter_px": int(diam_orig),
               "sclera_b": None if not tint else round(tint["b"], 1), "sclera_a": None if not tint else round(tint["a"], 1)}
    if device is not None: capture["device"] = device
    if study is not None: capture["study"] = study
    print("snapeyes capture " + json.dumps(capture), flush=True)
    # a short-lived signed ticket: the paid endpoints refuse work without one, so a bare scripted loop
    # has to come through this (cheap) endpoint first instead of hitting the image model directly.
    # No ticket for a circle that is not an iris: from a crop of eyelid skin the image model invented a
    # complete brown iris, which would then be sold as the customer's own eye.
    return {"ok": True, "ticket": L.mint_ticket("work") if locked else None, "pupil_r": pupil_r, "fibre": round(fibre, 2),
            "iris": {"cx": cx / W, "cy": cy / H, "r": r / W}, "pad": pad, "glare_boxes_crop": boxes,
            "quality": {"diameter_px": int(diam_orig), "sharpness": round(sharp, 1), "fibre": round(fibre, 2), "sharpness_label": label, "occlusion_pct": occl,
                        "glare": bool(v.get("glare_boxes")), "locked": bool(locked),
                        "detail": detail, "fibre_score": round(fscore, 2), "glare_on_fibres_pct": round(glare_fib, 1),
                        "pupil_reflection": bool(on_pupil), "lamp_cast": lamp, "lamp_message": LAMP_MESSAGE if lamp else None,
                        "verdict": verdict, "message": msg, "tips": tips},
            "targets": TARGETS,
            "preview": L.pil_to_b64(crop.resize((320, 320), Image.LANCZOS), "JPEG", 85)}

def handle(req): L.run(req, analyze)

class handler(BaseHTTPRequestHandler):
    def do_POST(self): handle(self)
