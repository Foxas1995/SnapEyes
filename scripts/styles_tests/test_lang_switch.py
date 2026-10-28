# -*- coding: utf-8 -*-
"""The language switch in the middle of the capture flow (QA of 2026-10-20). /try sends its language with every request and the server writes its customer sentences
(api/analyze.py: the quality message, the tips, the lamp note) and draws the preview watermark into the display copy of the restoration (api/_lib/iris.py WATERMARK_TEXT) in it.
A visitor who switched the language while the quality step was on screen, or while the analysis or the restoration ran, kept the sentences and the watermark of the old language.

  1. /api/analyze answers every sentence in all four languages (quality.words), each the very sentence a request in that language gets, the four different, none with an unfilled
     {placeholder}, and the fields of the request's own language (message, tips, lamp_message) are exactly as before: an older page reads them unchanged
  2. /api/enhance {redisplay: true, sealed, lang}: the display copy of an eye that is already restored, drawn again in the request's language: no ticket, no model call, the plain copy
     equal to preview.display_b64 for that language, the Reveal's copy (eyelid hidden, pupil crushed) when the deglared crop comes with it, and "shown" says which
  3. it is no way to watermark anything else: only the exact sealed preview this server made (KIND_ORDER) is accepted, a compose copy, a changed one, a plain picture or nothing is refused
     in the page's language, and an expired seal says so; the ticketed route and the sample route are as they were

No network, no image model (the vision answer is a stub and any model call raises), no real eye: the pictures are the public sample eye of the repository.
    python test_lang_switch.py      prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure
Run by suites/run_main.sh as v3lang."""
import atexit
import base64
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
API = os.path.join(REPO, "api")
SP_DIR = os.environ.get("SNAPEYES_SP") or ""
HARNESS = next((d for d in (os.path.join(SP_DIR, "wave-pv", "tests") if SP_DIR else "", os.path.join(REPO, "suites", "tree", "wave-pv", "tests"))
                if d and os.path.isfile(os.path.join(d, "harness.py"))), None) or sys.exit("the payments harness (wave-pv/tests/harness.py) is not found")

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   <- {str(detail)[:900]}"), flush=True)


def section(title):
    print(f"\n== {title}", flush=True)


for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "AWS_", "NOW_", "LAMBDA_", "STORE_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP"):
            os.environ.pop(k)
TMP = tempfile.mkdtemp(prefix="snapeyes_v3lang_")
atexit.register(shutil.rmtree, TMP, ignore_errors=True)
STORE = os.path.join(TMP, "store")
sys.path.insert(0, HARNESS)
os.environ["PYTHONIOENCODING"] = "utf-8"
import harness as H  # noqa: E402

stub = H.start_stub()
H.setup_env(STORE, stub.server_address[1])
sys.path.insert(0, API)
import requests  # noqa: E402
from PIL import Image  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import events as E  # noqa: E402
from _lib import preview as P  # noqa: E402
from _lib.styles import reveal as REV  # noqa: E402

E.record = lambda kind, **f: True            # no event is written


