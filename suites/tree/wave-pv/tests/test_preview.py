# -*- coding: utf-8 -*-
"""The /try preview protection (api/_lib/preview.py): /api/enhance returns a watermarked display copy and the clean
restoration sealed; /api/compose and the order draft take the sealed copy back. Runs on the payments harness (fake
Stripe + Resend, local store folder, the real handlers over HTTP) with the image model stubbed (no key, no cost).
    python test_preview.py        PASS/FAIL per check, exit 1 on any failure"""
import os, sys, io, json, time, base64, hashlib, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import harness as H

STORE = os.path.join(HERE, "store_pv")
stub = H.start_stub()
H.setup_env(STORE, stub.server_address[1])
api = H.start_api()
BASE = f"http://127.0.0.1:{api.server_address[1]}"

import requests
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, H.API)
from _lib import iris as L
from _lib import store
from _lib import preview as P

for name in ("compose", "enhance"):          # served by the harness' dispatcher, which looks modules up per request
    spec = importlib.util.spec_from_file_location(name, os.path.join(H.API, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    H.MODS[name] = m

RESULTS = []
DASHES = (chr(0x2013), chr(0x2014))


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"   <- {str(detail)[:600]}"), flush=True)


def post(path, body):
    r = requests.post(BASE + path, data=json.dumps(body), headers={"Content-Type": "application/json"}, timeout=180)
    try:
        return r.status_code, r.json(), r.text
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}, r.text


def local(path):
    return os.path.join(STORE, *path.split("/"))


def read_json(path):
    with open(local(path), encoding="utf-8") as f:
        return json.load(f)


def files_under(folder):
    top = local(folder)
    return sorted(os.path.join(d, f) for d, _, fs in os.walk(top) for f in fs) if os.path.isdir(top) else []


def b64(raw):
    return base64.b64encode(raw).decode("ascii")


def flip(sealed, at):
    raw = bytearray(base64.b64decode(sealed))
    raw[at] ^= 0x01
    return b64(bytes(raw))


def sealed_with_secret(data, secret, ttl=P.SEAL_TTL):
    old = os.environ["SNAPEYES_TICKET_SECRET"]
    os.environ["SNAPEYES_TICKET_SECRET"] = secret
    try:
        return P.seal(data, ttl=ttl)
    finally:
        os.environ["SNAPEYES_TICKET_SECRET"] = old


# ------------------------------------------------------------------ the image model, stubbed
MODEL_CALLS = []


def fake_gemini_image(prompt, im, size=None, thinking=None, model=None):
    MODEL_CALLS.append(prompt[:30])
    return im.filter(ImageFilter.UnsharpMask(2, 60, 2))      # a "restoration" close enough to pass the fidelity guard


L.gemini_image = fake_gemini_image

SEEN = []                                                     # what enhance handed protect(): the clean image and bytes
_REAL_PROTECT = P.protect


def spy_protect(clean_im, clean_bytes, lang=None, **kw):       # protect() gained profile= (the eye profile, WP3): passed through
    SEEN.append((clean_im.copy(), bytes(clean_bytes)))
    return _REAL_PROTECT(clean_im, clean_bytes, lang, **kw)


P.protect = spy_protect

WT_PUBLIC = os.path.join(H.REPO, "public", "assets")
CROP_RAW = open(os.path.join(WT_PUBLIC, "sample_eye_blue_before.jpg"), "rb").read()     # 638 px: no Real-ESRGAN pass
SAMPLE_RAW = open(os.path.join(WT_PUBLIC, "sample_eye_blue_restored.jpg"), "rb").read()

# ================================================================== A. seal / unseal
data = os.urandom(200_000)
s1, s2 = P.seal(data), P.seal(data)
check("A1 seal round trip returns the exact bytes", P.unseal(s1) == data and P.unseal(s2) == data)
check("A2 two seals of the same bytes differ (random nonce) and neither carries the plain bytes",
      s1 != s2 and base64.b64decode(s1)[P.HEAD_BYTES:P.HEAD_BYTES + 64] != data[:64])
