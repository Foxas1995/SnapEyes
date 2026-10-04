# -*- coding: utf-8 -*-
"""The server's own making of paid orders (api/_lib/maker.py, /api/order action "advance"), without real keys: fake
Stripe + Resend + legal pack (../../wave-r-back/pb/harness.py), a local store folder, the API served over HTTP in
this process (the self-calls go to it: SNAPEYES_SELF_BASE), master_eye / master_compose stubbed with the REAL eye
claim (master_eye._claim), so a double render would show.
    python test_advance.py        PASS/FAIL per check, exit 1 on any failure"""
import os, sys, io, json, time, base64, threading, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(os.path.dirname(HERE))
PB = HERE   # wave-pv: the harness copy pointed at the worktree
sys.path.insert(0, PB)
import harness as H

STORE = os.path.join(HERE, "store_adv")
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

RESULTS = []
PACK = json.load(open(os.path.join(H.REPO, "dist", "legal", "order-mail.json"), encoding="utf-8"))
PACK_AUTO = dict(PACK, making_start="after_confirmation")
DASHES = (chr(0x2013), chr(0x2014))
ADMIN = [sys.executable, os.path.join(H.REPO, "scripts", "order_admin.py")]


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


def hook(obj, typ="checkout.session.completed"):
    body, sig = H.signed_event(obj, typ)
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
    """The legal pack the stub serves: with "making_start": "after_confirmation" (the texts say the server starts
    right after the confirmation email) or without it (today's texts: the order page starts it)."""
    H.Fake.legal = PACK_AUTO if on else PACK
    pay._LEGAL.update(pack=None, t=0.0, failed=0.0)
    M._KICKED.clear()


def draft(eye, order=None, k=None, seed=1, lang="en"):
    b = {"action": "draft", "eye": eye, "crop": H.jpeg_b64(256, seed * 10 + eye), "preview": H.jpeg_b64(256, seed * 10 + eye + 5),
         "pad": 1.12, "ticket": H.fresh_ticket() if order is None else L.mint_ticket("work"), "lang": lang, "ref": f"e{eye}"}
    if order:
        b.update(order=order, k=k)
    return post("/api/order", b)


def new_order(eyes=2, lang="en", email="kunde@example.com", pay_it=True, hook_it=True, style="studio_black"):
    c, j = draft(1, lang=lang)
    assert c == 200, (c, j)
    o, k = j["order"], j["k"]
    for i in range(2, eyes + 1):
        c, j = draft(i, o, k, lang=lang)
        assert c == 200, (c, j)
    c, j = post("/api/checkout", {"order": o, "k": k, "eyes": eyes, "style": style, "names": "Ona", "title": "",
                                  "lang": lang, "consent_digital": True})
    assert c == 200, (c, j)
    sid = rj(f"orders/{o}/order.json")["checkout"]["session_id"]
    if pay_it:
        sess = H.pay_session(sid, email=email)
        if hook_it:
            c, j = hook(sess)
            assert c == 200, (c, j)
    return o, k, sid


def mails(to, subject_start=None, since=0):
    return [m for m, _ in H.Fake.emails[since:] if m["to"] == [to]
            and (subject_start is None or m["subject"].startswith(subject_start))]


READY_EN, READY_DE = "Your SnapEyes artwork is ready", "Ihr SnapEyes-Kunstwerk ist fertig"


def stopped(o, why=None):
    b = rj(f"orders/{o}/advance.json")
    return isinstance(b, dict) and b.get("state") == "stopped" and (why is None or b.get("why") == why) and b


# ------------------------------------------------------------------ the renderer, stubbed (with the real eye claim)
ORDER_MOD = H.MODS["order"]
ME, MC = ORDER_MOD.ME, ORDER_MOD.MC
LOCK = threading.Lock()
RENDERS, COMPOSES = [], []
MODE = {"delay": 0.3, "busy": 0, "reject": set(), "slow": {}, "review": set(), "compose_delay": 0.3}


def fake_master_eye(body):
    order, eye = body["order"], body["eye"]
    assert L.check_ticket(body["ticket"], kind=store.unlock_kind(order)), "unlock ticket"
    folder = f"orders/{order}"
    key = f"{folder}/eye_{eye}.jpg"
    if store.exists(key):
        return {"ok": True, "existing": True, "seconds": 0.1, "needs_review": False, "key": key}
    lock = ME._claim(folder, eye)             # the real slot claim: 409 rendering while another request has it
    try:
        if store.exists(key):
            return {"ok": True, "existing": True, "seconds": 0.1, "needs_review": False, "key": key}
        with LOCK:
            if MODE["busy"] > 0:
                MODE["busy"] -= 1
                raise store.busy("model_busy", 3, "The artwork renderer is busy. Please try again in a moment.")
        if order in MODE["reject"]:
            raise store.Answer(502, "render_rejected", "We could not finish this artwork automatically.", False)
        time.sleep(MODE["slow"].get(order, MODE["delay"]))
        with LOCK:
            RENDERS.append((order, eye))
        store.put(key, base64.b64decode(body["crop"]), "image/jpeg", upsert=False)
        store.put(f"{folder}/eye_{eye}.json", store.json_bytes({"order": order, "eye": eye, "qa": {"ok": True}}),
                  "application/json", upsert=True)
        return {"ok": True, "existing": False, "seconds": 1.0, "needs_review": False, "key": key}
    finally:
        ME._release(lock)


