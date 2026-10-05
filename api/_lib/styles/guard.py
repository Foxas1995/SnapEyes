# -*- coding: utf-8 -*-
"""styles.guard: the two process wide guards of a heavy render, and the memory meter.

A Vercel function has about 2 GB and ONE vCPU (V4 reads the project's real settings). Memory is guarded and CPU must be too: a 4096 px master
is 6 to 25 s of one core and 500 to 1300 MB, so two of them in one instance neither fit in memory nor finish in time. The rule of the
plan (SPIKE, ED17):

  * one memory budget for the process (costs.MEM_BUDGET_MB: 70 percent of the configured function memory): a render declares what it
    needs (est_mb, from the cost table) and the sum of the renders in flight never passes the budget;
  * one semaphore of count 1 for every render estimated above HEAVY_S seconds (a master, a batch of tiles, a preview of many eyes):
    one heavy render at a time per instance.

A new render waits up to WAIT_S for room; with none it is refused with Busy, and the caller answers 503 room_retry (the wait counts against
the invocation's time: the caller looks at the time that is left AFTER it has a slot). Busy says when the room should be there: eta_s, the
seconds the holder that frees it first still has by ITS OWN estimate (None when no holder declared one), so the caller can ask for a back-off of
that length (api/_lib/styles/steps.py _room) and not retry at once: a refusal that is retried at once spends the busy hops of the chain in the
few seconds of the waits (the review of WP6a).

Both guards are released in a finally (a render that raises gives its slot back), and a render that is larger than the whole budget is let in
when nothing else runs (assess() refuses such a plan long before: a guard that could never be satisfied would only be a deadlock).

Nothing here imports numpy or an engine. memory_now() reads what the instance says of itself (Linux: /proc/self/status VmRSS and VmHWM;
Windows, for the development machine: the working set; elsewhere nothing). MemWatch samples the resident size while a step runs and
reports the INCREASE of the resident size over the step (VmRSS), not ru_maxrss: ru_maxrss is the high-water mark of the whole life of a
warm instance and would say nothing about one step. The instance's own VmHWM is reported beside it, labelled as that.
"""
from __future__ import annotations

import contextlib
import os
import threading
import time

WAIT_S = 2.0                 # a new render waits this long for room, then 503 busy_retry
HEAVY_S = 3.0                # a render estimated above this many seconds takes the CPU semaphore
POLL_S = 0.05
SAMPLE_S = 0.1               # MemWatch's sampling interval


class Busy(RuntimeError):
    """No room for this render (kind: "memory" or "cpu"): the caller answers 503 room_retry, with a back-off of eta_s."""

    def __init__(self, kind, detail="", eta_s=None):
        super().__init__(f"no room for a render ({kind}){': ' + detail if detail else ''}")
        self.kind = kind
        self.eta_s = eta_s           # seconds until the holder that frees room first should be done (its own estimate), None when unknown


_COND = threading.Condition()
_STATE = {"mb": 0.0, "heavy": 0, "running": 0}
_HOLDERS = {}                # ticket -> (monotonic start, the estimate in seconds or None, heavy): what Busy.eta_s is read from
_TICKETS = [0]


def reset():
    """Forget every holder (a test that simulates a killed process: the real guard lives and dies with the process)."""
    with _COND:
        _STATE.update(mb=0.0, heavy=0, running=0)
        _HOLDERS.clear()
        _COND.notify_all()


def state():
    with _COND:
        return dict(_STATE)


def _budget_mb():
    from . import costs
    return float(costs.MEM_BUDGET_MB)


def _eta_locked(kind):
    """Seconds until the holder that frees room first should be done, by its own estimate: the heavy holder for "cpu", any holder for "memory". A
    holder that is past its estimate counts 0 (the caller's back-off has a floor of its own); None when no holder declared an estimate. _COND is held."""
    now = time.monotonic()
    rest = [max(0.0, est - (now - t0)) for t0, est, heavy in _HOLDERS.values() if est is not None and (heavy or kind != "cpu")]
    return min(rest) if rest else None