check("A3 envelope: version byte, kind byte (order by default), expiry about SEAL_TTL ahead, 16-byte nonce, 32-byte tag",
      base64.b64decode(s1)[0] == P.VERSION and base64.b64decode(s1)[1] == P.KIND_ORDER
      and abs(int.from_bytes(base64.b64decode(s1)[2:6], "big") - (time.time() + P.SEAL_TTL)) < 5
      and len(base64.b64decode(s1)) == len(data) + 1 + 1 + 4 + 16 + 32)


def refused(s, kind=P.SealError):
    try:
        P.unseal(s)
    except kind:
        return True
    except Exception as e:  # noqa
        return f"wrong exception {e!r}"
    return False


def refused_kinds(s, kinds):
    try:
        P.unseal(s, kinds=kinds)
    except P.SealError:
        return True
    return False


def bytes_set(sealed, at, value):
    raw = bytearray(base64.b64decode(sealed))
    raw[at] = value
    return b64(bytes(raw))


n = len(base64.b64decode(s1))
check("A4 a changed ciphertext byte is refused", refused(flip(s1, 500)) is True)
check("A5 a changed tag byte is refused", refused(flip(s1, n - 1)) is True)
check("A6 a changed expiry (pushed later) is refused", refused(flip(s1, 4)) is True)
check("A7 a changed nonce byte is refused", refused(flip(s1, 10)) is True)
check("A8 another version byte is refused", refused(flip(s1, 0)) is True)
check("A9 truncated / empty / not base64 / oversized are refused",
      refused(s1[:40]) is True and refused("") is True and refused("%%%notbase64%%%") is True
      and refused("A" * (P.SEALED_B64_MAX + 4)) is True and refused(None) is True)
check("A10 sealed with another server key is refused", refused(sealed_with_secret(data, "another-secret")) is True)
expired = P.seal(data, ttl=-1)
check("A11 an expired seal is refused as expired, a changed expired one as invalid (tag first)",
      refused(expired, P.SealExpired) is True and refused(flip(expired, 300), P.SealExpired) is not True
      and refused(flip(expired, 300)) is True)
sc = P.seal(data, kind=P.KIND_COMPOSE)
check("A13 kinds: a compose copy opens for compose (default kinds) but not where only an order's preview is taken",
      P.unseal(sc) == data and refused_kinds(sc, (P.KIND_ORDER,)) is True and P.unseal(s1, kinds=(P.KIND_ORDER,)) == data
      and base64.b64decode(sc)[1] == P.KIND_COMPOSE)
check("A14 a compose copy relabelled as the order kind is refused by the tag", refused(bytes_set(sc, 1, P.KIND_ORDER)) is True)
try:
    P.seal(data, kind=9)
    bad_kind = False
except ValueError:
    bad_kind = True
check("A15 seal refuses an unknown kind", bad_kind)
t0 = time.time()
P.unseal(P.seal(SAMPLE_RAW))
check("A12 seal + unseal of a 295 kB preview under 0.5 s", time.time() - t0 < 0.5, time.time() - t0)

# ================================================================== B. /api/enhance
TICKET = L.mint_ticket("work")
c, j, raw = post("/api/enhance", {"crop": b64(CROP_RAW), "mode": "artistic", "pad": 1.12, "ticket": TICKET, "lang": "de"})
check("B1 enhance -> 200 with image, sealed and sealed_sizes 768 / 560", c == 200 and isinstance(j.get("image"), str)
      and isinstance(j.get("sealed"), str) and set((j.get("sealed_sizes") or {}).keys()) == {"768", "560"}, (c, str(j)[:300]))
CLEAN_IM, CLEAN = SEEN[-1]
check("B2 the clean bytes are the old reply's encoding (JPEG q93 4:4:4 of the 1024 px result)",
      CLEAN == base64.b64decode(L.pil_to_b64(CLEAN_IM, "JPEG", 93)) and CLEAN_IM.size == (1024, 1024))
check("B3 sealed opens to exactly the clean enhance output", P.unseal(j["sealed"]) == CLEAN)
check("B4 the reply never carries the clean image (not as image, not anywhere in the text)",
      b64(CLEAN) not in raw and base64.b64decode(j["image"]) != CLEAN and b64(CLEAN)[1000:1100] not in raw)
