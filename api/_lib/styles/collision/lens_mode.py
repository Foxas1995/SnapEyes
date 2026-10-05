# -*- coding: utf-8 -*-
"""lens_mode: DG1 rung 2 of INTEGRATION_SPEC 1.7, the safety net of Collision Infinity and Clean Infinity: the automatic per-pair choice between the WOVEN lens (the smooth S weave
of seam_plan.py, the default) and the STACK lens (the same two discs, one iris fully in front over the whole lens, the thin dark edge only inside the front iris, the soft contact
shadow of the front iris on the back one (Zone C), no weave, no seam).

THE RULE.  weave unless the colour step across the planned seam is beyond anything the weave was seen to carry:   K = mean CIEDE2000 between the smoothed iris A just above and the
smoothed iris B just below the planned seam (seam_plan.plan_seam, info['K_chosen'], measured on the canonical 256 px grade, so it is the same at every size, in the Clean and in the
Collision build and for every tile of the pair).  stack iff K > K_STACK.
  Calibration (DG1 judge, 2026-10-04): the 23 gate-passing eyes of the fixtures give 506 ordered pairs, 441 of them Infinity pairs (65 have a wide pupil and already fall back to the
  Kiss geometry): K median 27, 90th percentile 43, 99th 52, maximum 56.  The weave was judged clean at 100 percent on every pair inspected up to K 56 (blue with brown 48, blue with
  dark orange brown 56), so K_STACK sits above the corpus maximum: THE NET DOES NOT FIRE ON ANY PAIR OF THE CORPUS.  It is a provisional limit for a pair the corpus does not contain;
  the stack lens is built, measured (T1, T2, T3) and reachable by hand (opts lens_mode='stack') so that the first real failing pair has somewhere to go.

THE STACK LENS.  Front iris = the one whose seam-side band is brighter (brief 1.3.2, ties: A); centre distance raised to at least STACK_D = 1.57 R (a stack hides the whole lens of the
back iris: 88.6 percent of it stays visible at 1.57 R, 87.2 to 88.0 measured on the pixels, the T3 floor of Collision Infinity is 87 percent; at the weave distance 1.33 R the back
iris would keep only 78 percent, at B's 1.42 R only 82 percent).  Recorded as
design_used 'stack' and fallback 'stack_contrast'.

numpy only, deterministic (no random number, no clock).
"""
from __future__ import annotations

# PORT of work package WP7A (step A): lens_mode.py of the DG1 snapshot of the scratch prototype, verbatim but for the edits
# scripts/styles_tests/port_collision.py lists (no edit); test_goldens_collision.py replays the edits on the scratch and the pixels of the
# scratch's own pictures.

K_STACK = 62.0
STACK_D = 1.57


def decide(plan_info, forced="auto"):
    """'weave' or 'stack' for one pair. plan_info: the info dict of seam_plan.plan_seam (needs 'K_chosen'). forced: 'auto' | 'weave' | 'stack'."""
    if forced in ("weave", "stack"):
        return forced
    return "stack" if float(plan_info.get("K_chosen", 0.0)) > K_STACK else "weave"


def stack_distance(d_over_R, d_max=1.70):
    """Centre distance (R units) of the stack lens: the weave distance, at least STACK_D, at most the Kiss distance."""
    return float(min(max(d_over_R, STACK_D), d_max))