@contextlib.contextmanager
def slot(est_mb=None, est_s=None, wait=None, left=None, budget_mb=None, heavy_s=HEAVY_S):
    """Hold a render's place for the length of the block. est_mb: the memory the render declares (None: none declared, only the CPU
    semaphore applies); est_s: its estimated seconds (above heavy_s it takes the CPU semaphore, and an unknown estimate counts as heavy);
    wait: how long to wait for room (default WAIT_S, read when the slot is asked for); left: the seconds the invocation has left (the wait never takes more than left minus one second).
    Raises Busy."""
    budget = _budget_mb() if budget_mb is None else float(budget_mb)
    mb = max(0.0, float(est_mb)) if est_mb is not None else 0.0
    heavy = est_s is None or est_s > heavy_s
    wait = WAIT_S if wait is None else wait
    limit = float(wait) if left is None else max(0.0, min(float(wait), float(left) - 1.0))
    t_end = time.monotonic() + limit
    taken = False
    ticket = None
    with _COND:
        while True:
            alone = _STATE["running"] == 0
            fits_mem = mb <= 0.0 or alone or _STATE["mb"] + mb <= budget
            fits_cpu = not heavy or _STATE["heavy"] == 0
            if fits_mem and fits_cpu:
                _STATE["mb"] += mb
                _STATE["heavy"] += 1 if heavy else 0
                _STATE["running"] += 1
                _TICKETS[0] += 1
                ticket = _TICKETS[0]
                _HOLDERS[ticket] = (time.monotonic(), None if est_s is None else max(0.0, float(est_s)), heavy)
                taken = True
                break
            rest = t_end - time.monotonic()
            if rest <= 0:
                kind = "cpu" if not fits_cpu else "memory"
                raise Busy(kind, f"{_STATE['mb']:.0f} of {budget:.0f} MB held by {_STATE['running']} render(s)", _eta_locked(kind))
            _COND.wait(min(POLL_S * 4, rest))
    try:
        yield {"mb": mb, "heavy": heavy}
    finally:
        if taken:
            with _COND:
                _HOLDERS.pop(ticket, None)
                _STATE["mb"] = max(0.0, _STATE["mb"] - mb)
                _STATE["heavy"] = max(0, _STATE["heavy"] - (1 if heavy else 0))
                _STATE["running"] = max(0, _STATE["running"] - 1)
                _COND.notify_all()


# ----------------------------------------------------------------------------- the memory meter
def _linux_status():
    try:
        out = {}
        with open("/proc/self/status", encoding="ascii", errors="replace") as f:
            for line in f:
                if line.startswith(("VmRSS:", "VmHWM:")):
                    k, v = line.split(":", 1)
                    out[k] = float(v.split()[0]) / 1024.0           # kB to MB
        return out.get("VmRSS"), out.get("VmHWM")
    except (OSError, ValueError):
        return None, None


_WIN = {}


def _windows_status():
    try:
        if not _WIN:
            import ctypes
            from ctypes import wintypes

            class PMC(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t),
                            ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t),
                            ("PeakPagefileUsage", ctypes.c_size_t)]
            k32 = ctypes.WinDLL("kernel32", use_last_error=True)
            k32.GetCurrentProcess.restype = wintypes.HANDLE
            psapi = ctypes.WinDLL("psapi", use_last_error=True)
            psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
            _WIN.update(ctypes=ctypes, PMC=PMC, k32=k32, psapi=psapi)
        ctypes, PMC = _WIN["ctypes"], _WIN["PMC"]
        pmc = PMC()
        pmc.cb = ctypes.sizeof(PMC)
        if not _WIN["psapi"].GetProcessMemoryInfo(_WIN["k32"].GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
            return None, None
        return pmc.WorkingSetSize / 1048576.0, pmc.PeakWorkingSetSize / 1048576.0
    except Exception:  # noqa: a meter must never cost a render
        return None, None


def memory_now():
    """(VmRSS in MB, VmHWM in MB) of this process: either may be None where the platform says nothing."""
    if os.name == "nt":
        return _windows_status()
    rss, hwm = _linux_status()
    if rss is None:
        try:
            import resource
            ru = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss     # kB on Linux, bytes on macOS: only a last resort for the high-water mark
            hwm = ru / 1048576.0 if os.uname().sysname == "Darwin" else ru / 1024.0
        except Exception:  # noqa
            pass
    return rss, hwm


class MemWatch:
    """The resident size of the process while a step runs: start() takes the size before, a thread samples it every SAMPLE_S, stop() returns
    {peak_mb: the largest resident size seen minus the size before (VmRSS increase over the step), rss_mb: the size before, hwm_mb: the
    instance's own high-water mark, labelled as that}. A platform that reports nothing gives None for all of them."""

    def __init__(self, interval=SAMPLE_S):
        self.interval = interval
        self.before = None
        self.top = None
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        self.before, _ = memory_now()
        self.top = self.before
        if self.before is not None:
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        return self

    def _run(self):
        while not self._stop.wait(self.interval):
            rss, _ = memory_now()
            if rss is not None and (self.top is None or rss > self.top):
                self.top = rss

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(1.0)
        rss, hwm = memory_now()
        if rss is not None and (self.top is None or rss > self.top):
            self.top = rss
        peak = None if self.before is None or self.top is None else max(0.0, self.top - self.before)
        return {"peak_mb": None if peak is None else int(round(peak)), "rss_mb": None if self.before is None else int(round(self.before)),
                "hwm_mb": None if hwm is None else int(round(hwm))}