disp_raw = base64.b64decode(j["image"])
disp = Image.open(io.BytesIO(disp_raw))
check("B5 image is the 800 px display copy, marked in its JPEG comment",
      disp.format == "JPEG" and disp.size == (800, 800) and P.is_display(disp_raw) and not P.is_display(CLEAN), (disp.size, disp.info))
want = P.display_image(CLEAN_IM, "de")
d_px = np.asarray(disp.convert("RGB"), np.float32)
check("B6 the display copy is display_image() of the clean result in German (the request's language)",
      np.abs(d_px - np.asarray(want, np.float32)).mean() < 2.0, np.abs(d_px - np.asarray(want, np.float32)).mean())
plain = np.asarray(CLEAN_IM.resize((800, 800), Image.LANCZOS), np.float32)
yy, xx = np.mgrid[0:800, 0:800]
rr = np.hypot(yy - 400, xx - 400) / 400
ring = (rr > 0.35) & (rr < 0.85)                         # the iris itself (pupil and the dark corners left out)
changed = (np.abs(np.asarray(want, np.float32) - plain).max(axis=2) > 40)
check("B7 the watermark crosses the iris itself (a share of the iris ring changed by more than 40 levels)",
      changed[ring].mean() > 0.02, changed[ring].mean())
check("B8 German and English display copies differ (VORSCHAU / PREVIEW)",
      np.abs(np.asarray(P.display_image(CLEAN_IM, "en"), np.float32) - np.asarray(want, np.float32)).max() > 100)
small = {k: Image.open(io.BytesIO(P.unseal(v))) for k, v in j["sealed_sizes"].items()}
check("B9 sealed_sizes open to clean JPEG squares of 768 and 560 px",
      small["768"].size == (768, 768) and small["560"].size == (560, 560) and all(i.format == "JPEG" for i in small.values()))
check("B9b sealed is of the order kind, sealed_sizes of the compose kind",
      base64.b64decode(j["sealed"])[1] == P.KIND_ORDER
      and all(base64.b64decode(v)[1] == P.KIND_COMPOSE for v in j["sealed_sizes"].values()))
c2, j2, _ = post("/api/enhance", {"crop": b64(CROP_RAW), "mode": "artistic", "pad": 1.12, "lang": "de"})
check("B10 enhance without a ticket -> 403, nothing sealed", c2 == 403 and "sealed" not in j2, (c2, j2))
calls = len(MODEL_CALLS)
c3, j3, raw3 = post("/api/enhance", {"sample": True, "image": b64(SAMPLE_RAW), "lang": "en"})
check("B11 the sample eye's file -> 200 display + sealed, no ticket, no model call",
      c3 == 200 and P.unseal(j3["sealed"]) == SAMPLE_RAW and P.is_display(base64.b64decode(j3["image"]))
      and set(j3["sealed_sizes"]) == {"768", "560"} and len(MODEL_CALLS) == calls and b64(SAMPLE_RAW) not in raw3, (c3, str(j3)[:200]))
bad = bytearray(SAMPLE_RAW)
bad[5000] ^= 1
c4, j4, _ = post("/api/enhance", {"sample": True, "image": b64(bytes(bad)), "lang": "en"})
c5, j5, _ = post("/api/enhance", {"sample": True, "image": b64(CROP_RAW), "lang": "en"})
c6, j6, _ = post("/api/enhance", {"sample": True, "image": 5})
check("B12 any other image as the sample -> 400 (no free watermarking or sealing service)",
      c4 == 400 and c5 == 400 and c6 == 400 and "sealed" not in j4 and "sealed" not in j5, (c4, j4, c5, c6))
check("B13 SAMPLE_SHA256 is the shipped sample file's hash",
      H.MODS["enhance"].SAMPLE_SHA256 == hashlib.sha256(SAMPLE_RAW).hexdigest())
SEALED, SIZES, DISPLAY_B64 = j["sealed"], j["sealed_sizes"], j["image"]

