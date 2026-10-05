# -*- coding: utf-8 -*-
"""/api/checkout: opens the Stripe payment page for an order whose eyes are uploaded (/api/order action "draft").

GET  /api/checkout
     {ok, open, currency, prices, market, markets, max_eyes, styles, orderable_max_eyes, consent: {version, en, de, lt, hu, markets}, country, suggest}: whether
     ordering is open on this deployment (Stripe and storage configured), the price lists the server charges (currency
     and prices: the default market's, as before markets existed; markets: {key: {currency, prices}} of every market
     the site sells in, api/_lib/markets.py), and the exact withdrawal-waiver text the checkbox must show (en, de, lt,
     hu: the EU text, also the Hungarian edition's; markets: {"au": {en, de}}, the text of a market that has its own,
     pay.ACL_MARKETS, in the languages of its edition). country:
     the visitor's country as Vercel names it (x-vercel-ip-country, "" when unknown) and suggest: a sellable market
     for that country other than the default one, or null. Only a hint the page may offer; it never picks the market.
     Nothing secret, nothing per order.
     styles: the public catalogue (api/_lib/catalogue.py public_catalogue): only the styles at preview or live, each with the effective stage per eye
     count it has at those stages (the owner's override in the admin page lowers it; a held, planned or retired style is never listed); orderable_max_eyes: the
     largest eye count some style can be ordered for now (0 when nothing can). The landing page, the buy card and the picker print the number of eyes and
     the list of styles from here, never from a text; the terms of sale print neither (they are a build-time text). max_eyes stays the structural limit (8).
POST /api/checkout {order, k, eyes: 1-8, style, layout, names (a list, or the old string "Anna;Max"), date, opts {swap, rotate, look}, title, plan8,
                    lang: "en"|"de"|"lt"|"hu", market, consent_digital: true}
     market: one of the markets the site sells in ("eu" when missing; one that is not offered, or any other value:
     400). lang: the page's language when the market's edition of the legal texts has it (the Australian one: en, de),
     else "en": the order, its consent text and its emails are in that language. The server computes the price from eyes, style and market (a price or currency sent by the client is
     ignored), refuses without the withdrawal waiver, records the consent's version, time and text fingerprint,
     creates a Stripe Checkout Session (mode payment, the market's currency, one line item, the customer's email
     collected by Stripe, Stripe's own page in de or en (en-GB for Australia), payment methods chosen by Stripe, no
     Stripe Tax, no Adaptive Pricing), records market, currency and amount with the order and in the session's
     metadata, and returns its URL.
     Reply 200: {ok, url, order, amount, currency, market, eyes, style, plan8, engine {v, reg, pv}, expires_at}; redirect the browser to url.
     The PLAN (WP12, spec 2.4 and C8): the server recomputes the plan of the order from the draft's sealed eye records (api/_lib/styles/steps.py make_plan:
     the style, layout, applied options, the eyes' ids and sealed profiles, and for the collision family the pixels of the approved previews), stores it in
     order.json (checkout.plan, with engine {v, reg, pv}, the set level gate result and whether the page's plan8 was compared) and writes its plates
     version, engine version and plan8 to the Stripe metadata (pv, ev, plan8; also date, opts and the names as one JSON string). The master step reads that
     plan and never works the geometry out again. plan8 in the request is the page's copy (compose's reply says it): it is only compared, never trusted.
     Errors ({ok: false, reason, error, retry}):
       503 payments_not_configured / storage_not_configured   ordering is not open on this deployment (no Stripe,
                                a live key without the confirmation email, CRON_SECRET or complete legal texts, a
                                test key on production: pay.ordering_problem())
       403 bad_link             order and k do not match
       409 withdrawn            the customer withdrew this order (/api/order action withdraw): start a new one
       400                      bad eyes, an unknown style or layout, bad options (L.run's sentence); bad_words {why, field, chars}: a name or a date over
                                its limit or with a letter the artwork font cannot draw (names: one per eye, 24 characters, 200 in all; date: 20);
                                consent_required without the waiver
       409 style_unavailable    {style, eyes, why}: the style is known but cannot be bought for these eyes now. why: eyes (it does not take that
                                many), stage (it is not live: it opens soon, it was taken back, its look is not live), gate and reseal (a hard
                                style and an eye whose sealed gate failed or has none: retake or make the preview again; the SEALED value of the
                                draft decides, nothing is measured again), bar_pupil (the collision family draws no bar pupil), plates (a 4K plate
                                the plan will draw is not in storage: found before payment, never after), capacity (the plan's time or memory
                                need can never fit one call at the slow factor in force). Nothing was created. The admin counts the demand.
       409 plan_changed         {plan8, engine}: the plan8 the page sent is not the one the server made of the same draft: show the preview again
                                (retry true); nothing was created
       503 storage_busy         the owner's style switch (or a plate, or the draft) could not be read: never read as live
       409 already_paid         the order is paid, or an earlier checkout of it was completed and its payment is
                                still settling (settling: true); order_url says where it lives
     Before a new session is made, the order's earlier sessions are expired at Stripe (one payable session per
     order); one that turns out paid is recorded and answered 409 already_paid.
       409 eyes_missing         eyes 1..n are not all uploaded (missing: [n, ...]); upload them and ask again
       410 draft_expired        the order is older than 24 h (less than 32 min left): start a new one
       503 payments_busy        Stripe did not answer; retry
       502 payments_error       Stripe refused the request; not retryable, logged
       409 price_changed        (only when the request carried "shown") the price the page showed is not what would be
                                charged now: {amount, prices, currency, market[, exp_token]} is the current one; nothing was
                                created

Price experiments (api/_lib/abtest.py, api/_lib/experiments.py; none runs unless the owner switched it on in the admin page):
GET /api/checkout while one runs and ordering is open: without a visitor id the reply only adds "exp_markets" (the markets
     that run one: the page creates an id only for those); with the id in the header X-Snapeyes-Visitor (32 hex characters,
     made by the page, never in a URL) it holds the ladders of the visitor's variant in "markets" (and "prices" for the
     default market), "experiments": [{key, variant, markets, run}] and the signed "exp_token". Nothing running: the reply
     is exactly the old one.
POST /api/checkout {..., exp_token, shown}: the price comes from the verified token only ("shown" is checked, never used);
     no valid token for a running experiment of the order's market: the standard ladder. Errors as above.
POST /api/checkout {exp_event: "visit" | "preview", exp_token, market[, eyes, style]}: the page's once-per-visitor funnel
     beacon (no order, no Stripe): {ok, counted}."""
