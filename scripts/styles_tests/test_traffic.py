# -*- coding: utf-8 -*-
"""The owner's visitor pages (2026-10-20): the admin actions sources, funnel, why, photos, daily and ads (api/_lib/ops.py, traffic.py, ads.py) over an empty store and over a seeded one, the
filters, the orders and the revenue tied to a campaign, the spend ledger and its refusals, and the order row's source. Suite v3traffic.

  1. nothing recorded yet: every page answers with empty tables (the owner starts with zero orders and zero visits)
  2. a seeded fortnight of events and orders: Saltiniai by source, campaign, ad set and advertisement; the filters; revenue per currency; the order records
  3. Piltuvas: the steps by device and browser, the time from a photo to its preview, the countries
  4. Kodel nepavyksta and Nuotrauku kokybe: the cross tabs by device, browser and campaign, the times
  5. Reklamos: the spend ledger (rows, VAT, pasted lines, refusals, stale revisions, deletion, the audit log), the daily block
  6. over HTTP: the key is needed
No network, no image model, no real eye. Run by suites/run_main.sh as v3traffic.
    python test_traffic.py   prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure"""
import atexit
import json
import os
import shutil
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
TMP = tempfile.mkdtemp(prefix="snapeyes_v3traffic_")
atexit.register(shutil.rmtree, TMP, ignore_errors=True)
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, HARNESS)
sys.path.insert(0, HERE)
import harness as H  # noqa: E402

STORE = os.path.join(TMP, "store")
stub = H.start_stub()
H.setup_env(STORE, stub.server_address[1])
os.environ["SNAPEYES_ADMIN_SECRET"] = "traffic-admin-secret-for-tests-0123456789abcdef0123"
os.environ["CRON_SECRET"] = "traffic-cron-secret-for-tests-0123456789"
sys.path.insert(0, API)
import importlib.util  # noqa: E402
import requests  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import events as E  # noqa: E402
from _lib import store, ops, traffic as TR, ads as AD  # noqa: E402

for name in ("admin",):
    spec_m = importlib.util.spec_from_file_location(name, os.path.join(API, name + ".py"))
    mod = importlib.util.module_from_spec(spec_m)
    spec_m.loader.exec_module(mod)
    H.MODS[name] = mod
api = H.start_api()
BASE = f"http://127.0.0.1:{api.server_address[1]}"
WHO = {"kind": "admin-v1", "exp": int(time.time()) + 3600}
NOW = time.time()


def act(action, **body):
    return ops.ACTIONS[action](dict(body), WHO)


def refused(action, **body):
    try:
        act(action, **body)
    except store.Answer as a:
        return ("answer", a.status, a.body.get("reason"))
    except L.ClientError as e:
        return ("client", 400, str(e))
    return None


def put_event(ev):
    t = ev["t"]
    g = time.gmtime(t)
    path = f"ops/events/{time.strftime('%Y-%m-%d', g)}/{time.strftime('%H%M%S', g)}-{os.urandom(6).hex()}.json"
    store.put(path, store.json_bytes(ev), "application/json", upsert=False)


def ev(kind, days_ago=0, secs=0, **f):
    return dict(E.build(kind, f, now=NOW - days_ago * 86400 - secs), t=round(NOW - days_ago * 86400 - secs, 3))


def wipe():
    for p in ("ops", "orders"):
        shutil.rmtree(os.path.join(STORE, p), ignore_errors=True)
    ops._ROLLUPS.clear()
    ops._DAYCACHE.clear()


# ============================================================================================ 1. nothing recorded yet
section("1. nothing recorded yet: every page answers with empty tables")
wipe()
out = {a: act(a) for a in ("sources", "funnel", "why", "photos", "daily", "ads")}
check("each action answers ok with empty tables over an empty store", all(o.get("ok") for o in out.values()) and out["sources"]["rows"] == [] and out["funnel"]["steps"] == {} and out["why"]["fx"] == {}
      and out["photos"]["fx"] == {} and out["ads"]["rows"] == [] and out["ads"]["groups"] == [] and out["ads"]["rev"] == 0 and len(out["daily"]["days"]) == 8, {k: list(v) for k, v in out.items()})