# ================================================================== C. /api/compose
BASE_C = {"style": "celestial_gold", "names": "Jūratė & Tomas", "pad": 1.12, "lang": "de"}
c, jc, _ = post("/api/compose", dict(BASE_C, sealed=[SEALED]))
cl, jl, _ = post("/api/compose", dict(BASE_C, irises=[b64(CLEAN)]))
check("C1 compose with the sealed iris -> the same artwork as with the clean iris (old form)",
      c == 200 and cl == 200 and jc["image"] == jl["image"] and jc["width"] == 1024 and jc["count"] == 1, (c, cl, str(jc)[:200]))
c, jw, _ = post("/api/compose", dict(BASE_C, sealed=[SEALED], irises=["not an image"]))
check("C2 sealed wins when both forms are sent", c == 200 and jw["image"] == jc["image"], (c, str(jw)[:200]))
three = [SIZES["768"], SIZES["768"], j3["sealed_sizes"]["768"]]
c, j3c, _ = post("/api/compose", dict(BASE_C, sealed=three, layout="triangle"))
c3l, j3l, _ = post("/api/compose", dict(BASE_C, irises=[b64(P.unseal(s)) for s in three], layout="triangle"))
check("C3 three sealed 768 px irises -> the triangle artwork, the same as from their clean bytes",
      c == 200 and c3l == 200 and j3c["image"] == j3l["image"] and j3c["count"] == 3 and j3c["layout"] == "triangle", (c, c3l))
eight = [SIZES["560"]] * 4 + [j3["sealed_sizes"]["560"]] * 4
body8 = dict(BASE_C, sealed=eight)
c, j8, _ = post("/api/compose", body8)
check("C4 eight sealed 560 px irises fit one request and compose (galaxy)",
      c == 200 and j8["count"] == 8 and sum(map(len, eight)) < H.MODS["compose"].MAX_TOTAL_B64, (c, str(j8)[:200]))
c, jt, _ = post("/api/compose", dict(BASE_C, sealed=[flip(SEALED, 2000)]))
check("C5 a tampered sealed iris -> 400 with the German sentence", c == 400 and jt["error"] == P.refusal(P.SealError(), "de")
      and "Vorschau" in jt["error"], (c, jt))
c, je, _ = post("/api/compose", dict(BASE_C, sealed=[P.seal(CLEAN, ttl=-1)], lang="en"))
check("C6 an expired sealed iris -> 400 'too old' in English", c == 400 and jt["error"] != je["error"]
      and je["error"] == "This preview is too old. Please take the photo again.", (c, je))
c, jk, _ = post("/api/compose", dict(BASE_C, sealed=[sealed_with_secret(CLEAN, "another-secret")]))
c2, jg, _ = post("/api/compose", dict(BASE_C, sealed=["abc"]))
c3_, jn, _ = post("/api/compose", dict(BASE_C, sealed=[SEALED, 7]))
check("C7 another key's seal, garbage and a non-string -> 400", c == 400 and c2 == 400 and c3_ == 400, (c, c2, c3_, jn))
# C9-C11: the artwork preview is watermarked across the irises too (iris._iris_mark): the share of iris-ring pixels
# changed by more than 40 levels against the same artwork without a watermark (both JPEG q90), and not one pixel
# outside the discs changed against the tile-only watermark of b5d3113
DISCS = []
_REAL_MARK = L._iris_mark


def spy_mark(out, layer, discs):
    DISCS.append(list(discs))
    return _REAL_MARK(out, layer, discs)


def dec_np(b):
    return np.asarray(Image.open(io.BytesIO(base64.b64decode(b))).convert("RGB"), np.int16)


def jpeg90(im):
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=90)
    return np.asarray(Image.open(buf).convert("RGB"), np.int16)


def ring_share(new, ref, discs):
    H_, W_ = new.shape[:2]
    yy_, xx_ = np.mgrid[0:H_, 0:W_]
    ring_ = np.zeros((H_, W_), bool)
    for cx, cy, r in discs:
        d = np.hypot(xx_ + 0.5 - cx, yy_ + 0.5 - cy)
        ring_ |= (d > 0.35 * r) & (d < 0.95 * r)
    ring_[: int(0.11 * max(W_, H_))] = False              # the badge band
    return float((np.abs(new - ref).max(axis=2)[ring_] > 40).mean())


