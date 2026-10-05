# -*- coding: utf-8 -*-
"""Unit and integration tests of the admin panel backend (api/admin.py, api/_lib/ops.py, api/_lib/events.py, the event
hooks, scripts/mint_admin.py), against a local store folder, a fake Stripe + Resend + legal-pack stub and the real
handlers served over HTTP in this process. No real key, no Gemini call: every model call is replaced (a 4K "render" is
the preview scaled up). Usage: python test_admin.py [filter]"""
import os, sys, io, re, json, time, base64, shutil, hashlib, secrets, threading, subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))   # wave-pv/tests/admin
REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh (it names the checkout under test)")
API = os.path.join(REPO, "api")
FIX = os.path.join(SP, "wave-b", "try-multi", "fixtures")
STORE = os.path.join(HERE, "store_unit")
LEGAL = os.path.join(HERE, "dist", "legal", "order-mail.json")
ONLY = sys.argv[1] if len(sys.argv) > 1 else ""

SK = "sk_test_" + "AdminFake0123456789abcdef"
WHSEC = "whsec_" + "YWRtaW4tdGVzdC1zZWNyZXQtZm9yLXRlc3Rz"
RESEND = "re_Admin1234_abcdefghijklmnop"
SECRET = "admin-unit-test-secret-0123456789"
ADMIN_SECRET = "admin-panel-own-secret-for-tests-0123456789abcdef"
CRON = "cron-test-secret-0123456789"

ok_all, n_checks, fails = True, 0, []


def check(label, cond, info=""):
    global ok_all, n_checks
    n_checks += 1
    ok_all &= bool(cond)
    if not cond:
        fails.append(label)
    print(("PASS " if cond else "FAIL ") + label + (f"  [{info}]" if info and not cond else ""), flush=True)


# ---------------------------------------------------------------------------------------------------- the stub
class Fake:
    emails = []
    refunds = []
    fail_refund = []


class Stub(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("content-length") or 0))
        path = urlsplit(self.path).path
        if path == "/emails":
            if self.headers.get("Authorization") != "Bearer " + RESEND:
                return self._send(401, {"message": "bad key"})
            Fake.emails.append((json.loads(raw), self.headers.get("Idempotency-Key")))
            return self._send(200, {"id": "email_" + secrets.token_hex(4)})
        if path == "/v1/refunds":
            if self.headers.get("Authorization") != "Bearer " + SK:
                return self._send(401, {"error": {"type": "invalid_request_error"}})
            p = {k: v[0] for k, v in parse_qs(raw.decode()).items()}
            Fake.refunds.append((p, self.headers.get("Idempotency-Key")))
            if Fake.fail_refund:
                code = Fake.fail_refund.pop(0)
                return self._send(code, {"error": {"type": "invalid_request_error", "code": "charge_already_refunded",
                                                   "message": "injected"}})
            return self._send(200, {"id": "re_" + secrets.token_hex(6), "object": "refund", "status": "succeeded",
                                    "amount": 3997, "currency": "eur", "payment_intent": p.get("payment_intent")})
        self._send(404, {})

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/legal/order-mail.json":
            with open(LEGAL, encoding="utf-8") as f:
                return self._send(200, json.load(f))
        self._send(404, {"error": {"type": "invalid_request_error", "code": "resource_missing"}})


stub = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
threading.Thread(target=stub.serve_forever, daemon=True).start()
STUB = f"http://127.0.0.1:{stub.server_address[1]}"

# ---------------------------------------------------------------------------------------------------- environment
for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_")):
        os.environ.pop(k)
if os.path.isdir(STORE):
    shutil.rmtree(STORE)
os.makedirs(STORE)
os.environ.update({"STORE_LOCAL_DIR": STORE, "SNAPEYES_TICKET_SECRET": SECRET, "SNAPEYES_ADMIN_SECRET": ADMIN_SECRET,
                   "CRON_SECRET": CRON, "STRIPE_SECRET_KEY": SK,
                   "STRIPE_WEBHOOK_SECRET": WHSEC, "RESEND_API_KEY": RESEND, "STRIPE_API_BASE": STUB,
                   "RESEND_API_BASE": STUB, "LEGAL_PACK_BASE": STUB, "GEMINI_API_KEY": "fake-key-no-calls",
                   "PYTHONIOENCODING": "utf-8"})

sys.path.insert(0, API)
import requests  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import store, pay, events as E, ops  # noqa: E402
import admin, order, analyze, deglare, enhance, compose, master_eye, master_compose, health  # noqa: E402,F401

MODS = {m.__name__: m for m in (admin, order, analyze, deglare, enhance, compose, master_eye, master_compose, health)}