def fake_master_compose(body):
    order = body["order"]
    assert L.check_ticket(body["ticket"], kind=store.unlock_kind(order)), "unlock ticket"
    for kk in body["keys"]:
        assert store.exists(kk), kk
    time.sleep(MODE["compose_delay"])
    key = f"orders/{order}/artwork_fake{len(body['keys'])}.jpg"
    store.put(key, b"artwork", "image/jpeg", upsert=True)
    with LOCK:
        COMPOSES.append(order)
    return {"ok": True, "url": store.signed_url(key, 604800), "key": key, "width": 4096, "height": 2600, "bytes": 7,
            "style": body["style"], "layout": body["layout"], "count": len(body["keys"]),
            "needs_review": order in MODE["review"]}


ME.master_eye, MC.master_compose = fake_master_eye, fake_master_compose


def renders(o):
    return sorted(e for x, e in RENDERS if x == o)


# ======================================================================================= A. tab closed, no page at all
gate(True)
n0 = len(H.Fake.emails)
oA, kA, _ = new_order(2, "en", "anna@example.com")
conf = mails("anna@example.com", "Your SnapEyes order", n0)
t = conf[0]["text"] if conf else ""
check("A1 confirmation (texts that say the server starts): 'right after this email', no 'When you open it'",
      len(conf) == 1 and "We start making your artwork right after this email has been sent" in t
      and "When you open it, we start" not in t and "“Withdraw from contract here”" in t
      and f"/order?o={oA}&k={kA}&withdraw=1&lang=en" in t and not any(d in t for d in DASHES), t[:1800])
check("A2 the confirmation mark says which practice the email described (making: server)",
      (rj(f"orders/{oA}/mail_delivery.json") or {}).get("making") == "server", rj(f"orders/{oA}/mail_delivery.json"))
done = wait_for(lambda: stopped(oA, "ready"), 40)
check("A3 no page at all: the server made both eyes, the artwork and stopped 'ready'", bool(done)
      and exists(f"orders/{oA}/delivery.json") and renders(oA) == [1, 2] and COMPOSES.count(oA) == 1, (done, renders(oA)))
rd = mails("anna@example.com", READY_EN, n0)
check("A4 the customer got ONE 'ready' email with the order page link (not 'checked')", len(rd) == 1
      and f"/order?o={oA}&k={kA}&lang=en" in rd[0]["text"] and "ready and checked" not in rd[0]["text"]
      and (rj(f"orders/{oA}/mail_ready.json") or {}).get("state") == "sent", [m["subject"] for m, _ in H.Fake.emails[n0:]])
mk, md = rj(f"orders/{oA}/making.json") or {}, rj(f"orders/{oA}/mail_delivery.json") or {}
check("A5 making began after the confirmation went out (making.json after mail_delivery.json, withdraw.py's rule)",
      mk.get("t", 0) >= md.get("t", 1e18) and mk.get("confirmation_at") == md.get("t"), (mk, md))
check("A6 the index note is gone, the lease released", not exists(f"cleanup/making/{oA}.json")
      and not exists(f"orders/{oA}/advance.lock") and not exists(f"orders/{oA}/compose.lock"))
c, j = get(f"/api/order?o={oA}&k={kA}")
check("A7 the order page opened later: ready with a download, no 'server' block", c == 200 and j["state"] == "ready"
      and j.get("download", {}).get("url") and "server" not in j, j)
check("A8 no owner note about an error", not any("could not be finished" in m["subject"] for m, _ in H.Fake.emails), "")

# ======================================================================================= B. texts in force: the page starts it
gate(False)
n0 = len(H.Fake.emails)
oB, kB, _ = new_order(2, "de", "berta@example.com")
conf = mails("berta@example.com", "Ihre SnapEyes-Bestellung", n0)
t = conf[0]["text"] if conf else ""
check("B1 confirmation (texts in force): 'Sobald Sie diese Seite öffnen' as before, the mark says making: page",
      len(conf) == 1 and "Sobald Sie diese Seite öffnen, beginnen wir mit der Erstellung" in t
      and "Direkt nach dem Versand" not in t and (rj(f"orders/{oB}/mail_delivery.json") or {}).get("making") == "page", t[:1200])
