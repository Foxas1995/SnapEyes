# -*- coding: utf-8 -*-
"""The nonce in the work ticket (2026-10-13). A ticket was "<kind>.<expiry>.<signature>" with the expiry in whole seconds, so two /api/analyze calls
in the same second got the SAME ticket, and pay.order_for_ticket (one work ticket, at most one unpaid order, its marker named by the hash of the
ticket string) handed both customers the same unpaid order and access key: one customer's draft could overwrite or expose the other's. A ticket is
now "<kind>.<expiry>.<nonce>.<signature>": a random 16 hex nonce from secrets, signed with kind and expiry by the same HMAC. The three-field form
stays good (tickets minted before the deploy live up to 15 minutes, the internal ones of the self-calls 5).

  1. the form of a minted ticket: four fields, the nonce signed with the kind and the expiry, characters safe in JSON and in a link
  2. two tickets minted in the same second differ (one kind, other kinds, many threads), and the nonce comes from secrets
  3. check_ticket takes both forms by the same rules: kind, expiry (to the last second), a constant-time compare
  4. every tampered nonce, kind, expiry or signature is refused; so is a nonce dropped from a new ticket or added to an old one, another secret, junk
  5. the kinds: a ticket opens its own kind and no other, in both forms; a dotted kind never validates
  6. the places that touch tickets agree: pay.ticket_path, the self-call of maker.kick, the admin lab, scripts/mint_unlock.py, the admin key
  7. END TO END through the payments harness: two analyses in the same second give two tickets and two different unpaid orders, each customer's eye
     stays in its own order, a ticket of the old form still makes an order, a tampered or expired one makes none

No network, no image model (the vision answer is a stub), no real eye: the picture is the public sample eye of the repository.
    python test_ticket_nonce.py     prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure
Run by suites/run_main.sh as v3nonce."""
import atexit
import base64
import contextlib
import hashlib
import hmac
import importlib.util
import io
import json
import os
import re
import secrets
import shutil
import sys
import tempfile
import threading
import time
import urllib.parse
from unittest import mock

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
API = os.path.join(REPO, "api")
SP_DIR = os.environ.get("SNAPEYES_SP") or ""
HARNESS = next((d for d in (os.path.join(SP_DIR, "wave-pv", "tests") if SP_DIR else "", os.path.join(REPO, "suites", "tree", "wave-pv", "tests"))
                if d and os.path.isfile(os.path.join(d, "harness.py"))), None) or sys.exit("the payments harness (wave-pv/tests/harness.py) is not found")

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   <- {str(detail)[:900]}"), flush=True)


def section(title):
    print(f"\n== {title}", flush=True)


def raised(fn):
    try:
        fn()
    except BaseException as e:  # noqa: BLE001
        return e
    return None


for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "AWS_", "NOW_", "LAMBDA_", "STORE_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP"):
            os.environ.pop(k)
TMP = tempfile.mkdtemp(prefix="snapeyes_v3nonce_")
atexit.register(shutil.rmtree, TMP, ignore_errors=True)
STORE = os.path.join(TMP, "store")
sys.path.insert(0, HARNESS)
os.environ["PYTHONIOENCODING"] = "utf-8"
import harness as H  # noqa: E402

stub = H.start_stub()
H.setup_env(STORE, stub.server_address[1])
sys.path.insert(0, API)
import requests  # noqa: E402
from PIL import Image  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import events as E  # noqa: E402
from _lib import store, pay, ops, maker as M  # noqa: E402

E.record = lambda kind, **f: True            # no event is written
SECRET = os.environ["SNAPEYES_TICKET_SECRET"]
srv = H.start_api()
BASE = f"http://127.0.0.1:{srv.server_address[1]}"


