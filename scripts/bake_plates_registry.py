# -*- coding: utf-8 -*-
"""Offline tool (never in a function, never in a bundle: scripts/ is excluded): bakes api/_lib/plates_registry.py and copies the 1K
plate files into api/_assets/plates/ from the scratch plate library of the design rounds.

    python scripts/bake_plates_registry.py --y2 <wave-y2/plates> --y3 <wave-y3> [--write]

The design rounds kept three registries in three formats (the plate workflow's plates.json for CLOUD, CROWN, FLAME and SPIRAL;
plates_uv/plates.json for DUST and MILKY; plates_cx/fits.json and a folder of raw files for the collision JET and RIVER plates), and the
engines fitted, scanned and cached at run time. A function bundle is read-only and a warm instance renders for hours, so everything an
engine asked of the plate folders is decided here, once, and written down:

  usable   the plate is one an engine may pick. CLOUD, CROWN: every keeper (the engine's own filters by variable and void apply at pick
           time). FLAME: the v3 plates only (the v2 plates are soft glows clipped to white). SPIRAL: the plates with a crisp circular void
           (measured on the 1K file: the radius at which the luminance first exceeds 0.12 has an angular deviation under 0.4 percent of
           r0 and a 10 to 50 percent edge under 2 percent of r0; uni_plates.spiral_plates). MILKY: not the three plates drawn in visible
           tiles. JET and RIVER: those that pass the collision accept rules (cx_plates.qa), the Pro 4K ones when there are any.
           A plate that is not usable keeps its record and ships no file.
  fit      JET and RIVER: the fitted source point, axis, reach and width (cx_plates fit_jet, fit_river).
  crisp    SPIRAL: the measurement above.
  1K file  bundled with the four rendering functions (api/_assets/plates/<family>/<file>); sha256 and size below. The collision plates
           are used as luminance at 1K only (no 4K file leaves the archive); their 1K files are made here from the raw files exactly
           as the prototype's _plate_lum did (convert to L, LANCZOS to 1024 px, PNG level 3).
  4K file  private storage (plates/v1/<family>/<file>), fetched by id at a master that needs it, sha256 checked; the registry holds its
           size and hash, and only for the plates an engine can fetch at all (needs_4k: the engines' own filters, so CLOUD is the
           Powder-eligible subset); the others are read at 1K or not at all. FLAKE, SHARD, DROPS and BUTTERFLY sheets are not read at run time (the atlases were built from them) and are not here.
  since    the plates version a plate arrived in (1: the library of the design rounds); until: 0, or the first version that ignores it.
           The registry is append-only: nothing is deleted, a retired plate gets an until, so an old plates version picks the same plate.

The generated file is JSON inside Python (as api/_lib/styles_registry.py is): ASCII, double quotes, 1 and 0, [] and {} for nothing, and
the literal ends the file. Without --write it only prints what it would do.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "api", "_lib", "plates_registry.py")
BUNDLE = os.path.join(ROOT, "api", "_assets", "plates")
ATLAS_DIR = os.path.join(ROOT, "api", "_assets", "atlas")
# the two sprite atlases (built offline from the FLAKE, SHARD and DROPS sheets): the prototype kept four byte identical copies of the
# chips atlas (one per family); one is shipped. file name in the scratch designs/data folder -> file name in the bundle
ATLASES = {"chips": ("chips_atlas.npz", "chips.npz"), "drops": ("drops_atlas.npz", "drops.npz")}

PLATES_VERSION = 1
DEPENDENCIES_MIB = 126        # the Linux wheels of requirements.txt (suites/baseline.md, from the PyPI zip directories: 125.6); replaced by V1
MILKY_BLOCKED = ("P-UV-MILKY__band-high_stars-dense__v1__pro4K__t0", "P-UV-MILKY__band-high_stars-sparse__v1__pro4K__t0",
                 "P-UV-MILKY__band-high_stars-sparse__v1__pro4K__t1")
FAMILIES = {
    # store4k: the 4K files of this family go to private storage; release1: a style of the first release needs them
    "P-SN-CLOUD": {"store4k": 1, "release1": 1, "source": "y2"},
    "P-SP-CROWN": {"store4k": 1, "release1": 1, "source": "y2"},
    "P-EL-FLAME": {"store4k": 1, "release1": 0, "source": "y2"},
    "P-DN-SPIRAL": {"store4k": 1, "release1": 1, "source": "y2"},
    "P-UV-DUST": {"store4k": 1, "release1": 0, "source": "uv"},
    "P-UV-MILKY": {"store4k": 1, "release1": 0, "source": "uv"},
    "P-CX-JET": {"store4k": 0, "release1": 0, "source": "cx"},
    "P-CX-RIVER": {"store4k": 0, "release1": 0, "source": "cx"},
}


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fl(x):
    """A float as it is: a fit, a void circle or an angle is written with the full precision the prototype read, so that a placement
    computed from the registry is the very same number as in the prototype. json writes the shortest text that reads back exactly."""
    return None if x is None else float(x)


def spiral_crisp(path_1k, void):
    """uni_plates.spiral_plates, one plate: a crisp, circular void on the 1K file."""
    im = np.asarray(Image.open(path_1k).convert("L"), np.float32) / 255.0
    cx, cy, r0 = void
    n = im.shape[0]
    ang = np.linspace(0, 2 * np.pi, 180, endpoint=False)
    rs = np.linspace(0.6 * r0, 1.6 * r0, 200) * n
    X = cx * n + np.outer(np.cos(ang), rs)
    Y = cy * n + np.outer(np.sin(ang), rs)
    prof = im[np.clip(Y.astype(int), 0, n - 1), np.clip(X.astype(int), 0, n - 1)]
    edge = np.array([rs[np.argmax(prof[i] > 0.12)] if (prof[i] > 0.12).any() else np.nan for i in range(len(ang))])
    mp = prof.mean(0)
    w = (rs[np.argmax(mp > 0.5 * mp.max())] - rs[np.argmax(mp > 0.1 * mp.max())]) / (r0 * n)
    sd = float(np.nanstd(edge) / (r0 * n))
    return bool(sd < 0.004 and w < 0.02)


def cx_qa(p):
    """cx_plates.qa: the accept rules of the collision plates."""
    if p["fam"] == "JET":
        up = abs(((p["axis"] + math.pi / 2) + math.pi) % (2 * math.pi) - math.pi)
        return (p["sy"] >= 0.85 and abs(p["sx"] - 0.5) <= 0.12 and math.radians(18) <= p["half"] <= math.radians(75) and p["black"] >= 0.45
                and up < math.radians(28) and p.get("glare", 0) < 0.10)
    a = abs(math.degrees(p["axis"]) % 180)
    ok_axis = min(abs(a - 35), abs(a - 145)) <= 22
    return ok_axis and 0.10 <= p["width"] <= 0.62 and p["black"] >= 0.40


def lum1k(path):
    """cx_plates._lum(path, 1024) as PNG bytes (level 3), what _plate_lum wrote for the 1K LOD."""
    im = Image.open(path).convert("L")
    if im.size[0] != 1024:
        im = im.resize((1024, 1024), Image.LANCZOS if im.size[0] > 1024 else Image.BICUBIC)
    a = np.asarray(im, np.float32) / 255.0
    import io
    b = io.BytesIO()
    Image.fromarray((a * 255 + 0.5).astype(np.uint8)).save(b, "PNG", compress_level=3)
    return b.getvalue()


def needs_4k(rec):
    """Does an engine ever fetch the 4K file of this plate at a master? The filters are the engines' own (singles_powder.pick_cloud, the
    Deep Field and Vortex looks): only those plates go to private storage. The collision haze and the previews read 1K files only."""
    fam = rec["family"]
    if not rec["usable"] or not FAMILIES[fam]["store4k"]:
        return False
    if fam == "P-SN-CLOUD":
        return (rec["variables"].get("black") in ("30", "45", "60") and "strong_angle" in rec and rec.get("strength", 0) >= 0.08
                and rec.get("void_diam", 0) >= 0.40)
    if fam == "P-DN-SPIRAL":
        return rec["void"][2] >= 0.20
    if fam == "P-UV-DUST":
        return rec["void"][2] >= 0.185
    return True


def collect(y2, y3):
    """[(id, record, source 1K path, 1K file name, source 4K path or None, 4K file name)] sorted by family and id."""
    out = []
    # ---- the plate workflow's registry: CLOUD, CROWN, FLAME, SPIRAL
    reg = json.load(open(os.path.join(y2, "plates.json"), encoding="utf-8"))["plates"]
    for pid in sorted(reg):
        v = reg[pid]
        fam = v["family"]
        if FAMILIES.get(fam, {}).get("source") != "y2":
            continue
        k1 = os.path.join(y2, v["paths"]["k1"])
        k4 = os.path.join(y2, v["paths"]["k4"])
        void = v.get("void") or {}
        rec = {"family": fam, "since": PLATES_VERSION, "until": 0, "usable": 1, "mono": 1 if v["mono"] else 0, "kind": v["kind"],
               "variables": {k: str(x) for k, x in sorted(v["variables"].items())}, "score": fl(v.get("score") or 0.0)}
        if void:
            rec["void"] = [fl(void["cx"]), fl(void["cy"]), fl(void["r0"])]
            rec["void_diam"] = fl(v.get("void_diam"))
        if v.get("strong_angle") is not None:
            rec["strong_angle"] = fl(v["strong_angle"])
        rec["strength"] = fl(v.get("strength") or 0.0)
        if fam == "P-EL-FLAME" and "__v3__" not in pid:
            rec["usable"] = 0
        if fam == "P-DN-SPIRAL":
            rec["crisp"] = 1 if spiral_crisp(k1, rec["void"]) else 0
            rec["usable"] = rec["crisp"]
        out.append((pid, rec, k1, os.path.basename(k1), k4, os.path.basename(k4)))
    # ---- the universe registry: DUST, MILKY
    uv = json.load(open(os.path.join(y3, "plates_uv", "plates.json"), encoding="utf-8"))["plates"]
    for pid in sorted(uv):
        v = uv[pid]
        fam = v["family"]
        k1 = os.path.join(y3, "plates_uv", v["k1"])
        k4 = os.path.join(y3, "plates_uv", v["k4"])
        rec = {"family": fam, "since": PLATES_VERSION, "until": 0, "usable": 0 if pid in MILKY_BLOCKED else 1, "mono": 1, "kind": "uv",
               "variables": {}, "score": 0.0}
        if "void" in v:
            rec["void"] = [fl(v["void"]["cx"]), fl(v["void"]["cy"]), fl(v["void"]["r0"])]
            rec["void_diam"] = fl(2 * v["void"]["r0"])
        extra = {k: (fl(x) if isinstance(x, float) else x) for k, x in v.items() if k not in ("id", "family", "k1", "k4", "void")}
        extra = {k: ([fl(y) for y in x] if isinstance(x, list) else x) for k, x in extra.items()}
        rec["extra"] = extra
        out.append((pid, rec, k1, os.path.basename(k1), k4, os.path.basename(k4)))
    # ---- the collision plates: the fits and the raw files
    fits = json.load(open(os.path.join(y3, "plates_cx", "fits.json"), encoding="utf-8"))
    by_fam = {}
    for key, f in fits.items():
        by_fam.setdefault(f["fam"], []).append((key, f))
    for fam, items in sorted(by_fam.items()):
        pro = [k for k, f in items if "pro4K" in k and cx_qa(f)]
        ok = pro or [k for k, f in items if cx_qa(f)]
        for key, f in sorted(items):
            raw = os.path.join(y3, f["path"].replace("/", os.sep))
            fit = {k: (fl(x) if isinstance(x, float) else (1 if x is True else (0 if x is False else x))) for k, x in f.items() if k not in ("path",)}
            rec = {"family": f"P-CX-{fam}", "since": PLATES_VERSION, "until": 0, "usable": 1 if key in ok else 0, "mono": 1, "kind": fam.lower(),
                   "variables": {}, "score": 0.0, "fit": fit}
            out.append((key, rec, raw if rec["usable"] else None, key + ".png", None, ""))
    out.sort(key=lambda t: (t[1]["family"], t[0]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--y2", required=True, help="the plate workflow folder (wave-y2/plates of the scratch tree)")
    ap.add_argument("--y3", required=True, help="the wave-y3 folder of the scratch tree (plates_uv, plates_cx)")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    rows = collect(a.y2, a.y3)
    plates = {}
    todo = []
    for pid, rec, src1, name1, src4, name4 in rows:
        if rec["usable"]:
            if rec["family"].startswith("P-CX"):
                data = lum1k(src1)
                rec["k1"] = {"file": name1, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "px": 1024}
                todo.append((rec["family"], name1, data))
            else:
                rec["k1"] = {"file": name1, "bytes": os.path.getsize(src1), "sha256": sha256_of(src1), "px": 1024}
                todo.append((rec["family"], name1, src1))
            if src4 and needs_4k(rec):
                rec["k4"] = {"file": name4, "bytes": os.path.getsize(src4), "sha256": sha256_of(src4), "px": 4096}
            else:
                rec["k4"] = {}
        else:
            rec["k1"] = {}
            rec["k4"] = {}
        plates[pid] = rec
    fam_count = {}
    for rec in plates.values():
        c = fam_count.setdefault(rec["family"], [0, 0, 0, 0])
        c[0] += 1
        if rec["usable"]:
            c[1] += 1
            c[2] += rec["k1"]["bytes"]
            c[3] += rec["k4"].get("bytes", 0)
    for fam, (n, u, b1, b4) in sorted(fam_count.items()):
        print(f"{fam:14s} {n:3d} plates, {u:3d} usable, 1K {b1 / 1048576:6.2f} MiB, 4K {b4 / 1048576:7.2f} MiB")
    print(f"total 1K {sum(c[2] for c in fam_count.values()) / 1048576:.2f} MiB, 4K {sum(c[3] for c in fam_count.values()) / 1048576:.2f} MiB, {len(plates)} plates")
    if not a.write:
        return
    if os.path.isdir(BUNDLE):
        shutil.rmtree(BUNDLE)
    for fam, name, src in todo:
        d = os.path.join(BUNDLE, fam)
        os.makedirs(d, exist_ok=True)
        if isinstance(src, bytes):
            open(os.path.join(d, name), "wb").write(src)
        else:
            shutil.copyfile(src, os.path.join(d, name))
    atlas = {}
    os.makedirs(ATLAS_DIR, exist_ok=True)
    for key, (src_name, dst_name) in ATLASES.items():
        src = os.path.join(a.y3, "designs", "data", src_name)
        shutil.copyfile(src, os.path.join(ATLAS_DIR, dst_name))
        atlas[key] = {"file": dst_name, "bytes": os.path.getsize(src), "sha256": sha256_of(src)}
    lit = {"atlas": atlas, "families": FAMILIES, "plates": plates}
    body = json.dumps(lit, indent=1, sort_keys=True, ensure_ascii=True)
    head = '''# -*- coding: utf-8 -*-
"""The plate library as the engines read it: BAKED OFFLINE by scripts/bake_plates_registry.py from the design rounds' registries, never
edited by hand, never fitted, scanned or written at run time (a function's folder is read-only). api/_lib/styles/plates.py is the only
reader. JSON inside Python, as styles_registry.py is: ASCII, double quotes, 1 and 0, [] and {} for nothing, the literal ends the file.

  PLATES_REGISTRY_SCHEMA   1
  PLATES_VERSION           the version of the library (the same number as styles_registry.PLATES_VERSION: a build check compares them)
  DEPENDENCIES_MIB         the Linux wheels of requirements.txt in MiB (suites/baseline.md): added to the bytes of api/ by the build check of the
                           function size (scripts/check_styles.mjs, item 9). Replaced by the measured figure when V1 has one
  atlas                    {chips, drops: {file, bytes, sha256}}: the two sprite atlases in api/_assets/atlas/
  families                 {family: {store4k, release1, source}}: store4k 1 when the family's 4K files go to private storage (the collision
                           plates are used at 1K only), release1 1 when a style of the first release needs them
  plates                   {id: {family, since, until, usable, mono, kind, variables, score, void [cx, cy, r0], void_diam, strong_angle,
                           strength, k1 {file, bytes, sha256, px}, k4 {file, bytes, sha256, px}, fit, crisp, extra}}
    since / until          the plates version a plate arrived in, and 0 or the first version that ignores it: the library is append-only, a
                           plate added later never changes the pick of an older version, a retired plate keeps its record
    usable                 1 when an engine may pick it; 0 keeps the record and ships no file (the v2 flames, the soft spirals, the vetoed
                           milky ways, the collision plates that fail the accept rules)
    k1                     the 1024 px file in the bundle: api/_assets/plates/<family>/<file>
    k4                     the 4096 px file in private storage: plates/v1/<family>/<file> (empty: none, or not read at 4K)
"""
'''
    text = head + f"PLATES_REGISTRY_SCHEMA = 1\nPLATES_VERSION = {PLATES_VERSION}\nDEPENDENCIES_MIB = {DEPENDENCIES_MIB}\nPLATES_REGISTRY = {body}\n"
    open(OUT, "w", encoding="utf-8", newline="\n").write(text)
    print("wrote", os.path.relpath(OUT, ROOT), f"({len(text) // 1024} KiB) and {len(todo)} files in", os.path.relpath(BUNDLE, ROOT))


if __name__ == "__main__":
    main()
