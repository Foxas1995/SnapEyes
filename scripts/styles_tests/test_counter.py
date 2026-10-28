# -*- coding: utf-8 -*-
"""The anonymous counter (2026-10-20, api/_lib/counter.py, api/checkout.py, api/_lib/events.py kind "hit", src/shared/counter.ts): which step of the site a visit reached,
with no cookie and no identifier. Suite v3counter.

  1. the classes: the device and browser of a user agent (Facebook's and Instagram's in-app browsers among them), robots, the country, the campaign code
  2. the beacon over HTTP: what is stored (only the whitelisted codes), what is refused (unknown step, robot, wrong content type, another origin), the client and
     instance ceilings, the fields that are dropped, and that nothing of an IP address or a user agent reaches the store
  3. the kill switch: SNAPEYES_COUNTER read once at import, health and checkout say counter false, the beacon counts nothing
  4. the day's counts: the hits table by step and codes, the country table, the time histogram, the cap on distinct keys, the size of a busy day, merge and rollup
  6. the server steps of a visit are counted by campaign, device class and browser family: the analysis (and the classes of the photo), the restoration, the sets of eyes, the checkout, the
     errors and the times, the caps on the tables, the size of a busy day
  5. the campaign code travels: the events other endpoints write during a request carry it with the device class, the browser family and the country (iris.ctx); the checkout keeps it in
     the order record and Stripe's metadata, the payment in paid.json and the paid event, the admin's order row names it; a hostile code is cut down; nothing of the requests is kept
No network, no image model, no real eye. Run by suites/run_main.sh as v3counter (in the world before the cutover: section 5 sells a legacy style).
    python test_counter.py   prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure"""
import atexit
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(REPO, "api")
SP = os.environ.get("SNAPEYES_SP") or ""
HARNESS = next((d for d in (os.path.join(SP, "wave-pv", "tests") if SP else "", os.path.join(REPO, "suites", "tree", "wave-pv", "tests"))
                if d and os.path.isfile(os.path.join(d, "harness.py"))), None) or sys.exit("the payments harness (wave-pv/tests/harness.py) is not found")

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   <- {str(detail)[:700]}"), flush=True)


def section(title):
    print(f"\n== {title}", flush=True)


for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "AWS_", "NOW_", "LAMBDA_", "STORE_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP"):
            os.environ.pop(k)
TMP = tempfile.mkdtemp(prefix="snapeyes_v3counter_")
atexit.register(shutil.rmtree, TMP, ignore_errors=True)
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, HARNESS)
sys.path.insert(0, HERE)
import harness as H  # noqa: E402

STORE = os.path.join(TMP, "store")
stub = H.start_stub()
H.setup_env(STORE, stub.server_address[1])
os.environ["CRON_SECRET"] = "counter-cron-secret-for-tests-0123456789"        # the events are stored only while the daily clean-up can delete them
sys.path.insert(0, API)
import requests  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import counter as C  # noqa: E402
from _lib import events as E  # noqa: E402
from _lib import markets, pay, store, ops  # noqa: E402

api = H.start_api()
BASE = f"http://127.0.0.1:{api.server_address[1]}"
C.BEACON_WAIT = 10.0            # a slow disk (a virus scanner) must not make a check flaky: the beacon waits for its write as long as it needs here

UA_FB_IOS = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBAV/430.0.0.0;FBBV/1]"
UA_FB_AND = "Mozilla/5.0 (Linux; Android 13; SM-S918B; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/118.0.0.0 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/430.0.0.31.108;]"
UA_IG_AND = "Mozilla/5.0 (Linux; Android 13; Pixel 7 Build/TQ3A) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/118.0.0.0 Mobile Safari/537.36 Instagram 300.0.0.1 Android"
UA_IG_IOS = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 310.0.0.20.113 (iPhone14,5; iOS 17_0; en_US; en; scale=3.00; 1170x2532; 123456789)"
UA_SAFARI_IOS = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
UA_CHROME_AND = "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36"
UA_CHROME_WIN = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
UA_EDGE_WIN = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.46"
UA_FIREFOX_LINUX = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0"
UA_SAMSUNG = "Mozilla/5.0 (Linux; Android 13; SAMSUNG SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 Chrome/115.0.0.0 Mobile Safari/537.36"
UA_TIKTOK = "Mozilla/5.0 (Linux; Android 12; SM-A525F Build/SP1A.210812.016; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/118.0.0.0 Mobile Safari/537.36 trill_2023 BytedanceWebview/d8a21c6"
UA_OPERA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 OPR/104.0.0.0"
UA_IOS_WEBVIEW = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
UA_BOTS = ["Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)", "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
           "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/118.0.0.0 Safari/537.36",
           "Mozilla/5.0 (Linux; Android 11; moto g power (2022)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36 Chrome-Lighthouse",
           "python-requests/2.31.0", "curl/8.4.0", "Wget/1.21", "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)", "", "Mozilla/5.0",
           "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15 (Applebot/0.1)",
           "meta-externalagent/1.1 (+https://developers.facebook.com/docs/sharing/webmasters/crawler)"]


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def day():
    return time.strftime("%Y-%m-%d", time.gmtime())


def events_today():
    """The events stored today, read once no write is under way (a local store writes through a .part file)."""
    out = []
    folder = os.path.join(STORE, "ops", "events", day())
    for _ in range(60):
        names = sorted(os.listdir(folder)) if os.path.isdir(folder) else []
        if not any(n.endswith(".part") or ".part" in n for n in names):
            break
        time.sleep(0.1)
    for n in names:
        if n.endswith(".json"):
            with open(os.path.join(folder, n), encoding="utf-8") as f:
                out.append(json.load(f))
    return out


def wipe():
    """An empty store, empty ceilings and an empty client table."""
    shutil.rmtree(os.path.join(STORE, "ops"), ignore_errors=True)
    E._SEEN.update({"all": [], "error": [], "exp": [], "help": [], "hit": [], "day": "", "errors_today": 0, "exp_day": "", "exp_today": 0,
                    "help_day": "", "help_today": 0, "hit_day": "", "hit_today": 0})
    C._CLIENTS.clear()