class D(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _r(self):
        name = urlsplit(self.path).path.rstrip("/").rsplit("/", 1)[-1]
        m = MODS.get(name)
        if not m:
            self.send_response(404)
            self.end_headers()
            return
        m.handle(self)
    do_GET = do_POST = _r


srv = ThreadingHTTPServer(("127.0.0.1", 0), D)
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{srv.server_address[1]}"


def post(path, body, headers=None, **kw):
    h = {"Content-Type": "application/json"}
    h.update(headers or {})
    return requests.post(BASE + path, data=json.dumps(body), headers=h, timeout=120, **kw)


def admin_key(days=30, kind=None):
    return ops.mint_admin_key(int(days * 86400), kind)


KEY = admin_key()
IP = {"x-real-ip": "203.0.113.7"}


def adm(action, key=None, ip=IP, **body):
    h = dict(ip)
    if key is not False:
        h["Authorization"] = "Bearer " + (key or KEY)
    return post("/api/admin", dict(body, action=action), h)


def reset_limits():
    ops._FAILS.clear()
    ops._BLOCKED.clear()
    E._SEEN.update({"all": [], "error": [], "errors_today": 0})


def files(prefix):
    root = os.path.join(STORE, *prefix.split("/"))
    out = []
    for d, _, fs in os.walk(root):
        for f in fs:
            out.append(os.path.relpath(os.path.join(d, f), STORE).replace("\\", "/"))
    return sorted(out)


def events_now():
    """Every stored event, oldest first (by its time, then its name)."""
    out = []
    for p in files("ops/events"):
        if not p.endswith(".json"):
            continue              # a write still on its way (the local store's .part file)
        try:
            with open(os.path.join(STORE, p), encoding="utf-8") as f:
                out.append((p, json.load(f)))
        except (OSError, ValueError):
            pass
    return sorted(out, key=lambda x: (x[1].get("t") or 0, x[0]))


def settle(quiet=0.4, limit=3.0):
    """Wait until no event has been written for `quiet` s (error events are written after their reply went out)."""
    t_end, last, n = time.time() + limit, time.time(), len(files("ops/events"))
    while time.time() < t_end:
        time.sleep(0.05)
        m = len(files("ops/events"))
        if m != n:
            n, last = m, time.time()
        elif time.time() - last >= quiet:
            break


def snap():
    settle()
    return {p for p, _ in events_now()}


def section(name):
    print(f"\n==== {name}", flush=True)
    return not ONLY or ONLY in name


# ---------------------------------------------------------------------------------------------------- fixtures
def fixture_b64(name, field):
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return json.load(f)[field]


CROP_B64 = fixture_b64("deglare_sample_ai.json", "crop")
PREVIEW_B64 = fixture_b64("enhance_sample_ai.json", "image")
CROP, PREVIEW = base64.b64decode(CROP_B64), base64.b64decode(PREVIEW_B64)
CONSENT = {"version": pay.CONSENT_VERSION, "at": pay.iso(time.time() - 600), "lang": "en", "text": pay.CONSENT_TEXT["en"],
           "text_sha256": hashlib.sha256(pay.CONSENT_TEXT["en"].encode()).hexdigest()[:16]}


def put_json(path, obj):
    store.put(path, store.json_bytes(obj), "application/json", upsert=True)


def make_order(oid, paid=False, eyes=1, style="deep_nebula", email="kunde@example.com", mail=None, age=0, live=False,
               names="Anna <img src=x onerror=alert(1)>", checkout=False):
    k = pay.access_key(oid)
    now = int(time.time()) - age
    rec = {"v": 1, "order": oid, "created_at": now, "created": pay.iso(now), "key_sha": pay.key_sha(k), "lang": "en"}
    spec = {"eyes": eyes, "style": style, "layout": L.multi_layout(eyes), "names": names, "title": "", "lang": "en"}
    if checkout or paid:
        rec["checkout"] = {"session_id": "cs_test_" + secrets.token_hex(8), "amount": pay.price_cents(eyes, style), "spec": spec}
    put_json(f"orders/{oid}/order.json", rec)
    for i in range(1, eyes + 1):
        uid = secrets.token_hex(4)
        cp, pp = f"orders/{oid}/draft/eye_{i}_crop_{uid}.jpg", f"orders/{oid}/draft/eye_{i}_preview_{uid}.jpg"
        store.put(cp, CROP, "image/jpeg", upsert=True)
        store.put(pp, PREVIEW, "image/jpeg", upsert=True)
        put_json(f"orders/{oid}/draft/eye_{i}.json", {
            "eye": i, "pad": 1.12, "ref": None, "uploaded_at": now, "uploaded": pay.iso(now),
            "crop": {"path": cp, "type": "image/jpeg", "side": 1024, "bytes": len(CROP), "sha256": hashlib.sha256(CROP).hexdigest()},
            "preview": {"path": pp, "type": "image/jpeg", "side": 1024, "bytes": len(PREVIEW), "sha256": hashlib.sha256(PREVIEW).hexdigest()}})
    if paid:
        put_json(f"orders/{oid}/paid.json", {
            "paid": True, "order": oid, "session_id": rec["checkout"]["session_id"], "payment_intent": "pi_test_" + oid.replace("-", "")[:20],
            "amount_total": pay.price_cents(eyes, style), "currency": "eur", "livemode": live, "email": email, "paid_at": now,
            "paid_iso": pay.iso(now), "source": "webhook", "event_id": None, "spec": spec, "consent": CONSENT})
    if mail:
        put_json(f"orders/{oid}/mail_delivery.json", {"state": mail, "t": time.time(), "result": mail})
    return k


def day_id(t=None):
    return pay.day(t)


# ==================================================================================================== 1. auth
if section("auth"):
    reset_limits()
    r = adm("me")
    check("a valid key logs in (200, kind admin-v1)", r.status_code == 200 and r.json().get("kind") == "admin-v1", r.text[:200])
    check("me says when the key expires", abs(r.json().get("expires_at", 0) - (time.time() + 30 * 86400)) < 60)
    r = adm("me", key=False)
    check("no Authorization header: 403 admin_denied", r.status_code == 403 and r.json().get("reason") == "admin_denied", r.text[:200])
    bad = KEY[:-1] + ("0" if KEY[-1] != "0" else "1")
    check("a changed signature: 403", adm("me", key=bad).status_code == 403)
    check("an expired key: 403", adm("me", key=ops.mint_admin_key(-10, "admin-v1")).status_code == 403)
    check("a work ticket is no admin key: 403", adm("me", key=L.mint_ticket("work", 900)).status_code == 403)
    check("an admin key is no work ticket", not L.check_ticket(KEY, kind="work"))
    check("an admin key opens no order", not L.check_ticket(KEY, kind=store.unlock_kind("260929-abcdef01")))
    check("a key living longer than 90 days: 403", adm("me", key=ops.mint_admin_key(120 * 86400, "admin-v1")).status_code == 403)
    # the admin secret (review finding: keys used to fall back to a secret derived from the Gemini key)
    reset_limits()
    check("an admin-v1 ticket signed with the ticket secret (the old scheme) is no admin key: 403",
          adm("me", key=L.mint_ticket("admin-v1", 3600), ip={"x-real-ip": "198.51.100.40"}).status_code == 403)
    check("an admin key is no admin-v1 ticket of the ticket secret either", not L.check_ticket(KEY, kind="admin-v1"))
    r = adm("summary")
    check("summary says which secret signs the admin keys", r.json().get("admin", {}).get("secret") == "SNAPEYES_ADMIN_SECRET", r.text[:200])
    reset_limits()
    n_marks = len(files("ops/adminfail"))
    os.environ.pop("SNAPEYES_ADMIN_SECRET")
    os.environ["SNAPEYES_TICKET_SECRET"] = "short-ticket-secret-01234"          # 25 characters
    r = adm("me")
    check("no admin secret (ticket secret under 32 characters): 503 admin_not_configured, even for a once-good key",
          r.status_code == 503 and r.json().get("reason") == "admin_not_configured", r.text[:200])
    os.environ.pop("SNAPEYES_TICKET_SECRET")
    gem_key = L.mint_ticket("admin-v1", 3600)                                   # the old fallback: Gemini-derived secret
    r = adm("me", key=gem_key)
    check("only the Gemini key set: 503 admin_not_configured, a key minted from the Gemini key is refused",
          r.status_code == 503 and r.json().get("reason") == "admin_not_configured", r.text[:200])
    check("no admin secret derived from the Gemini key", ops.admin_secret() is None and ops.admin_secret_source() == "")
    try:
        ops.mint_admin_key(60)
        refused = False
    except RuntimeError as e:
        refused = "SNAPEYES_ADMIN_SECRET" in str(e)
    check("mint_admin_key raises, naming SNAPEYES_ADMIN_SECRET", refused)
    check("503 answers write no failed-login marker", len(files("ops/adminfail")) == n_marks)
    os.environ["SNAPEYES_TICKET_SECRET"] = SECRET + "-long-enough"             # 44 characters: the fallback
    kt = ops.mint_admin_key(3600)
    r = adm("me", key=kt)
    check("SNAPEYES_ADMIN_SECRET unset, SNAPEYES_TICKET_SECRET of 32+ characters: its admin keys work", r.status_code == 200, r.text[:200])
    check("that fallback key is signed under its own label: it is no ticket of the same secret",
          not L.check_ticket(kt, kind="admin-v1") and adm("me", key=L.mint_ticket("admin-v1", 3600), ip={"x-real-ip": "198.51.100.41"}).status_code == 403)
    check("summary names the fallback", adm("summary", key=kt).json().get("admin", {}).get("secret") == "SNAPEYES_TICKET_SECRET")
    os.environ["SNAPEYES_ADMIN_SECRET"] = "too-short-admin-secret"
    check("SNAPEYES_ADMIN_SECRET set but short: 503 (no silent fallback to the ticket secret)",
          adm("me", key=kt).status_code == 503 and "shorter" in ops.admin_problem())
    os.environ["SNAPEYES_ADMIN_SECRET"] = ADMIN_SECRET
    os.environ["SNAPEYES_TICKET_SECRET"] = SECRET
    reset_limits()
    link_before = pay.access_key("260929-abcdef01")
    os.environ["SNAPEYES_ADMIN_SECRET"] = ADMIN_SECRET[::-1]
    check("a new SNAPEYES_ADMIN_SECRET revokes every admin key", adm("me", ip={"x-real-ip": "198.51.100.42"}).status_code == 403)
    check("and leaves the customers' order links as they were", pay.access_key("260929-abcdef01") == link_before)
    os.environ["SNAPEYES_ADMIN_SECRET"] = ADMIN_SECRET
    check("the same secret back: the key works again", adm("me", ip={"x-real-ip": "198.51.100.43"}).status_code == 200)
    reset_limits()
    r = requests.post(BASE + "/api/admin?key=" + KEY, data=json.dumps({"action": "me"}),
                      headers={"Content-Type": "application/json", **IP}, timeout=30)
    check("a key in the address is not accepted: 403", r.status_code == 403)
    r = requests.post(BASE + "/api/admin", data="{}", headers={"Content-Type": "text/plain", "Authorization": "Bearer " + KEY}, timeout=30)
    check("not application/json: 415 (L.run's gate)", r.status_code == 415)
    r = post("/api/admin", {"action": "me"}, {"Authorization": "Bearer " + KEY, "Origin": "https://evil.example"})
    check("a foreign Origin: 403 (L.run's gate)", r.status_code == 403)
    check("an unknown action: 400", adm("nope").status_code == 400)
    # the epoch
    os.environ["SNAPEYES_ADMIN_EPOCH"] = "2"
    check("SNAPEYES_ADMIN_EPOCH=2: the v1 key is revoked (403)", adm("me", ip={"x-real-ip": "198.51.100.9"}).status_code == 403)
    k2 = ops.mint_admin_key(3600, "admin-v2")
    r = adm("me", key=k2, ip={"x-real-ip": "198.51.100.9"})
    check("SNAPEYES_ADMIN_EPOCH=2: a v2 key works", r.status_code == 200 and r.json().get("kind") == "admin-v2")
    got = {}
    for val in ("v2", "2.0", "two", "-2", "1234567"):
        os.environ["SNAPEYES_ADMIN_EPOCH"] = val
        r = adm("me", ip={"x-real-ip": "198.51.100.10"})
        got[val] = (r.status_code, r.json().get("reason"))
    check("an epoch typed wrong (v2, 2.0, two, -2, 7 digits): 503 admin_not_configured, the old v1 key does not work",
          all(v == (503, "admin_not_configured") for v in got.values()), got)
    os.environ.pop("SNAPEYES_ADMIN_EPOCH")
    reset_limits()
    # the failed-login ceiling
    t0 = time.time()
    codes = [adm("me", key=bad, ip={"x-real-ip": "192.0.2.50"}).status_code for _ in range(ops.FAIL_LOCAL)]
    check(f"{ops.FAIL_LOCAL} failed logins: each 403, each slowed", codes == [403] * ops.FAIL_LOCAL and time.time() - t0 >= ops.FAIL_LOCAL * ops.FAIL_SLEEP * 0.9)
    r = adm("me", ip={"x-real-ip": "192.0.2.50"})
    check("then even the right key from that client: 429 too_many_attempts", r.status_code == 429 and r.json().get("reason") == "too_many_attempts", r.text[:200])
    check("429 carries Retry-After", int(r.headers.get("Retry-After") or 0) >= 60)
    check("another client is not blocked", adm("me", ip={"x-real-ip": "192.0.2.51"}).status_code == 200)
    marks = files("ops/adminfail")
    check("failed logins are marked in storage (CRON_SECRET set)", len(marks) >= ops.FAIL_LOCAL, marks[:3])
    check("the markers hold no address (a 12-hex tag only)", all(re.fullmatch(r"ops/adminfail/[0-9]{8}/[0-9a-f]{12}-[0-9a-f]{8}\.json", m) for m in marks)
          and not any("192.0.2" in open(os.path.join(STORE, m), encoding="utf-8").read() + m for m in marks))
    # across instances: the storage count blocks a client this instance has not seen fail
    ops._FAILS.clear()
    ops._BLOCKED.clear()
    tag = ops.client_tag(type("R", (), {"headers": {"x-real-ip": "192.0.2.60"}})())
    hour = time.strftime("%y%m%d%H", time.gmtime())
    for i in range(ops.FAIL_HOURLY):
        store.put(f"ops/adminfail/{hour}/{tag}-{i:08x}.json", b"{}", "application/json")
    r = adm("me", key=bad, ip={"x-real-ip": "192.0.2.60"})
    check(f"{ops.FAIL_HOURLY} failures in storage (other instances): the next failure answers 429", r.status_code == 429)
    check("and that client stays blocked here", adm("me", ip={"x-real-ip": "192.0.2.60"}).status_code == 429)
    reset_limits()
    # without CRON_SECRET the daily clean-up never deletes the markers: none is written (review finding)
    os.environ.pop("CRON_SECRET")
    n_marks = len(files("ops/adminfail"))
    codes = [adm("me", key=bad, ip={"x-real-ip": "192.0.2.70"}).status_code for _ in range(ops.FAIL_LOCAL)]
    check("no CRON_SECRET: failed logins write no marker", len(files("ops/adminfail")) == n_marks, files("ops/adminfail")[-3:])
    check("no CRON_SECRET: this instance's own limit still answers 429", codes == [403] * ops.FAIL_LOCAL
          and adm("me", ip={"x-real-ip": "192.0.2.70"}).status_code == 429)
    s_ = adm("summary").json().get("retention")
    check("summary: retention cron false", s_ == {"cron": False, "events": False}, s_)
    os.environ["CRON_SECRET"] = CRON
    check("summary: retention cron true again", adm("summary").json().get("retention") == {"cron": True, "events": True})
    reset_limits()
    # the owner's script
    env = dict(os.environ)
    out = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "mint_admin.py"), "--days", "5"], capture_output=True, text=True, env=env)
    tok = out.stdout.strip()
    check("mint_admin.py prints only the key on stdout", out.returncode == 0 and re.fullmatch(r"admin-v1\.[0-9]{10}\.[0-9a-f]{32}", tok), out.stderr[-300:])
    check("mint_admin.py says nothing secret on stderr", SECRET not in out.stderr + out.stdout and ADMIN_SECRET not in out.stderr + out.stdout)
    check("mint_admin.py names the secret it signed with", "SNAPEYES_ADMIN_SECRET" in out.stderr, out.stderr[-200:])
    check("the minted key logs in", adm("me", key=tok).status_code == 200)
    chk = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "mint_admin.py"), "--check", tok], capture_output=True, text=True, env=env)
    check("mint_admin.py --check accepts it", chk.returncode == 0 and "valid admin-v1" in chk.stdout)
    over = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "mint_admin.py"), "--days", "91"], capture_output=True, text=True, env=env)
    check("mint_admin.py refuses more than 90 days", over.returncode != 0 and not over.stdout.strip())
    env["SNAPEYES_ADMIN_EPOCH"] = "3"
    k3 = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "mint_admin.py")], capture_output=True, text=True, env=env).stdout.strip()
    check("mint_admin.py follows SNAPEYES_ADMIN_EPOCH", k3.startswith("admin-v3."))
    check("a v3 key does not work while the server is at epoch 1", adm("me", key=k3, ip={"x-real-ip": "198.51.100.77"}).status_code == 403)
    env["SNAPEYES_ADMIN_SECRET"] = "another-admin-secret-0123456789-abcdefgh"
    other = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "mint_admin.py")], capture_output=True, text=True, env=env).stdout.strip()
    check("a key signed with another secret: 403", adm("me", key=other.replace("admin-v3", "admin-v1"), ip={"x-real-ip": "198.51.100.78"}).status_code == 403)
    env2 = {k: v for k, v in env.items() if k not in ("SNAPEYES_ADMIN_SECRET", "SNAPEYES_TICKET_SECRET", "SNAPEYES_ADMIN_EPOCH")}
    env2["GEMINI_API_KEY"] = "fake-gemini-key-for-the-test-0123456789"
    none = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "mint_admin.py")], capture_output=True, text=True, env=env2)
    check("mint_admin.py with only the Gemini key: mints nothing (exit 2), says to set SNAPEYES_ADMIN_SECRET",
          none.returncode == 2 and not none.stdout.strip() and "SNAPEYES_ADMIN_SECRET" in none.stderr, (none.returncode, none.stderr[-200:]))
    ns = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "mint_admin.py"), "--new-secret"], capture_output=True, text=True, env=env2)
    val = ns.stdout.strip()
    check("mint_admin.py --new-secret: one random value of 64 characters on stdout", ns.returncode == 0 and len(val) == 64 and "\n" not in val
          and len(val) >= ops.ADMIN_SECRET_MIN)
    env2["SNAPEYES_ADMIN_SECRET"] = val
    k_new = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "mint_admin.py")], capture_output=True, text=True, env=env2).stdout.strip()
    os.environ["SNAPEYES_ADMIN_SECRET"] = val
    check("a key minted with that new secret works on a server with the same secret", adm("me", key=k_new, ip={"x-real-ip": "198.51.100.79"}).status_code == 200)
    os.environ["SNAPEYES_ADMIN_SECRET"] = ADMIN_SECRET
    reset_limits()

