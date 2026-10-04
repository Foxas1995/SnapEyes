# -*- coding: utf-8 -*-
"""The fixer's checks for the two findings on the server's own making (api/_lib/maker.py):
  1. a stalled paid order is reported to the owner (a refused self-call, a busy give-up, the daily 'not ready after
     LATE_HOURS' reminder), and the self-call chain can be proven on a deployment (the self-call test, probe);
  2. a failure after a paid render is not retried as busy: counted per order, held for a person at LOST_MAX, with the
     REAL master_eye marking which failures cost nothing (unspent).
Same local setup as ../review/test_review.py (fake Stripe + Resend + legal pack, a local store, the API served in this
process, self-calls to it).  python test_fixmk.py   PASS/FAIL per check, exit 1 on any failure"""
import os, sys, io, json, time, base64, threading, socket, subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(os.path.dirname(HERE))
PB = os.path.join(SP, "wave-r-back", "pb")
sys.path.insert(0, PB)
import harness as H

STORE = os.path.join(HERE, "store_fixmk")
stub = H.start_stub()
H.setup_env(STORE, stub.server_address[1])
api = H.start_api()
BASE = f"http://127.0.0.1:{api.server_address[1]}"
os.environ["SNAPEYES_SELF_BASE"] = BASE

import requests
sys.path.insert(0, H.API)
from _lib import iris as L
from _lib import store
from _lib import pay
from _lib import maker as M
from _lib import cleanup as C

PACK = json.load(open(os.path.join(H.REPO, "dist", "legal", "order-mail.json"), encoding="utf-8"))
PACK_AUTO = dict(PACK, making_start="after_confirmation")
RESULTS = []
DASHES = (chr(0x2013), chr(0x2014))


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"   <- {str(detail)[:900]}"), flush=True)


def post(path, body, headers=None):
    h = {"Content-Type": "application/json"}
    h.update(headers or {})
    r = requests.post(BASE + path, data=json.dumps(body), headers=h, timeout=120)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}


def get(path):
    r = requests.get(BASE + path, timeout=120)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}


def hook(obj):
    body, sig = H.signed_event(obj, "checkout.session.completed")
    r = requests.post(BASE + "/api/stripe_webhook", data=body,
                      headers={"Content-Type": "application/json", "Stripe-Signature": sig}, timeout=120)
    return r.status_code, r.json()


def local(path):
    return os.path.join(STORE, *path.split("/"))


def exists(path):
    return os.path.exists(local(path))