time.sleep(3.0)
check("B2 the server does NOT start it: no self-call, no making.json, no eye", not exists(f"orders/{oB}/making.json")
      and not exists(f"orders/{oB}/advance.json") and renders(oB) == [], renders(oB))
c, j = get(f"/api/order?o={oB}&k={kB}")
time.sleep(2.0)
check("B3 a status read (the withdrawal page reads one) starts nothing: server inactive, no making.json",
      c == 200 and j["state"] == "paid" and j.get("server", {}).get("active") is False
      and not exists(f"orders/{oB}/making.json"), (c, j))
c, j = post("/api/order", {"action": "make", "order": oB, "k": kB, "eye": 1})
check("B4 the page makes eye 1 (making began)", c == 200 and j.get("made") and not j.get("existing"), (c, j))
done = wait_for(lambda: stopped(oB, "ready"), 40)
rd = mails("berta@example.com", READY_DE, n0)
check("B5 ... then the page is closed: the server finished eye 2 and the artwork by itself, one German 'ready' email",
      bool(done) and renders(oB) == [1, 2] and COMPOSES.count(oB) == 1 and len(rd) == 1, (done, renders(oB), len(rd)))

# ======================================================================================= C. page and server at once
gate(True)
MODE["delay"] = 1.0
n0 = len(H.Fake.emails)
oC, kC, sidC = new_order(3, "en", "carl@example.com", hook_it=False)
log = []


def page_drive(o, k, n):
    """What src/order/driver.ts does: two workers make the eyes (409 rendering: wait and ask again), then compose."""
    q, ql = list(range(1, n + 1)), threading.Lock()

    def worker():
        while True:
            with ql:
                if not q:
                    return
                eye = q.pop(0)
            for _ in range(80):
                c, j = post("/api/order", {"action": "make", "order": o, "k": k, "eye": eye})
                log.append(("make", eye, c, j.get("reason"), j.get("existing")))
                if c == 200:
                    break
                if j.get("reason") in ("rendering", "busy_retry", "model_busy", "confirming"):
                    time.sleep(0.4)
                    continue
                return
    ws = [threading.Thread(target=worker) for _ in range(2)]
    for w in ws:
        w.start()
    for w in ws:
        w.join()
    for _ in range(80):
        c, j = post("/api/order", {"action": "compose", "order": o, "k": k})
        log.append(("compose", c, j.get("reason"), j.get("state")))
        if c == 200:
            return j
        if j.get("reason") in ("rendering", "eyes_not_ready"):
            time.sleep(0.4)
            continue
        return j


hook_thread = threading.Thread(target=lambda: hook(H.pay_session(sidC, email="carl@example.com")))
hook_thread.start()
wait_for(lambda: (rj(f"orders/{oC}/mail_delivery.json") or {}).get("state") == "sent", 20, 0.05)
page = page_drive(oC, kC, 3)
hook_thread.join()
done = wait_for(lambda: stopped(oC), 40)
check("C1 page and server at once: ready, each eye rendered ONCE, the artwork composed ONCE", isinstance(page, dict)
      and page.get("state") == "ready" and renders(oC) == [1, 2, 3] and COMPOSES.count(oC) == 1, (page, renders(oC), log))
check("C2 the two really met: some page request got 409 rendering or found an eye made already",
      any((x[0] == "make" and (x[3] == "rendering" or x[4])) or (x[0] == "compose" and x[2] == "rendering") for x in log), log)
rd = mails("carl@example.com", READY_EN, n0)
check("C3 ONE ready email and ONE confirmation", len(rd) == 1 and len(mails("carl@example.com", "Your SnapEyes order", n0)) == 1,
      [m["subject"] for m in mails("carl@example.com", None, n0)])
MODE["delay"] = 0.3

# ======================================================================================= D. a busy model
gate(True)
n0 = len(H.Fake.emails)
MODE["busy"] = 2
t0 = time.time()
oD, kD, _ = new_order(2, "en", "dora@example.com")
seen_wait = wait_for(lambda: (rj(f"orders/{oD}/advance.json") or {}).get("state") == "waiting", 20, 0.1)
done = wait_for(lambda: stopped(oD, "ready"), 60)
check("D1 two 'model busy' answers: the server waited (advance.json waiting) and finished, each eye once",
      bool(seen_wait) and bool(done) and renders(oD) == [1, 2] and MODE["busy"] == 0 and time.time() - t0 >= 9, (seen_wait, done, renders(oD)))
check("D2 one ready email after the back-off", len(mails("dora@example.com", READY_EN, n0)) == 1)
M.MAX_BUSY, keep_busy = 1, M.MAX_BUSY
MODE["busy"] = 50
oD2, kD2, _ = new_order(1, "en", "dan@example.com")
done = wait_for(lambda: stopped(oD2), 40)
check("D3 busy past MAX_BUSY: the chain stops 'busy', nothing rendered, the index note stays for the daily run",
      bool(done) and done.get("why") == "busy" and renders(oD2) == [] and exists(f"cleanup/making/{oD2}.json"), done)