# ==================================================================================================== 2. events
if section("events"):
    reset_limits()
    s0 = snap()
    ok = E.record("analyze", ok=True, verdict="good", detail=91, blocked=False, block_reason=None, locked=True, shake_asked=False,
                  lang="de", device="ios", source="camera", email="anna@example.com", name="Anna", ua="Mozilla/5.0 (iPhone)",
                  ip="203.0.113.7", order="260929-abcdef01", image="aGVsbG8=")
    evs = [x for x in events_now() if x[0] not in s0]
    check("record() writes one event", ok and len(evs) == 1, evs)
    path, ev = evs[-1]
    check("at ops/events/<YYYY-MM-DD>/<HHMMSS>-<rand>.json", re.fullmatch(r"ops/events/\d{4}-\d{2}-\d{2}/\d{6}-[0-9a-f]{12}\.json", path), path)
    check("only the allowed fields are kept", set(ev) <= {"v", "kind", "t", "ms", "ok", "verdict", "detail", "blocked", "locked", "shake_asked", "lang", "device", "source"}, sorted(ev))
    blob = json.dumps(ev)
    check("no email, name, user agent, IP, order id or image in an analyze event", not any(x in blob for x in ("@", "Anna", "Mozilla", "203.0.113", "260929", "aGVsbG8")))
    E.record("analyze", verdict="Anna Muster", block_reason="anna@example.com", lang="<b>", device=5)
    ev = events_now()[-1][1]
    check("a code that is not a short lower-case code is dropped", "verdict" not in ev and "block_reason" not in ev and "lang" not in ev and "device" not in ev, ev)
    E.record("master", step="eye", order="lab-260929-abcd1234", eye=1, needs_review=False, attempts=1)
    ev = events_now()[-1][1]
    check("an order event keeps its order id and says lab", ev.get("order") == "lab-260929-abcd1234" and ev.get("lab") is True)
    E.record("master", step="eye", order="Anna@x", eye=1)
    check("an order id that is not one is dropped", "order" not in events_now()[-1][1])
    check("an unknown kind is refused", E.record("login", user="x") is False)
    check("device_class: iPhone -> ios, Android -> android, Windows -> desktop, none -> unknown",
          [E.device_class({"ua": u}) for u in ("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0)", "Mozilla/5.0 (Linux; Android 15)", "Mozilla/5.0 (Windows NT 10.0)", "")] == ["ios", "android", "desktop", "unknown"])
    check("device_source keeps only the known sources", [E.device_source({"source": s}) for s in ("lab", "camera", "x<y", None)] == ["lab", "camera", "other", "unknown"])
    # the time limit
    real_put = store.put

    def slow_put(*a, **k):
        time.sleep(4)
        return real_put(*a, **k)
    store.put = slow_put
    t0 = time.time()
    res = E.record("compose", style="supernova", eyes=1)
    took = time.time() - t0
    store.put = real_put
    check(f"a slow store: record() gives up after at most 1.5 s (took {took:.2f} s) and says False", res is False and took <= 1.7)
    slow_done = t0 + 4.6          # its write still lands in the background after 4 s: wait for it, so it cannot fall into a later section
    # never raises
    store.put = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    check("a failing store: record() says False, never raises", E.record("compose", style="supernova") is False)
    store.put = real_put
    time.sleep(max(0.0, slow_done - time.time()))
    # skipped without CRON_SECRET: only the daily clean-up deletes events (review finding)
    n_ev = len(files("ops/events"))
    for v in ("", "short-cron"):
        os.environ["CRON_SECRET"] = v
        check(f"CRON_SECRET {'unset' if not v else 'under 16 characters'}: record() writes nothing", E.record("compose", style="supernova") is False
              and len(files("ops/events")) == n_ev and E.retention_ok() is False)
    os.environ["CRON_SECRET"] = CRON
    check("CRON_SECRET set: record() writes again", E.record("compose", style="supernova") is True and E.retention_ok())
    # skipped without storage
    os.environ["STORE_LOCAL_DIR"] = ""
    t0 = time.time()
    n0 = threading.active_count()
    res = E.record("compose", style="supernova")
    check("no storage configured: skipped at once (False, no thread)", res is False and time.time() - t0 < 0.05 and threading.active_count() == n0)
    os.environ["STORE_LOCAL_DIR"] = STORE
    # the per-instance ceiling
    reset_limits()
    now = time.time()
    E._SEEN["error"] = [now] * E.RATE["error"][0]
    check("past the error ceiling an error event is dropped", E.record("error", endpoint="x", **{"class": "500"}) is False)
    reset_limits()
    # summarize and merge
    agg = E.summarize([
        {"kind": "analyze", "verdict": "good", "locked": True, "device": "ios", "source": "camera", "lang": "en", "ms": 4000, "shake_asked": True},
        {"kind": "analyze", "verdict": "weak", "blocked": True, "block_reason": "too_blurry", "locked": True, "ms": 6000},
        {"kind": "analyze", "ok": False, "verdict": "no_eye"},
        {"kind": "deglare", "glare_pct": 3.2, "lid_pct": 0, "model_call": False, "ms": 2000},
        {"kind": "enhance", "qa_ok": False, "fallback": False, "ms": 12000},
        {"kind": "compose", "style": "supernova", "eyes": 2, "ms": 800},
        {"kind": "master", "step": "eye", "order": "lab-x", "lab": True, "attempts": 2, "needs_review": True, "ms": 31000},
        {"kind": "master", "step": "compose", "order": "lab-x", "lab": True, "ms": 15000},
        {"kind": "error", "endpoint": "analyze", "class": "500", "status": 500, "t": 5},
        {"kind": "error", "endpoint": "analyze", "class": "busy", "status": 503, "t": 10},
    ])
    check("summarize: verdicts, blocks, no_eye", agg["verdict"] == {"good": 1, "weak": 1, "no_eye": 1} and agg["block_reason"] == {"too_blurry": 1})
    check("summarize: Gemini calls (vision 1+1 shake+1+1, 1K enhance, 4K attempts)", agg["gemini"] == {"vision": 4, "image_1k": 1, "image_4k": 2}, agg["gemini"])
    check("summarize: timings per step", agg["ms"]["analyze"] == [10000, 2] and agg["ms"]["master_eye"] == [31000, 1])
    check("summarize: busy and errors", agg["busy"] == 1 and agg["errors"] == {"busy": 1, "500": 1}, agg["errors"])
    check("summarize: recent errors newest first, with kind", [(e["t"], e["kind"]) for e in agg["recent_errors"]] == [(10, "busy"), (5, "500")])
    m = E.merge(agg, agg)
    check("merge adds everything", m["kinds"]["analyze"] == 6 and m["errors"]["busy"] == 2 and m["gemini"]["vision"] == 8 and m["ms"]["analyze"] == [20000, 4])
    # purge_old
    for d in ("2024-01-01", "2024-02-02"):
        store.put(f"ops/events/{d}/000000-aaaaaaaaaaaa.json", b'{"kind":"compose"}', "application/json", upsert=True)
    store.put("ops/daily/2024-01-01.json", b'{"v":1}', "application/json", upsert=True)
    store.put("ops/adminfail/24010100/abcdefabcdef-00000000.json", b"{}", "application/json", upsert=True)
    today = time.strftime("%Y-%m-%d", time.gmtime())
    n_today = len(files(f"ops/events/{today}"))
    res = E.purge_old(days=365)
    check("purge_old removes events, day counts and failed-login marks past their time", res["ok"] and res["events"] == 2 and res["days"] == 2 and res["rollups"] == 1 and res["adminfail"] >= 1, res)
    check("purge_old keeps today's events", len(files(f"ops/events/{today}")) == n_today and not files("ops/events/2024-01-01"))
    check("purge_old dry run changes nothing", E.purge_old(days=1, yes=False)["ok"] and len(files(f"ops/events/{today}")) == n_today)
    os.environ["STORE_LOCAL_DIR"] = ""
    check("purge_old without storage: skipped, never raises", E.purge_old().get("skipped") == "storage_not_configured")
    os.environ["STORE_LOCAL_DIR"] = STORE