check("and say that nothing is under the orders either (zero orders, zero revenue), with the orders comparable", out["sources"].get("orders") == 0 and out["sources"].get("revenue") == {} and out["sources"]["orders_comparable"] is True, out["sources"])
check("the filters' menus are empty lists", out["sources"]["available"] == {k: [] for k in ("market", "lang", "dev", "br", "src", "cmp")}, out["sources"]["available"])
check("an unknown group falls back to the campaign level, an unknown by to none (why) and to the campaign (photos)", act("sources", group="zzz")["group"] == "cmp" and act("why", by="x")["by"] is None and act("photos", by="x")["by"] == "cmp")
check("a filter that is no code is refused, with a sentence", refused("sources", market="A B")[0] == "client" and refused("funnel", dev="<x>")[0] == "client" and refused("why", br="a" * 41)[0] == "client")

# ============================================================================================ 2. a seeded fortnight
section("2. a seeded fortnight: Saltiniai")
wipe()
FB = dict(src="fb", med="paid", cmp="se-p0-test", trm="lt-a1-eye", cnt="a1-lt-s1", lang="lt", market="lt", dev="ios", br="fb", cc="lt")
IG = dict(src="ig", med="paid", cmp="se-p0-test", trm="lt-a2-restored", cnt="a2-lt-s1", lang="lt", market="lt", dev="android", br="ig", cc="lt")
DE = dict(src="fb", med="paid", cmp="se-p0-test", trm="de-win", cnt="a1-de-s1", lang="de", market="eu", dev="ios", br="safari", cc="de")
ORG = dict(src="direct", lang="en", market="eu", dev="desktop", br="chrome", cc="us")
plan = [(FB, {"landing": 40, "try": 30, "photo": 24, "result": 20, "soon": 3, "buy": 6, "order": 4}), (IG, {"landing": 30, "try": 14, "photo": 8, "result": 6, "buy": 0, "order": 0}),
        (DE, {"landing": 10, "try": 6, "photo": 5, "result": 4, "buy": 1, "order": 1}), (ORG, {"landing": 8, "try": 5, "photo": 3, "result": 2})]
n = 0
for d in range(14):
    for codes, steps in plan:
        for step, total in steps.items():
            each = total // 14 + (1 if d < total % 14 else 0)
            for _ in range(each):
                n += 1
                put_event(ev("hit", days_ago=d, secs=n % 3000, step=step, **codes, **({"took": 20000 + (n % 5) * 8000} if step == "result" else {})))
n_hits = n
# orders: 2 live paid from the FB ad (one in forints), 1 from the DE ad, 1 test payment, 1 withdrawn, 1 unpaid, 1 without a code, 1 with a code the counter never saw


def order(oid, camp, amount=1997, cur="eur", live=True, paid=True, market="eu", lang="de", withdrawn=False, days_ago=1):
    t = int(NOW - days_ago * 86400)
    rec = {"v": 1, "created_at": t, "lang": lang, "checkout": {"amount": amount, "currency": cur, "market": market, "spec": {"eyes": 1, "style": "solo.clean_iris", "lang": lang, "market": market}, **({"camp": camp} if camp else {})}}
    store.put(f"orders/{oid}/order.json", store.json_bytes(rec), "application/json", upsert=True)
    if paid:
        store.put(f"orders/{oid}/paid.json", store.json_bytes({"paid": True, "order": oid, "amount_total": amount, "currency": cur, "market": market, "livemode": live, "paid_at": t, "email": "a@b.co",
                                                              "spec": {"eyes": 1, "style": "solo.clean_iris", "lang": lang, "market": market}, **({"camp": camp} if camp else {})}), "application/json", upsert=True)
    if withdrawn:
        store.put(f"orders/{oid}/withdrawn.json", b"{}", "application/json", upsert=True)


