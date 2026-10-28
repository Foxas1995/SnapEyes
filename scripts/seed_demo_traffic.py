# -*- coding: utf-8 -*-
"""Fills a LOCAL store folder with a month of believable DEMO traffic for the owner's visitor pages (admin v2): the counter's beacons, the events the endpoints write, a few orders, the spend ledger and
its feedback answers (the chips and a few invented texts). Nothing here is real: every number comes from a seeded random generator (--seed), the people are invented, the e-mail addresses are example.com. Used to
look at every page with real looking numbers (screenshots) and by the suites that need a month of data (suites/README.md).

    python scripts/seed_demo_traffic.py --store D:/admin_out/demo_store [--days 30] [--seed 7] [--end 2026-10-31] [--clean]
    then:  STORE_LOCAL_DIR=D:/admin_out/demo_store SNAPEYES_ADMIN_SECRET=<32+ characters> CRON_SECRET=<16+ characters> python scripts/dev_api.py

The month: organic visits all along (Instagram bio and stories, TikTok, Google, direct); the ads plan's phase 0 (campaign se-p0-test: three ad sets for three days, then LT, DE and HU for four)
and phase 1 (se-p1-lt, ten euros a day) with the spend ledger typed beside it; the Facebook and Instagram in-app browsers among the devices (the iPhone in-app browser loses more visitors than the
others, so the pages have something to show); ordering opens on the 21st day and the orders follow. It writes through api/_lib/events.py build() and store.py, so what is on disk is exactly what the
site writes: codes and numbers, no address, no user agent, no photo.
"""
import argparse
import math
import os
import random
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "api"))

P = argparse.ArgumentParser()
P.add_argument("--store", required=True, help="the folder that stands in for the private bucket")
P.add_argument("--days", type=int, default=30)
P.add_argument("--seed", type=int, default=7)
P.add_argument("--end", default=None, help="the last day, YYYY-MM-DD (default: today, UTC)")
P.add_argument("--clean", action="store_true", help="remove ops/ and orders/ of the folder first")
A = P.parse_args()
os.makedirs(A.store, exist_ok=True)
os.environ["STORE_LOCAL_DIR"] = os.path.abspath(A.store)
os.environ.pop("VERCEL", None)
from _lib import ads as AD  # noqa: E402
from _lib import events as E  # noqa: E402
from _lib import feedback as FBK  # noqa: E402
from _lib import markets as MK  # noqa: E402
from _lib import pay  # noqa: E402
from _lib import store  # noqa: E402
from _lib import styles_registry as SR  # noqa: E402
from _lib.styles import gate as GT  # noqa: E402

if A.clean:
    for p in ("ops", "orders"):
        shutil.rmtree(os.path.join(A.store, p), ignore_errors=True)
R = random.Random(A.seed)
END = time.mktime(time.strptime(A.end, "%Y-%m-%d")) + 86400 - 1 if A.end else time.time()
END = min(END, time.time() + 86400)
OPEN_DAY = 21                                   # the day index (0 = the oldest) on which ordering opens
N = A.days
written = {"events": 0, "orders": 0, "ledger": 0, "feedback": 0}


def day_start(i):
    """00:00 UTC of day i (0 oldest, N-1 the last)."""
    end_day = END - (END % 86400)
    return end_day - (N - 1 - i) * 86400


def put_event(ev):
    t = ev["t"]
    g = time.gmtime(t)
    store.put(f"ops/events/{time.strftime('%Y-%m-%d', g)}/{time.strftime('%H%M%S', g)}-{os.urandom(6).hex()}.json", store.json_bytes(ev), "application/json", upsert=False)
    written["events"] += 1


def emit(t, kind, **f):
    if t > END:
        return
    put_event(dict(E.build(kind, f, now=t), t=round(t, 3)))


def pick(table):
    x, acc = R.random() * sum(w for _v, w in table), 0.0
    for v, w in table:
        acc += w
        if x <= acc:
            return v
    return table[-1][0]