# ==================================================================================================== 3. hooks
if section("hooks"):
    reset_limits()
    shutil.rmtree(os.path.join(STORE, "ops", "events"), ignore_errors=True)

    def new_events(s0, endpoint=None):
        """The events written since the snapshot s0 (after they settled), oldest first. With endpoint: only that
        endpoint's own events and error events (an earlier request's late error event is not this one's)."""
        settle()
        evs = [e for p, e in events_now() if p not in s0]
        if endpoint:
            evs = [e for e in evs if (e.get("endpoint") == endpoint if e["kind"] == "error" else e["kind"] == endpoint
                                      or (endpoint in ("master_eye", "master_compose") and e["kind"] == "master"))]
        return evs
    # analyze: the vision call replaced by the sample's own iris box (a locked, sharp photo), the shake call refused
    from PIL import Image
    real_json, real_gemini, real_image = L.gemini_json, L.gemini, L.gemini_image
    im = Image.open(os.path.join(REPO, "public", "assets", "sample_eye_blue_1789706902835.jpg")).convert("RGB")
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=90)
    photo = base64.b64encode(buf.getvalue()).decode()
    L.gemini_json = lambda model, prompt, img: {"found": True, "iris_box": [226, 225, 786, 785], "pupil_box": [425, 424, 587, 586],
                                                "glare_boxes": [], "sharpness": "sharp", "iris_occluded_by_eyelids_percent": 2}
    L.gemini = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no calls in tests"))
    n0 = snap()
    dev = {"ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) Safari", "w": 390, "h": 844, "source": "camera"}
    r = post("/api/analyze", {"image": photo, "origWidth": 1024, "origHeight": 1024, "device": dev, "lang": "de"})
    ev = [e for e in new_events(n0) if e["kind"] == "analyze"]
    check("analyze answers (vision mocked)", r.status_code == 200 and r.json().get("ok"), r.text[:200])
    q = r.json().get("quality") or {}
    check("analyze: one event with the reply's verdict, detail, lock, block", len(ev) == 1 and ev[0].get("verdict") == q.get("verdict")
          and ev[0].get("detail") == q.get("detail") and ev[0].get("locked") == q.get("locked") and ev[0].get("blocked") == q.get("blocked"), (ev, q.get("verdict")))
    check("analyze event: lang de, device ios, source camera, a time", ev and ev[0].get("lang") == "de" and ev[0].get("device") == "ios"
          and ev[0].get("source") == "camera" and ev[0].get("ms", 0) > 0)
    L.gemini_json = lambda model, prompt, img: {"found": False}
    n0 = snap()
    r = post("/api/analyze", {"image": photo, "device": {"ua": "Mozilla/5.0 (Windows NT 10.0)", "source": "gallery"}})
    ev = new_events(n0)
    check("analyze without an eye: an event verdict no_eye, ok false", r.status_code == 200 and len(ev) == 1 and ev[0].get("verdict") == "no_eye"
          and ev[0].get("ok") is False and ev[0].get("device") == "desktop", ev)
    L.gemini_json = lambda model, prompt, img: (_ for _ in ()).throw(L.ModelBusy("503"))
    n0 = snap()
    r = post("/api/analyze", {"image": photo})
    ev = new_events(n0)
    check("Gemini busy: 503 and an error event class busy, endpoint analyze", r.status_code == 503 and ev and ev[-1]["kind"] == "error"
          and ev[-1].get("class") == "busy" and ev[-1].get("endpoint") == "analyze" and ev[-1].get("status") == 503, ev)
    L.gemini_json = lambda model, prompt, img: (_ for _ in ()).throw(RuntimeError("secret detail anna@example.com"))
    n0 = snap()
    r = post("/api/analyze", {"image": photo})
    ev = new_events(n0)
    check("a crash: 500 and an error event 500 without the message", r.status_code == 500 and ev and ev[-1].get("class") == "500"
          and "anna" not in json.dumps(ev) and "secret" not in json.dumps(ev), ev)
    L.gemini_json = real_json
    # deglare (no model call: the switch is off)
    n0 = snap()
    r = post("/api/deglare", {"crop": CROP_B64, "pad": 1.12, "ticket": L.mint_ticket("work"), "pupil_r": 0.13, "glare_boxes": []})
    ev = new_events(n0)
    check("deglare: one event with glare_pct, lid_pct, model_call false", r.status_code == 200 and len(ev) == 1 and ev[0]["kind"] == "deglare"
          and ev[0].get("glare_pct") == r.json().get("glare_pct") and ev[0].get("model_call") is False, (r.status_code, ev))
    n0 = snap()
    r = post("/api/deglare", {"crop": CROP_B64})
    ev = new_events(n0)
    check("deglare without a ticket: 403 and an error event 403", r.status_code == 403 and ev and ev[-1].get("status") == 403 and ev[-1].get("endpoint") == "deglare", ev)
    # enhance: the image model replaced by the input
    L.gemini_image = lambda prompt, img, size=None, thinking=None, model=None: img
    n0 = snap()
    r = post("/api/enhance", {"crop": CROP_B64, "mode": "artistic", "pad": 1.12, "ticket": L.mint_ticket("work")})
    ev = new_events(n0)
    check("enhance: one event with qa_ok, ring_de00, fallback", r.status_code == 200 and len(ev) == 1 and ev[0]["kind"] == "enhance"
          and ev[0].get("qa_ok") == r.json()["qa"]["ok"] and "fallback" in ev[0], (r.status_code, r.text[:200], ev))
    L.gemini_image, L.gemini = real_image, real_gemini
    # compose
    n0 = snap()
    r = post("/api/compose", {"irises": [PREVIEW_B64, PREVIEW_B64], "style": "supernova", "layout": "fusion", "names": "Anna & Jan"})
    ev = new_events(n0)
    check("compose: one event with style, eyes, layout, clean false", r.status_code == 200 and len(ev) == 1 and ev[0].get("style") == "supernova"
          and ev[0].get("eyes") == 2 and ev[0].get("layout") == "fusion" and ev[0].get("clean") is False, ev)
    check("compose event: no names", "Anna" not in json.dumps(ev))
    n0 = snap()
    r = post("/api/compose", {"irises": "x"})
    ev = new_events(n0)
    check("compose with bad input: 400 and an error event 400", r.status_code == 400 and ev and ev[-1].get("status") == 400, ev)
    # an endpoint's own refusal (store.Answer through the box): /api/order with a wrong key
    oid = f"{day_id()}-hook0001"
    make_order(oid)
    n0 = snap()
    r = post("/api/order", {"action": "status", "order": oid, "k": "0" * 32})
    ev = new_events(n0)
    check("order with a wrong key: 403 bad_link and an error event reason bad_link", r.status_code == 403 and ev and ev[-1].get("reason") == "bad_link"
          and ev[-1].get("endpoint") == "order", ev)
    n0 = snap()
    r = post("/api/order", {"action": "make", "order": oid, "k": pay.access_key(oid), "eye": 1})
    ev = new_events(n0)
    check("the ordinary 402 not_paid of the order flow is no error event", r.status_code == 402 and not ev, (r.status_code, ev))
    n0 = snap()
    requests.post(BASE + "/api/compose", data="x", headers={"Content-Type": "text/plain"}, timeout=30)
    settle()
    check("a gate refusal (415) writes no event", {p for p, _ in events_now()} == n0)
    all_ev = json.dumps([e for _, e in events_now()])
    check("no event anywhere holds an email, a name, a user agent or an IP", not any(x in all_ev for x in ("@", "Anna", "Mozilla", "iPhone OS", "203.0.113")))

