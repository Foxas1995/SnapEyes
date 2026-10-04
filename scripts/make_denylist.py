# -*- coding: utf-8 -*-
"""Offline tool: makes scripts/hygiene_denylist.json, the hashes of the images that must never be committed.

    python scripts/make_denylist.py --scratch <the scratch tree of the design rounds> [--write]

What goes in (SHA-256 of the file bytes, with the path relative to the scratch tree as the label; no image and no pixel is copied):
  wave-y3/ref, wave-ref        the owner's reference works from another studio (measured, never shipped: a build check refuses their bytes)
  wave-g/live/out              the 29 calibration restorations of volunteers' eyes and pets and every stage that made them (biometric-adjacent)
  wave-o                       the stored real 4096 px masters made from them (not its copies of this repository's own files)
  suites/fixtures.sha256       the replies recorded from the owner's own photos (the private fixtures of the admin suites; the hash list is in git)
An image that the repository already holds on purpose (the site's published sample eye is one of the calibration photos) is left off the list.
scripts/check_styles.mjs (item 12) hashes every image of the repository and refuses one that is on the list. This is a tripwire against
committing the ORIGINALS by accident (git add of a wrong folder); it does not recognise a resized or re-encoded copy, and the rule behind it
(the style suites use the synthetic iris generator, scripts/styles_tests/synth_iris.py, never a real eye) is what keeps real eyes out.
Without --write it prints the counts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "hygiene_denylist.json")
IMAGES = re.compile(r"\.(png|jpe?g|webp|gif|bmp|tiff?)$", re.I)
FOLDERS = ["wave-y3/ref", "wave-ref", "wave-g/live/out", "wave-o"]
SKIP = {"wave-o": {"applytest", "base", "fixer", "guards", "work"}}     # copies of this repository's own files made while testing, not masters


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def repo_hashes():
    """The hashes of the images this repository holds today (the published samples, the backgrounds, the plates): never on the deny list."""
    out = set()
    for root, ds, fs in os.walk(ROOT):
        ds[:] = [d for d in ds if d not in ("node_modules", ".git", "dist", "__pycache__", "private", "out") and not (root == ROOT and d.startswith("."))]
        for f in fs:
            if IMAGES.search(f):
                out.add(sha256_of(os.path.join(root, f)))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--scratch", required=True, help="the scratch tree that holds wave-y3, wave-ref, wave-g and wave-o")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    deny, counts = {}, {}
    mine = repo_hashes()
    for folder in FOLDERS:
        base = os.path.join(a.scratch, *folder.split("/"))
        if not os.path.isdir(base):
            sys.exit(f"not found: {base}")
        n = 0
        for root, ds, fs in os.walk(base):
            if root == base:
                ds[:] = [d for d in ds if d not in SKIP.get(folder, ())]
            for f in sorted(fs):
                if IMAGES.search(f):
                    p = os.path.join(root, f)
                    h = sha256_of(p)
                    if h in mine:
                        continue
                    deny.setdefault(h, os.path.relpath(p, a.scratch).replace("\\", "/"))
                    n += 1
        counts[folder] = n
    fx = os.path.join(ROOT, "suites", "fixtures.sha256")
    n = 0
    if os.path.isfile(fx):
        for line in open(fx, encoding="utf-8"):
            m = re.match(r"^([0-9a-f]{64})\s+\*?(.+?)\s*$", line)
            if m:
                deny.setdefault(m.group(1), "suites/private/fixtures/" + m.group(2).replace("\\", "/").rsplit("/", 1)[-1])
                n += 1
    counts["suites/fixtures.sha256"] = n
    for k, v in counts.items():
        print(f"{k:26s} {v:5d} files")
    print(f"{len(deny)} distinct hashes")
    if a.write:
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"about": "SHA-256 of the images that never enter the repository: the owner's reference works, the calibration irises and their masters, the private "
                                "fixtures. Made by scripts/make_denylist.py; read by scripts/check_styles.mjs (item 12). Hashes and labels only.",
                       "sources": counts, "sha256": dict(sorted(deny.items(), key=lambda kv: kv[1]))}, f, indent=1)
            f.write("\n")
        print("wrote", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
