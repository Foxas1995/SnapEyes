# -*- coding: utf-8 -*-
"""WP0 of the v3 engine work: the CPU probe (api/_lib/cpu_probe.py, the admin action `cpu_probe`), the pins (requirements.txt,
.python-version), the guard-suite folder (suites/) and the bundle report (scripts/bundle_report.mjs).
Real admin handler over HTTP on a local store folder, synthetic secrets, no network, no image model.
    python test_wp0.py        prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure
Run by suites/run_main.sh as the entry v3wp0 (SNAPEYES_REPO names the checkout)."""
import atexit
import importlib.metadata as md
import json
import math
import os
import re
import shutil
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(REPO, "api")
STORE = os.path.join(HERE, "store_wp0")
ADMIN_SECRET = "wp0-admin-secret-for-tests-0123456789abcdef"
TICKET = "wp0-ticket-secret-for-tests-0123456789abcdef"
FAKE_KEYS = {"GEMINI_API_KEY": "wp0-fake-gemini-key-no-calls", "STRIPE_SECRET_KEY": "sk_test_wp0FakeKey0123456789",
             "RESEND_API_KEY": "re_wp0Fake1234_abcdefghijklmnop"}

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   <- {str(detail)[:500]}"), flush=True)


for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "AWS_", "NOW_", "LAMBDA_")):
        os.environ.pop(k)
if os.path.isdir(STORE):
    shutil.rmtree(STORE)
os.makedirs(STORE)
atexit.register(shutil.rmtree, STORE, ignore_errors=True)   # its own folder only: gone at exit, green, red or crashed
os.environ.update({"STORE_LOCAL_DIR": STORE, "SNAPEYES_TICKET_SECRET": TICKET, "SNAPEYES_ADMIN_SECRET": ADMIN_SECRET,
                   "PYTHONIOENCODING": "utf-8", **FAKE_KEYS})
sys.path.insert(0, API)
import requests  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import ops, store  # noqa: E402
from _lib import cpu_probe as P  # noqa: E402
import admin  # noqa: E402