def rj(path):
    try:
        with open(local(path), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def wj(path, obj):
    with open(local(path), "w", encoding="utf-8") as f:
        json.dump(obj, f)


def wait_for(cond, timeout=60.0, step=0.2):
    t0 = time.time()
    while time.time() - t0 < timeout:
        v = cond()
        if v:
            return v
        time.sleep(step)
    return cond()


def gate(on):
    H.Fake.legal = PACK_AUTO if on else PACK
    pay._LEGAL.update(pack=None, t=0.0, failed=0.0)
    M._KICKED.clear()


def draft(eye, order=None, k=None, seed=1):
    b = {"action": "draft", "eye": eye, "crop": H.jpeg_b64(256, seed * 10 + eye), "preview": H.jpeg_b64(256, seed * 10 + eye + 5),
         "pad": 1.12, "ticket": H.fresh_ticket() if order is None else L.mint_ticket("work"), "lang": "en", "ref": f"e{eye}"}
    if order:
        b.update(order=order, k=k)
    return post("/api/order", b)


def new_order(eyes=2, email="kunde@example.com"):
    c, j = draft(1)
    assert c == 200, (c, j)
    o, k = j["order"], j["k"]
    for i in range(2, eyes + 1):
        c, j = draft(i, o, k)
        assert c == 200, (c, j)
    c, j = post("/api/checkout", {"order": o, "k": k, "eyes": eyes, "style": "studio_black", "names": "Ona", "title": "",
                                  "lang": "en", "consent_digital": True})
    assert c == 200, (c, j)
    sid = rj(f"orders/{o}/order.json")["checkout"]["session_id"]
    c, j = hook(H.pay_session(sid, email=email))
    assert c == 200, (c, j)
    return o, k


def owner_mails(order, since=0, word=None):
    own = pay.owner_mail()
    return [m for m, _ in H.Fake.emails[since:] if m["to"] == [own] and order in m["subject"]
            and (word is None or word in m["subject"])]


def stopped(o, why=None):
    b = rj(f"orders/{o}/advance.json")
    return isinstance(b, dict) and b.get("state") == "stopped" and (why is None or b.get("why") == why) and b


def dead_base():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return f"http://127.0.0.1:{port}"


ORDER_MOD = H.MODS["order"]
ME, MC = ORDER_MOD.ME, ORDER_MOD.MC
REAL_ME = ME.master_eye
LOCK = threading.Lock()
RENDERS, COMPOSES = [], []
MODE = {"delay": 0.3, "boom": set(), "upload_fail": set(), "busy": 0}


def fake_master_eye(body):
    """As test_review.py's stub: the REAL eye claim; failures after the 'render' are raised UNMARKED, as an unknown
    failure out of master_eye would be (the conservative side: counted)."""
    order, eye = body["order"], body["eye"]
    assert L.check_ticket(body["ticket"], kind=store.unlock_kind(order)), "unlock ticket"
    folder = f"orders/{order}"
    key = f"{folder}/eye_{eye}.jpg"
    if store.exists(key):
        return {"ok": True, "existing": True, "seconds": 0.1, "needs_review": False, "key": key}
    lock = ME._claim(folder, eye)
    try:
        if store.exists(key):
            return {"ok": True, "existing": True, "seconds": 0.1, "needs_review": False, "key": key}
        if MODE["busy"] > 0:
            MODE["busy"] -= 1
            raise store.busy("model_busy", 1, "The artwork renderer is busy.")
        if (order, eye) in MODE["boom"]:
            with LOCK:
                RENDERS.append((order, eye))
            raise RuntimeError("post-processing failed")
        time.sleep(MODE["delay"])
        with LOCK:
            RENDERS.append((order, eye))
        if (order, eye) in MODE["upload_fail"]:
            raise store.StorageError(f"put {key}: HTTP 413 payload too large")
        store.put(key, base64.b64decode(body["crop"]), "image/jpeg", upsert=False)
        store.put(f"{folder}/eye_{eye}.json", store.json_bytes({"order": order, "eye": eye, "qa": {"ok": True}}),
                  "application/json", upsert=True)
        return {"ok": True, "existing": False, "seconds": 1.0, "needs_review": False, "key": key}
    finally:
        ME._release(lock)


def fake_master_compose(body):
    order = body["order"]
    time.sleep(0.2)
    key = f"orders/{order}/artwork_fake{len(body['keys'])}.jpg"
    store.put(key, b"artwork", "image/jpeg", upsert=True)
    with LOCK:
        COMPOSES.append(order)
    return {"ok": True, "url": store.signed_url(key, 604800), "key": key, "width": 4096, "height": 2600, "bytes": 7,
            "style": body["style"], "layout": body["layout"], "count": len(body["keys"]), "needs_review": False}


ME.master_eye, MC.master_compose = fake_master_eye, fake_master_compose


def renders(o, eye=None):
    return [e for x, e in RENDERS if x == o and (eye is None or e == eye)]


def lost_files(o):
    return sorted(n for n in os.listdir(local(f"orders/{o}")) if n.startswith("render_lost_"))


# =============================================================================== B. a lost paid render (finding 2)
gate(False)
oU, kU = new_order(2, "u1@example.com")
MODE["upload_fail"].add((oU, 2))
n0 = len(H.Fake.emails)
M._KICKED.clear()
c, j = post("/api/order", {"action": "make", "order": oU, "k": kU, "eye": 1})   # the page makes eye 1, then is closed
first = wait_for(lambda: stopped(oU), 30)
time.sleep(1.0)
check("B1 upload refused after the paid render: the chain rendered eye 2 ONCE and stopped 'render_lost' (no busy retry)",
      c == 200 and bool(first) and first.get("why") == "render_lost" and len(renders(oU, 2)) == 1
      and lost_files(oU) == ["render_lost_1.json"], (c, first, renders(oU), lost_files(oU)))
notes = owner_mails(oU, n0, "could not be finished")
check("B2 ONE owner note for it, naming the lost render and the storage; the index note stays for the daily run",
      len(notes) == 1 and "paid render was lost" in notes[0]["subject"] and "HTTP 413" in notes[0]["text"]
      and exists(f"cleanup/making/{oU}.json"), [m["subject"] for m in notes])
lr = rj(f"orders/{oU}/render_lost_1.json") or {}
check("B3 the count records the eye, the time and the (scrubbed) error", lr.get("eye") == 2 and "HTTP 413" in str(lr.get("error"))
      and isinstance(lr.get("t"), (int, float)), lr)
# the page's status read asks the server again (the one more try); lost again: held for a person
M._KICKED.clear()
c, j = get(f"/api/order?o={oU}&k={kU}")
held = wait_for(lambda: rj(f"orders/{oU}/review.json"), 30)
time.sleep(1.0)
rv = held or {}
check("B4 the second lost render holds the order: review.json 'render_lost', eye 2 rendered twice in all",
      str(rv.get("reason", "")).startswith("render_lost") and rv.get("eye") == 2 and len(renders(oU, 2)) == 2
      and lost_files(oU) == ["render_lost_1.json", "render_lost_2.json"], (rv, renders(oU), lost_files(oU)))
check("B5 the server's chain stopped 'review'; the owner got the 'needs a look' note", bool(stopped(oU, "review"))
      and len(owner_mails(oU, n0, "needs a look")) == 1, (rj(f"orders/{oU}/advance.json"), [m["subject"] for m in owner_mails(oU, n0)]))
n_r = len(renders(oU))
for _ in range(4):
    get(f"/api/order?o={oU}&k={kU}")
    time.sleep(0.4)
cc, cj = post("/api/order", {"action": "make", "order": oU, "k": kU, "eye": 2})
M.CATCHUP_AGE, keep_age = 0, M.CATCHUP_AGE
res = M.catch_up(yes=True, stop_left=-1, max_seconds=30)
M.CATCHUP_AGE = keep_age
time.sleep(1.5)
c, j = get(f"/api/order?o={oU}&k={kU}")
check("B6 held: status reads, the page's make (409 in_review) and the daily run render nothing more",
      len(renders(oU)) == n_r and cc == 409 and cj.get("reason") == "in_review" and j.get("state") == "review"
      and res.get("held", 0) >= 1, (len(renders(oU)), n_r, cc, cj.get("reason"), j.get("state"), res))
todo = C._review_todo(oU, rv)
check("B7 the owner's review reminder explains a lost render (storage) and how to go on (clear-review)",
      "lost" in todo[0] and "clear-review" in todo[1] and "Supabase" in todo[1], todo)
MODE["upload_fail"].discard((oU, 2))
# the owner clears the review: one more try, and it works now
os.remove(local(f"orders/{oU}/review.json"))
M._KICKED.clear()
c, j = post("/api/order", {"action": "make", "order": oU, "k": kU, "eye": 2})
done = wait_for(lambda: stopped(oU, "ready"), 30)
check("B8 after the owner cleared it (storage fixed): the page makes eye 2, the server finishes, ready",
      c == 200 and bool(done) and len(renders(oU, 2)) == 3, (c, j, done, renders(oU)))

# the page alone (no server): the same count holds it at the second loss
gate(False)
oP, kP = new_order(1, "p1@example.com")
MODE["upload_fail"].add((oP, 1))
c1, j1 = post("/api/order", {"action": "make", "order": oP, "k": kP, "eye": 1})
c2, j2 = post("/api/order", {"action": "make", "order": oP, "k": kP, "eye": 1})
c3, j3 = post("/api/order", {"action": "make", "order": oP, "k": kP, "eye": 1})
check("B9 the order page alone: 503 storage_busy (retry), then 409 in_review; two paid renders, the third make renders nothing",
      c1 == 503 and j1.get("reason") == "storage_busy" and c2 == 409 and j2.get("reason") == "in_review"
      and c3 == 409 and len(renders(oP, 1)) == 2, (c1, j1.get("reason"), c2, j2.get("reason"), c3, renders(oP)))
MODE["upload_fail"].discard((oP, 1))

# X6's case: an error after the render, then status reads
gate(False)
oE, kE = new_order(2, "e1@example.com")
MODE["boom"].add((oE, 2))
M._KICKED.clear()
post("/api/order", {"action": "make", "order": oE, "k": kE, "eye": 1})
wait_for(lambda: stopped(oE), 30)
first_n = len(renders(oE, 2))
for _ in range(5):
    M._KICKED.clear()
    get(f"/api/order?o={oE}&k={kE}")
    time.sleep(1.5)
wait_for(lambda: rj(f"orders/{oE}/review.json"), 20)
check("B10 an error after the render (post-processing): 5 status reads cost at most ONE more paid render, then held",
      first_n == 1 and len(renders(oE, 2)) == 2 and isinstance(rj(f"orders/{oE}/review.json"), dict),
      (first_n, renders(oE), rj(f"orders/{oE}/review.json")))
MODE["boom"].discard((oE, 2))

# failures that cost nothing are not counted: a claim that exists, a 400, a marked (unspent) one
gate(False)
oN, kN = new_order(1, "n1@example.com")
recN, paidN = rj(f"orders/{oN}/order.json"), pay.get_paid(oN)
store.put(f"orders/{oN}/making.json", store.json_bytes({"t": time.time(), "eye": 1}), "application/json")
outs = []
for exc in (store.StorageExists("put x: exists"), L.ClientError("bad"), store.mark_unspent(store.StorageError("claim: HTTP 503"))):
    def boom(body, exc=exc):
        raise exc
    ME.master_eye = boom
    try:
        ORDER_MOD.make_eye(oN, recN, paidN, 1)
    except Exception as e:  # noqa
        outs.append((type(e).__name__, store.lost(e)))
ME.master_eye = fake_master_eye
check("B11 StorageExists, a 400 and an unspent-marked failure are NOT counted (no render_lost file, no hold)",
      lost_files(oN) == [] and not exists(f"orders/{oN}/review.json") and [o[1] for o in outs] == [0, 0, 0], (outs, lost_files(oN)))

# =============================================================================== R. the REAL master_eye marks what cost nothing
gate(False)
from PIL import Image
real_render = ME._render_4k
RCALLS = []


def fake_render(base, order_, eye, prompt=None):
    RCALLS.append((order_, eye))
    return base.resize((4096, 4096), Image.BILINEAR), 1, {"prompt": 1, "output": 1}


ME._render_4k = fake_render
ME.master_eye = REAL_ME
real_put = store.put
FAIL_PUT = set()


def flaky_put(path, data, content_type, upsert=False, timeout=30.0, retry=True):
    if path in FAIL_PUT:
        raise store.StorageError(f"put {path}: HTTP 413 payload too large")
    return real_put(path, data, content_type, upsert=upsert, timeout=timeout, retry=retry)


store.put = flaky_put
oR, kR = new_order(1, "r1@example.com")
recR, paidR = rj(f"orders/{oR}/order.json"), pay.get_paid(oR)
store.put(f"orders/{oR}/making.json", store.json_bytes({"t": time.time(), "eye": 1}), "application/json")
# (a) the claim cannot be written: before the model call
FAIL_PUT.add(f"orders/{oR}/eye_1.lock")
try:
    ORDER_MOD.make_eye(oR, recR, paidR, 1, server=True)
    ea = None
except Exception as e:  # noqa
    ea = e
FAIL_PUT.clear()
check("R1 real master_eye: a storage failure before the model call is marked unspent, not counted, no render",
      isinstance(ea, store.StorageError) and store.unspent(ea) and store.lost(ea) == 0 and RCALLS == []
      and lost_files(oR) == [], (repr(ea), RCALLS, lost_files(oR)))
# (b) the model refuses with an HTTP error: unspent
ME._render_4k = real_render
keep_gemini = L.gemini


def gemini_401(*a, **kw):
    raise RuntimeError("gemini gemini-image: HTTP 401 unauthorized")


L.gemini = gemini_401
try:
    ORDER_MOD.make_eye(oR, recR, paidR, 1, server=True)
    eb = None
except Exception as e:  # noqa
    eb = e
L.gemini = keep_gemini
ME._render_4k = fake_render
check("R2 real master_eye: the image model refusing with HTTP 401 is marked unspent, not counted",
      isinstance(eb, RuntimeError) and store.unspent(eb) and lost_files(oR) == [], (repr(eb), lost_files(oR)))
# (c) the master cannot be stored after the render: counted, marked lost
FAIL_PUT.add(f"orders/{oR}/eye_1.jpg")
try:
    ORDER_MOD.make_eye(oR, recR, paidR, 1, server=True)
    ec = None
except Exception as e:  # noqa
    ec = e
FAIL_PUT.clear()
check("R3 real master_eye: the master not stored AFTER the render is a lost render (counted 1, marked for the server)",
      isinstance(ec, store.StorageError) and not store.unspent(ec) and store.lost(ec) == 1 and len(RCALLS) == 1
      and lost_files(oR) == ["render_lost_1.json"] and not exists(f"orders/{oR}/eye_1.jpg"),
      (repr(ec), RCALLS, lost_files(oR)))
# (d) the eye claim is released after it: the next try renders and stores it
r = ORDER_MOD.make_eye(oR, recR, paidR, 1, server=True)
check("R4 ... the claim was released: the next try renders and stores the master", r.get("made") and not r.get("existing")
      and exists(f"orders/{oR}/eye_1.jpg") and len(RCALLS) == 2, (r, RCALLS))
# (e) a failure after the master was stored (its record) loses nothing: not raised at all (logged), not counted
r2 = ORDER_MOD.make_eye(oR, recR, paidR, 1, server=True)
check("R5 a stored master is answered from storage: no render, nothing counted", r2.get("existing") and len(RCALLS) == 2
      and lost_files(oR) == ["render_lost_1.json"], (r2, RCALLS))
store.put = real_put
ME._render_4k = real_render
ME.master_eye = fake_master_eye

# =============================================================================== N. the owner hears of a chain that stops
# N1. busy past MAX_BUSY: one owner note
gate(False)
oD, kD = new_order(1, "d1@example.com")
store.put(f"orders/{oD}/making.json", store.json_bytes({"t": time.time(), "eye": 1}), "application/json")
n0 = len(H.Fake.emails)
M.MAX_BUSY, keep_busy = 1, M.MAX_BUSY
MODE["busy"] = 50
M._KICKED.clear()
M.kick(oD, why="test")
done = wait_for(lambda: stopped(oD, "busy"), 40)
time.sleep(0.5)
nb = owner_mails(oD, n0, "(busy)")
check("N1 a chain that gives up busy: stops 'busy', ONE owner note ('could not be finished automatically (busy)')",
      bool(done) and len(nb) == 1 and "busy answers in a row" in nb[0]["text"] and renders(oD) == [],
      ([m["subject"] for m in owner_mails(oD, n0)], done))
M._KICKED.clear()
M.kick(oD, why="test")
wait_for(lambda: stopped(oD, "busy") and stopped(oD, "busy").get("t", 0) > done.get("t", 0), 40)
check("N2 a second busy give-up of the same order: no second note", len(owner_mails(oD, n0, "(busy)")) == 1)
MODE["busy"], M.MAX_BUSY = 0, keep_busy


# N3. a self-call answered with an error status: one owner note per order, with the code and what it means
class Refuse(BaseHTTPRequestHandler):
    code = 508

    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("content-length") or 0)
        self.rfile.read(n)
        Refuse.seen.append(self.headers.get("User-Agent"))
        self.send_response(Refuse.code)
        self.send_header("Content-Length", "0")
        self.end_headers()