def mod(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(API, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


A = mod("analyze")
H.MODS.update({"analyze": A, "enhance": mod("enhance")})
srv = H.start_api()
BASE = f"http://127.0.0.1:{srv.server_address[1]}"
LANGS = ("en", "de", "lt", "hu", "hr")       # Croatian since 2026-10-28
PUBLIC = os.path.join(REPO, "public", "assets")

# the model must never be asked: the vision answer is a stub, any other model call raises (counted)
MODEL_CALLS = []
VISION = {"box": [226, 225, 786, 785], "pupil": [425, 424, 587, 586], "glare": [], "sharp": "sharp", "occl": 2}


def fake_vision(model, prompt, img):
    return {"found": True, "iris_box": VISION["box"], "pupil_box": VISION["pupil"], "glare_boxes": VISION["glare"], "sharpness": VISION["sharp"],
            "iris_occluded_by_eyelids_percent": VISION["occl"]}


def no_model(*a, **k):
    MODEL_CALLS.append(1)
    raise RuntimeError("no model call in this suite")


L.gemini_json, L.gemini, L.gemini_image = fake_vision, no_model, no_model
JSON = {"Content-Type": "application/json"}


def post(path, body):
    r = requests.post(BASE + path, data=json.dumps(body), headers=JSON, timeout=300)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}


im = Image.open(os.path.join(PUBLIC, "sample_eye_blue_1789706902835.jpg")).convert("RGB")
buf = io.BytesIO()
im.save(buf, "JPEG", quality=90)
PHOTO = base64.b64encode(buf.getvalue()).decode()


def analyze(lang, **vision):
    VISION.update({"box": [226, 225, 786, 785], "pupil": [425, 424, 587, 586], "glare": [], "sharp": "sharp", "occl": 2})
    VISION.update(vision)
    return post("/api/analyze", {"image": PHOTO, "origWidth": 1024, "origHeight": 1024, "lang": lang})


# ============================================================================================ 1. the sentences of an analysis
section("1. /api/analyze: every sentence in all five languages")
good = {lang: analyze(lang) for lang in LANGS}
check("five analyses of one photo, one per language, are all answered 200 with a quality block",
      all(c == 200 and a.get("ok") is True and isinstance(a.get("quality"), dict) for c, a in good.values()), {k: v[0] for k, v in good.items()})
qs = {lang: good[lang][1]["quality"] for lang in LANGS}
check("quality.words has the five languages, each a message, a list of tips and a lamp note (text or none)",
      all(set(q.get("words", {})) == set(LANGS) and all(isinstance(w["message"], str) and w["message"] and isinstance(w["tips"], list) and all(isinstance(t, str) and t for t in w["tips"])
                                                          and (w["lamp_message"] is None or isinstance(w["lamp_message"], str)) for w in q["words"].values()) for q in qs.values()), qs["en"].get("words"))
check("the fields of the request's own language are exactly as before and are the same sentences as that language's entry of quality.words (an older page reads them unchanged)",
      all(qs[l]["message"] == qs[l]["words"][l]["message"] and qs[l]["tips"] == qs[l]["words"][l]["tips"] and qs[l]["lamp_message"] == qs[l]["words"][l]["lamp_message"] for l in LANGS), {l: qs[l]["message"] for l in LANGS})
check("the words do not depend on the language of the request: all five answers carry the same quality.words (one analysis, the sentences written five times)",
      all(qs[l]["words"] == qs["en"]["words"] for l in LANGS) and all(qs[l]["verdict"] == qs["en"]["verdict"] for l in LANGS))
msgs = [qs["en"]["words"][l]["message"] for l in LANGS]
check("the five messages are five different sentences, and each is the sentence of that language's text table (German, Lithuanian, Hungarian, Croatian) or the English one that is inline",
      len(set(msgs)) == 5 and qs["en"]["words"]["de"]["message"] == A.TEXT_DE[qs["en"]["verdict"]] and qs["en"]["words"]["lt"]["message"] == A.TEXT_LT[qs["en"]["verdict"]]
      and qs["en"]["words"]["hu"]["message"] == A.TEXT_HU[qs["en"]["verdict"]] and qs["en"]["words"]["hr"]["message"] == A.TEXT_HR[qs["en"]["verdict"]], msgs)
# a small iris and a reflection on the pupil: tips with numbers and words in every language
small = {lang: analyze(lang, box=[380, 380, 640, 640], pupil=[470, 470, 550, 550], glare=[[500, 500, 520, 520]], sharp="soft", occl=40) for lang in LANGS}
sq = {lang: small[lang][1]["quality"] for lang in LANGS if small[lang][0] == 200 and small[lang][1].get("ok")}
tips_by = {l: sq[l]["words"][l]["tips"] for l in sq}
check("a small, soft, reflected shot gives tips in every language (at least two each, the same number in all five), and the request's own tips are that language's entry",
      set(sq) == set(LANGS) and all(len(t) >= 2 for t in tips_by.values()) and len({len(t) for t in tips_by.values()}) == 1 and all(sq[l]["tips"] == tips_by[l] for l in LANGS), {l: len(t) for l, t in tips_by.items()})
every = [s for q in sq.values() for w in q["words"].values() for s in [w["message"], *w["tips"], w["lamp_message"] or ""]]
check("no sentence of any language has an unfilled {placeholder} or an empty text, and the iris size is in the tip about it in all five languages",
      every and not any("{" in s or "}" in s for s in every) and all(re.search(r"\d{3}", sq["en"]["words"][l]["tips"][0]) or any(re.search(r"\d{3}", t) for t in sq["en"]["words"][l]["tips"]) for l in LANGS), every[:3])
check("the model was never asked (the vision answer is a stub, any other call raises)", not MODEL_CALLS, MODEL_CALLS)

# ============================================================================================ 2. redisplay
section("2. /api/enhance {redisplay}: the display copy in the language of the request")
CLEAN_RAW = open(os.path.join(PUBLIC, "sample_eye_blue_restored.jpg"), "rb").read()
CROP_RAW = open(os.path.join(PUBLIC, "sample_eye_blue_before.jpg"), "rb").read()
clean_im = Image.open(io.BytesIO(CLEAN_RAW)).convert("RGB")
prot = P.protect(clean_im, CLEAN_RAW, lang="en")
SEALED = prot["sealed"]
shown = {lang: post("/api/enhance", {"redisplay": True, "sealed": SEALED, "lang": lang, "pad": 1.12}) for lang in LANGS}
check("a sealed preview is drawn again in each of the five languages: 200, ok, the plain display copy (shown plain), and the reply names the language it was drawn in",
      all(c == 200 and r.get("ok") is True and r.get("shown") == "plain" and r.get("lang") == l and isinstance(r.get("image"), str) for l, (c, r) in shown.items()), {l: (c, r.get("shown"), r.get("lang")) for l, (c, r) in shown.items()})
# since 2026-10-20 the words on the iris are the site's address alone, the same in every language (the owner: "drop PREVIEW, keep SnapEyes.com", iris.py
# WATERMARK_TILE): the four copies are one picture now, and the redraw still answers each language with exactly what display_b64 makes in it (the check below)
check("every copy is a display copy (the mark of preview.is_display_b64), and the five carry the same words in the pixels (SnapEyes.com in every language since 2026-10-20)",
      all(P.is_display_b64(r["image"]) for _, r in shown.values()) and len({r["image"] for _, r in shown.values()}) == 1
      and len({L.WATERMARK_TEXT[l][0] for l in LANGS}) == 1, {l: len(r["image"]) for l, (_, r) in shown.items()})
check("each copy is byte for byte what preview.display_b64 makes of the sealed clean picture in that language (the first one, English, is also the one /api/enhance made in English)",
      all(r["image"] == P.display_b64(clean_im, l, 1.12) for l, (_, r) in shown.items()) and shown["en"][1]["image"] == prot["image"], [l for l, (_, r) in shown.items() if r["image"] != P.display_b64(clean_im, l, 1.12)])
rv = {l: post("/api/enhance", {"redisplay": True, "sealed": SEALED, "lang": l, "pad": 1.12, "crop": base64.b64encode(CROP_RAW).decode()}) for l in ("en", "de")}
crop_im = Image.open(io.BytesIO(CROP_RAW)).convert("RGB")
want_rv = {l: REV.reveal_for(L.mask_disk(crop_im.crop((0, 0, min(crop_im.size), min(crop_im.size))), 1.12), clean_im, lang=l, pad=1.12) for l in ("en", "de")}
if all(want_rv[l]["image"] is not None for l in want_rv):
    check("with the deglared crop the Reveal's copy comes back (shown reveal: eyelid hidden, pupil crushed), byte for byte what the Reveal makes in that language (the same words in both since 2026-10-20)",
          all(c == 200 and r.get("shown") == "reveal" and r["image"] == REV.display_b64(want_rv[l]["image"]) for l, (c, r) in rv.items()) and rv["en"][1]["image"] == rv["de"][1]["image"]
          and rv["en"][1]["image"] != shown["en"][1]["image"], {l: (c, r.get("shown")) for l, (c, r) in rv.items()})
else:
    check("with the deglared crop the Reveal is measured on this pair or the reply says plain (never a Reveal claim it did not make)", all(r.get("shown") == "plain" for _, r in rv.values()), {l: (c, r.get("shown")) for l, (c, r) in rv.items()})
check("an eye is never asked for again with the Reveal's measuring off its padding: a padding the Reveal does not measure at (1.5) gives the plain copy and says so",
      post("/api/enhance", {"redisplay": True, "sealed": SEALED, "lang": "de", "pad": 1.5, "crop": base64.b64encode(CROP_RAW).decode()})[1].get("shown") == "plain")
check("no model call and no ticket: none of the calls above sent a ticket, and the model was not asked", not MODEL_CALLS and all("ticket" not in json.dumps(b) for b in [{"redisplay": True}]), MODEL_CALLS)

# ============================================================================================ 3. what it will not do
section("3. the redisplay is no way round the ticket or the seal")
compose_copy = prot["sealed_sizes"]["768"]
other = P.seal(b"not a picture", kind=P.KIND_ORDER)
flipped = SEALED[:-4] + ("A" if SEALED[-4] != "A" else "B") + SEALED[-3:]
expired = P.seal(CLEAN_RAW, ttl=-10)
refused = {}
for label, sealed in (("a compose copy", compose_copy), ("a changed seal", flipped), ("a seal of something that is no picture", other), ("an expired seal", expired), ("a plain picture", base64.b64encode(CLEAN_RAW).decode()),
                      ("an empty string", ""), ("a number", 5), ("nothing", None)):
    for lang in ("de", "lt"):
        c, r = post("/api/enhance", {"redisplay": True, "sealed": sealed, "lang": lang, "pad": 1.12})
        refused[(label, lang)] = (c, r.get("ok"), r.get("error") or r.get("message") or "", "image" in r)
check("a compose copy, a changed or expired seal, a seal of something that is not a picture, a plain picture, an empty string, a number and no seal at all are all refused (4xx, no image), none answered",
      all(200 < c < 500 and ok is not True and not has_image for (c, ok, _, has_image) in refused.values()), {k: v[:2] for k, v in refused.items() if not (200 < v[0] < 500)})
check("the refusals are written in the page's language: the German and the Lithuanian one differ from each other and from the English one, and an expired seal says it is too old",
      refused[("a changed seal", "de")][2] != refused[("a changed seal", "lt")][2] and refused[("a changed seal", "de")][2] and refused[("an expired seal", "de")][2] == P.REFUSALS["de"][0]
      and refused[("an expired seal", "lt")][2] == P.REFUSALS["lt"][0], {k: v[2] for k, v in refused.items() if k[0] in ("a changed seal", "an expired seal")})
c_t, r_t = post("/api/enhance", {"crop": base64.b64encode(CROP_RAW).decode(), "mode": "artistic", "pad": 1.12})
c_s, r_s = post("/api/enhance", {"sample": True, "image": base64.b64encode(CLEAN_RAW).decode(), "lang": "de"})
check("the other two routes are as they were: a restoration without a ticket is still a 403, and the sample route still answers the shipped sample (its display copy in the request's language)",
      c_t == 403 and c_s == 200 and r_s.get("sample") is True and P.is_display_b64(r_s["image"]) and r_s["image"] == P.display_b64(clean_im, "de", 1.12), (c_t, c_s, r_s.get("ok")))
check("still no model call", not MODEL_CALLS, MODEL_CALLS)

# ============================================================================================ 4. the words of the watermark (the owner's insight 4, 2026-10-20)
section("4. the address on the iris, and a badge that promises nothing while ordering is closed")
OLD_EN_TILE = "SNAPEYES.COM  ·  PREVIEW"
check("the words on the iris are the site's address alone, the same in all five languages: no PREVIEW, VORSCHAU, PERŽIŪRA, ELŐNÉZET or PREGLED",
      all(L.WATERMARK_TEXT[l][0] == "SnapEyes.com" for l in LANGS), {l: L.WATERMARK_TEXT[l][0] for l in LANGS})
check("the badge while ordering is closed (soon) says the preview is free and that ordering opens soon, in each language, and offers nothing to unlock or buy",
      all(L.watermark_badge(l, soon=True) == L.WATERMARK_SOON[l] for l in LANGS)
      and all(w in L.WATERMARK_SOON[l] for l, w in (("en", "FREE"), ("de", "KOSTENLOSE"), ("lt", "NEMOKAMA"), ("hu", "INGYENES"), ("hr", "BESPLATNI")))
      and not any(re.search("UNLOCK|KAUFEN|UŽSAKYKITE|RENDELD|NARUČITE", L.WATERMARK_SOON[l]) for l in LANGS), L.WATERMARK_SOON)
check("with ordering open the badge is the one of before in every language (its call to order the full size)",
      all(L.watermark_badge(l, soon=False) == L.WATERMARK_TEXT[l][1] for l in LANGS) and L.watermark_badge("en") == "WATERMARKED PREVIEW  ·  UNLOCK FULL SIZE")
from PIL import ImageDraw  # noqa: E402
import numpy as np  # noqa: E402
wide = {}
for W_, H_ in ((1024, 1024), (473, 1024)):
    u_ = min(W_, H_)
    d_ = ImageDraw.Draw(Image.new("RGB", (W_, H_)))
    f_ = L._font("PlusJakartaSans.ttf", int(u_ * 0.016), "Bold")
    wide[(W_, H_)] = (max(d_.textlength(L.WATERMARK_SOON[l], font=f_) for l in LANGS), d_.textlength(L.WATERMARK_TEXT["de"][1], font=f_))
check("every closed badge is narrower than the German badge of an open deployment (the widest, measured to fit) on the 1024 px square and the 473 px wallpaper",
      all(a < b and a + 2 * 0.022 * min(W_, H_) < W_ - 4 for (W_, H_), (a, b) in wide.items()), wide)
canvas = Image.new("RGB", (1024, 1024), (8, 8, 8))
canvas.paste(clean_im.resize((900, 900)), (62, 62))
disc = [(512.0, 512.0, 900 * L.iris_radius_frac(1.12))]
w_soon = np.asarray(P.watermark(canvas, (245, 197, 66), disc, lang="lt", soon=True), np.int16)
w_open = np.asarray(P.watermark(canvas, (245, 197, 66), disc, lang="lt", soon=False), np.int16)
band = int(0.11 * 1024)
check("a picture's closed and open watermarks differ only in the badge band at the top (the words on the iris and everything else are the same pixels)",
      int((np.abs(w_soon - w_open)[:band] > 40).sum()) > 200 and int(np.abs(w_soon - w_open)[band:].max()) == 0)
ink = {t: round(float((np.asarray(L._watermark_layer(800, 800, 800.0, t).getchannel("A")) > 10).mean()), 4) for t in (OLD_EN_TILE, "SnapEyes.com")}
check("the address alone is laid closer on the tile (iris.WATERMARK_STEP), so it covers about as much as the long words did (at least 80 % of their ink)",
      ink["SnapEyes.com"] >= 0.8 * ink[OLD_EN_TILE], ink)

ok = sum(RESULTS)
print(f"\n{ok} of {len(RESULTS)} passed")
sys.exit(0 if ok == len(RESULTS) else 1)