import os, re, sys, time, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import BaseHTTPRequestHandler
from _lib import iris as L
from _lib import store
from _lib import pay
from _lib import abtest
from _lib import catalogue


def country_hint(value):
    """(country, suggested market) from Vercel's x-vercel-ip-country: a sellable market other than the default one
    that names this country (api/_lib/markets.py countries), else None. A hint only: nothing is priced by it."""
    cc = value.strip().upper() if isinstance(value, str) and re.fullmatch(r"\s*[A-Za-z]{2}\s*", value) else ""
    for m in pay.SELECTABLE:
        if (m != pay.DEFAULT_MARKET and cc and cc in (pay.MARKETS[m].get("countries") or ())
                and pay.market_currency(m) != pay.market_currency(pay.DEFAULT_MARKET)):
            return cc, m
    return cc, None


def info(body, country=None):
    cc, suggest = country_hint(country)
    return {"ok": True, "open": pay.ordering_open() and store.configured(),
            "currency": pay.market_currency(pay.DEFAULT_MARKET).upper(), "prices": pay.price_list(pay.DEFAULT_MARKET),
            "market": pay.DEFAULT_MARKET,
            "markets": {m: {"currency": pay.market_currency(m).upper(), "prices": pay.price_list(m)} for m in pay.SELECTABLE},
            "max_eyes": pay.MAX_EYES,
            # the run-time catalogue (not strict: a page-facing answer, capped at preview when the owner's switch cannot be read, never live on a guess)
            "styles": catalogue.public_catalogue(), "orderable_max_eyes": catalogue.orderable_max_eyes(),
            "consent": dict({"version": pay.CONSENT_VERSION}, **{lang: pay.CONSENT_TEXT[lang] for lang in pay.LANGS},
                            markets={m: {lang: pay.consent_for(m, lang) for lang in pay.edition_langs(m)}
                                     for m in pay.SELECTABLE if pay.acl_market(m)}),
            "country": cc, "suggest": suggest}


def _engine(plan):
    return {"v": plan.get("engine_v"), "reg": plan.get("reg"), "pv": plan.get("pv")}


