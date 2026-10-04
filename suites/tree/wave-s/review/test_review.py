# -*- coding: utf-8 -*-
"""Reviewer's adversarial checks of the server's own making (api/_lib/maker.py, /api/order action "advance").
Same local setup as ../advance/test_advance.py: fake Stripe + Resend + legal pack, a local store folder, the API
served in this process (self-calls go to it), master_eye / master_compose stubbed with the REAL eye claim.
    python test_review.py        PASS/FAIL per check (a FAIL here is a finding, not a broken test)"""
import os, sys, json, time, base64, threading, socket
HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(os.path.dirname(HERE))
PB = os.path.join(SP, "wave-r-back", "pb")
sys.path.insert(0, PB)
import harness as H

STORE = os.path.join(HERE, "store_review")
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
from _lib import ops

PACK = json.load(open(os.path.join(H.REPO, "dist", "legal", "order-mail.json"), encoding="utf-8"))
PACK_AUTO = dict(PACK, making_start="after_confirmation")
RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"   <- {str(detail)[:700]}"), flush=True)


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


def mails(to, subject_start=None, since=0):
    return [m for m, _ in H.Fake.emails[since:] if m["to"] == [to]
            and (subject_start is None or m["subject"].startswith(subject_start))]


def stopped(o, why=None):
    b = rj(f"orders/{o}/advance.json")
    return isinstance(b, dict) and b.get("state") == "stopped" and (why is None or b.get("why") == why) and b


ORDER_MOD = H.MODS["order"]
ME, MC = ORDER_MOD.ME, ORDER_MOD.MC
LOCK = threading.Lock()
RENDERS, COMPOSES = [], []
MODE = {"delay": 0.3, "boom": set(), "upload_fail": set()}


def fake_master_eye(body):
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
        if (order, eye) in MODE["boom"]:
            with LOCK:
                RENDERS.append((order, eye))          # the model was called (spent), then something broke
            raise RuntimeError("post-processing failed")
        time.sleep(MODE["delay"])
        with LOCK:
            RENDERS.append((order, eye))
        if (order, eye) in MODE["upload_fail"]:
            raise store.StorageError(f"put {key}: HTTP 413 payload too large")     # after the paid render
        store.put(key, base64.b64decode(body["crop"]), "image/jpeg", upsert=False)
        store.put(f"{folder}/eye_{eye}.json", store.json_bytes({"order": order, "eye": eye, "qa": {"ok": True}}),
                  "application/json", upsert=True)
        return {"ok": True, "existing": False, "seconds": 1.0, "needs_review": False, "key": key}
    finally:
        ME._release(lock)


def fake_master_compose(body):
    order = body["order"]
    assert L.check_ticket(body["ticket"], kind=store.unlock_kind(order)), "unlock ticket"
    time.sleep(0.3)
    key = f"orders/{order}/artwork_fake{len(body['keys'])}.jpg"
    store.put(key, b"artwork", "image/jpeg", upsert=True)
    with LOCK:
        COMPOSES.append(order)
    return {"ok": True, "url": store.signed_url(key, 604800), "key": key, "width": 4096, "height": 2600, "bytes": 7,
            "style": body["style"], "layout": body["layout"], "count": len(body["keys"]), "needs_review": False}


ME.master_eye, MC.master_compose = fake_master_eye, fake_master_compose


def renders(o):
    return sorted(e for x, e in RENDERS if x == o)


def snapshot(o):
    d = local(f"orders/{o}")
    return sorted(os.listdir(d)) if os.path.isdir(d) else []


# =============================================================================== X1. advance from outside
gate(False)
oX, kX = new_order(2, "x1@example.com")
oY, kY = new_order(2, "y1@example.com")
before = snapshot(oX)
idx_before = exists(f"cleanup/making/{oX}.json")
cases = {
    "no ticket": {},
    "the customer's k": {"ticket": kX},
    "a work ticket": {"ticket": L.mint_ticket("work")},
    "this order's unlock ticket": {"ticket": L.mint_ticket(store.unlock_kind(oX), 300)},
    "another order's advance ticket": {"ticket": L.mint_ticket("advance-" + oY, 300)},
    "an expired advance ticket": {"ticket": L.mint_ticket("advance-" + oX, -5)},
    "a forged signature": {"ticket": "advance-" + oX + "." + str(int(time.time()) + 300) + "." + "0" * 32},
    "kind with a dot smuggled": {"ticket": "advance-" + oX + ".x." + "0" * 32},
    "the ticket as a list": {"ticket": [L.mint_ticket("advance-" + oX, 300)]},
}
bad = []
for label, extra in cases.items():
    c, j = post("/api/order", dict({"action": "advance", "order": oX, "hop": 0}, **extra))
    if c != 403:
        bad.append((label, c, j))