# ==================================================================================================== 4. orders views
if section("views"):
    reset_limits()
    Fake.emails.clear()
    d = day_id()
    O = {s: f"{d}-{s[:4]}{secrets.token_hex(2)}" for s in ("unpaid", "checkout", "expired", "pending", "paid", "making", "review",
                                                            "ready", "held", "withdrawn", "deleted")}
    make_order(O["unpaid"])
    make_order(O["checkout"], checkout=True)
    make_order(O["expired"], age=25 * 3600)
    make_order(O["pending"], paid=True)
    make_order(O["paid"], paid=True, mail="sent")
    make_order(O["making"], paid=True, mail="sent")
    store.put(f"orders/{O['making']}/eye_1.jpg", PREVIEW, "image/jpeg")
    make_order(O["review"], paid=True, mail="sent")
    put_json(f"orders/{O['review']}/review.json", {"reason": "render_rejected", "eye": 1})
    for s in ("ready", "held"):
        make_order(O[s], paid=True, mail="sent", eyes=2)
        store.put(f"orders/{O[s]}/artwork_abc.jpg", PREVIEW, "image/jpeg")
        put_json(f"orders/{O[s]}/delivery.json", {"key": f"orders/{O[s]}/artwork_abc.jpg", "needs_review": s == "held"})
    make_order(O["withdrawn"], paid=True, mail="sent")
    put_json(f"orders/{O['withdrawn']}/withdrawn.json", {"t": time.time()})
    make_order(O["deleted"], paid=True, mail="sent")
    put_json(f"orders/{O['deleted']}/deleted.json", {"t": time.time()})
    r = adm("orders", days=30)
    rows = {x["order"]: x for x in r.json().get("orders", [])}
    check("orders: 200 and every test order listed", r.status_code == 200 and all(o in rows for o in O.values()), r.text[:300])
    got = {s: rows.get(o, {}).get("state") for s, o in O.items()}
    want = {"unpaid": "unpaid", "checkout": "checkout", "expired": "expired", "pending": "pending", "paid": "paid", "making": "making",
            "review": "review", "ready": "ready", "held": "review", "withdrawn": "withdrawn", "deleted": "deleted"}
    check("orders: each state read from the files alone", got == want, got)
    check("orders: the email masked (k***@e***.com)", rows[O["paid"]]["email"] == "k***@e***.com")
    check("orders: no name text in the list", "Anna" not in r.text and "onerror" not in r.text)
    check("orders: eyes, style, price", rows[O["ready"]]["eyes"] == 2 and rows[O["ready"]]["style"] == "deep_nebula" and rows[O["ready"]]["amount"] == 3997)
    check("orders: held flag", rows[O["held"]]["held"] is True and rows[O["ready"]]["held"] is False)
    check("the list sent no email and asked Stripe nothing", not Fake.emails and not Fake.refunds)
    r = adm("orders", days=30, state="ready")
    check("orders: filter by state", r.status_code == 200 and {x["state"] for x in r.json()["orders"]} == {"ready"})
    r = adm("order", order=O["ready"])
    dj = r.json()
    check("order: 200 with every record", r.status_code == 200 and {"order.json", "paid.json", "delivery.json", "draft/eye_1.json"} <= set(dj["records"]), sorted(dj.get("records", {}))[:8])
    check("order: the full email and the consent text", dj["email"] == "kunde@example.com" and dj["consent"]["text"] == pay.CONSENT_TEXT["en"])
    check("order: signed links for the draft images and the artwork", dj["eyes"][0]["draft"]["crop_url"] and dj["artworks"] and dj["artworks"][0]["current"])
    check("order: the payment intent listed, refundable", dj["payments"] and dj["payments"][0]["payment_intent"].startswith("pi_test_") and not dj["payments"][0]["refunded"])
    check("order: the customer's names come back as data (the page escapes them)", dj["records"]["paid.json"]["spec"]["names"].startswith("Anna <img"))
    check("order: a missing order is 404", adm("order", order=f"{d}-nothere1").status_code == 404)
    check("order: a bad order id is 400", adm("order", order="../x").status_code == 400)
    check("summary: 200 with ordering state", adm("summary").json().get("ordering", {}).get("problem") is not None)