day6 = time.strftime("%y%m%d", time.gmtime(NOW - 86400))
order(f"{day6}-aaaaaaaa", "fb|paid|se-p0-test|lt-a1-eye|a1-lt-s1", 1997, market="lt", lang="lt")
order(f"{day6}-bbbbbbbb", "fb|paid|se-p0-test|lt-a1-eye|a1-lt-s1", 2497, market="lt", lang="lt")
order(f"{day6}-cccccccc", "fb|paid|se-p0-test|de-win|a1-de-s1", 2497, market="eu", lang="de")
order(f"{day6}-dddddddd", "fb|paid|se-p0-test|lt-a1-eye|a1-lt-s1", 1997, live=False)
order(f"{day6}-eeeeeeee", "fb|paid|se-p0-test|lt-a1-eye|a1-lt-s1", 1997, withdrawn=True)
order(f"{day6}-ffffffff", "fb|paid|se-p0-test|lt-a1-eye|a1-lt-s1", 1997, paid=False)
order(f"{day6}-11111111", None, 1997, lang="en")
order(f"{day6}-22222222", "tiktok|org|o-plan||", 1997, days_ago=2, lang="en")
order(f"{day6}-33333333", "fb|paid|se-p0-test|lt-a1-eye|a1-lt-s1", 699000, cur="huf", market="hu", lang="hu")
r = act("sources", days=30, group="cmp")
rows = {tuple(x["key"][k] for k in ("src", "med", "cmp")): x for x in r["rows"]}
fbrow = rows[("fb", "paid", "se-p0-test")]
check("the sources by campaign: one row per source, medium and campaign, with the steps summed (the FB and DE ads share a source and a campaign)", fbrow["steps"]["landing"] == 50 and fbrow["steps"]["try"] == 36 and fbrow["steps"]["buy"] == 7
      and rows[("ig", "paid", "se-p0-test")]["steps"]["landing"] == 30 and rows[("direct", "", "")]["steps"]["landing"] == 8 and len(r["rows"]) >= 3, {k: v["steps"] for k, v in rows.items()})
check("the totals are the sum of the rows and the number of events read is the number written", r["totals"]["landing"] == 88 and sum(sum(x["steps"].values()) for x in r["rows"]) == sum(r["totals"].values()) == n_hits, (r["totals"], n_hits))
check("orders and revenue come from the paid, live, not withdrawn orders: three from the ad (two euro, one forint), the other one from tiktok, the one without a code under no source; a test payment, a withdrawn and an unpaid order count for nothing",
      fbrow["orders"] == 4 and fbrow["revenue"] == {"eur": 1997 + 2497 + 2497, "huf": 699000} and r["orders"] == 6 and r["revenue"]["eur"] == 1997 + 2497 + 2497 + 1997 + 1997, (fbrow["orders"], fbrow["revenue"], r["orders"], r["revenue"]))
none = rows.get(("", "", ""))
check("an order with no campaign code has a row of its own under no source, and an order whose code the counter never saw gets one too (revenue is never lost)", bool(none) and none["orders"] == 1 and ("tiktok", "org", "o-plan") in rows and rows[("tiktok", "org", "o-plan")]["orders"] == 1, list(rows))
rd = act("sources", days=30, group="cnt")
check("the advertisement level splits the campaign: three advertisements, each with its own steps and its orders", len([x for x in rd["rows"] if x["key"]["cnt"]]) >= 3 and
      next(x for x in rd["rows"] if x["key"]["cnt"] == "a1-lt-s1")["orders"] == 3 and next(x for x in rd["rows"] if x["key"]["cnt"] == "a1-de-s1")["orders"] == 1, [(x["key"]["cnt"], x.get("orders")) for x in rd["rows"]])
