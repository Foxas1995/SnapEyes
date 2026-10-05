# -*- coding: utf-8 -*-
"""Makes the server half of the Reveal from the SCRATCH prototype by a listed set of edits, and nothing else (work package WP9).
The committed files api/_lib/styles/reveal.py, reveal_clean.py and reveal_wm.py ARE the output of this tool plus the hand written part
of reveal.py (the enhance helper, below the marker line):

    set SNAPEYES_SCRATCH_Y3=<the wave-y3 folder of the scratch tree>
    python scripts/styles_tests/port_reveal.py            # writes the files
    python scripts/styles_tests/port_reveal.py --check    # compares them with what the edits make of the scratch (exit 1 on a difference)

test_reveal.py runs the check when the scratch tree is there (a LOCAL line), so "the port is the scratch with these edits" is a proven
sentence and not a claim, next to the goldens that prove the same from the other side.

What is taken, and what is not. The prototype's presentation family does two jobs. The server half (what /api/enhance hands the page next to
the display copy) is ported: reveal_params (pupil, registration, restored edge, colour drift, lid), prepare_restored (the lid hidden, the pupil
crushed to pure black), the display copy. The frame half (the wide frame, the card, the strip, the context crop: what the BROWSER builds from the
customer's own photo, and what a paid card would have stored) is not: decision C10 keeps the wide frame in the browser, so no server code builds
or stores one. Its arithmetic lives in src/reveal/revealMath.ts and is tested against vectors the prototype's Python wrote.

Edits, in four kinds: imports (the scratch paths and `fx.core` go, the engine module is api/_lib/iris.py), the cross references between the three
files (they were one family of modules next to each other), the module docstrings (the new ones say what each file is now), and
`from __future__ import annotations` after the docstring (Vercel's default Python is 3.12).
"""
from __future__ import annotations

import argparse
import ast
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("SNAPEYES_REPO") or os.path.dirname(os.path.dirname(HERE))      # the checkout (a suite runs from a prepared copy of this folder)
STYLES = os.path.join(ROOT, "api", "_lib", "styles")
MARK = "# ---- hand written below this line (scripts/styles_tests/port_reveal.py leaves it alone) "

# the top level names of designs/presentation.py that the server half needs (everything else there is the browser's frame, the card, the strip)
FROM_PRESENTATION = [
    "PAD", "R_FRAC", "RF", "ZONE_A", "F3_LO", "F3_HI", "EDGE_E1_MAX", "REG_TOL", "REG_BAND", "REG_NCC_MIN", "REG_SPREAD_OK", "SHIFT_MAX",
    "EDGE_TARGET", "EDGE_MIN_NATURAL", "SOFT_PX_PER_R", "DRIFT_FAIL", "DRIFT_WARN",
    "_clampf", "smoothstep01", "_circle_detector", "pupil_info", "pupil_centre", "display_copy", "_sample_lum", "edge_profile", "_width_1090",
    "restored_edge", "_lum", "_gauss1d", "_blur", "_grad", "_down", "_xcorr_peak", "_annulus", "_central_square", "registration", "_half_offsets", "align_crop",
    "reveal_params", "public_params", "prepare_restored",
]

REVEAL_DOC = '''"""reveal: the server half of the clean-iris Reveal (work package WP9), ported from the scratch prototype's designs/presentation.py.

What /api/enhance hands the page next to the display copy, all measured on the CLEAN restoration and the deglared crop it was made from (the
display copy's watermark would disturb every measurement):
  reveal_params(crop, restored)   the small dict ("reveal", about 140 bytes): pupil centre and radius, the registration shift of the photo layer,
                                  the restored edge (alpha 1 up to e0 R, 0 from e1 R, e0 >= 0.95 so zone A is untouched), ok (registration
                                  trusted AND colour drift <= 8: False means the page shows the strip without the cut), soft, drift, lid
  public_params(p)                p without its private masks: exactly what goes over the wire
  prepare_restored(restored, p)   the restored image as the Reveal shows it: the eyelid skin hidden, the pupil crushed to pure black (its own
                                  shape kept), nothing else touched
  display_copy(restored)          the 800 px display copy with the preview watermark (api/_lib/preview.py display_image; style "repo", the
                                  default). The AD's arcs variant (reveal_wm.py) stays OFF until the owner signs D14: only style="arcs" reaches it
  reveal_for(crop, restored)      the one call of /api/enhance: the guard on the time left, the measurement, the prepared and watermarked copy,
                                  the codes of the event; never raises, never costs the preview

What is NOT here (decision C10): the wide frame, the 4:5 card, the strip and the context crop. The browser builds the customer's frame from the
photo it still holds (src/reveal/wideFrame.ts), keeps it in memory and never uploads it; no server code builds or stores one. Its arithmetic is
src/reveal/revealMath.ts, checked against vectors the prototype's Python wrote (src/reveal/vectors.json).

Nothing is written on the picture (the studio writes nothing on the artwork), nothing is drawn around the iris: no stroke, no glow. Deterministic,
no randomness, no model call. numpy and Pillow only.

Module rule of the v3 work: every module starts with the __future__ import (Vercel's default Python is 3.12)."""'''