Refuse.seen = []
rs = ThreadingHTTPServer(("127.0.0.1", 0), Refuse)
threading.Thread(target=rs.serve_forever, daemon=True).start()
REFUSE = f"http://127.0.0.1:{rs.server_address[1]}"
gate(False)
oF, kF = new_order(2, "f1@example.com")
n0 = len(H.Fake.emails)
os.environ["SNAPEYES_SELF_BASE"] = REFUSE
M._KICKED.clear()
c, j = post("/api/order", {"action": "make", "order": oF, "k": kF, "eye": 1})   # the page makes eye 1; the nudge: 508
time.sleep(0.5)
nf = owner_mails(oF, n0, "HTTP 508")
check("N3 a self-call answered 508 (Vercel's loop protection): ONE owner note naming it, what it means and the test",
      c == 200 and len(nf) == 1 and "loop protection" in nf[0]["text"] and "selfcall-probe" in nf[0]["text"]
      and Refuse.seen and Refuse.seen[-1] == "snapeyes-self-call/1", ([m["subject"] for m in owner_mails(oF, n0)], Refuse.seen))
M._KICKED.clear()
r = M.kick(oF, why="again")
check("N4 refused again for the same order: 'refused', no second note", r == "refused" and len(owner_mails(oF, n0, "HTTP")) == 1,
      (r, [m["subject"] for m in owner_mails(oF, n0)]))