def hit(step="landing", ua=UA_SAFARI_IOS, ip="198.51.100.7", cc="LT", body=None, ct="application/json", headers=None):
    h = {"User-Agent": ua, "x-forwarded-for": ip, "Content-Type": ct}
    if cc is not None:
        h["x-vercel-ip-country"] = cc
    h.update(headers or {})
    b = {"hit": step, "lang": "lt", "market": "lt"}
    b.update(body or {})
    return requests.post(BASE + "/api/checkout", data=json.dumps(b), headers=h, timeout=20)


def store_text():
    """Every file of the store as text, for the greps that prove no address and no user agent is kept."""
    out = []
    for root, _d, files in os.walk(STORE):
        for n in files:
            with open(os.path.join(root, n), "rb") as f:
                out.append(f.read().decode("utf-8", "replace"))
    return "\n".join(out)


# ============================================================================================ 1. the classes
section("1. the classes: device and browser of a user agent, robots, the country, the campaign code")
cases = [(UA_FB_IOS, ("ios", "fb")), (UA_FB_AND, ("android", "fb")), (UA_IG_AND, ("android", "ig")), (UA_IG_IOS, ("ios", "ig")), (UA_SAFARI_IOS, ("ios", "safari")),
         (UA_CHROME_AND, ("android", "chrome")), (UA_CHROME_WIN, ("desktop", "chrome")), (UA_EDGE_WIN, ("desktop", "edge")), (UA_FIREFOX_LINUX, ("desktop", "firefox")),
         (UA_SAMSUNG, ("android", "samsung")), (UA_TIKTOK, ("android", "tt")), (UA_OPERA, ("desktop", "opera")), (UA_IOS_WEBVIEW, ("ios", "wv"))]
bad = [(ua[:60], C.ua_classes(ua)[:2], want) for ua, want in cases if C.ua_classes(ua)[:2] != want or C.ua_classes(ua)[2]]
check("the device class and the browser family of 13 real user agents, among them the Facebook and Instagram apps on iPhone and Android (the ads plan's gate G4), TikTok, Samsung "
      "and the iPhone web view with no Safari token", not bad, bad)
check("the Android web view token (; wv) with no app named is the in-app family wv", C.ua_classes("Mozilla/5.0 (Linux; Android 13; Pixel 7; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/118.0.0.0 Mobile Safari/537.36")[:2] == ("android", "wv"))
bad = [(ua[:50], C.ua_classes(ua)) for ua in UA_BOTS if not C.ua_classes(ua)[2]]
check("eleven robots (Googlebot, the link preview crawlers of Facebook and Meta, headless Chrome, Lighthouse, python, curl, wget, bingbot, Applebot, an empty and a too short user "
      "agent) are robots", not bad, bad)
check("a phone brand with 'bot' inside its name (CUBOT) is not a robot", not C.ua_classes("Mozilla/5.0 (Linux; Android 12; CUBOT_X30) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36")[2])
check("the country is the two letters Vercel names, in lower case, and xx for anything else",
      [C.country(v) for v in ("LT", " de ", "hu", "", None, "LTU", "a1", "L", 5)] == ["lt", "de", "hu", "xx", "xx", "xx", "xx", "xx", "xx"])
WIRE = "utm_source=fb&utm_medium=paid&utm_campaign=se-p0-test&utm_term=lt-a1-eye&utm_content=a1-lt-s1"
p = C.parse(WIRE)
check("a campaign code as the pages carry it (the utm_ parameters of the address; a fbclid beside them is ignored) parses into its five parts and packs into the stored form src|med|cmp|trm|cnt, which parses back",
      p == {"src": "fb", "med": "paid", "cmp": "se-p0-test", "trm": "lt-a1-eye", "cnt": "a1-lt-s1"} and C.pack(p) == "fb|paid|se-p0-test|lt-a1-eye|a1-lt-s1" and C.parse("fb|paid|se-p0-test|lt-a1-eye|a1-lt-s1") == p and C.parse(WIRE + "&fbclid=IwAR0x") == p, p)
check("the kind of page the visitor came from is read as ref=<class>; an unknown class, or no source at all, is no code",
      [C.parse("ref=" + x) for x in ("facebook", "instagram", "tiktok", "google", "direct", "other")] == [{"src": x} for x in ("facebook", "instagram", "tiktok", "google", "direct", "other")]
      and C.parse("ref=evil") is None and C.parse("ref=") is None and C.parse("utm_medium=paid") is None and C.parse("utm_source=") is None)
check("percent-encoded values are decoded before they are checked, and what is no code afterwards is dropped (a script tag, a pipe, an address)",
      C.parse("utm_source=%3Cscript%3E") is None and C.parse("utm_source=fb&utm_medium=a%7Cb&utm_campaign=203.0.113.7&utm_term=ok") == {"src": "fb", "trm": "ok"}
      and C.parse("utm_source=FB&utm_medium=Paid+Ads") == {"src": "fb"} and C.parse("utm_source=fb&utm_campaign=Spring%20Sale") == {"src": "fb"}, "")
check("in the stored form empty parts stay empty, upper case is folded, and a code needs a source", C.parse("direct||||") == {"src": "direct"} and C.parse("FB|Paid") == {"src": "fb", "med": "paid"}
      and C.parse("|paid|x") is None and C.parse("") is None and C.parse(None) is None and C.parse(5) is None)
hostile = ["fb|<script>|x", "fb|paid|a b|c", "fb|paid|" + "a" * 41, "fb|paid|ok|203.0.113.7|a@b.c", "fb|../etc|x"]
got = [C.parse(h) for h in hostile]
check("a part that is not a short code of letters, digits and _ . - is dropped on its own and never reaches an event (a script tag, a space, 41 characters, an address, an e-mail, a path)",
      got[0] == {"src": "fb", "cmp": "x"} and got[1] == {"src": "fb", "med": "paid", "trm": "c"} and got[2] == {"src": "fb", "med": "paid"}
      and got[3] == {"src": "fb", "med": "paid", "cmp": "ok"} and got[4] == {"src": "fb", "cmp": "x"}, got)
check("a text of more than 500 characters is no campaign code", C.parse("fb|" + "a|" * 260) is None and C.parse("utm_source=fb&" + "x" * 500) is None)
check("the beacon's steps are the events' steps, its languages the site's, its markets the markets file's",
      C.STEPS == E.HIT_STEPS and set(C.LANGS) == set(pay.LANGS) and set(C.MARKETS) == set(markets.MARKETS), (C.STEPS, E.HIT_STEPS, C.LANGS, C.MARKETS))