CLEAN_DOC = '''"""reveal_clean: what the Reveal does to the restored layer's SOURCE before it is resampled (ported from the scratch prototype's
designs/presentation_clean.py, work package WP9). numpy and Pillow only.

One function per job, every one a server side step of reveal.reveal_params() and every one baked into the image the page receives (the
watermarked display copy on /try), so the page needs no extra arithmetic:

  pupil_info(restored, kind)     centre, radius and SHAPE CLASS of the restored pupil: round (the engine's circle detector, human eyes), slit or
                                 bar (a dark-blob detector, animals; pets are out of scope for release 1: kind is always "human"); the cut goes
                                 through this centre.
  crush_pupil(restored, info)    the restored pupil to pure black, its own shape kept: luma x 0.12, chroma 0, feathered over the pupil's rim.
  lid_mask(restored, lid=None)   eyelid skin inside the restored disc: the pink skin wedges the colour rule finds (and any lid line /api/analyze
                                 supplies: it supplies none today). Returns a soft mask (1 = lid) and the share of the disc it covers; the masked
                                 pixels are hidden (black), never altered.
  apply_lid(restored, mask)      the restored image with the lid hidden.
  colour_drift(crop, restored)   dE00 between the median colour of the photo's iris band and the restored one: above 8 the cut is withheld.

Module rule of the v3 work: every module starts with the __future__ import (Vercel's default Python is 3.12)."""'''

WM_DOC = '''"""reveal_wm: the display copy with the watermark on ARCS (the art director's proposal, owner sign-off D14 outstanding; ported from the scratch
prototype's designs/presentation_wm.py, work package WP9). OFF: reveal.display_copy uses the repo's own tile unless style="arcs" is asked for, and
nothing asks for it until D14 is signed.

The repo's display copy (preview.display_image) draws the preview tile across the WHOLE square at 3.5 x its artwork strength, so the words run over
the pupil and the iris centre. This one puts the same words on three concentric arcs between 0.62 R and 0.92 R of the iris, at about 0.045 R cap
height, opacity 0.17 over a soft dark copy, and draws nothing inside 0.55 R (pupil, collarette) or outside the disc. The words are the engine's
(iris.WATERMARK_TEXT, the page's language); the font is the engine's Plus Jakarta Sans Bold. numpy and Pillow only.

Module rule of the v3 work: every module starts with the __future__ import (Vercel's default Python is 3.12)."""'''


def sub(old, new, count=1):
    return ("sub", old, new, count)


NL = chr(10)


def _names_of(n):
    if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
        return [n.name]
    if isinstance(n, ast.Assign):
        out = []
        for t in n.targets:
            if isinstance(t, ast.Name):
                out.append(t.id)
            elif isinstance(t, ast.Tuple):
                out += [e.id for e in t.elts if isinstance(e, ast.Name)]
        return out
    return []


def _seg(src, nodes, names):
    """The source of the named top level definitions or assignments, in the order of the file, each with its own comment lines above."""
    lines = src.splitlines()
    out, seen = [], set()
    for n in nodes:
        have = _names_of(n)
        if not set(have) & names:
            continue
        seen |= set(have)
        start = n.lineno - 1
        while start > 0 and lines[start - 1].lstrip().startswith("#"):
            start -= 1
        out.append((isinstance(n, (ast.FunctionDef, ast.ClassDef)), NL.join(lines[start:n.end_lineno])))
    missing = names - seen
    if missing:
        raise SystemExit(f"presentation.py: {sorted(missing)} not found: the scratch file moved")
    return out


def _apply(text, edits, where):
    for kind, old, new, count in edits:
        n = text.count(old)
        if n != count:
            raise SystemExit(f"{where}: edit {old[:60]!r} matches {n} times, expected {count}: the scratch file moved")
        text = text.replace(old, new)
    return text


