# -*- coding: utf-8 -*-
"""Price experiments: who gets which ladder, what Stripe charges for it, how a paid session is checked against it, the
anonymous events per variant and the data of the admin page "Kainų testai". The definitions (every variant's FULL ladder)
are api/_lib/experiments.py, the standard prices api/_lib/markets.py; nothing here holds a price.

What a visitor can and cannot do
  - The page asks GET /api/checkout WITHOUT any id, as it always did. Only while an experiment runs (the owner switched it
    on and ordering is open) that reply also says in "exp_markets" which markets run one. A visitor whose market is one of
    them (and who has not opted out) gets a random anonymous visitor id in the page's localStorage ("snapeyes.vid", 32 hex
    characters, no personal data, kept at most 90 days, removed again when no experiment runs for the visitor's market) and
    asks once more, with the id in the request HEADER X-Snapeyes-Visitor (never in a URL). The server derives the visitor's
    variant from that id alone (HMAC-SHA256 of experiment key and id under the ticket secret, so the same id always gets the
    same variant: sticky) and answers with the ladders of that variant plus a SIGNED assignment token
    ("x1.<payload>.<signature>", HMAC under a key derived from the ticket secret, valid 30 days). The server stores no id.
  - POST /api/checkout carries the token ("exp_token") and, optionally, the price the page showed ("shown"). The price is
    computed from the verified token only: the request cannot name a variant, a ladder or an amount. No token, a token
    that fails the signature, is too old, names an experiment that is not running (or not for the order's market) or a
    variant that does not exist: the standard ladder. When "shown" differs from what the server would charge, nothing is
    created: 409 price_changed with the price the visitor should see now, so the page never charges more or less than it
    showed.
  - The one thing a visitor can do is get a new random draw by clearing the site's data (a new id): that is the nature of
    an anonymous test, it costs the visitor effort for a price difference of a few euros, and the statistics count a
    changed browser as a new visitor.

What is recorded
  - order.json checkout.experiment, the Stripe session metadata (exp, exp_var), paid.json experiment {key, variant,
    prices}: for an order made under a variant only. An order made without a token has no experiment (the standard
    ladder), and orders made before this file existed stay as they are.
  - Anonymous events (api/_lib/events.py kind "exp": stage visit, preview, checkout, paid; experiment, variant, market;
    eyes, amount, currency for the last two): no visitor id, no order number, no personal data. The admin page adds
    them per variant.

The session of an experiment order carries the ladder it was priced on in its Stripe metadata (exp_lad: the four prices in
the smallest unit, written by the server at checkout). A paid session is refused (session_matches, so it is never recorded
as the order's payment, and the owner is told) when its amount is not the price of THAT ladder for the artwork it was made
for, or is not the amount the server wrote into its metadata (session_ok): never silently another amount. Because the
ladder travels with the session, editing, retiring or deleting an experiment while checkouts are open never makes a paid
session unrecordable (Stripe sessions live up to 24 hours): the order is recorded at the price the customer was quoted.
Still, the rule of thumb is: stop the test, wait 24 hours, then change prices or definitions.

The state (which experiment is on) is one small file per experiment in the private bucket, ops/experiments/<key>.json,
read through a per-instance cache of STATE_TTL seconds; an unreadable state means "off". Default: off everywhere.
Rotating SNAPEYES_TICKET_SECRET (or the Gemini key when it stands in for it) reshuffles every visitor's variant and voids
tokens: checkouts then get 409 price_changed or the standard ladder, never a wrong charge."""
import re, json, math, time, hmac, base64, hashlib, threading
from . import iris as L
from . import catalogue
from . import store
from . import events as E
from .markets import MARKETS, DEFAULT_MARKET
from . import experiments as X

DEFS = X.EXPERIMENTS
COSTS = X.COSTS
PRICE_KEYS = ("one_eye_studio_black", "one_eye_art", "two_eyes", "each_further_eye")
MAX_EYES = 8
STATE_DIR = "ops/experiments"
STATE_TTL = 15.0             # seconds an instance keeps what it read of the states (the admin's own change clears it)
STALE_MAX = 300.0            # a failed read falls back to the last good one this long; after that: off
TOKEN_KIND = "x1"
TOKEN_TTL = 30 * 86400
TOKEN_MAX = 1200
STATS_DAYS_MAX = 90          # api/_lib/ops.py STATS_DAYS_MAX: the events are read per day for at most this many days
MIN_ARM_PAID = 10            # a difference is tested only when every arm has this many paid orders ...
MIN_ARM_VISITORS = 100       # ... and this many visitors
SPREAD_WARN = 1.5            # ladders that differ by more than this factor for some artwork are flagged
NEED_REL_EFFECT = 0.25       # "enough data" means: able to see a 25 % relative difference in the paid rate ...
NEED_ALPHA_Z, NEED_POWER_Z = 1.959964, 0.841621      # ... at 95 % confidence and 80 % power
NEED_ASSUMED_RATE = 0.02     # the paid rate assumed for that estimate until the control arm has one of its own
NEED_ASSUMED_HIT = 0.15      # the share of orders a partial test (only 3+ eyes, say) is assumed to affect, until the control has data
VISITOR_HEADER = "x-snapeyes-visitor"    # the request header that carries the visitor id (never a URL)
VISITOR_TIMEOUT = 1.0        # seconds a visitor's request waits for the state of the experiments (the admin's read waits longer)

VID_RE = re.compile(r"^[a-f0-9]{32}$")
_CODE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,39}$")
_STAGES = ("visit", "preview")


# ----------------------------------------------------------------------------- the definitions
def get(key):
    d = DEFS.get(key) if isinstance(key, str) else None
    return d if isinstance(d, dict) else None


def check_key(key):
    """The experiment's key, or ClientError."""
    if not isinstance(key, str) or get(key) is None:
        raise L.ClientError("Choose one of the experiments.")
    return key


def base_ladder(market):
    return {k: int(MARKETS[market]["prices"][k]) for k in PRICE_KEYS}


def retired(key):
    """A retired experiment is kept for its history and the admin's numbers: never assigned, never started again, and its
    control ladder need not equal the standard one any more (the owner adopted a winner and changed markets.py)."""
    return bool((get(key) or {}).get("retired"))


def ladder_of(key, variant, market):
    """The variant's full ladder for a market (a copy), or None when the experiment, variant or market is not defined."""
    d = get(key)
    v = ((d or {}).get("variants") or {}).get(variant) if isinstance(variant, str) else None
    p = ((v or {}).get("prices") or {}).get(market) if isinstance(market, str) else None
    if not isinstance(p, dict):
        return None
    try:
        return {k: int(p[k]) for k in PRICE_KEYS}
    except (KeyError, TypeError, ValueError):
        return None