MODE["busy"], M.MAX_BUSY = 0, keep_busy
check("D4 the page would be told the server is not on it", M.view(rj(f"orders/{oD2}/advance.json"))["active"] is False)
c, j = get(f"/api/order?o={oD2}&k={kD2}")
done = wait_for(lambda: stopped(oD2, "ready"), 40)
check("D5 ... and its status call asks the server again (an unfinished order nobody is on): active, then ready",
      c == 200 and j["state"] == "paid" and j.get("server", {}).get("active") is True and bool(done)
      and renders(oD2) == [1], (j.get("server"), done))

# ======================================================================================= E. a withdrawal on the way
gate(True)
MODE["slow"] = {}
n0 = len(H.Fake.emails)
oE, kE, sidE = new_order(2, "en", "erik@example.com", hook_it=False)
MODE["slow"][oE] = 2.0
hook(H.pay_session(sidE, email="erik@example.com"))
wait_for(lambda: exists(f"orders/{oE}/eye_1.jpg"), 20, 0.05)
c, j = post("/api/order", {"action": "withdraw", "order": oE, "k": kE, "name": "Erik", "email": "erik@example.com", "lang": "en"})
check("E1 withdrawal after the first eye (making began after the confirmation): lapsed, recorded",
      c == 200 and j["withdrawal"]["state"] == "lapsed" and j["withdrawal"]["reason"] == "making_began", (c, j))
done = wait_for(lambda: stopped(oE), 40)
check("E2 ... so the server goes on and finishes (the right had ended)", bool(done) and done.get("why") == "ready"
      and renders(oE) == [1, 2] and not exists(f"orders/{oE}/withdrawn.json"), (done, renders(oE)))
# the right has NOT lapsed: making began without the confirmation email (a test order where email is off)
keep_resend = os.environ.pop("RESEND_API_KEY")
oF, kF, sidF = new_order(2, "en", "fay@example.com", hook_it=False)
MODE["slow"][oF] = 3.0
c, j = hook(H.pay_session(sidF, email="fay@example.com"))
check("E3 email off, test order: the webhook starts the server itself (no confirmation needed here)", c == 200
      and j.get("mail") == "off" and wait_for(lambda: exists(f"orders/{oF}/making.json"), 15, 0.05), (c, j))
c, j = post("/api/order", {"action": "withdraw", "order": oF, "k": kF, "name": "Fay", "email": "fay@example.com", "lang": "en"})
check("E4 withdrawal while eye 1 renders, without a confirmation: effective (began_without_confirmation)",
      c == 200 and j["withdrawal"]["state"] == "withdrawn" and j["withdrawal"]["reason"] == "began_without_confirmation", (c, j))
done = wait_for(lambda: stopped(oF), 40)
check("E5 the server stops BEFORE the next eye: eye 1 (already rendering) kept, eye 2 never rendered, no artwork",
      bool(done) and done.get("why") == "withdrawn" and renders(oF) == [1] and not exists(f"orders/{oF}/eye_2.jpg")
      and not exists(f"orders/{oF}/delivery.json") and not exists(f"cleanup/making/{oF}.json"), (done, renders(oF)))
c, j = get(f"/api/order?o={oF}&k={kF}")
check("E6 status withdrawn", c == 200 and j["state"] == "withdrawn", j)
os.environ["RESEND_API_KEY"] = keep_resend
# withdrawn before anything was made, then the server is asked: it stops at once
gate(False)
oG, kG, _ = new_order(1, "en", "gus@example.com")
c, j = post("/api/order", {"action": "withdraw", "order": oG, "k": kG, "name": "Gus", "email": "gus@example.com", "lang": "en"})
gate(True)
r = M.kick(oG, why="test")
done = wait_for(lambda: stopped(oG), 20)
check("E7 withdrawn before making began: effective; a later self-call stops at once, nothing rendered",
      j.get("withdrawal", {}).get("state") == "withdrawn" and r in ("sent", "done") and bool(done) and done.get("why") == "withdrawn"
      and renders(oG) == [], (j, r, done))

# ======================================================================================= F. held for review
gate(True)
n0 = len(H.Fake.emails)
oH, kH, sidH = new_order(1, "en", "hana@example.com", hook_it=False)
MODE["review"].add(oH)
hook(H.pay_session(sidH, email="hana@example.com"))
done = wait_for(lambda: stopped(oH), 30)
d = rj(f"orders/{oH}/delivery.json") or {}
check("F1 an artwork a check flags: the server stops 'review', NO ready email, the index note stays",
      bool(done) and done.get("why") == "review" and d.get("needs_review") is True
      and not mails("hana@example.com", READY_EN, n0) and exists(f"cleanup/making/{oH}.json"), (done, d))
