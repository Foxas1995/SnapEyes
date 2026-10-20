# -*- coding: utf-8 -*-
"""The anonymous feedback box of /try (2026-10-20, api/_lib/feedback.py, api/checkout.py, api/_lib/events.py kind "fb", src/try/Feedback.tsx): six chips and an optional text, no e-mail,
no name, kept 90 days. Suite v3feedback.

  1. the text filter: what is kept, what is dropped (contact details, links, markup, noise, a paste), how it is cleaned and cut
  2. the answer over HTTP: what is stored (an event of codes, and the text apart from it), what is refused (a wrong chip, a robot, the honeypot, a flood), the fields that are dropped,
     duplicates, a text that could not be stored
  3. the kill switch: SNAPEYES_FEEDBACK read once at import, health and checkout say feedback false, the answer keeps nothing
  4. the day's counts: the fx metrics of the chips, the style on screen, the block reason and what became of the texts; the report of the admin page
  5. retention and the owner's hands: the texts newest first with filters, delete by id, the daily clean-up deletes them after 90 days (and the events after twelve months), nothing else
  6. no personal data: after hostile requests (addresses, user agents, cookies, typed e-mail addresses and telephone numbers) none of it is anywhere in the store
  7. the admin actions over HTTP: the key is needed, the report keeps its keys on the wire, a deleted text is gone and the audit log never holds it
No network, no image model, no real eye. Run by suites/run_main.sh as v3feedback.
    python test_feedback.py   prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure"""
import atexit
import importlib.util
import json
import os
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
TMP = tempfile.mkdtemp(prefix="snapeyes_v3feedback_")
atexit.register(shutil.rmtree, TMP, ignore_errors=True)
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, HARNESS)
sys.path.insert(0, HERE)
import harness as H  # noqa: E402

STORE = os.path.join(TMP, "store")
stub = H.start_stub()
H.setup_env(STORE, stub.server_address[1])
os.environ["CRON_SECRET"] = "feedback-cron-secret-for-tests-0123456789"      # the events are stored only while the daily clean-up can delete them
os.environ["SNAPEYES_ADMIN_SECRET"] = "feedback-admin-secret-for-tests-0123456789abcdef01"
sys.path.insert(0, API)
import requests  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import counter as C  # noqa: E402
from _lib import events as E  # noqa: E402
from _lib import feedback as F  # noqa: E402
from _lib import store, ops, traffic as TR  # noqa: E402

for name in ("admin",):
    spec_m = importlib.util.spec_from_file_location(name, os.path.join(API, name + ".py"))
    mod = importlib.util.module_from_spec(spec_m)
    spec_m.loader.exec_module(mod)
    H.MODS[name] = mod
api = H.start_api()
BASE = f"http://127.0.0.1:{api.server_address[1]}"
C.BEACON_WAIT = 10.0
F.WAIT = 10.0                  # the answer waits for its event as long as it needs here
E.WAIT = 10.0                  # a slow disk must not make a check flaky: the event waits for its write as long as it needs here

UA_SAFARI_IOS = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
UA_FB_IOS = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBAV/430.0.0.0;FBBV/1]"
UA_CHROME_WIN = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
UA_BOTS = ["Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)", "python-requests/2.31.0", "curl/8.4.0", "", "Mozilla/5.0",
           "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/118.0.0.0 Safari/537.36"]
CAMP = "utm_source=fb&utm_medium=paid&utm_campaign=se-p0-test&utm_term=lt-a1-eye&utm_content=a1-lt-s1"
GOOD_TEXT = "Spalvos šiek tiek per šaltos, norėjau šiltesnių."


def day():
    return time.strftime("%Y-%m-%d", time.gmtime())


def folder_json(folder):
    out = []
    for _ in range(60):
        names = sorted(os.listdir(folder)) if os.path.isdir(folder) else []
        if not any(".part" in n for n in names):
            break
        time.sleep(0.1)
    for n in names:
        if n.endswith(".json"):
            with open(os.path.join(folder, n), encoding="utf-8") as f:
                out.append(json.load(f))
    return out


def events_today():
    return folder_json(os.path.join(STORE, "ops", "events", day()))


def rows_today():
    return folder_json(os.path.join(STORE, "ops", "feedback", day()))


