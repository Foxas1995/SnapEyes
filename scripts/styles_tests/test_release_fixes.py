# -*- coding: utf-8 -*-
"""The finish of the release (2026-10-06): what the four reviews of the release branch found, fixed and held by checks. Nothing here is a new feature; each section is one
finding of the reviews (the findings are listed in suites/baseline.md, section 31).

  1. the developer's key file is never read by itself (a probe once spent a real 4K call because it was) and a suite cannot reach a real service
  2. the model's refusal: a blocked, leaked or invalid Gemini key is a plain 503 with a sentence in four languages, the instance remembers it, /api/health says so
  3. /api/health: model, ticket_secret and admin as booleans, and plates_4k only when the first and the last plate of every family are in storage (a good answer kept 60 s)
  4. the display copy of a delivered artwork (the order page shows 1600 px, not the 4096 px file): made once, beside the file, small, deleted with the order, never fatal
  5. a refund stops the page's making; a new eye after the checkout closes the order's open checkout page
  6. small answers: a missing image is a 400, the 409 for missing plates names no plate, the security headers of every page, the share card has no count of styles

No network, no image model (the model's answers are stubs), no real eye.
    python test_release_fixes.py     prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure
Run by suites/run_main.sh as v3rel."""
import atexit
import io
import json
import os
import shutil
import sys
import tempfile
import time
import importlib.util
from unittest import mock

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(REPO, "api")
SP_DIR = os.environ.get("SNAPEYES_SP") or ""
HARNESS = next((d for d in (os.path.join(SP_DIR, "wave-pv", "tests") if SP_DIR else "", os.path.join(REPO, "suites", "tree", "wave-pv", "tests"))
                if d and os.path.isfile(os.path.join(d, "harness.py"))), None) or sys.exit("the payments harness (wave-pv/tests/harness.py) is not found")

RESULTS = []
LOCAL = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   <- {str(detail)[:900]}"), flush=True)


def local(name, ok, detail=""):
    LOCAL.append(bool(ok))
    print(("LOCAL ok   " if ok else "FAIL LOCAL ") + name + ("" if ok else f"   <- {str(detail)[:600]}"), flush=True)


def section(title):
    print(f"\n== {title}", flush=True)


def raised(fn):
    try:
        fn()
    except BaseException as e:  # noqa: BLE001
        return e
    return None


if os.environ.get("SNAPEYES_WORLD"):
    sys.exit("v3rel runs in the real world: SNAPEYES_WORLD must not be set")
PROXIED = (os.environ.get("HTTPS_PROXY") or "").startswith("http://127.0.0.1:9")        # run_all.sh closes the network this way
for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "AWS_", "NOW_", "LAMBDA_", "STORE_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP"):
            os.environ.pop(k)
TMP = tempfile.mkdtemp(prefix="snapeyes_v3rel_")
atexit.register(shutil.rmtree, TMP, ignore_errors=True)
STORE = os.path.join(TMP, "store")
sys.path.insert(0, HARNESS)
sys.path.insert(0, HERE)
os.environ["PYTHONIOENCODING"] = "utf-8"
import harness as H  # noqa: E402

stub = H.start_stub()
H.setup_env(STORE, stub.server_address[1])
sys.path.insert(0, API)
import requests  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import events as E  # noqa: E402
from _lib import store, pay, ops  # noqa: E402
from _lib.styles import plates as PL  # noqa: E402

EVENTS = []
E.record = lambda kind, **f: EVENTS.append((kind, dict(f))) or True
H.start_api()
O, HEALTH = H.MODS["order"], H.MODS["health"]


