# -*- coding: utf-8 -*-
"""Offline tool (never in a function): bakes the per-design time and memory table of api/_lib/styles/costs.py from the measured spike
(SPIKE.md of the planning, sections 3.1, 4.1 and 4.4: quiet-core CPU seconds and peak memory of every design at 1024 px previews and 4096 px masters).

    python scripts/bake_costs.py <SPIKE.md> [--write]

Without --write it prints the literal; with it, it rewrites the block between the BAKED markers of costs.py. The spike's design
labels ("Infinity (universe bg)", "Family 6 (dark)", "Echo 3 eyes") become the cost keys of costs.cost_key(): module.design with an
optional .clean or .universe variant. Every figure is the spike's own, unrounded; nothing is interpolated.
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COSTS = os.path.join(HERE, "..", "api", "_lib", "styles", "costs.py")
BEGIN, END = "# BEGIN BAKED (scripts/bake_costs.py)", "# END BAKED"

SINGLE = {"Powder Burst": "singles.powder", "Splash": "singles.splash", "Elements": "singles.elements", "Radiance": "singles.radiance",
          "Gold": "singles.gold", "Clean": "singles.clean", "Vortex": "universe.vortex", "Deep Field": "universe.deepfield",
          "Starfield": "universe.starfield", "Infinity (dark)": "collision.infinity", "Infinity (clean)": "collision.infinity.clean",
          "Infinity (universe bg)": "collision.infinity.universe", "Kiss (dark)": "collision.kiss", "Kiss (universe bg)": "collision.kiss.universe",
          "Trio (dark)": "collision.trio", "Trio (universe bg)": "collision.trio.universe"}


def key_of(label):
    label = label.strip()
    if label in SINGLE:
        return SINGLE[label]
    m = re.fullmatch(r"Family \d \((dark|universe bg)\)", label)
    if m:
        return "collision.family" + (".universe" if "universe" in m.group(1) else "")
    if re.fullmatch(r"Chain \d \(dark\)", label):
        return "collision.chain"
    if re.fullmatch(r"Echo \d eyes?", label):
        return "universe.echo"
    raise KeyError(label)


def rows(text, header_start):
    """The markdown table rows after the line that starts with header_start, until the first line that is not a table row."""
    lines = text.splitlines()
    i = next(k for k, l in enumerate(lines) if l.startswith(header_start))
    out = []
    for l in lines[i + 2:]:
        if not l.startswith("|"):
            break
        out.append([c.strip() for c in l.strip().strip("|").split("|")])
    return out


def num(s):
    s = s.replace("*", "").strip()
    return float(s) if s not in ("", "-") else None


def literal(d, indent):
    lines = ["{"]
    for k in d:
        inner = ", ".join(f"{n}: {tuple(v)!r}" for n, v in sorted(d[k].items()))
        lines.append(f'{indent}    "{k}": {{{inner}}},')
    lines.append(indent + "}")
    return "\n".join(lines)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__)
    text = open(src, encoding="utf-8").read()
    master, preview, capped = {}, {}, {}
    for r in rows(text, "| design | eyes | cold cpu s |"):
        k, n = key_of(r[0]), int(r[1])
        master.setdefault(k, {})[n] = (num(r[2]), num(r[3]), int(num(r[4])), int(num(r[5])))
    for r in rows(text, "| design | eyes | cold | warm, new eyes |"):
        k, n = key_of(r[0]), int(r[1])
        preview.setdefault(k, {})[n] = (num(r[2]), num(r[3]), num(r[4]), num(r[5]), int(num(r[6])))
    for r in rows(text, "| design | full 4096 px source: cpu s |"):
        label = r[0]
        m = re.fullmatch(r"(Family (\d)) \((dark|universe bg)\)", label)
        if m:
            k, n = key_of(label), int(m.group(2))
        elif label in ("Infinity (dark)", "Kiss (dark)", "Trio (dark)", "Clean", "Elements", "Powder Burst", "Radiance", "Deep Field", "Vortex"):
            k, n = key_of(label), 1 if label in ("Clean", "Elements", "Powder Burst", "Radiance", "Deep Field", "Vortex") else (3 if label.startswith("Trio") else 2)
        elif label == "Echo 1 eye":
            k, n = "universe.echo", 1
        elif label == "Echo 6 eyes":
            k, n = "universe.echo", 6
        else:
            continue
        capped.setdefault(k, {})[n] = (num(r[3]), int(num(r[4])))
    block = (f"{BEGIN}\n"
             "# MASTER[key][eyes] = (cold cpu s, warm cpu s, cold peak MB, warm peak MB): a 4096 px master from 4096 px eyes, one thread, quiet core\n"
             f"MASTER = {literal(master, '')}\n\n"
             "# CAPPED[key][eyes] = (cpu s, peak MB) with the working copy of every eye cut to 2048 px: what the pairs, families and chain cost\n"
             f"CAPPED = {literal(capped, '')}\n\n"
             "# PREVIEW[key][eyes] = (cold s, warm s with new eyes, warm s with the same eyes (the design alone), per-eye preparation s, peak MB):\n"
             "# a 1024 px preview, quiet core\n"
             f"PREVIEW = {literal(preview, '')}\n"
             f"{END}")
    if "--write" in sys.argv:
        t = open(COSTS, encoding="utf-8").read()
        a, b = t.index(BEGIN), t.index(END) + len(END)
        open(COSTS, "w", encoding="utf-8", newline="\n").write(t[:a] + block + t[b:])
        print("costs.py rewritten:", sum(len(v) for v in master.values()), "master rows,", sum(len(v) for v in capped.values()), "capped rows,",
              sum(len(v) for v in preview.values()), "preview rows")
    else:
        print(block)


if __name__ == "__main__":
    main()