c, j = get(f"/api/order?o={oH}&k={kH}")
check("F2 status review, no server block", c == 200 and j["state"] == "review" and "server" not in j, j)
env = dict(os.environ)
rr = subprocess.run(ADMIN + ["release", oH], capture_output=True, text=True, env=env, encoding="utf-8")
got = mails("hana@example.com", READY_EN, n0)
check("F3 the owner releases it: ready, ONE 'ready and checked' email from the release", rr.returncode == 0
      and len(got) == 1 and "ready and checked" in got[0]["text"], (rr.stdout[-400:], rr.stderr[-400:], len(got)))
pj = rj(f"orders/{oH}/paid.json")
pj["paid_at"] -= 3600
wj(f"orders/{oH}/paid.json", pj)
res = C.run(yes=True, lock=False)
check("F4 the daily run: the released order leaves the index, no second ready email", not exists(f"cleanup/making/{oH}.json")
      and len(mails("hana@example.com", READY_EN, n0)) == 1 and res["advance"]["dropped"] >= 1, res.get("advance"))
oI, kI, sidI = new_order(1, "en", "ida@example.com", hook_it=False)
MODE["reject"].add(oI)
n0 = len(H.Fake.emails)
hook(H.pay_session(sidI, email="ida@example.com"))
done = wait_for(lambda: stopped(oI), 30)
notes = [m for m, _ in H.Fake.emails[n0:] if m["to"] == ["info@snapeyes.com"] and "needs a look" in m["subject"]]
check("F5 a refused render: review.json, the server stops 'review', the owner told once, nothing rendered",
      bool(done) and done.get("why") == "review" and exists(f"orders/{oI}/review.json") and len(notes) == 1
      and renders(oI) == [], (done, [m["subject"] for m, _ in H.Fake.emails[n0:]]))
r = M.kick(oI, why="test")
done2 = wait_for(lambda: (rj(f"orders/{oI}/advance.json") or {}).get("t", 0) > done.get("t", 0) and stopped(oI), 20)
check("F6 asked again while held: stops 'review' again, no render, no second note", bool(done2) and done2.get("why") == "review"
      and renders(oI) == [] and len([m for m, _ in H.Fake.emails[n0:] if "needs a look" in m["subject"]]) == 1, done2)
MODE["reject"].discard(oI)

# ======================================================================================= G. the daily catch-up
gate(True)
keep_base = os.environ.pop("SNAPEYES_SELF_BASE")
stuck = [new_order(1, "en", f"s{i}@example.com") for i in range(3)]
young = new_order(1, "en", "young@example.com")
time.sleep(1.0)
check("G1 without a self-call (a lost one) nothing is made", all(renders(o) == [] and not exists(f"orders/{o}/making.json")
                                                                for o, _, _ in stuck + [young]))
os.environ["SNAPEYES_SELF_BASE"] = keep_base
M._KICKED.clear()
for o, _, _ in stuck:
    p = rj(f"orders/{o}/paid.json")
    p["paid_at"] -= 45 * 60
    wj(f"orders/{o}/paid.json", p)
res = C.run(yes=False, lock=False)
check("G2 dry run: would advance the 3 old orders, not the young one; nothing asked for, nothing made",
      res["advance"]["kicked"] == 3 and all(renders(o) == [] for o, _, _ in stuck) and not any(
          exists(f"orders/{o}/advance.json") for o, _, _ in stuck), res.get("advance"))
M.CATCHUP_MAX, keep_max = 2, M.CATCHUP_MAX
res = C.run(yes=True, lock=False)
check("G3 the daily run asks for at most CATCHUP_MAX (2) and says more", res["advance"]["kicked"] == 2 and res["more"] is True
      and res["advance"]["waiting"] >= 1, res.get("advance"))
wait_for(lambda: sum(1 for o, _, _ in stuck if stopped(o, "ready")) >= 2, 40)
res2 = C.run(yes=True, lock=False)
check("G4 the next run takes the rest", res2["advance"]["kicked"] == 1, res2.get("advance"))
M.CATCHUP_MAX = keep_max
ok = wait_for(lambda: all(stopped(o, "ready") for o, _, _ in stuck), 40)
check("G5 all three old orders finished by the catch-up, each eye once; the young one untouched",
      bool(ok) and all(renders(o) == [1] for o, _, _ in stuck) and renders(young[0]) == [], [renders(o) for o, _, _ in stuck])
check("G6 finished orders left the index; the young one is still in it", not any(exists(f"cleanup/making/{o}.json") for o, _, _ in stuck)
      and exists(f"cleanup/making/{young[0]}.json"))
# the young one, never started (its self-call was lost): a status read (the withdrawal page reads one too) must not
# start it; the order page's own make does, and the server finishes it
c, j = get(f"/api/order?o={young[0]}&k={young[1]}")
time.sleep(2.0)
check("G7 a status read never STARTS an order (the withdrawal page reads it): server inactive, no making.json",
      c == 200 and j["state"] == "paid" and j.get("server", {}).get("active") is False
      and not exists(f"orders/{young[0]}/making.json") and renders(young[0]) == [], j.get("server"))