pale_im = Image.open(io.BytesIO(CLEAN)).convert("RGB")
shares = {}
for style, seals, layout in (("studio_black", [SEALED], None), ("celestial_gold", [SEALED], None),
                             ("deep_nebula", [SIZES["768"]] * 2, "duo"), ("celestial_gold", [SIZES["768"]] * 4, "row"),
                             ("celestial_gold", [SIZES["560"]] * 8, "galaxy")):
    DISCS.clear()
    L._iris_mark = spy_mark
    body_m = dict(BASE_C, style=style, sealed=seals, lang="en", names="")
    if layout:
        body_m["layout"] = layout
    c, jm_, _ = post("/api/compose", body_m)
    L._iris_mark = _REAL_MARK
    ims_m = [Image.open(io.BytesIO(P.unseal(x))).convert("RGB") for x in seals]
    nowm = L.compose_multi(ims_m, style=style, names="", title=None, watermark=False, r_frac=L.iris_radius_frac(1.12),
                           size=1024, layout=L.multi_layout(len(seals), layout), fmt="artwork")
    key = f"{style}/{layout or 'single'}"
    shares[key] = (c, ring_share(dec_np(jm_["image"]), jpeg90(nowm), DISCS[0]) if c == 200 and DISCS else 0.0,
                   len(DISCS[0]) if DISCS else 0)
check("C9 every compose preview marks each iris disc: > 2% of the iris ring changed by more than 40 levels",
      all(c == 200 and sh > 0.02 for c, sh, _ in shares.values()) and [v[2] for v in shares.values()] == [1, 1, 2, 4, 8],
      {k: (v[0], round(v[1] * 100, 2), v[2]) for k, v in shares.items()})
print("   iris ring share changed > 40 levels:", {k: round(v[1] * 100, 2) for k, v in shares.items()})
L._iris_mark = lambda out, layer, discs: out            # the watermark of b5d3113: the tile alone
old_art = L.compose_multi([pale_im], style="celestial_gold", names="A & B", watermark=True, r_frac=L.iris_radius_frac(1.12),
                          size=1024, layout="single", fmt="artwork")
L._iris_mark = spy_mark
DISCS.clear()
new_art = L.compose_multi([pale_im], style="celestial_gold", names="A & B", watermark=True, r_frac=L.iris_radius_frac(1.12),
                          size=1024, layout="single", fmt="artwork")
a_, b_ = np.asarray(new_art, np.int16), np.asarray(old_art, np.int16)
yy_, xx_ = np.mgrid[0:1024, 0:1024]
cx_, cy_, r_ = DISCS[0][0]
outside = np.hypot(xx_ + 0.5 - cx_, yy_ + 0.5 - cy_) > r_ + 6
check("C10 outside the iris discs the preview is pixel for pixel the tile-only watermark (badge, caption, background)",
      int((np.abs(a_ - b_).max(axis=2)[outside] > 0).sum()) == 0 and int((np.abs(a_ - b_).max(axis=2)[~outside] > 40).sum()) > 1000)
DISCS.clear()
unw = L.compose_multi([pale_im], style="celestial_gold", names="A & B", watermark=False, r_frac=L.iris_radius_frac(1.12),
                      size=1024, layout="single", fmt="artwork")
L._iris_mark = _REAL_MARK
check("C11 an unlocked artwork (watermark off, as master_compose renders it) gets no iris mark", not DISCS and unw.size == (1024, 1024))
check("C8 no refusal sentence carries a dash", all(ch not in (jt["error"] + je["error"] + P.refusal(P.SealExpired(), "de"))
                                                   for ch in DASHES))

# ================================================================== D. the order draft
CROP_B64 = b64(CROP_RAW)


def draft(eye=1, order=None, k=None, **kw):
    b = {"action": "draft", "eye": eye, "crop": CROP_B64, "pad": 1.12, "lang": "de", "ref": f"eye-{eye}",
         "ticket": H.fresh_ticket() if order is None else TICKET}
    if order:
        b.update(order=order, k=k)
    b.update(kw)
    return post("/api/order", b)