Refuse.code = 403
oF2, kF2 = new_order(1, "f2@example.com")
n1 = len(H.Fake.emails)
M._KICKED.clear()
r = M.kick(oF2, why="test")
n403 = owner_mails(oF2, n1, "HTTP 403")
check("N5 a 403 (another ticket secret, or the Firewall / Bot Protection): the note says to let snapeyes-self-call/1 through",
      r == "refused" and len(n403) == 1 and "Firewall" in n403[0]["text"] and "snapeyes-self-call/1" in n403[0]["text"],
      (r, [m["subject"] for m in owner_mails(oF2, n1)]))
# N6. inside a chain: the step is done, then its next self-call is refused: stops self_call_refused with the note
Refuse.code = 508
oF3, kF3 = new_order(2, "f3@example.com")
store.put(f"orders/{oF3}/making.json", store.json_bytes({"t": time.time(), "eye": 1}), "application/json")
n2 = len(H.Fake.emails)
os.environ["SNAPEYES_SELF_BASE"] = BASE
M._KICKED.clear()
tk = L.mint_ticket("advance-" + oF3, 300)
os.environ["SNAPEYES_SELF_BASE"] = REFUSE          # the step runs in this process; its NEXT self-call is refused
c, j = post("/api/order", {"action": "advance", "order": oF3, "ticket": tk, "hop": 0})
check("N6 a chain whose next self-call is refused: the step was done (eye 1), stopped self_call_refused, the owner told",
      c == 200 and j.get("why") == "self_call_refused" and renders(oF3) == [1] and len(owner_mails(oF3, n2, "HTTP 508")) == 1,
      (c, j, renders(oF3), [m["subject"] for m in owner_mails(oF3, n2)]))