def ladder_price(ladder, eyes, style):
    """The price of n eyes in a style on a ladder: api/_lib/pay.py price_cents, the same rule (src/shared/markets.ts
    priceMinor and scripts/check_prices.mjs priceRule restate it; the build compares all three)."""
    n = int(eyes)
    if not 1 <= n <= MAX_EYES:
        raise L.ClientError(f"An artwork holds 1 to {MAX_EYES} eyes.")
    if n == 1:
        return int(ladder["one_eye_studio_black"] if catalogue.is_black(style) else ladder["one_eye_art"])
    return int(ladder["two_eyes"]) + (n - 2) * int(ladder["each_further_eye"])


def currency_of_experiment(key):
    d = get(key) or {}
    ms = [m for m in d.get("markets") or [] if m in MARKETS]
    return MARKETS[ms[0]]["currency"] if ms else MARKETS[DEFAULT_MARKET]["currency"]


def differs(key, market, eyes, style):
    """Does the price of this artwork differ between the variants of the experiment (an "affected order")?"""
    d = get(key)
    if d is None:
        return False
    try:
        prices = {ladder_price(ladder_of(key, v, market), eyes, style) for v in d["variants"]
                  if ladder_of(key, v, market) is not None}
    except (L.ClientError, TypeError, KeyError, ValueError):
        return False
    return len(prices) > 1


def validate(defs=None, markets=None):
    """Every problem of the definitions as sentences ([] when sound): the rules of experiments.py, the same ones
    scripts/check_experiments.mjs applies at build time (the build is the gate; this is for the tests and the admin)."""
    defs = DEFS if defs is None else defs
    markets = MARKETS if markets is None else markets
    out = []
    for key, d in defs.items():
        at = f"experiment {key!r}"
        if not re.fullmatch(r"[a-z][a-z0-9_]{2,39}", key):
            out.append(f"{at}: the key must be lower case letters, digits and _")
        ms = d.get("markets") or []
        if not ms or any(m not in markets for m in ms):
            out.append(f"{at}: markets must be a non-empty list of markets of markets.py")
            continue
        if len({markets[m]["currency"] for m in ms}) != 1:
            out.append(f"{at}: its markets must share one currency")
        vs = d.get("variants") or {}
        if "control" not in vs or len(vs) < 2:
            out.append(f"{at}: needs a variant 'control' and at least one other")
        if sorted(d.get("split") or {}) != sorted(vs) or sum((d.get("split") or {}).values()) != 100 \
                or any(not isinstance(x, int) or x <= 0 for x in (d.get("split") or {}).values()):
            out.append(f"{at}: split must give every variant a whole percent above 0, adding up to 100")
        for name, v in vs.items():
            if not _CODE.fullmatch(name):
                out.append(f"{at}: variant name {name!r} is not a code")
            for m in ms:
                p = ((v or {}).get("prices") or {}).get(m)
                if not isinstance(p, dict) or sorted(p) != sorted(PRICE_KEYS) or any(
                        not isinstance(p[k], int) or isinstance(p[k], bool) or p[k] <= 0 for k in PRICE_KEYS):
                    out.append(f"{at} variant {name!r} market {m!r}: a full ladder of the four prices is required")
                    continue
                if name == "control" and not d.get("retired") and p != {k: markets[m]["prices"][k] for k in PRICE_KEYS}:
                    out.append(f"{at}: the control ladder of {m!r} is not the standard one of markets.py")
        if d.get("retired") not in (None, 0, 1):
            out.append(f"{at}: 'retired' is 1 or left out")
        for m in ms:
            changed = sorted(k for k in PRICE_KEYS if len({(v["prices"].get(m) or {}).get(k) for v in vs.values()}) > 1)
            if changed != sorted(d.get("changes") or []):
                out.append(f"{at} market {m!r}: the ladders differ in {changed}, 'changes' says {sorted(d.get('changes') or [])}")
    return out


# ----------------------------------------------------------------------------- the on/off state
_LOCK = threading.Lock()
_CACHE = {"t": 0.0, "states": {}, "good": None, "good_t": 0.0, "busy": False}


def _blank():
    return {"on": False, "since": None, "started_at": None, "stopped_at": None, "updated": None, "runs": []}


def _norm(rec):
    out = _blank()
    if not isinstance(rec, dict):
        return out
    out["on"] = rec.get("on") is True
    for k in ("since", "started_at", "stopped_at", "updated"):
        v = rec.get(k)
        out[k] = int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None
    runs = rec.get("runs") if isinstance(rec.get("runs"), list) else []
    out["runs"] = [{"start": r.get("start"), "stop": r.get("stop")} for r in runs[-50:] if isinstance(r, dict)]
    return out


def invalidate():
    with _LOCK:
        _CACHE["t"] = 0.0


def states(force=False, timeout=3.0):
    """{key: state} of every defined experiment, read through a cache of STATE_TTL seconds. When the storage cannot be
    read, the last good reading is used for up to STALE_MAX seconds (a blip must not flip a running experiment off for
    some visitors), and after that every experiment counts as off (the safe side: everybody pays the standard ladder).
    While one request refreshes an expired cache, the others are served the old reading at once (no pile-up on the
    storage); `timeout` is what one read of a state file may take."""
    now = time.time()
    with _LOCK:
        have = set(_CACHE["states"]) == set(DEFS)
        if not force and have and now - _CACHE["t"] < STATE_TTL:
            return dict(_CACHE["states"])
        if not force and have and _CACHE["busy"] and _CACHE["good"] is not None:
            return dict(_CACHE["states"])
        _CACHE["busy"] = True
    got = {}
    try:
        try:
            if store.configured():
                for key in DEFS:
                    got[key] = _norm(store.get_json(f"{STATE_DIR}/{key}.json", timeout=timeout, retry=False))
            else:
                got = {key: _blank() for key in DEFS}
            good = True
        except Exception as e:  # noqa: unreadable state: the last good reading for a while, else off
            good = False
            with _LOCK:
                last, age = _CACHE.get("good"), now - _CACHE.get("good_t", 0.0)
            keep = bool(last) and set(last) == set(DEFS) and age < STALE_MAX
            got = dict(last) if keep else {key: _blank() for key in DEFS}
            print(f"snapeyes experiments: state not readable ({type(e).__name__}): "
                  f"{'the reading of %d s ago is used' % age if keep else 'all off'}", flush=True)
        with _LOCK:
            _CACHE["t"], _CACHE["states"] = time.time(), got
            if good:
                _CACHE["good"], _CACHE["good_t"] = dict(got), time.time()
    finally:
        with _LOCK:
            _CACHE["busy"] = False
    return dict(got)


def running_keys(timeout=3.0):
    """The experiments that run now: switched on and not retired."""
    st = states(timeout=timeout)
    return [k for k in DEFS if st.get(k, {}).get("on") is True and not retired(k)]