# ============================================================================================ 2. the beacon over HTTP
section("2. the beacon over HTTP")
wipe()
r = hit("landing", ua=UA_FB_IOS, cc="LT", body={"camp": WIRE})
ev = events_today()
check("a landing beacon is answered 200 {ok, counted} and one event is stored", r.status_code == 200 and r.json().get("ok") is True and r.json().get("counted") is True and len(ev) == 1, (r.status_code, r.text, ev))
e0 = ev[0] if ev else {}
check("the event holds the step, the five campaign codes, the page language and market, the device class, the browser family and the country, and nothing else",
      {k: v for k, v in e0.items() if k not in ("t",)} == {"v": 1, "kind": "hit", "step": "landing", "src": "fb", "med": "paid", "cmp": "se-p0-test", "trm": "lt-a1-eye", "cnt": "a1-lt-s1",
                                                           "lang": "lt", "market": "lt", "dev": "ios", "br": "fb", "cc": "lt"}, e0)
check("a beacon's event has no 'ms' (the request's own time says nothing about the visit)", "ms" not in e0)
wipe()
bad = []
for step in C.STEPS:
    r = hit(step)
    if not (r.status_code == 200 and r.json().get("counted") is True):
        bad.append((step, r.status_code, r.text))
check("every one of the seven steps is counted", not bad and sorted(x["step"] for x in events_today()) == sorted(C.STEPS), bad)
wipe()
r = [hit("nope"), hit(""), hit(None), hit(["landing"]), hit("LANDING"), hit("landing ")]
check("an unknown step is answered 200 counted false and stores nothing", all(x.status_code == 200 and x.json().get("counted") is False for x in r) and not events_today(), [(x.status_code, x.text) for x in r])
wipe()
rs = [hit("landing", ua=ua) for ua in UA_BOTS]
check("a robot is answered 200 counted false and stores nothing", all(x.status_code == 200 and x.json().get("counted") is False for x in rs) and not events_today(), [x.text for x in rs][:3])
wipe()
r1 = hit("landing", ct="text/plain")
r2 = hit("landing", headers={"Origin": "https://evil.example"})
r3 = hit("landing", headers={"Origin": "https://snapeyes.com"})
check("a beacon with another content type is refused (415) and one from another origin is refused (403), neither is stored; the site's own origin is counted",
      r1.status_code == 415 and r2.status_code == 403 and r3.status_code == 200 and r3.json().get("counted") is True and len(events_today()) == 1, (r1.status_code, r2.status_code, r3.status_code))
wipe()
r = requests.post(BASE + "/api/checkout", data="not json", headers={"User-Agent": UA_SAFARI_IOS, "Content-Type": "application/json"}, timeout=20)
r2 = requests.post(BASE + "/api/checkout", data="[1]", headers={"User-Agent": UA_SAFARI_IOS, "Content-Type": "application/json"}, timeout=20)
time.sleep(1.0)             # the error event of a refused request is written after its reply
check("a body that is not a JSON object is refused 400 and no beacon is stored (the refusal is an ordinary error event)", r.status_code == 400 and r2.status_code == 400
      and not [x for x in events_today() if x.get("kind") == "hit"], (r.status_code, r2.status_code))
wipe()
r = hit("result", body={"took": 23456, "eyes": 2, "style": "solo.clean_iris", "lang": "de", "market": "eu"})
e = events_today()[0]
check("a result beacon keeps took (the page's own milliseconds), eyes and style", e.get("took") == 23456 and e.get("eyes") == 2 and e.get("style") == "solo.clean_iris" and e.get("lang") == "de" and e.get("market") == "eu", e)
wipe()
hit("landing", body={"took": 5, "eyes": 3, "style": "x"})
e = events_today()[0]
check("took is kept for the result step only; eyes and style on any step", "took" not in e and e.get("eyes") == 3 and e.get("style") == "x", e)
wipe()
bad = hit("result", body={"took": -1, "eyes": 0, "style": "has space", "lang": "xx", "market": "zz"})
# 2026-10-28: "us" is a market of api/_lib/markets.py now (with "uk" and "hr"), so the unknown market of this beacon is "ca" (no market of ours)
hit("result", body={"took": 10 ** 9, "eyes": 9, "style": "A" * 50, "camp": "|paid|x", "lang": "fr", "market": "ca"})
hit("result", body={"took": "5", "eyes": True, "style": ["a"], "lang": ["lt"], "market": 5, "camp": 5})
evs = events_today()
check("a took below 0 or above fifteen minutes, an eye count outside 1 to 8, a style that is not a short code, an unknown language or market and a campaign without a source are all dropped; "
      "the beacon itself is still counted",
      len(evs) == 3 and all(not ({"took", "eyes", "style", "lang", "market", "src"} & set(x)) for x in evs), evs)
wipe()
for mk in ("us", "uk", "hr"):
    hit("landing", ip="203.0.113.19", body={"lang": "en", "market": mk})
evs = events_today()
check("the markets of 2026-10-28 are counted under their own keys (us, uk, hr), each a market of api/_lib/markets.py",
      sorted(x.get("market") for x in evs) == ["hr", "uk", "us"] and {"us", "uk", "hr"} <= set(markets.MARKETS), evs)

wipe()
IPS = ["203.0.113.77", "198.51.100.200", "2001:db8::beef"]
UAS = [UA_FB_IOS, UA_IG_AND, UA_SAFARI_IOS]
for ip, ua in zip(IPS, UAS):
    hit("landing", ua=ua, ip=ip, body={"camp": f"fb|paid|{ip.replace(':', '-')}|x", "style": ip.replace(":", "-"), "lang": ip, "market": ua[:20]})
    hit("result", ua=ua, ip=ip, headers={"X-Real-IP": ip, "Referer": "https://snapeyes.com/try?utm_source=" + ip, "Cookie": "sid=secret-cookie-value"})
text = store_text()
needles = IPS + [x for x in UAS] + ["Mozilla", "AppleWebKit", "FBAN", "FBAV", "Instagram 300", "iPhone14", "secret-cookie-value", "utm_source", "evil", "snapeyes.com/try"]
leaks = [n for n in needles if n in text]
check("synthetic traffic with three IP addresses, three user agents, a cookie and a referrer, then every file of the store read: none of them is in it (addresses, user agents, tokens of "
      "a user agent, cookie, referrer, URL)", not leaks and len(events_today()) >= 6, leaks)