os.environ["SNAPEYES_SELF_BASE"] = BASE

# N7. a self-call that did not go out is tried once more (same hop, same wait)
calls = []
keep_kick = M.kick


def fake_kick(order, hop=0, busy=0, after=None, wait=0, why=""):
    calls.append((hop, busy, after, wait))
    return "failed" if len(calls) == 1 else "sent"


M.kick = fake_kick
out = M._then("260929-0000000000000000", 3, 0, "abcdef012345", ("next", 0, False, "eye_1"))
M.kick = keep_kick
check("N7 a self-call that failed to go out is sent once more, the same hop", len(calls) == 2 and calls[0] == calls[1]
      and out.get("state") == "next", (calls, out))

# =============================================================================== L. the daily 'not ready' reminder
gate(False)
os.environ["SNAPEYES_SELF_BASE"] = dead_base()      # the self-calls get lost: nothing moves by itself
now = time.time()


def backdate(o, hours):
    p = rj(f"orders/{o}/paid.json")
    p["paid_at"] = now - hours * 3600
    wj(f"orders/{o}/paid.json", p)
    ix = rj(f"cleanup/making/{o}.json") or {}
    ix["t"] = int(now - hours * 3600)
    wj(f"cleanup/making/{o}.json", ix)


oL1, kL1 = new_order(2, "l1@example.com")
M._KICKED.clear()
post("/api/order", {"action": "make", "order": oL1, "k": kL1, "eye": 1})        # begun; then nothing (lost self-call)
backdate(oL1, 13)
oL2, kL2 = new_order(2, "l2@example.com")
M._KICKED.clear()
post("/api/order", {"action": "make", "order": oL2, "k": kL2, "eye": 1})
backdate(oL2, 11)                                                              # not late yet
oL3, kL3 = new_order(1, "l3@example.com")                                      # never opened: the page starts it
backdate(oL3, 20)
oL4, kL4 = new_order(1, "l4@example.com")                                      # held for review: its own reminder
store.put(f"orders/{oL4}/review.json", store.json_bytes({"reason": "draft_missing", "eye": 1, "t": int(now)}), "application/json")
backdate(oL4, 20)
n0 = len(H.Fake.emails)
said = []
dry = M.catch_up(yes=False, stop_left=-1, out=said.append, max_seconds=30)
check("L1 dry run: would remind the owner of the two late unfinished orders (not the young one, not the held one); no email",
      dry.get("late") == 2 and len(H.Fake.emails) == n0 and any(oL1 in s and "would remind" in s for s in said)
      and any(oL3 in s and "would remind" in s for s in said) and not any(oL2 in s and "remind" in s for s in said),
      (dry, [s for s in said if "remind" in s]))