c, j = post("/api/order", {"action": "advance", "order": oX.upper(), "ticket": L.mint_ticket("advance-" + oX, 300)})
if c not in (400, 403):
    bad.append(("upper-case order id", c, j))
c, j = post("/api/order", {"action": "advance", "order": oX, "ticket": L.mint_ticket("advance-" + oX, 300)},
            headers={"Origin": "https://evil.example"})
if c != 403:
    bad.append(("foreign Origin with a valid ticket", c, j))
c, j = get(f"/api/order?o={oX}&k={kX}&action=advance")
if "advance" in json.dumps(j) and j.get("state") not in ("paid", "making"):
    bad.append(("GET with action=advance", c, j))
check("X1 every outside attempt at 'advance' is 403 (or 400), and nothing changed in the order folder",
      not bad and snapshot(oX) == before and exists(f"cleanup/making/{oX}.json") == idx_before
      and renders(oX) == [], (bad, snapshot(oX), before))

# =============================================================================== X2. replayed valid ticket, many at once
tk = L.mint_ticket("advance-" + oX, 300)
c, j = post("/api/order", {"action": "make", "order": oX, "k": kX, "eye": 1})     # the page began (texts in force)
n0 = len(H.Fake.emails)
outs = []
ths = [threading.Thread(target=lambda: outs.append(post("/api/order", {"action": "advance", "order": oX, "ticket": tk,
                                                                      "hop": 0}))) for _ in range(6)]
for t in ths:
    t.start()
for t in ths:
    t.join()
done = wait_for(lambda: stopped(oX, "ready"), 60)
check("X2 six replays of one valid ticket at once (plus the page's own nudge): each eye rendered once, one compose, "
      "one ready email", bool(done) and renders(oX) == [1, 2] and COMPOSES.count(oX) == 1
      and len(mails("x1@example.com", "Your SnapEyes artwork is ready")) == 1,
      (done, renders(oX), COMPOSES.count(oX), len(mails("x1@example.com", "Your SnapEyes artwork is ready")), [x[1].get("why") for x in outs]))

# =============================================================================== X3. withdrawn order, valid ticket, relay hop
gate(False)
oW, kW = new_order(3, "w1@example.com")
store.put(f"orders/{oW}/making.json", store.json_bytes({"t": time.time(), "eye": 1}), "application/json")
store.put(f"orders/{oW}/withdrawn.json", store.json_bytes({"t": int(time.time()), "reason": "test"}), "application/json")
c, j = post("/api/order", {"action": "advance", "order": oW, "ticket": L.mint_ticket("advance-" + oW, 300), "hop": 0})
c2, j2 = post("/api/order", {"action": "advance", "order": oW, "ticket": L.mint_ticket("advance-" + oW, 300), "hop": 3,
                             "wait": 1})
time.sleep(4)
check("X3 a withdrawn order: advance stops 'withdrawn', a relay hop's successor stops too, nothing rendered, index gone",
      c == 200 and j.get("why") == "withdrawn" and renders(oW) == [] and not exists(f"cleanup/making/{oW}.json")
      and stopped(oW, "withdrawn"), (c, j, c2, j2, renders(oW)))

# =============================================================================== X4. hop cap and a huge hop number
oH, kH = new_order(2, "h1@example.com")
store.put(f"orders/{oH}/making.json", store.json_bytes({"t": time.time(), "eye": 1}), "application/json")
c, j = post("/api/order", {"action": "advance", "order": oH, "ticket": L.mint_ticket("advance-" + oH, 300),
                           "hop": M.MAX_HOPS})
c2, j2 = post("/api/order", {"action": "advance", "order": oH, "ticket": L.mint_ticket("advance-" + oH, 300),
                             "hop": -5, "busy": -3, "wait": 10 ** 9})
time.sleep(0.5)
check("X4 hop >= MAX_HOPS stops at once without a render; negative or huge numbers are clamped (no long sleep)",
      c == 200 and j.get("why") == "hops" and j2.get("state") in ("waited", "next", "stopped"), (c, j, c2, j2))
wait_for(lambda: stopped(oH), 60)

# =============================================================================== X5. self-call lost, the daily run, a lost index
gate(False)
oS, kS = new_order(3, "s1@example.com")
dead = socket.socket()
dead.bind(("127.0.0.1", 0))
dead_port = dead.getsockname()[1]
dead.close()
os.environ["SNAPEYES_SELF_BASE"] = f"http://127.0.0.1:{dead_port}"
M._KICKED.clear()
c, j = post("/api/order", {"action": "make", "order": oS, "k": kS, "eye": 1})   # the page makes eye 1, then is closed
time.sleep(2.0)
check("X5a the page made eye 1 and was closed; the self-call could not go out: nothing more happens by itself",
      c == 200 and renders(oS) == [1] and not exists(f"orders/{oS}/delivery.json"), (c, j, renders(oS)))