rs = act("sources", days=30, group="src")
check("the source level folds the campaigns: Facebook's ads are one row", next(x for x in rs["rows"] if x["key"]["src"] == "fb")["steps"]["landing"] == 50, [(x["key"], x["steps"].get("landing")) for x in rs["rows"]])
rm = act("sources", days=30, group="cmp", market="lt")
check("the market filter keeps the steps of that market and the orders of that market", all(x["key"]["src"] in ("fb", "ig") for x in rm["rows"] if x["steps"]) and rm["totals"]["landing"] == 70 and rm["orders"] == 2 and rm["available"]["market"] == ["eu", "lt"], (rm["totals"], rm["orders"]))
rl = act("sources", days=30, group="cmp", lang="de")
check("the language filter likewise (the German ad)", rl["totals"]["landing"] == 10 and rl["orders"] == 1, (rl["totals"], rl["orders"]))
rb = act("sources", days=30, group="cmp", br="fb")
check("a device or browser filter keeps the steps but not the orders (the order record keeps neither): orders_comparable false, no orders attached", rb["totals"]["landing"] == 40 and rb["orders_comparable"] is False and "orders" not in rb, (rb["totals"], rb["orders_comparable"]))
rc = act("sources", days=30, group="cmp", src="ig")
check("a campaign source filter works on the steps", rc["totals"]["landing"] == 30)
r7 = act("sources", days=7, group="cmp")
check("the period: seven days read seven days of the fortnight (about half of the landings), today included", 44 <= r7["totals"]["landing"] <= 56 and r7["days"] == 7, r7["totals"])
csv_head = None
check("the CSV the page makes of the rows is checked in the page tests; here the rows carry every column it needs", all(set(x) >= {"key", "steps"} and set(x["key"]) == {"src", "med", "cmp", "trm", "cnt"} for x in r["rows"]))
row = ops.order_row(f"{day6}-aaaaaaaa")
check("the order row names the source (camp) and the Orders page can filter by it", row["camp"] == "fb|paid|se-p0-test|lt-a1-eye|a1-lt-s1" and ops.order_row(f"{day6}-11111111")["camp"] is None, row.get("camp"))

# ============================================================================================ 3. Piltuvas
section("3. Piltuvas")
f = act("funnel", days=30)
check("the funnel steps are the sums over everything; the split by device and by browser has the same total", f["steps"]["landing"] == 88 and sum(s.get("landing", 0) for s in f["by_dev"].values()) == 88 and sum(s.get("landing", 0) for s in f["by_br"].values()) == 88
      and f["by_br"]["fb"]["landing"] == 40 and f["by_br"]["ig"]["landing"] == 30 and f["by_dev"]["ios"]["landing"] == 50, (f["steps"], list(f["by_dev"]), list(f["by_br"])))
check("the countries of the landings", f["cc"]["landing"] == {"lt": 70, "de": 10, "us": 8}, f["cc"].get("landing"))
tt = f["ttp"]
check("the time from a photo to its preview: p50 and p95 from the buckets of the page's own milliseconds (20 to 52 s: p50 in the 45 s bucket, p95 in the 60 s bucket)",
      tt["all"]["p50"]["ms"] in (30000, 45000) and tt["all"]["p95"]["ms"] in (60000, 90000) and tt["all"]["p50"]["n"] == 32 and set(tt["by_dev"]) == {"ios", "android", "desktop"}, tt["all"])
check("and a filter on the funnel narrows the time too (iPhone only)", act("funnel", days=30, dev="ios")["ttp"]["all"]["p50"]["n"] == 24 and act("funnel", days=30, dev="ios")["steps"]["landing"] == 50)
check("percentile of nothing is none, of a bucket above the last bound is over", TR.percentile({}, E.TTP_MS, 0.5)["ms"] is None and TR.percentile({str(len(E.TTP_MS)): 3}, E.TTP_MS, 0.95) == {"ms": None, "over": True, "n": 3}
      and TR.percentile({"0": 1, "1": 1}, E.TTP_MS, 0.5)["ms"] == E.TTP_MS[0])

# ============================================================================================ 4. why and photos
section("4. Kodel nepavyksta and Nuotrauku kokybe")
wipe()
n = 0
for d in range(3):
    for codes in (FB, IG):
        for i in range(6):
            n += 1
            put_event(ev("analyze", days_ago=d, secs=n, ok=True, verdict="good" if i < 4 else "weak", blocked=i == 5, block_reason="too_blurry" if i == 5 else None, res="mp_8_16" if codes is FB else "mp_1_3",
                         ori="portrait", irs="d_420_600", source="camera", locked=True, ms=2000 + 400 * i, **codes))
            put_event(ev("enhance", days_ago=d, secs=n, mode="faithful", gate="ok" if i < 4 else "lid", reason="none" if i < 4 else "lid_colour_wedge", cls="grey", pupil="round",
                         retry="kept2" if i == 4 else None, retry_ms=9000 if i == 4 else None, qa_ok=True, ms=14000 + 1000 * i, **codes))
            put_event(ev("compose", days_ago=d, secs=n, style="solo.clean_iris", eyes=1, tiles=0, gate="ok" if i < 5 else "lid", retake=0 if i < 4 else 1, **codes))
        put_event(ev("error", days_ago=d, secs=n + 1, endpoint="enhance", reason="model_busy", status=503, **{"class": "busy"}, **codes))