def is_running(key):
    return key in running_keys()


def _write_state(key, rec):
    store.put(f"{STATE_DIR}/{key}.json", store.json_bytes(dict(rec, v=1, key=key)), "application/json", upsert=True,
              timeout=8.0)
    invalidate()


def conflict(key):
    """The running experiment that shares a market with this one (only one experiment per market at a time), or None."""
    mine = set((get(key) or {}).get("markets") or [])
    for other in running_keys():
        if other != key and mine & set(DEFS[other].get("markets") or []):
            return other
    return None


def start(key, accept_loss=False):
    """Switch an experiment on. Answers 409 when it already runs, when another running one shares a market, and when a
    ladder would sell at a loss (unless accept_loss). Returns its new state."""
    check_key(key)
    if not store.configured():
        raise store.StorageNotConfigured(store.problem())
    if retired(key):
        raise store.Answer(409, "retired", "This experiment is retired: add a new one (a new key) instead.", False)
    cur = states(force=True)[key]
    if cur["on"]:
        raise store.Answer(409, "already_running", "This experiment is already running.", False)
    other = conflict(key)
    if other:
        raise store.Answer(409, "market_taken", "Another experiment already runs in one of its markets: stop it first.",
                           False, other=other)
    loss = loss_report(key)
    if loss and not accept_loss:
        raise store.Answer(409, "sells_at_loss", "A variant would sell at a loss (see the warning).", False,
                           rows=loss[:6], count=len(loss))
    now = int(time.time())
    rec = dict(cur, on=True, since=cur["since"] or now, started_at=now, stopped_at=None, updated=now,
               runs=(cur["runs"] + [{"start": now, "stop": None}])[-50:])
    _write_state(key, rec)
    return _norm(rec)


def stop(key):
    """Switch an experiment off (409 when it is not running). Sessions already open keep their variant's price: their
    payment is still checked and recorded (a stopped experiment only stops new assignments)."""
    check_key(key)
    if not store.configured():
        raise store.StorageNotConfigured(store.problem())
    cur = states(force=True)[key]
    if not cur["on"]:
        raise store.Answer(409, "not_running", "This experiment is not running.", False)
    now = int(time.time())
    runs = [dict(r) for r in cur["runs"]]
    if runs and runs[-1].get("stop") is None:
        runs[-1]["stop"] = now
    rec = dict(cur, on=False, stopped_at=now, updated=now, runs=runs)
    _write_state(key, rec)
    return _norm(rec)


# ----------------------------------------------------------------------------- assignment and the signed token
def _key():
    """The signing key: derived from the ticket secret under its own label, so a token is never an order, unlock or
    admin ticket and none of those is a token."""
    return hmac.new(L._ticket_secret(), b"snapeyes-experiments-v1", hashlib.sha256).digest()


def bucket(vid, key):
    """0..9999: where this visitor falls for this experiment (the same id and key always give the same number)."""
    h = hmac.new(_key(), f"assign:{key}:{vid}".encode("ascii", "replace"), hashlib.sha256).digest()
    return int.from_bytes(h[:8], "big") % 10000


def assign(vid, key):
    """The variant of a visitor id in an experiment, by the split (percent, in name order)."""
    b, acc, last = bucket(vid, key), 0, None
    for name in sorted(DEFS[key]["split"]):
        acc += int(DEFS[key]["split"][name]) * 100
        last = name
        if b < acc:
            return name
    return last