res = M.catch_up(yes=True, stop_left=-1, max_seconds=30)
l1 = owner_mails(oL1, n0, "not ready after")
l3 = owner_mails(oL3, n0, "not ready after")
check("L2 the daily run: ONE reminder each for the two late orders, none for the young or the held one",
      res.get("late") == 2 and len(l1) == 1 and len(l3) == 1 and not owner_mails(oL2, n0, "not ready")
      and not owner_mails(oL4, n0, "not ready"), (res, [m["subject"] for m, _ in H.Fake.emails[n0:]]))
t1 = l1[0]["text"] if l1 else ""
t3 = l3[0]["text"] if l3 else ""
check("L3 the reminder: hours since payment, the 48 h promise, eyes made, why it waits, what to do",
      "13 h" in l1[0]["subject"] and "48 hours" in t1 and "Eyes made: 1 of 2" in t1 and "/admin" in t1
      and "has not taken a step" in t1 and "open their order page" in t3, (t1[:600], t3[:400]))
res2 = M.catch_up(yes=True, stop_left=-1, max_seconds=30)
check("L4 the next day: no second reminder for the same orders", res2.get("late") == 0
      and len(owner_mails(oL1, n0, "not ready")) == 1 and len(owner_mails(oL3, n0, "not ready")) == 1, res2)