def wipe():
    shutil.rmtree(os.path.join(STORE, "ops"), ignore_errors=True)
    E._SEEN.update({"all": [], "error": [], "exp": [], "help": [], "hit": [], "fb": [], "day": "", "errors_today": 0, "exp_day": "", "exp_today": 0,
                    "help_day": "", "help_today": 0, "hit_day": "", "hit_today": 0, "fb_day": "", "fb_today": 0})
    F._CLIENTS.clear()
    del F._DUPS[:]
    C._CLIENTS.clear()


_N = [0]


def fb(place="result", chip="love", x="solo.powder", eyes=1, t=None, hp=None, ua=UA_SAFARI_IOS, ip=None, cc="LT", camp=CAMP, ct="application/json", headers=None, lang="lt", market="lt", raw=None):
    """One answer over HTTP. A new address each time unless ip is given (the per-client limit is a check of its own)."""
    if ip is None:
        _N[0] += 1
        ip = f"198.51.{(_N[0] // 250) % 250}.{_N[0] % 250 + 1}"
    a = {"w": place, "c": chip}
    for k, v in (("x", x), ("eyes", eyes), ("t", t), ("hp", hp)):
        if v is not None:
            a[k] = v
    body = raw if raw is not None else {"feedback": a, "camp": camp, "lang": lang, "market": market}
    h = {"User-Agent": ua, "x-forwarded-for": ip, "Content-Type": ct}
    if cc is not None:
        h["x-vercel-ip-country"] = cc
    h.update(headers or {})
    return requests.post(BASE + "/api/checkout", data=json.dumps(body), headers=h, timeout=30)


def j(r):
    """The JSON of a reply without the call's own time (iris.run adds ms to every answer)."""
    d = r.json()
    d.pop("ms", None)
    return d


def day_files(d):
    """The files kept for a day of texts (an emptied day folder may stay on a local disk)."""
    folder = os.path.join(STORE, "ops", "feedback", d)
    return sorted(os.listdir(folder)) if os.path.isdir(folder) else []