c, j = post("/api/order", {"action": "make", "order": young[0], "k": young[1], "eye": 1})
done = wait_for(lambda: stopped(young[0], "ready"), 30)
check("G7b the order page makes the eye; the server finishes the artwork and the email", c == 200 and bool(done)
      and renders(young[0]) == [1] and len(mails("young@example.com", READY_EN)) == 1, (c, j, done))
# a server step still running is not doubled by the daily run
oJ, kJ, _ = new_order(1, "en", "jo@example.com", hook_it=False)
os.environ.pop("SNAPEYES_SELF_BASE")
hook(H.pay_session(_, email="jo@example.com"))
os.environ["SNAPEYES_SELF_BASE"] = keep_base
p = rj(f"orders/{oJ}/paid.json")
p["paid_at"] -= 45 * 60
wj(f"orders/{oJ}/paid.json", p)
M.beat(oJ, "working", step="eye", eye=1, hop=0)
M._KICKED.clear()
res = C.run(yes=True, lock=False)
check("G8 an order with a live server step (fresh advance.json) is left alone by the daily run", res["advance"]["kicked"] == 0
      and renders(oJ) == [], res.get("advance"))
M.beat(oJ, "stopped", why="test", hop=0)
res = C.run(yes=True, lock=False)
done = wait_for(lambda: stopped(oJ, "ready"), 30)
check("G9 ... and advanced once that step is over", res["advance"]["kicked"] == 1 and bool(done), res.get("advance"))

# ======================================================================================= H. nobody else can ask for a step
gate(True)
oK, kK, _ = new_order(1, "en", "kai@example.com")
wait_for(lambda: stopped(oK, "ready"), 30)
before = sorted(os.listdir(local(f"orders/{oK}")))
cases = {
    "no ticket": {"action": "advance", "order": oK},
    "the customer's access key only": {"action": "advance", "order": oK, "k": kK},
    "k as the ticket": {"action": "advance", "order": oK, "ticket": kK},
    "forged ticket": {"action": "advance", "order": oK, "ticket": f"advance-{oK}.{int(time.time()) + 300}.{'0' * 32}"},
    "expired ticket": {"action": "advance", "order": oK, "ticket": L.mint_ticket(M.KIND + oK, -5)},
    "another order's ticket": {"action": "advance", "order": oK, "ticket": L.mint_ticket(M.KIND + oA, 300)},
    "a work ticket": {"action": "advance", "order": oK, "ticket": L.mint_ticket("work", 300)},
    "this order's unlock ticket": {"action": "advance", "order": oK, "ticket": L.mint_ticket(store.unlock_kind(oK), 300)},
    "no order": {"action": "advance", "ticket": L.mint_ticket(M.KIND + oK, 300)},
}
out = {name: post("/api/order", b) for name, b in cases.items()}
check("H1 every self-call not signed by the server for this order: 403 forbidden", all(c == 403 and j.get("reason") == "forbidden"
                                                                                    for c, j in out.values()), out)
import hmac as _h, hashlib as _hl
msg = f"{M.KIND}{oK}.{int(time.time()) + 300}"
other = msg + "." + _h.new(_hl.sha256(b"snapeyes-ticket-v1:another-secret").digest(), msg.encode(), _hl.sha256).hexdigest()[:32]
c, j = post("/api/order", {"action": "advance", "order": oK, "ticket": other})
check("H2 a ticket signed with another secret: 403", c == 403 and j.get("reason") == "forbidden", (c, j))
c, j = post("/api/order", {"action": "advance", "order": oK, "ticket": L.mint_ticket(M.KIND + oK, 300)},
            {"Origin": "https://evil.example"})
check("H3 a browser from another site, even with a valid ticket: 403 (the origin gate)", c == 403, (c, j))
check("H4 the refused calls wrote nothing into the order", sorted(os.listdir(local(f"orders/{oK}"))) == before,
      (before, sorted(os.listdir(local(f"orders/{oK}")))))
c, j = get(f"/api/order?o={oK}&k={kK}")
st_txt = json.dumps(j)
check("H5 no reply carries an internal ticket", M.KIND not in st_txt, st_txt[:300])
c, j = post("/api/order", {"action": "advance", "order": oK, "ticket": L.mint_ticket(M.KIND + oK, 300), "hop": 1})
check("H6 the server's own ticket works (a finished order: stops 'ready', nothing more made, no second email)",
      c == 200 and j.get("state") == "stopped" and j.get("why") == "ready" and renders(oK) == [1]
      and len(mails("kai@example.com", READY_EN)) == 1, (c, j))