# --------------------------------------------------------------------------------------------------- who comes from where
def ad(trm, cnt, market, lang, cc, cpc, daily, days, cmp="se-p0-test"):
    return {"codes": dict(src="fb", med="paid", cmp=cmp, trm=trm, cnt=cnt), "market": market, "lang": lang, "cc": cc, "cpc": cpc, "daily": daily, "days": days, "paid": True,
            "mix": [(("ios", "fb"), 36), (("android", "fb"), 25), (("ios", "ig"), 14), (("android", "ig"), 12), (("ios", "safari"), 4), (("android", "chrome"), 6), (("desktop", "chrome"), 3)]}


CAMPS = [
    ad("lt-a1-eye", "a1-lt-s1", "lt", "lt", [("lt", 94), ("gb", 3), ("de", 3)], 0.36, 2.5, range(10, 13)),
    ad("lt-a2-restored", "a2-lt-s1", "lt", "lt", [("lt", 94), ("gb", 3), ("de", 3)], 0.33, 2.5, range(10, 13)),
    ad("lt-a3-gift", "a3-lt-s1", "lt", "lt", [("lt", 95), ("gb", 3), ("ie", 2)], 0.44, 2.5, range(10, 13)),
    ad("lt-win", "a2-lt-s1", "lt", "lt", [("lt", 95), ("gb", 3), ("ie", 2)], 0.34, 3.0, range(13, 17)),
    ad("de-win", "a2-de-s1", "eu", "de", [("de", 82), ("at", 12), ("ch", 6)], 0.92, 4.0, range(13, 17)),
    ad("hu-win", "a2-hu-s1", "hu", "hu", [("hu", 96), ("ro", 4)], 0.21, 3.0, range(13, 17)),
    ad("lt-broad-25-55", "a2-lt-s1", "lt", "lt", [("lt", 95), ("gb", 3), ("ie", 2)], 0.35, 5.0, range(17, N), "se-p1-lt"),
    ad("lt-art-25-55", "a3-lt-s1", "lt", "lt", [("lt", 95), ("gb", 3), ("ie", 2)], 0.41, 5.0, range(17, N), "se-p1-lt"),
]
ORGANIC = [
    {"codes": dict(src="ig", med="bio", cmp="o-plan", cnt="p03"), "market": "lt", "lang": "lt", "cc": [("lt", 90), ("gb", 6), ("us", 4)], "n": 5, "mix": [(("ios", "ig"), 50), (("android", "ig"), 40), (("ios", "safari"), 10)]},
    {"codes": dict(src="ig", med="story", cmp="o-plan", cnt="s02"), "market": "lt", "lang": "lt", "cc": [("lt", 92), ("gb", 5), ("us", 3)], "n": 3, "mix": [(("ios", "ig"), 55), (("android", "ig"), 45)]},
    {"codes": dict(src="tiktok"), "market": "eu", "lang": "en", "cc": [("lt", 40), ("gb", 20), ("us", 25), ("de", 15)], "n": 2, "mix": [(("android", "tt"), 50), (("ios", "tt"), 50)]},
    {"codes": dict(src="google"), "market": "eu", "lang": "en", "cc": [("de", 30), ("gb", 25), ("us", 25), ("lt", 20)], "n": 2, "mix": [(("desktop", "chrome"), 45), (("ios", "safari"), 30), (("android", "chrome"), 25)]},
    {"codes": dict(src="direct"), "market": "lt", "lang": "lt", "cc": [("lt", 80), ("gb", 10), ("de", 10)], "n": 3, "mix": [(("ios", "safari"), 35), (("android", "chrome"), 30), (("desktop", "chrome"), 25), (("desktop", "safari"), 10)]},
]
# the visit breaks off more often in the iPhone in-app browser (the story the pages are there to show) and less on a computer
P_LAND = {("ios", "fb"): 0.62, ("ios", "ig"): 0.70, ("android", "fb"): 0.79, ("android", "ig"): 0.80}
P_TRY = {("ios", "fb"): 0.40, ("ios", "ig"): 0.44}
P_PHOTO = {("ios", "fb"): 0.50, ("ios", "ig"): 0.54, ("desktop", "chrome"): 0.30, ("desktop", "safari"): 0.30}
RES = [("mp_8_16", 58), ("mp_16_40", 20), ("mp_3_8", 14), ("mp_1_3", 6), ("mp_lt1", 2)]
IRS = [("d_lt280", 14), ("d_280_420", 30), ("d_420_600", 36), ("d_600p", 20)]
LID, FILL = list(GT.WHY["lid"]), list(GT.WHY["fill"][:3])        # the reason codes of the restoration gate (api/_lib/styles/gate.py WHY): the lid rule's eight, the fill rule's first three
# the styles and the prices are read from the one place that holds them (api/_lib/styles_registry.py, markets.py through pay.price_cents): the build refuses a script that types an id or a price
SOLO = sorted((k for k, v in SR.STYLES.items() if v["group"] == "solo"), key=lambda k: SR.STYLES[k]["tile_order"])
HARD = next(k for k in SOLO if SR.STYLES[k]["gate"] == "hard")                   # the style whose gate judges a set of eyes
STYLES = [(k, max(2, 40 // (i + 1))) for i, k in enumerate(SOLO)]                # the first on the page is chosen the most
ORDERS = []
# the feedback box: the chips a visitor chooses (weights) and a few invented texts per chip, in the page's language (English where a language has none;
# Croatian has its texts although no Croatian visit is seeded yet)
FB_RESULT = [("love", 30), ("likeness", 14), ("colour", 20), ("style", 12), ("price", 16), ("other", 8)]
FB_RETAKE = [("unclear", 28), ("fine", 22), ("device", 14), ("only", 12), ("effort", 14), ("other", 10)]
FB_TEXTS = {
    "love": {"lt": ["Labai graži! Nepatikėjau, kad iš mano akies gali išeiti toks paveikslas.", "Ačiū, mano mamai tikrai patiks."], "en": ["Wow, thank you, my mum will love this."], "de": ["Wunderschön, danke!"], "hu": ["Nagyon szép lett, köszönöm."], "hr": ["Prekrasno, hvala vam!"]},
    "likeness": {"lt": ["Mano akis žalsva, o čia atrodo ruda.", "Rainelės raštas aplink vyzdį kitoks nei mano."], "en": ["The pattern around the pupil is not the same as mine."], "de": ["Die Form der Pupille stimmt nicht ganz."], "hu": ["A szivárványhártya mintája nem az enyém."], "hr": ["Uzorak oko zjenice nije isti kao moj."]},
    "colour": {"lt": ["Spalvos per šaltos, norėjau šiltesnių.", "Atrodo pilkesnė nei tikrovėje."], "en": ["Too grey, my eye is warm brown."], "de": ["Die Farben sind zu kühl."], "hu": ["A színek túl halványak."], "hr": ["Boje su previše hladne."]},
    "style": {"lt": ["Norėjau kažko ryškesnio, su auksu."], "en": ["I would like a darker background."], "de": ["Ich hätte gern etwas Dunkleres."], "hu": ["Sötétebb hátteret szerettem volna."], "hr": ["Htjela sam tamniju pozadinu."]},
    "price": {"lt": ["Per brangu dovanai, jei imti du."], "en": ["A bit more than I expected for a file."], "de": ["Teurer als erwartet."], "hu": ["Kicsit soknak találom az árat."], "hr": ["Malo skuplje nego što sam očekivala."]},
    "other": {"lt": ["Ar galima užsakyti ant drobės?"], "en": ["Does it come as a print?"], "de": ["Gibt es das auch gedruckt?"], "hu": ["Nyomtatva is kapható?"], "hr": ["Može li se dobiti i tiskano?"]},
    "unclear": {"lt": ["Nesupratau, kaip laikyti telefoną."], "en": ["I do not get what is wrong with the picture."], "de": ["Ich verstehe nicht, was falsch ist."], "hu": ["Nem értem, mi a baj a képpel."], "hr": ["Ne razumijem što ne valja sa slikom."]},
    "fine": {"lt": ["Nuotrauka man atrodo gera, kodėl atmesta?"], "en": ["The photo is sharp, I checked."], "de": ["Das Foto ist scharf."], "hu": ["A fotó éles, ellenőriztem."], "hr": ["Fotografija je oštra, provjerila sam."]},
    "device": {"lt": ["Turiu seną telefoną."], "en": ["My camera has no zoom."], "de": ["Mein Handy hat keinen Zoom."], "hu": ["Nincs zoom a telefonomon."], "hr": ["Moj mobitel nema zum."]},
    "only": {"lt": ["Tai močiutės akis, kitos nuotraukos nėra."], "en": ["It is an old photo of my dad."], "de": ["Es ist ein altes Foto meines Vaters."], "hu": ["Ez egy régi fotó az apámról."], "hr": ["To je stara fotografija mog tate."]},
    "effort": {"lt": ["Per ilgai užtrunka."], "en": ["Too many steps."], "de": ["Zu viele Schritte."], "hu": ["Túl sok lépés."], "hr": ["Previše koraka."]},
}


def lognorm(mean, sd=0.35):
    return mean * math.exp(R.gauss(0, sd) - sd * sd / 2)


def answer(t, place, chip, x, base):
    """One answer of the feedback box, written as the server writes it: an event of codes (events.build) and, when the visitor wrote something the filter keeps, the text row apart from it."""
    if t > END:
        return
    texts = FB_TEXTS.get(chip, {})
    text = None
    if R.random() < 0.4:
        text = R.choice(texts.get(base["lang"]) or texts.get("en") or [""]) or None
    dropped = None
    if R.random() < 0.1:
        text, dropped = None, R.choice(["contact", "link", "junk"])      # now and then somebody writes an address or a link: the answer counts, the text is not kept
    fields = dict(base, w=place, c=chip, eyes=1, **({"x": x} if x else {}), **({"txt": "kept"} if text else ({"txt": dropped} if dropped else {})))
    emit(t, "fb", **fields)
    if text:
        row = {"v": 1, "t": int(t), "w": place, "c": chip, "txt": text, "eyes": 1, **({"x": x} if x else {}),
               **{k: base[k] for k in ("src", "med", "cmp", "trm", "cnt", "dev", "br", "cc", "lang", "market") if base.get(k)}}
        store.put(FBK.row_path(t), store.json_bytes(row), "application/json", upsert=False)
        written["feedback"] += 1


def journey(c, t0, dev, br, ordering):
    """One visit that landed: the beacons and the events its steps write. Returns True when it ended in a paid order."""
    cd, mk, lg = c["codes"], c["market"], c["lang"]
    cc = pick(c["cc"])
    base = dict(cd, lang=lg, market=mk, dev=dev, br=br, cc=cc)
    slow = 1.7 if (dev, br) in (("ios", "fb"), ("ios", "ig")) else 1.0      # the upload and the waiting are slower in the iPhone in-app browser (one more thing for the pages to show)
    t = t0
    emit(t, "hit", step="landing", **base)
    if R.random() > P_TRY.get((dev, br), 0.55 if c.get("paid") else 0.62):
        return False
    t += lognorm(9, 0.6)
    emit(t, "hit", step="try", **base)
    if R.random() > P_PHOTO.get((dev, br), 0.62):
        return False
    t += lognorm(25, 0.5)
    t_photo = t
    emit(t, "hit", step="photo", **base)
    res, ori = pick(RES), pick([("portrait", 70), ("landscape", 25), ("square", 5)])
    usable, shots = False, R.choice([1, 2, 2, 3, 4])
    for _ in range(shots):
        an_ms = int(lognorm(2800 * slow, 0.3))
        t += an_ms / 1000
        irs = pick(IRS)
        verdict = pick([("good", 36), ("ok", 34), ("weak", 22), ("no_eye", 8)])
        blocked = verdict == "weak" and R.random() < 0.45
        reason = pick([("too_blurry", 5), ("too_small", 2), ("eyelid", 2), ("pupil_too_large", 1)]) if blocked else None
        usable = usable or (verdict in ("good", "ok") or (verdict == "weak" and not blocked))
        emit(t, "analyze", ok=verdict != "no_eye", verdict=verdict, detail=R.randint(15, 95), blocked=blocked, block_reason=reason,
             locked=verdict != "no_eye", res=res, ori=ori, irs=irs if verdict != "no_eye" else None, source=pick([("camera", 55), ("gallery", 45)]), ms=an_ms, **base)
        if blocked and R.random() < 0.2:
            answer(t + lognorm(8, 0.5), "retake", pick(FB_RETAKE), reason, base)
        t += lognorm(1.5, 0.4)                          # the visitor reads the verdict
    if not usable:
        return False
    gate = pick([("ok", 74), ("lid", 18), ("fill", 5), ("both", 3)])
    reason = None if gate == "ok" else (R.choice(LID) if gate in ("lid", "both") else R.choice(FILL))
    retried = gate != "ok" and R.random() < 0.6
    kept2 = retried and R.random() < 0.7
    enh_ms = int(lognorm((14500 + (9000 if retried else 0)) * (1.15 if slow > 1 else 1.0), 0.25))
    t += enh_ms / 1000
    emit(t, "enhance", mode="faithful", gate=gate, reason=reason or "none", cls=pick([("own", 55), ("dark_brown", 30), ("grey", 15)]), pupil=pick([("round", 92), ("slit", 6), ("bar", 2)]), qa_ok=R.random() > 0.04,
         retry=("kept2" if kept2 else "kept1") if retried else None, retry_ms=int(lognorm(9000, 0.2)) if retried else None, ms=enh_ms, **base)
    if R.random() < 0.025:
        emit(t + 1, "error", endpoint="enhance", reason="model_busy", status=503, **{"class": "busy"}, **base)
        return False
    final_ok = gate == "ok" or kept2
    t += lognorm(0.4, 0.3)
    retake = 0 if final_ok or R.random() < 0.5 else 1
    emit(t, "compose", style=HARD, eyes=1, tiles=0, gate="ok" if final_ok else gate, retake=retake, cls="own", ms=40, **base)
    if not final_ok:
        if R.random() < 0.3:
            emit(t + 2, "help", route="manual", eyes=1, why=gate, **base)
        return False
    for _ in range(3):
        emit(t + R.random() * 2, "compose", style=pick(STYLES), eyes=1, tiles=1, tile=True, gate="ok", again=True, size=480, ms=int(lognorm(900, 0.3)), **base)
    views = R.choice([1, 2, 2, 3, 4])
    t_res = t + lognorm(2.5 * slow, 0.3)                # the first preview is shown
    style = pick(STYLES)
    for k in range(views):
        style = pick(STYLES)
        emit(t_res + k * 9, "compose", style=style, eyes=1, tiles=1, gate="ok", again=True, size=1024, ms=int(lognorm(1500, 0.3)), **base)
    emit(t_res, "hit", step="result", eyes=1, took=int((t_res - t_photo) * 1000), **base)
    if R.random() < 0.09:
        answer(t_res + lognorm(40, 0.6), "result", pick(FB_RESULT), style, base)
    t = t_res + 9 * views + 15
    if not ordering:
        if R.random() < 0.6:
            emit(t, "hit", step="soon", eyes=1, style=style, **base)
        return False
    if R.random() > 0.27:
        return False
    emit(t, "hit", step="buy", eyes=1, style=style, **base)
    t += 6
    emit(t, "checkout", stage="start", style=style, eyes=1, gate="ok", **base)
    ORDERS.append((t, dict(cd), mk, lg, style, "start"))
    if R.random() > (0.55 if (dev, br) == ("ios", "fb") else 0.8):
        return False
    t += lognorm(70, 0.4)
    emit(t, "hit", step="order", eyes=1, **base)
    if R.random() < 0.96:
        emit(t - 3, "checkout", stage="paid", style=style, eyes=1, gate="ok", **{k: v for k, v in dict(cd, lang=lg, market=mk).items()})
        ORDERS[-1] = (t - 3, dict(cd), mk, lg, style, "paid")
        return True
    return False


for i in range(N):
    d0 = day_start(i)
    if d0 > END:
        break
    ordering = i >= OPEN_DAY
    weekend = time.gmtime(d0).tm_wday >= 5
    live_cut = min(1.0, max(0.0, (END - d0) / 86400))      # the last day is not over
    for c in ORGANIC:
        n = max(0, round(lognorm(c["n"] * (1.25 if weekend else 1.0), 0.45) * live_cut))
        for _ in range(n):
            dev, br = pick(c["mix"])
            t0 = d0 + 5 * 3600 + R.random() * 16 * 3600 * live_cut
            journey(c, t0, dev, br, ordering)
    for c in CAMPS:
        if i not in c["days"]:
            continue
        spend = c["daily"] * live_cut
        clicks = max(0, round(lognorm(spend / c["cpc"], 0.18)))
        for _ in range(clicks):
            dev, br = pick(c["mix"])
            t0 = d0 + 5 * 3600 + R.random() * 16 * 3600 * live_cut
            if R.random() <= P_LAND.get((dev, br), 0.86):
                journey(c, t0, dev, br, ordering)
        if live_cut >= 1.0 or i < N - 1:
            ctr = R.uniform(0.0085, 0.0145)
            AD.put([{"day": time.strftime("%Y-%m-%d", time.gmtime(d0)), "cmp": c["codes"]["cmp"], "trm": c["codes"]["trm"], "cnt": c["codes"]["cnt"], "amount": int(round(c["daily"] * 100 * R.uniform(0.96, 1.0))),
                     "impr": int(clicks / ctr), "clicks": clicks}])
            written["ledger"] += 1

# the orders the paid journeys made (and the checkouts that were left)
codes_seq = 0
for t, cd, mk, lg, style, stage in sorted(ORDERS, key=lambda x: x[0]):
    codes_seq += 1
    oid = f"{time.strftime('%y%m%d', time.gmtime(t))}-{R.getrandbits(32):08x}"
    amount, cur = pay.price_cents(1, style, mk), MK.MARKETS[mk]["currency"]
    camp = "|".join(cd.get(k, "") for k in ("src", "med", "cmp", "trm", "cnt")).rstrip("|")
    spec = {"eyes": 1, "style": style, "layout": "single", "lang": lg, "market": mk}
    rec = {"v": 1, "created_at": int(t - 120), "lang": lg, "key_sha": "0" * 16, "checkout": {"amount": amount, "currency": cur, "market": mk, "spec": spec, "camp": camp, "created_at": int(t - 100)}}
    if stage == "start" and (END - t) > 2 * 86400:
        continue                                        # an unpaid order is deleted after 26 hours: only the latest checkouts are still there
    store.put(f"orders/{oid}/order.json", store.json_bytes(rec), "application/json", upsert=True)
    if stage == "paid":
        store.put(f"orders/{oid}/paid.json", store.json_bytes({"paid": True, "order": oid, "amount_total": amount, "currency": cur, "market": mk, "livemode": True, "paid_at": int(t), "email": f"customer{codes_seq}@example.com",
                                                              "spec": spec, "camp": camp}), "application/json", upsert=True)
        store.put(f"orders/{oid}/delivery.json", store.json_bytes({"created": int(t + 400), "needs_review": False}), "application/json", upsert=True)
        store.put(f"orders/{oid}/mail_delivery.json", store.json_bytes({"state": "sent"}), "application/json", upsert=True)
    written["orders"] += 1
# one withdrawn order and one test payment, so the order pages show their states too
for k, (live, withdrawn) in enumerate(((True, True), (False, False))):
    t = END - 3 * 86400 - k * 3600
    oid = f"{time.strftime('%y%m%d', time.gmtime(t))}-{R.getrandbits(32):08x}"
    spec = {"eyes": 1, "style": HARD, "layout": "single", "lang": "lt", "market": "lt"}
    cents = pay.price_cents(1, HARD, "lt")
    store.put(f"orders/{oid}/order.json", store.json_bytes({"v": 1, "created_at": int(t - 100), "lang": "lt", "checkout": {"amount": cents, "currency": "eur", "market": "lt", "spec": spec, "camp": "ig|bio|o-plan||p03"}}), "application/json", upsert=True)
    store.put(f"orders/{oid}/paid.json", store.json_bytes({"paid": True, "order": oid, "amount_total": cents, "currency": "eur", "market": "lt", "livemode": live, "paid_at": int(t), "email": f"test{k}@example.com", "spec": spec,
                                                          "camp": "ig|bio|o-plan||p03"}), "application/json", upsert=True)
    if withdrawn:
        store.put(f"orders/{oid}/withdrawn.json", b"{}", "application/json", upsert=True)
    written["orders"] += 1

print("seeded", written)