def admin(action, **body):
    key = ops.mint_admin_key(3600)
    return requests.post(BASE + "/api/admin", data=json.dumps(dict(body, action=action)), headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"}, timeout=60)


def store_text():
    out = []
    for root, _d, files in os.walk(STORE):
        for n in files:
            with open(os.path.join(root, n), "rb") as f:
                out.append(f.read().decode("utf-8", "replace"))
    return "\n".join(out)


# ============================================================================================ 1. the text filter
section("1. the text filter")
KEEP = ["Spalvos šiek tiek per šaltos, norėjau šiltesnių.", "Nagyon szép, de a színek nem stimmelnek.", "Das gefällt mir sehr gut, danke!", "I love it, thank you so much", "Too yellow for my eye ❤️",
        "Waited 20 seconds, then it worked", "ok"]
check("an ordinary answer is kept as it is, in all four languages, with an emoji, a short word and a number of seconds", all(F.clean_text(t) == (t, None) for t in KEEP), [F.clean_text(t) for t in KEEP])
CONTACT = ["mail me: a.b@example.com", "vardas@", "my number is +370 612 34567", "00370 612 34567", "call 612-345-67 89", "write to me on gmail", "hotmail please", "tel. 8 612 34567 thanks"]
check("a text with an at sign, a mail host or a telephone number is dropped as contact", all(F.clean_text(t) == ("", "contact") for t in CONTACT), [F.clean_text(t) for t in CONTACT])
LINKS = ["https://evil.example/pay", "see www.shop-now.com", "visit shop.lt now", "bit.ly/abc", "example.com/x", "//cdn.example/x.js", "ftp://x"]
check("a text with a link is dropped as a link", all(F.clean_text(t) == ("", "link") for t in LINKS), [F.clean_text(t) for t in LINKS])
JUNK = ["<script>alert(1)</script>", "aaaaaaaaaaaa", "!!!!!!?????", "1234", "{{template}}", "ok ok ok ok ok ok", "x" * 901, "union select password from users", "javascript:void(0)", "a &amp; b &#39;"]
check("markup, a repeated character or word, a text with no letter and a paste are dropped as junk", all(F.clean_text(t) == ("", "junk") for t in JUNK), [(t[:20], F.clean_text(t)) for t in JUNK if F.clean_text(t) != ("", "junk")])
check("white space is one space, control characters are spaces, an empty or blank text is no text", F.clean_text(" \n a   b\t c ") == ("a b c", None) and F.clean_text("good" + chr(0) + chr(7) + " colours") == ("good colours", None)
      and F.clean_text("") == ("", None) and F.clean_text(None) == ("", None) and F.clean_text("  \n\t ") == ("", None), (F.clean_text(" \n a   b\t c "), F.clean_text("good" + chr(0) + chr(7) + " colours")))
long_text = "abcde fghij " * 40
cut, why = F.clean_text(long_text)
check("a text over 300 characters (but not a paste) is cut to 300 and still kept", why is None and len(cut) <= F.TEXT_MAX and cut.startswith("abcde fghij abcde") and len(long_text) <= F.PASTE_MAX, (len(cut), why))
check("a value that is no string is junk", F.clean_text(5) == ("", "junk") and F.clean_text(["a"]) == ("", "junk") and F.clean_text({"a": 1}) == ("", "junk"))

# ============================================================================================ 2. the answer over HTTP
section("2. the answer over HTTP")
wipe()
r = fb("result", "colour", x="solo.gold", eyes=2, t=GOOD_TEXT)
evs, rows = events_today(), rows_today()
check("an answer with a text is counted and its text kept: {ok, counted, text: kept}", r.status_code == 200 and j(r) == {"ok": True, "counted": True, "text": "kept"} and len(evs) == 1 and len(rows) == 1, (r.status_code, r.text, len(evs), len(rows)))
ev, row = (evs or [{}])[0], (rows or [{}])[0]
check("the event holds codes only: kind fb, the place, the chip, the style, the eyes, txt kept, the campaign code, the language and market, the device class, the browser family, the country",
      ev.get("kind") == "fb" and ev.get("w") == "result" and ev.get("c") == "colour" and ev.get("x") == "solo.gold" and ev.get("eyes") == 2 and ev.get("txt") == "kept"
      and (ev.get("src"), ev.get("med"), ev.get("cmp"), ev.get("trm"), ev.get("cnt")) == ("fb", "paid", "se-p0-test", "lt-a1-eye", "a1-lt-s1") and ev.get("lang") == "lt" and ev.get("market") == "lt"
      and ev.get("dev") == "ios" and ev.get("br") == "safari" and ev.get("cc") == "lt", ev)
check("the event never holds the text, and every key of it is one of the whitelist", GOOD_TEXT not in json.dumps(ev, ensure_ascii=False) and set(ev) <= set(E.FIELDS["fb"]) | {"v", "kind", "t", "ms"}, set(ev) - set(E.FIELDS["fb"]))
check("the text row holds the text, the chip, the place, the context code, the eyes and the same classes, and nothing else",
      row.get("txt") == GOOD_TEXT and row.get("w") == "result" and row.get("c") == "colour" and row.get("x") == "solo.gold" and row.get("eyes") == 2 and row.get("dev") == "ios" and row.get("cmp") == "se-p0-test"
      and set(row) <= {"v", "t", "w", "c", "txt", "x", "eyes", "src", "med", "cmp", "trm", "cnt", "dev", "br", "cc", "lang", "market"}, sorted(row))
wipe()
r = fb("retake", "fine", x="too_blurry")
check("an answer with no text is counted: text none, an event with no txt, no text row", j(r) == {"ok": True, "counted": True, "text": "none"} and len(events_today()) == 1 and "txt" not in events_today()[0] and not rows_today(), r.text)
wipe()
bad = [("result", "unclear"), ("retake", "love"), ("elsewhere", "love"), ("result", "x"), ("result", ""), ("result", None), (None, "love"), ("result", ["love"])]
rs = [fb(w, c) for w, c in bad]
check("a chip that is not one of the six of its place, or an unknown place, is not counted (and answered 200)", all(x.status_code == 200 and x.json().get("counted") is False for x in rs) and not events_today(), [x.text for x in rs])
wipe()
rs = [fb(raw=b) for b in ({"feedback": "love"}, {"feedback": None}, {"feedback": [1]}, {"feedback": {}}, {"feedback": 7})]
check("a feedback member that is no object, or an empty one, is not counted", all(x.status_code == 200 and x.json().get("counted") is False for x in rs) and not events_today(), [x.text for x in rs])
wipe()
fb("result", "love", x="a@b.com", eyes=9)
fb("result", "love", x="x" * 50, eyes=True)
fb("result", "love", x="198.51.100.7", eyes="3")
fb("result", "love", x="Powder Burst", eyes=0)
fb("result", "love", x="solo.universe", eyes=3)
evs = events_today()
check("a context code that is not a short code (an e-mail, too long, an address, a space) and a number of eyes outside 1 to 8 (or no number) are dropped from the event, the answer still counts",
      len(evs) == 5 and sum(1 for e in evs if "x" in e) == 1 and [e.get("x") for e in evs if "x" in e] == ["solo.universe"] and sorted(e.get("eyes") for e in evs if "eyes" in e) == [3], [(e.get("x"), e.get("eyes")) for e in evs])
wipe()
r = fb("result", "love", hp="http://spam.example")
r2 = fb("result", "love", raw={"feedback": {"w": "result", "c": "love", "hp": 1}, "lang": "lt", "market": "lt"})
check("a filled honeypot field is not counted and not kept (the page never fills it)", r.json().get("counted") is False and r2.json().get("counted") is False and not events_today() and not rows_today(), (r.text, r2.text))
wipe()
rs = [fb("result", "love", ua=ua) for ua in UA_BOTS]
check("a robot's user agent is not counted", all(x.json().get("counted") is False for x in rs) and not events_today(), [x.text for x in rs])
wipe()
r1 = fb("result", "love", ct="text/plain")
r2 = fb("result", "love", headers={"Origin": "https://evil.example"})
check("a request that is not JSON, or that comes from another origin, is refused by the route before the answer is looked at", r1.status_code in (400, 415) and r2.status_code == 403 and not events_today(), (r1.status_code, r2.status_code))
wipe()
rs = [fb("result", "love", ip="203.0.113.9") for _ in range(F.CLIENT_MAX + 2)]
check("a client is held to CLIENT_MAX answers in CLIENT_WINDOW seconds (the rest are answered 200 and not counted); another client still counts",
      [x.json().get("counted") for x in rs] == [True] * F.CLIENT_MAX + [False] * 2 and fb("result", "love", ip="203.0.113.10").json().get("counted") is True, [x.json().get("counted") for x in rs])
wipe()
old_rate = E.RATE["fb"]
E.RATE["fb"] = (3, 60.0)
rs = [fb("result", "love") for _ in range(6)]
check("an instance counts at most RATE['fb'] answers a minute", sum(1 for x in rs if x.json().get("counted")) == 3 and len(events_today()) == 3, len(events_today()))
E.RATE["fb"] = old_rate
wipe()
old_day = E.FB_DAY_MAX
E.FB_DAY_MAX = 2
rs = [fb("result", "love") for _ in range(5)]
check("and at most FB_DAY_MAX a UTC day", sum(1 for x in rs if x.json().get("counted")) == 2 and len(events_today()) == 2, len(events_today()))
E.FB_DAY_MAX = old_day
wipe()
r1, r2 = fb("result", "colour", t=GOOD_TEXT), fb("result", "colour", t=GOOD_TEXT.upper())
evs = events_today()
check("the same text twice (any case) is kept once: the second answer is counted with txt dup and its text dropped", r1.json()["text"] == "kept" and r2.json()["text"] == "dropped" and len(rows_today()) == 1
      and sorted(e.get("txt") for e in evs) == ["dup", "kept"], (r1.text, r2.text, [e.get("txt") for e in evs]))
wipe()
r = fb("result", "price", t="write to me at foo@bar.com please")
evs = events_today()
check("a text with contact details is not kept, the answer is counted with txt contact, and the page is told (text dropped)", j(r) == {"ok": True, "counted": True, "text": "dropped"} and len(evs) == 1 and evs[0].get("txt") == "contact" and not rows_today(), (r.text, evs))
wipe()
real_put = store.put
def failing_put(path, *a, **k):
    if path.startswith("ops/feedback/"):
        raise RuntimeError("disk full")
    return real_put(path, *a, **k)
store.put = failing_put
try:
    r = fb("result", "colour", t=GOOD_TEXT)
finally:
    store.put = real_put
check("a text that cannot be stored is reported lost, and the answer is still counted", j(r) == {"ok": True, "counted": True, "text": "lost"} and len(events_today()) == 1 and not rows_today(), r.text)

# ============================================================================================ 3. the kill switch
section("3. the kill switch SNAPEYES_FEEDBACK")
wipe()
h_on, c_on = requests.get(BASE + "/api/health", timeout=20).json(), requests.get(BASE + "/api/checkout", timeout=20).json()
check("while the box is on, GET /api/health and GET /api/checkout say feedback true (/try shows it)", h_on.get("feedback") is True and c_on.get("feedback") is True, (h_on.get("feedback"), c_on.get("feedback")))
L.FEEDBACK_ON = False
try:
    h_off, c_off = requests.get(BASE + "/api/health", timeout=20).json(), requests.get(BASE + "/api/checkout", timeout=20).json()
    r = fb("result", "love", t=GOOD_TEXT)
    check("with the switch off both say feedback false, and an answer that arrives anyway is answered on false, counted false, and stores nothing",
          h_off.get("feedback") is False and c_off.get("feedback") is False and r.status_code == 200 and r.json().get("counted") is False and r.json().get("on") is False and not events_today() and not rows_today(),
          (h_off.get("feedback"), c_off.get("feedback"), r.text))
finally:
    L.FEEDBACK_ON = True
check("back on, it counts again", fb("result", "love").json().get("counted") is True)


def flag(value):
    env = dict(os.environ)
    env.pop("SNAPEYES_FEEDBACK", None)
    if value is not None:
        env["SNAPEYES_FEEDBACK"] = value
    out = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, sys.argv[1]); from _lib import iris; print(iris.FEEDBACK_ON)", API], env=env, capture_output=True, text=True, timeout=300)
    return out.stdout.strip().splitlines()[-1] if out.stdout.strip() else out.stderr[-200:]