# ==================================================================================================== 5. actions
if section("actions"):
    reset_limits()
    Fake.emails.clear()
    d = day_id()
    # the confirmation email
    o1 = f"{d}-mail{secrets.token_hex(2)}"
    make_order(o1, paid=True)
    put_json(f"orders/{o1}/review.json", {"reason": "confirmation_email_failed"})
    r = adm("resend_confirmation", order=o1)
    check("resend_confirmation (none sent yet): sent, the mail hold lifted", r.status_code == 200 and r.json().get("result") == "sent"
          and r.json().get("hold_cleared") is True and not os.path.exists(os.path.join(STORE, "orders", o1, "review.json")), r.text[:300])
    check("the customer got the confirmation", Fake.emails and Fake.emails[-1][0]["to"] == ["kunde@example.com"] and "order confirmation" in Fake.emails[-1][0]["subject"])
    m = json.load(open(os.path.join(STORE, "orders", o1, "mail_delivery.json")))
    check("mail_delivery.json says sent", m.get("state") == "sent")
    r = adm("resend_confirmation", order=o1)
    check("resend_confirmation again: a copy with a new idempotency key, the mark unchanged", r.json().get("copy") is True and r.json().get("result") == "sent"
          and Fake.emails[-1][1] != Fake.emails[-2][1] and json.load(open(os.path.join(STORE, "orders", o1, "mail_delivery.json"))) == m)
    put_json(f"orders/{o1}/mail_delivery.json", {"state": "sending", "t": time.time()})
    check("resend_confirmation while another sends: 409 mail_in_progress", adm("resend_confirmation", order=o1).json().get("reason") == "mail_in_progress")
    check("resend_confirmation of an unpaid order: 409 not_paid", adm("resend_confirmation", order=f"{d}-hook0001").json().get("reason") in ("not_paid", "not_found"))
    # mailed by hand, clear review
    o2 = f"{d}-hand{secrets.token_hex(2)}"
    make_order(o2, paid=True)
    put_json(f"orders/{o2}/review.json", {"reason": "confirmation_email_no_address"})
    r = adm("mailed_by_hand", order=o2)
    check("mailed_by_hand: marked sent by the owner, hold lifted", r.json().get("result") == "marked" and r.json().get("hold_cleared") is True
          and json.load(open(os.path.join(STORE, "orders", o2, "mail_delivery.json"))).get("by") == "owner")
    put_json(f"orders/{o2}/review.json", {"reason": "render_rejected"})
    r = adm("clear_review", order=o2)
    check("clear_review removes review.json", r.json().get("removed") is True and not os.path.exists(os.path.join(STORE, "orders", o2, "review.json")))
    # release and the ready email
    o3 = f"{d}-rels{secrets.token_hex(2)}"
    make_order(o3, paid=True, mail="sent")
    check("resend_ready without an artwork: 409 no_artwork", adm("resend_ready", order=o3).json().get("reason") == "no_artwork")
    check("release without an artwork: 409 no_artwork", adm("release", order=o3).json().get("reason") == "no_artwork")
    store.put(f"orders/{o3}/artwork_x.jpg", PREVIEW, "image/jpeg")
    put_json(f"orders/{o3}/delivery.json", {"key": f"orders/{o3}/artwork_x.jpg", "needs_review": True})
    put_json(f"orders/{o3}/review.json", {"reason": "x"})
    check("resend_ready while held: 409 held", adm("resend_ready", order=o3).json().get("reason") == "held")
    n = len(Fake.emails)
    r = adm("release", order=o3)
    check("release: release.json by admin, review.json gone, the ready email sent", r.json().get("result") == "released" and r.json().get("mail") == "sent"
          and os.path.exists(os.path.join(STORE, "orders", o3, "release.json")) and not os.path.exists(os.path.join(STORE, "orders", o3, "review.json"))
          and len(Fake.emails) == n + 1 and "ready" in Fake.emails[-1][0]["subject"], r.text[:300])
    r = adm("resend_ready", order=o3)
    check("resend_ready after release: sent", r.json().get("result") == "sent" and len(Fake.emails) == n + 2)
    r = adm("release", order=o3, mail=False)
    check("release with mail false sends nothing", r.json().get("mail") is None and len(Fake.emails) == n + 2)
    # the link
    r = adm("link", order=o3)
    check("link: the withdrawal link and the order page link (to copy), no plain url", r.json().get("order_url", "").endswith(f"&k={pay.access_key(o3)}&lang=en")
          and "withdraw=1" in r.json().get("withdraw_url", "") and "url" not in r.json(), r.text[:300])
    # refund
    o4 = f"{d}-refd{secrets.token_hex(2)}"
    make_order(o4, paid=True, mail="sent", eyes=2)
    pi = f"pi_test_{o4.replace('-', '')[:20]}"
    put_json(f"orders/{o4}/extra_payment_1234.json", {"paid": False, "extra_payment": True, "payment_intent": "pi_test_extra0001", "amount_total": 3997})
    check("refund without the typed order number: 400", adm("refund", order=o4, payment_intent=pi).status_code == 400 and not Fake.refunds)
    check("refund with another order's number typed: 400", adm("refund", order=o4, payment_intent=pi, confirm=o3).status_code == 400)
    check("refund of a payment not of this order: 409 unknown_payment", adm("refund", order=o4, payment_intent="pi_test_other000", confirm=o4).json().get("reason") == "unknown_payment" and not Fake.refunds)
    r = adm("refund", order=o4, payment_intent=pi, confirm=o4)
    check("refund: Stripe POST /v1/refunds on the payment intent", r.status_code == 200 and Fake.refunds and Fake.refunds[-1][0].get("payment_intent") == pi
          and Fake.refunds[-1][1] == f"snapeyes-refund-{pi}", r.text[:300])
    check("refund: recorded under ops/refunds/<order>/", len(files(f"ops/refunds/{o4}")) == 1)
    check("refund again: 409 already_refunded, Stripe not asked", adm("refund", order=o4, payment_intent=pi, confirm=o4).json().get("reason") == "already_refunded" and len(Fake.refunds) == 1)
    r = adm("refund", order=o4, payment_intent="pi_test_extra0001", confirm=o4)
    check("refund of the extra payment works too", r.status_code == 200 and Fake.refunds[-1][0].get("payment_intent") == "pi_test_extra0001")
    check("order detail shows both payments refunded", all(p["refunded"] for p in adm("order", order=o4).json()["payments"]))
    o5 = f"{d}-reff{secrets.token_hex(2)}"
    make_order(o5, paid=True, mail="sent")
    Fake.fail_refund.append(400)
    r = adm("refund", order=o5, payment_intent=f"pi_test_{o5.replace('-', '')[:20]}", confirm=o5)
    check("Stripe refuses: 502 payments_error with Stripe's code, nothing recorded", r.status_code == 502 and "charge_already_refunded" in r.json().get("detail", "")
          and not files(f"ops/refunds/{o5}"), r.text[:300])
    os.environ["STRIPE_SECRET_KEY"] = ""
    check("refund without Stripe: 409 stripe_off", adm("refund", order=o5, payment_intent=f"pi_test_{o5.replace('-', '')[:20]}", confirm=o5).json().get("reason") == "stripe_off")
    os.environ["STRIPE_SECRET_KEY"] = SK
    r = adm("mark_refunded", order=o5, note="refunded by hand in the Stripe Dashboard")
    mk = json.load(open(os.path.join(STORE, "orders", o5, "refunded.json")))
    check("mark_refunded: refunded.json as order_admin writes it (by admin)", r.json().get("result") == "marked" and mk.get("by") == "admin"
          and mk.get("amount") == 1997 * 0 + pay.price_cents(1, "deep_nebula"), mk)
    check("mark_refunded of an unpaid order: refused", adm("mark_refunded", order=f"{d}-nothere2").status_code in (404, 409))
    # delete files
    o6 = f"{d}-dele{secrets.token_hex(2)}"
    make_order(o6, paid=True, mail="sent")
    store.put(f"orders/{o6}/eye_1.jpg", PREVIEW, "image/jpeg")
    check("delete_files without the typed number: 400", adm("delete_files", order=o6).status_code == 400 and os.path.exists(os.path.join(STORE, "orders", o6, "eye_1.jpg")))
    r = adm("delete_files", order=o6, confirm=o6)
    left = sorted(os.path.basename(p) for p in files(f"orders/{o6}"))
    check("delete_files (paid): images gone, the records and deleted.json stay", r.json().get("result") == "deleted" and "eye_1.jpg" not in left
          and {"order.json", "paid.json", "deleted.json", "mail_delivery.json"} <= set(left) and not files(f"orders/{o6}/draft"), left)
    check("the order then reads deleted", adm("order", order=o6).json().get("state") == "deleted")
    o7 = f"{d}-delu{secrets.token_hex(2)}"
    make_order(o7)
    adm("delete_files", order=o7, confirm=o7)
    check("delete_files (unpaid): the whole folder goes", not files(f"orders/{o7}"))
    check("delete_files of nothing: 404", adm("delete_files", order=o7, confirm=o7).status_code == 404)
    # the audit log
    aud = []
    for p in files("ops/audit"):
        aud.append(json.load(open(os.path.join(STORE, p), encoding="utf-8")))
    acts = {a["action"] for a in aud}
    check("every action is in the audit log", {"resend_confirmation", "mailed_by_hand", "clear_review", "release", "resend_ready", "link", "refund", "mark_refunded", "delete_files"} <= acts, acts)
    check("failed actions are logged as failed", any(a["action"] == "refund" and a["ok"] is False and a["result"] == "unknown_payment" for a in aud))
    blob = json.dumps(aud)
    check("the audit log holds no email, no link, no key", "@" not in blob and "k=" not in blob and "http" not in blob, blob[:200])
    check("per-order log under ops/orderlog/<order>/", len(files(f"ops/orderlog/{o4}")) >= 3)
    r = adm("audit")
    check("audit view: newest entries", r.status_code == 200 and len(r.json()["entries"]) >= 10)
    # the lab
    r = adm("lab_start")
    lab = r.json()
    check("lab_start: a lab-<yymmdd>-<rand> order and its unlock ticket", r.status_code == 200 and re.fullmatch(rf"lab-{d}-[0-9a-f]{{8}}", lab.get("order", ""))
          and L.check_ticket(lab["ticket"], kind=store.unlock_kind(lab["order"])), r.text[:200])
    check("lab_start: the ticket opens no real order", not L.check_ticket(lab["ticket"], kind=store.unlock_kind(o4)))
    check("lab marker written", os.path.exists(os.path.join(STORE, "ops", "lab", lab["order"] + ".json")))
    store.put(f"orders/{lab['order']}/eye_1.jpg", PREVIEW, "image/jpeg")
    row = {x["order"]: x for x in adm("lab_list").json()["lab"]}.get(lab["order"])
    check("lab_list lists it with its files", row and row["files"] == 1 and row["eyes"] == 1, row)
    check("the order list hides lab orders", lab["order"] not in {x["order"] for x in adm("orders", days=30).json()["orders"]})
    check("lab_delete refuses a real order", adm("lab_delete", order=o4).status_code == 400 and files(f"orders/{o4}"))
    r = adm("lab_delete", order=lab["order"])
    check("lab_delete removes the lab order", r.status_code == 200 and not os.path.exists(os.path.join(STORE, "ops", "lab", lab["order"] + ".json"))
          and not files(f"orders/{lab['order']}") and lab["order"] not in {x["order"] for x in adm("lab_list").json()["lab"]})

