# -*- coding: utf-8 -*-
"""Bake the restoration of the sample eye again, through the current chain, on this machine (ONE image-model call).

The page's "Try the sample" button shows public/assets/sample_eye_blue_restored.jpg, the restoration the live engine made of the AI-generated
sample eye once (2026-09-29: analyze, deglare, enhance artistic) and ships as a file instead of paying for it on every click; /api/enhance
{sample: true} takes exactly that file (api/enhance.py SAMPLE_SHA256). That file's profile fails the fill rule of the restoration gate
(fill_hard_edges: 127 of 180 sectors step by more than 25 L* inside the iris, the rule fails at 120), which held the Universe styles for a picture the
visitor did not take and raised the "Your eye needs a retake" card (QA of 2026-10-20). This script makes a candidate for a better file: the stored
client crop (public/assets/sample_eye_blue_before.jpg, what the page cut from the sample) goes through the deglare step (no model call: the
reflection call is off) and the steps of api/enhance.py _draw (the ONE model call, then the locks, the pupil repairs, the clean JPEG q93 and the
profile), exactly the first restoration /api/enhance makes; the second restoration of a failed lid rule is not made (SNAPEYES_RETRY2 is forced off
here), so one run is one call (about 0.07 USD). It prints the gate of the candidate and writes the candidate to --out; it changes nothing else.

    SNAPEYES_DEV_KEYFILE=1 python scripts/bake_sample.py --out <folder> --yes-spend

The key is read by api/_lib/iris.py (GEMINI_API_KEY, or C:\\kuriam\\.gemini-key with SNAPEYES_DEV_KEYFILE=1) and never printed. Without --yes-spend nothing is called.
After a good candidate (both rules ok, fidelity above the floor, looked at): copy it over the shipped file, put its sha256 into api/enhance.py SAMPLE_SHA256, and
run the suites (suites/README.md)."""
import argparse, base64, hashlib, json, os, sys, time

os.environ["SNAPEYES_RETRY2"] = "off"                     # read once by api/enhance.py at import: one run is one model call
os.environ.setdefault("SNAPEYES_TICKET_SECRET", "bake-sample-local")   # the tickets of this script's own two calls, never a deployment's
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api"))

import numpy as np
from PIL import Image
from _lib import iris as L
from _lib.styles import eye as EYE
from _lib.styles import gate as GATE
import deglare as DEG
import enhance as ENH

PAD = 1.12


def pupil_fraction(crop):
    """The pupil's radius as a share of the crop's side (what /api/analyze tells deglare): the dark core in the middle of the square."""
    g = np.asarray(crop.convert("L"), np.float32)
    s = g.shape[0]
    c = g[int(s * 0.3):int(s * 0.7), int(s * 0.3):int(s * 0.7)]
    dark = c < (float(np.percentile(c, 5)) + 22.0)
    return float(np.sqrt(dark.sum() / np.pi)) / s


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, help="folder for the candidate (sample_restored_candidate.jpg) and its numbers")
    ap.add_argument("--yes-spend", action="store_true", help="make the ONE image-model call")
    a = ap.parse_args()
    before = os.path.join(ROOT, "public", "assets", "sample_eye_blue_before.jpg")
    crop = Image.open(before).convert("RGB")
    pr = pupil_fraction(crop)
    print(f"client crop {crop.size[0]}x{crop.size[1]}, pupil {pr:.3f} of the side")
    buf = io_bytes(crop)
    ticket = L.mint_ticket()
    d = DEG.deglare({"crop": base64.b64encode(buf).decode(), "pad": PAD, "ticket": ticket, "pupil_r": pr, "glare_boxes": []})
    print(f"deglare: glare {d['glare_pct']}%, lid {d['lid_pct']}%, veil {d['veil_pct']}%, changed {d['changed']}")
    if not a.yes_spend:
        print("dry run: no model call (add --yes-spend)")
        return 0
    # the steps of api/enhance.py enhance() before the model call
    c = L.b64_to_pil(d["crop"])
    s = min(c.size)
    c = c.crop((0, 0, s, s))
    if s > L.WORK:
        c = c.resize((L.WORK, L.WORK), Image.LANCZOS); s = L.WORK
    r_frac = L.iris_radius_frac(PAD)
    c = L.mask_disk(c, PAD)
    source = c
    if s < L.SR_MAX_SIDE:
        c = L.sr_x4(c)
    base = c.resize((L.WORK, L.WORK), Image.LANCZOS)
    t0 = time.time()
    draw = ENH._draw("artistic", base, source, r_frac, PAD)             # THE model call
    print(f"restored in {time.time() - t0:.1f}s, fidelity {draw.fid:.3f} (floor {L.FIDELITY_FLOOR}), fallback {draw.fallback}")
    prof = EYE.profile_of_bytes(draw.clean, pad=PAD)
    report = {"sha256": hashlib.sha256(draw.clean).hexdigest(), "bytes": len(draw.clean), "fidelity": round(draw.fid, 3), "fallback": draw.fallback,
              "cls": prof.cls, "pupil": prof.pupil_cls, "gate": {r: prof.gate(r) for r in GATE.RULES}, "severity": GATE.severity(prof)}
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "sample_restored_candidate.jpg"), "wb") as f:
        f.write(draw.clean)
    with open(os.path.join(a.out, "sample_restored_candidate.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    print(json.dumps(report, indent=1))
    ok = not draw.fallback and all(report["gate"][r]["ok"] for r in GATE.RULES)
    print("CANDIDATE " + ("PASSES both rules" if ok else "fails a rule or fell back: keep the shipped file"))
    return 0 if ok else 3


def io_bytes(im):
    import io
    b = io.BytesIO()
    im.save(b, "JPEG", quality=95)
    return b.getvalue()


if __name__ == "__main__":
    sys.exit(main())