cases = {None: "True", "": "True", "on": "True", "1": "True", "yes": "True", "true": "True", "off": "False", "OFF": "False", " Off ": "False", "0": "False", "false": "False", "no": "False",
         chr(0xFEFF) + "off": "False", chr(0xFEFF) + "on": "True"}
got = {k: flag(k) for k in cases}
check("SNAPEYES_FEEDBACK: unset, empty, on, 1, yes and true are on; off, 0, false and no (any case, with white space or a BOM) are off", got == cases, {k: (got[k], cases[k]) for k in cases if got[k] != cases[k]})
flag_none = os.environ.pop("CRON_SECRET")
try:
    check("with no CRON_SECRET (the daily clean-up could not delete the texts) the box says false: on() and health", F.on() is False and requests.get(BASE + "/api/health", timeout=20).json().get("feedback") is False)
finally:
    os.environ["CRON_SECRET"] = flag_none
check("and with it back it is true again", F.on() is True)

# ============================================================================================ 4. the counts
section("4. the day's counts")
wipe()
fb("result", "love", x="solo.powder", t=GOOD_TEXT)
fb("result", "colour", x="solo.gold", t="too grey")
fb("result", "colour", x="solo.gold")
fb("result", "price", x="solo.powder", t="see www.example.com")
fb("retake", "unclear", x="too_blurry", ua=UA_FB_IOS)
fb("retake", "unclear", x="too_blurry", ua=UA_FB_IOS, t="not clear")
fb("retake", "effort", x="pupil_too_large", ua=UA_CHROME_WIN, camp="ref=google")
agg = E.summarize(events_today())
fx = agg["fx"]
want = {"fb_result|love|fb|se-p0-test|ios|safari": 1, "fb_result|colour|fb|se-p0-test|ios|safari": 2, "fb_result|price|fb|se-p0-test|ios|safari": 1, "fb_retake|unclear|fb|se-p0-test|ios|fb": 2,
        "fb_retake|effort|google|-|desktop|chrome": 1, "fb_style|colour:solo.gold|fb|se-p0-test|ios|safari": 2, "fb_style|love:solo.powder|fb|se-p0-test|ios|safari": 1, "fb_block|unclear:too_blurry|fb|se-p0-test|ios|fb": 2,
        "fb_block|effort:pupil_too_large|google|-|desktop|chrome": 1, "fb_text|kept|fb|se-p0-test|ios|safari": 2, "fb_text|link|fb|se-p0-test|ios|safari": 1, "fb_text|kept|fb|se-p0-test|ios|fb": 1}