os.environ["SNAPEYES_SELF_BASE"] = BASE
keep_age = M.CATCHUP_AGE
M.CATCHUP_AGE = 0
res = M.catch_up(yes=True, stop_left=-1, max_seconds=30)
done = wait_for(lambda: stopped(oS, "ready"), 60)
check("X5b the daily run picks it up from cleanup/making/ and the server finishes it", bool(done)
      and renders(oS) == [1, 2, 3], (res, done, renders(oS)))
# the same, but the index note is missing (a storage error when paid.json was written, and hop 0 never ran)
oS2, kS2 = new_order(2, "s2@example.com")
os.remove(local(f"cleanup/making/{oS2}.json"))
os.environ["SNAPEYES_SELF_BASE"] = f"http://127.0.0.1:{dead_port}"
M._KICKED.clear()
post("/api/order", {"action": "make", "order": oS2, "k": kS2, "eye": 1})
os.environ["SNAPEYES_SELF_BASE"] = BASE
res2 = M.catch_up(yes=True, stop_left=-1, max_seconds=30)
time.sleep(3)
check("X5c (resilience) with the index note missing, the daily run does not find the order (only the page can finish it)",
      not stopped(oS2, "ready"), (res2, renders(oS2)))
M.CATCHUP_AGE = keep_age

# =============================================================================== X6. an error stop, then status polling
gate(False)
oE, kE = new_order(2, "e1@example.com")
MODE["boom"].add((oE, 2))
M._KICKED.clear()
post("/api/order", {"action": "make", "order": oE, "k": kE, "eye": 1})   # the page makes eye 1; its nudge starts a chain
first = wait_for(lambda: stopped(oE, "error"), 30)
print(f"   X6 first chain: {first}")
n_after_first = len(renders(oE))
for _ in range(5):
    get(f"/api/order?o={oE}&k={kE}")
    wait_for(lambda: stopped(oE, "error"), 10)
    time.sleep(0.3)
extra = len(renders(oE)) - n_after_first
owner = [m for m, _ in H.Fake.emails if "could not be finished" in m["subject"] and oE in m["subject"]]
print(f"   X6 detail: renders after the first error chain {n_after_first}, extra paid attempts from 5 status reads {extra}, owner notes {len(owner)}")
check("X6 (cost) after a permanent error, repeated status reads do not start a new paid attempt each time",
      extra <= 1, f"extra={extra}")
MODE["boom"].discard((oE, 2))

# =============================================================================== X7. storage refuses the upload after the render
gate(False)
oU, kU = new_order(2, "u1@example.com")
MODE["upload_fail"].add((oU, 2))
keep_busy = M.MAX_BUSY
M.MAX_BUSY = 2
M._KICKED.clear()
t0 = time.time()
post("/api/order", {"action": "make", "order": oU, "k": kU, "eye": 1})   # the page makes eye 1; its nudge starts a chain
done = wait_for(lambda: stopped(oU, "busy"), 90)
paid_renders = len([e for e in renders(oU) if e == 2])
print(f"   X7 detail: eye 2 rendered {paid_renders} times by one chain (MAX_BUSY {M.MAX_BUSY}) in {time.time() - t0:.0f} s; "
      f"stop: {done and done.get('why')}")
check("X7 (cost) a storage error AFTER a paid render is not retried as 'busy' (each retry is another paid render)",
      paid_renders <= 1, f"eye 2 rendered {paid_renders} times with MAX_BUSY={M.MAX_BUSY} (default {keep_busy})")
busy_note = [m for m, _ in H.Fake.emails if oU in m["subject"] or oU in m.get("text", "")]
check("X7b the owner hears about a chain that gave up 'busy'", any("could not" in m["subject"] for m in busy_note),
      [m["subject"] for m in busy_note])
M.MAX_BUSY = keep_busy
MODE["upload_fail"].discard((oU, 2))

# =============================================================================== X8. admin release after the server's ready email
gate(False)
oR, kR = new_order(2, "r1@example.com")
post("/api/order", {"action": "make", "order": oR, "k": kR, "eye": 1})
wait_for(lambda: stopped(oR, "ready"), 60)
n0 = len(H.Fake.emails)
try:
    out = ops.act_release({"order": oR}, "test")
except Exception as e:  # noqa
    out = {"error": repr(e)}
second = mails("r1@example.com", "Your SnapEyes artwork is ready", n0)
print(f"   X8 detail: act_release on a non-held artwork already announced: {out.get('mail')}, emails now {len(second)}")
check("X8 (minor) the admin 'release' of an artwork that was never held does not send a second 'ready' email",
      len(second) == 0, [m["text"][:80] for m in second])

n = len(RESULTS)
fails = [r for r in RESULTS if not r[1]]
print(f"\n{n - len(fails)} of {n} passed")
os._exit(0)
