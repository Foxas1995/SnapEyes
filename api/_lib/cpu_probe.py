# -*- coding: utf-8 -*-
"""The CPU probe: how much slower than a quiet local core is the real function instance? It answers the admin action
`cpu_probe` (api/_lib/ops.py a_cpu_probe) and scripts/cpu_probe.py (the same workload run on a developer machine).

The workload stands in for what the style engines do at 4096 px and uses no engine code: a blur by cumulative sums, float32
sine, cosine and exp, a 4096 px RGB frame, a LANCZOS reduction to 1024 px, a bincount scatter, a JPEG q95 4:4:4 encode and a
decode. It is the workload of the planning spike's `cpu_probe` with one change: the RGB frame is made in float32 (50 MB as bytes,
about 200 MB while it is made), not float64 (about 800 MB at the peak), so that the probe cannot be the thing that runs a
1 GB function out of memory; the whole probe peaks near 350 MB. Because the code differs from the spike's, its baseline is
measured again with this very code (scripts/cpu_probe.py), on the day of the Vercel run, and sent with the request.

slow_factor = seconds on the instance / baseline seconds, over the sum of the phases (and per phase). The style engines' time
estimates multiply their local seconds by STYLE_SLOW_CPU (environment, default 1.6, style_slow_cpu() here); this is where a
better number comes from. `mode`: "cold" is one measured run with no warm-up and with the import times of numpy and Pillow, the
way the first request on a fresh instance sees it (call it right after a deploy, once: `first_on_instance` says whether it was
the first probe of this process); "warm" is one unmeasured run, then the median of up to three. The reply also carries what the
instance says about itself (memory and CPU limits, /tmp, interpreter and package versions, the region), a fixed list of facts
and no environment values besides it, so it answers the instance questions of the plan (memory, vCPU, /tmp) as far as an
instance can know them; the project's own settings (Fluid, maximum duration) stay unverified until someone reads them."""
from __future__ import annotations

import io
import math
import os
import re
import shutil
import sys
import tempfile
import threading
import time

PHASES = ("blur_cumsum", "float32_math", "make_rgb", "lanczos_4k_to_1k", "bincount_scatter", "jpeg95_encode_4k", "jpeg_decode_4k")
SLOW_CPU_DEFAULT = 1.6          # measured 1.58 (1.44 to 1.73) on /api/compose with 1024 px work; 4096 px work is not measured
SLOW_CPU_MIN, SLOW_CPU_MAX = 1.0, 6.0
RUNS_MAX = 5
MODES = ("cold", "warm")

# The development machine (Ryzen 7 3800X, Windows 11, Python 3.14.3, numpy 2.4.4, Pillow 12.2.0) on 2026-10-04, this workload: the
# median of three invocations of `python scripts/cpu_probe.py --runs 5`, seconds per phase, total 1.393 (the planning spike's own
# probe, with the float64 RGB frame, took 1.464 on a pinned quiet core: the other six phases agree within 5 percent). A default
# only: the machine is shared and its speed moves, so the number that counts is the one measured the same day and sent as
# `baseline` (scripts/cpu_probe.py --remote does exactly that).
BASELINE_DEV = {"blur_cumsum": 0.303, "float32_math": 0.060, "make_rgb": 0.203, "lanczos_4k_to_1k": 0.158,
                "bincount_scatter": 0.083, "jpeg95_encode_4k": 0.275, "jpeg_decode_4k": 0.311}

_LOCK = threading.Lock()        # one probe per process: two at once would measure each other
_RUNS_DONE = 0                  # probes this process has finished (first_on_instance)

# the only environment values the reply may carry: platform facts, no secret
_ENV_FACTS = ("AWS_LAMBDA_FUNCTION_MEMORY_SIZE", "AWS_REGION", "AWS_EXECUTION_ENV", "VERCEL", "VERCEL_ENV", "VERCEL_REGION",
              "VERCEL_GIT_COMMIT_SHA", "NOW_REGION", "LAMBDA_TASK_ROOT")


def style_slow_cpu() -> float:
    """STYLE_SLOW_CPU, the factor of a Vercel call against a quiet local core that the style engines multiply their local
    seconds by: the environment variable, a number between 1.0 and 6.0, else 1.6."""
    try:
        v = float(os.environ.get("STYLE_SLOW_CPU", "").strip())
    except ValueError:
        return SLOW_CPU_DEFAULT
    return min(max(v, SLOW_CPU_MIN), SLOW_CPU_MAX) if math.isfinite(v) else SLOW_CPU_DEFAULT


