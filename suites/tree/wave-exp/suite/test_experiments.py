# -*- coding: utf-8 -*-
"""Price experiments (api/_lib/experiments.py, api/_lib/abtest.py and their hooks in checkout, pay, events, ops, the
webhook, the emails; scripts/check_experiments.mjs; the page code src/shared/pricing.ts): default off, sticky and signed
assignment, tampered tokens, price shown = charged = recorded for every variant, market, eye count and style, the
refusal of other amounts, old orders, events per variant, the admin actions and page data, the significance note and
the loss warning, the build check (also against broken definitions), the privacy and terms sentences.
Fake Stripe + Resend + legal pack, real handlers over HTTP, a local store folder. No real key.
    python test_experiments.py [filter]        prints PASS/FAIL per check; exits 1 on any failure"""
import os, sys, io, re, json, math, time, base64, shutil, hashlib, secrets, subprocess, random, importlib.util
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.environ.get("SNAPEYES_SP") or os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(SP, "wave-pv", "tests"))
import harness as H

REPO = H.REPO
STORE = os.path.join(HERE, "store_exp")
ADMIN_SECRET = "exp-admin-secret-for-tests-0123456789abcdef"
CRON = "cron-test-secret-0123456789"
ONLY = sys.argv[1] if len(sys.argv) > 1 else ""

stub = H.start_stub()
H.setup_env(STORE, stub.server_address[1])
os.environ.update({"SNAPEYES_ADMIN_SECRET": ADMIN_SECRET, "CRON_SECRET": CRON})
api = H.start_api()
BASE = f"http://127.0.0.1:{api.server_address[1]}"

import requests
sys.path.insert(0, H.API)
from _lib import iris as L
from _lib import store, pay, events as E, ops, abtest as A, experiments as X, markets as MK

_spec = importlib.util.spec_from_file_location("admin", os.path.join(H.API, "admin.py"))
_adm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_adm)
H.MODS["admin"] = _adm
E.RATE = {"all": (10_000_000, 60.0), "error": (30, 60.0), "exp": (10_000_000, 60.0)}     # the tests write far more events than a minute of visitors
E.EXP_DAY_MAX = 10 ** 9

RESULTS = []
DEFS = json.loads(json.dumps(X.EXPERIMENTS))
KEYS = list(DEFS)
KEY = "extra_eye_eur"
BASE_LADDER = {m: MK.MARKETS[m]["prices"] for m in MK.MARKETS}


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"   <- {str(detail)[:600]}"), flush=True)


def section(t):
    print(f"\n== {t}", flush=True)


def post(path, body, headers=None):
    h = {"Content-Type": "application/json"}
    h.update(headers or {})
    r = requests.post(BASE + path, data=json.dumps(body), headers=h, timeout=60)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}


def get(path):
    r = requests.get(BASE + path, timeout=60)
    return r.status_code, r.json()


def local(path):
    return os.path.join(STORE, *path.split("/"))


def read_json(path):
    with open(local(path), encoding="utf-8") as f:
        return json.load(f)


def exists(path):
    return os.path.exists(local(path))


def hook(body, sig):
    h = {"Content-Type": "application/json; charset=utf-8"}
    if sig is not None:
        h["Stripe-Signature"] = sig
    r = requests.post(BASE + "/api/stripe_webhook", data=body, headers=h, timeout=60)
    return r.status_code, r.json()


# ------------------------------------------------------------------ helpers of the flows
WORK = L.mint_ticket("work")
CROP = H.jpeg_b64(256, 1)
PREV = H.jpeg_b64(512, 2)


def draft(eye, order=None, k=None):
    ticket = H.fresh_ticket() if order is None else WORK
    b = {"action": "draft", "eye": eye, "crop": CROP, "preview": PREV, "pad": 1.12, "ticket": ticket, "lang": "en", "ref": f"eye-{eye}"}
    if order:
        b["order"], b["k"] = order, k
    return post("/api/order", b)


def new_order(eyes=8):
    c, j = draft(1)
    assert c == 200, (c, j)
    o, k = j["order"], j["k"]
    for i in range(2, eyes + 1):
        c2, j2 = draft(i, o, k)
        assert c2 == 200, (c2, j2)
    return o, k


def checkout(o, k, eyes, style="studio_black", market="eu", lang="en", **kw):
    b = {"order": o, "k": k, "eyes": eyes, "style": style, "names": "", "title": "", "lang": lang, "market": market,
         "consent_digital": True}
    b.update(kw)
    return post("/api/checkout", b)


def info(vid=None):
    """GET /api/checkout; the visitor id, when given, in the header X-Snapeyes-Visitor (never in the address)."""
    h = {"X-Snapeyes-Visitor": vid} if vid is not None else {}
    r = requests.get(BASE + "/api/checkout", headers=h, timeout=60)
    return r.status_code, r.json()


def ladder_price(l, eyes, style):
    """An independent restatement of the rule (one eye by its style, two eyes, then a further eye each)."""
    if eyes == 1:
        return l["one_eye_studio_black"] if style == "studio_black" else l["one_eye_art"]
    return l["two_eyes"] + (eyes - 2) * l["each_further_eye"]


def vid_for(key, variant, n=0):
    """A visitor id the server assigns to this variant (found by asking the very function the server uses)."""
    r = random.Random(f"{key}/{variant}/{n}")
    while True:
        v = "%032x" % r.getrandbits(128)
        if A.assign(v, key) == variant:
            return v


def adm_key():
    return ops.mint_admin_key(3600)


def adm(action, auth=None, **body):
    h = {"Content-Type": "application/json"}
    if auth is not False:
        h["Authorization"] = "Bearer " + (auth or adm_key())
    r = requests.post(BASE + "/api/admin", data=json.dumps(dict(body, action=action)), headers=h, timeout=90)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}


def pay_session(sid, live=True):
    s = H.pay_session(sid)
    s["livemode"] = bool(live)
    body, sig = H.signed_event(s)
    return hook(body, sig)


def owner_notes():
    return [m for m, _ in H.Fake.emails if m.get("to") == ["info@snapeyes.com"]]


def start(key):
    c, j = adm("exp_start", **{"key": key})
    return c, j


def variants_of(key):
    return list(DEFS[key]["variants"])


def want_ladder(key, variant, market):
    return DEFS[key]["variants"][variant]["prices"][market]


def events_of(day=None):
    """Every stored event of kind exp (parsed), from the local store folder."""
    out = []
    base = local("ops/events")
    if not os.path.isdir(base):
        return out
    for d in sorted(os.listdir(base)):
        for f in sorted(os.listdir(os.path.join(base, d))):
            if not f.endswith(".json"):
                continue
            try:
                with open(os.path.join(base, d, f), encoding="utf-8") as fh:
                    ev = json.load(fh)
            except (FileNotFoundError, ValueError):
                continue
            if ev.get("kind") == "exp":
                out.append(ev)
    return out


def event_keys():
    """The names (day/file) of the stored exp events."""
    out = set()
    base = local("ops/events")
    if os.path.isdir(base):
        for d in os.listdir(base):
            for f in os.listdir(os.path.join(base, d)):
                if not f.endswith(".json"):
                    continue                    # a write in flight (the local store renames a .part file)
                try:
                    with open(os.path.join(base, d, f), encoding="utf-8") as fh:
                        if json.load(fh).get("kind") == "exp":
                            out.add(f"{d}/{f}")
                except (FileNotFoundError, ValueError):
                    pass
    return out


def events_since(before):
    out = []
    for name in sorted(event_keys() - before):
        with open(local("ops/events/" + name), encoding="utf-8") as fh:
            out.append(json.load(fh))
    return out


def view():
    c, j = adm("experiments")
    assert c == 200, (c, j)
    return {e["key"]: e for e in j["experiments"]}, j


def stat(v, key, variant):
    return next(s for s in v[key]["stats"] if s["variant"] == variant)


def run_section(name):
    return not ONLY or ONLY in name


# =================================================================== 1. definitions and the build check
section("1. definitions and the build check")
check("the definitions pass the server's own rules (abtest.validate)", A.validate() == [], A.validate())
check("every control ladder is the standard ladder of markets.py",
      all(want_ladder(k, "control", m) == BASE_LADDER[m] for k in KEYS for m in DEFS[k]["markets"]))
check("the two approved tests exist: extra eye in eu and lt, the Australian ladder",
      set(KEYS) == {"extra_eye_eur", "au_ladder_high"} and DEFS["extra_eye_eur"]["markets"] == ["eu", "lt"] and DEFS["au_ladder_high"]["markets"] == ["au"])
xe, xa = DEFS["extra_eye_eur"]["variants"], DEFS["au_ladder_high"]["variants"]
check("extra eye: +15 EUR (control) against +10 EUR, everything else equal",
      xe["control"]["prices"]["eu"]["each_further_eye"] == 1500 and xe["extra10"]["prices"]["eu"]["each_further_eye"] == 1000
      and all(xe["control"]["prices"][m][k] == xe["extra10"]["prices"][m][k] for m in ("eu", "lt") for k in ("one_eye_studio_black", "one_eye_art", "two_eyes")))
check("Australia: A$39 / 49 / 79 / +29 against A$49 / 59 / 89 / +35",
      [xa["control"]["prices"]["au"][k] for k in ("one_eye_studio_black", "one_eye_art", "two_eyes", "each_further_eye")] == [3900, 4900, 7900, 2900]
      and [xa["high"]["prices"]["au"][k] for k in ("one_eye_studio_black", "one_eye_art", "two_eyes", "each_further_eye")] == [4900, 5900, 8900, 3500])
check("every variant carries its full ladder for every market of its experiment",
      all(sorted(v["prices"]) == sorted(DEFS[k]["markets"]) and all(len(l) == 4 for l in v["prices"].values()) for k in KEYS for v in DEFS[k]["variants"].values()))
check("the split of every experiment adds up to 100", all(sum(DEFS[k]["split"].values()) == 100 for k in KEYS))
check("no loss and no wide spread in the approved ladders", all(not A.loss_report(k) and not A.spread_report(k) for k in KEYS))
for k in KEYS:
    for v in DEFS[k]["variants"].values():
        for m, l in v["prices"].items():
            for eyes in range(1, 9):
                assert ladder_price(l, eyes, "studio_black") == A.ladder_price(l, eyes, "studio_black")
                assert ladder_price(l, eyes, "celestial_gold") == A.ladder_price(l, eyes, "celestial_gold")
check("abtest.ladder_price = pay.price_cents for the standard ladders (eyes 1-8, both styles)",
      all(A.ladder_price(BASE_LADDER[m], e, s) == pay.price_cents(e, s, m) for m in MK.MARKETS for e in range(1, 9) for s in ("studio_black", "celestial_gold", "supernova")))
try:
    A.ladder_price(BASE_LADDER["eu"], 9, "studio_black")
    ok9 = False
except L.ClientError:
    ok9 = True
check("nine eyes are refused by the ladder rule", ok9)

r = subprocess.run(["node", "scripts/check_prices.mjs"], cwd=REPO, capture_output=True, text=True, encoding="utf-8")
check("the build's price check passes on the real files (with the experiments)", r.returncode == 0 and "price check ok" in r.stdout, r.stdout + r.stderr)