c, j = post("/api/order", {"action": "advance", "order": oK, "ticket": L.mint_ticket(M.KIND + oK, 300), "hop": M.MAX_HOPS})
check("H7 a chain past MAX_HOPS stops", c == 200 and j.get("why") == "hops", (c, j))

# ======================================================================================= I. two chains at once, the lease
gate(True)
os.environ.pop("SNAPEYES_SELF_BASE")
MODE["delay"] = 0.8
oL, kL, _ = new_order(3, "en", "lea@example.com")
os.environ["SNAPEYES_SELF_BASE"] = keep_base
M._KICKED.clear()
ts = [threading.Thread(target=lambda: M.kick(oL, why="twice")) for _ in range(3)]
for x in ts:
    x.start()
for x in ts:
    x.join()
done = wait_for(lambda: stopped(oL, "ready"), 60)
check("I1 three self-calls at once for one order: one step at a time, each eye ONCE, one artwork, one email",
      bool(done) and renders(oL) == [1, 2, 3] and COMPOSES.count(oL) == 1 and len(mails("lea@example.com", READY_EN)) == 1,
      (done, renders(oL)))
MODE["delay"] = 0.3
wj(f"orders/{oL}/advance.lock", {"t": time.time(), "id": "abcdef012345"})
c, j = post("/api/order", {"action": "advance", "order": oL, "ticket": L.mint_ticket(M.KIND + oL, 300), "hop": 3})
c2, j2 = post("/api/order", {"action": "advance", "order": oL, "ticket": L.mint_ticket(M.KIND + oL, 300), "hop": 3,
                            "after": "abcdef012345"})
check("I2 a live lease: another call leaves; the holder's own next hop (after) takes it over",
      j.get("state") == "busy" and j2.get("state") == "stopped" and j2.get("why") == "ready"
      and not exists(f"orders/{oL}/advance.lock"), (j, j2))
wj(f"orders/{oL}/advance.lock", {"t": time.time() - 200, "id": "abcdef012345"})
c, j = post("/api/order", {"action": "advance", "order": oL, "ticket": L.mint_ticket(M.KIND + oL, 300), "hop": 3})
check("I3 a stale lease (a dead invocation) is taken over", j.get("state") == "stopped", j)

# ======================================================================================= J. what the page sees
gate(True)
oN, kN, sidN = new_order(2, "en", "nia@example.com", hook_it=False)
MODE["slow"][oN] = 2.5
hook(H.pay_session(sidN, email="nia@example.com"))
seen = wait_for(lambda: (lambda cj: cj[1] if cj[1].get("server", {}).get("step") == "eye" else None)(get(f"/api/order?o={oN}&k={kN}")), 15, 0.3)
check("J1 while the server renders: status 'server': active, step eye, the eye", bool(seen)
      and seen["server"]["active"] is True and seen["server"]["eye"] in (1, 2), seen)
done = wait_for(lambda: stopped(oN, "ready"), 40)
check("J2 then ready", bool(done))
now = time.time()
check("J3 view(): fresh working active; stopped, 10 min old or missing: not active; waiting until later: active",
      M.view({"state": "working", "t": now - 5, "step": "eye", "eye": 2})["active"] is True
      and M.view({"state": "stopped", "t": now - 1})["active"] is False
      and M.view({"state": "working", "t": now - 600})["active"] is False and M.view(None)["active"] is False
      and M.view({"state": "waiting", "t": now - 110, "until": now + 20})["active"] is True
      and M.view({"state": "compose", "t": now})["active"] is False)

# ======================================================================================= K. the self-call itself
gate(True)
keep_req = M.requests.post
seen_req = []


def fake_post(url, data=None, headers=None, timeout=None, allow_redirects=True):
    seen_req.append({"url": url, "body": json.loads(data), "headers": dict(headers or {}), "timeout": timeout,
                     "redirects": allow_redirects})
    raise requests.exceptions.ReadTimeout("fake")


M.requests.post = fake_post
M._KICKED.clear()
r1 = M.kick(oN, hop=4, busy=1, why="unit")
b = seen_req[-1]
check("K1 the self-call: POST /api/order advance with this order's ticket, 1.5 s timeouts, no redirects, not waited for",
      r1 == "sent" and b["url"] == BASE + "/api/order" and b["body"]["action"] == "advance" and b["body"]["hop"] == 4
      and L.check_ticket(b["body"]["ticket"], kind=M.KIND + oN) and b["timeout"] == (1.5, 1.5) and b["redirects"] is False, b)
saved = {k: os.environ.get(k) for k in ("VERCEL", "VERCEL_ENV", "VERCEL_URL", "VERCEL_AUTOMATION_BYPASS_SECRET", "SNAPEYES_SITE")}
try:
    os.environ.update({"VERCEL": "1", "VERCEL_ENV": "preview", "VERCEL_URL": "snap-eyes-abc123-team.vercel.app",
                       "VERCEL_AUTOMATION_BYPASS_SECRET": "BypassSecret0123456789"})
    os.environ.pop("SNAPEYES_SITE", None)
    M._KICKED.clear()
    r2 = M.kick(oN, why="unit")
    b2 = seen_req[-1]
    os.environ["VERCEL_ENV"] = "production"
    M._KICKED.clear()
    r3 = M.kick(oN, why="unit")
    b3 = seen_req[-1]
