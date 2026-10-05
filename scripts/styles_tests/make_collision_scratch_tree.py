# -*- coding: utf-8 -*-
"""Makes the recording tree of the collision goldens: a copy of the DG1 snapshot of the collision code (wave-dg1/final: designs/ and fx/) with the plate
library of the design round (wave-y3/plates_cx: the fits, the 1K files and, as a link, the raw 4K files) next to it, so that the scratch code draws what the
owner's boards were drawn with. The DG1 folder itself has no plates_cx, which makes its notch jets fall back to the parametric fan.

    set SNAPEYES_SCRATCH_DG1=<the wave-dg1/final folder>     set SNAPEYES_SCRATCH_Y3=<the wave-y3 folder>
    python scripts/styles_tests/make_collision_scratch_tree.py <a new folder>

Nothing in either scratch folder is written (the raw plates are linked, read only; the fits and the 1K files are copied because the prototype writes a missing
one). The folder then goes into SNAPEYES_COLLISION_REC for record_goldens_collision_scratch.py.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    dst = os.path.abspath(sys.argv[1])
    dg1 = os.environ.get("SNAPEYES_SCRATCH_DG1") or sys.exit("SNAPEYES_SCRATCH_DG1 is not set")
    y3 = os.environ.get("SNAPEYES_SCRATCH_Y3") or sys.exit("SNAPEYES_SCRATCH_Y3 is not set")
    if os.path.exists(dst) and os.listdir(dst):
        sys.exit(f"{dst} is not empty")
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    shutil.copytree(os.path.join(dg1, "designs"), os.path.join(dst, "designs"), ignore=ignore)
    shutil.copytree(os.path.join(dg1, "fx"), os.path.join(dst, "fx"), ignore=ignore)
    pc = os.path.join(dst, "plates_cx")
    os.makedirs(os.path.join(pc, "lod"), exist_ok=True)
    shutil.copy2(os.path.join(y3, "plates_cx", "fits.json"), os.path.join(pc, "fits.json"))
    shutil.copytree(os.path.join(y3, "plates_cx", "lod", "1k"), os.path.join(pc, "lod", "1k"))
    raw = os.path.join(y3, "plates_cx", "raw")
    link = os.path.join(pc, "raw")
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", link, raw], check=True, capture_output=True)
    else:
        os.symlink(raw, link, target_is_directory=True)
    print(f"made {dst}")


if __name__ == "__main__":
    main()