def mod(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(API, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


H.MODS.update({n: mod(n) for n in ("analyze", "deglare", "enhance")})      # the harness serves order, checkout, stripe_webhook and health


class FrozenClock:
    """The `time` of api/_lib/iris.py with time() held at one instant (so that tickets are minted, and checked, in 'the same second'); the rest is the real module."""
    def __init__(self, now):
        self.now = now

    def time(self):
        return self.now

    def __getattr__(self, name):
        return getattr(time, name)


def frozen(now):
    return mock.patch.object(L, "time", FrozenClock(now))


def sig_of(msg):
    return hmac.new(L._ticket_secret(), msg.encode(), hashlib.sha256).hexdigest()[:32]


def legacy(kind, ttl=900, now=None):
    """A ticket as mint_ticket made it before the nonce, built by hand: kind.expiry.signature, the HMAC of "kind.expiry" under the ticket secret."""
    msg = kind + "." + str(int(time.time() if now is None else now) + int(ttl))
    return msg + "." + sig_of(msg)


def fields(t, n=4):
    """The dot-separated fields of a ticket, padded with empty strings to n (so that a check on a ticket of the old form FAILS where it must, and does not crash)."""
    p = t.split(".")
    return p + [""] * (n - len(p))


def flip_last(h):
    return h[:-1] + ("0" if h[-1:] != "0" else "1")


def flip_first(h):
    return ("0" if h[:1] != "0" else "1") + h[1:]


ACUTE = chr(233)               # a letter outside ASCII, written as a number so that this file stays ASCII
NONCE_BYTES = getattr(L, "TICKET_NONCE_BYTES", 8)
ORDER_A, ORDER_B = "261013-a1b2c3d4e5f60718", "261013-0f1e2d3c4b5a6978"
PROBE = "a1b2c3d4e5f6"
KINDS = ["work", "unlock", store.unlock_kind(ORDER_A), store.unlock_kind(ORDER_B), M.KIND + ORDER_A, M.KIND + ORDER_B, M.PROBE_KIND + PROBE, "admin-v1"]
T0 = int(time.time())

# ============================================================================================ 1. the form
section("1. the form of a minted ticket")
with frozen(T0 + 0.25):
    t = L.mint_ticket("work")
    t_unlock60 = L.mint_ticket("unlock", 60)
    t_longest = L.mint_ticket(store.unlock_kind("a" * 64), 900)
f = fields(t)
check("a minted ticket has four fields: kind, expiry, nonce, signature", len(t.split(".")) == 4 and f[0] == "work", t)
check("the expiry is the second of minting plus the ttl: 900 by default (TICKET_TTL), 60 when asked", f[1] == str(T0 + 900) and L.TICKET_TTL == 900
      and fields(t_unlock60)[1] == str(T0 + 60) and fields(t_unlock60)[0] == "unlock", (t, t_unlock60))
check("the nonce is 16 lowercase hex characters (8 random bytes) and the signature 32", len(t.split(".")) == 4 and NONCE_BYTES == 8 and re.fullmatch(r"[0-9a-f]{16}", f[2])
      and re.fullmatch(r"[0-9a-f]{32}", f[3]), t)
check("the signature is the HMAC-SHA256 of 'kind.expiry.nonce' under the ticket secret (32 hex): the nonce is signed together with the kind and the expiry",
      len(t.split(".")) == 4 and f[3] == sig_of(".".join(f[:3])) and f[3] != sig_of(".".join(f[:2])), t)
check("only letters, digits, '.' and '-' (the character classes the pages already send): the same text in JSON and in a link",
      re.fullmatch(r"[A-Za-z0-9.-]+", t) and json.dumps(t) == '"' + t + '"' and json.loads(json.dumps({"ticket": t}))["ticket"] == t
      and urllib.parse.quote(t, safe="") == t, t)
check("the longest ticket there is (unlock-<64 character order id>) stays under 160 characters", len(t_longest) < 160 and len(t_longest.split(".")) == 4, len(t_longest))

# ============================================================================================ 2. two tickets of one second
section("2. two tickets minted in the same second differ")
with frozen(T0 + 0.5):
    same = [L.mint_ticket("work") for _ in range(500)]
    unl = [L.mint_ticket(store.unlock_kind(ORDER_A), 300) for _ in range(100)]
    adv = [L.mint_ticket(M.KIND + ORDER_A, M.TICKET_TTL) for _ in range(100)]
check("500 work tickets minted in one second: 500 different strings, one and the same expiry", len(set(same)) == 500 and len({x.split(".")[1] for x in same}) == 1, len(set(same)))
check("100 unlock tickets of one order and 100 internal advance tickets of one order, each in one second: all different", len(set(unl)) == 100 and len(set(adv)) == 100
      and len({x.split(".")[1] for x in unl}) == 1 and len({x.split(".")[1] for x in adv}) == 1, (len(set(unl)), len(set(adv))))
got = []


def worker():
    got.extend(L.mint_ticket("work") for _ in range(50))


ths = [threading.Thread(target=worker) for _ in range(8)]
[x.start() for x in ths]
[x.join() for x in ths]
check("eight threads minting 50 each on the real clock: 400 different tickets", len(got) == 400 and len(set(got)) == 400, len(set(got)))
hex_calls = []
real_hex = secrets.token_hex
with mock.patch.object(secrets, "token_hex", lambda n=None: hex_calls.append(n) or real_hex(n)):
    L.mint_ticket("work")
check("the nonce is made by secrets.token_hex(TICKET_NONCE_BYTES), once per ticket", hex_calls == [NONCE_BYTES], hex_calls)
with frozen(T0 + 0.5), mock.patch.object(secrets, "token_hex", lambda n=None: "00" * NONCE_BYTES):
    fixed = [L.mint_ticket("work"), L.mint_ticket("work")]
check("with the nonce held fixed, two tickets of one second are the same string again: the nonce alone is what keeps them apart", fixed[0] == fixed[1], fixed)

# ============================================================================================ 3. both forms are good
section("3. check_ticket takes the four-field form and the three-field form of before, by the same rules")
new_tickets = {k: L.mint_ticket(k) for k in KINDS}
old_tickets = {k: legacy(k) for k in KINDS}
check("every kind of ticket in use is accepted in the new form, for its own kind", all(L.check_ticket(new_tickets[k], kind=k) for k in KINDS), [k for k in KINDS if not L.check_ticket(new_tickets[k], kind=k)])
check("... and in the old three-field form (a ticket minted before the deploy, a self-call in flight)", all(L.check_ticket(old_tickets[k], kind=k) for k in KINDS), [k for k in KINDS if not L.check_ticket(old_tickets[k], kind=k)])
check("the default kind is 'work' for both forms", L.check_ticket(new_tickets["work"]) and L.check_ticket(old_tickets["work"]) and not L.check_ticket(new_tickets["unlock"]) and not L.check_ticket(old_tickets["unlock"]))
with frozen(T0 + 0.1):
    tn, to = L.mint_ticket("work", 900), legacy("work", 900, now=T0)
EXP = T0 + 900
with frozen(float(EXP)):
    at_end = (L.check_ticket(tn), L.check_ticket(to))
with frozen(EXP + 0.001):
    after_end = (L.check_ticket(tn), L.check_ticket(to))
with frozen(EXP - 899.0):
    early = (L.check_ticket(tn), L.check_ticket(to))
check("expiry, both forms: good up to and including the last second (now == expiry), refused a moment after", at_end == (True, True) and after_end == (False, False) and early == (True, True),
      (at_end, after_end, early))
check("a ticket minted with a negative ttl is expired at once, in both forms", not L.check_ticket(L.mint_ticket("work", -5)) and not L.check_ticket(legacy("work", -5)) and not L.check_ticket(L.mint_ticket("work", -1)))
cmp_seen = []
real_cmp = hmac.compare_digest
with mock.patch.object(hmac, "compare_digest", lambda a, b: cmp_seen.append((a, b)) or real_cmp(a, b)):
    ok_new, ok_old = L.check_ticket(new_tickets["work"]), L.check_ticket(old_tickets["work"])
sig_new, sig_old = fields(new_tickets["work"])[3], fields(old_tickets["work"])[2]
check("the signature is compared with hmac.compare_digest (constant time) in both forms, once each, against the signature recomputed from the fields before it",
      ok_new and ok_old and cmp_seen == [(sig_new, sig_new), (sig_old, sig_old)], cmp_seen)

# ============================================================================================ 4. tampering
section("4. a tampered nonce, kind, expiry or signature is refused")
tk = L.mint_ticket("work")
k_, e_, n_, s_ = fields(tk)
tk_other = L.mint_ticket("work")
variants = {
    "the signature's last digit changed": (".".join([k_, e_, n_, flip_last(s_)]), "work"),
    "the signature's first digit changed": (".".join([k_, e_, n_, flip_first(s_)]), "work"),
    "the signature cut by one character": (".".join([k_, e_, n_, s_[:-1]]), "work"),
    "the signature one character longer": (".".join([k_, e_, n_, s_ + "0"]), "work"),
    "no signature": (".".join([k_, e_, n_, ""]), "work"),
    "the signature in capitals": (".".join([k_, e_, n_, s_.upper()]), "work"),
    "the signature of another ticket of the same kind and second": (".".join([k_, e_, n_, fields(tk_other)[3]]), "work"),
    "the nonce's last digit changed": (".".join([k_, e_, flip_last(n_), s_]), "work"),
    "the nonce's first digit changed": (".".join([k_, e_, flip_first(n_), s_]), "work"),
    "the nonce swapped for another well formed one": (".".join([k_, e_, "0123456789abcdef" if n_ != "0123456789abcdef" else "fedcba9876543210", s_]), "work"),
    "the nonce of another ticket (this one's signature kept)": (".".join([k_, e_, fields(tk_other)[2], s_]), "work"),
    "the nonce cut by one character": (".".join([k_, e_, n_[:-1], s_]), "work"),
    "the nonce one character longer": (".".join([k_, e_, n_ + "0", s_]), "work"),
    "the nonce empty": (".".join([k_, e_, "", s_]), "work"),
    "the nonce in capitals": (".".join([k_, e_, n_.upper(), s_]), "work"),
    "the nonce not hex": (".".join([k_, e_, "zzzzzzzzzzzzzzzz", s_]), "work"),
    "the expiry one second later": (".".join([k_, str(int(e_) + 1), n_, s_]), "work"),
    "the expiry one second earlier": (".".join([k_, str(int(e_) - 1), n_, s_]), "work"),
    "the expiry an hour later (a longer life)": (".".join([k_, str(int(e_) + 3600), n_, s_]), "work"),
    "the expiry written with a plus sign": (".".join([k_, "+" + e_, n_, s_]), "work"),
    "the expiry written with a leading zero": (".".join([k_, "0" + e_, n_, s_]), "work"),
    "the expiry with a space after it": (".".join([k_, e_ + " ", n_, s_]), "work"),
    "the expiry not a number": (".".join([k_, "soon", n_, s_]), "work"),
    "the kind changed to unlock (the rest kept)": (".".join(["unlock", e_, n_, s_]), "unlock"),
    "the kind changed to the unlock of an order (the rest kept)": (".".join([store.unlock_kind(ORDER_A), e_, n_, s_]), store.unlock_kind(ORDER_A)),
    "the kind in capitals": (".".join(["WORK", e_, n_, s_]), "WORK"),
    "the nonce dropped (kind.expiry.signature of a new ticket)": (".".join([k_, e_, s_]), "work"),
    "a fifth field": (tk + ".0", "work"),
    "a leading dot": ("." + tk, "work"),
    "a trailing dot": (tk + ".", "work"),
    "a space before": (" " + tk, "work"),
    "a newline after": (tk + "\n", "work"),
}
variants = {n: v for n, v in variants.items() if v[0] != tk}          # (a change that happens to leave the text as it was is no change)
bad = [n for n, (v, kind) in variants.items() if L.check_ticket(v, kind=kind)]
check(f"a new ticket altered in any of {len(variants)} ways (signature, nonce, expiry, kind, shape) is refused every time", not bad and len(variants) >= 30, bad)
ol = legacy("work")
ko, eo, so = ol.split(".")
NONCE_X = "0123456789abcdef"
old_variants = {
    "the signature's last digit changed": (".".join([ko, eo, flip_last(so)]), "work"),
    "the signature cut by one character": (".".join([ko, eo, so[:-1]]), "work"),
    "the expiry one second later": (".".join([ko, str(int(eo) + 1), so]), "work"),
    "the expiry an hour later": (".".join([ko, str(int(eo) + 3600), so]), "work"),
    "the kind changed to unlock": (".".join(["unlock", eo, so]), "unlock"),
    "a nonce added, the old signature kept": (".".join([ko, eo, NONCE_X, so]), "work"),
}
bad_old = [n for n, (v, kind) in old_variants.items() if L.check_ticket(v, kind=kind)]
check(f"an old-form ticket altered in any of {len(old_variants)} ways, a nonce added to it included, is refused every time", not bad_old, bad_old)


def four(nonce):
    """A four-field ticket made by hand with the right signature (the HMAC of 'kind.expiry.nonce' under the secret) and any nonce."""
    return ".".join([ko, eo, nonce, sig_of(ko + "." + eo + "." + nonce)])


good_nonces = {"one character": "a", "8 characters": "0123abcd", "16 characters": NONCE_X, "capitals": "0123ABCDEF", "64 characters": NONCE_X * 4}
check("the control: a four-field ticket whose signature is the HMAC of 'kind.expiry.nonce' under the secret IS good, with a hex nonce of any width from 1 to 64 characters, so the refusals above are about the signature, not the shape",
      all(L.check_ticket(four(n), kind="work") for n in good_nonces.values()), [w for w, n in good_nonces.items() if not L.check_ticket(four(n), kind="work")])
bad_nonces = {"empty": "", "65 characters": "0" * 65, "not hex": "zz11", "with a space": "ab cd", "with a dash": "ab-cd", "with a newline": "abcd" + chr(10), "non-ASCII": ACUTE * 4}
check("... and a correct signature does not make a ticket of a nonce that is empty, longer than 64 characters or not hex (the nonce is hex, nothing else)",
      not [w for w, n in bad_nonces.items() if L.check_ticket(four(n), kind="work")], [w for w, n in bad_nonces.items() if L.check_ticket(four(n), kind="work")])
os.environ["SNAPEYES_TICKET_SECRET"] = "another-secret-entirely-0123456789"
try:
    other_secret = (L.check_ticket(new_tickets["work"]), L.check_ticket(old_tickets["work"]), L.check_ticket(L.mint_ticket("work")))
finally:
    os.environ["SNAPEYES_TICKET_SECRET"] = SECRET
check("a ticket minted under another ticket secret is refused in both forms (a changed secret voids every open ticket), and the right secret takes them again",
      other_secret == (False, False, True) and L.check_ticket(new_tickets["work"]) and L.check_ticket(old_tickets["work"]), other_secret)
junk = ["", None, 0, 1791904441, True, [], [tk], {}, {"t": tk}, b"work.1.2.3", tk.encode(), "work", "work.", ".", "..", "...", "....", ".....", "work.1", "work.1.", "work..", "work.x.y",
        "work.1.2.3.4.5", "work." + e_ + "." + n_, "work." + e_ + "." + n_ + ".", ACUTE * 2 + ".1.2.3", tk.replace(".", ","), tk.replace(".", "..")]
junk_bad = []
for j in junk:
    err = raised(lambda j=j: L.check_ticket(j))
    if err is not None or L.check_ticket(j) is not False:
        junk_bad.append((j, err))
check("junk is no ticket and never raises: empty, None, numbers, lists, dicts, bytes, one to five dots, a missing or doubled field, a non-ASCII kind", not junk_bad, junk_bad)
nonascii = [".".join([k_, e_, n_, ACUTE * 32]), ".".join([ko, eo, ACUTE * 32])]
check("a signature with a non-ASCII character is refused, not raised on (compare_digest takes ASCII only)", all(raised(lambda x=x: L.check_ticket(x)) is None and L.check_ticket(x) is False for x in nonascii))

# ============================================================================================ 5. the kinds
section("5. a ticket opens its own kind and no other")
wrong = []
for form, mk in (("new", L.mint_ticket), ("old", legacy)):
    for ki in KINDS:
        tki = mk(ki)
        for kj in KINDS:
            if L.check_ticket(tki, kind=kj) != (ki == kj):
                wrong.append((form, ki, kj))
check(f"the {len(KINDS)} x {len(KINDS)} matrix of kinds, both forms: work, unlock, two orders' unlock, two orders' advance, a probe, admin-v1; each opens itself only", not wrong and len(KINDS) == 8, wrong[:6])
check("a work ticket opens no order's paid endpoints and no self-call; an order's unlock ticket opens no other order and no self-call; an advance ticket opens no unlock",
      not L.check_ticket(new_tickets["work"], kind=store.unlock_kind(ORDER_A)) and not L.check_ticket(new_tickets[store.unlock_kind(ORDER_A)], kind=store.unlock_kind(ORDER_B))
      and not L.check_ticket(new_tickets[store.unlock_kind(ORDER_A)], kind=M.KIND + ORDER_A) and not L.check_ticket(new_tickets[M.KIND + ORDER_A], kind=store.unlock_kind(ORDER_A))
      and not L.check_ticket(new_tickets[M.KIND + ORDER_A], kind="work") and not L.check_ticket(new_tickets["unlock"], kind=store.unlock_kind(ORDER_A)))
dotted = ("a.b", "a.b.c", "selfcall-probe-../x")
check("a kind with a dot can never be validated (the fields would shift), in either form, even for its own kind",
      not [d for d in dotted if L.check_ticket(L.mint_ticket(d), kind=d) or L.check_ticket(legacy(d), kind=d)])
check("an order id cannot bring a dot into a kind: store.unlock_kind refuses it (and the order id pattern has no dot)",
      isinstance(raised(lambda: store.unlock_kind("261013.a1b2c3d4e5f60718")), L.ClientError) and not store.ORDER_RE.fullmatch("261013.a1b2c3d4e5f60718"))

# ============================================================================================ 6. the places that touch tickets
section("6. the places that touch tickets agree with the new form")
with frozen(T0 + 0.5):
    ta, tb = L.mint_ticket("work"), L.mint_ticket("work")
pa, pb = pay.ticket_path(ta), pay.ticket_path(tb)
ma = re.fullmatch(r"ticketuse/([0-9]{6})/([0-9a-f]{32})\.json", pa)
check("pay.ticket_path: ticketuse/<day of the expiry>/<32 hex of the whole ticket>; the same ticket the same marker, two tickets of one second two markers",
      bool(ma) and ma.group(1) == pay.day(T0 + 900) and ma.group(2) == hashlib.sha256(ta.encode()).hexdigest()[:32] and pay.ticket_path(ta) == pa and pa != pb, (pa, pb))
lo = legacy("work")
check("... the old form keeps the marker it always had (day of field 2, hash of the whole string); a string that is no ticket falls back to today's folder and does not raise",
      pay.ticket_path(lo) == f"ticketuse/{pay.day(int(lo.split('.')[1]))}/{hashlib.sha256(lo.encode()).hexdigest()[:32]}.json"
      and raised(lambda: pay.ticket_path("junk")) is None and pay.ticket_path("junk").startswith(f"ticketuse/{pay.day()}/") and pay.ticket_path(None).startswith(f"ticketuse/{pay.day()}/"))
check("maker.ticket_ok: the self-call's internal ticket of an order opens that order only, in both forms (a chain in flight at the deploy)",
      M.ticket_ok(ORDER_A, L.mint_ticket(M.KIND + ORDER_A, M.TICKET_TTL)) and not M.ticket_ok(ORDER_B, L.mint_ticket(M.KIND + ORDER_A, M.TICKET_TTL))
      and M.ticket_ok(ORDER_A, legacy(M.KIND + ORDER_A, M.TICKET_TTL)) and not M.ticket_ok(ORDER_B, legacy(M.KIND + ORDER_A, M.TICKET_TTL))
      and not M.ticket_ok(ORDER_A, L.mint_ticket(store.unlock_kind(ORDER_A), 300)))
sent = []
saved_base = os.environ.get("SNAPEYES_SELF_BASE")
os.environ["SNAPEYES_SELF_BASE"] = "http://127.0.0.1:9"
try:
    with frozen(T0 + 0.5), mock.patch.object(M, "_post", lambda body: (sent.append(dict(body)), ("sent", None))[1]):
        M._KICKED.clear()
        r1 = M.kick(ORDER_A, hop=0, why="unit")
        M._KICKED.clear()
        r2 = M.kick(ORDER_A, hop=1, why="unit")
finally:
    if saved_base is None:
        os.environ.pop("SNAPEYES_SELF_BASE", None)
    else:
        os.environ["SNAPEYES_SELF_BASE"] = saved_base
check("maker.kick, the server's own self-call, mints its internal ticket in the new form; two kicks of one order in one second carry two different tickets, both accepted by ticket_ok",
      r1 == r2 == "sent" and len(sent) == 2 and sent[0]["ticket"] != sent[1]["ticket"] and all(len(b["ticket"].split(".")) == 4 and M.ticket_ok(ORDER_A, b["ticket"]) for b in sent), (r1, r2, sent))
with frozen(T0 + 0.5):
    lab1, lab2 = ops.act_lab_start({}, {}), ops.act_lab_start({}, {})
check("the admin lab (ops.act_lab_start): its unlock ticket is in the new form, opens its own test order only, and two lab starts in one second differ",
      lab1["ticket"] != lab2["ticket"] and lab1["order"] != lab2["order"] and len(lab1["ticket"].split(".")) == 4 and L.check_ticket(lab1["ticket"], kind=store.unlock_kind(lab1["order"]))
      and not L.check_ticket(lab1["ticket"], kind=store.unlock_kind(lab2["order"])) and not L.check_ticket(lab1["ticket"], kind="work"), (lab1, lab2))
spec_mu = importlib.util.spec_from_file_location("mint_unlock", os.path.join(REPO, "scripts", "mint_unlock.py"))
MU = importlib.util.module_from_spec(spec_mu)
spec_mu.loader.exec_module(MU)


def run_mu(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = MU.main(list(argv))
    return code, out.getvalue().strip(), err.getvalue()


c_mint, minted, _ = run_mu("--order", "test-0001", "--ttl", "600")
c_ok_new, _, _ = run_mu("--order", "test-0001", "--check", minted)
c_ok_old, _, _ = run_mu("--order", "test-0001", "--check", legacy(store.unlock_kind("test-0001"), 600))
c_bad, _, _ = run_mu("--order", "test-0001", "--check", flip_last(minted))
c_wrong, _, _ = run_mu("--order", "test-0002", "--check", minted)
c_prev, minted_prev, _ = run_mu("--preview")
check("scripts/mint_unlock.py prints a four-field ticket of the order's unlock kind; --check takes it and the old three-field form, and refuses a changed one and another order's",
      c_mint == 0 and len(minted.split(".")) == 4 and minted.split(".")[0] == store.unlock_kind("test-0001") and (c_ok_new, c_ok_old, c_bad, c_wrong) == (0, 0, 1, 1)
      and c_prev == 0 and minted_prev.split(".")[0] == "unlock", (c_mint, minted, c_ok_new, c_ok_old, c_bad, c_wrong))
saved_admin = os.environ.get("SNAPEYES_ADMIN_SECRET")
os.environ["SNAPEYES_ADMIN_SECRET"] = "admin-secret-of-the-nonce-suite-0123456789"
try:
    admin_key = ops.mint_admin_key(3600)
    admin_ok = ops.check_admin_key(admin_key)
    as_ticket = L.check_ticket(admin_key, kind=ops.admin_kind())
    as_admin = [ops.check_admin_key(x) for x in (L.mint_ticket(ops.admin_kind(), 3600), legacy(ops.admin_kind(), 3600), L.mint_ticket("work", 900), legacy("work", 900))]
finally:
    if saved_admin is None:
        os.environ.pop("SNAPEYES_ADMIN_SECRET", None)
    else:
        os.environ["SNAPEYES_ADMIN_SECRET"] = saved_admin
check("an admin key is no ticket of its kind, and no ticket (new or old form, of the admin kind or any other) is an admin key: the two schemes stay apart",
      admin_ok is True and as_ticket is False and as_admin == [False] * 4, (admin_ok, as_ticket, as_admin))

# ============================================================================================ 7. end to end
section("7. end to end: two analyses in one second, two different unpaid orders")
im = Image.open(os.path.join(REPO, "public", "assets", "sample_eye_blue_1789706902835.jpg")).convert("RGB")
buf = io.BytesIO()
im.save(buf, "JPEG", quality=90)
PHOTO = base64.b64encode(buf.getvalue()).decode()
real_json, real_gem, real_img = L.gemini_json, L.gemini, L.gemini_image
L.gemini_json = lambda model, prompt, img: {"found": True, "iris_box": [226, 225, 786, 785], "pupil_box": [425, 424, 587, 586],
                                            "glare_boxes": [], "sharpness": "sharp", "iris_occluded_by_eyelids_percent": 2}
L.gemini = L.gemini_image = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no model call in this suite"))
JSON = {"Content-Type": "application/json"}


def post(path, body):
    r = requests.post(BASE + path, data=json.dumps(body), headers=JSON, timeout=300)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}


def analyze():
    return post("/api/analyze", {"image": PHOTO, "origWidth": 1024, "origHeight": 1024, "lang": "en"})


def jpeg(seed):
    return H.jpeg_b64(256, seed)


def draft(ticket, seed, **extra):
    return post("/api/order", dict({"action": "draft", "eye": 1, "crop": jpeg(seed), "preview": jpeg(seed + 100), "pad": 1.12, "ticket": ticket, "lang": "en", "ref": "e1"}, **extra))


def orders_on_disk():
    root = os.path.join(STORE, "orders")
    return sorted(os.listdir(root)) if os.path.isdir(root) else []


def markers():
    return [os.path.join(r, x) for r, _, fs in os.walk(os.path.join(STORE, "ticketuse")) for x in fs]


def exists(order, name):
    return os.path.isfile(os.path.join(STORE, "orders", order, name))


def draft_record(order, eye=1):
    with open(os.path.join(STORE, "orders", order, "draft", f"eye_{eye}.json"), encoding="utf-8") as fh:
        return json.load(fh)


with frozen(time.time()):                 # both analyses end in one and the same second, however long each takes
    (c1, a1), (c2, a2) = analyze(), analyze()
check("two analyses in the same second both answer 200 with a work ticket (the sample eye locks and passes the gate; the vision model is a stub)",
      c1 == c2 == 200 and bool(a1.get("ok")) and bool(a2.get("ok")) and bool(a1.get("ticket")) and bool(a2.get("ticket")), (c1, c2, str(a1)[:200], str(a2)[:200]))
tk1, tk2 = a1.get("ticket") or "", a2.get("ticket") or ""
check("... their tickets expire in the same second and are two different tickets", bool(tk1) and tk1.split(".")[1:2] == tk2.split(".")[1:2] and tk1 != tk2, (tk1, tk2))
n_before = len(orders_on_disk())
(d1c, d1), (d2c, d2) = draft(tk1, 1), draft(tk2, 2)
check("both customers draft their eye with their own ticket: 200 for both, and each draft CREATED an order", d1c == d2c == 200 and d1.get("created") is True and d2.get("created") is True, (d1c, d1, d2c, d2))
oa, ob, ka, kb = d1.get("order"), d2.get("order"), d1.get("k"), d2.get("k")
check("two different orders and two different access keys", bool(oa) and bool(ob) and oa != ob and bool(ka) and bool(kb) and ka != kb and len(orders_on_disk()) == n_before + 2, (oa, ob, ka, kb))
check("both orders are unpaid and open (order.json, no paid.json, no withdrawn.json)", all(exists(o, "order.json") and not exists(o, "paid.json") and not exists(o, "withdrawn.json") for o in (oa, ob)), (oa, ob))
mk = markers()
named = []
for p in mk:
    try:
        with open(p, encoding="utf-8") as fh:
            named.append(json.load(fh).get("order"))
    except (OSError, ValueError):
        named.append(None)
check("two ticket markers, one per ticket (named by the hash of the whole ticket), each naming its own order", len(mk) == 2 and sorted(x for x in named if x) == sorted([oa, ob])
      and {os.path.basename(pay.ticket_path(tk1)), os.path.basename(pay.ticket_path(tk2))} == {os.path.basename(p) for p in mk}, (mk, named))
sha = lambda seed: hashlib.sha256(base64.b64decode(jpeg(seed))).hexdigest()      # noqa: E731
try:
    ra, rb = draft_record(oa), draft_record(ob)
    own = (ra["crop"]["sha256"], rb["crop"]["sha256"], ra["preview"]["sha256"], rb["preview"]["sha256"]) == (sha(1), sha(2), sha(101), sha(102))
    files_a, files_b = sorted(os.listdir(os.path.join(STORE, "orders", oa, "draft"))), sorted(os.listdir(os.path.join(STORE, "orders", ob, "draft")))
except Exception as exc:  # noqa: BLE001
    own, files_a, files_b = repr(exc), [], []
check("each customer's eye is in their own order, not overwritten by the other's: the stored crop and preview of each are the bytes that customer sent", own is True and len(files_a) == 3 and len(files_b) == 3, (own, files_a, files_b))
refuse = [raised(lambda: pay.load_order(oa, kb)), raised(lambda: pay.load_order(ob, ka))]
check("neither access key opens the other customer's order (a 403 bad_link), each opens its own",
      all(isinstance(x, store.Answer) and x.status == 403 for x in refuse) and raised(lambda: pay.load_order(oa, ka)) is None and raised(lambda: pay.load_order(ob, kb)) is None, refuse)
(d3c, d3) = draft(tk1, 1)
check("a repeat with the first ticket (a lost reply) gets the first customer's order and key back, creates nothing, and leaves the second order alone",
      d3c == 200 and d3.get("order") == oa and d3.get("k") == ka and d3.get("created") is False and len(orders_on_disk()) == n_before + 2 and draft_record(ob)["crop"]["sha256"] == sha(2), (d3c, d3))
(d4c, d4) = draft(tk2, 2, order=ob, k=kb, eye=2)
check("the second customer's next eye goes into their own order with their own key", d4c == 200 and d4.get("order") == ob and exists(ob, "draft/eye_2.json") and not exists(oa, "draft/eye_2.json"), (d4c, d4))
old_t = legacy("work")
(d5c, d5), (d6c, d6) = draft(old_t, 5), draft(old_t, 5)
check("a ticket of the old three-field form (minted just before the deploy) still makes an order: 200, created, and the same ticket again gets that order back",
      d5c == 200 and d5.get("created") is True and d5.get("order") not in (oa, ob) and d6c == 200 and d6.get("created") is False and d6.get("order") == d5.get("order"), (d5c, d5, d6c, d6))
n_now = len(orders_on_disk())
p1 = fields(tk1)
bads = {"a nonce changed": ".".join([p1[0], p1[1], flip_last(p1[2]), p1[3]]), "an expiry extended": ".".join([p1[0], str(int(p1[1]) + 3600), p1[2], p1[3]]),
        "a signature changed": flip_last(tk1), "the nonce dropped": ".".join([p1[0], p1[1], p1[3]]), "expired (new form)": L.mint_ticket("work", -5),
        "expired (old form)": legacy("work", -5), "another kind": L.mint_ticket("unlock"), "no ticket": None}
codes = {n: draft(v, 7)[0] for n, v in bads.items()}
check("a changed, extended, truncated, expired, wrong-kind or missing ticket makes no order: 403 each time, nothing stored", all(c == 403 for c in codes.values()) and len(orders_on_disk()) == n_now, (codes, len(orders_on_disk()), n_now))
gates = {}
for path in ("/api/deglare", "/api/enhance"):
    gates[path] = {"new": post(path, {"ticket": L.mint_ticket("work")})[0], "old": post(path, {"ticket": legacy("work")})[0],
                   "changed": post(path, {"ticket": flip_last(L.mint_ticket("work"))})[0], "expired": post(path, {"ticket": L.mint_ticket("work", -5)})[0],
                   "missing": post(path, {})[0]}
check("/api/deglare and /api/enhance gate on the ticket before they read the picture: a good ticket of either form gets past it (400, no picture sent), a changed, expired or missing one is a 403",
      all(g["new"] == 400 and g["old"] == 400 and g["changed"] == 403 and g["expired"] == 403 and g["missing"] == 403 for g in gates.values()), gates)
tickets_par, codes_par = [], []


def par_analyze():
    c, a = analyze()
    codes_par.append(c)
    tickets_par.append(a.get("ticket"))


ths = [threading.Thread(target=par_analyze) for _ in range(4)]
[x.start() for x in ths]
[x.join() for x in ths]
orders_par = [draft(tk, 20 + i)[1].get("order") for i, tk in enumerate(tickets_par) if tk]
check("four analyses at once on the real clock: four 200s, four different tickets, and four drafts make four different orders", codes_par == [200] * 4 and len(set(tickets_par)) == 4 and None not in tickets_par
      and len(orders_par) == 4 and len(set(orders_par)) == 4 and not set(orders_par) & {oa, ob, d5.get("order")}, (codes_par, tickets_par, orders_par))
L.gemini_json, L.gemini, L.gemini_image = real_json, real_gem, real_img

ok = sum(RESULTS)
print(f"\n{ok} of {len(RESULTS)} passed")
sys.exit(0 if ok == len(RESULTS) else 1)