# ==================================================================================================== 6. render and recompose
if section("render"):
    reset_limits()
    d = day_id()
    real_render = master_eye._render_4k
    calls = []

    def fake_render(base, order_, eye, prompt=None):
        calls.append((order_, eye))
        return base.resize((4096, 4096), Image.LANCZOS), 1, {"prompt": 1, "output": 1}
    from PIL import Image
    master_eye._render_4k = fake_render
    o = f"{d}-rend{secrets.token_hex(2)}"
    make_order(o, paid=True, eyes=1)
    r = adm("render", order=o, eye=1)
    check("render before the confirmation email: 409 making_not_started, nothing rendered", r.status_code == 409 and r.json().get("reason") == "making_not_started" and not calls, r.text[:200])
    put_json(f"orders/{o}/mail_delivery.json", {"state": "sent", "t": time.time()})
    # paid, confirmation out, the customer never opened the order page (review finding): the owner cannot start it
    r = adm("render", order=o, eye=1)
    check("render of a never-started order: 409 making_not_started, nothing rendered, no making.json",
          r.status_code == 409 and r.json().get("reason") == "making_not_started" and not calls
          and not os.path.exists(os.path.join(STORE, "orders", o, "making.json")), r.text[:200])
    dj = adm("order", order=o).json()
    check("order view: making not begun, the page offers no start", dj.get("making") == {"began": False, "period_over": False} and dj["can"]["start"] is False, dj.get("making"))
    from _lib import withdraw as W_  # noqa
    rec_, paid_ = json.load(open(os.path.join(STORE, "orders", o, "order.json"))), json.load(open(os.path.join(STORE, "orders", o, "paid.json")))
    check("the customer's right is intact (withdraw._assess_paid: withdrawn, nothing_made)",
          W_._assess_paid(o, rec_, paid_, time.time()).get("reason") == "nothing_made")
    # the customer's order page starts making (as the page does: order.make)
    t0 = time.time()
    rm = post("/api/order", {"action": "make", "order": o, "k": pay.access_key(o), "eye": 1})
    check("the order page's make answers 200", rm.status_code == 200, rm.text[:200])
    check("the customer's page made eye 1 (making.json written)", os.path.exists(os.path.join(STORE, "orders", o, "making.json")) and len(calls) == 1)
    check("order view: making began, start offered", adm("order", order=o).json()["can"]["start"] is True)
    o_two = f"{d}-rnd2{secrets.token_hex(2)}"
    k_two = make_order(o_two, paid=True, eyes=2, mail="sent")
    post("/api/order", {"action": "make", "order": o_two, "k": k_two, "eye": 1})
    n_calls = len(calls)
    r = adm("render", order=o_two, eye=2)
    check(f"render (not made) once the customer's page began: made through order.make ({time.time() - t0:.0f} s)",
          r.status_code == 200 and r.json().get("result") == "made" and len(calls) == n_calls + 1, r.text[:300])
    o_old = f"{d}-rold{secrets.token_hex(2)}"
    make_order(o_old, paid=True, eyes=1, mail="sent", age=20 * 86400)
    dj = adm("order", order=o_old).json()
    check("an order paid 20 days ago, nothing made: period over, start offered", dj.get("making") == {"began": False, "period_over": True} and dj["can"]["start"] is True, dj.get("making"))
    r = adm("render", order=o_old, eye=1)
    check("render after the 14-day period (the right is over anyway): made", r.status_code == 200 and r.json().get("result") == "made", r.text[:300])
    del calls[1:]                  # the checks below count the renders of order o only (its eye 1 is calls[0])
    check("render of an eye above the order's count: 400", adm("render", order=o, eye=2).status_code == 400)
    r = adm("render", order=o, eye=1)
    rec = json.load(open(os.path.join(STORE, "orders", o, "eye_1.json")))
    if not master_eye._can_rerender(rec):
        check("render again of a master that passed: 409 rerender_not_allowed", r.status_code == 409 and r.json().get("reason") == "rerender_not_allowed" and len(calls) == 1, r.text[:200])
        rec["preview"] = dict(rec.get("preview") or {}, render_ok=False, ok=False)
        put_json(f"orders/{o}/eye_1.json", rec)
    r = adm("render", order=o, eye=1)
    check("render of a master that failed its check: re-rendered by master_eye (same preview)", r.status_code == 200 and r.json().get("result") == "rerendered" and len(calls) == 2, r.text[:300])
    r = adm("render", order=o, eye=1)
    check("a second re-render: 409 rerender_not_allowed (master_eye's rule)", r.status_code == 409 and r.json().get("reason") == "rerender_not_allowed" and len(calls) == 2)
    t0 = time.time()
    r = adm("recompose", order=o)
    dl = json.load(open(os.path.join(STORE, "orders", o, "delivery.json")))
    check(f"recompose: the artwork composed, delivery.json by admin ({time.time() - t0:.0f} s)", r.status_code == 200 and r.json().get("result") == "composed"
          and dl.get("by") == "admin" and os.path.exists(os.path.join(STORE, *dl["key"].split("/"))), r.text[:300])
    r = adm("recompose", order=o)
    check("recompose again: the same file", r.json().get("result") == "same")
    ev = [e for _, e in events_now() if e.get("kind") == "master" and e.get("order") == o]
    # (WP6a: the master plan's step runner writes one master event per step drawn, step "art", beside the legacy composer's own "compose" event; a recompose
    # that draws nothing, the same file again, writes none)
    check("master events: two eye renders (one a re-render), one composition and its art step, with the order id", sorted((e["step"], bool(e.get("rerender"))) for e in ev)
          == [("art", False), ("compose", False), ("eye", False), ("eye", True)], ev)
    o2 = f"{d}-recm{secrets.token_hex(2)}"
    make_order(o2, paid=True, eyes=2, mail="sent")
    check("recompose with an eye missing: 409 eyes_not_ready", adm("recompose", order=o2).json().get("reason") == "eyes_not_ready")
    put_json(f"orders/{o2}/withdrawn.json", {"t": time.time()})
    check("render of a withdrawn order: 409 withdrawn", adm("render", order=o2, eye=1).json().get("reason") == "withdrawn")
    master_eye._render_4k = real_render