def freeze_plan(order, rec, spec, body, drafts):
    """The plan of this order, frozen for the master (WP12; spec 2.4, C8, ED12, ER3): (plan, gate, shown). Every refusal is a 409 and nothing is created
    before it. drafts: the order's draft eye records, which carry the eye id and the sealed profile of each eye (written from the seal, never from the page).

      1. the gate and the pupil of the SEALED profile decide for a hard style (catalogue.why_unavailable: gate, reseal, bar_pupil); nothing is measured
         again. An advisory style is bought on a failing eye: that is recorded (gate, "ordered after failure"), not refused;
      2. make_plan recomputes the plan from those records (the collision family from the pixels of the approved previews: a plan made without them is
         refused as reseal, because nothing would freeze what the preview showed; a bar pupil the profile did not show is bar_pupil);
      3. the page's plan8, when it sends one, must be the server's (409 plan_changed: the page shows the preview again);
      4. every 4K plate the plan will draw is in storage now (409 plates, not a hold after payment), and the plan can ever fit one call at the slow factor
         in force (409 capacity: a refusal that can never succeed is a configuration error, and is found here, not retried as busy after payment)."""
    from _lib import styles as ST
    from _lib.styles import steps as SP
    from _lib.styles import gate as GATE
    style, n = spec["style"], spec["eyes"]
    eyes = [{"eye_id": d.get("eye_id"), "profile": d.get("profile") if isinstance(d.get("profile"), dict) else None} for d in drafts]
    profiles = [e["profile"] for e in eyes]
    why = catalogue.why_unavailable(style, n, [p or {} for p in profiles])
    if why:
        raise pay.unavailable(style, n, why)
    rule = (catalogue.engine_for(style, n) or {}).get("gate_rules") or "lid"
    r = GATE.set_result(profiles, rule)
    gate = "ok" if r["ok"] is True else ("unknown" if r["ok"] is None else r["first"]["why"])
    plan_spec = {"style": style, "layout": spec["layout"], "eyes": n, "opts": spec.get("opts") or {}, "names": spec.get("names"), "date": spec.get("date")}
    ctx = SP.Ctx(order, plan_spec, rec=rec, eyes_from="draft")
    try:
        plan = SP.make_plan(plan_spec, eyes, irises=SP.plan_irises(ctx, eyes))
    except SP.Hold as h:
        raise pay.unavailable(style, n, "bar_pupil" if h.reason == "design_changed" else "stage") from None
    if plan.get("decided") is False and ST.wants_eyes({"style": style, "eyes": n}):
        raise pay.unavailable(style, n, "reseal")
    shown = body.get("plan8")
    if shown is not None and not catalogue.is_legacy(style):
        if not (isinstance(shown, str) and shown.strip().lower() == plan["plan8"]):
            raise store.Answer(409, "plan_changed", "The preview you approved is not the one we would make now. Please look at the preview again.", True,
                               None, plan8=plan["plan8"], engine=_engine(plan))
    need = plan.get("plates_needed") or []
    if need:
        have = pay.parallel([lambda x=x: store.exists(x["path"], timeout=8.0) for x in need])
        lost = [x["id"] for x, ok in zip(need, have) if not ok]
        if lost:
            raise pay.unavailable(style, n, "plates", plates=lost[:4])
    cap = SP.capacity(plan)
    if not cap["ok"]:
        raise pay.unavailable(style, n, "capacity", capacity=cap["why"])
    if len(json.dumps(plan, sort_keys=True)) > SP.RECORD_MAX:
        raise pay.unavailable(style, n, "capacity", capacity="plan_size")
    return plan, gate, shown is not None