os.environ["SNAPEYES_SELF_BASE"] = BASE
check("L5 LATE_HOURS leaves the owner time: a daily run reminds 12 to 36 h after payment, inside the 48",
      M.LATE_HOURS + 24 < 48, M.LATE_HOURS)

# =============================================================================== P. the self-call test (probe)
sys.path.insert(0, os.path.join(H.REPO, "scripts"))
import order_admin as OA
M.PROBE_HOPS, keep_hops = 5, M.PROBE_HOPS
M.PROBE_WORK, keep_work = 1.8, M.PROBE_WORK                   # still longer than KICK_READ: the caller leaves first
buf = io.StringIO()
keep_out = sys.stdout
sys.stdout = buf
try:
    ok = OA.cmd_selfcall_probe(site=BASE)
finally:
    sys.stdout = keep_out
txt = buf.getvalue()
print("   P1 output:\n" + "\n".join("   | " + l for l in txt.splitlines()))
check("P1 the self-call test on a deployment that allows it: PASS, every hop ran after its caller left ('sent')",
      ok is True and "PASS" in txt and len([l for l in txt.splitlines() if l.startswith("  hop") and "the next: sent" in l])
      == M.PROBE_HOPS - 1 and "the next: last" in txt, txt[-600:])
check("P2 the test deleted its files", not os.path.isdir(local("ops/selfcall")) or all(not files for _, _, files in os.walk(local("ops/selfcall"))),
      list(os.walk(local("ops/selfcall"))))
# a deployment whose loop protection stops the 3rd nested call
keep_post = M._post
count = {"n": 0}


def post_508_after_2(body):
    if body.get("probe") and body.get("hop") >= 3:
        return "refused", 508
    return keep_post(body)


M._post = post_508_after_2
buf = io.StringIO()
sys.stdout = buf
try:
    ok2 = OA.cmd_selfcall_probe(site=BASE)
