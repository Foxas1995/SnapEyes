# -*- coding: utf-8 -*-
"""The result table of a suite run.   python suites/summary.py <results dir> [--baseline suites/baseline.json] [--all] [--md]

A suite is GREEN when its .exit file says 0, SKIPPED on 77 (its private fixtures are missing), RED on anything else. Checks are
counted as the lines of its output that start with PASS or FAIL (every suite and the page-code tests print those). With a
baseline, a green suite that passes FEWER checks than the baseline records is flagged too: a suite that quietly stops running
checks is not "at least as green". Exit code 0 only when nothing is RED, FEWER or MISSING (a skipped suite does not fail the run;
the table says so). --md prints the table as markdown rows (suites/baseline.md)."""
import json, os, re, sys


def read(path):
    try:
        return open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return ""


def main(argv):
    if not argv:
        sys.exit(__doc__)
    res = argv[0]
    md = "--md" in argv
    base = {}
    if "--baseline" in argv:
        base = json.load(open(argv[argv.index("--baseline") + 1], encoding="utf-8")).get("suites", {})
    names = sorted(f[:-5] for f in os.listdir(res) if f.endswith(".exit"))
    for n in base if "--all" in argv else []:      # a full run: a baseline suite with no result is MISSING (a subset run leaves them out)
        if n not in names:
            names.append(n)
    rows, bad = [], 0
    for n in names:
        ex = read(os.path.join(res, n + ".exit")).strip()
        m = re.search(r"EXIT (\d+)", ex)
        code = int(m.group(1)) if m else None
        out = read(os.path.join(res, n + ".out"))
        p = len(re.findall(r"^PASS", out, flags=re.M))
        f = len(re.findall(r"^FAIL", out, flags=re.M))
        want = base.get(n, {}).get("pass")
        if code is None:
            state = "MISSING"
        elif code == 0 and f == 0:
            state = "GREEN"
        elif code == 77:
            state = "SKIPPED"
        else:
            state = "RED"
        if state == "GREEN" and want is not None and p < want:
            state = "FEWER"
        if state in ("RED", "FEWER", "MISSING"):
            bad += 1
        rows.append((n, "-" if code is None else code, p, f, want if want is not None else "-", state))
    if md:
        print("| suite | exit | PASS lines | FAIL lines | baseline | state |\n|---|---:|---:|---:|---:|---|")
        for r in rows:
            print("| " + " | ".join(str(x) for x in r) + " |")
    else:
        print(f"{'suite':10} {'exit':>4} {'pass':>5} {'fail':>5} {'base':>5}  state")
        for r in rows:
            print(f"{r[0]:10} {r[1]!s:>4} {r[2]:>5} {r[3]:>5} {r[4]!s:>5}  {r[5]}")
    green = sum(1 for r in rows if r[5] == "GREEN")
    skipped = sum(1 for r in rows if r[5] == "SKIPPED")
    print(f"\n{green} of {len(rows)} green" + (f", {skipped} skipped" if skipped else "") + (f", {bad} NOT GREEN" if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