check("the day's counts hold the chips by campaign, device class and browser family, the chip with the style on screen or the block reason, and what became of the texts", all(fx.get(k) == v for k, v in want.items()),
      {k: (fx.get(k), v) for k, v in want.items() if fx.get(k) != v})
check("an event of kind fb is counted in the kinds and nowhere else of the counter's tables (no hit)", agg["kinds"].get("fb") == 7 and not agg["hits"] and "hit" not in agg["kinds"], agg["kinds"])
rep = TR.feedback_report(agg, {}, "cmp")
chips = {v: sum(g.values()) - g.get("all", 0) if "all" in g else sum(g.values()) for v, g in rep["fx"]["fb_result"].items()}
check("the report of the admin page: the result chips split by campaign", rep["by"] == "cmp" and set(rep["fx"]) == {"fb_result", "fb_retake", "fb_style", "fb_block", "fb_text"}
      and rep["fx"]["fb_result"]["colour"].get("fb / se-p0-test") == 2 and rep["fx"]["fb_retake"]["effort"].get("google / -") == 1 and chips.get("love") == 1, rep["fx"]["fb_result"])
rep_dev = TR.feedback_report(agg, {"dev": "desktop"}, None)
check("and filtered by the device class", rep_dev["fx"].get("fb_retake") == {"effort": {"all": 1}} and "fb_result" not in rep_dev["fx"], rep_dev["fx"])
check("the lists agree with the page's: the places of events.py and feedback.py, and a chip set of six per place", E.FB_PLACES == F.PLACES and all(len(F.CHIPS[p]) == 6 and len(set(F.CHIPS[p])) == 6 for p in F.PLACES), (E.FB_PLACES, F.PLACES))
check("no field of the fb event can hold a text: every one is a short code, a number or a flag, apart from the ones of the counter's own kind", all(t in ("c", "n") for t in E.FIELDS["fb"].values()) and "t" not in E.FIELDS["fb"] and "txt" in E.FIELDS["fb"] and E.FIELDS["fb"]["txt"] == "c")
big = E.summarize([dict(E.build("fb", {"w": "result", "c": "love", "x": "solo.gold", "txt": "kept", "src": "fb", "cmp": f"c{i}", "dev": "ios", "br": "safari"}), t=time.time()) for i in range(3200)])
check("a day of fb events with many distinct campaign codes stays under the cap of the fx table (the rest is counted as overflow)", len(big["fx"]) <= E.TABLE_KEYS_MAX["fx"] + 1 and big["fx"].get("overflow", 0) > 0, len(big["fx"]))