finally:
    sys.stdout = keep_out
M._post = keep_post
txt2 = buf.getvalue()
print("   P3 output:\n" + "\n".join("   | " + l for l in txt2.splitlines()))
check("P3 a deployment that answers 508 at the 3rd nested call: FAIL, naming the loop protection and the depth",
      ok2 is False and "FAIL after 3 of 5 hops" in txt2 and "loop protection" in txt2, txt2[-600:])
# a hop killed when its caller left (the callee does not run on): simulated by a hop that never finishes
keep_sleep = M.time.sleep


class Killed(Exception):
    pass


def post_kill(body):
    if body.get("probe") and body.get("hop") == 2:
        return "sent", None                      # it "went out", but no hop 2 ever runs
    return keep_post(body)


M._post = post_kill
buf = io.StringIO()
sys.stdout = buf
t0 = time.time()
try:
    ok3 = OA.cmd_selfcall_probe(site=BASE)
finally:
    sys.stdout = keep_out
M._post = keep_post
txt3 = buf.getvalue()
check("P4 a call that went out but whose hop never ran: FAIL, 'never ran' (the cold-start / disconnect case)",
      ok3 is False and "never ran" in txt3 and "FAIL after 2 of 5" in txt3, txt3[-500:])
M.PROBE_HOPS, M.PROBE_WORK = keep_hops, keep_work
# only the server's own probe ticket opens it; nothing is written otherwise
bad = []
for label, b in {"no ticket": {"probe": "a1b2c3d4e5f6"},
                 "an order's advance ticket": {"probe": "a1b2c3d4e5f6", "ticket": L.mint_ticket("advance-" + oU, 300)},
                 "another probe's ticket": {"probe": "a1b2c3d4e5f6", "ticket": L.mint_ticket(M.PROBE_KIND + "ffffffffffff", 300)},
                 "a bad probe id": {"probe": "../x", "ticket": L.mint_ticket(M.PROBE_KIND + "../x", 300)},
                 "a work ticket": {"probe": "a1b2c3d4e5f6", "ticket": L.mint_ticket("work")}}.items():
    c, j = post("/api/order", dict({"action": "advance", "hop": 0}, **b))
    if c != 403:
        bad.append((label, c, j))
c, j = post("/api/order", {"action": "advance", "probe": "a1b2c3d4e5f6", "hop": 0,
                           "ticket": L.mint_ticket(M.PROBE_KIND + "a1b2c3d4e5f6", 300)}, headers={"Origin": "https://evil.example"})
if c != 403:
    bad.append(("foreign origin", c, j))
check("P5 the probe action: 403 without its own ticket (or from a foreign site); nothing written",
      not bad and not os.path.isdir(local("ops/selfcall/a1b2c3d4e5f6")), bad)

# =============================================================================== H. hygiene
files = ["api/_lib/maker.py", "api/order.py", "api/master_eye.py", "api/_lib/store.py", "api/_lib/cleanup.py",
         "api/_lib/pay.py", "scripts/order_admin.py"]
badf = []
for f in files:
    t = open(os.path.join(H.REPO, f), encoding="utf-8").read()
    if any(ch in t for ch in DASHES) or any(ord(ch) < 32 and ch not in "\n\t\r" for ch in t):
        badf.append(f)
check("H1 the changed files: no em/en dashes, no control characters", not badf, badf)
r = subprocess.run([sys.executable, "-m", "py_compile"] + [os.path.join(H.REPO, f) for f in files], capture_output=True, text=True)
check("H2 py_compile", r.returncode == 0, r.stderr[-400:])
secret_like = [m for m, _ in H.Fake.emails if "advance-" in m.get("text", "") and "." in m.get("text", "")
               and any(len(p) == 32 and all(ch in "0123456789abcdef" for ch in p) for p in m.get("text", "").split("."))]
check("H3 no owner note carries an internal ticket", not secret_like, [m["subject"] for m in secret_like])

fails = [n for n, ok in RESULTS if not ok]
print(f"\n{len(RESULTS) - len(fails)} of {len(RESULTS)} passed" + (f"; FAILED: {fails}" if fails else ""))
sys.stdout.flush()
os._exit(1 if fails else 0)