c, jd, _ = draft(sealed=SEALED)
check("D1 draft with the sealed preview -> 200, a new order", c == 200 and jd.get("created") is True, (c, jd))
O1, K1 = jd["order"], jd["k"]
rec = read_json(f"orders/{O1}/draft/eye_1.json")
stored = open(local(rec["preview"]["path"]), "rb").read()
check("D2 the stored preview is byte for byte the clean enhance output (and its sha256 in the record)",
      stored == CLEAN and rec["preview"]["sha256"] == hashlib.sha256(CLEAN).hexdigest() and rec["preview"]["side"] == 1024
      and rec["preview"]["type"] == "image/jpeg", rec)
before = files_under(f"orders/{O1}")
c, jx, _ = draft(2, O1, K1, sealed=flip(SEALED, 3000))
check("D3 a tampered sealed preview -> 400 preview_invalid, nothing stored", c == 400 and jx.get("reason") == "preview_invalid"
      and files_under(f"orders/{O1}") == before, (c, jx))
c, jx, _ = draft(2, O1, K1, sealed=P.seal(CLEAN, ttl=-1))
check("D4 an expired sealed preview -> 410 preview_expired, nothing stored", c == 410 and jx.get("reason") == "preview_expired"
      and files_under(f"orders/{O1}") == before, (c, jx))
c, jx, _ = draft(2, O1, K1, sealed=sealed_with_secret(CLEAN, "another-secret"))
check("D5 a preview sealed with another key -> 400 preview_invalid", c == 400 and jx.get("reason") == "preview_invalid", (c, jx))
c, jx, _ = draft(2, O1, K1, sealed="A" * (P.SEALED_B64_MAX + 8))
check("D6 an oversized sealed preview -> 413 too_large", c == 413 and jx.get("reason") == "too_large", (c, jx))
c, jx, _ = draft(2, O1, K1, preview=DISPLAY_B64)
check("D7 the display copy sent as an old page's preview -> 409 preview_outdated, nothing stored",
      c == 409 and jx.get("reason") == "preview_outdated" and files_under(f"orders/{O1}") == before, (c, jx))
c, jx, _ = draft(2, O1, K1, preview=b64(CLEAN))
d2 = read_json(f"orders/{O1}/draft/eye_2.json") if c == 200 else {}
check("D8 an old page's clean preview is still accepted (one release)", c == 200
      and open(local(d2["preview"]["path"]), "rb").read() == CLEAN, (c, jx))
c, jx, _ = draft(2, O1, K1, sealed=j3["sealed"], preview="not an image")
d2 = read_json(f"orders/{O1}/draft/eye_2.json") if c == 200 else {}
check("D9 sealed wins over preview (eye 2 replaced by the sample's sealed file)", c == 200
      and open(local(d2["preview"]["path"]), "rb").read() == SAMPLE_RAW, (c, jx))
before2 = files_under(f"orders/{O1}")
c, jx, _ = draft(3, O1, K1, sealed=SIZES["768"])
check("D11 a smaller sealed_sizes copy is refused as an order's preview (400 preview_invalid), nothing stored",
      c == 400 and jx.get("reason") == "preview_invalid" and files_under(f"orders/{O1}") == before2, (c, jx))
check("D10 the draft's new refusal sentences carry no dash", all(ch not in open(os.path.join(H.API, "order.py"),
                                                                                   encoding="utf-8").read() for ch in DASHES))

# ================================================================== E. paid: master_eye gets exactly the clean output
c, jd, _ = draft(sealed=SEALED)
O2, K2 = jd["order"], jd["k"]
c, jc2, _ = post("/api/checkout", {"order": O2, "k": K2, "eyes": 1, "style": "studio_black", "names": "", "title": "",
                                   "lang": "de", "consent_digital": True})
check("E1 checkout of the sealed-draft order -> 200", c == 200 and jc2.get("url"), (c, jc2))
sid = read_json(f"orders/{O2}/order.json")["checkout"]["session_id"]
sess = H.pay_session(sid)
body, sig = H.signed_event(sess)
r = requests.post(BASE + "/api/stripe_webhook", data=body, headers={"Content-Type": "application/json", "Stripe-Signature": sig},
                  timeout=60)
check("E2 paid by webhook, confirmation sent", r.status_code == 200 and r.json().get("mail") == "sent", r.text[:300])
ME = H.MODS["order"].ME
SEEN_ME = []
REAL_ME = ME.master_eye


