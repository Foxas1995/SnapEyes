# -*- coding: utf-8 -*-
"""cx_kit: shared plumbing of the collision designs (ported from the scratch prototype): eye loading, pupil analysis, atlas, memory meter."""
from __future__ import annotations

# PORT of work package WP7A (step A): cx_kit.py of the DG1 snapshot of the scratch prototype, verbatim but for the edits
# scripts/styles_tests/port_collision.py lists (imports, no calibration eye loader, no path atlas, bounded caches, no Windows meter); test_goldens_collision.py replays the edits on the scratch and the pixels of the
# scratch's own pictures.

import sys

import numpy as np

from .. import atlas as AT
from .. import core as C
from .. import pupil as PUP


def atlas():
    """The chip atlas (api/_lib/styles/atlas.py: read once per process, checked against the registry's sha256)."""
    return AT.chips()


_PUP = C.BoundedCache(64)


def pupil(ir):
    """Pupil analysis on the canonical 256 grade (R units, resolution independent)."""
    got = _PUP.get(ir.digest)
    if got is None:
        fr = ir.graded(C.REF_SIDE)
        sq, t = C._tight(fr)
        got = _PUP.put(ir.digest, PUP.analyse(sq))
    return got


def peak_rss_mb():
    """The peak memory of the process in MB (the high-water mark of a warm instance), or None where the platform has no resource module. Only the
    options that ask for a memory trace read it."""
    try:
        import resource
        ru = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return round(ru / (1024.0 if sys.platform.startswith("linux") else 1048576.0))
    except Exception:  # noqa: no meter on this platform
        return None


# ----------------------------------------------------------------------------- input gate (round 2c, AD: eyelid or skin remnants inside a fixture iris are a hard fail)
_GATE = C.BoundedCache(64)


def gate(ir):
    """Input gate of a restored iris: does the graded disc still carry eyelid, lash or skin? Cues on the canonical 256 grade (R units, resolution
    independent): (1) sectors (10 deg) of the annuli 0.70-0.88 R and 0.88-0.98 R whose mean L* deviates > 16 from the median sector (a lash band or a lid
    margin is darker or brighter than any iris sector), (2) the ring-colour outlier bins (fx.core.ring_colours re-fills bins that are dE00 > 20 from the
    ring's median: a lid band), (3) the largest single deviation. A designer cannot repair such an input (an effect never recolours or repaints an iris):
    the restoration must, so a design board shows only irises that pass and lists the rest. Returns dict(ok, lid70, lid88, outlier_bins, maxdev70)."""
    k = ir.digest
    got = _GATE.get(k)
    if got is not None:
        return got
    info = {}
    C.ring_colours(ir, info=info)
    fr = ir.graded(C.REF_SIDE)
    sq, t = C._tight(fr)
    R = t / 2.0
    ax = np.arange(t) + 0.5 - R
    rr = np.sqrt(ax[None, :] ** 2 + ax[:, None] ** 2) / R
    th = np.degrees(np.arctan2(ax[:, None] + 0 * ax[None, :], ax[None, :] + 0 * ax[:, None])) % 360.0
    rgb = sq.astype(np.float32) / 255.0
    res = []
    for (r0, r1) in ((0.70, 0.88), (0.88, 0.98)):
        m = (rr > r0) & (rr < r1)
        Lv = C.lch(rgb[m])[0]
        b = (th[m]).astype(int) // 10
        cnt = np.maximum(np.bincount(b, minlength=36), 1)
        Lm = np.bincount(b, weights=Lv, minlength=36) / cnt
        dev = np.abs(Lm - np.median(Lm))
        res.append((float(dev.max()), int((dev > 16).sum())))
    ob = int(info.get("outlier_bins", 0))
    lid70, lid88, md = res[0][1], res[1][1], res[0][0]
    bad = lid70 >= 3 or lid88 >= 4 or ob >= 40 or (ob >= 20 and lid70 + lid88 >= 2) or (md >= 22.0 and lid70 >= 2)
    out = dict(ok=not bad, lid70=lid70, lid88=lid88, outlier_bins=ob, maxdev70=round(md, 1))
    return _GATE.put(k, out)