wipe()
hit("landing", body={"camp": "fb|paid|203.0.113.7|198.51.100.4|ok", "style": "192.0.2.1"})
e = events_today()[0]
check("a dotted IPv4 address is no code: put in a campaign part or in the style it is dropped, in the beacon (counter.is_code) and in every code of every event (events._value)",
      e.get("src") == "fb" and e.get("cnt") == "ok" and not ({"cmp", "trm", "style"} & set(e)) and E.build("compose", {"style": "203.0.113.7", "eyes": 1}).get("style") is None
      and E.build("compose", {"style": "solo.clean_iris", "layout": "1.2.3"}).get("layout") == "1.2.3", e)

# the client ceiling: forty beacons a minute from one address
wipe()
rs = [hit("landing", ip="192.0.2.50") for _ in range(C.CLIENT_MAX + 5)]
n = sum(1 for x in rs if x.json().get("counted"))
other = hit("landing", ip="192.0.2.51")
check(f"one client may send {C.CLIENT_MAX} beacons a minute, the next are not counted (still answered 200); another client is counted", n == C.CLIENT_MAX and other.json().get("counted") is True and len(events_today()) == C.CLIENT_MAX + 1, (n, len(events_today())))
check("the client table holds only keyed hashes of twelve hex characters (never an address), in memory", all(re.fullmatch(r"[0-9a-f]{12}", k) for k in C._CLIENTS) and C._CLIENTS, list(C._CLIENTS)[:3])
C._CLIENTS.clear()
old_len = C.CLIENTS_KEPT
C.CLIENTS_KEPT = 3
for i in range(8):
    C._client_ok(f"{i:012x}", time.time())
check("the client table is cut back when it grows past its limit", len(C._CLIENTS) <= 4, len(C._CLIENTS))
C.CLIENTS_KEPT = old_len

# the instance ceilings
wipe()
old_rate = E.RATE["hit"]
E.RATE["hit"] = (6, 60.0)
rs = [hit("landing", ip=f"192.0.2.{i}") for i in range(10)]
check("an instance counts at most RATE['hit'] beacons a minute", sum(1 for x in rs if x.json().get("counted")) == 6 and len(events_today()) == 6, len(events_today()))
E.RATE["hit"] = old_rate
wipe()
old_day = E.HIT_DAY_MAX
E.HIT_DAY_MAX = 4
rs = [hit("landing", ip=f"192.0.2.{i}") for i in range(9)]
check("and at most HIT_DAY_MAX a UTC day", sum(1 for x in rs if x.json().get("counted")) == 4 and len(events_today()) == 4, len(events_today()))
E.HIT_DAY_MAX = old_day
wipe()
r = hit("landing", ip="192.0.2.9")
check("after the ceilings are reset the beacon counts again", r.json().get("counted") is True)

# ============================================================================================ 3. the kill switch
section("3. the kill switch SNAPEYES_COUNTER")
wipe()
h_on, c_on = requests.get(BASE + "/api/health", timeout=20).json(), requests.get(BASE + "/api/checkout", timeout=20).json()
check("while the counter is on, GET /api/health and GET /api/checkout say counter true (the pages send their beacons)", h_on.get("counter") is True and c_on.get("counter") is True, (h_on.get("counter"), c_on.get("counter")))
L.COUNTER_ON = False
try:
    h_off, c_off = requests.get(BASE + "/api/health", timeout=20).json(), requests.get(BASE + "/api/checkout", timeout=20).json()
    r = hit("landing")
    check("with the switch off both say counter false (the pages send nothing) and a beacon that arrives anyway is answered on false, counted false and stores nothing",
          h_off.get("counter") is False and c_off.get("counter") is False and r.status_code == 200 and r.json().get("counted") is False and r.json().get("on") is False and not events_today(),
          (h_off.get("counter"), c_off.get("counter"), r.text))
finally:
    L.COUNTER_ON = True
check("back on, it counts again", hit("landing").json().get("counted") is True)


def counter_flag(value):
    env = dict(os.environ)
    env.pop("SNAPEYES_COUNTER", None)
    if value is not None:
        env["SNAPEYES_COUNTER"] = value
    out = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, sys.argv[1]); from _lib import iris; print(iris.COUNTER_ON)", API], env=env,
                         capture_output=True, text=True, timeout=120)
    return out.stdout.strip().splitlines()[-1] if out.stdout.strip() else out.stderr[-300:]


flags = {v: counter_flag(v) for v in (None, "", "on", "1", "yes", "true", "garbage", "off", "0", "false", "no", "OFF", " False ", "﻿off", "No")}
check("read once at import: unset, empty, on, 1, yes, true and any other text are on; off, 0, false and no (any case, with spaces or a BOM) are off",
      all(flags[v] == "True" for v in (None, "", "on", "1", "yes", "true", "garbage")) and all(flags[v] == "False" for v in ("off", "0", "false", "no", "OFF", " False ", "﻿off", "No")), flags)
saved = os.environ.pop("STORE_LOCAL_DIR")
try:
    check("with no store to keep the counts, the counter says false (health, and on() itself)", counter_flag is not None and C.on() is False and requests.get(BASE + "/api/health", timeout=20).json().get("counter") is False)
finally:
    os.environ["STORE_LOCAL_DIR"] = saved
saved = os.environ.pop("CRON_SECRET")
try:
    check("and with no CRON_SECRET (nothing would delete the counts after twelve months) it says false too", C.on() is False and not hit("landing").json().get("counted"))
finally:
    os.environ["CRON_SECRET"] = saved
check("with both back it is on again", C.on() is True)

# ============================================================================================ 4. the day's counts
section("4. the day's counts")


def mk(step, **kw):
    f = {"step": step, "src": "fb", "med": "paid", "cmp": "se-p0-test", "trm": "lt-a1-eye", "cnt": "a1-lt-s1", "lang": "lt", "market": "lt", "dev": "ios", "br": "fb", "cc": "lt"}
    f.update(kw)
    return E.build("hit", f)