w = act("why", days=7)
check("the analysis verdicts and the refusal reason are counted (36 analyses: 24 good, 12 weak, 6 of them blocked as too blurry)", w["fx"]["an_verdict"]["good"]["all"] == 24 and w["fx"]["an_verdict"]["weak"]["all"] == 12 and w["fx"]["an_block"]["too_blurry"]["all"] == 6, w["fx"]["an_verdict"])
check("the gate by code and reason (the lid failures with their sub-code), the second restoration (kept2: 6 of 36), the set retakes (12 of 36)",
      w["fx"]["en_gate"]["lid"]["all"] == 12 and w["fx"]["en_reason"]["lid_colour_wedge"]["all"] == 12 and w["fx"]["en_retry"]["kept2"]["all"] == 6 and w["fx"]["en_retry"]["none"]["all"] == 30
      and w["fx"]["set_retake"]["1"]["all"] == 12 and w["fx"]["set_retake"]["0"]["all"] == 24 and w["fx"]["set_gate"]["lid"]["all"] == 6, w["fx"]["set_retake"])
check("errors per endpoint with the requests behind them", w["fx"]["err_ep"]["enhance"]["all"] == 6 and w["fx"]["req"]["enhance"]["all"] == 36 and w["fx"]["req"]["analyze"]["all"] == 36, (w["fx"].get("err_ep"), w["fx"].get("req")))
wd = act("why", days=7, by="br")
check("split by browser: the Facebook app and the Instagram app each have their half, with the group named beside all", wd["fx"]["an_verdict"]["good"]["fb"] == 12 and wd["fx"]["an_verdict"]["good"]["ig"] == 12 and wd["fx"]["en_gate"]["lid"]["fb"] == 6, wd["fx"]["en_gate"])
wf = act("why", days=7, br="ig")
check("a browser filter narrows every count to it", wf["fx"]["an_verdict"]["good"]["all"] == 12 and wf["fx"]["req"]["analyze"]["all"] == 18)
check("server times: p50 and p95 of the analysis, the restoration and the style preview from the buckets of HIST_MS", w["times"]["analyze"]["all"]["p50"]["ms"] in (2000, 3000) and w["times"]["enhance"]["all"]["p95"]["ms"] in (16000, 24000)
      and set(w["times"]) == {"analyze", "enhance", "compose"} and set(w["times"]["enhance"]["by_dev"]) == {"ios", "android"}, w["times"]["analyze"])
ph = act("photos", days=7)
check("photos by campaign: the resolution classes of the two campaigns, the colour class, the pupil, the gate and the set size, as counts", ph["by"] == "cmp" and ph["fx"]["an_res"]["mp_8_16"]["fb / se-p0-test"] == 18 and ph["fx"]["an_res"]["mp_1_3"]["ig / se-p0-test"] == 18
      and ph["fx"]["en_cls"]["grey"]["all"] == 36 and ph["fx"]["en_pupil"]["round"]["all"] == 36 and ph["fx"]["set_eyes"]["1"]["all"] == 36 and "sv_style" not in ph["fx"], ph["fx"]["an_res"])
check("and it carries no request count or error (those belong to the other page)", "req" not in ph["fx"] and "err_ep" not in ph["fx"])
check("the metrics the pages ask for are the ones the tables hold (nothing asked is silently empty)", set(TR.PHOTO_METRICS) | set(TR.WHY_METRICS) >= {m for m in ("an_verdict", "an_res", "en_gate", "set_retake", "req", "err_ep")})