# ============================================================================================ 5. retention and the owner's hands
section("5. retention and the owner's hands")
wipe()
fb("result", "colour", x="solo.gold", t="first one", ua=UA_SAFARI_IOS)
time.sleep(1.1)
fb("retake", "unclear", x="too_blurry", t="second one", ua=UA_FB_IOS)
time.sleep(1.1)
fb("result", "price", x="solo.powder", t="third one, from a computer", ua=UA_CHROME_WIN)
rows, more = F.texts(30)
check("the stored texts come newest first, each with its id, its day and its time", [r["txt"] for r in rows] == ["third one, from a computer", "second one", "first one"] and not more and all(F.id_path(r["id"]) and r["day"] == day() and len(r["at"]) == 6 for r in rows), [r.get("txt") for r in rows])
fl, _m = F.texts(30, {"dev": "ios"})
fl2, _m = F.texts(30, {"br": "fb"})
fl3, _m = F.texts(30, {"cmp": "se-p0-test", "dev": "desktop"})
check("a filter keeps the rows that match its device class, browser family, campaign, language or market", [r["txt"] for r in fl] == ["second one", "first one"] and [r["txt"] for r in fl2] == ["second one"] and [r["txt"] for r in fl3] == ["third one, from a computer"],
      ([r["txt"] for r in fl], [r["txt"] for r in fl2], [r["txt"] for r in fl3]))
