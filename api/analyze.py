# -*- coding: utf-8 -*-
"""POST /api/analyze  {image: b64 (<=1600px), origWidth, origHeight, device: {...} (optional), study: {...} (optional)}
Finds the iris, refines the limbus circle, measures size and sharpness, returns the crop geometry for the client.
A photo that shows too little of the customer's own iris pattern to restore it comes back with quality.blocked true,
a retake message and no work ticket, the same as a circle that did not lock. quality.block_reason says why:
"too_blurry", "too_dark" for a photo the vision model calls sharp of an iris too dark to show its pattern, or
"pupil_too_large" for a pupil so wide that too thin a ring of iris shows (pupil_blocked).
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
# Dark irises show their fibres faintly, and on the 30-photo brown test set the fix for a weak dark photo was more
# light, not focus: 8 of 24 weak brown photos had an iris ring median luma below this. Detail itself stays on the
# absolute measure (normalising it by brightness predicted the render's own-pattern survival worse: 0.46 vs 0.61).
DARK_IRIS_LUMA = 50
DARK_IRIS_TIP = ("Your iris is dark, so its fibres show faintly. Stand close to a bright window in daylight (not direct "
                 "sun), with the window off to one side, and shoot again: more light brings them out. A desk lamp or a "
                 "torch changes your eye colour.")
# The blur block. A photo that does not show enough of the customer's own iris pattern gets no work ticket and a
# retake request: from it the studio model invents an iris, which would be sold as the customer's own eye. Any one
# trigger blocks (blur_blocked); only a locked circle is judged. Lines 1-3 read how much fibre and crypt energy is
# left, which a phone's sharpening lifts, so they skip a photo whose fibres read 'ok' or better (basis >= FIBRE_OK,
# Detail 40+); lines 4 and 5 read how the pattern was smeared, which sharpening does not undo, and judge every photo.
# Calibrated first on 36 photos (the 30 test photos, the owner's 4, the 2 site samples) and 3,802 perturbed copies
# (wave-e/quality-gate rounds 2-4), then re-cut (wave-g/gatefix) on 8,273 copies run through this analyze() with the
# stored vision replies: the release verifier's attack sets (wave-g/verify-gate cases_*.json: straight shakes 3-12 %
# of the iris diameter at 8 angles, curved hand-shake paths, shakes with sensor noise and phone sharpening, Gaussian
# and defocus blur with fine and blotchy noise, sharpened blurs, exposure, re-sends, dark irises, irises off the frame,
# wide pupils, wrong pupil boxes, reflections and lashes), its hard grid on the owner's and the samples' photos, and a
# must-pass set of every ticketed photo under noise (fine, blotchy, chroma), sharpening, exposure, re-sends and the
# smallest shakes (gatefix/mk_pass.py). Ground truth is the verifier's survival: the normalised cross-correlation of a
# copy's crypt band (3.5-8 px) with the unperturbed photo's, i.e. how much of the photo's own pattern it still carries.
#  1. Detail < BLOCK_DETAIL: no fibre band left. The owner's softest photos read Detail 16-19, and a shake too small to
#     cost their pattern (215102 with a curved shake of spread 0.5 %: survival 0.98) takes them to 6-7, so the line is
#     6. With the other lines as they are, 8 would block 44 more must-pass copies (10 of the owner's and the samples')
#     to catch 7 more erased ones, and 7 would block 13 more (14 and 18 slightly shaken) to catch 3.
#  2. iris_pattern() < BLOCK_PATTERN: the crypt band (crypts, furrows: what a render has to follow) left once the
#     part that is only noise is taken out. Noise and grain also lift Detail (a grainy haze with no iris in it, 04,
#     reads Detail 23, above the owner's own soft photos, 16-25), so this measure subtracts the fibre band's energy
#     from the crypt band's: noise puts 0.4-0.9 of its fibre-band energy into the crypt band, a real iris 0.8-2.1
#     (PATTERN_NOISE, round2). Never more than PATTERN_NOISE_CAP of the crypt band's energy is taken out: a phone's
#     sharpening lifts the noise in the fibre band far more than in the crypt band (the owner's 215102 at 1 EV
#     darker with noise 3 and a 150 % unsharp mask: fibre band 3.16 against 1.32, crypt band 2.09 against 2.01), and
#     the uncapped subtraction then removed all of a sharp photo's crypts: that photo read 0.35 and was blocked, as
#     were 38 sharp test-photo copies (round4 summary4.py); capped, 5 remain, all of dark irises (ring luma 30-46)
#     1-1.5 EV darker, told 'too_dark'. The price is noisy blurs that the cap lets through: of the Gaussian and
#     defocus blurs inside the envelope 231 of 1,463 get a ticket instead of 158, 54 of the 73 more at noise 6 (the
#     envelope's top), where a blur and a sharpened sharp photo read the same and the gate falls back to no block.
#     It is read past the pupil's edge (the strongest edge in any eye, which carried a fully
#     blurred dilated pupil past the old line), with the reflections cut out as fibre_measure does, as the median of
#     16 sectors (a glint or a lid in a few of them cannot carry it), against the ring's brightness floored at
#     PATTERN_FLOOR: a darker photo only ever reads lower, where the old unfloored divisor let 1 EV of darkness carry
#     a blocked blur through. As they are, 04 (0.79), 12 (0.56, blur), 01 (1.01, an almost black iris), 10 (1.23,
#     washed out) and 24 (1.55, grain over no visible pattern) read under the line; the next photo up is the owner's
#     softest, 2.09, then 2.16-12.1; the owner's four read 2.09-2.92 (1.92 at the lowest, 1.5 EV darker) and the
#     site's samples 6.08 and 8.40. The line sits between 1.55 and 2.09.
#  2b. pattern < BLOCK_NOISY_PATTERN and its shape < BLOCK_NOISY_SHAPE: sensor noise lifts a blur over line 2 with a
#     crypt band that is Gaussian (excess kurtosis -0.17..0.07 on 8 of the 10 such blurs in round3 kurt_try.py), while
#     real crypts are sparse, strong blobs: the owner's four read 0.19-1.46 as they are. The shape line was 0.05, but
#     215120's fine radial fibres read 0.03-0.18 with noise 4 (round4 seeds.py) and -0.07..0.04 with a shake of
#     0.5-0.75 % (survival 0.91-0.97), so it is 0.0. The shape may reach BLOCK_NOISY_SHAPE_SOFT when the 7-10 px band has
#     lost its energy too (line 5's softness under NOISY_SOFT): must-pass copies with a band that Gaussian read 0.79
#     (14 shaken) and 0.91 (215120) at the lowest, 215102 reads 0.645 in the hard grid but its shape stays 0.34 and up,
#     and the noisy blurs this catches read 0.48-0.58. Live, the three noisy blurs
#     line 2b was added for read 1.76-1.81 / -0.13..-0.01 and were blocked, and the vision model called all three
#     'soft', so no label would have caught them.
#  3. The vision model calls the photo 'blurry' AND Detail < BLOCK_LABEL_DETAIL. The label alone is not a line:
#     it is a model's word that changes between calls on the same photo (04: 'blurry' 2 of 3, 10: 1 of 2, the owner's
#     215102: 'soft' 1 of 2), and one 'blurry' on an owner's photo would block it. With Detail under 10 as well it
#     cannot block the owner's photos (Detail 10 and up at -1..+1 EV, re-sent or not). The model never called the
#     owner's photos 'blurry': 16 live calls (8 as they are, 4 at 1 EV darker, 4 re-sent at q70) and 4 cached replies.
#  4. direction_fine < BLOCK_MOTION[0] or direction < BLOCK_MOTION[1]: hand-shake. Per 22.5-degree sector the structure
#     tensor of a band's gradient (mean gx^2, gy^2, gx*gy), divided by its trace so a lid edge or a glint in a few
#     sectors cannot dominate, averaged over the valid sectors; the smaller eigenvalue over the larger, for the 5-7 and
#     the 7-10 px band (MOTION_BANDS). The crypt band that the line used to read (at 0.30) is emptied along the shake by
#     a 3 % shake that keeps the pattern (survival 0.87-0.96): it blocked 47 such copies, the owner's 215106 among them.
#     The coarser bands keep a 3 % shake's energy and lose a 6 % one's. Unblurred copies read 0.40 (5-7 px, 11) and
#     0.47 (7-10 px, 17) at the lowest, the owner's hard grid 0.46 and 0.51 (215106). Judged at any Detail: a phone's
#     sharpening lifted shaken photos into Detail 40+, where 23 of 23 got a ticket. Read only on a ring at least
#     DIRECTION_MIN_RING wide (a pupil dilated past 0.62 of the iris leaves too thin a one: 23).
#  5. softness < BLOCK_SOFT: a blur of any shape. The 7-10 px band's gradient energy over the 14-20 px band's, per
#     sector, averaged. A blur takes the first down far more than the second, and sensor noise barely reaches either
#     (its energy per band falls with the band's size, an iris's does not), so it still reads through the noise that
#     lifts lines 1-3. The photos that get a ticket read 0.72 (the owner's 215102; 0.645 at the lowest in the hard
#     grid) and 0.94 and up as they are, the samples 4.0, the blurred 12 0.18. Only on a ring as wide as line 4 needs: on a thin ring the
#     pupil's and the limbus' edges carry the coarse band (215102 with a pupil box 20-30 % too large read 0.32-0.41).
# Lines 2-5 are read with the part of the crop outside the photo cut out, grown by FRAME_MARGIN: circular_crop fills it
# with black, and its straight edge through the iris read as pattern (blurred irises 30 % off the frame kept a ticket)
# and as one direction (sharp irises 30-40 % off the frame were blocked by line 4 before the cut).
# What no line here can do. A curved hand-shake path is a thin kernel that lays shifted copies of the pattern over each
# other: the bands keep most of their energy while the pattern is lost to the ghosting, so band ratios and anisotropy
# barely see it (erased copies of 30 that keep a ticket read softness 0.46-1.56, the owner's sharp photos 0.72-1.58). And the owner's
# photos are small irises (243-387 px as sent, upscaled 1.8-2.8x here): their pupil edges read as soft as a 1.1-1.6 %
# blur of the samples, so no line on how blurred a photo looks blocks every 1.5 % blur without blocking the owner.
# Where the two overlap the photo is let through, as before the gate existed.
# Results (gatefix/final_eval.py, the same 8,273 copies through the lines before this re-cut and through these):
# the owner's and the samples' hard grid 0 of 571 blocked (0 of 571 before); must-pass copies blocked 27 of 1,589
# (114 of 1,589), the owner's and the samples' 16 of 930 (38 of 930); copies with survival 0.9+ blocked 107 of 2,068
# (195 of 2,068). With a ticket: must-block copies (blur std 1.5 %+ of the iris) 681 of 4,583 (766 of 4,583), erased
# copies (survival under 0.45) 185 of 1,392 (196 of 1,392); curved shakes of 1.5 %+ 111 of 264 (121 of 264), with noise
# 58 of 118 (77 of 118); shakes with noise 4 56 of 232 (85 of 232); sharpened shakes at Detail 40+ 0 of 23 (23 of
# 23); irises off the frame (G) 22 of 284 (64 of 284). Worse, from copies at Detail 6-7 (under the old line 8) and
# straight shakes just over lines 4: straight 6-12 % shakes 45 of 929 (35 of 929), blurs re-sent or of dark irises (F,
# H) 42 of 419 (22 of 419), with a wrong pupil box (J) 26 of 348 (14 of 348), behind lashes and reflections (RL)
# 61 of 207 (49 of 207).
BLOCK_DETAIL = 6
BLOCK_LABEL_DETAIL = 10
BLOCK_PATTERN = 1.6
BLOCK_NOISY_PATTERN = 2.0    # 2b: under this pattern...
BLOCK_NOISY_SHAPE = 0.0      # ...a crypt band whose shape (excess kurtosis) is this Gaussian is noise, not crypts,
BLOCK_NOISY_SHAPE_SOFT = 0.1  # ...and this Gaussian when the 7-10 px band has also lost its energy (softness under
NOISY_SOFT = 0.6              # this): noise lifting a blur, not an iris whose own crypts are fine and faint
MOTION_BANDS = ((5.0, 7.0), (7.0, 10.0))   # 4: the two bands whose gradients' weakest over strongest direction...
BLOCK_MOTION = (0.24, 0.38)                 # ...is read: under either line, a hand-shake
SOFT_BANDS = ((7.0, 10.0), (14.0, 20.0))    # 5: gradient energy of the first band over the second's, per sector...
BLOCK_SOFT = 0.45                           # ...averaged: under this, a blur of any shape
DIRECTION_MIN_RING = 0.20    # 4 and 5 are read only on a ring at least this wide (share of the iris radius)
FRAME_MARGIN = 40            # px at 768: the part of the crop outside the photo, grown by this, is cut out of the ring
PATTERN_BAND = (3.5, 8.0)    # the crypt band: difference-of-Gaussians sigmas at the 768 working size
PATTERN_NOISE = 0.6          # share of the fibre band (iris.FIBRE_BAND) taken out of the crypt band as noise...
PATTERN_NOISE_CAP = 0.5      # ...but never more than this share of the crypt band's own energy
PATTERN_FLOOR = 60           # grey level the ring brightness is floored at
PATTERN_PUPIL_GAP = 0.10     # the ring starts this far (share of the iris radius) past the pupil's edge...
PATTERN_OUTER = 0.92         # ...and ends here (iris.FIBRE_RING)
PATTERN_SECTORS = 16
PATTERN_MIN_SECTORS = 8      # fewer sectors left after the reflections are cut out: no reading
BLOCK_MESSAGE = ("This photo is too blurry for us to restore your own iris, so we have not used it: the studio would "
                 "have to invent the pattern. Please retake it in daylight from a window off to one side, with the back "
                 "camera at 2x, tap the iris on screen to focus, and hold the phone steady.")
# The same block on a photo the vision model calls sharp, of a dark iris (DARK_IRIS_LUMA): 01 as it is (Laplacian
# 179.8, the owner's passing photos 31.6-80.7), 18 and 19 1-1.5 EV darker. Focus and a steady hand cannot help
# there; light can. The same light as the capture guide's (a window off to one side), only closer.
BLOCK_MESSAGE_DARK = ("Your iris is dark and there was too little light in this photo to see its own pattern, so we have "
                      "not used it: the studio would have to invent the pattern. Please retake it close to a bright "
                      "window in daylight, with the window off to one side (not direct sun, not a lamp or the flash), the "
                      "back camera at 2x, tap the iris on screen to focus, and hold the phone steady.")
BLOCK_MESSAGES = {"too_blurry": BLOCK_MESSAGE, "too_dark": BLOCK_MESSAGE_DARK}
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

_GAUSS = {}

def _gauss_matrix(sigma, n):
    """n x n matrix that blurs one image axis with a Gaussian of `sigma` px (reflected border, cut at 4 sigma), so
    m @ img @ m.T is the 2-D blur in float32. PIL's blur rounds to whole grey levels, and a blurred iris's whole
    crypt band is 0.3-0.6 grey levels. Built once per size and sigma (eight 2.4 MB matrices at 768)."""
    key = (sigma, n)
    if key not in _GAUSS:
        r = int(4 * sigma) + 1
        k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
        k /= k.sum()
        idx = np.arange(n)[:, None] + np.arange(-r, r + 1)[None, :]
        idx = np.where(idx < 0, -idx - 1, np.where(idx >= n, 2 * n - idx - 1, idx))
        m = np.zeros((n, n), np.float32)
        np.add.at(m, (np.repeat(np.arange(n), 2 * r + 1), idx.ravel()), np.tile(k, n).astype(np.float32))
        _GAUSS[key] = m
    return _GAUSS[key]

def iris_pattern(crop, pupil_r=None, boxes=None, size=768, frame=None):
    """(pattern, shape, direction, direction_fine, softness). pattern: how much of the iris's own coarse pattern
    (crypts, furrows) the photo shows once noise is taken out, x100 of the ring's brightness (floored at
    PATTERN_FLOOR). shape: the crypt band's excess kurtosis, ~0 when that band is Gaussian noise, higher for the
    sparse, strong blobs of real crypts. direction / direction_fine: the gradient energy of the 7-10 / 5-7 px band
    (MOTION_BANDS) along its weakest direction over its strongest (1 the same every way, near 0 smeared along one
    line: a hand-shake). softness: the 7-10 px band's gradient energy over the 14-20 px band's (SOFT_BANDS), per
    sector, averaged: a blur of any shape takes the first down with the second nearly whole. The last three are None
    on a ring narrower than DIRECTION_MIN_RING. All None when reflections leave fewer than PATTERN_MIN_SECTORS
    sectors to read. On the square crop at `size` px (so the reading does not depend on how large the iris was), in
    the ring from PATTERN_PUPIL_GAP past the pupil's edge to PATTERN_OUTER, with the reflections cut out (glare_mask
    grown as fibre_measure grows it) and so is the part of the crop outside the photo, grown by FRAME_MARGIN (its
    straight black edge would read as pattern and as one direction); per 22.5-degree sector the crypt band's std
    with PATTERN_NOISE of the fibre band's std taken out (in quadrature, at most PATTERN_NOISE_CAP of its energy),
    its kurtosis, and each motion band's gradient structure tensor divided by the tensor's trace; the median of the
    sectors for the first two, the mean for the tensors. pupil_r: pupil radius as a share of the crop side; boxes:
    vision glare boxes as shares of the crop side; frame: the photo's extent (x0, y0, x1, y1) as shares of the crop
    side, None when the crop lies inside it. About 0.3 s (0.32 s median on the owner's and the samples' crops, 0.28 s
    before lines 4 and 5), most of it the glare mask."""
    rf = L.iris_radius_frac()
    work = crop if crop.size == (size, size) else crop.resize((size, size), Image.LANCZOS)
    g = np.asarray(work.convert("L"), dtype=np.float32)
    blurred = {}
    sig = {L.FIBRE_BAND[0], PATTERN_BAND[0], PATTERN_BAND[1]} | {s for b in MOTION_BANDS + SOFT_BANDS for s in b}
    for s in sorted(sig):
        m = _gauss_matrix(s, size)
        blurred[s] = m @ g @ m.T
    crypt = blurred[PATTERN_BAND[0]] - blurred[PATTERN_BAND[1]]
    fibre = blurred[L.FIBRE_BAND[0]] - blurred[L.FIBRE_BAND[1]]   # FIBRE_BAND[1] is PATTERN_BAND[0]
    hard, _, _ = L.glare_mask(work, rf * size, [[c * size for c in b] for b in (boxes or [])])
    glare = L._grow_mask(hard > 0, L.FIBRE_GLARE_GROW)
    ax = np.arange(size) - size / 2 + 0.5
    d = np.sqrt(ax[None, :] ** 2 + ax[:, None] ** 2) / (rf * size)
    ang = (np.degrees(np.arctan2(ax[:, None], ax[None, :])) + 360.0) % 360.0
    pupil = (pupil_r or 0.0) * 2 * (1.0 / (2 * rf))       # pupil radius in iris radii
    inner = max(L.FIBRE_RING[0], pupil + PATTERN_PUPIL_GAP)
    ring = (d > inner) & (d < PATTERN_OUTER)
    off = np.zeros((size, size), bool)
    if frame is not None:
        px = np.arange(size) + 0.5
        x0, y0, x1, y1 = (c * size for c in frame)
        none = np.zeros(size, bool)
        cols = ((px < x0 + FRAME_MARGIN) if x0 > 0 else none) | ((px > x1 - FRAME_MARGIN) if x1 < size else none)
        rows = ((px < y0 + FRAME_MARGIN) if y0 > 0 else none) | ((px > y1 - FRAME_MARGIN) if y1 < size else none)
        off = rows[:, None] | cols[None, :]
    if not (ring & ~off).any():
        return None, None, None, None, None
    luma = float(np.median(g[ring & ~off]))
    sector = np.minimum((ang / (360.0 / PATTERN_SECTORS)).astype(np.int64), PATTERN_SECTORS - 1)
    keep = ring & ~glare & ~off
    total = np.bincount(sector[ring], minlength=PATTERN_SECTORS)
    si = sector[keep]
    n = np.bincount(si, minlength=PATTERN_SECTORS).astype(np.float64)

    def sector_std(band):
        v = band[keep].astype(np.float64)
        s1 = np.bincount(si, weights=v, minlength=PATTERN_SECTORS)
        s2 = np.bincount(si, weights=v * v, minlength=PATTERN_SECTORS)
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.sqrt(np.maximum(s2 / n - (s1 / n) ** 2, 0.0))
    sc, sf = sector_std(crypt), sector_std(fibre)
    valid = n >= np.maximum(250, 0.15 * total)
    if valid.sum() < PATTERN_MIN_SECTORS:
        return None, None, None, None, None
    noise = np.minimum((PATTERN_NOISE * sf[valid]) ** 2, PATTERN_NOISE_CAP * sc[valid] ** 2)
    excess = np.sqrt(np.maximum(sc[valid] ** 2 - noise, 0.0))
    # the crypt band's shape per sector: excess kurtosis from the central moments
    v = crypt[keep].astype(np.float64)
    with np.errstate(invalid="ignore", divide="ignore"):
        mu = np.bincount(si, weights=v, minlength=PATTERN_SECTORS) / n
        e2, e3, e4 = (np.bincount(si, weights=v ** p, minlength=PATTERN_SECTORS) / n for p in (2, 3, 4))
        m2 = e2 - mu ** 2
        m4 = e4 - 4 * mu * e3 + 6 * mu ** 2 * e2 - 3 * mu ** 4
        kurt = m4[valid] / np.maximum(m2[valid] ** 2, 1e-12) - 3.0
    direction = direction_fine = softness = None
    if PATTERN_OUTER - inner >= DIRECTION_MIN_RING:
        def tensor(band):
            gy, gx = np.gradient(band)
            with np.errstate(invalid="ignore", divide="ignore"):
                return [np.bincount(si, weights=w[keep].astype(np.float64), minlength=PATTERN_SECTORS)[valid] / n[valid]
                        for w in (gx * gx, gy * gy, gx * gy)]
        def weakest_over_strongest(t):
            tr = np.maximum(t[0] + t[1], 1e-12)
            a, b, c = float(np.mean(t[0] / tr)), float(np.mean(t[1] / tr)), float(np.mean(t[2] / tr))
            lo, hi = np.linalg.eigvalsh(np.array([[a, c], [c, b]]))
            return float(lo / hi) if hi > 0 else 1.0
        bands = {bd: blurred[bd[0]] - blurred[bd[1]] for bd in set(MOTION_BANDS + SOFT_BANDS)}
        tens = {bd: tensor(band) for bd, band in bands.items()}
        direction_fine, direction = (weakest_over_strongest(tens[bd]) for bd in MOTION_BANDS)
        num, den = (tens[bd][0] + tens[bd][1] for bd in SOFT_BANDS)
        softness = float(np.mean(num / np.maximum(den, 1e-12)))
    return (100.0 * float(np.median(excess)) / max(luma, PATTERN_FLOOR), float(np.median(kurt)), direction,
            direction_fine, softness)

def blur_blocked(locked, basis, detail, pattern, shape, label, direction=None, direction_fine=None, softness=None):
    """(blocked, trigger): True when the photo does not show enough of the customer's own iris to restore it (see
    BLOCK_DETAIL). Only a locked circle is judged (an unlocked one already gets no ticket). Lines 1-3 read how much
    fibre and crypt energy is left, so a photo whose fibres read 'ok' or better (Detail 40+) is not judged by them;
    lines 4 and 5 read how the pattern was smeared, which a phone's sharpening does not undo, so they judge every
    photo. trigger names the first line crossed, for the capture log and the reason."""
    if not locked:
        return False, None
    if basis < FIBRE_OK:
        if detail < BLOCK_DETAIL: return True, "detail"
        if pattern is not None and pattern < BLOCK_PATTERN: return True, "pattern"
        if pattern is not None and pattern < BLOCK_NOISY_PATTERN and (
                shape < BLOCK_NOISY_SHAPE
                or (shape < BLOCK_NOISY_SHAPE_SOFT and softness is not None and softness < NOISY_SOFT)): return True, "noise"
        if label == "blurry" and detail < BLOCK_LABEL_DETAIL: return True, "label"
    if ((direction_fine is not None and direction_fine < BLOCK_MOTION[0])
            or (direction is not None and direction < BLOCK_MOTION[1])): return True, "motion"
    if softness is not None and softness < BLOCK_SOFT: return True, "soft"
    return False, None

def block_reason(trigger, dark_iris, label):
    """Why a blocked photo is blocked, in the words the capture screen shows (quality.block_reason). 'too_dark' for a
    dark iris on a photo the vision model calls sharp, where more light is the fix and focus is not; a shaken or
    smeared photo (lines 4 and 5, which compare bands of the photo with each other, so light does not move them) is
    blurry whatever the iris; 'too_blurry' otherwise. The shake question (SHAKE_CONF) is blurry the same way."""
    if trigger not in ("motion", "soft", "shake") and dark_iris and label == "sharp":
        return "too_dark"
    return "too_blurry"

# ---- the shake question. A curved hand-shake path lays shifted copies of the pattern over each other, and the lines
# above cannot see it (see "What no line here can do"): of the curved shakes that erased the pattern (survival under
# 0.45, wave-g/gatefix final_eval.txt) 41 of 89 kept a ticket. So one more small call to the vision model asks only
# whether the camera moved, on a square around the iris SHAKE_PAD iris diameters wide (the lashes, lids and the
# reflection's outline show a shake best), and a confident yes blocks as 'too_blurry'. It is asked only of a locked
# photo that neither lines 1-5 nor the wide-pupil block (below) blocked and whose fibres read under 'ok' (Detail under
# 40): the 185 erased copies that keep a ticket in all the attack sets read Detail 6-32. Without an answer (an error,
# a busy model, a reply slower than SHAKE_TIMEOUT, one that cannot be read) nothing is blocked: the photo is judged
# as before.
# Calibration (wave-i/shake, 60 live calls, gemini-3.8-flash; this prompt is its "sep2"). How wide the square is sets
# how large a shake the model sees. At 1.5 diameters it said yes (75-92) to 4 of 5 copies with a 0.75-1 % shake that
# keep the pattern (survival 0.84-0.90): it would block photos the gate rightly lets through. At 2.5 it said no to
# all 4 copies with a 0.75 % shake (survival 0.89-0.93, confidence 4-8), the owner's 215120 with 1 % (0.87, 12) and
# 6 test photos as they are (05 09 16 18 21 29, 0-10), and yes to 5 of 9 erased curved shakes that keep a ticket
# today (06 13 26 27 sample_blue 2 %, 85-98); the other 4 it called defocus (sample_blue 1.5 % and 2 % with noise,
# sample_amber 2 %, 30 2.5 %: 10-15). A yes read 85-98 and a no 0-15, so the line is 80. Bars, live at 2.5: the
# owner's four photos as they are, 1 EV darker and lighter, re-sent at q70 and sharpened (unsharp 60 %): no, 12 of 12
# (0-10); the site's samples read Detail 78-100 on the same grid, so they are never asked (asked anyway: no, 6 of 6).
# The same question inside the analyze vision prompt (whole photo, 4 calls) caught 1 of the 2 erased copies it was
# shown, as the square did, but it would change the reply, and so the boxes, of every photo, and it cannot set how
# large the iris is in the model's view. The call takes 3.3 s median as shipped (2.5-7.4 s over 38 calls; 1 of all
# 78 calls took 15 s), only on the photos it is asked of.
SHAKE_PAD = 2.5              # side of the square sent, in iris diameters (the part outside the photo is black)
SHAKE_SIDE = 1024            # px: a larger square is scaled down to this, a smaller one is sent as it is
SHAKE_MAX_PIXELS = 16_000_000   # px: a larger square is cut from a reduced copy of the photo (shake_square)
SHAKE_CONF = 80              # a yes at this confidence or higher blocks
SHAKE_TIMEOUT = 12           # s
PROMPT_SHAKE = (
    "Close-up phone photo of one human eye, cropped around the iris. Decide whether this photo is spoiled by camera "
    "shake (the phone moved during the exposure). Look closely at the eyelashes, the pupil rim, the outer edge of the "
    "iris, the outline of any reflection and the fine iris fibres and crypts. Camera shake drags every edge the same "
    "way: edges are smeared into streaks or arcs, or show two or three faint offset copies (ghosting), and the fine "
    "fibres and crypts dissolve into streaks or a haze. In a close-up the lashes, lids and iris all sit at almost the "
    "same distance, so blur that covers all of them is not a shallow depth of field. A photo that is only "
    "low-resolution, noisy or compressed, whose edges are fine but pixel-soft and not dragged or doubled, is NOT "
    'camera shake. Return ONLY JSON: {"shake":true|false,"confidence":n,"blur":"none|slight|strong","evidence":"a few '
    'words"}. confidence (0-100) is how sure you are that camera shake is visible: 0 = certainly none, 100 = certainly '
    "shaken. blur is how blurred the iris texture is, whatever the cause."
)

def shake_square(im, cx, cy, r):
    """The image the shake question sees: the square SHAKE_PAD iris diameters wide around the circle (cx, cy, r in
    the photo's pixels), black outside the photo, scaled down to SHAKE_SIDE when wider. A square of more than
    SHAKE_MAX_PIXELS (an iris about 1600 px wide or more) is cut from a copy of the photo reduced by a whole factor
    first, so no photo can make it allocate a canvas many times its own size; the square sent then differs by a
    fraction of a grey level (0.04 on test photo 22, whose iris runs off its frame). None when it misses the photo."""
    S = 2 * r * SHAKE_PAD
    box = [int(round(c)) for c in (cx - S / 2, cy - S / 2, cx + S / 2, cy + S / 2)]
    k = max(1, math.ceil(math.sqrt(max(box[2] - box[0], 1) * max(box[3] - box[1], 1) / SHAKE_MAX_PIXELS)))
    if k > 1:
        im, box = im.reduce(k), [int(round(c / k)) for c in box]
    W, H = im.size
    if box[2] - box[0] < 8 or box[3] - box[1] < 8 or box[2] <= 0 or box[3] <= 0 or box[0] >= W or box[1] >= H:
        return None
    sq = im.crop(tuple(box))          # PIL fills the part outside the photo with black
    return sq.resize((SHAKE_SIDE, SHAKE_SIDE), Image.LANCZOS) if sq.size[0] > SHAKE_SIDE else sq

def shake_seen(im, cx, cy, r):
    """(yes, confidence) from the shake question, or None when the call fails, is too slow or its answer cannot be
    read: no answer never blocks. One call, no retry (a busy model is not waited for). Logged as 'snapeyes shake'."""
    import time
    t0, rec, res = time.time(), {}, None
    try:
        sq = shake_square(im, cx, cy, r)
        if sq is not None:
            parts = [{"text": PROMPT_SHAKE}, {"inlineData": {"mimeType": "image/jpeg", "data": L.pil_to_b64(sq, "JPEG", 90)}}]
            j = L.gemini(L.VISION_MODEL, parts, {"responseMimeType": "application/json", "temperature": 0},
                         timeout=SHAKE_TIMEOUT, retries=0)
            a = json.loads("".join(p.get("text", "") for p in j["candidates"][0]["content"]["parts"]))
            yes, conf = a.get("shake"), a.get("confidence")
            yes = yes is True or (isinstance(yes, str) and yes.strip().lower() == "true")
            if isinstance(conf, (int, float)) and not isinstance(conf, bool) and math.isfinite(conf):
                res = (yes, float(conf))
            rec = {"shake": yes, "confidence": conf if res else None,
                   "evidence": "".join(c for c in str(a.get("evidence") or "")[:160] if c.isprintable())[:80]}
    except Exception as e:  # noqa
        rec = {"error": L._scrub(repr(e))[:160]}
    rec["secs"] = round(time.time() - t0, 2)
    print("snapeyes shake " + json.dumps(rec), flush=True)
    return res

# ---- the wide-pupil block. A pupil this wide leaves too thin a ring of iris to make an artwork from, and the studio
# model then paints an iris into the pupil (test photo 23: pupil 0.74 of the iris radius; the render drew one of 0.35
# and filled the rest with invented fibres; /api/enhance now puts the photo's pupil back, which leaves a black disc
# inside a thin ring). The pupil is measured on this endpoint's own crop (iris.pupil_circle) and the vision model's
# pupil box has to agree, so one misread edge cannot block a photo on its own. On the 36 calibration photos (the 30
# test photos, the owner's 4, the 2 site samples) at 800-1600 px, 23 reads 0.735-0.738 (vision 0.76); the other
# photos with a readable, round pupil edge read 0.48 or less (the owner's four 0.29-0.48, the samples 0.30 and
# 0.31); the rest are not read (dark irises, glare, lid shadows) and pass. The vision box reaches 0.55 only on 23,
# 24 (0.61, not read) and the owner's 215102 (0.60, read 0.48). The line is a margin, not a measured limit of what
# is too thin: no render between 0.48 and 0.74 has been judged. Dim light widens a pupil, daylight narrows it.
PUPIL_BLOCK = 0.62           # measured pupil radius, in iris radii
PUPIL_BLOCK_VISION = 0.55    # the vision pupil box's radius, in iris radii
PUPIL_BLOCK_MESSAGE = ("Your pupil is very wide in this photo, so only a thin ring of your iris shows: too little to make "
                       "your artwork from. More light makes the pupil smaller: stand close to a bright window in daylight "
                       "(not direct sun) for a minute, then shoot again with the window off to one side. After dark, "
                       "switch on all the ceiling lights and wait a minute first. If drops at an eye exam widened your "
                       "pupils, wait until they wear off.")
BLOCK_MESSAGES["pupil_too_large"] = PUPIL_BLOCK_MESSAGE

def pupil_blocked(crop, pupil_r, pad, locked):
    """(blocked, pupil_size): True when the pupil fills so much of the iris that the artwork would have to invent
    the iris (see PUPIL_BLOCK). pupil_size is the pupil measured on the crop, in iris radii, None when its edge
    cannot be read; pupil_r is the vision pupil box as a share of the crop side. Only a locked circle is judged."""
    if not locked:
        return False, None
    pc = L.pupil_circle(crop, L.iris_radius_frac(pad))
    size = None if pc is None else round(pc[2], 3)
    return bool(size is not None and size >= PUPIL_BLOCK and pupil_r and pupil_r * 2 * pad >= PUPIL_BLOCK_VISION), size

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
    # The model is asked for [x1,y1,x2,y2] but sometimes answers in its native [y1,x1,y2,x2] order. On a
    # non-square photo that lands the circle on the eyelid or the skin: 10_Mybrownyes10 and 20_Auge (test set,
    # 2 of 30) and the owner's 215106 eyelid crop were all this, and a re-run of 20 swapped again. So both
    # readings are fitted and locked, which costs ~40 ms and no model call, and the locked one with the
    # stronger limbus wins (on 12 of 12 wrong circles the lock let through, the true circle had the larger step).
    pbox = v.get("pupil_box")
    pbox_ok = (isinstance(pbox, (list, tuple)) and len(pbox) == 4
               and all(isinstance(c, (int, float)) and c == c for c in pbox)
               and pbox[2] > pbox[0] and pbox[3] > pbox[1])
    best = None
    for swap in (False, True):
        sw = (lambda b: (b[1], b[0], b[3], b[2])) if swap else (lambda b: tuple(b))
        x1, y1, x2, y2 = sw(box)
        bx = [x1 * W / 1000, y1 * H / 1000, x2 * W / 1000, y2 * H / 1000]
        ccx, ccy = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
        r0 = ((bx[2] - bx[0]) + (bx[3] - bx[1])) / 4
        # the pupil is the one landmark a model gets right in a tight close-up: the iris is concentric with it,
        # so centring on the pupil survives an iris box that drifted onto the eyelid or the sclera
        if pbox_ok:
            p = sw(pbox)
            px, py = ((p[0] + p[2]) / 2) * W / 1000, ((p[1] + p[3]) / 2) * H / 1000
            prr = ((p[2] - p[0]) * W / 1000 + (p[3] - p[1]) * H / 1000) / 4
            # only trust it when it is plausibly a pupil inside this iris
            if prr < r0 * 0.75 and ((px - ccx) ** 2 + (py - ccy) ** 2) ** 0.5 < r0 * 1.1:
                ccx, ccy = px, py
        # refine on a working copy where the iris radius is ~120px
        f = min(1.0, 120.0 / max(r0, 1))
        g = L.to_gray(im.resize((max(8, int(W * f)), max(8, int(H * f))), Image.LANCZOS))
        rcx, rcy, rr = L.refine_circle(g, ccx * f, ccy * f, r0 * f)
        ok, step = L.iris_lock_score(g, rcx, rcy, rr)
        cand = (ok, step, swap, rcx / f, rcy / f, rr / f)
        if best is None or (ok and (not best[0] or step > best[1])): best = cand
    locked, _, swapped_boxes, cx, cy, r = best
    if swapped_boxes:   # everything below reads the vision boxes too; give it the reading that locked
        v = dict(v); v["glare_boxes"] = [[b[1], b[0], b[3], b[2]] for b in (v.get("glare_boxes") or [])
                                         if isinstance(b, (list, tuple)) and len(b) == 4]
        if pbox_ok: v["pupil_box"] = [pbox[1], pbox[0], pbox[3], pbox[2]]
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
    # too blurry to restore the customer's own iris: no ticket, and the capture screen asks for a retake. Read past
    # the pupil's edge, so the pupil is found first; skipped for an unlocked circle, which is never judged. Read for
    # a sharp photo too, which is never blocked, so the capture log shows where real photos fall.
    # the photo's extent on the crop (circular_crop's own square), so a frame edge running through the iris is cut out
    Sq = crop.size[0]; qx, qy = int(round(cx - Sq / 2)), int(round(cy - Sq / 2))
    frame = (-qx / Sq, -qy / Sq, (W - qx) / Sq, (H - qy) / Sq)
    frame = None if frame[0] <= 0 and frame[1] <= 0 and frame[2] >= 1 and frame[3] >= 1 else frame
    pattern, shape, direction, direction_fine, softness = (iris_pattern(crop, pupil_r, boxes, frame=frame) if locked
                                                           else (None, None, None, None, None))
    blocked, block_by = blur_blocked(locked, basis, detail, pattern, shape, label, direction, direction_fine, softness)
    # how dark the iris itself is (median of the fibre ring), to give a dark eye the advice that actually helps
    gs = L.to_gray(crop.resize((256, 256), Image.LANCZOS))
    gy, gx = np.ogrid[0:256, 0:256]
    gd = np.sqrt((gx - 127.5) ** 2 + (gy - 127.5) ** 2) / (L.iris_radius_frac() * 256)
    ring_luma = float(np.median(gs[(gd > 0.45) & (gd < 0.90)]))
    dark_iris = locked and ring_luma < DARK_IRIS_LUMA
    reason = block_reason(block_by, dark_iris, label) if blocked else None
    # a pupil too wide to leave a ring of iris: blocked the same way; a photo that is also too blurry says blurry first
    pupil_block, pupil_size = pupil_blocked(crop, pupil_r, pad, locked)
    if pupil_block and not blocked:
        blocked, block_by, reason = True, "pupil", "pupil_too_large"
    # a curved hand-shake no line sees: asked only of a locked photo nothing above blocked, under 'ok' (SHAKE_CONF)
    shake = shake_seen(im, cx, cy, r) if locked and not blocked and basis < FIBRE_OK else None
    if shake is not None and shake[0] and shake[1] >= SHAKE_CONF:
        blocked, block_by = True, "shake"
        reason = block_reason(block_by, dark_iris, label)
    tips = []
    if diam_orig < GOOD_DIAMETER_PX:
        tips.append(f"Move closer or use 2x zoom: the iris is {int(diam_orig)} px, we want {GOOD_DIAMETER_PX} px or more.")
    if basis < FIBRE_GOOD:
        tips.append(DARK_IRIS_TIP if dark_iris else
                    "The fibres are not resolved yet. Tap the iris on screen so it locks focus, "
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
    # a dark iris that the vision model still calls sharp needs light, not focus: its tip is already above
    if label != "sharp" or (basis < FIBRE_GOOD and not dark_iris):
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
    if blocked:
        msg = BLOCK_MESSAGES[reason]
    # the white of the eye shows the colour of the light: a strong cast here is on the iris too, and the
    # colour lock later keeps whatever colour the photo has. Only judged on a locked circle.
    tint = L.sclera_tint(im, cx, cy, r) if locked else None
    lamp = lamp_cast(tint)
    capture = {"verdict": verdict, "detail": detail, "fibre_score": round(fscore, 2),
               "fibre": round(fibre, 2), "basis": round(basis, 2), "glare_on_fibres_pct": round(glare_fib, 1), "diameter_px": int(diam_orig),
               "sclera_b": None if not tint else round(tint["b"], 1), "sclera_a": None if not tint else round(tint["a"], 1),
               "pattern": None if pattern is None else round(pattern, 2), "pattern_shape": None if shape is None else round(shape, 2),
               "direction": None if direction is None else round(direction, 3),
               "direction_fine": None if direction_fine is None else round(direction_fine, 3),
               "softness": None if softness is None else round(softness, 3),
               "blocked": blocked, "block_by": block_by, "block_reason": reason, "pupil_size": pupil_size}
    if device is not None: capture["device"] = device
    if study is not None: capture["study"] = study
    print("snapeyes capture " + json.dumps(capture), flush=True)
    # a short-lived signed ticket: the paid endpoints refuse work without one, so a bare scripted loop
    # has to come through this (cheap) endpoint first instead of hitting the image model directly.
    # No ticket for a circle that is not an iris: from a crop of eyelid skin the image model invented a
    # complete brown iris, which would then be sold as the customer's own eye. The same for a photo too blurry to
    # carry the customer's own pattern (blur_blocked): the model would invent it.
    return {"ok": True, "ticket": L.mint_ticket("work") if locked and not blocked else None, "pupil_r": pupil_r, "fibre": round(fibre, 2),
            "iris": {"cx": cx / W, "cy": cy / H, "r": r / W}, "pad": pad, "glare_boxes_crop": boxes,
            "quality": {"diameter_px": int(diam_orig), "sharpness": round(sharp, 1), "fibre": round(fibre, 2), "sharpness_label": label, "occlusion_pct": occl,
                        "glare": bool(v.get("glare_boxes")), "locked": bool(locked),
                        "detail": detail, "fibre_score": round(fscore, 2), "glare_on_fibres_pct": round(glare_fib, 1),
                        "pupil_reflection": bool(on_pupil), "lamp_cast": lamp, "lamp_message": LAMP_MESSAGE if lamp else None,
                        "verdict": verdict, "message": msg, "tips": tips,
                        "pattern": None if pattern is None else round(pattern, 2),
                        "pattern_shape": None if shape is None else round(shape, 2),
                        "direction": None if direction is None else round(direction, 3),
                        "direction_fine": None if direction_fine is None else round(direction_fine, 3),
                        "softness": None if softness is None else round(softness, 3), "blocked": blocked,
                        "block_reason": reason, "pupil_size": pupil_size},
            "targets": TARGETS,
            "preview": L.pil_to_b64(crop.resize((320, 320), Image.LANCZOS), "JPEG", 85)}

def handle(req): L.run(req, analyze)

class handler(BaseHTTPRequestHandler):
    def do_POST(self): handle(self)