def _body_of(src):
    """The top level statements of a scratch module after its docstring and imports, as source."""
    tree = ast.parse(src)
    body = tree.body
    i = 0
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant):
        i = 1
    while i < len(body) and isinstance(body[i], (ast.Import, ast.ImportFrom)):
        i += 1
    lines = src.splitlines()
    start = body[i].lineno - 1
    while start > 0 and lines[start - 1].lstrip().startswith("#"):
        start -= 1
    return "\n".join(lines[start:]) + "\n"


def make(y3):
    """{path relative to api/_lib/styles: text of the generated part}. reveal.py's text ends at MARK (the hand written part follows)."""
    def read(name):
        with open(os.path.join(y3, "designs", name), "r", encoding="utf-8") as f:
            return f.read()

    pres, clean, wm = read("presentation.py"), read("presentation_clean.py"), read("presentation_wm.py")

    # ---- reveal.py: the selected names of presentation.py
    tree = ast.parse(pres)
    parts = _seg(pres, tree.body, set(FROM_PRESENTATION))
    body = ""
    for i, (is_def, text) in enumerate(parts):
        if i:
            body += NL * (3 if (is_def or parts[i - 1][0]) else 1)       # two blank lines around a function, none between constants
        body += text
    body += NL
    body = _apply(body, [
        sub('        import presentation_wm as WM\n        return WM.display_copy_arcs(restored, lang)\n',
            '        from . import reveal_wm as WM\n        return WM.display_copy_arcs(restored, lang)\n'),
        sub("    from _lib import preview as PV\n", "    from .. import preview as PV\n"),
    ], "presentation.py")
    head = (
        "# -*- coding: utf-8 -*-\n" + REVEAL_DOC + "\nfrom __future__ import annotations\n\n"
        "import base64\nimport io\nimport math\nimport time\n\nimport numpy as np\nfrom PIL import Image\n\nfrom .. import iris as L\nfrom . import reveal_clean as CL\n\n\n"
    )
    # the constants come first (as in the scratch), then the functions
    reveal_text = head + body + "\n\n" + MARK + "-" * 20 + "\n"

    # ---- reveal_clean.py: the whole of presentation_clean.py after its imports
    cbody = _body_of(clean)
    clean_text = ("# -*- coding: utf-8 -*-\n" + CLEAN_DOC + "\nfrom __future__ import annotations\n\n"
                  "import math\nfrom collections import deque\n\nimport numpy as np\nfrom PIL import Image, ImageFilter\n\n" + cbody)

    # ---- reveal_wm.py: the whole of presentation_wm.py after its imports
    wbody = _body_of(wm)
    wm_text = ("# -*- coding: utf-8 -*-\n" + WM_DOC + "\nfrom __future__ import annotations\n\n"
               "import math\n\nimport numpy as np\nfrom PIL import Image, ImageDraw, ImageFilter\n\nfrom .. import iris as L\n\n" + wbody)
    wm_text = _apply(wm_text, [
        sub("L = _core.L\n", ""),
    ], "presentation_wm.py")
    return {"reveal.py": reveal_text, "reveal_clean.py": clean_text, "reveal_wm.py": wm_text}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    y3 = os.environ.get("SNAPEYES_SCRATCH_Y3") or sys.exit("SNAPEYES_SCRATCH_Y3 is not set (the wave-y3 folder of the scratch tree)")
    made = make(y3)
    bad = 0
    for rel, text in made.items():
        path = os.path.join(STYLES, rel)
        if a.check:
            try:
                with open(path, "r", encoding="utf-8", newline="") as f:
                    have = f.read().replace("\r\n", "\n")
            except FileNotFoundError:
                print(f"missing {rel}")
                bad += 1
                continue
            want = text
            if rel == "reveal.py":
                i = have.find(MARK)
                if i < 0:
                    print("reveal.py: the hand written marker is gone")
                    bad += 1
                    continue
                j = have.find("\n", i) + 1
                have, want = have[:j], text
            if have != want:
                print(f"{rel}: differs from what the edits make of the scratch")
                bad += 1
            else:
                print(f"{rel}: equals the scratch plus the listed edits")
            continue
        if rel == "reveal.py" and os.path.exists(path):
            with open(path, "r", encoding="utf-8", newline="") as f:
                old = f.read().replace("\r\n", "\n")
            i = old.find(MARK)
            tail = old[old.find("\n", i) + 1:] if i >= 0 else ""
            text = text + tail
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"wrote {rel}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
