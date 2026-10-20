# -*- coding: utf-8 -*-
"""The thin lid of a light iris, filled like any lid inside /api/deglare (2026-10-20, the owner's insight 2: "the restoration added brown pigment
where my eyelid covered the iris"; api/_lib/lidcap.py has the measurements). iris.lid_mask leaves a thin rim lid alone, so on a blue, grey or
green iris the lid skin went to the image model and iris.chroma_lock kept its colour; now the lid analyze already measures (api/_lib/coverage.py)
is filled from the same iris at the same radius, behind SNAPEYES_LIDCAP (on by default).
    section 1  the switch: SNAPEYES_LIDCAP read once at import in a fresh interpreter (on unless off, 0, false or no, any case, BOM safe), and in
               one file of api/ only
    section 2  coverage.lid_cover is unchanged by the refactor that lets lidcap read the same lids (_lids): equal to a verbatim copy of the
               function as it was, on the fixture crops and on painted synthetic eyes, at two sizes each
    section 3  the owner's own eye (the private fixture founder_215208: a thin lower lid over a grey-green iris): iris.lid_mask finds no lid;
               with the switch on deglare fills the cap (lid_pct, lid_cap in the reply), the colour of the cap is the iris' own at the same radius
               (the photo there is the lid's skin), the mask stays inside 1.02 iris radii and out of the pupil, and the curved part is bounded
    section 4  what does not change: the switch off is the path of before (lid_pct 0, no lid_cap), an eye with no cap (founder_215120) gives the
               same bytes with the switch on and off, and a failure inside the cap leaves the crop as the switch off leaves it
Needs the private fixtures (suites/README.md): run by suites/run_main.sh as the entry v3lidcap, SKIPPED (exit 77) where they are missing.
    python test_lidcap.py       prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure"""
import io
import json
import math
import os
import subprocess
import sys

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(REPO, "api")
SP = os.environ.get("SNAPEYES_SP") or ""
FIX = os.environ.get("SNAPEYES_FIXTURES") or os.path.join(SP, "wave-b", "try-multi", "fixtures")

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   <- {str(detail)[:600]}"), flush=True)


def section(title):
    print(f"\n== {title}", flush=True)


if not os.path.isfile(os.path.join(FIX, "crop_founder_215208.jpg")):
    print("SKIPPED: the private image fixtures are missing (suites/README.md, SNAPEYES_FIXTURES)")
    sys.exit(77)
for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "AWS_", "NOW_", "LAMBDA_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP", "SNAPEYES_FIXTURES"):
            os.environ.pop(k)
os.environ["SNAPEYES_TICKET_SECRET"] = "suite-v3lidcap-local-secret-0123456789"
sys.path.insert(0, API)
sys.path.insert(0, HERE)
os.environ["PYTHONIOENCODING"] = "utf-8"
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
import synth_iris as SI  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import coverage as CV  # noqa: E402
from _lib import lidcap as LC  # noqa: E402
import deglare as DG  # noqa: E402