class D(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        admin.handle(self)


srv = ThreadingHTTPServer(("127.0.0.1", 0), D)
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{srv.server_address[1]}"
KEY = ops.mint_admin_key(30 * 86400)
IP = {"x-real-ip": "203.0.113.9"}


def adm(action, key=None, **body):
    h = {"Content-Type": "application/json", **IP}
    if key is not False:
        h["Authorization"] = "Bearer " + (key or KEY)
    return requests.post(BASE + "/api/admin", data=json.dumps(dict(body, action=action)), headers=h, timeout=120)


BASE_PH = dict(P.BASELINE_DEV)

# ----------------------------------------------------------------------------- 1. the admin action
print("\n== 1. admin action cpu_probe")
r = adm("cpu_probe", key=False)
check("no admin key: 403 admin_denied and nothing measured", r.status_code == 403 and r.json().get("reason") == "admin_denied" and "phases" not in r.json(), r.text)
r = adm("cpu_probe", key="admin-v1.1700000000.0123456789abcdef0123456789abcdef")
check("a key that does not verify: 403", r.status_code == 403, r.text)
check("the action is registered and not audited (read-only: no audit line is written for it)",
      ops.ACTIONS.get("cpu_probe") is ops.a_cpu_probe)

r = adm("cpu_probe", mode="warm", runs=1, baseline={"phases": BASE_PH})
j = r.json()
check("warm, one run, a baseline of the caller: 200 ok", r.status_code == 200 and j.get("ok") is True, r.text[:300])
check("seconds for every phase, all above zero, total = their sum",
      set(j.get("phases", {})) == set(P.PHASES) and all(v > 0 for v in j["phases"].values())
      and abs(j["total"] - sum(j["phases"].values())) < 0.002, j.get("phases"))
check("slow_factor = total / the baseline's total; every phase has its own factor",
      j.get("baseline_source") == "request" and abs(j["slow_factor"] - j["total"] / sum(BASE_PH.values())) < 0.01
      and set(j.get("phase_factors", {})) == set(P.PHASES), (j.get("slow_factor"), j.get("baseline_total")))
check("the first probe of the process says so; mode and runs are echoed", j.get("first_on_instance") is True and j.get("mode") == "warm" and j.get("runs") == 1, j)
check("it reports the configured STYLE_SLOW_CPU (1.6 when unset)", j.get("configured_style_slow_cpu") == 1.6, j.get("configured_style_slow_cpu"))
inst = j.get("instance", {})
check("the instance facts carry the interpreter and package versions",
      inst.get("python") == sys.version.split()[0] and bool(inst.get("numpy")) and bool(inst.get("pillow")) and inst.get("cpu_count"), inst)

r = adm("cpu_probe", mode="cold")
j2 = r.json()
check("cold: one run, imports timed (already loaded here, and it says so), not the first probe now",
      r.status_code == 200 and j2.get("runs") == 1 and j2.get("first_on_instance") is False
      and set(j2.get("imports", {})) == {"numpy", "PIL.Image"} and all(v["already_loaded"] for v in j2["imports"].values()), r.text[:300])
check("without a baseline in the request the built-in default is used, and named", j2.get("baseline_source") == "default" and j2.get("slow_factor"), j2.get("baseline_source"))

for label, body in (("a mode other than cold or warm", {"mode": "hot"}), ("runs 0", {"runs": 0}), ("runs 6", {"runs": 6}),
                    ("runs as a string", {"runs": "3"}), ("runs true", {"runs": True}),
                    ("a baseline that is not an object", {"baseline": 5}), ("a baseline total below the floor", {"baseline": {"total": 0}}),
                    ("a baseline total that is text", {"baseline": {"total": "x"}}), ("a negative baseline total", {"baseline": {"total": -1}}),
                    ("baseline phases missing one phase", {"baseline": {"phases": {k: 1.0 for k in P.PHASES[:-1]}}}),
                    ("baseline phases with an extra one", {"baseline": {"phases": {**{k: 1.0 for k in P.PHASES}, "x": 1.0}}}),
                    ("a baseline phase that is infinite", {"baseline": {"phases": {**{k: 1.0 for k in P.PHASES}, "blur_cumsum": 1e999}}})):
    r = adm("cpu_probe", **body)
    check(f"400 for {label}, nothing measured", r.status_code == 400 and r.json().get("ok") is False and "phases" not in r.json(), (r.status_code, r.text[:200]))

check("a baseline of a single total is accepted (factor by total only)",
      (lambda x: x.status_code == 200 and x.json().get("baseline_total") == 2.0 and "phase_factors" not in x.json())(adm("cpu_probe", runs=1, baseline={"total": 2.0})))

P._LOCK.acquire()
try:
    r = adm("cpu_probe", runs=1)
    check("a second probe while one runs: 503 probe_running with retry, not a second measurement",
          r.status_code == 503 and r.json().get("reason") == "probe_running" and r.json().get("retry") is True and "phases" not in r.json(), r.text[:200])
finally:
    P._LOCK.release()
check("...and the next one runs again", adm("cpu_probe", runs=1).status_code == 200)

os.environ.update({"VERCEL_REGION": "test1", "SNAPEYES_NOT_A_FACT": "must-not-appear", "AWS_LAMBDA_FUNCTION_MEMORY_SIZE": "2048"})
body = adm("cpu_probe", runs=1).text
check("only the listed platform facts are echoed from the environment (VERCEL_REGION yes, SNAPEYES_NOT_A_FACT no)",
      '"VERCEL_REGION": "test1"' in body and '"AWS_LAMBDA_FUNCTION_MEMORY_SIZE": "2048"' in body and "must-not-appear" not in body, body[-400:])
secrets_seen = [v for v in (ADMIN_SECRET, TICKET, KEY, *FAKE_KEYS.values()) if v in body]
check("no secret, key or token of the environment is in the reply", not secrets_seen, secrets_seen)
left = [os.path.join(r_, f) for r_, _, fs in os.walk(STORE) for f in fs]
check("the probe wrote nothing to storage: no audit line, no event, no file at all (CRON_SECRET is unset, so none is kept)", not left, left[:5])
for k in ("VERCEL_REGION", "SNAPEYES_NOT_A_FACT", "AWS_LAMBDA_FUNCTION_MEMORY_SIZE"):
    os.environ.pop(k)

# ----------------------------------------------------------------------------- 2. the maths and STYLE_SLOW_CPU
print("\n== 2. factors and STYLE_SLOW_CPU")
ph = {k: 2.0 for k in P.PHASES}
bs = {"phases": {k: 1.0 for k in P.PHASES}}
f = P.factors(ph, bs)
check("factors: twice the baseline everywhere gives 2.0 overall and per phase", f["slow_factor"] == 2.0 and set(f["phase_factors"].values()) == {2.0}, f)
check("factors by total only", P.factors(ph, {"total": 7.0})["slow_factor"] == 2.0 and "phase_factors" not in P.factors(ph, {"total": 7.0}))
for raw, want in ((None, 1.6), ("", 1.6), ("2.4", 2.4), ("0.5", 1.0), ("9", 6.0), ("abc", 1.6), ("nan", 1.6), ("inf", 1.6), ("-3", 1.0), (" 1.8 ", 1.8)):
    if raw is None:
        os.environ.pop("STYLE_SLOW_CPU", None)
    else:
        os.environ["STYLE_SLOW_CPU"] = raw
    got = P.style_slow_cpu()
    check(f"STYLE_SLOW_CPU {raw!r} -> {want}", math.isclose(got, want), got)
os.environ.pop("STYLE_SLOW_CPU", None)
check("the built-in baseline names every phase and is plausible (0.4 to 4 s in all)", set(P.BASELINE_DEV) == set(P.PHASES) and 0.4 < sum(P.BASELINE_DEV.values()) < 4.0)

# ----------------------------------------------------------------------------- 3. the pins
print("\n== 3. pins")
reqs = [ln.split("#", 1)[0].strip() for ln in open(os.path.join(REPO, "requirements.txt"), encoding="utf-8")]
reqs = [x for x in reqs if x]
pins = {}
for x in reqs:
    m = re.fullmatch(r"([A-Za-z0-9_.-]+)==([0-9][0-9A-Za-z.+!-]*)", x)
    if m:
        pins[m.group(1).lower()] = m.group(2)
check("requirements.txt: exactly the four packages, each pinned with ==", set(pins) == {"numpy", "pillow", "requests", "onnxruntime"} and len(pins) == len(reqs), reqs)
pv = open(os.path.join(REPO, ".python-version"), "rb").read()
check(".python-version: a major.minor and one line feed, no carriage return", re.fullmatch(rb"3\.[0-9]{2}\n", pv) is not None, pv)
drift = {}
for name, want in pins.items():
    try:
        have = md.version(name)
    except md.PackageNotFoundError:
        have = None
    if have != want:
        drift[name] = (have, want)
check("the interpreter that runs the suites has the pinned packages (otherwise the green list is for other versions)", not drift, drift)
vj = json.load(open(os.path.join(REPO, "vercel.json"), encoding="utf-8"))
excl = [c.get("excludeFiles", "") for c in vj["functions"].values()]
check("vercel.json: every functions entry excludes suites/** (the test sources never ride into a function)", excl and all("suites/**" in e for e in excl), excl)
vi = open(os.path.join(REPO, ".vercelignore"), encoding="utf-8").read().split()
check(".vercelignore keeps /suites/ out of the upload", "/suites/" in vi, vi)

# ----------------------------------------------------------------------------- 4. the suite folder
print("\n== 4. suites/ folder")
S = os.path.join(REPO, "suites")
lst = [ln.strip() for ln in open(os.path.join(S, "suites.list"), encoding="utf-8") if ln.strip() and not ln.lstrip().startswith("#")]
missing = []
for e in lst:
    name, d, script = e.split(":")[:3]
    if not (os.path.isfile(os.path.join(S, "tree", d, script)) or os.path.isfile(os.path.join(REPO, d, script))):
        missing.append(e)
names = [e.split(":")[0] for e in lst]
check("suites.list: every entry's script exists (in suites/tree or in the repository) and names are unique", not missing and len(set(names)) == len(names), missing)
check("suites.list keeps the twenty suites of the baseline", {"r2", "r3", "r4", "r5", "fix", "admin", "pay", "advance", "refund", "preview", "review", "fixmk",
                                                            "markets", "au", "payrev", "fixer", "oldpay", "oldadv", "oldadmin", "exp"} <= set(names), names)
bad_dash, bad_path = [], []
for root, ds, fs in os.walk(S):
    ds[:] = [d for d in ds if d not in ("out", "private", "__pycache__")]
    for fn in fs:
        p = os.path.join(root, fn)
        if fn.endswith((".jpg", ".png", ".pyc")):
            continue
        t = open(p, encoding="utf-8", errors="replace").read()
        if re.search("[" + "".join(chr(c) for c in range(0x2012, 0x2016)) + "]", t):
            bad_dash.append(os.path.relpath(p, REPO))
        if re.search(r"scratchpad|AppData[\\/]Local[\\/]Temp", t):
            bad_path.append(os.path.relpath(p, REPO))
check("no file of suites/ holds an en or em dash", not bad_dash, bad_dash)
check("no file of suites/ names a path of the session scratch folder", not bad_path, bad_path)
fx = [ln for ln in open(os.path.join(S, "fixtures.sha256"), encoding="utf-8") if ln.strip() and not ln.startswith("#")]
check("fixtures.sha256 lists the 20 private fixtures (hashes only; the images are not in the repository)", len(fx) == 20 and all(re.match(r"^[0-9a-f]{64}\s", x) for x in fx), len(fx))
g = subprocess.run(["git", "-C", REPO, "ls-files", "suites/private", "suites/out"], capture_output=True, text=True)
check("git tracks nothing under suites/private or suites/out", g.returncode != 0 or not g.stdout.strip(), g.stdout[:200])
gi = subprocess.run(["git", "-C", REPO, "check-ignore", "suites/private/fixtures/x.jpg", "suites/out/x"], capture_output=True, text=True)
check("both are ignored by .gitignore", gi.returncode != 0 or len(gi.stdout.split()) == 2, gi.stdout)
shs = [f for f in os.listdir(S) if f.endswith(".sh")]
crlf = [f for f in shs if b"\r\n" in open(os.path.join(S, f), "rb").read()]
check("the shell scripts have LF line endings", shs and not crlf, crlf)

# ----------------------------------------------------------------------------- 5. the bundle report
print("\n== 5. bundle report")
r = subprocess.run(["node", os.path.join(REPO, "scripts", "bundle_report.mjs"), "--json", "--check"], cwd=REPO, capture_output=True, text=True, encoding="utf-8")
try:
    rep = json.loads(r.stdout)
except ValueError:
    rep = {}
check("bundle_report.mjs --check exits 0 and prints JSON", r.returncode == 0 and bool(rep), (r.stdout + r.stderr)[-400:])
fn = [x["name"] for x in rep.get("rows", [])]
check("it finds the eleven functions of api/", len(fn) == 11 and "compose" in fn and "master_compose" in fn and "admin" in fn, fn)
check("it sees only api/ and root files in the bundle (no other folder rides along)", set(rep.get("top_level_included", {})) <= {"api", "(root files)"}, rep.get("top_level_included"))
py = rep.get("python", {}).get("windows_or_local", {})
check("it sizes the installed packages and lists numpy, pillow and onnxruntime", py.get("total_mib", 0) > 50 and {"numpy", "onnxruntime"} <= {d["name"].lower() for d in py.get("dists", [])}, py.get("error") or py.get("total_mib"))

# ----------------------------------------------------------------------------- 6. the interpreter matrix
print()
print("== 6. compile matrix")
r = subprocess.run([sys.executable, os.path.join(S, "compile_matrix.py")], cwd=REPO, capture_output=True, text=True, encoding="utf-8")
ok_lines = re.findall(r"python (3[.][0-9]+): compileall api ok", r.stdout)
check("compile_matrix.py: compileall api passes under every installed Python of 3.12, 3.13 and 3.14, and no file uses syntax newer than 3.12",
      r.returncode == 0 and bool(ok_lines) and re.search(r"syntax of [0-9]+ api files as Python 3[.]12: ok", r.stdout) is not None, r.stdout[-500:] + r.stderr[-300:])
check("...and it names each of the three (an interpreter that is not installed is reported, not skipped silently)",
      all(("python " + v + ":") in r.stdout for v in ("3.12", "3.13", "3.14")), r.stdout)

# ----------------------------------------------------------------------------- 7. the fixes after the review of WP0
print()
print("== 7. review fixes: the local store under threads, the probe's inputs, the runners")
import tempfile  # noqa: E402
import time  # noqa: E402
import unittest.mock as mock  # noqa: E402

# 7a. the local folder store on Windows: a file that another thread has open or is replacing refuses open, rename and delete for a
# moment; six parallel drafts of one work ticket (suite fix, A2) failed one run in thirteen before store._retry_busy.
calls = []


def flaky(n, exc=PermissionError):
    def fn():
        calls.append(1)
        if len(calls) <= n:
            raise exc("busy")
        return "done"
    return fn


calls.clear()
with mock.patch.object(store.os, "name", "nt"), mock.patch.object(store.time, "sleep", lambda s: None):
    got = store._retry_busy(flaky(5))
check("store._retry_busy: on Windows a PermissionError is tried again and the call then succeeds", got == "done" and len(calls) == 6, (got, len(calls)))
calls.clear()
with mock.patch.object(store.os, "name", "nt"), mock.patch.object(store.time, "sleep", lambda s: None):
    try:
        store._retry_busy(flaky(10 ** 6), tries=7)
        err = None
    except PermissionError as e:
        err = e
check("...after the last try the PermissionError stays (a real refusal is not swallowed): exactly 7 tries", isinstance(err, PermissionError) and len(calls) == 7, (err, len(calls)))
calls.clear()
with mock.patch.object(store.os, "name", "posix"), mock.patch.object(store.time, "sleep", lambda s: None):
    try:
        store._retry_busy(flaky(1))
        err = None
    except PermissionError as e:
        err = e
check("...and off Windows there is no retry at all: the first PermissionError is raised", isinstance(err, PermissionError) and len(calls) == 1, len(calls))
calls.clear()
try:
    store._retry_busy(flaky(1, FileNotFoundError))
    err = None
except FileNotFoundError as e:
    err = e
check("...other errors (a missing file: delete() relies on it) pass through at once", isinstance(err, FileNotFoundError) and len(calls) == 1, len(calls))

stress_errors, stress_n = [], [0]


def hammer(worker):
    for i in range(60):
        try:
            if worker % 3 == 0:
                store.put("wp0stress/ticket.json", b'{"w": %d, "i": %d}' % (worker, i), "application/json", upsert=True)
            elif worker % 3 == 1:
                got_ = store.get("wp0stress/ticket.json")
                if got_ is not None:
                    json.loads(got_)
            else:
                store.put(f"wp0stress/gone_{worker}_{i % 4}.json", b"{}", "application/json", upsert=True)
                store.delete(f"wp0stress/gone_{worker}_{i % 4}.json")
            stress_n[0] += 1
        except Exception as e:  # noqa: the point is that nothing is raised
            stress_errors.append(f"{type(e).__name__}: {str(e)[:80]}")


store.put("wp0stress/ticket.json", b'{"w": -1}', "application/json", upsert=True)
ths = [threading.Thread(target=hammer, args=(w,)) for w in range(9)]
[t.start() for t in ths]
[t.join() for t in ths]
check("the local store under 9 threads (replace, read and delete of the same files, 540 calls): no error, no torn read",
      not stress_errors and stress_n[0] == 540, (stress_n[0], stress_errors[:3]))

# 7b. the probe's inputs and its cold mode
for label, body in (("a whole number too big for a float as the baseline total", {"baseline": {"total": 10 ** 400}}),
                    ("the same as one baseline phase", {"baseline": {"phases": {**{k: 1.0 for k in P.PHASES}, "blur_cumsum": 10 ** 400}}}),
                    ("a negative one", {"baseline": {"total": -(10 ** 400)}})):
    r = adm("cpu_probe", **body)
    check(f"400, not 500, for {label}", r.status_code == 400 and r.json().get("ok") is False and "phases" not in r.json(), (r.status_code, r.text[:200]))
r = adm("cpu_probe", mode="cold", runs=1)
fresh = r.json().get("imports_fresh_interpreter", {})
check("cold: the import cost is also measured in a fresh interpreter (the admin function has numpy and Pillow loaded already)",
      r.status_code == 200 and fresh.get("numpy", 0) > 0 and fresh.get("PIL.Image", 0) > 0 and "error" not in fresh, (r.status_code, fresh))
with mock.patch.object(sys, "executable", os.path.join(STORE, "no-such-python")):
    bad_child = P.fresh_import_seconds(5.0)
check("...and when the child cannot start the answer says so instead of failing the probe", "error" in bad_child, bad_child)
check("the warm reply has no fresh-interpreter figure (only cold pays for the child)", "imports_fresh_interpreter" not in adm("cpu_probe", runs=1).json())

# 7c. scripts/cpu_probe.py never follows a redirect with the admin key
sys.path.insert(0, os.path.join(REPO, "scripts"))
import cpu_probe as CP  # noqa: E402
seen = []


class Target(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        seen.append(("GET", self.headers.get("Authorization")))
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        seen.append(("POST", self.headers.get("Authorization")))
        self.send_response(200)
        self.end_headers()


tgt = ThreadingHTTPServer(("127.0.0.1", 0), Target)
threading.Thread(target=tgt.serve_forever, daemon=True).start()


def redirector(code):
    class R(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_POST(self):
            self.send_response(code)
            self.send_header("Location", f"http://127.0.0.1:{tgt.server_address[1]}/elsewhere")
            self.end_headers()
    return R


for code in (301, 302, 303, 307, 308):
    red = ThreadingHTTPServer(("127.0.0.1", 0), redirector(code))
    threading.Thread(target=red.serve_forever, daemon=True).start()
    st, rep = CP.post(f"http://127.0.0.1:{red.server_address[1]}", "admin-v1.1700000000.0123456789abcdef0123456789abcdef", {"action": "cpu_probe"}, {})
    red.shutdown()
    check(f"scripts/cpu_probe.py: a {code} answer is not followed, the caller is told", st == code and str(rep.get("reason", "")).startswith("redirect_refused"), (st, rep))
check("...and the redirect target never received a request, so no Authorization header", not seen, seen)
tgt.shutdown()

# 7d. the runner of the suites and the result table
tmp = tempfile.mkdtemp(prefix="wp0_runner_")
try:
    for name, code in (("aa", 0), ("bb", 77)):
        open(os.path.join(tmp, name + ".exit"), "w").write(f"{name} EXIT {code}\n")
        open(os.path.join(tmp, name + ".out"), "w").write("PASS one\n" if code == 0 else "SKIPPED: x\n")
    env_ = {k: v for k, v in os.environ.items() if k != "SNAPEYES_ALLOW_SKIPPED"}
    run = lambda *a, **kw: subprocess.run([sys.executable, os.path.join(S, "summary.py"), tmp, *a], capture_output=True, text=True, encoding="utf-8", env={**env_, **kw})
    r = run()
    check("summary.py: a skipped suite makes the run INCOMPLETE: exit 1 and the last lines say which suite did not run",
          r.returncode == 1 and "INCOMPLETE: bb did not run" in r.stdout and "1 skipped" in r.stdout, (r.returncode, r.stdout[-300:]))
    r = run("--allow-skipped")
    check("...--allow-skipped accepts it on purpose (exit 0, still named)", r.returncode == 0 and "INCOMPLETE: bb" in r.stdout and "Accepted" in r.stdout, (r.returncode, r.stdout[-300:]))
    r = run(SNAPEYES_ALLOW_SKIPPED="1")
    check("...and so does SNAPEYES_ALLOW_SKIPPED=1", r.returncode == 0, (r.returncode, r.stdout[-200:]))
    os.remove(os.path.join(tmp, "bb.exit"))
    open(os.path.join(tmp, "bb.exit"), "w").write("bb EXIT 0\n")
    open(os.path.join(tmp, "bb.out"), "w").write("PASS two\n")
    r = run()
    check("...a run with nothing skipped and nothing red still exits 0", r.returncode == 0 and "INCOMPLETE" not in r.stdout, (r.returncode, r.stdout[-200:]))
finally:
    shutil.rmtree(tmp, ignore_errors=True)


def working_bash():
    """A bash that runs scripts: on Windows plain "bash" can be the WSL launcher of System32, found before Git's by CreateProcess."""
    for cand in (shutil.which("bash"), os.path.join(os.environ.get("EXEPATH", ""), "bin", "bash.exe"), "/bin/bash"):
        if cand and os.path.isfile(cand):
            try:
                if subprocess.run([cand, "-c", "echo ok"], capture_output=True, text=True, timeout=30).stdout.strip() == "ok":
                    return cand
            except (OSError, subprocess.SubprocessError):
                pass
    return None


BASH = working_bash()
check("a working bash is available for the runner checks", BASH is not None, shutil.which("bash"))
for argv_ in ([], ["a", "b"], ["a", "b", ""]):
    r = subprocess.run([BASH, os.path.join(S, "run_all.sh"), *argv_], capture_output=True, text=True, encoding="utf-8", timeout=60, cwd=tempfile.gettempdir())
    check(f"run_all.sh with {len(argv_)} argument(s): usage message, exit 2, nothing deleted (it used to expand rm -f /*)",
          r.returncode == 2 and "usage" in r.stderr, (r.returncode, r.stderr[:200]))
r = subprocess.run([BASH, os.path.join(S, "run_all.sh"), "a", "b", "/"], capture_output=True, text=True, encoding="utf-8", timeout=60, cwd=tempfile.gettempdir())
check("run_all.sh refuses a results folder of / and of .", r.returncode == 2 and "refusing" in r.stderr, (r.returncode, r.stderr[:200]))

# 7e. the page-code runner counts every node:test test, and an empty file is a failure
tt = tempfile.mkdtemp(prefix="wp0_tstest_")
try:
    open(os.path.join(tt, "three.test.ts"), "w").write("import test from 'node:test';\ntest('one', () => {});\ntest('two', () => {});\ntest('three', () => {});\n")
    open(os.path.join(tt, "empty.test.ts"), "w").write("import test from 'node:test';\nvoid test;\n")
    open(os.path.join(tt, "bad.test.ts"), "w").write("import test from 'node:test';\nimport assert from 'node:assert';\ntest('fine', () => {});\ntest('broken', () => { assert.equal(1, 2); });\ntest('later', { skip: true }, () => {});\n")
    runner = ["node", os.path.join(REPO, "scripts", "run_ts_tests.mjs")]
    r3 = subprocess.run([*runner, os.path.join(tt, "three.test.ts")], cwd=REPO, capture_output=True, text=True, encoding="utf-8", timeout=120)
    check("run_ts_tests.mjs: a node:test file of three tests counts three PASS lines (not one) and exits 0",
          r3.returncode == 0 and len(re.findall(r"^PASS ", r3.stdout, flags=re.M)) == 3 and "3 of 3 passed" in r3.stdout, (r3.returncode, r3.stdout[-300:]))
    re_ = subprocess.run([*runner, os.path.join(tt, "empty.test.ts")], cwd=REPO, capture_output=True, text=True, encoding="utf-8", timeout=120)
    check("...a node:test file that defines no test is a FAIL, never a pass", re_.returncode == 1 and "defines no node:test test" in re_.stdout and not re.search(r"^PASS ", re_.stdout, flags=re.M), (re_.returncode, re_.stdout[-300:]))
    rb = subprocess.run([*runner, os.path.join(tt, "bad.test.ts")], cwd=REPO, capture_output=True, text=True, encoding="utf-8", timeout=120)
    check("...a failing test and a skipped one are FAIL lines, the good one a PASS line, and the exit is 1",
          rb.returncode == 1 and len(re.findall(r"^PASS ", rb.stdout, flags=re.M)) == 1 and len(re.findall(r"^FAIL ", rb.stdout, flags=re.M)) == 2, (rb.returncode, rb.stdout[-300:]))
finally:
    shutil.rmtree(tt, ignore_errors=True)

# 7f. the bundle report no longer relies on .vercelignore, and .vercelignore carries what .gitignore keeps out of git
BR = open(os.path.join(REPO, "scripts", "bundle_report.mjs"), encoding="utf-8").read()


def mini_tree(exclude):
    d = tempfile.mkdtemp(prefix="wp0_bundle_")
    for sub in ("scripts", "api", "suites"):
        os.makedirs(os.path.join(d, sub))
    open(os.path.join(d, "scripts", "bundle_report.mjs"), "w", encoding="utf-8").write(BR)
    shutil.copy(os.path.join(REPO, "scripts", "bundle_deps.py"), os.path.join(d, "scripts", "bundle_deps.py"))
    open(os.path.join(d, "api", "x.py"), "w").write("x = 1\n")
    open(os.path.join(d, "suites", "t.py"), "w").write("t = 1\n")
    open(os.path.join(d, ".vercelignore"), "w").write("/suites/\n")
    json.dump({"functions": {"api/**/*.py": {"maxDuration": 60, "excludeFiles": exclude}}}, open(os.path.join(d, "vercel.json"), "w"))
    return d


for exclude, want_rc in (("{scripts/**,suites/**}", 0), ("{scripts/**}", 1)):
    d = mini_tree(exclude)
    try:
        r = subprocess.run(["node", os.path.join(d, "scripts", "bundle_report.mjs"), "--check"], cwd=d, capture_output=True, text=True, encoding="utf-8", timeout=120,
                           env=dict(os.environ))
        check(f"bundle_report --check with excludeFiles {exclude} and .vercelignore naming /suites/: exit {want_rc}"
              + (" (suites/ would ride into every function if the Git deployment ignores .vercelignore)" if want_rc else ""),
              r.returncode == want_rc and (want_rc == 0 or "suites" in r.stdout), (r.returncode, r.stdout[-300:], r.stderr[-200:]))
    finally:
        shutil.rmtree(d, ignore_errors=True)
gi = [ln.strip() for ln in open(os.path.join(REPO, ".gitignore"), encoding="utf-8") if ln.strip() and not ln.startswith(("#", "!"))]
vil = {ln.strip() for ln in open(os.path.join(REPO, ".vercelignore"), encoding="utf-8")}
missing_vi = [x for x in gi if not x.startswith("suites/") and x not in vil]
check(".vercelignore repeats every .gitignore entry (a CLI upload reads one of the two files, not both: not verified, V2)", not missing_vi, missing_vi)

print(f"\n{sum(RESULTS)} of {len(RESULTS)} passed")
srv.shutdown()
sys.stdout.flush()
sys.exit(0 if all(RESULTS) else 1)