finally:
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
check("K2 on a Vercel Preview: its own deployment URL (SNAPEYES_SELF_BASE ignored), with the bypass header",
      r2 == "sent" and b2["url"] == "https://snap-eyes-abc123-team.vercel.app/api/order"
      and b2["headers"].get("x-vercel-protection-bypass") == "BypassSecret0123456789", b2["url"])
check("K3 on production: the site itself (https://snapeyes.com)", r3 == "sent" and b3["url"] == "https://snapeyes.com/api/order", b3["url"])
os.environ["VERCEL_AUTOMATION_BYPASS_SECRET"] = "BypassSecret0123456789"
scrubbed = pay.scrub("x BypassSecret0123456789 y")
os.environ.pop("VERCEL_AUTOMATION_BYPASS_SECRET", None)
check("K4 the bypass secret is scrubbed from log lines", "BypassSecret0123456789" not in scrubbed, scrubbed)
M.requests.post = keep_req
os.environ["SNAPEYES_SELF_BASE"] = f"http://127.0.0.1:{stub.server_address[1]}"      # answers 404 to /api/order
M._KICKED.clear()
r4 = M.kick(oN, why="unit")
os.environ.pop("SNAPEYES_SELF_BASE")
M._KICKED.clear()
r5 = M.kick(oN, why="unit")
os.environ["SNAPEYES_SELF_BASE"] = "https://snapeyes.com"          # a local run may never call a real site
M._KICKED.clear()
r6 = M.kick(oN, why="unit")
os.environ["SNAPEYES_SELF_BASE"] = keep_base
check("K5 an error answer is 'refused'; a local run without SNAPEYES_SELF_BASE (or with a real site in it) makes none",
      r4 == "refused" and r5 == "off" and r6 == "off", (r4, r5, r6))

# ======================================================================================= L. texts
pay._LEGAL.update(pack=None, t=0.0)
paidA = rj(f"orders/{oA}/paid.json")
consent = pay.paid_consent(oA, rj(f"orders/{oA}/order.json"), paidA)
de = dict(paidA, spec=dict(paidA["spec"], lang="de"))
s1, t1, h1 = pay.confirmation_mail(oA, de, kA, PACK_AUTO, dict(consent, lang="de"))
s2, t2, h2 = pay.confirmation_mail(oA, de, kA, PACK, dict(consent, lang="de"))
check("L1 DE confirmation: 'Direkt nach dem Versand dieser E-Mail' where the texts say the server starts, else as before",
      "Direkt nach dem Versand dieser E-Mail beginnen wir" in t1 and "Schaltfläche „Vertrag hier widerrufen“" in t1
      and "Sobald Sie diese Seite öffnen" not in t1 and "Sobald Sie diese Seite öffnen, beginnen wir" in t2
      and not any(d in t1 + t2 for d in DASHES), t1[:1500])
s3, t3, _ = pay.ready_mail(oA, paidA, kA, checked=False)
s4, t4, _ = pay.ready_mail(oA, de, kA, checked=False)
check("L2 the server's ready email: 'is ready', not 'checked' (EN and DE)", "your iris artwork is ready. Download it" in t3
      and "Ihr Iris-Kunstwerk ist fertig. Sie laden" in t4 and "geprüft" not in t4)

# ======================================================================================= M. the order page code
drv = open(os.path.join(H.REPO, "src", "order", "driver.ts"), encoding="utf-8").read()
check("M1 the page driver watches while the server is on it (server.active) and drives otherwise",
      "st.server?.active" in drv and "WATCH_POLL" in drv)
bad = []
for f in ("api/_lib/maker.py", "api/_lib/pay.py", "api/order.py", "api/stripe_webhook.py", "api/_lib/cleanup.py",
          "src/order/driver.ts", "src/order/api.ts", "src/order/copy.ts", "src/order/OrderApp.tsx"):
    tx = open(os.path.join(H.REPO, f), encoding="utf-8").read()
    if any(d in tx for d in DASHES) or any(ord(ch) < 32 and ch not in "\n\t\r" for ch in tx):
        bad.append(f)
check("M2 the changed files: no em/en dashes, no control characters", not bad, bad)

fails = [n for n, ok in RESULTS if not ok]
print(f"\n{len(RESULTS) - len(fails)} of {len(RESULTS)} passed" + (f"; FAILED: {fails}" if fails else ""))
time.sleep(1.0)
api.shutdown()
stub.shutdown()
sys.exit(1 if fails else 0)