agg = E.summarize([mk("landing"), mk("landing"), mk("landing", dev="android", br="ig", cc="de"), mk("try"), mk("photo", src="direct", med=None, cmp=None, trm=None, cnt=None),
                   mk("result", took=12000), mk("result", took=70000), mk("result", took=4000, dev="android", br="chrome"), mk("buy"), mk("order"), mk("soon")])
h = agg["hits"]
check("the hits table counts a step by its codes: step|src|med|cmp|trm|cnt|lang|market|dev|br, an empty code is a dash",
      h.get("landing|fb|paid|se-p0-test|lt-a1-eye|a1-lt-s1|lt|lt|ios|fb") == 2 and h.get("landing|fb|paid|se-p0-test|lt-a1-eye|a1-lt-s1|lt|lt|android|ig") == 1
      and h.get("photo|direct|-|-|-|-|lt|lt|ios|fb") == 1, h)
check("the country table counts a step by country", agg["hit_cc"].get("landing|lt") == 2 and agg["hit_cc"].get("landing|de") == 1 and agg["hit_cc"].get("order|lt") == 1, agg["hit_cc"])
check("the time to a preview is counted in the buckets of TTP_MS by device and browser (12 s, 70 s, 4 s)",
      agg["hit_ms"] == {f"ios|fb|{E.ttp_bucket(12000)}": 1, f"ios|fb|{E.ttp_bucket(70000)}": 1, f"android|chrome|{E.ttp_bucket(4000)}": 1}
      and E.ttp_bucket(4000) == 0 and E.ttp_bucket(5000) == 0 and E.ttp_bucket(12000) == 2 and E.ttp_bucket(70000) == 7 and E.ttp_bucket(10 ** 7) == len(E.TTP_MS), agg["hit_ms"])
check("the events kind counter shows in kinds and events and nothing else moved (no compose, no error)", agg["kinds"] == {"hit": 11} and agg["events"] == 11 and not agg["errors"] and not agg["compose_style"], agg["kinds"])
check("a hit with a step that is not one of the seven is not counted in the tables (it is still an event)", not E.summarize([E.build("hit", {"step": "nope"})])["hits"])
two = E.merge(E.summarize([mk("landing")]), E.summarize([mk("landing"), mk("try")]))
check("merge adds the hits tables of two days", two["hits"]["landing|fb|paid|se-p0-test|lt-a1-eye|a1-lt-s1|lt|lt|ios|fb"] == 2 and two["hit_cc"]["landing|lt"] == 2 and two["hit_cc"]["try|lt"] == 1, two["hits"])
old_cap = dict(E.TABLE_KEYS_MAX)
E.TABLE_KEYS_MAX.update(hits=5, hit_cc=3, hit_ms=2)
many = E.summarize([mk("landing", cmp=f"c{i}", cc=chr(97 + i % 26) + "x") for i in range(40)] + [mk("result", took=1000 * i, dev=f"d{i}") for i in range(10)])
check("a stranger who sends a different campaign code with every beacon cannot grow a day's counts: past TABLE_KEYS_MAX the rest is counted under 'overflow', nothing is lost",
      len(many["hits"]) == 6 and many["hits"].get("overflow") == 45 and sum(many["hits"].values()) == 50 and len(many["hit_cc"]) == 4 and sum(many["hit_cc"].values()) == 50
      and sum(many["hit_ms"].values()) == 10 and len(many["hit_ms"]) == 3, (len(many["hits"]), many["hits"].get("overflow"), len(many["hit_cc"]), many["hit_ms"]))
E.TABLE_KEYS_MAX.update(old_cap)
import random  # noqa: E402
rnd = random.Random(7)
steps, srcs, cmps = list(C.STEPS), ["fb", "ig", "msg", "an", "tt", "direct"], [f"cmp-{i}" for i in range(60)]
big = E.summarize([E.build("hit", {"step": rnd.choice(steps), "src": rnd.choice(srcs), "med": "paid", "cmp": rnd.choice(cmps), "trm": f"t{rnd.randrange(30)}", "cnt": f"a{rnd.randrange(30)}",
                                   "lang": rnd.choice(["en", "de", "lt", "hu"]), "market": rnd.choice(["eu", "lt", "hu", "au"]), "dev": rnd.choice(["ios", "android", "desktop"]),
                                   "br": rnd.choice(["fb", "ig", "chrome", "safari", "tt", "wv"]), "cc": rnd.choice(["lt", "de", "hu", "at", "us", "gb"]), "took": rnd.randrange(60000)}) for _ in range(6000)])
size = len(json.dumps(dict(big, v=1, day="x")))
check("a day of 6000 beacons with every combination of codes stays under the 2 MB a stored day is read back with", size < E.ROLLUP_MAX_BYTES and len(big["hits"]) <= E.TABLE_KEYS_MAX["hits"] + 1, (size, len(big["hits"])))
info = f"   6000 beacons of random combinations: {len(big['hits'])} hit keys, {size // 1024} KB"
print(info, flush=True)
ops_stats = ops._slim(big)
check("the Statistika page's slim copy leaves the counter's tables out", not ({"hits", "hit_cc", "hit_ms"} & set(ops_stats)))
wipe()
day_a = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 3 * 86400))
folder = os.path.join(STORE, "ops", "events", day_a)
os.makedirs(folder, exist_ok=True)
for i in range(3):
    with open(os.path.join(folder, f"12000{i}-aaaaaaaa{i}b.json"), "w", encoding="utf-8") as f:
        json.dump(mk("landing"), f)
rows = ops.collect_days(5)
got = {d: a for d, a, _c in rows}
check("the admin's day reader sums stored beacon events into the day's counts and stores the finished day once (ops/daily)",
      got[day_a]["hits"].get("landing|fb|paid|se-p0-test|lt-a1-eye|a1-lt-s1|lt|lt|ios|fb") == 3 and os.path.isfile(os.path.join(STORE, "ops", "daily", day_a + ".json")), got[day_a].get("hits"))
back = E.get_rollup(day_a)
check("the stored day reads back with the counter's tables", isinstance(back, dict) and back.get("hits") == got[day_a]["hits"] and back.get("hit_cc") == got[day_a]["hit_cc"])
res = E.purge_old(days=1, yes=True)
check("events.purge_old deletes the beacon events with the other events after twelve months (the day folder is the same)", res.get("ok") is True and res.get("events") == 3
      and not [n for n in os.listdir(folder)] if os.path.isdir(folder) else res.get("events") == 3, res)