# ==================================================================================================== 7. stats
if section("stats"):
    reset_limits()
    now = time.time()
    y = time.strftime("%Y-%m-%d", time.gmtime(now - 86400))
    y3 = time.strftime("%Y-%m-%d", time.gmtime(now - 3 * 86400))
    for dday, n in ((y, 3), (y3, 2)):
        shutil.rmtree(os.path.join(STORE, "ops", "events", dday), ignore_errors=True)
        for i in range(n):
            ev = E.build("analyze", {"ok": True, "verdict": "good", "locked": True, "ms": 5000}, now)
            store.put(f"ops/events/{dday}/1200{i:02d}-{secrets.token_hex(6)}.json", store.json_bytes(ev), "application/json")
        store.put(f"ops/events/{dday}/130000-{secrets.token_hex(6)}.json",
                  store.json_bytes(E.build("error", {"endpoint": "enhance", "class": "busy", "status": 503}, now - 86400)), "application/json")
    ops._ROLLUPS.clear()
    ops._DAYCACHE.clear()
    r = adm("stats", days=7)
    days = {x["day"]: x for x in r.json().get("days", [])}
    check("stats: 7 days, oldest first, today last", r.status_code == 200 and len(days) == 7 and list(days)[-1] == time.strftime("%Y-%m-%d", time.gmtime()))
    check("stats: yesterday's counts", days[y]["counts"]["kinds"].get("analyze") == 3 and days[y]["counts"]["verdict"].get("good") == 3
          and days[y]["counts"]["busy"] == 1, days[y]["counts"]["kinds"])
    check("stats: finished days rolled up once (ops/daily/)", os.path.exists(os.path.join(STORE, "ops", "daily", y + ".json"))
          and os.path.exists(os.path.join(STORE, "ops", "daily", y3 + ".json")))
    check("stats: today is never rolled up", not os.path.exists(os.path.join(STORE, "ops", "daily", time.strftime("%Y-%m-%d", time.gmtime()) + ".json")))
    shutil.rmtree(os.path.join(STORE, "ops", "events", y))
    ops._ROLLUPS.clear()
    r = adm("stats", days=7)
    days2 = {x["day"]: x for x in r.json()["days"]}
    check("stats: a rolled-up day comes from its stored counts", days2[y]["counts"]["kinds"].get("analyze") == 3)
    check("stats: no recent_errors list in the per-day rows", "recent_errors" not in days2[y]["counts"])
    r = adm("errors")
    errs = r.json().get("errors", [])
    check("errors: the latest error events, newest first, with the day", r.status_code == 200 and errs and all("day" in e for e in errs)
          and [e.get("t") or 0 for e in errs] == sorted([e.get("t") or 0 for e in errs], reverse=True), errs[:3])
    check("errors: the enhance busy event of yesterday is there", any(e.get("endpoint") == "enhance" and e.get("kind") == "busy" for e in errs))
    check("errors: no message text", all(set(e) <= {"t", "endpoint", "kind", "reason", "status", "ms", "day"} for e in errs))

print(f"\n{n_checks} checks, {len(fails)} failed" + (": " + "; ".join(fails) if fails else ""))
stub.shutdown()
srv.shutdown()
sys.exit(0 if ok_all else 1)