def checkout(body):
    if "exp_event" in body:      # the price test's anonymous beacon: no order, no Stripe (api/_lib/abtest.py)
        return abtest.beacon(body)
    why = pay.ordering_problem()
    if why:
        raise pay.PayNotConfigured(why)
    order, k = body.get("order"), body.get("k")
    rec = pay.load_order(order, k)
    spec = pay.spec_from(body, markets=pay.SELECTABLE)
    if body.get("consent_digital") is not True:
        raise store.Answer(400, "consent_required", "Please tick the box about the digital file and your right of "
                           "withdrawal.", False)
    n, lang = spec["eyes"], spec["lang"]
    # a price experiment (api/_lib/abtest.py): the ladder of the variant the signed token names, when that experiment runs
    # for this market, else the standard price; the price the page says it showed is only compared with it, never used.
    # Checked before anything is closed or stored: a changed price answers 409 and touches nothing
    exp = abtest.assignment(body.get("exp_token"), spec["market"])
    amount = abtest.price_cents(exp, n, spec["style"], spec["market"]) if exp else pay.price_cents(n, spec["style"], spec["market"])
    abtest.check_shown(body, spec["market"], amount, exp)
    folder = f"orders/{order}"
    found = pay.parallel([lambda: store.exists(f"{folder}/paid.json", timeout=8.0),
                          lambda: store.exists(f"{folder}/withdrawn.json", timeout=8.0)] +
                         [lambda i=i: store.get_json(f"{folder}/draft/eye_{i}.json", timeout=8.0) for i in range(1, n + 1)])
    if found[0]:
        raise store.Answer(409, "already_paid", "This order is already paid.", False, order_url=pay.order_url(order, k, lang))
    if found[1]:
        raise store.Answer(409, "withdrawn", "This order was withdrawn. Please start a new one.", False)
    found = [found[0]] + found[2:]
    now = time.time()
    # the session ends when the draft does (24 h after the order was made), and always under Stripe's 24 h maximum
    expires = min(pay.expires_at(rec), int(now) + 86400 - 120)
    if expires - now < pay.SESSION_MIN:
        raise store.Answer(410, "draft_expired", "This unpaid order is more than 24 hours old. Please start a new one.",
                           False)
    missing = [i for i, d in enumerate(found[1:], 1) if not isinstance(d, dict)]
    if missing:
        raise store.Answer(409, "eyes_missing", "Some eyes of this artwork are not uploaded yet.", True, None,
                           missing=missing)
    # the plan of the order, frozen before anything is closed or made: a refused style leaves an earlier open session of the order as it was
    plan, gate, shown = freeze_plan(order, rec, spec, body, found[1:])
    # one payable session per order: the earlier ones are expired at Stripe first, so the old tab cannot be paid too
    paid_sess, settling = pay.close_open_sessions(order, rec)
    if paid_sess is not None:
        paid, new = pay.record_paid(order, rec, paid_sess, "checkout")
        if new:
            pay.after_paid(order, rec, paid)
        raise store.Answer(409, "already_paid", "This order is already paid.", False,
                           order_url=pay.order_url(order, k, lang))
    if settling:
        raise store.Answer(409, "already_paid", "A payment for this order is already being confirmed.", False,
                           order_url=pay.order_url(order, k, lang), settling=True)
    market = spec["market"]
    currency = pay.market_currency(market)
    # the exact text the customer ticked (the market's own for Australia) is kept with the order: the confirmation
    # email quotes it word for word
    text = pay.consent_for(market, lang)
    consent = {"version": pay.CONSENT_VERSION, "at": pay.iso(now), "lang": lang, "text": text,
               "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]}
    sess = pay.create_session(order, k, spec, amount, consent, expires, exp=exp, plan=plan)
    sid = sess["id"]
    rec = dict(rec, lang=lang, sessions=(list(rec.get("sessions") or [])[-9:] + [sid]),
               checkout={"session_id": sid, "created_at": int(now), "created": pay.iso(now), "amount": amount,
                         "currency": currency, "market": market, "spec": spec, "consent": consent,
                         "expires_at": int(expires),
                         "livemode": bool(sess.get("livemode")),
                         # the frozen plan (the master reads it, steps._stored_plan), the engine it was made under, the set level gate result at checkout
                         # and whether the page's plan8 was compared: what the admin shows beside the delivered file
                         "plan": plan, "engine": _engine(plan), "gate": gate, "plan8_shown": shown})
    if exp:
        rec["checkout"]["experiment"] = abtest.checkout_block(exp, market)
    pay.write_order(order, rec)
    pay.log(f"order {order}: checkout {sid} {amount} {currency} ({market}) {n} eye(s) {spec['style']} {lang} plan {plan['plan8']}"
            + (f" experiment {exp['key']}/{exp['variant']}" if exp else ""))
    abtest.note_checkout(exp, market, n, spec["style"], amount)
    pay.note_checkout("start", spec, rec, gate=gate)
    return {"ok": True, "url": sess["url"], "order": order, "amount": amount, "currency": currency.upper(),
            "market": market, "eyes": n, "style": spec["style"], "plan8": plan["plan8"], "engine": _engine(plan), "expires_at": int(expires)}


def handle_get(req):
    country = req.headers.get("x-vercel-ip-country") if hasattr(req, "headers") else None
    vid = abtest.vid_of(req)        # the visitor id travels in a header, never in the address (api/_lib/abtest.py)
    L.run(req, lambda body: abtest.decorate(info(body, country), vid), gate=False)


def handle_post(req):
    pay.serve(req, "checkout", checkout)


def handle(req):
    """scripts/dev_api.py calls handle() for GET and POST alike."""
    if req.command == "GET":
        handle_get(req)
    else:
        handle_post(req)


class handler(BaseHTTPRequestHandler):
    def do_GET(self): handle_get(self)
    def do_POST(self): handle_post(self)