# ============================================================================================ 5. the campaign code travels
section("5. the campaign code travels: the events of the other endpoints, the order record, Stripe's metadata, the paid record")
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer  # noqa: E402
import threading  # noqa: E402


class Probe(BaseHTTPRequestHandler):
    """A stand-in endpoint: L.run (the gates, the body, the context) around a function that writes the events the real endpoints write."""
    def log_message(self, *a):
        pass

    def do_POST(self):
        def fn(body):
            if body.get("boom"):
                raise RuntimeError("boom")
            E.record("analyze", ok=True, verdict="good", lang="de")
            E.record("enhance", mode="faithful")
            E.record("compose", style="solo.clean_iris", eyes=1, tiles=0, gate="ok", market="hu")
            return {"ok": True}
        L.run(self, fn)


probe = ThreadingHTTPServer(("127.0.0.1", 0), Probe)
threading.Thread(target=probe.serve_forever, daemon=True).start()


def call(body, ua=UA_FB_IOS, cc="LT", ip="198.51.100.7"):
    h = {"User-Agent": ua, "Content-Type": "application/json", "x-forwarded-for": ip}
    if cc:
        h["x-vercel-ip-country"] = cc
    return requests.post(f"http://127.0.0.1:{probe.server_address[1]}/probe", data=json.dumps(body), headers=h, timeout=20)


CAMP = "fb|paid|se-p0-test|lt-a1-eye|a1-lt-s1"
wipe()
r = call({"camp": WIRE, "lang": "lt", "market": "lt"})
evs = {e["kind"]: e for e in events_today()}
codes = {"src": "fb", "med": "paid", "cmp": "se-p0-test", "trm": "lt-a1-eye", "cnt": "a1-lt-s1", "dev": "ios", "br": "fb", "cc": "lt"}
check("an event an endpoint writes during a request carries the request's campaign code, device class, browser family and country, without that endpoint doing anything",
      r.status_code == 200 and all(evs.get("analyze", {}).get(k) == v for k, v in codes.items()) and all(evs.get("enhance", {}).get(k) == v for k, v in codes.items()), evs)
check("the page's language and market come from the request body when the event names none (enhance: lt, lt); what the endpoint says stays (analyze: its own lang de; compose: its own market hu)",
      evs["enhance"].get("lang") == "lt" and evs["enhance"].get("market") == "lt" and evs["analyze"].get("lang") == "de" and evs["analyze"].get("market") == "lt"
      and evs["compose"].get("market") == "hu" and evs["compose"].get("lang") == "lt", evs)
wipe()
call({"lang": "xx", "market": "zz"}, ua=UA_CHROME_WIN, cc=None)
evs = {e["kind"]: e for e in events_today()}
check("a request without a campaign code still gives the classes; an unknown language or market give nothing (no src, no lang, no market) and a missing country header is the country xx",
      evs["enhance"].get("dev") == "desktop" and evs["enhance"].get("br") == "chrome" and evs["enhance"].get("cc") == "xx" and not ({"src", "med", "cmp", "lang", "market"} & set(evs["enhance"])), evs["enhance"])
wipe()
call({"camp": "utm_source=fb&utm_medium=%3Cscript%3E&utm_campaign=a+b&utm_term=203.0.113.7&utm_content=ok"})
e = [x for x in events_today() if x["kind"] == "enhance"][0]
check("a hostile campaign code is cut down to its valid parts on the way in (a script tag, a space, an address)", e.get("src") == "fb" and e.get("cnt") == "ok" and not ({"med", "cmp", "trm"} & set(e)), e)
wipe()
call({"camp": WIRE}, ua="python-requests/2.31.0")
e = [x for x in events_today() if x["kind"] == "enhance"][0]
check("a robot's request is not refused (the endpoint serves it) and its events carry the unknown device class", e.get("dev") == "unknown" and e.get("br") == "other", e)
wipe()
call({"camp": WIRE, "boom": True})
time.sleep(1.5)                  # the error event is written after the reply
errs = [x for x in events_today() if x["kind"] == "error"]
check("the error event of a failed request carries the same codes (errors by device and browser)", len(errs) == 1 and errs[0].get("br") == "fb" and errs[0].get("src") == "fb" and errs[0].get("class") == "500", errs)
wipe()
ok_rec = E.record("checkout", stage="paid", style="solo.clean_iris", eyes=1, src="ig", cmp="c1")
ce = [x for x in events_today() if x["kind"] == "checkout"]
check("outside a request (the payment webhook, the clean-up) an event has no context to take: it carries the codes its caller gives and no device class",
      ok_rec is True and len(ce) == 1 and ce[0].get("src") == "ig" and ce[0].get("cmp") == "c1" and "dev" not in ce[0], ce)
check("run() forgets the context of the request before it (a warm instance serves many)", "_LOCAL.ctx = None" in read(os.path.join(API, "_lib", "iris.py")))

# the order: draft, checkout with the code, payment
CROP, PREV = H.jpeg_b64(512, 1), H.jpeg_b64(1024, 2)


def new_order():
    r = requests.post(BASE + "/api/order", data=json.dumps({"action": "draft", "eye": 1, "crop": CROP, "preview": PREV, "pad": 1.12, "ticket": H.fresh_ticket(), "lang": "de", "ref": "eye-1"}),
                      headers={"Content-Type": "application/json"}, timeout=60)
    j = r.json()
    return j["order"], j["k"]


def checkout(order, k, **kw):
    b = {"order": order, "k": k, "eyes": 1, "style": "deep_nebula", "names": "Anna", "title": "", "lang": "de", "consent_digital": True}
    b.update(kw)
    return requests.post(BASE + "/api/checkout", data=json.dumps(b), headers={"Content-Type": "application/json", "User-Agent": UA_FB_IOS, "x-vercel-ip-country": "LT"}, timeout=60)


def read_json(path):
    with open(os.path.join(STORE, *path.split("/")), encoding="utf-8") as f:
        return json.load(f)