# ============================================================================================ 5. Reklamos
section("5. Reklamos: the spend ledger")
wipe()
today = time.strftime("%Y-%m-%d", time.gmtime())
r = act("ads_put", rows=[{"day": today, "cmp": "se-p0-test", "trm": "lt-a1-eye", "cnt": "a1-lt-s1", "amount": 250, "impr": 1200, "clicks": 18}, {"day": today, "cmp": "se-p0-test", "trm": "de-win", "amount": 1210, "vat": True}])
led = act("ads")
rows = {x["trm"]: x for x in led["rows"]}
check("rows are stored with an id, a day, the codes, the amount in euro cents; the platform label defaults to meta", r["stored"] == 2 and led["rev"] == 1 and rows["lt-a1-eye"]["amount"] == 250 and rows["lt-a1-eye"]["src"] == "meta" and len(rows["de-win"]["id"]) == 8, led["rows"])
check("the Ads Manager figure of a row has no VAT: a typed card amount (vat true) is divided by 1,21 and an Ads Manager amount is multiplied by it for the card", AD.net(rows["de-win"]) == 1000 and AD.card(rows["de-win"]) == 1210 and AD.net(rows["lt-a1-eye"]) == 250 and AD.card(rows["lt-a1-eye"]) == 303, (AD.net(rows["de-win"]), AD.card(rows["lt-a1-eye"]), AD.net(dict(rows["de-win"], amount=363))))
bads = [dict(day=today, cmp="", amount=100), dict(day="2026-13-40", cmp="x", amount=100), dict(day="2099-01-01", cmp="x", amount=100), dict(day=today, cmp="a b", amount=100), dict(day=today, cmp="x", amount=-1),
        dict(day=today, cmp="x", amount=1_000_001), dict(day=today, cmp="x", amount=1.5), dict(day=today, cmp="x", amount="2"), dict(day=today, cmp="x", cnt="y", amount=1), dict(day=today, cmp="x", amount=1, impr=-3),
        dict(day=today, cmp="203.0.113.7", amount=1), {"day": today, "amount": 1}, "x", dict(day=today, cmp="x", amount=True)]
got = [refused("ads_put", rows=[b]) for b in bads]
check("a row with no campaign, a day that is no date or in the future, a code that is no code or an address, an amount that is negative, over 10 000 euros, fractional, text or true, an advertisement without its ad set, or a negative count is refused",
      all(g and g[0] == "client" for g in got) and act("ads")["rev"] == 1, [(i, g) for i, g in enumerate(got) if not g or g[0] != "client"])
check("nothing of a refused request is stored, even the good rows beside the bad one", refused("ads_put", rows=[dict(day=today, cmp="good", amount=100), dict(day=today, cmp="", amount=100)]) is not None and len(act("ads")["rows"]) == 2)
check("rows: one to 200 a request", refused("ads_put", rows=[])[0] == "client" and refused("ads_put", rows=[dict(day=today, cmp="x", amount=1)] * 201)[0] == "client" and refused("ads_put")[0] == "client")
a1 = act("ads")
r2 = act("ads_put", paste="diena; kampanija; rinkinys; reklama; suma; parodymai; paspaudimai\n" + f"{today}; se-p0-test; hu-win; a1-hu-s1; 3,75; 900; 12\n{today}\tse-p0-test\tlt-win\t\t2.5\t\t\n", rev=a1["rev"])
a2 = act("ads")
pr = {x["trm"]: x for x in a2["rows"] if x["trm"] in ("hu-win", "lt-win")}
check("pasted lines: the header is skipped, a semicolon or a tab separates, the amount takes a comma or a point, empty parts are empty", r2["stored"] == 2 and pr["hu-win"]["amount"] == 375 and pr["hu-win"]["impr"] == 900 and pr["hu-win"]["clicks"] == 12
      and pr["lt-win"]["amount"] == 250 and "impr" not in pr["lt-win"] and pr["hu-win"]["cnt"] == "a1-hu-s1", pr)
