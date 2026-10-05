# -*- coding: utf-8 -*-
"""Time and memory of a 4096 px universe render, the port against the scratch prototype, each in a FRESH process (an honest peak), alternating, one thread:

    set SNAPEYES_SCRATCH_Y3=<the wave-y3 folder of the scratch tree>
    python scripts/styles_tests/time_universe.py [--rounds 2] [CASE ...]        cases: echo1 echo2 echo6 vortex deepfield starfield (default: all)

The eyes are the synthetic irises of synth_iris at 1024 px (the same bytes for both sides); a pair and a group work on copies of at most 2048 px (the registry's work_side), a single eye
on 4096 px. The plate looks draw their 2k and 4k LODs of the 4K plates: the port reads them from a local store made out of the scratch tree's own files (scripts/upload_plates.py logic),
the scratch from its folders. Printed per run: CPU seconds of the render (process time, imports apart), wall seconds, the peak working set in MB (Windows psapi, or VmHWM). The
baseline document (suites/baseline.md, section 14) holds the table this tool printed, next to the spike's table (SP 4.1) scaled by this machine's yardstick (scripts/cpu_probe.py).
Not run by any suite: it measures, it does not decide.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("SNAPEYES_REPO") or os.path.dirname(os.path.dirname(HERE))
Y3 = os.environ.get("SNAPEYES_SCRATCH_Y3") or ""
CASES = {"echo1": ("echo", ["blue_round"], None, 4096), "echo2": ("echo", ["blue_round", "dark_brown_round"], "3:2", 2048),
         "echo6": ("echo", ["blue_round", "green_round", "amber_slit", "dark_brown_round", "grey_round", "blue_slit"], None, 2048),
         "vortex": ("vortex", ["blue_round"], None, 4096), "deepfield": ("deepfield", ["green_round"], None, 4096), "starfield": ("starfield", ["dark_brown_round"], None, 4096)}


def peak_mb():
    try:
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes

            class PMC(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
            k32 = ctypes.WinDLL("kernel32", use_last_error=True)
            k32.GetCurrentProcess.restype = wintypes.HANDLE
            psapi = ctypes.WinDLL("psapi", use_last_error=True)
            psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
            pmc = PMC()
            pmc.cb = ctypes.sizeof(PMC)
            psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb)
            return round(pmc.PeakWorkingSetSize / 1048576.0)
        for line in open("/proc/self/status"):
            if line.startswith("VmHWM:"):
                return round(int(line.split()[1]) / 1024.0)
    except Exception:  # noqa: BLE001
        return None
    return None


def child(which, case):
    import time
    look, names, asp, size = CASES[case]
    sys.path.insert(0, HERE)
    import synth_iris as SI
    raws = [SI.png_bytes(n) for n in names]
    if which == "port":
        sys.path.insert(0, os.path.join(REPO, "api"))
        from _lib.styles import core as C, universe as U
        work = 4096 if len(names) == 1 else 2048
        eyes = [C.Iris(r, n, max_side=work) for r, n in zip(raws, names)]
        render = lambda: U.render(look, eyes, size, asp, times={})
    else:
        sys.path.insert(0, Y3)
        from fx import core as C
        from designs import universe as U
        C.WORK_SIDE = 4096 if len(names) == 1 else 2048
        eyes = [C.Iris(r, n) for r, n in zip(raws, names)]
        render = lambda: U.render(look, eyes, size, asp)
    c0, t0 = time.process_time(), time.time()
    img = render()
    print(json.dumps({"cpu": round(time.process_time() - c0, 1), "wall": round(time.time() - t0, 1), "peak_mb": peak_mb(), "size": list(img.size)}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cases", nargs="*", default=list(CASES))
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--child", nargs=2, metavar=("WHICH", "CASE"))
    a = ap.parse_args()
    if a.child:
        return child(*a.child)
    if not Y3:
        sys.exit("SNAPEYES_SCRATCH_Y3 is not set (the wave-y3 folder of the scratch tree)")
    store = tempfile.mkdtemp(prefix="time_universe_")
    env = dict(os.environ, OMP_NUM_THREADS="1", PYTHONIOENCODING="utf-8", STORE_LOCAL_DIR=os.path.join(store, "store"), STYLE_PLATE_CACHE=os.path.join(store, "cache"),
               SNAPEYES_TICKET_SECRET="t" * 40, SNAPEYES_REPO=REPO)
    os.makedirs(env["STORE_LOCAL_DIR"])
    sys.path.insert(0, os.path.join(REPO, "api"))
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    os.environ.update(STORE_LOCAL_DIR=env["STORE_LOCAL_DIR"], SNAPEYES_TICKET_SECRET=env["SNAPEYES_TICKET_SECRET"])
    import upload_plates as UP
    from _lib import plates_registry as REG
    from _lib import store as st
    table = REG.PLATES_REGISTRY["plates"]
    fams = {"P-DN-SPIRAL", "P-UV-DUST", "P-UV-MILKY"}
    y2 = os.path.join(os.path.dirname(os.path.abspath(Y3)), "wave-y2", "plates")
    rows = UP.plan({i: r for i, r in table.items() if r["family"] in fams and r["k4"]}, fams, UP.sources(y2, Y3))
    tot = UP.run(rows, st, True, out=lambda m: None)
    print(f"4K plates in a local store: {tot}", flush=True)
    print(f"{'case':10s} {'side':6s} {'cpu s':>7s} {'wall s':>7s} {'peak MB':>8s}")
    for case in a.cases:
        for r in range(a.rounds):
            for which in ("port", "scratch"):
                out = subprocess.run([sys.executable, os.path.abspath(__file__), "--child", which, case], capture_output=True, text=True, env=env, timeout=900)
                line = [x for x in out.stdout.splitlines() if x.startswith("{")]
                if not line:
                    print(f"{case:10s} {which:6s} FAILED {out.stderr[-300:]}")
                    continue
                j = json.loads(line[-1])
                print(f"{case:10s} {which:6s} {j['cpu']:7.1f} {j['wall']:7.1f} {j['peak_mb']!s:>8s}", flush=True)


if __name__ == "__main__":
    main()