few, more = F.texts(30, limit=2)
check("at most the limit of rows are listed, and more says there are others", len(few) == 2 and more is True)
victim = rows[1]["id"]
check("a text is deleted by its id, once (the second time it is gone), and a bad id is refused", F.delete_text(victim) is True and F.delete_text(victim) is False and [r["txt"] for r in F.texts(30)[0]] == ["third one, from a computer", "first one"], None)
try:
    F.delete_text("../../orders/x")
    ok = False
except ValueError:
    ok = True
check("an id that is a path (or anything but 8 digits, 6 digits, 12 hex) is refused, never turned into a path of the store", ok and F.id_path("../x") is None and F.id_path("20261020-123105-0123456789ab") == "ops/feedback/2026-10-20/123105-0123456789ab.json" and F.row_id("ops/feedback/2026-10-20/123105-0123456789ab.json") == "20261020-123105-0123456789ab")
# the clean-up
for d, n in (("2026-01-01", "010101-aaaaaaaaaaaa.json"), ("2026-07-01", "010101-bbbbbbbbbbbb.json"), (time.strftime("%Y-%m-%d", time.gmtime(time.time() - 89 * 86400)), "010101-cccccccccccc.json")):
    store.put(f"ops/feedback/{d}/{n}", store.json_bytes({"v": 1, "t": 1, "w": "result", "c": "love", "txt": "old " + d}), "application/json", upsert=True)
store.put("ops/events/2024-01-01/000000-aaaaaaaaaaaa.json", store.json_bytes({"v": 1, "kind": "fb", "t": 1, "w": "result", "c": "love"}), "application/json", upsert=True)
cut90 = F.purge_text(days=90, yes=False)
left = sorted(os.listdir(os.path.join(STORE, "ops", "feedback")))
check("the dry run of the clean-up counts the texts older than 90 days and deletes none", cut90["texts"] == 2 and cut90["days"] == 2 and len(left) == 4 and all(day_files(d) for d in left), (cut90, left))
res = E.purge_old(days=365, yes=True)
left = sorted(os.listdir(os.path.join(STORE, "ops", "feedback")))
kept_days = sorted(d for d in left if day_files(d))
check("the daily clean-up (events.purge_old) deletes the texts older than 90 days with the events older than twelve months, and keeps the younger ones", res.get("ok") is True and res.get("feedback") == 2 and res.get("events") == 1
      and kept_days == sorted([day(), time.strftime("%Y-%m-%d", time.gmtime(time.time() - 89 * 86400))]) and not os.path.exists(os.path.join(STORE, "ops", "events", "2024-01-01", "000000-aaaaaaaaaaaa.json")), (res, kept_days))
check("and it left today's events and the 89 day old text alone", len(events_today()) == 3 and any("old" in r.get("txt", "") for r in folder_json(os.path.join(STORE, "ops", "feedback", time.strftime("%Y-%m-%d", time.gmtime(time.time() - 89 * 86400))))))

# ============================================================================================ 6. no personal data
section("6. no personal data")
wipe()
HOSTILE_IP, HOSTILE_UA, COOKIE = "203.0.113.77", "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Version/17.0 Mobile/15E148 Safari/604.1 SECRETDEVICE-4711", "session=abcdef123456"
foreign = fb("result", "colour", ip=HOSTILE_IP, ua=HOSTILE_UA, headers={"Referer": "https://example.org/private?id=991"}, t=GOOD_TEXT)
fb("result", "colour", ip=HOSTILE_IP, ua=HOSTILE_UA, headers={"Cookie": COOKIE, "Referer": BASE + "/try?utm_source=fb&private=991", "x-real-ip": HOSTILE_IP}, t=GOOD_TEXT)
fb("result", "colour", ip=HOSTILE_IP + "1", t="please call me on +370 699 12345 or mail jonas.petraitis@example.org", camp="utm_source=fb&utm_campaign=jonas.petraitis@example.org")
fb("retake", "fine", ip=HOSTILE_IP + "2", t="my name is Jonas Petraitis, see https://example.org/jonas")
everything = store_text()
check("a request that names another site as its origin is refused (403); and no address, user agent, cookie or referrer of a request is anywhere in the store", foreign.status_code == 403
      and all(x not in everything for x in (HOSTILE_IP, "SECRETDEVICE-4711", COOKIE, "abcdef123456", "example.org/private", "id=991", "private=991", "/try?utm")), (foreign.status_code, None))