def build_check_on_copy(mutate):
    """Copy the files the check reads into a temp root, mutate experiments.py (or another file), run the check."""
    tmp = os.path.join(HERE, "root_tmp")
    if os.path.isdir(tmp):
        shutil.rmtree(tmp)
    for d in ("api", "src", "scripts"):
        shutil.copytree(os.path.join(REPO, d), os.path.join(tmp, d), ignore=shutil.ignore_patterns("__pycache__", "node_modules", "_assets"))
    p = os.path.join(tmp, "api", "_lib", "experiments.py")
    src = open(p, encoding="utf-8").read()
    new = mutate(src, tmp)
    if new is not None:
        open(p, "w", encoding="utf-8", newline="").write(new)
    r = subprocess.run(["node", "scripts/check_prices.mjs"], cwd=tmp, capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout + r.stderr


def append_file(root, parts, text):
    with open(os.path.join(root, *parts), "a", encoding="utf-8") as f:
        f.write(text)
    return None


NEG = [
    ("a control ladder that is not the standard one", lambda s, t: s.replace('"lt": {"one_eye_studio_black": 1997, "one_eye_art": 2497, "two_eyes": 3997, "each_further_eye": 1500}', '"lt": {"one_eye_studio_black": 1997, "one_eye_art": 2497, "two_eyes": 3997, "each_further_eye": 1400}', 1), "control ladder"),
    ("a variant without a full ladder", lambda s, t: s.replace('"eu": {"one_eye_studio_black": 1997, "one_eye_art": 2497, "two_eyes": 3997, "each_further_eye": 1000}', '"eu": {"one_eye_studio_black": 1997, "one_eye_art": 2497, "two_eyes": 3997}', 1), "FULL ladder"),
    ("a variant that sells at a loss (image work costing far more than the prices)", lambda s, t: s.replace('"unit_usd_per_eye": 0.22', '"unit_usd_per_eye": 40', 1), "would sell at a loss"),
    ("a split that does not add up", lambda s, t: s.replace('"split": {"control": 50, "extra10": 50}', '"split": {"control": 50, "extra10": 40}', 1), "split"),
    ("changes that do not match the ladders", lambda s, t: s.replace('"changes": ["each_further_eye"]', '"changes": ["two_eyes"]', 1), "changes"),
    ("identical ladders", lambda s, t: s.replace('"each_further_eye": 1000}', '"each_further_eye": 1500}'), "nothing to test"),
    ("Australian cents", lambda s, t: s.replace('"one_eye_art": 5900', '"one_eye_art": 5950', 1), "whole Australian dollars"),
    ("two eyes cheaper than one", lambda s, t: s.replace('"one_eye_art": 5900, "two_eyes": 8900', '"one_eye_art": 9900, "two_eyes": 8900', 1), "must cost more"),
    ("markets in two currencies", lambda s, t: s.replace('"markets": ["eu", "lt"]', '"markets": ["eu", "au"]', 1), "share one currency"),
    ("an unknown market", lambda s, t: s.replace('"markets": ["au"]', '"markets": ["zz"]', 1), "non-empty list of distinct markets"),
    ("an em dash in the file", lambda s, t: s.replace('"hit_label": "visi užsakymai"', '"hit_label": "visi \u2014 užsakymai"', 1), "dash"),
    ("a variant price held by another file", lambda s, t: append_file(t, ("src", "try", "checkout.ts"), "\nconst leaked = 5900;\n"), "holds the price 5900 of its own"),
    ("a written variant price in another file", lambda s, t: append_file(t, ("src", "landing", "config.ts"), "\nexport const LEAK = 'from A$59 upwards';\n"), "A$59"),
    ("a broken JSON literal", lambda s, t: s.replace('"title": "Papildomos akies kaina eurų rinkose (eu ir lt)",', '"title": "Papildomos akies kaina eurų rinkose (eu ir lt)"', 1), "cannot be read as JSON"),
]
if run_section("build"):
    for label, mut, needle in NEG:
        code, out = build_check_on_copy(mut)
        check(f"build check refuses: {label}", code == 1 and needle in out, out[-500:])
    code, out = build_check_on_copy(lambda s, t: None)
    check("build check on an untouched copy of the repo passes", code == 0, out[-400:])

# the client-agreement check with a client that ignores the ladder
node_probe = r"""
import { createRequire } from 'node:module'; import { join } from 'node:path'; import { pathToFileURL } from 'node:url';
const { checkExperiments } = await import(pathToFileURL(join(process.cwd(), 'scripts', 'check_experiments.mjs')).href);
const req = createRequire(join(process.cwd(), 'package.json'));
const { runnerImport } = await import(pathToFileURL(req.resolve('vite')).href);
const { module: M } = await runnerImport('./src/shared/markets.ts', { configFile: false, logLevel: 'silent' });
const good = []; checkExperiments(process.cwd(), M.MARKETS, good, M);
const bad = []; checkExperiments(process.cwd(), M.MARKETS, bad, { priceMinor: (n, s, m) => M.priceMinor(n, s, m) });
console.log(JSON.stringify({ good, bad: bad.length, first: bad[0] || '' }));
"""
r = subprocess.run(["node", "--input-type=module", "-e", node_probe], cwd=REPO, capture_output=True, text=True, encoding="utf-8")
try:
    pr = json.loads(r.stdout.strip().splitlines()[-1])
except Exception:
    pr = {"good": ["?"], "bad": 0, "first": r.stdout + r.stderr}
check("the client rule (priceMinor fed a ladder) agrees with the server's for every variant in the build check", pr["good"] == [], pr)
check("a client that ignores the ladder is caught by the build check", pr["bad"] > 0 and "priceMinor" in pr["first"], pr)

# =================================================================== 2. everything off by default
section("2. default off")
c, plain = info()
check("GET /api/checkout: open and the standard reply (no experiment fields)", c == 200 and plain.get("open") is True and "experiments" not in plain and "exp_token" not in plain
      and plain["prices"] == {k: BASE_LADDER["eu"][k] for k in BASE_LADDER["eu"]}, plain)
KEYS_OLD = {"ok", "open", "currency", "prices", "market", "markets", "max_eyes", "consent", "country", "suggest", "ms"}
check("the reply's fields are exactly the old ones", set(plain) == KEYS_OLD, sorted(set(plain) ^ KEYS_OLD))
vid0 = vid_for("extra_eye_eur", "extra10")
c, j = info(vid0)
check("with a visitor id but nothing running: the very same reply", c == 200 and {k: v for k, v in j.items() if k != "ms"} == {k: v for k, v in plain.items() if k != "ms"}, j)
check("every experiment is off in the admin's state", all(not s["on"] for s in A.states(force=True).values()) and not A.running_keys())
v, jv = view()
check("the admin page lists both experiments as off, with no data yet", all(not e["state"]["running"] and stat(v, k, "control")["visitors"] == 0 for k, e in v.items()), jv)
# a token from an earlier run of a test, or forged with the right key: nothing runs, so the standard price
tok_dead = A.sign({"extra_eye_eur": "extra10"})
o, k = new_order(3)
c, j = checkout(o, k, 3, exp_token=tok_dead)
p, _ = H.Fake.creates[-1]
check("a valid token while nothing runs: the standard price, no experiment anywhere", c == 200 and j["amount"] == 3997 + 1500
      and p["line_items[0][price_data][unit_amount]"] == str(3997 + 1500) and "metadata[exp]" not in p and "metadata[exp_var]" not in p
      and "experiment" not in read_json(f"orders/{o}/order.json")["checkout"], (c, j))
c, j = post("/api/checkout", {"exp_event": "visit", "exp_token": tok_dead, "market": "eu"})
check("a beacon while nothing runs is answered and not counted", c == 200 and j.get("counted") is False and not events_of(), (c, j))
c, j = adm("experiments", auth=False)
check("the experiments page data needs the admin key (no key: 403)", c == 403, (c, j))
c, j = adm("exp_start", auth=False, **{"key": "extra_eye_eur"})
check("starting without the admin key: 403, and nothing starts", c == 403 and not A.states(force=True)["extra_eye_eur"]["on"], (c, j))
c, j = adm("exp_start", auth="admin-v1.1790000000.0123456789abcdef0123456789abcdef", **{"key": "extra_eye_eur"})
check("starting with a forged admin key: 403", c == 403, (c, j))

# =================================================================== 3. start and stop from the admin page
section("3. start and stop, audit, conflicts, loss")
c, j = adm("exp_start")
check("start without a key -> 400", c == 400, (c, j))
c, j = adm("exp_start", **{"key": "no_such_test"})
check("start of an unknown experiment -> 400", c == 400, (c, j))
c, j = adm("exp_stop", **{"key": "extra_eye_eur"})
check("stop of an experiment that is not running -> 409 not_running", c == 409 and j.get("reason") == "not_running", (c, j))
c, j = adm("exp_start", **{"key": "extra_eye_eur"})
check("start extra_eye_eur -> ok, running", c == 200 and j.get("result") == "started" and j["state"]["on"] is True and A.is_running("extra_eye_eur"), (c, j))
st = read_json("ops/experiments/extra_eye_eur.json")
check("the state is one file in the private bucket (ops/experiments/<key>.json) with the run", st["on"] is True and st["runs"][-1]["stop"] is None and st["since"] and st["key"] == "extra_eye_eur", st)
check("the other experiment stays off", not A.is_running("au_ladder_high") and not exists("ops/experiments/au_ladder_high.json"))
c, j = adm("exp_start", **{"key": "extra_eye_eur"})
check("starting a running experiment -> 409 already_running", c == 409 and j.get("reason") == "already_running", (c, j))
aud = []
for d in sorted(os.listdir(local("ops/audit"))):
    for f in sorted(os.listdir(local(f"ops/audit/{d}"))):
        aud.append(read_json(f"ops/audit/{d}/{f}"))
starts = [a for a in aud if a["action"] == "exp_start"]
check("every start is in the audit log with the experiment's key, the refused one too", len(starts) >= 3
      and any(a["ok"] and a["result"] == "started" and a.get("detail") == "extra_eye_eur" for a in starts)
      and any(not a["ok"] and a["result"] == "already_running" for a in starts), starts)
check("audit lines carry no email, link or key", not re.search(r"@|https?://|admin-v", json.dumps(starts)))
# only one experiment per market: a synthetic second one on eu
saved = A.DEFS
synth = json.loads(json.dumps(DEFS))
synth["eu_second"] = json.loads(json.dumps(DEFS["extra_eye_eur"]))
synth["eu_second"]["markets"] = ["eu"]
synth["eu_second"]["variants"] = {n: {"label": v["label"], "prices": {"eu": v["prices"]["eu"]}} for n, v in synth["eu_second"]["variants"].items()}
A.DEFS = synth
A.invalidate()
c, j = adm("exp_start", **{"key": "eu_second"})
check("a second experiment in a market that already runs one -> 409 market_taken", c == 409 and j.get("reason") == "market_taken" and j.get("other") == "extra_eye_eur", (c, j))
v, jv = view()
check("the page marks it (conflict) and gives no start", v["eu_second"]["conflict"] == "extra_eye_eur", v["eu_second"])
A.DEFS = saved
A.invalidate()
# loss: a synthetic ladder far under the cost
synth = json.loads(json.dumps(DEFS))
synth["au_ladder_high"]["variants"]["high"]["prices"]["au"]["two_eyes"] = 60      # A$0.60 for two eyes: less than the image work and the fee
synth["au_ladder_high"]["changes"] = ["one_eye_studio_black", "one_eye_art", "two_eyes", "each_further_eye"]
A.DEFS = synth
A.invalidate()
v, jv = view()
wl = [w for w in v["au_ladder_high"]["warnings"] if w["code"] == "loss"]
check("a variant that would sell at a loss is warned about on the page (with the eye count and the net)", wl and all(w["net"] < 0 for w in wl) and wl[0]["variant"] == "high", v["au_ladder_high"]["warnings"])
c, j = adm("exp_start", **{"key": "au_ladder_high"})
check("start of a loss-making ladder is refused without accept_loss (409 sells_at_loss), and does not start", c == 409 and j.get("reason") == "sells_at_loss" and not A.is_running("au_ladder_high") and j.get("rows"), (c, j))
c, j = adm("exp_start", **{"key": "au_ladder_high", "accept_loss": "yes"})
check("accept_loss must be the boolean true", c == 409 and not A.is_running("au_ladder_high"), (c, j))
c, j = adm("exp_start", **{"key": "au_ladder_high", "accept_loss": True})
check("with accept_loss true it starts (the owner was warned)", c == 200 and A.is_running("au_ladder_high"), (c, j))
c, j = adm("exp_stop", **{"key": "au_ladder_high"})
check("...and stops", c == 200 and j["result"] == "stopped" and not A.is_running("au_ladder_high"), (c, j))
synth = json.loads(json.dumps(DEFS))
synth["au_ladder_high"]["variants"]["high"]["prices"]["au"] = {"one_eye_studio_black": 9900, "one_eye_art": 9900, "two_eyes": 20000, "each_further_eye": 9900}
A.DEFS = synth
A.invalidate()
v, jv = view()
sp = [w for w in v["au_ladder_high"]["warnings"] if w["code"] == "spread"]
check("ladders that differ by more than 1.5 times are flagged as a spread warning", sp and max(w["ratio"] for w in sp) > 1.5, v["au_ladder_high"]["warnings"])
A.DEFS = saved
A.invalidate()
# net calculation
check("net after fees and image work: A$39 leaves about A$36, a EUR 19.97 eye about EUR 19; a price under the cost is negative",
      3500 < A.net_minor("aud", 3900, 1) < 3700 and 1800 < A.net_minor("eur", 1997, 1) < 1950 and A.net_minor("eur", 30, 1) < 0)

# the state survives a blip of the storage, for a while
saved_get = store.get_json


def _boom(*a, **k):
    raise store.StorageError("injected")


A.states(force=True)
store.get_json = _boom
A._CACHE["t"] = 0.0
st_blip = A.states()
check("a failed read of the state keeps the last good reading (a running experiment does not flip off on a storage blip)", st_blip[KEY]["on"] is True and A.is_running(KEY), st_blip[KEY])
A._CACHE["good_t"] -= 10_000
A._CACHE["t"] = 0.0
st_long = A.states()
check("...but after minutes of failure it is off for everybody (the safe side)", all(not x["on"] for x in st_long.values()) and not A.running_keys(), st_long)
store.get_json = saved_get
A.invalidate()
check("...and the real state is read again as soon as storage answers", A.states(force=True)[KEY]["on"] is True and A.is_running(KEY))

# =================================================================== 4. assignment: sticky, signed, tamper-proof
section("4. assignment and the signed token")
KEY = "extra_eye_eur"
vids = {var: vid_for(KEY, var) for var in variants_of(KEY)}
sticky = all(A.assign(vids[var], KEY) == var for var in vids for _ in range(5))
check("assignment is sticky: the same id always gets the same variant", sticky)
c1, i1 = info(vids["extra10"])
c2, i2 = info(vids["extra10"])
check("GET twice for one id: the same variant and ladders (the token differs by nothing but time)", i1["experiments"] == i2["experiments"] and i1["prices"] == i2["prices"] and A.verify(i1["exp_token"]) == A.verify(i2["exp_token"]), (i1, i2))
check("the variant of that id is what the server derived (and the run it belongs to)", i1["experiments"] == [{"key": KEY, "variant": "extra10", "markets": ["eu", "lt"], "run": A.states()[KEY]["started_at"]}], i1.get("experiments"))
c0p, plain_run = info()
check("a request WITHOUT an id only learns which markets run a test (exp_markets), nothing else changes",
      c0p == 200 and plain_run.get("exp_markets") == ["eu", "lt"] and "experiments" not in plain_run and "exp_token" not in plain_run
      and plain_run["prices"] == BASE_LADDER["eu"] and plain_run["markets"]["lt"]["prices"] == BASE_LADDER["lt"]
      and set(plain_run) == KEYS_OLD | {"exp_markets"}, plain_run)
CAP_PLAIN_RUN = plain_run
c0q, withq = get(f"/api/checkout?v={vids['extra10']}")
check("the old ?v= form of the id is not read any more: the reply is the one without an id", c0q == 200 and withq.get("exp_markets") == ["eu", "lt"] and "exp_token" not in withq, withq)
check("its ladders are the variant's full ladders for eu and lt, the default market's 'prices' too",
      i1["markets"]["eu"]["prices"] == want_ladder(KEY, "extra10", "eu") and i1["markets"]["lt"]["prices"] == want_ladder(KEY, "extra10", "lt") and i1["prices"] == want_ladder(KEY, "extra10", "eu"), i1)
check("a market outside the experiment keeps the standard ladder", i1["markets"]["au"]["prices"] == BASE_LADDER["au"], i1["markets"]["au"])
c3, ic = info(vids["control"])
check("the control visitor gets the standard ladder, with a token all the same (so the control is counted)", ic["prices"] == BASE_LADDER["eu"] and A.verify(ic["exp_token"]) == {KEY: "control"} and ic["experiments"][0]["variant"] == "control", ic)
check("the token says the assignment and nothing else (no id, no price)", A.verify(i1["exp_token"]) == {KEY: "extra10"}
      and not re.search(vids["extra10"], base64.urlsafe_b64decode(i1["exp_token"].split(".")[1] + "==").decode()), i1["exp_token"])
# distribution
rng = random.Random(7)
counts = {"control": 0, "extra10": 0}
N = 6000
for _ in range(N):
    counts[A.assign("%032x" % rng.getrandbits(128), KEY)] += 1
check(f"the 50/50 split holds over {N} random visitors (within 3 %)", all(abs(c / N - 0.5) < 0.03 for c in counts.values()), counts)
both = [("%032x" % rng.getrandbits(128)) for _ in range(2000)]
same = sum(1 for v in both if (A.assign(v, "extra_eye_eur") == "control") == (A.assign(v, "au_ladder_high") == "control"))
check("two experiments draw independently (agreement near 50 %)", 0.44 < same / 2000 < 0.56, same / 2000)
# invalid ids take no part
for bad in ("x", "A" * 32, "g" * 32, "0" * 31, "0" * 33, "", "%20"):
    c, j = info(bad)
    check(f"an invalid visitor id {bad!r} is not part of any experiment (the standard reply)", c == 200 and "exp_token" not in j and j["prices"] == BASE_LADDER["eu"], j)
r2 = requests.get(BASE + "/api/checkout", headers={"X-Snapeyes-Visitor": f"{vids['extra10']}, {vids['control']}"}, timeout=60)
check("a header holding two ids is not a valid id: not part of any experiment, nothing breaks", r2.status_code == 200 and "exp_token" not in r2.json(), r2.text[:200])
# ordering closed: nothing is assigned
saved_key = os.environ.pop("STRIPE_SECRET_KEY")
c, j = info(vids["extra10"])
os.environ["STRIPE_SECRET_KEY"] = saved_key
check("while ordering is closed (no Stripe key) nobody is assigned and the reply says closed", c == 200 and j["open"] is False and "exp_token" not in j and "experiments" not in j, j)
# a changed ticket secret voids every token
tok = i1["exp_token"]
os.environ["SNAPEYES_TICKET_SECRET"] = "another-secret-entirely-0123456789"
check("a token does not verify under another ticket secret", A.verify(tok) is None)
forged_other = A.sign({KEY: "extra10"})
os.environ["SNAPEYES_TICKET_SECRET"] = "paybackend-test-secret"
check("...and one signed under it does not verify under the real one", A.verify(forged_other) is None)
check("...the real secret verifies its own token again", A.verify(tok) == {KEY: "extra10"})

# tampered tokens at checkout
section("5. tampered tokens: the price comes from the verified assignment only")
o, k = new_order(4)


def price_with(token, eyes=4, market="eu", **kw):
    n0 = len(H.Fake.creates)
    c, j = checkout(o, k, eyes, market=market, exp_token=token, **kw)
    unit = int(H.Fake.creates[-1][0]["line_items[0][price_data][unit_amount]"]) if len(H.Fake.creates) > n0 else None
    return c, j, unit


std4 = ladder_price(BASE_LADDER["eu"], 4, "studio_black")           # 3997 + 2 x 1500
low4 = ladder_price(want_ladder(KEY, "extra10", "eu"), 4, "studio_black")   # 3997 + 2 x 1000
check("test setup: the variants really differ for four eyes", std4 == 6997 and low4 == 5997)
c, j, unit = price_with(i1["exp_token"])
check("the honest token of the cheaper variant is charged the cheaper ladder", c == 200 and unit == low4 and j["amount"] == low4, (c, j))
c, j, unit = price_with(ic["exp_token"])
check("the control token is charged the standard ladder", c == 200 and unit == std4, (c, j))
c, j, unit = price_with(None)
check("no token: the standard ladder", c == 200 and unit == std4 and "metadata[exp]" not in H.Fake.creates[-1][0], (c, j))
good = i1["exp_token"]
head, body_b64, sig = good.split(".")


def flip(s, i=3):
    return s[:i] + ("A" if s[i] != "A" else "B") + s[i + 1:]


forgeries = {
    "one signature character flipped": f"{head}.{body_b64}.{flip(sig, 5)}",
    "the payload of the cheaper variant with the control's signature": f"{head}.{body_b64}.{ic['exp_token'].split('.')[2]}",
    "the control payload with the cheaper variant's signature": f"{head}.{ic['exp_token'].split('.')[1]}.{sig}",
    "a payload edited to another variant, old signature": ".".join([head, base64.urlsafe_b64encode(json.dumps({"a": {KEY: "extra10"}, "t": int(time.time())}, separators=(",", ":"), sort_keys=True).encode()).rstrip(b"=").decode() + "A", sig]),
    "no signature": f"{head}.{body_b64}.",
    "signature too short": f"{head}.{body_b64}.{sig[:16]}",
    "another kind": f"x2.{body_b64}.{sig}",
    "only a payload": body_b64,
    "empty": "",
    "a number": 7,
    "an object": {"a": {KEY: "extra10"}},
    "a list": [good],
    "a huge string": "x1." + "A" * 5000 + "." + sig,
    "whitespace around a good token": " " + good + " ",
}
for label, tk in forgeries.items():
    c, j, unit = price_with(tk)
    check(f"forged token refused, the standard price is charged ({label})", c == 200 and unit == std4 and "metadata[exp]" not in H.Fake.creates[-1][0] and A.verify(tk) is None, (c, unit, j))
now = int(time.time())
check("an expired token (31 days old, correctly signed) is not honoured", A.verify(A.sign({KEY: "extra10"}, now=now - 31 * 86400)) is None)
check("a token from the future (an hour ahead) is not honoured", A.verify(A.sign({KEY: "extra10"}, now=now + 3600)) is None)
check("a token 29 days old is still honoured", A.verify(A.sign({KEY: "extra10"}, now=now - 29 * 86400)) == {KEY: "extra10"})
c, j, unit = price_with(A.sign({KEY: "extra10"}, now=now - 31 * 86400))
check("...and an expired one at checkout is the standard price", unit == std4, (c, j))
c, j, unit = price_with(A.sign({KEY: "does_not_exist_variant"}))
check("a correctly signed token naming a variant that does not exist: the standard price", unit == std4, (c, j))
c, j, unit = price_with(A.sign({"no_such_experiment": "extra10"}))
check("...or an experiment that does not exist", unit == std4, (c, j))
c, j, unit = price_with(A.sign({"au_ladder_high": "high"}))
check("a token of an experiment that is not running (au) is the standard price on its own market and elsewhere", unit == std4, (c, j))
c, j, unit = price_with(i1["exp_token"], eyes=4, market="au")
check("a token of the euro experiment used in Australia: the Australian standard price", c == 200 and unit == ladder_price(BASE_LADDER["au"], 4, "studio_black"), (c, j, unit))
# extra body fields never name a variant or a price
c, j, unit = price_with(ic["exp_token"], variant="extra10", exp_var="extra10", exp="extra_eye_eur", experiment={"key": KEY, "variant": "extra10"},
                        ladder=want_ladder(KEY, "extra10", "eu"), prices=want_ladder(KEY, "extra10", "eu"), amount=1, unit_amount=1, price=1, total=1, currency="usd")
check("fields that name a variant, a ladder or an amount are ignored: the token's variant decides", c == 200 and unit == std4 and j["amount"] == std4, (c, j))
# shown: only compared
n_sessions = len(H.Fake.creates)
rec_before = read_json(f"orders/{o}/order.json")
for label, shown in (("a cheaper price", low4 - 1000), ("the other variant's price", std4), ("a string", str(low4)), ("a bool", True), ("a float", float(low4)), ("zero", 0)):
    c, j, unit = price_with(i1["exp_token"], shown=shown)
    check(f"'shown' that is not the price to be charged ({label}) -> 409 price_changed, nothing created",
          c == 409 and j.get("reason") == "price_changed" and j["amount"] == low4 and j["prices"] == want_ladder(KEY, "extra10", "eu") and j["market"] == "eu"
          and len(H.Fake.creates) == n_sessions, (c, j))
check("...and the order record is untouched by those refusals", read_json(f"orders/{o}/order.json") == rec_before)
c, j, unit = price_with(i1["exp_token"], shown=low4)
check("'shown' equal to the price to be charged: the session is created, at that price", c == 200 and unit == low4, (c, j))
c, j, unit = price_with(None, shown=low4)
check("a page that showed the cheaper price but sends no token: 409 price_changed with the standard price and no token",
      c == 409 and j["reason"] == "price_changed" and j["amount"] == std4 and j["prices"] == BASE_LADDER["eu"] and "exp_token" not in j, (c, j))
c, j, unit = price_with(i1["exp_token"], shown=std4)
check("the 409 for a token names the current price, ladder and a re-signed token", c == 409 and j["amount"] == low4 and A.verify(j["exp_token"]) == {KEY: "extra10"}, (c, j))
c, j, unit = price_with(None, shown=std4)
check("'shown' with no experiment at all and the right standard price is simply accepted", c == 200 and unit == std4, (c, j))

# =================================================================== 6. shown = charged = recorded for everything
section("6. price shown = charged = recorded: every variant, market, eye count, style")
for key in KEYS:
    c, j = adm("exp_start", **{"key": key}) if not A.is_running(key) else (200, {})
    assert c == 200, (key, c, j)
c_b, plain_both = info()
check("with both tests running a request without an id names all three markets (exp_markets)", c_b == 200 and plain_both.get("exp_markets") == ["au", "eu", "lt"], plain_both)
combos = []
n_checked = 0
mismatch = []
captured = {}
for key in KEYS:
    for variant in variants_of(key):
        for market in DEFS[key]["markets"]:
            vid = vid_for(key, variant, 1)
            c, rep = info(vid)
            assert c == 200 and rep["experiments"], (key, variant, rep)
            ex = next(e for e in rep["experiments"] if e["key"] == key)
            assert ex["variant"] == variant
            page_ladder = rep["markets"][market]["prices"]
            if page_ladder != want_ladder(key, variant, market):
                mismatch.append(("ladder", key, variant, market))
            captured[f"{key}_{variant}"] = {"reply": rep, "market": market, "ladder": page_ladder} if f"{key}_{variant}" not in captured else captured[f"{key}_{variant}"]
            o6, k6 = new_order(8)
            for eyes in range(1, 9):
                for style in ("studio_black", "celestial_gold") if eyes == 1 else ("studio_black", "supernova"):
                    shown = ladder_price(page_ladder, eyes, style)          # what the page prints (client rule, restated)
                    c, j = checkout(o6, k6, eyes, style=style, market=market, exp_token=rep["exp_token"], shown=shown)
                    p, _ = H.Fake.creates[-1]
                    rec = read_json(f"orders/{o6}/order.json")["checkout"]
                    n_checked += 1
                    good = (c == 200 and j["amount"] == shown and int(p["line_items[0][price_data][unit_amount]"]) == shown
                            and p["line_items[0][price_data][currency]"] == MK.MARKETS[market]["currency"]
                            and p["metadata[amount]"] == str(shown) and p["metadata[exp]"] == key and p["metadata[exp_var]"] == variant
                            and p["metadata[market]"] == market and rec["amount"] == shown
                            and p["metadata[exp_lad]"] == A.ladder_text(want_ladder(key, variant, market))
                            and rec["experiment"] == {"key": key, "variant": variant, "prices": want_ladder(key, variant, market)}
                            and rec["market"] == market and rec["currency"] == MK.MARKETS[market]["currency"])
                    if not good:
                        mismatch.append((key, variant, market, eyes, style, c, j))
check(f"shown = charged by Stripe = metadata = order.json for all {n_checked} checkouts (every variant, market, 1-8 eyes, styles)", not mismatch and n_checked == 96, (n_checked, mismatch[:3]))

# a full payment of every variant and market, at several eye counts
paid_orders = {}
for key in KEYS:
    for variant in variants_of(key):
        for market in DEFS[key]["markets"]:
            vid = vid_for(key, variant, 2)
            c, rep = info(vid)
            lad = rep["markets"][market]["prices"]
            for eyes, style in ((1, "celestial_gold"), (2, "studio_black"), (3, "studio_black"), (8, "studio_black")):
                o7, k7 = new_order(eyes)
                shown = ladder_price(lad, eyes, style)
                c, j = checkout(o7, k7, eyes, style=style, market=market, exp_token=rep["exp_token"], shown=shown)
                sid = next(s for s, x in H.Fake.sessions.items() if x["metadata"].get("order") == o7)
                cw, jw = pay_session(sid, live=True)
                paid = read_json(f"orders/{o7}/paid.json")
                stc, stj = get(f"/api/order?o={o7}&k={k7}")
                exp_rec = paid.get("experiment") or {}
                ok = (cw == 200 and paid["amount_total"] == shown and "amount_mismatch" not in paid and paid["market"] == market
                      and paid["currency"] == MK.MARKETS[market]["currency"] and exp_rec.get("key") == key and exp_rec.get("variant") == variant
                      and exp_rec.get("prices") == lad and stj["amount"] == shown and stj["currency"] == MK.MARKETS[market]["currency"].upper()
                      and pay.price_text(shown, "en", paid["currency"]))
                paid_orders[(key, variant, market, eyes)] = (o7, k7, shown, ok)
                if not ok:
                    check(f"paid {key}/{variant}/{market}/{eyes} eyes: paid.json amount, market, experiment and the order page", False, (cw, jw, paid, stj))
check("every paid variant order (24 of them): paid.json amount = the variant's price, experiment {key, variant, prices} recorded, no mismatch, the order page says the same amount",
      len(paid_orders) == 24 and all(v[3] for v in paid_orders.values()), [k for k, v in paid_orders.items() if not v[3]])
mails = [m for m, _ in H.Fake.emails if m.get("to") != ["info@snapeyes.com"]]
sample = paid_orders[("extra_eye_eur", "extra10", "eu", 8)]
mail8 = next(m for m in mails if sample[0] in m.get("subject", "") and "confirmation" in m.get("subject", ""))
want_txt = pay.price_text(sample[2], "en", "eur")
check("the confirmation email of a variant order names the price paid and the full price list that applied (each further eye at the variant's price)",
      want_txt in mail8["text"] and "Price list that applied to your order" in mail8["text"] and pay.price_text(1000, "en", "eur") in mail8["text"]
      and pay.price_text(1997, "en", "eur") in mail8["text"], mail8["text"][:900])
sample_au = paid_orders[("au_ladder_high", "high", "au", 3)]
mail_au = next(m for m in mails if sample_au[0] in m.get("subject", "") and "confirmation" in m.get("subject", ""))
seg_au = mail_au["text"].split("Price list that applied to your order", 1)[1][:400]
check("the Australian variant order: email with the invoice total = the amount paid, the price list of the high ladder (A$59 art background, not the standard A$49), no 'was' price",
      pay.price_text(sample_au[2], "en", "aud") in mail_au["text"] and "Invoice" in mail_au["text"] and pay.price_text(5900, "en", "aud") in seg_au
      and pay.price_text(3900, "en", "aud") not in seg_au and not re.search(r"\bwas\b|strike|countdown|only today|hurry", seg_au, re.I), seg_au)
abtest_row = A.price_list_row({"experiment": {"prices": want_ladder(KEY, "extra10", "eu")}, "currency": "eur"}, "de")
check("German confirmation of a variant order uses 'Preisliste, die für Ihre Bestellung galt'",
      abtest_row and "Preisliste, die für Ihre Bestellung galt" in abtest_row[0] and "10,00 €" in abtest_row[1], abtest_row)
check("no dash of any kind in that sentence (all languages of the row)", not re.search("[\u2013\u2014]", json.dumps([A.ROW_LABEL, A.ROW_TEXT], ensure_ascii=False)))
# old orders: no experiment key at all
o8, k8 = new_order(3)
c, j = checkout(o8, k8, 3, exp_token=None)
sid8 = next(s for s, x in H.Fake.sessions.items() if x["metadata"].get("order") == o8)
pay_session(sid8, live=True)
old_paid = read_json(f"orders/{o8}/paid.json")
check("an order made without a token: the standard price, paid.json has no experiment, the mail has no price-list row",
      old_paid["amount_total"] == 3997 + 1500 and "experiment" not in old_paid and A.price_list_row(old_paid, "en") is None, old_paid)
# a paid record made before experiments existed (no experiment key, no exp metadata) is still read everywhere
legacy = json.loads(json.dumps(old_paid))
check("order_view of a legacy record is None; the confirmation mail of it builds", A.order_view(legacy, {"checkout": {}}) is None and A.session_ok({"metadata": {"eyes": "3", "style": "studio_black"}, "amount_total": 5}) is True)

# =================================================================== 7. sessions that are not ours to record
section("7. paid sessions at other amounts or under undefined experiments are refused")


def fresh_session(token, eyes=3, market="eu", shown=None):
    oo, kk = new_order(eyes)
    c, j = checkout(oo, kk, eyes, market=market, exp_token=token)
    sid = next(s for s, x in H.Fake.sessions.items() if x["metadata"].get("order") == oo)
    return oo, kk, sid


tok_x = info(vid_for(KEY, "extra10", 3))[1]["exp_token"]
n_notes = len(owner_notes())
oo, kk, sid = fresh_session(tok_x)
H.Fake.sessions[sid]["amount_total"] -= 500
cw, jw = pay_session(sid)
check("a paid session of an experiment at another amount than its variant's price: refused, not recorded, nothing made",
      cw == 200 and jw.get("ignored") == "session does not match" and not exists(f"orders/{oo}/paid.json"), (cw, jw))
notes = owner_notes()
check("...and the owner is told (once) to check and refund it", len(notes) == n_notes + 1 and "unexpected price" in notes[-1]["subject"] and sid in notes[-1]["text"], notes[-1:])
cw, jw = pay_session(sid)
check("a replayed event of it does not tell the owner again", len(owner_notes()) == n_notes + 1, (cw, jw))
cheap = A.ladder_text(want_ladder(KEY, "extra10", "eu")).split(",")
cheap[3] = "100"
for label, tweak in (("a ladder in its metadata that does not give the amount", lambda s: s["metadata"].update(exp_lad=",".join(cheap))),
                     ("a malformed ladder and an undefined variant", lambda s: s["metadata"].update(exp_lad="x", exp_var="zzz")),
                     ("no ladder and an undefined experiment", lambda s: (s["metadata"].pop("exp_lad"), s["metadata"].update(exp="no_such_test"))),
                     ("an amount in its metadata that is not the amount charged", lambda s: s["metadata"].update(amount=str(int(s["metadata"]["amount"]) + 1))),
                     ("a market the experiment does not cover", lambda s: s["metadata"].update(market="au", currency="aud")),
                     ("an eye count the amount does not fit", lambda s: s["metadata"].update(eyes="2")),
                     ("a style the amount does not fit", lambda s: s["metadata"].update(style="studio_black") if False else s["metadata"].update(style="not_a_style"))):
    oo, kk, sid = fresh_session(tok_x)
    tweak(H.Fake.sessions[sid])
    if label == "a market the experiment does not cover":
        H.Fake.sessions[sid]["currency"] = "aud"
    cw, jw = pay_session(sid)
    check(f"a paid session with {label}: refused, not recorded", cw == 200 and not exists(f"orders/{oo}/paid.json"), (cw, jw))
# the untouched session of the same kind is recorded
oo, kk, sid = fresh_session(tok_x)
cw, jw = pay_session(sid)
check("the same kind of session, untouched, is recorded with its experiment", cw == 200 and exists(f"orders/{oo}/paid.json") and read_json(f"orders/{oo}/paid.json")["experiment"]["variant"] == "extra10", (cw, jw))
# the standard behaviour for a session without an experiment is unchanged: another amount is recorded with amount_mismatch and delivered
oo, kk, sid = fresh_session(None)
H.Fake.sessions[sid]["amount_total"] -= 500
cw, jw = pay_session(sid)
pd = read_json(f"orders/{oo}/paid.json") if exists(f"orders/{oo}/paid.json") else {}
check("without an experiment the old rule stands: another amount is recorded with amount_mismatch (and delivered), as before", cw == 200 and pd.get("amount_mismatch", {}).get("expected") == 3997 + 1500, (cw, jw, pd))
# record_paid itself refuses such a session too (every caller checks session_matches first; this is the second lock)
oo, kk, sid = fresh_session(tok_x)
H.Fake.sessions[sid]["amount_total"] -= 500
sess_bad = H.pay_session(sid)
try:
    pay.record_paid(oo, read_json(f"orders/{oo}/order.json"), sess_bad, "test")
    refused = False
except pay.PayError:
    refused = True
check("pay.record_paid called directly with such a session raises and records nothing (defence in depth)", refused and not exists(f"orders/{oo}/paid.json"))
# the session checks themselves
sess = {"object": "checkout.session", "mode": "payment", "amount_total": low4, "metadata": {"exp": KEY, "exp_var": "extra10", "market": "eu", "eyes": "4", "style": "studio_black"}}
check("abtest.session_ok: the variant's price passes, one cent off fails, the other variant's price fails",
      A.session_ok(sess) and not A.session_ok(dict(sess, amount_total=low4 + 1)) and not A.session_ok(dict(sess, amount_total=std4)))
check("abtest.session_ok: amount missing, a string or a bool fails",
      not A.session_ok({k: v for k, v in sess.items() if k != "amount_total"}) and not A.session_ok(dict(sess, amount_total=str(low4))) and not A.session_ok(dict(sess, amount_total=True)))
check("abtest.session_ok: exp without exp_var, or exp_var without exp, fails; both missing passes",
      not A.session_ok(dict(sess, metadata={"exp": KEY, "market": "eu", "eyes": "4", "style": "studio_black"})) and not A.session_ok(dict(sess, metadata={"exp_var": "extra10", "market": "eu"}))
      and A.session_ok({"metadata": {}, "amount_total": 1}))

# =================================================================== 8. stopping and restarting
section("8. an experiment stopped while a checkout is open")
tok_s = info(vid_for(KEY, "extra10", 4))[1]["exp_token"]
oo, kk, sid = fresh_session(tok_s, eyes=5)
c, j = adm("exp_stop", **{"key": KEY})
check("stop: ok, not running, the stop time recorded", c == 200 and not A.is_running(KEY) and read_json(f"ops/experiments/{KEY}.json")["runs"][-1]["stop"], (c, j))
c, j = info(vid_for(KEY, "extra10", 4))
check("after the stop GET holds no assignment of that experiment and the standard ladder (the Australian one still runs)",
      all(e["key"] != KEY for e in j.get("experiments", [])) and j["prices"] == BASE_LADDER["eu"] and j["markets"]["lt"]["prices"] == BASE_LADDER["lt"], j)
cw, jw = pay_session(sid)
paid = read_json(f"orders/{oo}/paid.json")
check("a checkout opened before the stop is still paid at its variant's price and recorded with its experiment",
      cw == 200 and paid["amount_total"] == ladder_price(want_ladder(KEY, "extra10", "eu"), 5, "studio_black") and paid["experiment"]["variant"] == "extra10" and "amount_mismatch" not in paid, paid)
o9, k9 = new_order(3)
c, j = checkout(o9, k9, 3, exp_token=tok_s, shown=ladder_price(want_ladder(KEY, "extra10", "eu"), 3, "studio_black"))
check("the old token after the stop: the page's price is refused with the standard price (409), nothing is created", c == 409 and j["reason"] == "price_changed" and j["amount"] == 3997 + 1500, (c, j))
c, j = checkout(o9, k9, 3, exp_token=tok_s)
check("...and without 'shown' it is charged the standard price", c == 200 and j["amount"] == 3997 + 1500, (c, j))
c, j = adm("exp_start", **{"key": KEY})
check("start again: a second run, the same visitors get the same variants", c == 200 and len(read_json(f"ops/experiments/{KEY}.json")["runs"]) == 2 and info(vid_for(KEY, "extra10", 4))[1]["experiments"][0]["variant"] == "extra10", (c, j))

# =================================================================== 9. events per variant
section("9. anonymous events per variant")
ev0 = event_keys()
tv = info(vid_for(KEY, "extra10", 5))[1]["exp_token"]
tc = info(vid_for(KEY, "control", 5))[1]["exp_token"]
for tk in (tv, tv, tc):
    post("/api/checkout", {"exp_event": "visit", "exp_token": tk, "market": "eu"})
post("/api/checkout", {"exp_event": "preview", "exp_token": tv, "market": "lt", "eyes": 3, "style": "deep_nebula"})
post("/api/checkout", {"exp_event": "preview", "exp_token": tc, "market": "eu", "eyes": 1, "style": "celestial_gold"})
post("/api/checkout", {"exp_event": "preview", "exp_token": tv, "market": "eu", "eyes": 9, "style": "celestial_gold"})
new = events_since(ev0)
check("beacons with a valid token of a running experiment are stored, one event each", len(new) == 6 and {e["stage"] for e in new} == {"visit", "preview"}, new)
check("a preview of 3 eyes on the cheaper variant is an affected artwork (hit), one eye on the control is not",
      any(e["stage"] == "preview" and e["variant"] == "extra10" and e.get("eyes") == 3 and e.get("hit") is True for e in new)
      and any(e["stage"] == "preview" and e["variant"] == "control" and e.get("eyes") == 1 and e.get("hit") is False for e in new), new)
check("a preview with nine eyes is counted but carries no eye count or hit", any(e["stage"] == "preview" and "eyes" not in e and "hit" not in e for e in new), new)
for label, body in (("an unknown event", {"exp_event": "click", "exp_token": tv, "market": "eu"}), ("no market", {"exp_event": "visit", "exp_token": tv}),
                    ("a market that is not a string", {"exp_event": "visit", "exp_token": tv, "market": 5})):
    c, j = post("/api/checkout", body)
    check(f"beacon: {label} -> 400", c == 400, (c, j))
for label, body in (("a forged token", {"exp_event": "visit", "exp_token": tv[:-1] + ("0" if tv[-1] != "0" else "1"), "market": "eu"}),
                    ("a market no experiment covers", {"exp_event": "visit", "exp_token": tv, "market": "hu"}),
                    ("an unknown market", {"exp_event": "visit", "exp_token": tv, "market": "zz"})):
    n1 = event_keys()
    c, j = post("/api/checkout", body)
    check(f"beacon with {label}: answered, not counted, nothing stored", c == 200 and j.get("counted") is False and event_keys() == n1, (c, j))
allev = json.dumps(events_of())
check("no event holds a visitor id, a token, an order number or an email", not re.search(r"[a-f0-9]{32}|x1\.|@|\d{6}-[0-9a-f]{8,}", allev), allev[:300])
check("every event holds only the whitelisted fields", all(set(e) <= {"v", "kind", "t", "ms", "stage", "exp", "variant", "market", "eyes", "amount", "currency", "hit", "live"} for e in events_of()))
# an event through events.build that tries to smuggle personal data
ev = E.build("exp", {"stage": "visit", "exp": KEY, "variant": "control", "market": "eu", "email": "a@b.c", "vid": "0" * 32, "order": "260101-abcdef0123456789", "ip": "1.2.3.4"})
check("events.build drops any field it does not list (email, id, order, ip)", set(ev) <= {"v", "kind", "t", "ms", "stage", "exp", "variant", "market"} and "email" not in ev, ev)
ev = E.build("exp", {"stage": "visit", "exp": "a b@c", "variant": "control", "market": "eu"})
check("...and a code with a space or @ is dropped", "exp" not in ev, ev)

# funnel numbers: checkouts and payments of known amounts
v, jv = view()
base_paid = {var: stat(v, KEY, var)["paid"] for var in variants_of(KEY)}
base_chk = {var: stat(v, KEY, var)["checkouts"] for var in variants_of(KEY)}
base_rev = {var: stat(v, KEY, var)["revenue"] for var in variants_of(KEY)}
o10, k10 = new_order(3)
tk1 = info(vid_for(KEY, "extra10", 6))[1]["exp_token"]
tk0 = info(vid_for(KEY, "control", 6))[1]["exp_token"]
c, j = checkout(o10, k10, 3, exp_token=tk1)
sid10 = next(s for s, x in H.Fake.sessions.items() if x["metadata"].get("order") == o10)
pay_session(sid10, live=True)
o11, k11 = new_order(2)
c, j = checkout(o11, k11, 2, exp_token=tk0)
sid11 = next(s for s, x in H.Fake.sessions.items() if x["metadata"].get("order") == o11)
pay_session(sid11, live=True)
o12, k12 = new_order(3)
c, j = checkout(o12, k12, 3, exp_token=tk1)
sid12 = next(s for s, x in H.Fake.sessions.items() if x["metadata"].get("order") == o12)
pay_session(sid12, live=False)          # a Stripe test payment: counted as a test payment, no revenue
v, jv = view()
d_paid = {var: stat(v, KEY, var)["paid"] - base_paid[var] for var in variants_of(KEY)}
d_chk = {var: stat(v, KEY, var)["checkouts"] - base_chk[var] for var in variants_of(KEY)}
d_rev = {var: stat(v, KEY, var)["revenue"] - base_rev[var] for var in variants_of(KEY)}
check("the funnel counts a checkout and a live payment per variant (control: 1 and 1; cheaper: 2 checkouts, 1 live payment, the test one apart)",
      d_paid == {"control": 1, "extra10": 1} and d_chk == {"control": 1, "extra10": 2} and stat(v, KEY, "extra10")["paid_test"] >= 1, (d_paid, d_chk, stat(v, KEY, "extra10")))
check("revenue per variant is the sum of the live payments' amounts (a test payment adds nothing)", d_rev == {"control": 3997, "extra10": 3997 + 1000}, d_rev)
s1 = stat(v, KEY, "extra10")
check("average order = revenue / paid orders, per the experiment's currency; conversion = paid / visitors", s1["avg_order"] == round(s1["revenue"] / s1["paid"]) and abs(s1["rate_paid"] - s1["paid"] / s1["visitors"]) < 1e-9, s1)
check("affected orders (3+ eyes) are counted apart: the 3-eye payment is a hit on both, the 2-eye one is not",
      stat(v, KEY, "extra10")["hit_paid"] >= 1 and stat(v, KEY, "control")["hit_paid"] >= 0 and s1["revenue_hit"] > 0, s1)
check("the events of the payment carry the amount, the currency and live", any(e["stage"] == "paid" and e["variant"] == "extra10" and e.get("amount") == 4997 and e.get("currency") == "eur" and e.get("live") is True for e in events_of()))
# the paid event is written once even when the webhook is replayed
n_paid_ev = len([e for e in events_of() if e["stage"] == "paid"])
body, sig = H.signed_event(H.Fake.sessions[sid10])
hook(body, sig)
check("a replayed webhook adds no second paid event", len([e for e in events_of() if e["stage"] == "paid"]) == n_paid_ev)

# =================================================================== 10. the admin page's data
section("10. admin page data")
v, jv = view()
e1 = v[KEY]
check("the page data lists each experiment with title, key, markets, currency, state, full ladders and the split",
      all(k in e1 for k in ("title", "about", "markets", "currency", "changes", "state", "variants", "stats", "compare", "need", "warnings", "hit_label"))
      and e1["currency"] == "EUR" and v["au_ladder_high"]["currency"] == "AUD"
      and [x["variant"] for x in e1["variants"]] == ["control", "extra10"] and e1["variants"][1]["prices"] == DEFS[KEY]["variants"]["extra10"]["prices"], e1)
check("Lithuanian titles with diacritics, no dashes in what the page shows",
      all(re.search("[ąčęėįšųūž]", v[k]["title"] + v[k]["about"]) for k in v) and not re.search("[\u2013\u2014]", json.dumps(jv, ensure_ascii=False)))
check("the experiment is running on the page, since a time", e1["state"]["running"] and e1["state"]["since"] and len(e1["state"]["runs"]) == 2)
check("the log of the page holds the start and stop lines of the audit log", any(l["action"] == "exp_stop" for l in jv["log"]) and any(l["action"] == "exp_start" and l.get("detail") == KEY for l in jv["log"]), jv["log"][:4])
check("the rules the page states are the server's (10 paid, 100 visitors, spread 1.5, 25 %)", jv["rules"] == {"min_arm_paid": 10, "min_arm_visitors": 100, "spread_warn": 1.5, "rel_effect": 0.25}, jv["rules"])
c, js = adm("summary")
check("the summary lists every experiment with whether it runs", c == 200 and {x["key"]: x["running"] for x in js["experiments"]} == {k: A.is_running(k) for k in KEYS} and A.is_running(KEY), js.get("experiments"))
c, jo = adm("orders", days=2)
rows = {r["order"]: r for r in jo["orders"]}
check("the orders list marks orders made under an experiment (key and variant) and leaves the others empty",
      {k: rows[o10]["experiment"][k] for k in ("key", "variant")} == {"key": KEY, "variant": "extra10"} and rows[o10]["experiment"]["label"]
      and {k: rows[o11]["experiment"][k] for k in ("key", "variant")} == {"key": KEY, "variant": "control"} and rows[o8]["experiment"] is None, {k: rows[k]["experiment"] for k in (o10, o11, o8)})
c, jd = adm("order", order=o10)
ex = jd.get("experiment") or {}
check("the order detail shows the variant, its label, and the price list that applied", c == 200 and ex.get("key") == KEY and ex.get("variant") == "extra10" and ex.get("prices") == want_ladder(KEY, "extra10", "eu")
      and ex.get("label") and ex.get("source") == "paid" and ex.get("known") is True, ex)
c, jd = adm("order", order=o8)
check("an old order's detail has no experiment", jd.get("experiment") is None, jd.get("experiment"))
ou, ku = new_order(2)
checkout(ou, ku, 2, exp_token=tk1)
c, jd = adm("order", order=ou)
check("the order detail of an unpaid checkout under an experiment shows it from the checkout (its variant, not yet paid)",
      c == 200 and (jd.get("experiment") or {}).get("variant") == "extra10" and jd["experiment"]["source"] == "checkout" and jd["paid"] is False
      and jd["experiment"]["prices"] == want_ladder(KEY, "extra10", "eu"), jd.get("experiment"))
check("the page data lists the runs from the state, says where the paid numbers come from and whether events are collected",
      jv["runs"] and all({"key", "title", "start", "stop"} <= set(r) for r in jv["runs"]) and jv["orders_source"] == "orders" and jv["collecting"] is True, {k: jv.get(k) for k in ("runs", "orders_source", "collecting")})

# significance: known numbers through the real code path (events written into the store for a fresh experiment day)
section("11. significance note, sample size")


def z_two_sided(x1, n1, x2, n2):
    p = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    z = (x2 / n2 - x1 / n1) / se
    return z, math.erfc(abs(z) / math.sqrt(2))


c = A.compare({"variant": "control", "visitors": 1000, "paid": 30, "rate_paid": 0.03}, {"variant": "extra10", "visitors": 1000, "paid": 50, "rate_paid": 0.05})
zz, pp = z_two_sided(30, 1000, 50, 1000)
check("z test: 30/1000 against 50/1000 gives the textbook p (about 0.0225)", c["enough"] and abs(c["p"] - round(pp, 4)) < 1e-9 and abs(c["z"] - round(zz, 3)) < 1e-9 and 0.022 < c["p"] < 0.023, (c, zz, pp))
c = A.compare({"variant": "control", "visitors": 1000, "paid": 5, "rate_paid": 0.005}, {"variant": "extra10", "visitors": 1000, "paid": 50, "rate_paid": 0.05})
check("too few paid orders in one arm: no p-value, why few_paid", not c["enough"] and c["p"] is None and c["why"] == "few_paid", c)
c = A.compare({"variant": "control", "visitors": 60, "paid": 30, "rate_paid": 0.5}, {"variant": "extra10", "visitors": 1000, "paid": 50, "rate_paid": 0.05})
check("too few visitors in one arm: no p-value, why few_visitors", not c["enough"] and c["p"] is None and c["why"] == "few_visitors", c)
c = A.compare({"variant": "control", "visitors": 500, "paid": 10, "rate_paid": 0.02}, {"variant": "extra10", "visitors": 500, "paid": 10, "rate_paid": 0.02})
check("equal rates: p = 1", c["enough"] and c["p"] == 1.0, c)
ns = A.need_sample(0.02)
p1, p2 = 0.02, 0.025
n_ref = ((1.959964 * math.sqrt(2 * ((p1 + p2) / 2) * (1 - (p1 + p2) / 2)) + 0.841621 * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2) / (p2 - p1) ** 2
check("sample size for a 25 % change at a 2 % rate matches the textbook formula (about 13.8 thousand visitors, 277 paid orders per arm)",
      abs(ns["visitors"] - math.ceil(n_ref)) <= 1 and 277 <= ns["paid"] <= 278, (ns, n_ref))
check("the page says the sample needed and that it is an assumption while the control has no rate of its own", e1["need"]["assumed"] in (True, False) and e1["need"]["paid"] > 100, e1["need"])
# through the whole path: visitors as events in today's folder, paid orders as order records, both read through the admin action
day = time.strftime("%Y-%m-%d", time.gmtime())
os.makedirs(local(f"ops/events/{day}"), exist_ok=True)


def add_events(variant, stage, n, **kw):
    for i in range(n):
        ev = E.build("exp", dict({"stage": stage, "exp": "au_ladder_high", "variant": variant, "market": "au"}, **kw))
        with open(local(f"ops/events/{day}/{time.strftime('%H%M%S', time.gmtime())}-{secrets.token_hex(6)}.json"), "w", encoding="utf-8") as f:
            json.dump(ev, f)


def write_json(path, obj):
    os.makedirs(os.path.dirname(local(path)), exist_ok=True)
    with open(local(path), "w", encoding="utf-8") as f:
        json.dump(obj, f)


def add_orders(key, variant, n, amount, market="au", currency="aud", eyes=2, style="studio_black", live=True, kind=None, tokened=True, created=None):
    """n order folders in the local store, written the way the flows write them (order.json with its checkout, paid.json).
    kind: None (kept), "refunded" (refunded.json) or "withdrawn" (withdrawn.json). tokened False: an order without a variant."""
    ids = []
    lad = want_ladder(key, variant, market) if tokened else None
    for _ in range(n):
        oid = time.strftime("%y%m%d", time.gmtime()) + "-" + secrets.token_hex(8)
        now = int(time.time()) if created is None else created
        spec = {"eyes": eyes, "style": style, "market": market, "lang": "en", "layout": "single", "names": "", "title": ""}
        co = {"session_id": "cs_test_" + secrets.token_hex(6), "created_at": now, "amount": amount, "currency": currency, "market": market, "spec": spec}
        if tokened:
            co["experiment"] = {"key": key, "variant": variant, "prices": lad}
        write_json(f"orders/{oid}/order.json", {"order": oid, "created_at": now, "checkout": co, "lang": "en"})
        paid = {"paid": True, "order": oid, "session_id": co["session_id"], "payment_intent": "pi_" + secrets.token_hex(8), "amount_total": amount,
                "currency": currency, "market": market, "livemode": live, "email": "x@example.com", "paid_at": now, "paid_iso": "2026-09-30T10:00:00Z",
                "source": "webhook", "spec": spec}
        if tokened:
            paid["experiment"] = {"key": key, "variant": variant, "prices": lad}
        write_json(f"orders/{oid}/paid.json", paid)
        if kind == "refunded":
            write_json(f"orders/{oid}/refunded.json", {"t": now})
        if kind == "withdrawn":
            write_json(f"orders/{oid}/withdrawn.json", {"t": now})
        ids.append(oid)
    return ids


adm("exp_start", **{"key": "au_ladder_high"}) if not A.is_running("au_ladder_high") else None
ops._DAYCACHE.clear()
v0, _ = view()
b0c, b0h = stat(v0, "au_ladder_high", "control"), stat(v0, "au_ladder_high", "high")
u0 = v0["au_ladder_high"]["untokened"]
add_events("control", "visit", 1000)
add_events("high", "visit", 1000)
add_events("high", "paid", 7, eyes=2, amount=8900, currency="aud", live=True, hit=True)      # events that the order records do not back up
add_orders("au_ladder_high", "control", 30, 7900)
add_orders("au_ladder_high", "high", 50, 8900)
add_orders("au_ladder_high", "high", 3, 8900, kind="refunded")
add_orders("au_ladder_high", "high", 2, 8900, kind="withdrawn")
add_orders("au_ladder_high", "high", 2, 8900, live=False)
add_orders("au_ladder_high", "control", 4, 7900, tokened=False)
add_orders("au_ladder_high", "control", 2, 7900, tokened=False, live=False)       # untokened test payments do not count as paid untokened orders
ops._DAYCACHE.clear()
v, jv = view()
ea = v["au_ladder_high"]
sc, sh = stat(v, "au_ladder_high", "control"), stat(v, "au_ladder_high", "high")
cmp_ = ea["compare"][0]
zz, pp = z_two_sided(30, 1000, 50, 1000)
dv = lambda new, old, k: new[k] - old[k]
check("through the admin action: visitors come from the events (1000 each), paid orders and revenue from the order records (30 and 50 live orders of A$79 and A$89)",
      dv(sc, b0c, "visitors") == 1000 and dv(sh, b0h, "visitors") == 1000 and dv(sc, b0c, "paid") == 30 and dv(sh, b0h, "paid") == 50
      and dv(sc, b0c, "revenue") == 30 * 7900 and dv(sh, b0h, "revenue") == 50 * 8900 and sc["source"] == "orders", (sc, sh, b0c, b0h))
check("...refunded and withdrawn orders are counted as returned, not as revenue; test-mode payments apart",
      dv(sh, b0h, "returned") == 5 and dv(sh, b0h, "returned_revenue") == 5 * 8900 and dv(sh, b0h, "paid_test") == 2 and dv(sc, b0c, "returned") == 0, (sh, b0h))
check("...the 7 paid EVENTS the records do not back up are kept apart (paid_events) and the page warns that events and orders differ",
      dv(sh, b0h, "paid_events") == 7 and any(w["code"] == "events_differ" and w["variant"] == "high" for w in ea["warnings"]), (sh, ea["warnings"]))
zz, pp = z_two_sided(sc["paid"], sc["visitors"], sh["paid"], sh["visitors"])
check("...the comparison carries the textbook p-value for the totals, marked enough, and the difference in paid per visitor", cmp_["enough"] and abs(cmp_["p"] - round(pp, 4)) < 1e-9 and abs(cmp_["diff"] - (sh["paid"] / sh["visitors"] - sc["paid"] / sc["visitors"])) < 1e-9, (cmp_, pp))
check("...average order, revenue per visitor and the affected figures follow from the totals (every AU order is affected)",
      sh["avg_order"] == round(sh["revenue"] / sh["paid"]) and sh["revenue_per_visitor"] == round(sh["revenue"] / sh["visitors"]) and sh["hit_paid"] == sh["paid"] and sh["revenue_hit"] == sh["revenue"], sh)
check("...the test changes every price, so it is not a partial test and there is no affected-only comparison to ask for", ea["partial"] is False and ea["need_hit"] is None, ea["need_hit"])
check("...a verdict is not allowed yet: the planned size (hundreds of paid orders per arm) is not reached", cmp_["planned"] is False and ea["need"]["paid"] > 200, (cmp_, ea["need"]))
uu = ea["untokened"]
check("orders of the test's market made while it ran without a variant are counted apart (4 orders, test payments not among the paid ones)",
      uu["orders"] - u0["orders"] == 6 and uu["paid"] - u0["paid"] == 4, (uu, u0))
# revenue per visitor: Welch against an independent computation
def welch(n1, s1, q1, n2, s2, q2):
    m1, m2 = s1 / n1, s2 / n2
    v1, v2 = (q1 - n1 * m1 * m1) / (n1 - 1), (q2 - n2 * m2 * m2) / (n2 - 1)
    z = (m2 - m1) / math.sqrt(v1 / n1 + v2 / n2)
    return m2 - m1, z, math.erfc(abs(z) / math.sqrt(2))


got = A.rpv_test({"visitors": 1000, "amount_sum": 30 * 7900, "amount_sq": 30 * 7900 ** 2}, {"visitors": 1000, "amount_sum": 50 * 8900, "amount_sq": 50 * 8900 ** 2})
d_, z_, p_ = welch(1000, 30 * 7900, 30 * 7900 ** 2, 1000, 50 * 8900, 50 * 8900 ** 2)
check("revenue-per-visitor test: the difference, z and p of Welch's test (normal approximation) match an independent computation",
      got and abs(got["diff"] - d_) < 0.01 and abs(got["z"] - round(z_, 3)) < 1e-9 and abs(got["p"] - round(p_, 4)) < 1e-9, (got, (d_, z_, p_)))
check("...through the admin action it is there for the pair, with a difference that is revenue per visitor apart",
      cmp_["rpv"] and abs(cmp_["rpv"]["diff"] - (sh["amount_sum"] / sh["visitors"] - sc["amount_sum"] / sc["visitors"])) < 0.01 and 0 <= cmp_["rpv"]["p"] <= 1, cmp_["rpv"])
# fewer data: a p only with enough of it
c = A.compare({"variant": "control", "visitors": 100, "paid": 101, "rate_paid": 1.01}, {"variant": "extra10", "visitors": 100, "paid": 101, "rate_paid": 1.01})
check("more paid orders than visitors: no p, no crash, the reason is named", c["why"] == "paid_exceeds_visitors" and c["p"] is None, c)
check("z_test and need_sample never raise (paid above visitors, a rate of one, nothing at all)",
      A.z_test(130, 100, 130, 100) == (None, None) and A.z_test(0, 0, 0, 0) == (None, None) and A.need_sample(1.0)["paid"] > 0 and A.need_sample(0.9999)["visitors"] > 0 and A.need_sample(0)["visitors"] > 0)
adm("exp_stop", **{"key": "au_ladder_high"})

# =================================================================== 12. texts and misc
section("12. privacy, terms, docs")
priv = open(os.path.join(REPO, "src", "legal", "docs", "privacy.ts"), encoding="utf-8").read()
en_i, de_i = priv.index("const en: LegalDoc"), priv.index("const de: LegalDoc")
check("the privacy policy names the anonymous visitor id in local storage in English and in German (storage section)",
      "snapeyes.vid" in priv[en_i:de_i] and "snapeyes.vid" in priv[de_i:] and "price" in priv[en_i:de_i].split("snapeyes.vid")[1][:1500].lower() and "Preis" in priv[de_i:].split("snapeyes.vid")[1][:1500], "")
en_par = priv[en_i:de_i].split('"snapeyes.vid"', 1)[1].split("',", 1)[0]
de_par = priv[de_i:].split('„snapeyes.vid“', 1)[1].split("',", 1)[0]
check("the privacy paragraph says what the page does: only while a test runs for the viewed market, deleted when none runs, 90 days, a header and never the address, not stored by the application, the opt-out links, Global Privacy Control (en)",
      all(x in en_par for x in ("only while a price test is running", "deleted again as soon as no test runs", "90 days", "request header", "never in the address", "does not store it",
                                "/?pricetest=off", "/?pricetest=on", "Global Privacy Control", "snapeyes.notest")) and "never stored by the server" not in en_par, en_par[:300])
check("...and in German",
      all(x in de_par for x in ("solange", "wieder gelöscht", "90 Tagen", "Anfrage-Header", "nie in der Adresse", "speichert sie nicht", "/?pricetest=off", "/?pricetest=on", "Global Privacy Control", "snapeyes.notest")), de_par[:300])
check("...and the Australian edition inherits it (its patch only inserts a section after 'rights')", "id: 'storage'" not in priv[priv.index("const auEn"):] and "replace:" not in priv[priv.index("const auEn"):])
terms = open(os.path.join(REPO, "src", "legal", "docs", "terms.ts"), encoding="utf-8").read()
check("the terms' price sections say that the table is the standard price list and that a price test may apply (EU en, de and AU en, de)", terms.count("STANDARD_LIST_NOTE") >= 4, terms.count("STANDARD_LIST_NOTE"))
allsrc = []
for d in ("api", "src", "scripts"):
    for root, ds, fs in os.walk(os.path.join(REPO, d)):
        ds[:] = [x for x in ds if x not in ("__pycache__", "node_modules", "_assets")]
        for f in fs:
            if f.endswith((".py", ".ts", ".tsx", ".mjs", ".mts")):
                allsrc.append(os.path.join(root, f))
touched = subprocess.run(["git", "-C", REPO, "status", "--porcelain"], capture_output=True, text=True).stdout.split("\n")
files = [l[3:].strip() for l in touched if l.strip()]
bad_dash = []
for f in files:
    p = os.path.join(REPO, f)
    if os.path.isfile(p) and p.endswith((".py", ".ts", ".tsx", ".mjs", ".mts", ".md", ".html")):
        t = open(p, encoding="utf-8").read()
        if re.search("[\u2013\u2014]", t) and not f.startswith("dist"):
            # a file that had dashes before (another team's texts) is not judged: only lines this change added
            added = subprocess.run(["git", "-C", REPO, "diff", "-U0", "HEAD", "--", f], capture_output=True, text=True, encoding="utf-8").stdout
            if any(l.startswith("+") and re.search("[\u2013\u2014]", l) for l in added.split("\n")) or subprocess.run(["git", "-C", REPO, "ls-files", "--error-unmatch", f], capture_output=True).returncode != 0:
                bad_dash.append(f)
check("no em or en dash and no control character in anything this change adds", not bad_dash, bad_dash)

# =================================================================== 13. the page code, through Vite
section("13. the page code (src/shared/pricing.ts, checkout.ts)")
cap = {"definitions": DEFS, "base": {m: BASE_LADDER[m] for m in MK.MARKETS}, "plain": plain, "plain_running": CAP_PLAIN_RUN,
       "plain_both": plain_both, "replies": captured}
capfile = os.path.join(HERE, "captured.json")
with open(capfile, "w", encoding="utf-8") as f:
    json.dump(cap, f)
r = subprocess.run(["node", os.path.join(HERE, "client_exp.mjs"), HERE, capfile], cwd=REPO, capture_output=True, text=True, encoding="utf-8")
lines = [l for l in r.stdout.split("\n") if l.startswith(("PASS ", "FAIL "))]
for l in lines:
    ok = l.startswith("PASS ")
    check("page: " + l[5:].split("   <- ")[0], ok, l.split("   <- ")[1] if "   <- " in l else "")
check("the page-code script ran to the end", r.returncode == 0 and "passed" in r.stdout, r.stdout[-400:] + r.stderr[-800:])

# =================================================================== 14. a paid session survives edits, retirement, deletion
section("14. a paid session survives edits, retirement and deletion of its experiment")
if not A.is_running(KEY):
    adm("exp_start", **{"key": KEY})
tok14 = info(vid_for(KEY, "extra10", 14))[1]["exp_token"]


def definitions_changed(label, mutate, eyes=5):
    oo, kk, sid = fresh_session(tok14, eyes=eyes)
    want_amount = ladder_price(want_ladder(KEY, "extra10", "eu"), eyes, "studio_black")
    syn = json.loads(json.dumps(DEFS))
    mutate(syn)
    A.DEFS = syn
    A.invalidate()
    n_notes = len(owner_notes())
    try:
        cw, jw = pay_session(sid)
        cd, jd = adm("order", order=oo)
    finally:
        A.DEFS = saved
        A.invalidate()
    paid = read_json(f"orders/{oo}/paid.json") if exists(f"orders/{oo}/paid.json") else {}
    stc, stj = get(f"/api/order?o={oo}&k={kk}")
    mails = [m for m, _ in H.Fake.emails if oo in m.get("subject", "") and "confirmation" in m.get("subject", "")]
    c2, j2 = checkout(oo, kk, eyes, exp_token=tok14)
    check(f"{label}: the paid session is recorded at the price the customer was quoted (paid.json, the order page), with the ladder from its own metadata",
          cw == 200 and paid.get("amount_total") == want_amount and "amount_mismatch" not in paid and paid.get("experiment", {}).get("variant") == "extra10"
          and paid["experiment"]["prices"] == want_ladder(KEY, "extra10", "eu") and stj.get("amount") == want_amount, (cw, jw, paid, stj))
    check(f"{label}: the customer gets the confirmation and the owner no 'unexpected price' note; the same order cannot be paid twice",
          len(mails) == 1 and not any("unexpected price" in m["subject"] for m in owner_notes()[n_notes:]) and c2 == 409 and j2.get("reason") == "already_paid", (len(mails), c2, j2))
    return paid, (jd.get("experiment") if cd == 200 else None)


def _edit(syn):
    syn[KEY]["variants"]["extra10"]["prices"]["eu"]["each_further_eye"] = 900
    syn[KEY]["variants"]["control"]["prices"]["eu"]["each_further_eye"] = 1600      # the standard price moved too
    syn[KEY]["changes"] = ["each_further_eye"]


saved = A.DEFS
definitions_changed("ladders edited after the checkout was opened", _edit)
definitions_changed("experiment retired after the checkout was opened", lambda syn: syn[KEY].update(retired=1))
paid_del, ex_del = definitions_changed("experiment deleted after the checkout was opened", lambda syn: syn.pop(KEY))
check("the admin still reads an order of a deleted experiment: its variant and price list as recorded, marked as no longer defined",
      ex_del and ex_del["variant"] == "extra10" and ex_del["known"] is False and ex_del["prices"] == want_ladder(KEY, "extra10", "eu"), ex_del)
syn = json.loads(json.dumps(DEFS))
syn[KEY]["retired"] = 1
A.DEFS = syn
A.invalidate()
check("a retired experiment does not run, is not assigned, and is refused a start (409 retired)",
      not A.is_running(KEY) and "experiments" not in info(vid_for(KEY, "extra10", 14))[1] and adm("exp_start", **{"key": KEY})[1].get("reason") == "retired", A.running_keys())
check("...its control ladder may differ from the standard one (the owner adopted a winner), the unretired one may not",
      (lambda s2: (s2[KEY]["variants"]["control"]["prices"]["eu"].update(each_further_eye=1600), A.validate(s2) == [])[1])(json.loads(json.dumps(syn)))
      and (lambda s2: (s2[KEY]["variants"]["control"]["prices"]["eu"].update(each_further_eye=1600), s2[KEY].pop("retired"), A.validate(s2) != [])[2])(json.loads(json.dumps(syn))))
check("...and no loss or spread warning is made for it", A.loss_report(KEY) == [] and A.spread_report(KEY) == [])
check("...the summary does not list it as running although the state file still says on", next(x for x in A.summary() if x["key"] == KEY)["running"] is False and A.states()[KEY]["on"] is True)
vr, _ = view()
check("the page shows it as retired, with its numbers", vr[KEY]["retired"] is True and vr[KEY]["stats"], vr[KEY]["retired"])
A.DEFS = saved
A.invalidate()

# =================================================================== 15. the beacons' own budget
section("15. the beacons have a budget of their own")
saved_rate, saved_day = dict(E.RATE), E.EXP_DAY_MAX
tokb = info(vid_for(KEY, "extra10", 15))[1]["exp_token"]
E.RATE["exp"] = (5, 60.0)
E._SEEN["exp"] = []
E._SEEN["exp_today"] = 0
nb = len(event_keys())
res = [post("/api/checkout", {"exp_event": "visit", "exp_token": tokb, "market": "eu"})[1].get("counted") for _ in range(12)]
check("only the first 5 beacons of a minute are counted and stored; the rest are answered 200 and not counted", res.count(True) == 5 and len(event_keys()) - nb == 5, (res, len(event_keys()) - nb))
E.RATE["all"] = (2, 60.0)
E._SEEN["all"] = []
E._SEEN["exp"] = []
for _ in range(20):
    post("/api/checkout", {"exp_event": "visit", "exp_token": tokb, "market": "eu"})
ok_a = E.record("compose", style="studio_black", eyes=1)
ok_b = E.record("compose", style="studio_black", eyes=1)
check("a flood of beacons leaves the ordinary events' ceiling untouched (two ordinary events still go through)", ok_a and ok_b and len(E._SEEN["all"]) == 2, (ok_a, ok_b, E._SEEN["all"]))
E.RATE["exp"] = (0, 60.0)
E.RATE["all"] = (0, 60.0)
okp = E.record("exp", stage="paid", exp=KEY, variant="extra10", market="eu", eyes=3, amount=4997, currency="eur", live=True, hit=True)
okc = E.record("compose", style="studio_black", eyes=1)
check("a payment's event is never held back by the ceilings (an ordinary event is, with the ceiling at zero)", okp is True and okc is False, (okp, okc))
E.RATE.update(saved_rate)
E.RATE["exp"] = (10_000, 60.0)
E.EXP_DAY_MAX = 3
E._SEEN["exp"], E._SEEN["exp_today"], E._SEEN["exp_day"] = [], 0, time.strftime("%Y-%m-%d", time.gmtime())
res = [post("/api/checkout", {"exp_event": "visit", "exp_token": tokb, "market": "eu"})[1].get("counted") for _ in range(8)]
check("the daily cap of beacons holds (3 counted of 8)", res.count(True) == 3, res)
E.RATE.update(saved_rate)
E.EXP_DAY_MAX = saved_day
E._SEEN["exp"], E._SEEN["exp_today"] = [], 0
t0 = time.time()
E.RATE["exp"] = (10_000_000, 60.0)
post("/api/checkout", {"exp_event": "visit", "exp_token": tokb, "market": "eu"})
check("a beacon waits for its write for half a second at most (BEACON_WAIT), not the full second and a half", A.BEACON_WAIT <= 0.5 < E.WAIT)
check("events.record takes a _wait cap and never stores it as a field", "_wait" not in json.dumps(events_of()[-3:]))

# =================================================================== 16. the visitor path fails open
section("16. GET /api/checkout for a visitor fails open and does not pile up on the storage")
vid16 = vid_for(KEY, "extra10", 16)
saved_dec = A._decorate


def _dec_boom(*a, **k):
    raise RuntimeError("injected")


A._decorate = _dec_boom
c, j = info(vid16)
A._decorate = saved_dec
check("an unexpected error while deciding the variant leaves the reply as it was (200, open, standard prices, no token)", c == 200 and j.get("open") is True and "exp_token" not in j and j["prices"] == BASE_LADDER["eu"], j)
seen_to = []
saved_get = store.get_json


def _spy(path, *a, **k):
    seen_to.append((path, k.get("timeout")))
    return saved_get(path, *a, **k)


store.get_json = _spy
A.invalidate()
info(vid16)
store.get_json = saved_get
state_reads = [t for p, t in seen_to if p.startswith("ops/experiments/")]
check("a visitor's request reads the states with a 1 second timeout, the admin's read waits the usual 3", state_reads and all(t == A.VISITOR_TIMEOUT == 1.0 for t in state_reads), seen_to)
A.states(force=True)
seen_to.clear()
store.get_json = _spy
A.states(force=True)
store.get_json = saved_get
check("...and the admin's own read uses the longer timeout", all(t == 3.0 for p, t in seen_to if p.startswith("ops/experiments/")) and seen_to, seen_to)
# one refresh at a time: while a request refreshes an expired cache, the others get the old reading at once
A.states(force=True)
A._CACHE["t"] = 0.0
A._CACHE["busy"] = True


def _never(*a, **k):
    raise AssertionError("the storage must not be read while another request refreshes")


store.get_json = _never
try:
    got = A.states()
    served = got[KEY]["on"] is True
except AssertionError:
    served = False
finally:
    store.get_json = saved_get
    A._CACHE["busy"] = False
check("while one request refreshes an expired cache the others are served the old reading at once (no pile-up)", served)
store.get_json = lambda *a, **k: (_ for _ in ()).throw(store.StorageError("injected"))
A._CACHE["t"] = 0.0
A.states()
store.get_json = saved_get
check("a failed refresh leaves the 'refreshing' flag off (the next request can try again)", A._CACHE["busy"] is False)
A.invalidate()

# =================================================================== 17. the page data when the numbers fail
section("17. one experiment whose numbers fail never takes the page down")
saved_vs = A.variant_stats


def _vs_boom(tot, key, variant, currency, orders=None):
    if key == "au_ladder_high":
        raise ZeroDivisionError("injected")
    return saved_vs(tot, key, variant, currency, orders)


A.variant_stats = _vs_boom
c, j = adm("experiments")
A.variant_stats = saved_vs
byk = {e["key"]: e for e in j.get("experiments", [])} if c == 200 else {}
check("the page data still answers 200; the failed experiment has its state, variants, ladders and flags, the other one its numbers",
      c == 200 and byk["au_ladder_high"]["stats_error"] is True and byk["au_ladder_high"]["variants"] and "state" in byk["au_ladder_high"] and byk["au_ladder_high"]["stats"] == []
      and byk[KEY]["stats_error"] is False and byk[KEY]["stats"], (c, str(j)[:300]))
# more paid orders than visitors in an arm, through the real admin action
for var in variants_of(KEY):
    for _ in range(105):
        ev = E.build("exp", {"stage": "visit", "exp": KEY, "variant": var, "market": "eu"})
        write_json_path = local(f"ops/events/{day}/{time.strftime('%H%M%S', time.gmtime())}-{secrets.token_hex(6)}.json")
        with open(write_json_path, "w", encoding="utf-8") as f:
            json.dump(ev, f)
ops._DAYCACHE.clear()
vx, _ = view()
need_paid = 200
add_orders(KEY, "control", max(0, need_paid - stat(vx, KEY, "control")["paid"]), 5000, market="eu", currency="eur", eyes=3)
add_orders(KEY, "extra10", 12, 4000, market="eu", currency="eur", eyes=3)
ops._DAYCACHE.clear()
c, j = adm("experiments")
byk = {e["key"]: e for e in j.get("experiments", [])} if c == 200 else {}
cc = (byk.get(KEY) or {}).get("compare", [{}])[0]
check("more paid orders than visitors in an arm: the page answers 200 (no 400), names the reason and shows no p", c == 200 and cc.get("why") == "paid_exceeds_visitors" and cc.get("p") is None and cc.get("planned") in (True, False), (c, cc))
check("...the control's sample-size note still computes (a rate above one half is capped, never a division by zero)", byk[KEY]["need"]["paid"] > 0, byk[KEY]["need"])

# =================================================================== 18. starting without anything to count with
section("18. a test does not start silently when this deployment stores no events")
os.environ.pop("CRON_SECRET", None)
check("(setup) events are not stored without CRON_SECRET", E.retention_ok() is False)
c, j = adm("experiments")
check("the page data says so (collecting false)", c == 200 and j["collecting"] is False, (c, j.get("collecting")))
c, j = adm("exp_start", **{"key": "au_ladder_high"})
check("start without CRON_SECRET and without the owner's word: 409 stats_not_collected, and it does not start", c == 409 and j.get("reason") == "stats_not_collected" and not A.is_running("au_ladder_high"), (c, j))
c, j = adm("exp_start", **{"key": "au_ladder_high", "accept_no_stats": "yes"})
check("accept_no_stats must be the boolean true", c == 409 and not A.is_running("au_ladder_high"), (c, j))
c, j = adm("exp_start", **{"key": "au_ladder_high", "accept_no_stats": True})
check("with accept_no_stats true it starts", c == 200 and A.is_running("au_ladder_high"), (c, j))
adm("exp_stop", **{"key": "au_ladder_high"})
os.environ["CRON_SECRET"] = CRON
check("(teardown) events are stored again", E.retention_ok() is True)

# =================================================================== 19. the audit log names the test and what was accepted
section("19. audit lines")
aud = []
for d in sorted(os.listdir(local("ops/audit"))):
    for f in sorted(os.listdir(local(f"ops/audit/{d}"))):
        aud.append(read_json(f"ops/audit/{d}/{f}"))
exp_lines = [a for a in aud if a["action"] in ("exp_start", "exp_stop")]
refused = [a for a in exp_lines if not a["ok"]]
check("a refused start or stop of a known test names the test in its line (already_running, not_running, sells_at_loss, market_taken, stats_not_collected, retired)",
      {a["result"] for a in refused} >= {"already_running", "not_running", "sells_at_loss", "market_taken", "stats_not_collected", "retired"}
      and all(a.get("detail") in DEFS for a in refused if a["result"] in ("already_running", "not_running", "sells_at_loss", "stats_not_collected", "retired")), [(a["result"], a.get("detail")) for a in refused])
check("a start that accepted a loss says so in its line, and so does one that accepted missing statistics",
      any(a["ok"] and a.get("detail") == "au_ladder_high accept_loss" for a in exp_lines) and any(a["ok"] and a.get("detail") == "au_ladder_high accept_no_stats" for a in exp_lines), [(a["result"], a.get("detail")) for a in exp_lines if a["ok"]])
check("the page's log shows those lines (with their details)", any(l.get("detail") == "au_ladder_high accept_loss" for l in adm("experiments")[1]["log"]))

# =================================================================== 20. the build check and retired tests
section("20. the build check and a retired test")
RET = [
    ("a retired test may keep an old control ladder (the owner adopted a winner)",
     lambda s2, t: s2.replace('"markets": ["eu", "lt"],', '"markets": ["eu", "lt"],\n        "retired": 1,', 1).replace('"lt": {"one_eye_studio_black": 1997, "one_eye_art": 2497, "two_eyes": 3997, "each_further_eye": 1500}', '"lt": {"one_eye_studio_black": 1997, "one_eye_art": 2497, "two_eyes": 3997, "each_further_eye": 1400}', 1), 0, "price check ok"),
    ("retired must be 1 or left out", lambda s2, t: s2.replace('"markets": ["eu", "lt"],', '"markets": ["eu", "lt"],\n        "retired": 2,', 1), 1, "retired is 1 or left out"),
    ("an unknown field", lambda s2, t: s2.replace('"markets": ["eu", "lt"],', '"markets": ["eu", "lt"],\n        "flavour": 1,', 1), 1, "its fields must be exactly"),
]
if run_section("build"):
    for label, mut, want_code, needle in RET:
        code, out = build_check_on_copy(mut)
        check(f"build check: {label}", code == want_code and needle in out, out[-400:])

# =================================================================== 21. a verdict only at the planned size
section("21. significance: no verdict before the planned size; the affected-orders test for a partial test")
if not A.is_running(KEY):
    adm("exp_start", **{"key": KEY})


def synth_view(visits, orders_per_arm, amounts=(4500, 4000)):
    """admin_view over synthetic numbers: visits per arm (events) and live 3-eye orders per arm (order rows)."""
    counts = {"exp_stage": {f"{KEY}|control|visit": visits, f"{KEY}|extra10|visit": visits}, "exp_hit": {}, "exp_rev": {}, "exp_rev_hit": {}}
    row = lambda var, amt: {"order": "x", "state": "paid", "experiment": {"key": KEY, "variant": var}, "created_at": time.time(), "eyes": 3,
                            "style": "studio_black", "amount": amt, "currency": "EUR", "market": "eu", "paid": True, "live": True}
    orders = [row("control", amounts[0]) for _ in range(orders_per_arm[0])] + [row("extra10", amounts[1]) for _ in range(orders_per_arm[1])]
    vw = A.admin_view(lambda n: [(time.strftime("%Y-%m-%d", time.gmtime()), counts, True)], orders=orders, now=time.time(), collecting=True)
    return next(x for x in vw["experiments"] if x["key"] == KEY)


ex_small = synth_view(80000, (40, 60))
check("a partial test (only 3+ eyes change) is sized by the affected orders: need_hit is there, and the sample comes from the control's own rate once it has data",
      ex_small["partial"] is True and ex_small["need_hit"] and ex_small["need_hit"]["assumed"] is False and abs(ex_small["need_hit"]["rate"] - 40 / 80000) < 1e-9, ex_small["need_hit"])
cs = ex_small["compare"][0]
check("with a few affected orders the pair can be tested (p shown) but the verdict is not allowed yet (planned false)",
      cs["hit"] and cs["hit"]["enough"] is True and cs["hit"]["p"] is not None and cs["planned"] is False and cs["enough"] is True, cs)
ex_big = synth_view(80000, (800, 820))
cb = ex_big["compare"][0]
need_paid = ex_big["need_hit"]["paid"]
check(f"with at least the planned {need_paid} affected paid orders in every arm (800 and 820) the verdict is allowed (planned true)", cb["planned"] is True and 800 >= need_paid and cb["hit"]["enough"] and cb["rpv"] is not None, (cb, ex_big["need_hit"]))
check("...revenue per visitor is compared from the orders' amounts, control earning more per visitor here (the cheaper extra eye did not pay back)",
      cb["rpv"]["diff"] < 0 and ex_big["stats"][1]["revenue_per_visitor"] < ex_big["stats"][0]["revenue_per_visitor"], (cb["rpv"], [st["revenue_per_visitor"] for st in ex_big["stats"]]))
ex_none = synth_view(80000, (0, 0))
check("no orders at all: the page data is complete, need_hit is an assumption, nothing to compare", ex_none["need_hit"]["assumed"] is True and ex_none["compare"][0]["hit"]["enough"] is False, ex_none["need_hit"])
ex_mis = synth_view(50, (5, 5))
check("fewer than 100 visitors: no p anywhere, the reason is named", ex_mis["compare"][0]["why"] == "few_visitors" and ex_mis["compare"][0]["hit"]["why"] == "few_visitors", ex_mis["compare"][0])

# =================================================================== summary
bad = [n for n, ok in RESULTS if not ok]
print(f"\n{len(RESULTS) - len(bad)} of {len(RESULTS)} passed", flush=True)
if bad:
    print("FAILED:", *bad, sep="\n  ", flush=True)
sys.exit(1 if bad else 0)