def workload() -> dict:
    """One pass of the workload: seconds per phase (PHASES)."""
    import numpy as np
    from PIL import Image
    t = {}
    rng = np.random.Generator(np.random.PCG64(7))
    t0 = time.perf_counter()
    a = rng.random((2048, 2048), dtype=np.float32)
    for _ in range(3):
        c = np.cumsum(a, axis=0, dtype=np.float32)
        a = (c[8:] - c[:-8])[:2040] / np.float32(8)
        c = np.cumsum(a, axis=1, dtype=np.float32)
        a = (c[:, 8:] - c[:, :-8])[:, :2032] / np.float32(8)
    t["blur_cumsum"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    x = rng.random(4_000_000, dtype=np.float32) * np.float32(6.28)
    y = np.sin(x) * np.cos(x * np.float32(1.7)) + np.exp(-x * np.float32(0.2))
    t["float32_math"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    px = rng.random((4096, 4096, 3), dtype=np.float32)
    px *= np.float32(255)
    im = Image.fromarray(px.astype(np.uint8))
    del px
    t["make_rgb"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    small = im.resize((1024, 1024), Image.LANCZOS)
    t["lanczos_4k_to_1k"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    idx = rng.integers(0, 4096 * 4096, 3_000_000)
    acc = np.bincount(idx, weights=rng.random(3_000_000), minlength=4096 * 4096)
    t["bincount_scatter"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=95, subsampling=0)
    t["jpeg95_encode_4k"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    Image.open(io.BytesIO(buf.getvalue())).load()
    t["jpeg_decode_4k"] = time.perf_counter() - t0
    del a, c, x, y, im, small, idx, acc, buf
    return t


def _median(v):
    s = sorted(v)
    return s[len(s) // 2]


def measure(mode: str = "warm", runs: int = 3, time_left=None) -> dict:
    """Run the probe here. `time_left()` (seconds, optional) stops the warm runs early; at least one measured run is always
    made. Returns {mode, runs, phases, total, cpu_total, run_totals, imports (cold)}."""
    imports = {}
    if mode == "cold":
        # what a fresh instance pays for these two imports (zero when they are already loaded: noted)
        for name in ("numpy", "PIL.Image"):
            t0 = time.perf_counter()
            loaded = name in sys.modules
            __import__(name)
            imports[name] = {"s": round(time.perf_counter() - t0, 3), "already_loaded": loaded}
    all_runs, cpu0 = [], time.process_time()
    wall0 = time.perf_counter()
    if mode == "warm":
        workload()                                  # the unmeasured warm-up
    last = time.perf_counter() - wall0
    n = 1 if mode == "cold" else max(1, min(runs, RUNS_MAX))
    for i in range(n):
        if i and time_left is not None and time_left() < last * 1.5 + 2.0:
            break
        t1 = time.perf_counter()
        all_runs.append(workload())
        last = time.perf_counter() - t1
    cpu = time.process_time() - cpu0
    phases = {k: round(_median([r[k] for r in all_runs]), 4) for k in PHASES}
    out = {"mode": mode, "runs": len(all_runs), "phases": phases, "total": round(sum(phases.values()), 4),
           "run_totals": [round(sum(r.values()), 4) for r in all_runs],
           "process_cpu_s": round(cpu, 3), "wall_s": round(time.perf_counter() - wall0, 3)}
    if imports:
        out["imports"] = imports
    return out


def factors(phases: dict, baseline: dict) -> dict:
    """slow_factor over the sum of the phases and per phase, against a baseline {phases: {...}} (or {total: s})."""
    b_ph = baseline.get("phases") or {}
    b_total = baseline.get("total") or (sum(b_ph.values()) if b_ph else None)
    total = sum(phases.values())
    out = {"slow_factor": round(total / b_total, 3) if b_total else None}
    if b_ph:
        out["phase_factors"] = {k: round(phases[k] / b_ph[k], 3) for k in PHASES if k in phases and b_ph.get(k)}
    out["baseline_total"] = round(b_total, 4) if b_total else None
    return out


# ----------------------------------------------------------------------------- what the instance says about itself
def _read(path: str) -> str | None:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(65536)
    except OSError:
        return None


def _kb(text: str | None, key: str) -> int | None:
    m = re.search(rf"^{key}:\s+(\d+)\s*kB", text or "", flags=re.M)
    return int(m.group(1)) if m else None


def instance_facts() -> dict:
    """A fixed list of facts about this instance, each best effort (absent when unknown). No environment value outside
    _ENV_FACTS and nothing that identifies a customer."""
    f = {"python": sys.version.split()[0], "platform": sys.platform, "cpu_count": os.cpu_count()}
    try:
        f["cpus_usable"] = len(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        pass
    try:
        import numpy
        import PIL
        f["numpy"], f["pillow"] = numpy.__version__, getattr(PIL, "__version__", None)
    except Exception:  # noqa: a missing package is a fact too, not a failure of the probe
        pass
    mem = _read("/proc/meminfo")
    if mem:
        f["mem_total_mb"] = round((_kb(mem, "MemTotal") or 0) / 1024) or None
        f["mem_available_mb"] = round((_kb(mem, "MemAvailable") or 0) / 1024) or None
    st = _read("/proc/self/status")
    if st:
        f["vm_rss_mb"] = round((_kb(st, "VmRSS") or 0) / 1024, 1)
        f["vm_hwm_mb"] = round((_kb(st, "VmHWM") or 0) / 1024, 1)
    for label, path in (("cgroup_memory_max", "/sys/fs/cgroup/memory.max"), ("cgroup_cpu_max", "/sys/fs/cgroup/cpu.max"),
                        ("cgroup_memory_limit_v1", "/sys/fs/cgroup/memory/memory.limit_in_bytes")):
        v = (_read(path) or "").strip()
        if v:
            f[label] = v[:40]
    try:
        # process age: the boot-relative start time (field 22 of /proc/self/stat) against /proc/uptime
        stat = (_read("/proc/self/stat") or "").rsplit(")", 1)[-1].split()
        up = float((_read("/proc/uptime") or "").split()[0])
        f["process_age_s"] = round(up - int(stat[19]) / os.sysconf("SC_CLK_TCK"), 1)
    except (IndexError, ValueError, OSError, AttributeError):
        pass
    try:
        du = shutil.disk_usage(tempfile.gettempdir())
        f["tmp_total_mb"], f["tmp_free_mb"] = round(du.total / 1048576), round(du.free / 1048576)
    except OSError:
        pass
    env = {k: os.environ[k] for k in _ENV_FACTS if os.environ.get(k)}
    if env:
        f["env"] = env
    return f


# ----------------------------------------------------------------------------- the admin action
def _baseline_from(body: dict):
    """The caller's baseline: {"phases": {phase: seconds}} (all PHASES) or {"total": seconds}; None when absent. A bad
    shape raises ValueError (the action answers 400)."""
    b = body.get("baseline")
    if b is None:
        return None
    if not isinstance(b, dict):
        raise ValueError("baseline must be an object")

    def num(v):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0.001 <= v <= 120:
            raise ValueError("baseline seconds must be numbers between 0.001 and 120")
        return float(v)
    if "phases" in b:
        ph = b["phases"]
        if not isinstance(ph, dict) or set(ph) != set(PHASES):
            raise ValueError("baseline.phases must have exactly the phases " + ", ".join(PHASES))
        return {"phases": {k: num(ph[k]) for k in PHASES}}
    return {"total": num(b.get("total"))}


def run_action(body: dict, time_left=None) -> dict:
    """The body of the admin action: {mode: "cold"|"warm" (default warm), runs: 1 to 5 (warm only, default 3), baseline?}.
    Raises ValueError for a bad request and BlockingIOError while another probe of this process runs."""
    global _RUNS_DONE
    mode = body.get("mode", "warm")
    if mode not in MODES:
        raise ValueError("mode must be cold or warm")
    runs = body.get("runs", 3)
    if isinstance(runs, bool) or not isinstance(runs, int) or not 1 <= runs <= RUNS_MAX:
        raise ValueError(f"runs must be a whole number from 1 to {RUNS_MAX}")
    base = _baseline_from(body)
    if not _LOCK.acquire(blocking=False):
        raise BlockingIOError("probe running")
    try:
        first = _RUNS_DONE == 0
        res = measure(mode, runs, time_left)
        _RUNS_DONE += 1
    finally:
        _LOCK.release()
    if base is None:
        base = {"phases": dict(BASELINE_DEV)} if BASELINE_DEV else {}
        source = "default" if base else "none"
    else:
        source = "request"
    out = {"ok": True, **res, "first_on_instance": first, "baseline_source": source,
           "configured_style_slow_cpu": style_slow_cpu(), "instance": instance_facts()}
    out.update(factors(res["phases"], base) if base else {"slow_factor": None, "baseline_total": None})
    return out


if __name__ == "__main__":     # python api/_lib/cpu_probe.py: one local pass, as JSON (scripts/cpu_probe.py is the fuller tool)
    import json
    print(json.dumps(measure("warm", 3)))