check("a typed e-mail address, telephone number or link is anywhere only if the filter let it through (it does not): none is in the store", all(x not in everything for x in ("jonas.petraitis", "699 12345", "+370 699", "example.org/jonas")), None)
check("the answers were counted; the texts with contact details or a link were dropped, the others kept", len(events_today()) == 3 and sorted(e.get("txt") for e in events_today()) == ["contact", "kept", "link"] and len(rows_today()) == 1, [e.get("txt") for e in events_today()])
check("the campaign code that is not a code (an e-mail) is cut down to nothing before it reaches an event", all("@" not in json.dumps(e) for e in events_today()))
check("the only thing of a visitor in the store is the text row, and its keys are the whitelist", all(set(r) <= {"v", "t", "w", "c", "txt", "x", "eyes", "src", "med", "cmp", "trm", "cnt", "dev", "br", "cc", "lang", "market"} for r in rows_today()))

# ============================================================================================ 7. the admin actions over HTTP
section("7. the admin actions over HTTP")
wipe()
fb("result", "colour", x="solo.gold", t=GOOD_TEXT)
time.sleep(1.1)                    # the names of the rows run to the second: two answers in one second have no order
fb("retake", "unclear", x="too_blurry", ua=UA_FB_IOS, t="neaišku, ką daryti")
fb("result", "love", x="solo.powder")
nokey = requests.post(BASE + "/api/admin", data=json.dumps({"action": "feedback"}), headers={"Content-Type": "application/json"}, timeout=30)
rep = admin("feedback", days=30)
body = rep.json()
direct = ops.ACTIONS["feedback"]({"days": 30}, {"kind": "admin-v1", "exp": int(time.time()) + 3600})
check("the report needs the admin key; with it every key of the action's own answer arrives, none replaced (the call's own time is a key of its own)", nokey.status_code == 403 and rep.status_code == 200 and body.get("ok") is True
      and all(k in body and type(body[k]) is type(direct[k]) for k in direct), (nokey.status_code, rep.status_code, [k for k in direct if k not in body]))
check("the report has the counts (by campaign), the texts newest first, the retention in days and whether the box is on", body.get("by") == "cmp" and set(body["fx"]) >= {"fb_result", "fb_retake", "fb_text"} and [t["txt"] for t in body["texts"]] == ["neaišku, ką daryti", GOOD_TEXT]
      and body.get("retention_days") == 90 and body.get("on") is True and body.get("texts_more") is False, body.get("texts"))
tid = body["texts"][0]["id"]
rd = admin("feedback_delete", id=tid)
again = admin("feedback_delete", id=tid)
bad = admin("feedback_delete", id="../../orders")
time.sleep(0.5)
audit = "\n".join(open(os.path.join(dp, f), encoding="utf-8").read() for dp, _d, fs in os.walk(os.path.join(STORE, "ops", "audit")) for f in fs)
check("a text is deleted by the owner (the second time not_found, a bad id is a 400), it is gone from the report, and the audit log has the action but not the text", rd.status_code == 200 and rd.json().get("result") == "deleted"
      and again.json().get("result") == "not_found" and bad.status_code == 400 and [t["txt"] for t in admin("feedback", days=30).json()["texts"]] == [GOOD_TEXT]
      and "feedback_delete" in audit and "neaišku" not in audit and GOOD_TEXT not in audit, (rd.text, again.text, bad.status_code))
fl = admin("feedback", days=30, dev="desktop").json()
check("the filters of the page reach the texts and the counts", fl["texts"] == [] and "fb_result" not in fl["fx"] or all(v.get("all", 0) == 0 for v in fl["fx"].get("fb_result", {}).values()), fl["texts"])

total = len(RESULTS)
passed = sum(RESULTS)
print(f"\n{passed} of {total} passed", flush=True)
sys.exit(0 if passed == total else 1)