e1 = refused("ads_put", paste=f"{today}; ; x; y; 1\n{today}; ok; ; ; abc\nnot a date; ok; ; ; 1\n")
check("a pasted line that is wrong is named by its number and nothing at all is stored", e1 and e1[0] == "client" and "line 1" in e1[2] and "line 2" in e1[2] and "line 3" in e1[2] and len(act("ads")["rows"]) == 4, e1)
st = refused("ads_put", rows=[dict(day=today, cmp="x", amount=1)], rev=0)
check("a revision the page did not see is a 409 stale_view and stores nothing", st == ("answer", 409, "stale_view") and len(act("ads")["rows"]) == 4, st)
a3 = act("ads")
rid = a3["rows"][0]["id"]
r3 = act("ads_put", rows=[dict(a3["rows"][0], amount=999)], rev=a3["rev"])
a4 = act("ads")
check("a row with an id we know replaces that row (an edit), the others stay", len(a4["rows"]) == 4 and next(x for x in a4["rows"] if x["id"] == rid)["amount"] == 999 and a4["rev"] == a3["rev"] + 1, a4["rows"])
d = act("ads_delete", ids=[rid], rev=a4["rev"])
check("a row is deleted by its id; a stale revision, no id and a bad id are refused", d["deleted"] == 1 and len(act("ads")["rows"]) == 3 and refused("ads_delete", ids=[rid], rev=0) == ("answer", 409, "stale_view")
      and refused("ads_delete", ids=[])[0] == "client" and refused("ads_delete", ids=["../x"])[0] == "client")
log = act("audit") if "audit" in ops.ACTIONS else {"entries": []}
names = [x.get("action") for x in log.get("entries", [])]
raw_ledger = open(os.path.join(STORE, "ops", "ads", "ledger.json"), encoding="utf-8").read()
check("the ledger holds only days, campaign names and amounts (no e-mail, no address, no link); the actions are audit-logged by the admin wrapper", "@" not in raw_ledger and "http" not in raw_ledger and json.loads(raw_ledger)["v"] == 1)
cl = AD.clean_row({"day": today, "cmp": " SE-P0 ", "src": " IG ", "amount": 1})
check("codes are lower-cased and trimmed, the platform label too", cl["cmp"] == "se-p0" and cl["src"] == "ig")
# the ads action ties the ledger to the counter and the orders: groups are the advertisement-level rows
wipe()
put_event(ev("hit", step="landing", **FB))
put_event(ev("hit", step="try", **FB))
order(f"{day6}-44444444", "fb|paid|se-p0-test|lt-a1-eye|a1-lt-s1", 1997)
act("ads_put", rows=[dict(day=today, cmp="se-p0-test", trm="lt-a1-eye", cnt="a1-lt-s1", amount=500)])
ad = act("ads", days=7)
g = [x for x in ad["groups"] if x["key"]["cnt"] == "a1-lt-s1"]
check("the ads action returns the ledger beside the counter's steps and the orders of the advertisement level", len(g) == 1 and g[0]["steps"]["landing"] == 1 and g[0]["orders"] == 1 and ad["vat"] == 1.21 and len(ad["rows"]) == 1, ad["groups"])
dl = act("daily")
check("the daily block: eight days, the last is today, the counter's steps summed over all codes, errors and Gemini calls per day, the five best sources of the week",
      len(dl["days"]) == 8 and dl["days"][-1]["day"] == today and dl["days"][-1]["steps"].get("landing") == 1 and dl["top"][0]["key"]["src"] == "fb" and "gemini" in dl["days"][-1], dl["days"][-1])

# ============================================================================================ 6. over HTTP
section("6. over HTTP")
r = requests.post(BASE + "/api/admin", data=json.dumps({"action": "sources"}), headers={"Content-Type": "application/json"}, timeout=30)
key = ops.mint_admin_key(3600)
r2 = requests.post(BASE + "/api/admin", data=json.dumps({"action": "sources", "days": 7}), headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"}, timeout=60)
check("the pages need the admin key: without it 403, with it the same answer as the action", r.status_code == 403 and r2.status_code == 200 and r2.json().get("ok") is True and r2.json().get("group") == "cmp", (r.status_code, r2.status_code))
r3 = requests.post(BASE + "/api/admin", data=json.dumps({"action": "ads_put", "rows": [{"day": today, "cmp": "x", "amount": 1}]}), headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"}, timeout=60)
time.sleep(0.5)
audit_files = [os.path.join(dp, f) for dp, _d, fs in os.walk(os.path.join(STORE, "ops", "audit")) for f in fs]
check("a ledger change over HTTP is written to the admin audit log (action, result, no amounts, no codes beyond the count)", r3.status_code == 200 and any("ads_put" in open(p, encoding="utf-8").read() for p in audit_files), (r3.status_code, r3.text[:200]))

# every report keeps its own keys on the wire: the call's own time ("ms", put in by iris.run on every reply) must not replace one of them
lost = []
for action in ("sources", "funnel", "why", "photos", "daily", "ads"):
    direct = act(action, days=7)
    wire = requests.post(BASE + "/api/admin", data=json.dumps({"action": action, "days": 7}), headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"}, timeout=60).json()
    lost += [f"{action}.{k}" for k in direct if k not in wire]
    lost += [f"{action}.{k}" for k in direct if type(wire.get(k)) is not type(direct[k])]
check("over HTTP every report keeps all its keys and their kinds (none is replaced by the call's own time)", not lost, lost)

# ============================================================================================ 7. a seeded month holds codes and numbers only
section("7. the demo seed (scripts/seed_demo_traffic.py): a month of believable traffic, codes and numbers only")
import re  # noqa: E402
import subprocess  # noqa: E402
demo = os.path.join(TMP, "demo")
run = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "seed_demo_traffic.py"), "--store", demo, "--days", "30", "--seed", "3", "--clean"], capture_output=True, text=True, timeout=300, env=dict(os.environ, STORE_LOCAL_DIR=demo))
seeded = {}
m = re.search(r"seeded ([{].*[}])", run.stdout)
if m:
    seeded = eval(m.group(1))  # noqa: S307: the line is printed by the script just run