def mod(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(API, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def read(rel):
    with open(os.path.join(REPO, *rel.split("/")), encoding="utf-8", newline="") as f:
        return f.read()


class Req:
    """A request as L.run and send_json use one."""
    def __init__(self, body=b"{}", path="/api/analyze"):
        self.headers = {"content-length": str(len(body))}
        self.rfile, self.wfile, self.path, self.status = io.BytesIO(body), io.BytesIO(), path, None

    def send_response(self, s):
        self.status = s

    def send_header(self, *a):
        pass

    def end_headers(self):
        pass

    def out(self):
        return json.loads(self.wfile.getvalue().decode("utf-8") or "{}")


def resp(status, text, ok_body=None):
    r = mock.Mock()
    r.status_code, r.text = status, text
    r.json = lambda: ok_body if ok_body is not None else {"candidates": [{"content": {"parts": [{"text": "{}"}]}}]}
    return r


# ============================================================================================ 1. the key file and the net
section("1. the developer's key file is read only on purpose; the suites cannot reach a real service")
os.environ.pop("GEMINI_API_KEY", None)
os.environ.pop("SNAPEYES_DEV_KEYFILE", None)
opened = []
real_exists = os.path.exists


def fake_exists(p):
    return True if str(p).endswith(".gemini-key") else real_exists(p)


def fake_open(p, *a, **k):
    opened.append(str(p))
    return io.StringIO("file-key-0123456789")


with mock.patch("os.path.exists", fake_exists), mock.patch("builtins.open", fake_open):
    e_nokey = raised(L._key)
check("with no GEMINI_API_KEY and no SNAPEYES_DEV_KEYFILE the key file is not read, even where it exists: 'not configured' and nothing opened (release review, security M2)",
      isinstance(e_nokey, RuntimeError) and "not configured" in str(e_nokey) and not opened, (e_nokey, opened))
os.environ["SNAPEYES_DEV_KEYFILE"] = "0"
with mock.patch("os.path.exists", fake_exists), mock.patch("builtins.open", fake_open):
    e_zero = raised(L._key)
check("... SNAPEYES_DEV_KEYFILE=0 (or anything but 1) does not read it either", isinstance(e_zero, RuntimeError) and not opened, (e_zero, opened))
os.environ["SNAPEYES_DEV_KEYFILE"] = "1"
with mock.patch("os.path.exists", fake_exists), mock.patch("builtins.open", fake_open):
    k_file = L._key()
check("... with SNAPEYES_DEV_KEYFILE=1 it is read (the owner's own machine, a real model run on purpose)", k_file == "file-key-0123456789" and len(opened) == 1 and opened[0].endswith(".gemini-key"), (k_file, opened))
os.environ["GEMINI_API_KEY"] = "env-key-0123456789"
opened.clear()
with mock.patch("os.path.exists", fake_exists), mock.patch("builtins.open", fake_open):
    k_env = L._key()
check("... and the environment's key wins without touching the file", k_env == "env-key-0123456789" and not opened, (k_env, opened))
os.environ.pop("SNAPEYES_DEV_KEYFILE")
os.environ.pop("GEMINI_API_KEY")
if PROXIED:
    t0 = time.time()
    e_net = raised(lambda: requests.post("https://generativelanguage.googleapis.com/v1beta/models/x:generateContent", json={}, timeout=8))
    check("run through suites/run_all.sh a request to the model's host is refused at once (ProxyError: the second line against a real call)",
          isinstance(e_net, requests.exceptions.ProxyError) and time.time() - t0 < 7, (type(e_net).__name__, time.time() - t0))
else:
    local("the network is closed by suites/run_all.sh (HTTPS_PROXY to a closed local port); this run was not started by it", True)
check("suites/run_all.sh closes the network and drops the keys before it starts a suite (the script says so)",
      all(s in read("suites/run_all.sh") for s in ("export HTTPS_PROXY=http://127.0.0.1:9", "NO_PROXY=127.0.0.1,localhost,::1", "unset GEMINI_API_KEY GOOGLE_API_KEY SNAPEYES_DEV_KEYFILE")), "")

# ============================================================================================ 2. the model's refusal
section("2. a refused Gemini key is a plain 503, remembered, and told in four languages")
os.environ["GEMINI_API_KEY"] = "test-key-not-real-0123456789"
DENIED_TEXT = '{"error":{"code":403,"message":"Your API key was reported as leaked. Please use another API key.","status":"PERMISSION_DENIED"}}'
cases = {401: ("", True), 403: (DENIED_TEXT, True), 400: ('{"error":{"message":"API key not valid. Please pass a valid API key.","details":[{"reason":"API_KEY_INVALID"}]}}', True)}
got = {}
for status, (text, want) in cases.items():
    with mock.patch.object(L.requests, "post", return_value=resp(status, text)) as post:
        got[status] = (raised(lambda: L.gemini("gemini-test", [{"text": "x"}], {})), post.call_count)
check("a 401, a 403 (PERMISSION_DENIED, a key reported as leaked) and the 400 of an invalid key are ModelDenied, asked ONCE (a retry cannot help), and ModelDenied is a ModelBusy (every busy answer covers it)",
      all(isinstance(e, L.ModelDenied) and isinstance(e, L.ModelBusy) and n == 1 for e, n in got.values()), {s: (type(e).__name__, n) for s, (e, n) in got.items()})
others = {}
for status, text in ((429, "RESOURCE_EXHAUSTED"), (500, "boom"), (503, "overloaded")):
    with mock.patch.object(L.requests, "post", return_value=resp(status, text)), mock.patch.object(L.time, "sleep", lambda s: None):
        others[status] = raised(lambda: L.gemini("gemini-test", [{"text": "x"}], {}, retries=0))
with mock.patch.object(L.requests, "post", return_value=resp(400, '{"error":{"message":"Invalid value at generation_config"}}')):
    other400 = raised(lambda: L.gemini("gemini-test", [{"text": "x"}], {"temperature": 0}))
check("a busy model (429, 500, 503) is still ModelBusy and not ModelDenied; a bad request (400 that is not the key) is a plain RuntimeError, not a refusal of the key",
      all(type(e) is L.ModelBusy for e in others.values()) and type(other400) is RuntimeError, ({s: type(e).__name__ for s, e in others.items()}, type(other400).__name__))
check("_key_denied reads the answer: 401, 403 and the invalid-key 400 are refusals; 200, 400 of another kind, 429, 500 and 503 are not",
      L._key_denied(resp(401, "")) and L._key_denied(resp(403, "x")) and L._key_denied(resp(400, "API_KEY_INVALID")) and L._key_denied(resp(400, "API key not valid"))
      and not any(L._key_denied(resp(s, "")) for s in (200, 400, 429, 500, 503)), "")
L._MODEL.update(ok=0.0, denied=0.0)
check("model_state: 'unknown' while nothing was asked", L.model_state() == "unknown", L.model_state())
with mock.patch.object(L.requests, "post", return_value=resp(403, DENIED_TEXT)):
    raised(lambda: L.gemini("gemini-test", [{"text": "x"}], {}))
check("... 'denied' after a refusal", L.model_state() == "denied", L.model_state())
time.sleep(0.02)
with mock.patch.object(L.requests, "post", return_value=resp(200, "", {"candidates": [{"content": {"parts": [{"text": "{}"}]}}]})):
    L.gemini("gemini-test", [{"text": "x"}], {})
check("... 'ok' after a good answer that came later, and 'unknown' once the last sight is older than 15 minutes",
      L.model_state() == "ok" and (L._MODEL.update(ok=time.time() - 1000.0, denied=0.0) or L.model_state()) == "unknown", L.model_state())
answers = {}
for lang in ("en", "de", "lt", "hu"):
    EVENTS.clear()
    r = Req(json.dumps({"lang": lang}).encode(), path="/api/analyze")
    with mock.patch.object(L.requests, "post", return_value=resp(403, DENIED_TEXT)):
        L.run(r, lambda body: L.gemini("gemini-test", [{"text": "x"}], {}), gate=False)
    answers[lang] = (r.status, r.out(), list(EVENTS))
SENTENCES = {"en": "Our studio is closed for a moment. Please try again later.", "de": L.RUN_ERRORS["de"]["denied"], "lt": L.RUN_ERRORS["lt"]["denied"], "hu": L.RUN_ERRORS["hu"]["denied"]}
check("L.run answers a refused key with 503, the reason model_denied and a sentence in the page's language (not the generic 500), and writes a 'busy' error event with the reason model_denied",
      all(st == 503 and o.get("reason") == "model_denied" and o.get("error") == SENTENCES[lg] and o.get("ok") is False and ev and ev[0][0] == "error" and ev[0][1].get("class") == "busy" and ev[0][1].get("reason") == "model_denied"
          for lg, (st, o, ev) in answers.items()), {lg: (a[0], a[1].get("reason"), a[2][:1]) for lg, a in answers.items()})
check("... the four sentences are four different sentences, none is the busy one or the generic one",
      len(set(SENTENCES.values())) == 4 and all(s != L._say(lg, "busy", "") and s != L._say(lg, "failed", "") for lg, s in SENTENCES.items()), SENTENCES)
with mock.patch.object(L.requests, "post", return_value=resp(429, "RESOURCE_EXHAUSTED")), mock.patch.object(L.time, "sleep", lambda s: None):
    r = Req(json.dumps({"lang": "en"}).encode())
    L.run(r, lambda body: L.gemini("gemini-test", [{"text": "x"}], {}, retries=0), gate=False)
check("a busy model still answers the busy sentence (503 'very busy'), unchanged", r.status == 503 and "very busy" in r.out().get("error", "") and "reason" not in r.out(), (r.status, r.out()))
os.environ.pop("GEMINI_API_KEY")

# ============================================================================================ 3. health
section("3. /api/health: the model, the two secrets, and the plates")


def health():
    cap = {}
    with mock.patch.object(L, "send_json", lambda req, code, info: cap.update(code=code, info=info)):
        HEALTH.handle(mock.Mock())
    return cap["info"]


L._MODEL.update(ok=0.0, denied=time.time())
h_denied = health()
L._MODEL.update(ok=time.time() + 1.0, denied=0.0)
h_ok = health()
L._MODEL.update(ok=0.0, denied=0.0)
h_unknown = health()
check("health says what this instance saw of the model: denied, ok, unknown (gemini_key only says that a key is set)", (h_denied["model"], h_ok["model"], h_unknown["model"]) == ("denied", "ok", "unknown"), (h_denied.get("model"), h_ok.get("model"), h_unknown.get("model")))
rows = []
for name, env in (("neither", {}), ("ticket 16", {"SNAPEYES_TICKET_SECRET": "t" * 16}), ("ticket 40", {"SNAPEYES_TICKET_SECRET": "t" * 40}),
                  ("admin 40", {"SNAPEYES_ADMIN_SECRET": "a" * 40}), ("admin 20, ticket 40", {"SNAPEYES_ADMIN_SECRET": "a" * 20, "SNAPEYES_TICKET_SECRET": "t" * 40}),
                  ("admin 40, ticket 5", {"SNAPEYES_ADMIN_SECRET": "a" * 40, "SNAPEYES_TICKET_SECRET": "t" * 5})):
    with mock.patch.dict(os.environ, env, clear=False):
        for k in ("SNAPEYES_ADMIN_SECRET", "SNAPEYES_TICKET_SECRET"):
            if k not in env:
                os.environ.pop(k, None)
        h = health()
        rows.append((name, h["ticket_secret"], h["admin"], ops.admin_problem() == ""))
H.setup_env(STORE, stub.server_address[1], fresh=False)
check("health's ticket_secret is 16 characters or more, and admin follows the rule of ops.admin_problem() in every case (an admin secret that is set but short does not fall back to the ticket secret)",
      rows == [("neither", False, False, False), ("ticket 16", True, False, False), ("ticket 40", True, True, True), ("admin 40", False, True, True), ("admin 20, ticket 40", True, False, False), ("admin 40, ticket 5", False, True, True)], rows)
check("health holds no secret: its values are booleans, a commit and two model words",
      all(isinstance(v, (bool, str)) for v in health().values()) and "paybackend-test-secret" not in json.dumps(health()), "")
# the plates: first and last of every family, a good answer kept 60 s, a bad one never
fam = "P-EL-FLAME"
ids = sorted(PL.storage_ids([fam]))
samples = PL.health_samples([fam])
check("the plates health asks for the first and the last plate (by id) of a family, one plate for a family of one", samples == [ids[0], ids[-1]] and len(ids) > 2, (samples, len(ids)))
real_exists_store = store.exists
calls = []


def counting_exists(path, *a, **k):
    calls.append(path)
    return real_exists_store(path, *a, **k)


with mock.patch.object(PL, "expected_families", return_value={fam}), mock.patch.object(store, "exists", counting_exists):
    PL._HEALTH.put("until", 0.0)
    store.put(PL.storage_path(ids[0]), b"x", "image/png", upsert=True)
    a1 = PL.health()["plates_4k"]
    store.put(PL.storage_path(ids[-1]), b"x", "image/png", upsert=True)
    n_before = len(calls)
    a2 = PL.health()["plates_4k"]
    n_second = len(calls) - n_before
    a3 = PL.health()["plates_4k"]
    n_third = len(calls) - n_before - n_second
    PL._HEALTH.put("until", 0.0)
    store.delete(PL.storage_path(ids[-1]))
    a4 = PL.health()["plates_4k"]
    a5 = PL.health()["plates_4k"]
check("plates_4k: false with only the first plate stored, true with the first and the last (two existence requests), true again from the cache with no request for 60 s, and a plate that goes missing is seen at once after the cache ends",
      (a1, a2, n_second, a3, n_third, a4, a5) == (False, True, 2, True, 0, False, False), (a1, a2, n_second, a3, n_third, a4, a5))
PL._HEALTH.put("until", 0.0)

# ============================================================================================ 4. the display copy
section("4. the display copy of a delivered artwork")
rng = np.random.default_rng(3)
yy, xx = np.mgrid[0:2400, 0:2400]
rr = np.hypot(xx - 1200, yy - 1200) / 1200
big = np.stack([np.clip(255 * (1 - rr), 0, 255), np.clip(160 * (1 - rr) + 30 * np.sin(xx / 5.0), 0, 255), np.clip(80 + 50 * np.cos(yy / 9.0), 0, 255)], -1)
big = np.clip(big + rng.normal(0, 5, big.shape), 0, 255).astype("uint8")
buf = io.BytesIO()
Image.fromarray(big).save(buf, "JPEG", quality=95, subsampling=0)
master = buf.getvalue()
ORD = "260106-display1"
store.put(f"orders/{ORD}/artwork.jpg", master, "image/jpeg", upsert=True)
dl = {"key": f"orders/{ORD}/artwork.jpg", "width": 2400, "height": 2400, "bytes": len(master)}
d1 = O._display(ORD, dl["key"], dl)
raw_disp = store.get(f"orders/{ORD}/display.jpg")
im_disp = Image.open(io.BytesIO(raw_disp))
check("a file longer than DISPLAY_FROM gets a display copy of DISPLAY_SIDE px beside it, progressive, much smaller than the file, and the answer names its size and a link",
      d1 and (d1["width"], d1["height"]) == (O.DISPLAY_SIDE, O.DISPLAY_SIDE) and im_disp.size == (O.DISPLAY_SIDE, O.DISPLAY_SIDE) and im_disp.info.get("progressive") and len(raw_disp) < len(master) / 5 and d1["url"], (d1, im_disp.size, len(raw_disp), len(master)))
store.put(f"orders/{ORD}/display.jpg", b"kept-as-it-is", "image/jpeg", upsert=True)
d2 = O._display(ORD, dl["key"], dl)
check("a copy that is there is signed and left alone (never made twice): its stored bytes are untouched", d2 and d2["url"] and store.get(f"orders/{ORD}/display.jpg") == b"kept-as-it-is", d2)
wide = {"key": dl["key"], "width": 4096, "height": 2731, "bytes": 5_000_000}
check("the size of the copy keeps the shape of the file (4096 x 2731 -> 1600 x 1067) and no copy is planned for a small or an unknown file",
      O._display_size(wide) == (1600, 1067) and O._display_size({"width": 1024, "height": 1024}) is None and O._display_size({}) is None and O._display_size({"width": O.DISPLAY_FROM, "height": 10}) is None
      and O._display_size({"width": True, "height": 4096}) is None, O._display_size(wide))
check("a small file is shown as it is (no copy, no request); a file that cannot be read, or is missing, gives no copy and never raises",
      O._display("260106-none0001", "orders/260106-none0001/artwork.jpg", dict(wide)) is None and O._display(ORD, dl["key"], {"width": 800, "height": 800}) is None, "")
store.put("orders/260106-broken01/artwork.jpg", b"this is not a jpeg", "image/jpeg", upsert=True)
check("... a broken file: no copy, no exception, and nothing stored", O._display("260106-broken01", "orders/260106-broken01/artwork.jpg", dict(wide)) is None
      and not store.exists("orders/260106-broken01/display.jpg"), "")
store.put("orders/260106-late0001/artwork.jpg", master, "image/jpeg", upsert=True)
with mock.patch.object(L, "time_left", lambda default=99.0: 3.0):
    d_late = O._display("260106-late0001", "orders/260106-late0001/artwork.jpg", dict(dl))
check("a call with little time left (under DISPLAY_TIME) makes no copy this time: the page shows the file itself, the next call makes it", d_late is None and not store.exists("orders/260106-late0001/display.jpg"), d_late)
dd = O._download(ORD, dl["key"], dl)
check("_download carries display_url, display_width and display_height beside the old fields, and the old fields are as they were (url, download_url, expires_in, width, height, bytes)",
      {"url", "download_url", "expires_in", "width", "height", "bytes", "display_url", "display_width", "display_height"} <= set(dd) and dd["width"] == 2400 and dd["download_url"].endswith(f"download=SnapEyes-{ORD}.jpg")
      and dd["display_width"] == dd["display_height"] == O.DISPLAY_SIDE, sorted(dd))
check("the old reply stands where the file is small: no display fields", "display_url" not in O._download(ORD, dl["key"], {"width": 800, "height": 800, "bytes": 90_000, "key": dl["key"]}), "")
check("the copy goes with the order: it is no kept record, and erasing an order's files deletes it",
      not pay.kept_record(f"orders/{ORD}/display.jpg") and (pay.erase_files(ORD, "test", yes=True) or True) and not store.exists(f"orders/{ORD}/display.jpg") and not store.exists(f"orders/{ORD}/artwork.jpg"), "")
src_order = read("src/order/OrderApp.tsx")
check("the order page shows the copy and keeps the file behind the buttons: the ready card's picture is display_url (else url), the download button and the open link use the file",
      "src={d.display_url ?? d.url}" in src_order and "href={d.download_url}" in src_order and 'href={d.url} target="_blank"' in src_order, "")

# ============================================================================================ 5. a refund, a new eye
section("5. a refund stops the page's making; a new eye closes the open checkout")
R1 = "260106-refund01"
paid = {"spec": {"eyes": 1}, "payment_intent": "pi_test_abcdef123456"}
with mock.patch.object(pay, "confirm_paid", return_value=(paid, False)), mock.patch.object(pay, "paid_counts", return_value=True):
    ok_paid = O._require_paid(R1, {}, None)
    store.put(pay.order_path(R1, "refunded.json"), b"{}", "application/json", upsert=True)
    e_ref = raised(lambda: O._require_paid(R1, {}, None))
    R2 = "260106-refund02"
    mark = O.M.refund_marks(R2, paid)[1]
    ok_before = O._require_paid(R2, {}, None)
    store.put(mark, b"{}", "application/json", upsert=True)
    e_ref2 = raised(lambda: O._require_paid(R2, {}, None))
check("an order that is paid and not refunded passes _require_paid; one with refunded.json, or with the admin panel's refund of its payment, is 409 refunded (make and compose answer it before anything is drawn)",
      ok_paid is paid and ok_before is paid and isinstance(e_ref, store.Answer) and e_ref.status == 409 and e_ref.body["reason"] == "refunded"
      and isinstance(e_ref2, store.Answer) and e_ref2.status == 409 and e_ref2.body["reason"] == "refunded", (e_ref, e_ref2))
ticket = H.fresh_ticket()
order, k, rec, created = pay.order_for_ticket(ticket, "en")
rec = dict(rec, checkout={"session_id": "cs_test_a1b2c3d4e5f6"}, sessions=[])
closed = []
body = {"order": order, "k": k, "ticket": ticket, "eye": 1, "crop": "c", "sealed": "s", "lang": "en"}
patches = dict(_ordering_open=lambda: None, _image=lambda raw, what, mx: (b"jpegbytes", "JPEG", 64), _preview_full=lambda b: (b"previewbytes", "JPEG", 64, {"eye_id": "0123456789abcdef"}), _open_draft=lambda o, kk: rec)
with mock.patch.multiple(O, **patches), mock.patch.object(pay, "close_open_sessions", lambda o, r: closed.append((o, r["checkout"]["session_id"])) or (None, False)):
    out1 = O.draft(dict(body))
check("a new eye for an order that already went to Stripe closes its open checkout pages (the old tab would take a payment for the eyes as they were)",
      out1.get("ok") and not out1["created"] and closed == [(order, "cs_test_a1b2c3d4e5f6")], (out1, closed))
closed.clear()
rec2 = dict(rec, checkout=None, sessions=[])
with mock.patch.multiple(O, **dict(patches, _open_draft=lambda o, kk: rec2)), mock.patch.object(pay, "close_open_sessions", lambda o, r: closed.append(o) or (None, False)):
    out2 = O.draft(dict(body))
check("... and an order that never went to Stripe asks Stripe nothing", out2.get("ok") and closed == [], (out2, closed))
with mock.patch.multiple(O, **patches), mock.patch.object(pay, "close_open_sessions", side_effect=RuntimeError("stripe is down")):
    out3 = O.draft(dict(body))
check("... and a Stripe that is down loses no upload: the draft still answers ok", out3.get("ok") is True, out3)

# ============================================================================================ 6. small answers, headers, the card
section("6. a missing image is a 400, the plate ids stay in the log, the headers, the share card")
analyze_m, enhance_m, deglare_m = mod("analyze"), mod("enhance"), mod("deglare")
errs = [raised(lambda: analyze_m.analyze({})), raised(lambda: enhance_m.enhance({"ticket": L.mint_ticket()})), raised(lambda: deglare_m.deglare({"ticket": L.mint_ticket()}))]
check("analyze, enhance and deglare without their image raise a ValueError ('no image supplied': L.run answers 400), never a KeyError (a 500 with an error event)",
      all(isinstance(e, ValueError) and not isinstance(e, KeyError) for e in errs), [type(e).__name__ for e in errs])
r400 = Req(b"{}", path="/api/analyze")
L.run(r400, analyze_m.analyze, gate=False)
check("... over run(): 400 with the sentence 'We could not read that image', not 500", r400.status == 400 and "read that image" in r400.out().get("error", ""), (r400.status, r400.out()))
src_ck = read("api/checkout.py")
check("the 409 style_unavailable for missing plates names the style and the reason only (the plate ids go to the server log)",
      'raise pay.unavailable(style, n, "plates")' in src_ck and "plates=lost" not in src_ck and "plate(s) not in storage" in src_ck, "")
vj = json.loads(read("vercel.json"))
rule = next((r for r in vj["headers"] if r["source"] == "/(.*)"), None)
hv = {h["key"]: h["value"] for h in (rule or {}).get("headers", [])}
check("vercel.json gives every page nosniff, X-Frame-Options DENY and a referrer policy (the order and admin pages keep their own no-referrer meta); the cache rules still follow",
      hv == {"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY", "Referrer-Policy": "strict-origin-when-cross-origin"} and vj["headers"][0] is rule
      and any(r["source"] == "/assets/(.*).js" for r in vj["headers"]) and not any(h["key"] == "Content-Security-Policy" for h in (rule or {}).get("headers", [])), hv)
card = np.asarray(Image.open(os.path.join(REPO, "public", "assets", "atelier", "og-founder-eye.jpg")).convert("L")).astype(int)
check("the share card says 'Free watermarked preview' and no count of styles: the place where '... in six styles' was is black", card.shape == (630, 1200) and card[446:481, 914:1061].max() < 16 and card[453:474, 644:912].max() > 120, (card.shape, card[446:481, 914:1061].max()))
landing_art = os.path.join(REPO, "public", "assets", "landing", "art")
check("the pictures of the two held Universe tiles are gone from the page (and from the manifest: check:assets holds the rest)",
      not [f for f in os.listdir(landing_art) if f.startswith(("duo_infinity_bb_uni_", "fam_6_uni_"))], "")
for page in ("index.html", "try.html", "order.html", "admin.html", "terms.html", "privacy.html", "imprint.html", "withdrawal.html"):
    if '<link rel="icon" href="/favicon.svg" type="image/svg+xml" />' not in read(page):
        check(f"{page} names its icon (no /favicon.ico 404 on every page load)", False, page)
        break
else:
    check("every page names its icon (public/favicon.svg), so the browser does not ask for /favicon.ico (a 404 and a console error on every load)", os.path.isfile(os.path.join(REPO, "public", "favicon.svg")), "")

ok = sum(RESULTS)
print(f"\n{ok} of {len(RESULTS)} passed" + (f"   (+ {len(LOCAL)} local checks)" if LOCAL else ""))
sys.exit(0 if ok == len(RESULTS) and all(LOCAL) else 1)
