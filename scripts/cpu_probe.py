# -*- coding: utf-8 -*-
"""The CPU probe from the command line (the workload and the maths are api/_lib/cpu_probe.py; this file is not deployed).

    python scripts/cpu_probe.py                        # one local run: seconds per phase, the sum (the baseline of today)
    python scripts/cpu_probe.py --runs 5 --json        # the same as JSON
    python scripts/cpu_probe.py --save today.json      # keep today's baseline for later --baseline today.json

    python scripts/cpu_probe.py --remote https://snapeyes.com --key-file <file holding the admin key>
                                                       # measures the baseline here NOW, then asks the deployment's admin action
                                                       # cpu_probe to run the same workload there and prints the slow factor
    python scripts/cpu_probe.py --remote URL --key-file F --mode cold    # the first probe of a fresh instance (once, right after a deploy)
    python scripts/cpu_probe.py --remote URL --key-file F --header "x-vercel-protection-bypass: ..."   # a protected Preview

The admin key is read from the file (or from the environment variable named by --key-env), checked for its shape, sent only in the
Authorization header of that one request, and never printed. Only https URLs are used, or http for localhost. The remote action
is read-only: it changes nothing and reads nothing from storage. Run it on a quiet machine: the baseline is a median of three
passes of the same code, and a loaded core makes the factor too small. The result closes step V3 of the plan (STYLE_SLOW_CPU)
and part of V4 and VE3 (the instance's memory, CPUs and /tmp)."""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api"))
from _lib import cpu_probe as P  # noqa: E402

KEY_SHAPE = re.compile(r"^admin-v[0-9]{1,6}\.[0-9]{9,11}\.[0-9a-f]{32}$")


def show_local(res):
    print(f"local pass ({res['runs']} run(s), median per phase), seconds:")
    for k in P.PHASES:
        print(f"  {k:20} {res['phases'][k]:8.3f}")
    print(f"  {'total':20} {res['total']:8.3f}   (process CPU {res['process_cpu_s']} s over {res['wall_s']} s of wall time)")


def post(url, key, body, headers):
    req = urllib.request.Request(url.rstrip("/") + "/api/admin", data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers=dict({"Content-Type": "application/json", "Authorization": "Bearer " + key,
                                               "User-Agent": "snapeyes-cpu-probe"}, **headers))
    try:
        with urllib.request.urlopen(req, timeout=100) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except ValueError:
            return e.code, {"ok": False, "reason": "not_json"}


def main():
    ap = argparse.ArgumentParser(description="CPU probe (api/_lib/cpu_probe.py)")
    ap.add_argument("--runs", type=int, default=3, help="measured runs here (1 to 5; the remote action takes the same number)")
    ap.add_argument("--json", action="store_true", help="print JSON")
    ap.add_argument("--save", help="write this machine's phases to a file (a baseline for --baseline)")
    ap.add_argument("--baseline", help="use the phases saved by --save instead of measuring now")
    ap.add_argument("--remote", help="the deployment to probe, e.g. https://snapeyes.com")
    ap.add_argument("--key-file", help="file holding the admin key (scripts/mint_admin.py)")
    ap.add_argument("--key-env", help="name of an environment variable holding the admin key")
    ap.add_argument("--mode", choices=P.MODES, default="warm")
    ap.add_argument("--header", action="append", default=[], help='an extra request header "Name: value" (repeatable)')
    a = ap.parse_args()
    if not 1 <= a.runs <= P.RUNS_MAX:
        ap.error(f"--runs must be 1 to {P.RUNS_MAX}")

    if a.baseline:
        base = json.load(open(a.baseline, encoding="utf-8"))
        local = {"phases": base["phases"], "total": base.get("total", sum(base["phases"].values())), "runs": 0, "process_cpu_s": 0, "wall_s": 0}
    else:
        local = P.measure("warm", a.runs)
    if a.save:
        json.dump({"phases": local["phases"], "total": local["total"]}, open(a.save, "w", encoding="utf-8"))
    if not a.remote:
        if a.json:
            print(json.dumps(local))
        else:
            show_local(local)
        return 0

    u = urlsplit(a.remote)
    if u.scheme != "https" and not (u.scheme == "http" and u.hostname in ("localhost", "127.0.0.1")):
        ap.error("--remote must be an https URL (or http for localhost)")
    key = ""
    if a.key_file:
        key = open(a.key_file, encoding="utf-8").read().strip()
    elif a.key_env:
        key = os.environ.get(a.key_env, "").strip()
    if not KEY_SHAPE.fullmatch(key):
        ap.error("no admin key in --key-file or --key-env, or it is not of the shape scripts/mint_admin.py makes")
    headers = {}
    for h in a.header:
        name, _, val = h.partition(":")
        if not name.strip() or not val.strip():
            ap.error('--header wants "Name: value"')
        headers[name.strip()] = val.strip()
    if not a.json:
        show_local(local)
        print(f"\nasking {u.scheme}://{u.netloc} (mode {a.mode}) ...")
    status, rep = post(a.remote, key, {"action": "cpu_probe", "mode": a.mode, "runs": a.runs, "baseline": {"phases": local["phases"]}}, headers)
    if a.json:
        print(json.dumps({"status": status, "reply": rep, "local": local}))
        return 0 if rep.get("ok") else 1
    if not rep.get("ok"):
        print(f"refused: HTTP {status} {rep.get('reason') or rep.get('error')}")
        return 1
    print(f"\nremote ({rep['mode']}, {rep['runs']} run(s), first probe on this instance: {rep['first_on_instance']}), seconds:")
    for k in P.PHASES:
        f = (rep.get("phase_factors") or {}).get(k)
        print(f"  {k:20} {rep['phases'][k]:8.3f}   x {f}")
    print(f"  {'total':20} {rep['total']:8.3f}   x {rep['slow_factor']}  (baseline {rep['baseline_total']}, from the {rep['baseline_source']})")
    print(f"  process CPU {rep['process_cpu_s']} s over {rep['wall_s']} s of wall time; run totals {rep['run_totals']}")
    if rep.get("imports"):
        print("  imports on this instance: " + ", ".join(f"{k} {v['s']} s{' (already loaded)' if v['already_loaded'] else ''}" for k, v in rep["imports"].items()))
    print(f"  configured STYLE_SLOW_CPU there: {rep['configured_style_slow_cpu']}")
    print("  instance: " + json.dumps(rep["instance"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