def read(rel):
    with open(os.path.join(REPO, *rel.split("/")), encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")


def fixture(name):
    a = json.load(open(os.path.join(FIX, f"analyze_{name}.json"), encoding="utf-8"))
    crop = Image.open(os.path.join(FIX, f"crop_{name}.jpg")).convert("RGB")
    return crop, {"pad": a["pad"], "pupil_r": a["pupil_r"], "glare_boxes": a.get("glare_boxes_crop") or []}


def run_deglare(crop, body, on=True):
    was = LC.CAP_ON
    LC.CAP_ON = on
    try:
        res = DG.deglare(dict(body, crop=L.pil_to_b64(crop, "JPEG", 95), ticket=L.mint_ticket("work")))
    finally:
        LC.CAP_ON = was
    return res


# ---- coverage.lid_cover as it was before this change (verbatim: api/_lib/coverage.py of e2754c1), the reference of "unchanged"
def lid_cover_ref(im, cx, cy, r, pupil_r=None):
    if r < 4:
        return None
    Q = CV._prep(im, cx, cy, r, pupil_r)
    if Q is None:
        return None
    out = []
    for i in range(CV.NDIR):
        phi = i * 360.0 / CV.NDIR
        cl = CV._classes(Q, phi)
        out.append((phi,) + (CV._cap(Q, phi, *cl) if cl is not None else (0.0, 0.0, 0.0, 0)))
    n = len(out)
    peaks = [i for i in range(n) if out[i][3] > 0 and out[i][3] >= out[i - 1][3] and out[i][3] >= out[(i + 1) % n][3]]
    reach = int(CV.NEAR / (360.0 / n))
    lids = set()
    for p in peaks:
        best = p
        for dj in range(-reach, reach + 1):
            j = (p + dj) % n
            if out[j][3] >= CV.NEAR_FRAC * out[p][3] and out[j][1] > out[best][1]:
                best = j
        lids.add(best)
    if not lids:
        return {"wedge_pct": 0.0, "covered_pct": 0.0, "side": None, "tilt": None, "depth": 0.0}
    lids = sorted(lids)
    i1 = max(lids, key=lambda i: out[i][1])
    other = [i for i in lids if abs((out[i][0] - out[i1][0] + 180) % 360 - 180) >= 90]
    i2 = max(other, key=lambda i: out[i][1]) if other else i1
    cov = np.zeros(len(Q["Xd"]), bool)
    for i in {i1, i2}:
        c, s = math.cos(math.radians(out[i][0])), math.sin(math.radians(out[i][0]))
        cov |= (Q["Xd"] * c + Q["Yd"] * s) > CV.RIM - out[i][4] * CV.DT
    phi = out[i1][0]
    side = "top" if 225 <= phi <= 315 else "bottom" if 45 <= phi <= 135 else "left" if 135 < phi < 225 else "right"
    return {"wedge_pct": round(float(out[i1][1]), 1), "covered_pct": round(float(100.0 * cov.sum() / Q["ndisc"]), 1),
            "side": side, "tilt": int(round(phi)), "depth": round(float(out[i1][2]), 2)}


def painted(kind, lower, seed):
    """A synthetic photo square: synth_iris's iris on a sclera, a lid of textured skin over the upper (or lower) rim with a dark line under its
    margin, carrying on over the sclera outside the circle. Only for the refactor's equality: what coverage reads on it does not matter."""
    side = 480
    iris = np.asarray(SI.make(kind, "round", False, False, seed, side), np.float32)
    R = SI.R_FRAC * side
    ax = (np.arange(side) - side / 2 + 0.5) / R
    X, Y = np.meshgrid(ax, ax)
    rho = np.hypot(X, Y)
    rng = np.random.Generator(np.random.PCG64(seed))
    sclera = np.array([222.0, 214.0, 208.0]) + rng.uniform(-6, 6, (side, side, 1))
    a = np.clip((1.0 - rho) / 0.02, 0, 1)[..., None]
    out = iris * a + sclera * (1 - a)
    tex = rng.uniform(-1, 1, (side, side))
    skin = np.array([150.0, 112.0, 104.0])[None, None, :] * (1.0 + 0.10 * tex[..., None])
    margin = (0.84 - 0.35 * X * X) if lower else -(0.84 - 0.35 * X * X)
    beyond = (Y > margin) if lower else (Y < margin)
    out = np.where(beyond[..., None], skin, out)
    out = np.where(((np.abs(Y - margin) < 0.035) & ~beyond)[..., None], np.array([58.0, 44.0, 40.0]), out)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def lab(im, n=512):
    return L.srgb_to_lab(np.asarray(im.convert("RGB").resize((n, n), Image.BOX), np.float32))


# ======================================================================================================== 1
section("1  the switch")
probe = ("import os, sys; sys.path.insert(0, %r); from _lib import lidcap as LC; print('ON' if LC.CAP_ON else 'OFF')" % API)
cases = {None: "ON", "": "ON", "on": "ON", "1": "ON", "yes": "ON", "anything": "ON", "off": "OFF", "OFF": "OFF", "0": "OFF", "false": "OFF",
         "No": "OFF", "\ufeffoff": "OFF", " off ": "OFF"}
got = {}
for v, want in cases.items():
    env = {k: x for k, x in os.environ.items() if k != "SNAPEYES_LIDCAP"}
    if v is not None:
        env["SNAPEYES_LIDCAP"] = v
    r = subprocess.run([sys.executable, "-c", probe], env=env, capture_output=True, text=True, timeout=120)
    got[repr(v)] = (r.stdout.strip(), want)
check("SNAPEYES_LIDCAP: on when unset, empty or anything else; off for off, 0, false or no (any case, spaces, a BOM), read once at import",
      all(a == b for a, b in got.values()), got)
names = [f for f in sorted(os.listdir(API)) + ["_lib/" + x for x in sorted(os.listdir(os.path.join(API, "_lib")))] if f.endswith(".py")]
users = [f for f in names if "SNAPEYES_LIDCAP" in read("api/" + f)]
check("the switch is read in api/_lib/lidcap.py and nowhere else in api/", users == ["_lib/lidcap.py"], users)
src = read("api/deglare.py")
check("deglare reads the cap only when iris.lid_mask found no lid (lid_pct <= 0), with the analyze pupil, at the working size",
      "if lid_pct <= 0:" in src and "LC.cap_mask(raw, pad, pr, S)" in src)

# ======================================================================================================== 2
section("2  coverage.lid_cover unchanged")
same, diff = 0, []
inputs = [(n, *fixture(n)) for n in ("founder_215208", "founder_215120", "founder_215102", "sample_ai")]
inputs += [(f"painted_{k}_{'lower' if lo else 'upper'}", painted(k, lo, 5 + i), {"pad": 1.12, "pupil_r": 0.13})
           for i, (k, lo) in enumerate([("blue", False), ("grey", True), ("green", False), ("amber", True), ("dark_brown", False)])]
for name, im, b in inputs:
    for scale in (1.0, 0.75):
        x = im if scale == 1.0 else im.resize((int(im.size[0] * scale),) * 2, Image.LANCZOS)
        n = x.size[0]
        a1 = lid_cover_ref(x, n / 2.0, n / 2.0, n * L.iris_radius_frac(b["pad"]), b["pupil_r"])
        a2 = CV.lid_cover(x, n / 2.0, n / 2.0, n * L.iris_radius_frac(b["pad"]), b["pupil_r"])
        if a1 == a2:
            same += 1
        else:
            diff.append((name, scale, a1, a2))
check(f"lid_cover gives the very same answer as the function before the change on {same + len(diff)} squares (4 fixture crops, 5 painted eyes, 2 sizes)",
      not diff and same == 2 * len(inputs), diff)
crop8, body8 = fixture("founder_215208")
n8 = crop8.size[0]
c8 = CV.lid_cover(crop8, n8 / 2.0, n8 / 2.0, n8 * L.iris_radius_frac(body8["pad"]), body8["pupil_r"])
check("on the owner's 215208 coverage reads a thin lower lid (the same 1.9 % analyze read on the photo)",
      c8 and c8["side"] == "bottom" and 1.0 <= c8["wedge_pct"] <= 4.0, c8)

# ======================================================================================================== 3
section("3  the owner's own eye 215208: the thin lower lid is filled from his iris")
S8 = L.WORK
raw8 = crop8.resize((min(n8, L.WORK),) * 2, Image.LANCZOS) if n8 > L.WORK else crop8
lm = L.lid_mask(raw8, L.iris_radius_frac(body8["pad"]) * raw8.size[0], size=raw8.size[0], pupil_rho=body8["pupil_r"] / L.iris_radius_frac(body8["pad"]))
check("iris.lid_mask finds no lid on it (a thin rim lid, left alone on purpose: the reason the skin reached the model)", lm[2] == 0.0, lm[2])
got = LC.cap_mask(crop8, body8["pad"], body8["pupil_r"], 1024)
check("lidcap.cap_mask reads the cap and gives a mask (hard, soft, pct, caps)", got is not None and got[2] > 0 and got[3], None if got is None else got[2:])
if got is not None:
    hard, soft, pct, caps = got
    R = L.iris_radius_frac(body8["pad"]) * 1024
    ax = (np.arange(1024) - 512 + 0.5) / R
    rho = np.hypot(ax[None, :], ax[:, None])
    m = hard > 0
    pr = body8["pupil_r"] / L.iris_radius_frac(body8["pad"])
    check("the mask stays inside 1.02 iris radii and out of the pupil and the inner 0.25 (as lid_mask's)",
          not (m & (rho >= 1.02)).any() and not (m & (rho <= max(0.25, pr * 1.04))).any())
    check("the soft edge only reaches outwards: 1 on the mask, 0 to 1 elsewhere, 0 in the pupil keep",
          float(soft[m].min()) == 1.0 and float(soft.max()) <= 1.0 and float(soft.min()) >= 0.0 and not (soft[rho <= max(0.25, pr * 1.04)] > 0).any())
    check("its share of the disc is between the straight cap and CAP_MAX_GROWTH times it, and under CAP_PCT[1]",
          caps[0][1] * 0.5 <= pct <= LC.CAP_MAX_GROWTH * max(caps[0][1], 1.0) + 2.0 and pct < LC.CAP_PCT[1], (pct, caps))
on = run_deglare(crop8, body8, True)
off = run_deglare(crop8, body8, False)
check("with the switch on the reply says the lid was filled: lid_pct over 0 and lid_cap [[tilt, pct]]",
      on["lid_pct"] > 0 and isinstance(on.get("lid_cap"), list) and on["lid_cap"] and on["lid_cap"][0][0] in range(60, 150), {k: on.get(k) for k in ("lid_pct", "lid_cap")})
check("with the switch off it is the reply of before: lid_pct 0 and no lid_cap", off["lid_pct"] == 0.0 and "lid_cap" not in off, {k: off.get(k) for k in ("lid_pct", "lid_cap")})
# the colour inside the straight cap against the iris at the same radius, at least 60 degrees round from it (the measure of lidcap.py's module text)
tilt, depth = c8["tilt"], c8["depth"]
N = 512
R = N * L.iris_radius_frac(body8["pad"])
ax = (np.arange(N) - N / 2 + 0.5) / R
X, Y = np.meshgrid(ax, ax)
rho, ang = np.hypot(X, Y), np.degrees(np.arctan2(Y, X)) % 360.0
cap = ((X * math.cos(math.radians(tilt)) + Y * math.sin(math.radians(tilt))) > CV.RIM - depth) & (rho > 0.3) & (rho < 0.95)
away = (np.abs((ang - tilt + 180) % 360 - 180) >= 60) & (rho > 0.3) & (rho < 0.95)
bins = np.minimum((rho / 0.05).astype(int), 19)


def off_iris(img):
    a = lab(img, N)
    ref = np.full((20, 3), np.nan)
    for bb in range(20):
        mm = away & (bins == bb) & (a[..., 0] > 3) & (a[..., 0] < 85)
        if mm.sum() >= 30:
            ref[bb] = np.median(a[mm], 0)
    have = np.nonzero(~np.isnan(ref[:, 0]))[0]
    for bb in range(20):
        if np.isnan(ref[bb, 0]):
            ref[bb] = ref[have[np.argmin(np.abs(have - bb))]]
    d = (a - ref[bins])[cap]
    return float(np.hypot(np.median(d[:, 1]), np.median(d[:, 2])))


d_photo = off_iris(crop8)
d_off = off_iris(L.b64_to_pil(off["crop"]))
d_on = off_iris(L.b64_to_pil(on["crop"]))
check(f"the photo's lid skin sits {d_photo:.1f} a*b* off his iris at its radius, the crop deglare sends to the model with the switch off {d_off:.1f} (the brown the restoration kept)",
      d_photo >= 8.0 and d_off >= 8.0, (d_photo, d_off))
check(f"with the switch on the cap of the crop is his iris' own colour: {d_on:.1f} a*b* off it (at most 3)", d_on <= 3.0, d_on)
sample, bs = fixture("sample_ai")
s_on, s_off = run_deglare(sample, bs, True), run_deglare(sample, bs, False)
check("the AI-generated sample's crop (a thin lower lid too) is filled the same way with the switch on, and is the reply of before with it off",
      s_on["lid_pct"] > 0 and s_on.get("lid_cap") and s_off["lid_pct"] == 0.0 and "lid_cap" not in s_off, (s_on.get("lid_cap"), s_off["lid_pct"]))

# ======================================================================================================== 4
section("4  what does not change")
crop0, body0 = fixture("founder_215120")
a_on, a_off = run_deglare(crop0, body0, True), run_deglare(crop0, body0, False)
check("an eye with no cap (founder_215120): the switch on gives the very same bytes and reply as the switch off",
      a_on == a_off and "lid_cap" not in a_on, sorted(set(a_on) ^ set(a_off)))
real = CV._lids
CV._lids = lambda Q: (_ for _ in ()).throw(RuntimeError("probe"))
try:
    broken = run_deglare(crop8, body8, True)
finally:
    CV._lids = real
check("a failure inside the cap leaves the crop as the switch off leaves it (never a failed deglare call)",
      broken["crop"] == off["crop"] and broken["lid_pct"] == 0.0 and "lid_cap" not in broken)
check("the module text says where the brown came from and what the switch does", all(w in read("api/_lib/lidcap.py") for w in ("chroma_lock", "SNAPEYES_LIDCAP=off", "lid_drift")))

ok = sum(RESULTS)
print(f"\n{ok} of {len(RESULTS)} passed")
sys.exit(0 if ok == len(RESULTS) else 1)