wipe()
O1, K1 = new_order()
r = checkout(O1, K1, camp=WIRE, market="eu")
p = H.Fake.creates[-1][0]
rec = read_json(f"orders/{O1}/order.json")
check("the checkout with a campaign code: Stripe's session metadata src and the order record's checkout.camp are the packed code",
      r.status_code == 200 and p.get("metadata[src]") == CAMP and rec["checkout"].get("camp") == CAMP, (r.status_code, r.text[:200], p.get("metadata[src]"), rec["checkout"].get("camp")))
start = [x for x in events_today() if x["kind"] == "checkout" and x.get("stage") == "start"]
check("and the checkout event of that request has the campaign and the visitor's classes", len(start) == 1 and all(start[0].get(k) == v for k, v in codes.items()), start)
sid = rec["checkout"]["session_id"]
sess = H.pay_session(sid)
body, sig = H.signed_event(sess)
rr = requests.post(BASE + "/api/stripe_webhook", data=body, headers={"Content-Type": "application/json; charset=utf-8", "Stripe-Signature": sig}, timeout=60)
paid = read_json(f"orders/{O1}/paid.json")
pe = [x for x in events_today() if x["kind"] == "checkout" and x.get("stage") == "paid"]
check("the payment (the webhook, with no browser behind it) records the campaign code in paid.json, and the paid event carries the code from the order record but no device class",
      rr.status_code == 200 and paid.get("camp") == CAMP and len(pe) == 1 and pe[0].get("src") == "fb" and pe[0].get("cnt") == "a1-lt-s1" and "dev" not in pe[0] and "br" not in pe[0],
      (rr.status_code, paid.get("camp"), pe))
row = ops.order_row(O1)
check("the admin's order row names the source (camp)", row.get("camp") == CAMP and row["paid"] is True, row.get("camp"))
O2, K2 = new_order()
r = checkout(O2, K2)
p2 = H.Fake.creates[-1][0]
rec2 = read_json(f"orders/{O2}/order.json")
check("an order with no campaign code has none anywhere: no metadata src, no checkout.camp, no camp in the row",
      r.status_code == 200 and "metadata[src]" not in p2 and "camp" not in rec2["checkout"] and ops.order_row(O2).get("camp") is None, (r.status_code, list(rec2["checkout"])))
O3, K3 = new_order()
r = checkout(O3, K3, camp="utm_source=fb&utm_medium=paid&utm_campaign=%3Cscript%3E&utm_term=ok&utm_content=" + "x" * 80)
p3 = H.Fake.creates[-1][0]
check("a hostile campaign code in a checkout is cut down to its valid parts before it reaches Stripe and the record",
      r.status_code == 200 and p3.get("metadata[src]") == "fb|paid||ok" and read_json(f"orders/{O3}/order.json")["checkout"]["camp"] == "fb|paid||ok", p3.get("metadata[src]"))
text = store_text()
check("the whole store after the checkout and the payment holds no address, no user agent and no cookie of the requests",
      not [n for n in ("198.51.100.7", "Mozilla", "FBAN", "FBAV", "iPhone", "x-forwarded-for") if n in text])


# ============================================================================================ 6. the server steps, counted by campaign
section("6. the server steps of a visit are counted by campaign, device class and browser family")
BASE_F = {"src": "fb", "med": "paid", "cmp": "se-p0-test", "trm": "lt-a1-eye", "cnt": "a1-lt-s1", "dev": "ios", "br": "fb", "lang": "lt", "market": "lt"}


def mk2(kind, **kw):
    f = dict(BASE_F)
    f.update(kw)
    return E.build(kind, f)


HK = "|".join(["%s", "fb", "paid", "se-p0-test", "lt-a1-eye", "a1-lt-s1", "lt", "lt", "ios", "fb"])
FX = lambda m, v: f"{m}|{v}|fb|se-p0-test|ios|fb"      # noqa: E731
a = E.summarize([
    mk2("analyze", ok=True, verdict="good", detail=80, res="mp_8_16", ori="portrait", irs="d_420_600", source="camera", locked=True, ms=2400),
    mk2("analyze", ok=True, verdict="weak", detail=30, blocked=True, block_reason="too_blurry", res="mp_1_3", ori="landscape", irs="d_lt280", source="gallery", locked=True, ms=3100),
    mk2("analyze", ok=False, verdict="no_eye", res="mp_3_8", ori="square", ms=1800),
    mk2("enhance", mode="faithful", qa_ok=True, gate="ok", cls="grey", pupil="round", reason="none", ms=14000),
    mk2("enhance", mode="faithful", qa_ok=True, gate="lid", reason="lid_colour_wedge", cls="own", pupil="round", retry="kept2", retry_ms=9000, ms=26000),
    mk2("enhance", mode="faithful", qa_ok=False, gate="fill", reason="fill_void", cls="dark_brown", pupil="slit", ms=15000),
    mk2("compose", style="solo.clean_iris", eyes=1, tiles=0, gate="ok", retake=0, ms=40),
    mk2("compose", style="solo.clean_iris", eyes=1, tiles=1, tile=True, gate="ok", ms=900),
    mk2("compose", style="solo.clean_iris", eyes=1, tiles=1, gate="ok", again=True, size=1024, ms=1400),
    mk2("compose", style="solo.clean_iris", eyes=1, tiles=0, gate="lid", retake=1, ms=30),
    mk2("checkout", stage="start", style="solo.clean_iris", eyes=1, gate="ok"),
    mk2("checkout", stage="paid", style="solo.clean_iris", eyes=1, gate="ok"),
    mk2("help", route="manual", eyes=1),
    mk2("error", endpoint="enhance", reason="model_busy", status=503, **{"class": "busy"}),
])
h, fx = a["hits"], a["fx"]
check("analyses are counted as the step an, the usable ones also as anok, under the codes", h.get(HK % "an") == 3 and h.get(HK % "anok") == 1, {k: v for k, v in h.items() if "|an" in k})
check("the verdicts, the refusal reason and the classes of the photo are counted by campaign, device and browser (and a no_eye photo still has its size and orientation)",
      fx.get(FX("an_verdict", "good")) == 1 and fx.get(FX("an_verdict", "weak")) == 1 and fx.get(FX("an_verdict", "no_eye")) == 1 and fx.get(FX("an_block", "too_blurry")) == 1
      and fx.get(FX("an_res", "mp_8_16")) == 1 and fx.get(FX("an_res", "mp_3_8")) == 1 and fx.get(FX("an_ori", "square")) == 1 and fx.get(FX("an_iris", "d_lt280")) == 1
      and fx.get(FX("an_source", "camera")) == 1 and fx.get(FX("an_lock", "locked")) == 2, {k: v for k, v in fx.items() if k.startswith("an_")})