def _b64(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _unb64(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def sign(assigned, now=None):
    """A signed assignment token for {experiment key: variant}."""
    payload = {"a": dict(sorted(assigned.items())), "t": int(time.time() if now is None else now)}
    body = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    sig = hmac.new(_key(), f"{TOKEN_KIND}.{body}".encode("ascii"), hashlib.sha256).hexdigest()[:32]
    return f"{TOKEN_KIND}.{body}.{sig}"


def verify(tok, now=None):
    """{experiment key: variant} of a token that is ours, unaltered and not older than TOKEN_TTL, else None. Says nothing
    about whether those experiments run (assignment() does)."""
    try:
        if not isinstance(tok, str) or len(tok) > TOKEN_MAX:
            return None
        kind, body, sig = tok.split(".")
        if kind != TOKEN_KIND or not re.fullmatch(r"[A-Za-z0-9_-]{2,1100}", body) or not re.fullmatch(r"[a-f0-9]{32}", sig):
            return None
        want = hmac.new(_key(), f"{kind}.{body}".encode("ascii"), hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(sig, want):
            return None
        payload = json.loads(_unb64(body).decode("utf-8"))
        t, a = payload.get("t"), payload.get("a")
        now = time.time() if now is None else now
        if not isinstance(t, int) or isinstance(t, bool) or t > now + 300 or now - t > TOKEN_TTL or not isinstance(a, dict):
            return None
        return {k: v for k, v in a.items() if isinstance(k, str) and isinstance(v, str) and _CODE.fullmatch(k)
                and _CODE.fullmatch(v)}
    except Exception:  # noqa: any malformed token is simply no token
        return None


def assignment(token, market):
    """{"key", "variant"} when the token is valid and names a RUNNING experiment for this market (and a variant that has
    a ladder for it), else None: the standard ladder. The first running experiment in file order wins (only one may run
    per market, start())."""
    asg = verify(token)
    if not asg or market not in MARKETS:
        return None
    for key in running_keys():
        v = asg.get(key)
        if v is not None and market in (DEFS[key].get("markets") or []) and ladder_of(key, v, market) is not None:
            return {"key": key, "variant": v}
    return None


def vid_of(req):
    """The visitor id a GET /api/checkout request carries in its header X-Snapeyes-Visitor, or None (a missing or malformed
    one: not part of any experiment). Never read from the URL: a page keeps the id out of every address."""
    try:
        h = getattr(req, "headers", None)
        v = h.get(VISITOR_HEADER) if h is not None and hasattr(h, "get") else None
        v = v.strip() if isinstance(v, str) else ""
        return v if VID_RE.fullmatch(v) else None
    except Exception:  # noqa
        return None


def decorate(out, vid):
    """The reply of GET /api/checkout for a visitor. Nothing is changed (the reply is byte for byte the old one) when nothing
    runs or ordering is closed. While an experiment runs and ordering is open:
      - a request WITHOUT a valid visitor id only learns which markets run an experiment ("exp_markets"), so the page knows
        whether it may create an id at all (src/shared/pricing.ts);
      - a request with a valid id gets the ladders of the visitor's variant for the markets the experiments cover (in
        "markets" and, for the default market, "prices"), the variants themselves ("experiments", with the run number of
        each) and the signed token ("exp_token").
    Fail open: any surprise here leaves the reply as it was (the standard ladder, which the checkout's "shown" check keeps
    safe), and never closes ordering."""
    try:
        return _decorate(out, vid)
    except Exception as e:  # noqa: the experiment must never cost a visitor the ordering check
        print(f"snapeyes experiments: decorate failed ({type(e).__name__}): reply left as it was", flush=True)
        return out


def _decorate(out, vid):
    if not isinstance(out, dict) or out.get("open") is not True:
        return out
    run = running_keys(VISITOR_TIMEOUT)
    if not run:
        return out
    if not isinstance(vid, str) or not VID_RE.fullmatch(vid):
        mk = sorted({m for k in run for m in (DEFS[k].get("markets") or [])})
        if mk:
            out["exp_markets"] = mk
        return out
    st = states(timeout=VISITOR_TIMEOUT)
    asg = {k: assign(vid, k) for k in run}
    markets = out.get("markets") if isinstance(out.get("markets"), dict) else {}
    seen = []
    for m in markets:
        for k in run:
            lad = ladder_of(k, asg[k], m) if m in (DEFS[k].get("markets") or []) else None
            if lad is not None:
                markets[m] = dict(markets[m], prices=lad)
                if m == out.get("market"):
                    out["prices"] = dict(lad)
                if k not in seen:
                    seen.append(k)
                break
    if not seen:
        return out
    out["experiments"] = [{"key": k, "variant": asg[k], "markets": [m for m in DEFS[k]["markets"] if m in markets],
                           "run": int((st.get(k) or {}).get("started_at") or 0)} for k in seen]
    out["exp_token"] = sign({k: asg[k] for k in seen})
    return out


# ----------------------------------------------------------------------------- checkout
def price_cents(exp, eyes, style, market):
    """What the server charges for an assignment (exp from assignment())."""
    return ladder_price(ladder_of(exp["key"], exp["variant"], market), eyes, style)


def current_ladder(exp, market):
    return ladder_of(exp["key"], exp["variant"], market) if exp else base_ladder(market)


def check_shown(body, market, amount, exp):
    """The price the page says it showed ("shown", in the market's smallest unit) must be what would be charged. If not,
    nothing is created: 409 price_changed with the current ladder, so the page shows it and asks again. Requests
    without "shown" (older pages) are charged as priced."""
    shown = body.get("shown") if isinstance(body, dict) else None
    if shown is None or (isinstance(shown, int) and not isinstance(shown, bool) and shown == amount):
        return
    extra = {"amount": int(amount), "prices": current_ladder(exp, market), "market": market,
             "currency": MARKETS[market]["currency"].upper()}
    if exp:
        extra["exp_token"] = sign({exp["key"]: exp["variant"]})
    raise store.Answer(409, "price_changed", "The price changed while you were looking. Please check the new price.",
                       False, **extra)


def ladder_text(lad):
    """A ladder as the session metadata holds it: the four prices in the smallest unit, comma separated (exp_lad)."""
    return ",".join(str(int(lad[k])) for k in PRICE_KEYS)


def _lad_from_meta(m):
    """The ladder a session's metadata carries (exp_lad), or None when it carries none or a malformed one."""
    raw = m.get("exp_lad") if isinstance(m, dict) else None
    if not isinstance(raw, str) or not re.fullmatch(r"[0-9]{1,9}(,[0-9]{1,9}){3}", raw):
        return None
    parts = [int(x) for x in raw.split(",")]
    if any(x <= 0 for x in parts):
        return None
    return dict(zip(PRICE_KEYS, parts))


def metadata(exp, market):
    """The Stripe session metadata of an experiment order ({} for the standard ladder): the experiment, the variant and the
    ladder the price was taken from, so the payment can always be checked against what the customer was quoted."""
    if not exp:
        return {}
    lad = ladder_of(exp["key"], exp["variant"], market)
    out = {"exp": exp["key"], "exp_var": exp["variant"]}
    if lad is not None:
        out["exp_lad"] = ladder_text(lad)
    return out


def checkout_block(exp, market):
    """order.json checkout.experiment: the variant and the price list that applied to this checkout."""
    if not exp:
        return None
    return {"key": exp["key"], "variant": exp["variant"], "prices": ladder_of(exp["key"], exp["variant"], market)}


def _meta(sess):
    return sess.get("metadata") if isinstance(sess, dict) and isinstance(sess.get("metadata"), dict) else {}


def session_exp(sess):
    """(key, variant) a session's metadata names, or None when it names none (the standard ladder)."""
    m = _meta(sess)
    key, var = m.get("exp"), m.get("exp_var")
    if key in (None, "") and var in (None, ""):
        return None
    return (str(key)[:40], str(var)[:40])


def session_ok(sess):
    """A session made under an experiment: is it one the server could have made? Its amount is the price of the ladder its
    own metadata carries (exp_lad, written at checkout) for the artwork in its metadata, and is the amount the server
    wrote into its metadata. So a payment is never refused because an experiment was stopped, edited, retired or deleted
    after the checkout was opened. While the experiment is still defined, it must also be one that runs in the session's
    market. A session of the standard ladder passes. (A session without exp_lad, which no deployed server makes, is checked
    against the definitions as they are now.)"""
    e = session_exp(sess)
    if e is None:
        return True
    key, var = e
    m = _meta(sess)
    market = m.get("market") or DEFAULT_MARKET
    if market not in MARKETS:
        return False
    d = get(key)
    if d is not None and market not in (d.get("markets") or []):
        return False
    lad = _lad_from_meta(m)
    if lad is None:
        if d is None or var not in (d.get("variants") or {}):
            return False
        lad = ladder_of(key, var, market)
    amount = sess.get("amount_total")
    try:
        eyes, style = int(m.get("eyes")), m.get("style")
        if lad is None or not catalogue.known(style) or not isinstance(amount, int) or isinstance(amount, bool):
            return False
        if amount != ladder_price(lad, eyes, style):
            return False
        priced = m.get("amount")
        return priced in (None, "") or (str(priced).isdigit() and int(priced) == amount)
    except (TypeError, ValueError, L.ClientError):
        return False


def paid_record(sess, spec):
    """What paid.json keeps of the experiment: {key, variant, prices} (the ladder that applied, taken from the session's own
    metadata, for the emails and the admin), or None."""
    e = session_exp(sess)
    if e is None:
        return None
    lad = _lad_from_meta(_meta(sess)) or ladder_of(e[0], e[1], (spec or {}).get("market") or DEFAULT_MARKET)
    return {"key": e[0], "variant": e[1], "prices": lad}


def expected_price(rec, spec):
    """The price the ladder in a paid.json experiment record gives the paid spec, or None."""
    try:
        lad = rec.get("prices") if isinstance(rec, dict) else None
        return ladder_price(lad, spec["eyes"], spec["style"]) if isinstance(lad, dict) else None
    except (KeyError, TypeError, ValueError, L.ClientError):
        return None


def note_refused(order, sess):
    """The owner is told (once per session) that a session of ours for this order was PAID at an amount or under an
    experiment the server never priced: it is not recorded as the order's payment and nothing is made."""
    from . import pay
    sid = str(sess.get("id") or "")
    m = _meta(sess)
    return pay.owner_note(order, "wrong_price_" + pay._order_tag(sid),
                          f"SnapEyes: order {order} was paid at an unexpected price, please check and refund",
                          f"Stripe reports a PAID Checkout Session {sid} for order {order} "
                          f"({pay.amount_text(sess.get('amount_total') or 0, 'en', sess.get('currency'))}); it was made "
                          f"for price experiment {str(m.get('exp') or '')[:40]!r} variant {str(m.get('exp_var') or '')[:40]!r}, "
                          f"market {str(m.get('market') or DEFAULT_MARKET)[:8]!r}, {str(m.get('eyes') or '')[:2]} eye(s), "
                          f"style {str(m.get('style') or '')[:20]!r}, and that is not a price the server sets.\n"
                          f"It is NOT recorded as the order's payment and nothing is made. Check the session in the Stripe "
                          f"Dashboard, refund it (Payments, search {sess.get('payment_intent') or sid}, Refund) and write "
                          f"to the customer ({(sess.get('customer_details') or {}).get('email') or 'email at Stripe'}).\n"
                          f"Status: python scripts/order_admin.py status {order}\n")


# ----------------------------------------------------------------------------- events
def _rec(**f):
    try:
        return E.record("exp", **f)
    except Exception:  # noqa: an event never costs a request
        return False


BEACON_WAIT = 0.5            # seconds a visit or preview beacon waits for its write (the page never waits for it at all)


def note_checkout(exp, market, eyes, style, amount):
    if exp:
        _rec(stage="checkout", exp=exp["key"], variant=exp["variant"], market=market, eyes=int(eyes), amount=int(amount),
             currency=MARKETS[market]["currency"], hit=differs(exp["key"], market, eyes, style))


def note_paid(paid):
    """The event of a first payment of an experiment order (record_paid, once: paid.json is created once)."""
    ex = paid.get("experiment") if isinstance(paid, dict) else None
    if not isinstance(ex, dict) or not isinstance(ex.get("key"), str) or get(ex["key"]) is None:
        return
    spec = paid.get("spec") if isinstance(paid.get("spec"), dict) else {}
    market = paid.get("market") or spec.get("market") or DEFAULT_MARKET
    _rec(stage="paid", exp=ex["key"], variant=ex.get("variant"), market=market, eyes=spec.get("eyes"),
         amount=paid.get("amount_total"), currency=str(paid.get("currency") or "").lower(),
         live=paid.get("livemode") is True, hit=differs(ex["key"], market, spec.get("eyes") or 1, spec.get("style") or ""))


def beacon(body):
    """POST /api/checkout {exp_event: "visit" | "preview", exp_token, market[, eyes, style]}: the page tells us once per
    visitor and experiment that it showed the variant's prices (visit) and that a preview was made (preview). Counted only
    for a valid token of a running experiment in the given market; anything else is answered 200 and ignored. The page
    sends each event once per browser; the server keeps no id."""
    ev = body.get("exp_event")
    market = body.get("market")
    if ev not in _STAGES or not isinstance(market, str):
        raise L.ClientError("Unknown event.")
    exp = assignment(body.get("exp_token"), market)
    if exp is None:
        return {"ok": True, "counted": False}
    f = {"stage": ev, "exp": exp["key"], "variant": exp["variant"], "market": market}
    if ev == "preview":
        eyes, style = body.get("eyes"), body.get("style")
        if isinstance(eyes, int) and not isinstance(eyes, bool) and 1 <= eyes <= MAX_EYES:
            f["eyes"] = eyes
            if catalogue.known(style):
                f["hit"] = differs(exp["key"], market, eyes, style)
    return {"ok": True, "counted": bool(_rec(_wait=BEACON_WAIT, **f))}


# ----------------------------------------------------------------------------- the emails
ROW_LABEL = {"en": "Price list that applied to your order", "de": "Preisliste, die für Ihre Bestellung galt",
             "lt": "Jūsų užsakymui taikytas kainoraštis", "hu": "A megrendelésére alkalmazott árlista"}
ROW_TEXT = {
    "en": "one eye Studio Black {b}, one eye on an art background {a}, two eyes {t}, each further eye +{f} (up to {m} eyes)",
    "de": "ein Auge Studio Black {b}, ein Auge mit Kunsthintergrund {a}, zwei Augen {t}, jedes weitere Auge +{f} (bis zu {m} Augen)",
    "lt": "viena akis Studio Black {b}, viena akis su meniniu fonu {a}, dvi akys {t}, kiekviena papildoma akis +{f} (iki {m} akių)",
    "hu": "egy szem Studio Black {b}, egy szem művészi háttérrel {a}, két szem {t}, minden további szem +{f} (legfeljebb {m} szem)",
}


def price_list_row(paid, lang):
    """(label, text) for an order made under a price experiment: the full price list that applied to it, so the order
    confirmation (the durable medium) is complete although the terms print the standard list. None for the standard list.
    The languages are ROW_LABEL and ROW_TEXT; any other one reads English."""
    ex = paid.get("experiment") if isinstance(paid, dict) else None
    lad = ex.get("prices") if isinstance(ex, dict) else None
    if not isinstance(lad, dict) or any(not isinstance(lad.get(k), int) for k in PRICE_KEYS):
        return None
    from . import pay
    cur = paid.get("currency")
    t = lambda c: pay.price_text(c, lang, cur)
    l = lang if lang in ROW_TEXT else "en"
    return ROW_LABEL[l], ROW_TEXT[l].format(b=t(lad["one_eye_studio_black"]), a=t(lad["one_eye_art"]), t=t(lad["two_eyes"]),
                                            f=t(lad["each_further_eye"]), m=MAX_EYES)


def insert_price_list_row(rows, paid, lang):
    """Put price_list_row after the price row of a confirmation email's "Your order" rows (in place; nothing for the
    standard list). rows: the (label, text) list pay.confirmation_mail builds."""
    row = price_list_row(paid, lang)
    if row:
        at = next((i for i, r in enumerate(rows) if r[0] in ("Preis", "Price", "Kaina", "Ár")), len(rows) - 1)
        rows.insert(at + 1, row)


# ----------------------------------------------------------------------------- what the admin shows of an order
def order_view(paid, rec):
    """{key, variant, title, label, prices, source} of an order's experiment (paid.json, else the checkout of order.json),
    or None."""
    ex, source = None, None
    if isinstance(paid, dict) and isinstance(paid.get("experiment"), dict):
        ex, source = paid["experiment"], "paid"
    else:
        co = rec.get("checkout") if isinstance(rec, dict) else None
        if isinstance(co, dict) and isinstance(co.get("experiment"), dict):
            ex, source = co["experiment"], "checkout"
    if ex is None:
        return None
    key, var = str(ex.get("key") or "")[:40], str(ex.get("variant") or "")[:40]
    d = get(key) or {}
    return {"key": key, "variant": var, "title": d.get("title"), "label": (((d.get("variants") or {}).get(var)) or {}).get("label"),
            "prices": ex.get("prices") if isinstance(ex.get("prices"), dict) else None, "source": source,
            "known": bool(d and var in (d.get("variants") or {}))}


def summary():
    """The experiments for the admin summary: key, title, markets and whether each is running."""
    st = states()
    return [{"key": k, "title": d.get("title"), "markets": d.get("markets"),
             "running": st.get(k, {}).get("on") is True and not d.get("retired"),
             "since": st.get(k, {}).get("since"), "started_at": st.get(k, {}).get("started_at")} for k, d in DEFS.items()]


# ----------------------------------------------------------------------------- the loss check
def net_minor(currency, price_minor, eyes, costs=None):
    """What is left of a price after Stripe's fee and the image work, in the currency's smallest unit (negative: a loss).
    Estimates with the constants of experiments.py COSTS (round numbers, on the safe side)."""
    c = COSTS if costs is None else costs
    price = price_minor / 100.0
    cost = (eyes * c["unit_usd_per_eye"] * c["per_usd"][currency] + c["fee_fixed_eur"] * c["per_eur"][currency]
            + price * c["fee_pct"][currency] / 100.0)
    return round((price - cost) * 100.0)


def loss_report(key, defs=None, costs=None):
    """The (variant, market, eyes, style) combinations that would sell at a loss, as dicts with price and net."""
    defs = DEFS if defs is None else defs
    d = defs.get(key) or {}
    rows = []
    if d.get("retired"):
        return rows          # a retired test never runs again: its old ladders are history
    for name, v in (d.get("variants") or {}).items():
        for m, p in (v.get("prices") or {}).items():
            cur = MARKETS[m if m in MARKETS else DEFAULT_MARKET]["currency"]
            for eyes in range(1, MAX_EYES + 1):
                for cls in catalogue.PRICE_CLASSES:
                    if eyes > 1 and cls != "black":
                        continue
                    style = catalogue.class_style(cls)
                    price = ladder_price(p, eyes, style)
                    net = net_minor(cur, price, eyes, costs)
                    if net < 0:
                        rows.append({"variant": name, "market": m, "eyes": eyes, "style": style, "price": price, "net": net})
    return rows


def spread_report(key, defs=None):
    """The largest price ratio between variants over the artworks of a market: [{market, eyes, style, ratio}] above
    SPREAD_WARN (ladders this far apart are noticed, and one of them may be far off the right price)."""
    defs = DEFS if defs is None else defs
    d = defs.get(key) or {}
    rows = []
    if d.get("retired"):
        return rows
    for m in d.get("markets") or []:
        for eyes in range(1, MAX_EYES + 1):
            for cls in catalogue.PRICE_CLASSES:
                if eyes > 1 and cls != "black":
                    continue
                style = catalogue.class_style(cls)
                ps = [ladder_price(v["prices"][m], eyes, style) for v in d["variants"].values() if m in v.get("prices", {})]
                if ps and min(ps) > 0 and max(ps) / min(ps) > SPREAD_WARN:
                    rows.append({"market": m, "eyes": eyes, "style": style, "ratio": round(max(ps) / min(ps), 2)})
    return rows


# ----------------------------------------------------------------------------- statistics
def _phi_upper(z):
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def z_test(x1, n1, x2, n2):
    """Two-sided two-proportion z-test (pooled): (z, p), or (None, None) when it cannot be computed. More paid than visitors
    in an arm (the visitor count is best effort) is clamped to the visitors, so this never raises."""
    if n1 <= 0 or n2 <= 0:
        return None, None
    x1, x2 = min(max(x1, 0), n1), min(max(x2, 0), n2)
    p = (x1 + x2) / (n1 + n2)
    var = p * (1 - p) * (1 / n1 + 1 / n2)
    if not var > 0:
        return None, None
    z = (x2 / n2 - x1 / n1) / math.sqrt(var)
    return z, 2 * _phi_upper(abs(z))


def need_sample(rate, rel=NEED_REL_EFFECT):
    """Visitors per arm needed to see a relative change `rel` of a paid rate `rate` (95 % confidence, 80 % power), and the
    paid orders per arm that many visitors bring. A rate above one half is taken as one half (never a division by zero)."""
    p1 = min(0.5, max(1e-6, rate))
    p2 = min(0.999, p1 * (1 + rel))
    pb = (p1 + p2) / 2
    n = ((NEED_ALPHA_Z * math.sqrt(2 * pb * (1 - pb)) + NEED_POWER_Z * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
         / (p2 - p1) ** 2)
    return {"visitors": int(math.ceil(n)), "paid": int(math.ceil(n * p1)), "rate": p1, "rel": rel}


def rpv_test(a, b):
    """Revenue per visitor of arm b against arm a: {diff (smallest unit), z, p}, or None. Each visitor's revenue is the
    amount of their paid order or 0, so the variance comes from the orders' amounts (amount_sum, amount_sq of the stats);
    the normal approximation of Welch's test, good from about 100 visitors per arm."""
    try:
        n1, n2 = int(a["visitors"]), int(b["visitors"])
        if n1 < 2 or n2 < 2 or a.get("amount_sum") is None or b.get("amount_sum") is None:
            return None

        def mv(x, n):
            m = x["amount_sum"] / n
            return m, max(0.0, (x["amount_sq"] - n * m * m) / (n - 1))

        m1, v1 = mv(a, n1)
        m2, v2 = mv(b, n2)
        se2 = v1 / n1 + v2 / n2
        if not se2 > 0:
            return None
        z = (m2 - m1) / math.sqrt(se2)
        return {"diff": round(m2 - m1, 2), "z": round(z, 3), "p": round(2 * _phi_upper(abs(z)), 4)}
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None


def _sum_days(rows):
    tot = {"exp_stage": {}, "exp_hit": {}, "exp_rev": {}, "exp_rev_hit": {}}
    for _day, agg, _c in rows:
        for name in tot:
            for k, v in ((agg or {}).get(name) or {}).items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    tot[name][k] = tot[name].get(k, 0) + v
    return tot


def order_stats(orders, key, variant, currency):
    """What the order records say about one variant (ops.order_row rows, live payments only): paid orders that were not
    returned, their revenue and sum of squares, the affected ones apart, test payments, and the orders that were refunded or
    withdrawn (a return is not revenue)."""
    out = {"paid": 0, "revenue": 0, "sq": 0, "hit_paid": 0, "revenue_hit": 0, "test": 0, "returned": 0, "returned_revenue": 0}
    for r in orders or []:
        x = r.get("experiment") if isinstance(r, dict) else None
        if not isinstance(x, dict) or x.get("key") != key or x.get("variant") != variant or r.get("paid") is not True:
            continue
        if str(r.get("currency") or "").lower() != currency:
            continue
        amount = r.get("amount")
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            continue
        if r.get("live") is not True:
            out["test"] += 1
            continue
        if r.get("returned") is True:
            out["returned"] += 1
            out["returned_revenue"] += amount
            continue
        out["paid"] += 1
        out["revenue"] += amount
        out["sq"] += amount * amount
        eyes = r.get("eyes")
        if differs(key, r.get("market"), eyes if isinstance(eyes, int) and not isinstance(eyes, bool) else 1, r.get("style") or ""):
            out["hit_paid"] += 1
            out["revenue_hit"] += amount
    return out


def untokened_orders(orders, key, runs, now):
    """Orders of the experiment's markets made while it ran that carry no variant (storage blocked, opted out, a stripped
    token, a first checkout before the answer came): {orders, paid}. A buyer who avoids the test on purpose shows up here."""
    d = get(key) or {}
    markets = set(d.get("markets") or [])
    cur = currency_of_experiment(key)
    windows = [(r["start"], r["stop"] or now) for r in runs if isinstance(r.get("start"), (int, float)) and not isinstance(r.get("start"), bool)]
    n = paid = 0
    for r in orders or []:
        if not isinstance(r, dict) or r.get("experiment") is not None or r.get("market") not in markets:
            continue
        t, amount = r.get("created_at"), r.get("amount")
        if not isinstance(t, (int, float)) or not isinstance(amount, int) or not any(a <= t <= b for a, b in windows):
            continue
        if str(r.get("currency") or "").lower() != cur:
            continue
        n += 1
        if r.get("paid") is True and r.get("live") is True and r.get("returned") is not True:
            paid += 1
    return {"orders": n, "paid": paid}


def variant_stats(tot, key, variant, currency, orders=None):
    """The funnel of one variant. Visitors, previews and payment pages opened come from the anonymous events (best effort);
    paid orders and revenue come from the order records when `orders` is given (they are the truth), else from the events.
    The event count of paid orders is kept as paid_events, for the cross-check."""
    g = lambda t, s: int(tot[t].get(f"{key}|{variant}|{s}", 0))
    visit, preview, checkout = g("exp_stage", "visit"), g("exp_stage", "preview"), g("exp_stage", "checkout")
    paid_ev = g("exp_stage", "paid")
    rev_ev = int(tot["exp_rev"].get(f"{key}|{variant}|{currency}", 0))
    if orders is not None:
        o = order_stats(orders, key, variant, currency)
        paid, rev, rev_hit, hit_paid, test = o["paid"], o["revenue"], o["revenue_hit"], o["hit_paid"], o["test"]
        amount_sum, amount_sq, returned, returned_rev = o["revenue"], o["sq"], o["returned"], o["returned_revenue"]
    else:
        paid, rev = paid_ev, rev_ev
        rev_hit = int(tot["exp_rev_hit"].get(f"{key}|{variant}|{currency}", 0))
        hit_paid, test = g("exp_hit", "paid"), g("exp_stage", "paid_test")
        amount_sum = amount_sq = None
        returned = returned_rev = 0
    rate = lambda a, b: (a / b) if b else None
    return {"variant": variant, "visitors": visit, "previews": preview, "checkouts": checkout, "paid": paid,
            "paid_test": test, "hit_previews": g("exp_hit", "preview"),
            "hit_checkouts": g("exp_hit", "checkout"), "hit_paid": hit_paid,
            "revenue": rev, "revenue_hit": rev_hit, "avg_order": round(rev / paid) if paid else None,
            "avg_order_hit": round(rev_hit / hit_paid) if hit_paid else None,
            "rate_preview": rate(preview, visit), "rate_checkout": rate(checkout, visit), "rate_paid": rate(paid, visit),
            "rate_hit_paid": rate(hit_paid, visit),
            "rate_paid_of_checkout": rate(paid, checkout), "revenue_per_visitor": round(rev / visit) if visit else None,
            "returned": returned, "returned_revenue": returned_rev, "paid_events": paid_ev, "revenue_events": rev_ev,
            "source": "orders" if orders is not None else "events", "amount_sum": amount_sum, "amount_sq": amount_sq}


def _gate(a, b, paid_key="paid"):
    """Why two arms cannot be tested yet (few_visitors, few_paid, paid_exceeds_visitors), or None."""
    if a["visitors"] < MIN_ARM_VISITORS or b["visitors"] < MIN_ARM_VISITORS:
        return "few_visitors"
    if a[paid_key] < MIN_ARM_PAID or b[paid_key] < MIN_ARM_PAID:
        return "few_paid"
    if a[paid_key] > a["visitors"] or b[paid_key] > b["visitors"]:
        return "paid_exceeds_visitors"
    return None


def compare(control, other):
    """The paid-per-visitor difference of a variant against the control, with a two-proportion z-test p-value, shown
    only when every arm has MIN_ARM_PAID paid orders and MIN_ARM_VISITORS visitors (else why not). This tests CONVERSION
    only; "rpv" is the revenue-per-visitor comparison (the one a price decision rests on) from the same data, and "hit"
    (only when the orders carry affected ones) the conversion to the affected orders alone."""
    out = {"variant": other["variant"], "p": None, "z": None, "enough": False, "why": None, "rpv": None, "hit": None}
    a, b = control, other
    out["why"] = _gate(a, b)
    if out["why"] is None:
        z, p = z_test(a["paid"], a["visitors"], b["paid"], b["visitors"])
        out.update(z=None if z is None else round(z, 3), p=None if p is None else round(p, 4), enough=p is not None)
        if p is None:
            out["why"] = "no_variance"
        out["rpv"] = rpv_test(a, b)
    if a.get("rate_paid") is not None and b.get("rate_paid") is not None:
        out["diff"] = b["rate_paid"] - a["rate_paid"]
    if "hit_paid" in a and "hit_paid" in b:
        why = _gate(a, b, "hit_paid")
        h = {"why": why, "p": None, "z": None, "enough": False}
        if why is None:
            z, p = z_test(a["hit_paid"], a["visitors"], b["hit_paid"], b["visitors"])
            h.update(z=None if z is None else round(z, 3), p=None if p is None else round(p, 4), enough=p is not None)
        if a.get("rate_hit_paid") is not None and b.get("rate_hit_paid") is not None:
            h["diff"] = b["rate_hit_paid"] - a["rate_hit_paid"]
        out["hit"] = h
    return out


def window_days(state, now=None):
    """How many UTC days of events cover the experiment since its first start (at most STATS_DAYS_MAX)."""
    now = time.time() if now is None else now
    since = state.get("since") if isinstance(state, dict) else None
    if not since:
        return 1
    return max(1, min(STATS_DAYS_MAX, int((now - since) // 86400) + 2))


def _partial(d):
    """Does the test change only some of the prices (so that only some orders, 3+ eyes say, are affected)?"""
    return set(d.get("changes") or []) != set(PRICE_KEYS)


def _experiment_view(key, d, s, rows, now, orders, collecting):
    cur = currency_of_experiment(key)
    tot = _sum_days(rows[-window_days(s, now):])
    stats = {name: variant_stats(tot, key, name, cur, orders) for name in d["variants"]}
    control = stats.get("control")
    base_rate = control["rate_paid"] if control and control["visitors"] >= MIN_ARM_VISITORS and control["paid"] else None
    need = need_sample(base_rate if base_rate else NEED_ASSUMED_RATE)
    need["assumed"] = base_rate is None
    partial = _partial(d)
    need_hit = None
    if partial:
        hr = control["rate_hit_paid"] if control and control["visitors"] >= MIN_ARM_VISITORS and control["hit_paid"] else None
        need_hit = need_sample(hr if hr else NEED_ASSUMED_RATE * NEED_ASSUMED_HIT)
        need_hit["assumed"] = hr is None
    comps = []
    if control:
        for n in d["variants"]:
            if n == "control":
                continue
            c = compare(control, stats[n])
            # "planned": every arm has reached the size the note above asks for; only then is a verdict allowed
            goal = (need_hit["paid"], "hit_paid") if partial and need_hit else (need["paid"], "paid")
            c["planned"] = control[goal[1]] >= goal[0] and stats[n][goal[1]] >= goal[0]
            comps.append(c)
    warnings = [dict(code="loss", **r) for r in loss_report(key)] + [dict(code="spread", **r) for r in spread_report(key)]
    if orders is not None:
        for n, st in stats.items():
            total_orders = st["paid"] + st["returned"]
            if st["paid_events"] != total_orders and (st["paid_events"] or total_orders):
                warnings.append({"code": "events_differ", "variant": n, "orders": total_orders, "events": st["paid_events"]})
    return {
        "key": key, "title": d.get("title"), "about": d.get("about"), "markets": d.get("markets"),
        "currency": cur.upper(), "changes": d.get("changes"), "hit_label": d.get("hit_label"), "partial": partial,
        "retired": bool(d.get("retired")),
        "state": {"running": s["on"], "since": s["since"], "started_at": s["started_at"], "stopped_at": s["stopped_at"],
                  "updated": s["updated"], "runs": s["runs"]},
        "conflict": conflict(key) if not s["on"] else None,
        "variants": [{"variant": n, "label": v.get("label"), "split": d["split"].get(n), "prices": v.get("prices")}
                     for n, v in d["variants"].items()],
        "stats": [stats[n] for n in d["variants"]], "compare": comps, "need": need, "need_hit": need_hit,
        "untokened": untokened_orders(orders, key, s["runs"], now) if orders is not None else None,
        "days": window_days(s, now), "warnings": warnings, "stats_error": False,
    }


def _failed_view(key, d, s, now, err):
    """The card of an experiment whose numbers could not be computed: its state, ladders and buttons still render."""
    try:
        warnings = [dict(code="loss", **r) for r in loss_report(key)]
    except Exception:  # noqa
        warnings = []
    print(f"snapeyes experiments: statistics of {key} failed ({type(err).__name__})", flush=True)
    return {
        "key": key, "title": d.get("title"), "about": d.get("about"), "markets": d.get("markets"),
        "currency": currency_of_experiment(key).upper(), "changes": d.get("changes"), "hit_label": d.get("hit_label"),
        "partial": False, "retired": bool(d.get("retired")),
        "state": {"running": s["on"], "since": s["since"], "started_at": s["started_at"], "stopped_at": s["stopped_at"],
                  "updated": s["updated"], "runs": s["runs"]},
        "conflict": conflict(key) if not s["on"] else None,
        "variants": [{"variant": n, "label": v.get("label"), "split": d["split"].get(n), "prices": v.get("prices")}
                     for n, v in d["variants"].items()],
        "stats": [], "compare": [], "need": None, "need_hit": None, "untokened": None, "days": window_days(s, now),
        "warnings": warnings, "stats_error": True,
    }


def admin_view(collect, audit=None, now=None, ordering_open=None, orders=None, orders_more=False, collecting=None):
    """The data of the admin page: every experiment with its definition, state, per-variant statistics, the comparison
    with the control, the sample needed and the warnings. collect(n): ops.collect_days, [(day, counts, complete)] for the
    last n UTC days, oldest first. audit: the admin audit entries (newest first) to show the experiments' lines from.
    orders: the order rows (ops.order_row) of the experiments' window, the source of the paid numbers (None: the events';
    orders_more: the list was cut short, so it is not used). collecting: does this deployment store events at all
    (events.retention_ok). One experiment whose numbers fail never takes the page down."""
    now = time.time() if now is None else now
    st = states(force=True)
    widest = max([window_days(st.get(k), now) for k in DEFS] or [1])
    rows = collect(widest)
    partial = not all(c for _d, _a, c in rows)
    use_orders = orders if isinstance(orders, list) and not orders_more else None
    exps = []
    for key, d in DEFS.items():
        s = st.get(key, _blank())
        try:
            exps.append(_experiment_view(key, d, s, rows, now, use_orders, collecting))
        except Exception as e:  # noqa: the state, the ladders and the stop button must always render
            exps.append(_failed_view(key, d, s, now, e))
    log = [e for e in (audit or []) if isinstance(e, dict) and str(e.get("action") or "").startswith("exp_")][:30]
    runs = []
    for key, d in DEFS.items():
        for r in (st.get(key) or _blank())["runs"]:
            if isinstance(r.get("start"), (int, float)) and not isinstance(r.get("start"), bool):
                runs.append({"key": key, "title": d.get("title"), "start": r["start"], "stop": r.get("stop")})
    runs.sort(key=lambda r: -r["start"])
    return {"ok": True, "now": int(now), "experiments": exps, "partial": partial, "log": log, "runs": runs[:30],
            "ordering_open": ordering_open, "collecting": collecting,
            "orders_source": "orders" if use_orders is not None else ("events_cut" if (orders_more and orders is not None) else "events"),
            "costs": {"unit_usd_per_eye": COSTS["unit_usd_per_eye"]},
            "rules": {"min_arm_paid": MIN_ARM_PAID, "min_arm_visitors": MIN_ARM_VISITORS, "spread_warn": SPREAD_WARN,
                      "rel_effect": NEED_REL_EFFECT}}