def fake_master_eye(b):
    SEEN_ME.append(b)
    key = f"orders/{b['order']}/eye_{b['eye']}.jpg"
    store.put(key, base64.b64decode(b["crop"]), "image/jpeg", upsert=False)
    return {"ok": True, "existing": False, "seconds": 0.5, "needs_review": False, "key": key}


ME.master_eye = fake_master_eye
c, jm, _ = post("/api/order", {"action": "make", "order": O2, "k": K2, "eye": 1})
ME.master_eye = REAL_ME
got = base64.b64decode(SEEN_ME[-1]["preview"]) if SEEN_ME else b""
check("E3 make: master_eye's preview input is byte for byte the clean /api/enhance output", c == 200 and got == CLEAN, (c, jm))
pv_a = ME._preview(SEEN_ME[-1]["preview"], 1.12) if SEEN_ME else None
pv_b = ME._preview(b64(CLEAN), 1.12)
sha = lambda im: hashlib.sha256(im.tobytes()).hexdigest()[:16]   # noqa: master_eye's preview_sha
check("E4 so master_eye's preview_sha is the one the clean output gives (the re-render rule holds)",
      pv_a is not None and sha(pv_a) == sha(pv_b))

# ================================================================== F. /api/master_eye takes the sealed preview, never a display copy
MEm = H.MODS["order"].ME
pv_clean = MEm._preview(b64(CLEAN), 1.12)
pv_sealed = MEm._preview(None, 1.12, SEALED)
pv_both = MEm._preview("not an image", 1.12, SEALED)
check("F1 master_eye opens sealed into exactly the clean preview (the same preview_sha), sealed wins over preview",
      sha(pv_sealed) == sha(pv_clean) and sha(pv_both) == sha(pv_clean))


def me_refused(s, sealed=None):
    try:
        MEm._preview(s, 1.12, sealed)
    except L.ClientError as e:
        return str(e)
    return None


check("F2 master_eye refuses the display copy (also as a data URL), a compose copy, a tampered and an expired seal",
      bool(me_refused(DISPLAY_B64) and me_refused("data:image/jpeg;base64," + DISPLAY_B64) and me_refused(None, SIZES["768"])
           and me_refused(None, flip(SEALED, 900))) and "too old" in (me_refused(None, P.seal(CLEAN, ttl=-1)) or ""),
      [me_refused(DISPLAY_B64), me_refused(None, SIZES["768"])])
LAB = "lab-20260930-probe01"
spec = importlib.util.spec_from_file_location("master_eye", os.path.join(H.API, "master_eye.py"))
mm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mm)
H.MODS["master_eye"] = mm
MODEL_CALLS.clear()
before_lab = files_under(f"orders/{LAB}")
c, jme, _ = post("/api/master_eye", {"crop": CROP_B64, "preview": DISPLAY_B64, "pad": 1.12, "order": LAB, "eye": 1,
                                     "ticket": L.mint_ticket(store.unlock_kind(LAB))})
check("F3 POST /api/master_eye with the display copy as preview -> 400, no model call, nothing claimed or stored",
      c == 400 and not MODEL_CALLS and files_under(f"orders/{LAB}") == before_lab, (c, jme))
c, jme2, _ = post("/api/master_eye", {"crop": CROP_B64, "sealed": SIZES["560"], "pad": 1.12, "order": LAB, "eye": 1,
                                      "ticket": L.mint_ticket(store.unlock_kind(LAB))})
check("F4 POST /api/master_eye with a compose copy as sealed -> 400, nothing claimed",
      c == 400 and not MODEL_CALLS and files_under(f"orders/{LAB}") == before_lab, (c, jme2))
c, jme3, _ = post("/api/master_eye", {"crop": CROP_B64, "sealed": SEALED, "pad": 1.12, "order": LAB, "eye": 1,
                                      "ticket": L.mint_ticket("unlock")})
check("F5 sealed does not get past master_eye's unlock ticket (a plain unlock ticket -> 403)", c == 403, (c, jme3))

# ------------------------------------------------------------------
ok = sum(1 for _, x in RESULTS if x)
print(f"\n{ok} of {len(RESULTS)} passed")
sys.exit(0 if ok == len(RESULTS) else 1)