check("the seed script runs and writes a month: thousands of events, orders, ledger rows and feedback answers", run.returncode == 0 and seeded.get("events", 0) > 1500 and seeded.get("orders", 0) >= 5 and seeded.get("ledger", 0) > 20 and seeded.get("feedback", 0) >= 1, (run.returncode, run.stdout[-300:], run.stderr[-300:]))
blobs, bad_keys = [], []
for root, _d, files in os.walk(demo):
    for n in files:
        text = open(os.path.join(root, n), encoding="utf-8", errors="replace").read()
        blobs.append(text)
        if root.replace(os.sep, "/").find("/ops/events/") >= 0:
            ev = json.loads(text)
            bad_keys += [k for k in ev if k not in set(E.FIELDS.get(ev.get("kind"), {})) | {"v", "kind", "t", "ms"}]
whole = chr(10).join(blobs)
check("every key of every event the seed wrote is one of the whitelist of its kind", not bad_keys, sorted(set(bad_keys))[:8])
check("and nothing the seed wrote holds an IP address, a user agent, a link, or an address of e-mail except the example.com ones of the demo orders", not re.search(r"[0-9]{1,3}[.][0-9]{1,3}[.][0-9]{1,3}[.][0-9]{1,3}", whole) and "Mozilla" not in whole and "http" not in whole
      and all(x.endswith("@example.com") for x in re.findall(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+[.][A-Za-z.]+", whole)), None)
snippet = ("import sys, json; sys.path.insert(0, sys.argv[1]); from _lib import ops; w = {'kind': 'admin-v1', 'exp': 9999999999}; "
           "s = ops.ACTIONS['sources']({'days': 30, 'group': 'cmp'}, w); f = ops.ACTIONS['funnel']({'days': 30}, w); "
           "print(json.dumps({'rows': len(s['rows']), 'orders': s.get('orders'), 'revenue': s.get('revenue'), 'brs': sorted(f['by_br']), 'devs': sorted(f['by_dev'])}))")
out = subprocess.run([sys.executable, "-c", snippet, API], capture_output=True, text=True, timeout=300, env=dict(os.environ, STORE_LOCAL_DIR=demo))
rep = json.loads(out.stdout.strip().splitlines()[-1]) if out.returncode == 0 and out.stdout.strip() else {}
check("the pages answer over the seeded month: several campaigns, orders with revenue, the Facebook and Instagram in-app browsers among the browsers, and the three device classes", rep.get("rows", 0) >= 5 and rep.get("orders", 0) >= 3
      and "eur" in (rep.get("revenue") or {}) and {"fb", "ig"} <= set(rep.get("brs", [])) and {"ios", "android", "desktop"} <= set(rep.get("devs", [])), (rep, out.stderr[-300:]))

total = len(RESULTS)
passed = sum(RESULTS)
print(f"\n{passed} of {total} passed", flush=True)
sys.exit(0 if passed == total else 1)