check("restorations: the step en, the gate code, the reason codes, the colour and pupil class, the second restoration (none when it did not happen) and the colour check",
      h.get(HK % "en") == 3 and fx.get(FX("en_gate", "ok")) == 1 and fx.get(FX("en_gate", "lid")) == 1 and fx.get(FX("en_reason", "lid_colour_wedge")) == 1 and fx.get(FX("en_reason", "fill_void")) == 1
      and FX("en_reason", "none") not in fx and fx.get(FX("en_cls", "dark_brown")) == 1 and fx.get(FX("en_pupil", "slit")) == 1 and fx.get(FX("en_retry", "kept2")) == 1 and fx.get(FX("en_retry", "none")) == 2
      and fx.get(FX("en_qa", "fail")) == 1 and fx.get(FX("en_qa", "ok")) == 2, {k: v for k, v in fx.items() if k.startswith("en_")})
check("a set of eyes is counted once by its first request (rs) with its gate, its retakes and its eye count; a repeat of the look (again) and a tile are not sets; a drawn preview (not a tile) is sv",
      h.get(HK % "rs") == 3 and fx.get(FX("set_gate", "ok")) == 2 and fx.get(FX("set_gate", "lid")) == 1 and fx.get(FX("set_retake", 0)) == 2 and fx.get(FX("set_retake", 1)) == 1
      and h.get(HK % "sv") == 1 and fx.get(FX("sv_style", "solo.clean_iris")) == 1, {k: v for k, v in list(h.items()) + list(fx.items()) if "rs" in k or "set_" in k or "sv" in k})
check("the checkout and the payment are co and pd, the manual route is help", h.get(HK % "co") == 1 and h.get(HK % "pd") == 1 and h.get(HK % "help") == 1)
check("errors are counted by endpoint, class and reason, and the requests behind them by endpoint (the error rate per endpoint)",
      fx.get(FX("err_ep", "enhance")) == 1 and fx.get(FX("err_cls", "busy")) == 1 and fx.get(FX("err_reason", "model_busy")) == 1 and fx.get(FX("req", "analyze")) == 3 and fx.get(FX("req", "enhance")) == 3
      and fx.get(FX("req", "compose")) == 4, {k: v for k, v in fx.items() if k.startswith(("err_", "req"))})
check("server times are counted in the buckets of HIST_MS by step, device and browser", a["fx_ms"].get(f"analyze|ios|fb|{E.hist_bucket(2400)}") == 1 and a["fx_ms"].get(f"enhance|ios|fb|{E.hist_bucket(26000)}") == 1
      and a["fx_ms"].get(f"compose|ios|fb|{E.hist_bucket(1400)}") == 1 and sum(a["fx_ms"].values()) == 3 + 3 + 1, a["fx_ms"])
b = E.summarize([E.build("analyze", {"ok": True, "verdict": "good"}), E.build("enhance", {"gate": "ok"})])
check("an event with no campaign and no classes (an old client, a script) is counted under dashes, nothing breaks", b["hits"].get("an|-|-|-|-|-|-|-|-|-") == 1 and b["fx"].get("en_gate|ok|-|-|-|-") == 1, b["fx"])
check("the event kinds the visitor pages do not read (master, exp) add nothing to the new tables",
      not E.summarize([E.build("master", {"step": "art", "order": "250101-aaaaaaaa", "style": "x"}), E.build("exp", {"stage": "visit", "exp": "e", "variant": "v"})])["fx"])
E.TABLE_KEYS_MAX.update(fx=4, hits=4)
many = E.summarize([mk2("analyze", ok=True, verdict="good", cmp=f"c{i}") for i in range(30)])
check("the fx and hits tables are capped like the counter's: a stranger's endless campaign names end up under 'overflow' and nothing is lost", len(many["fx"]) <= 5 and sum(many["fx"].values()) == 30 * 2 and sum(many["hits"].values()) == 60 and "overflow" in many["fx"], (len(many["fx"]), many["fx"].get("overflow")))
E.TABLE_KEYS_MAX.update(old_cap)
res = [E.photo_classes(*x) for x in ((4032, 3024), (3024, 4032), (1000, 1000), (800, 600, 150), (8000, 6000, 700), (0, 10), (None, None, 300), (True, True), (float("nan"), 10), (3000, 3000, 419.9))]
check("photo_classes: megapixel class, orientation (a square within 5 percent) and iris size class; zero, missing, boolean and non-finite numbers give none",
      res == [("mp_8_16", "landscape", None), ("mp_8_16", "portrait", None), ("mp_1_3", "square", None), ("mp_lt1", "landscape", "d_lt280"), ("mp_40p", "landscape", "d_600p"), (None, None, None),
              (None, None, "d_280_420"), (None, None, None), (None, None, None), ("mp_8_16", "square", "d_280_420")], res)
big = E.summarize([mk2(rnd.choice(["analyze", "enhance", "compose"]), **({"ok": True, "verdict": rnd.choice(["good", "ok", "weak"]), "res": rnd.choice(["mp_1_3", "mp_8_16"]), "ms": rnd.randrange(8000)} if True else {}),
                      src=rnd.choice(srcs), cmp=rnd.choice(cmps), dev=rnd.choice(["ios", "android", "desktop"]), br=rnd.choice(["fb", "ig", "chrome", "safari", "tt", "wv"])) for _ in range(6000)])
size = len(json.dumps(dict(big, v=1, day="x")))
print(f"   6000 server events of random combinations: {len(big['fx'])} fx keys, {len(big['hits'])} hit keys, {size // 1024} KB", flush=True)
check("a day of 6000 server events with every combination of campaign, device and browser stays under the 2 MB a stored day is read back with", size < E.ROLLUP_MAX_BYTES, size)
check("and the Statistika page's slim copy leaves the new tables out too", not ({"fx", "fx_ms"} & set(ops._slim(big))))


total = len(RESULTS)
passed = sum(RESULTS)
print(f"\n{passed} of {total} passed", flush=True)
sys.exit(0 if passed == total else 1)
