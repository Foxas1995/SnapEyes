# -*- coding: utf-8 -*-
"""Payments and orders for snapeyes.com: Stripe Checkout over raw HTTPS (form-encoded, API version pinned, no SDK),
the webhook signature check, the order records in the private bucket, the order access key, and the emails
(Resend). Used by /api/order, /api/checkout, /api/stripe_webhook and /api/health.

Everything here is INACTIVE until the owner sets the environment on Vercel (values are never logged or returned):
  STRIPE_SECRET_KEY      sk_test_... or sk_live_... (a restricted rk_ key allowed to write Checkout Sessions and
                         read them works too). Without it (and the next one) /api/checkout answers 503.
  STRIPE_WEBHOOK_SECRET  whsec_... of the endpoint https://snapeyes.com/api/stripe_webhook. Two may be given,
                         comma separated, while a secret is rolled.
  RESEND_API_KEY         optional, re_...: without it no email is sent (the order page still delivers).
  SNAPEYES_MAIL_FROM     optional sender, default "SnapEyes <info@snapeyes.com>" (the domain must be verified at Resend)
  SNAPEYES_OWNER_MAIL    optional address for the owner's order notes, default info@snapeyes.com
  SNAPEYES_SITE          optional, default https://snapeyes.com: the links in Stripe and in the emails
  SNAPEYES_TICKET_SECRET recommended (iris.py): the access keys are made from it. Orders made before it changes
                         keep working (their key is checked against the stored fingerprint), but the delivery email
                         and scripts/order_admin.py can only rebuild a link with the secret the order was made with.
  SNAPEYES_ALLOW_TEST_ORDERS  "1" on a Vercel PREVIEW deployment only (or a local run on the real bucket): there a
                         Stripe TEST payment unlocks the 4K files (for the owner's test purchase). Ignored on
                         production, where a test payment never unlocks anything (anyone can pay with Stripe's
                         public test card).
  SNAPEYES_DRAFT_DAY_MB  optional, default 250: how many MB of unpaid eye uploads the site accepts per day (UTC).
                         Past it, uploads pause until the next day and the owner gets one note.
  CRON_SECRET            for the daily clean-up (vercel.json crons -> GET /api/order, api/_lib/cleanup.py): Vercel
                         sends it as "Authorization: Bearer <CRON_SECRET>". Without it the clean-up answers 503, and
                         a live key takes no orders (the deletions the privacy policy promises must run).
  SNAPEYES_ADMIN_SECRET  for the owner's admin panel (/admin, api/_lib/ops.py; 32 characters or more, made with
                         python scripts/mint_admin.py --new-secret): the admin keys are signed with it. Without it
                         (and without a SNAPEYES_TICKET_SECRET of 32 or more characters) /api/admin answers 503.
Tests only, ignored whenever VERCEL is set: STRIPE_API_BASE, RESEND_API_BASE and LEGAL_PACK_BASE =
http://127.0.0.1:<port>.

The order confirmation email (confirmation_mail) carries the contract on a durable medium: the seller, what was
bought, the final price (no VAT), the customer's recorded consent with its exact text and time, the withdrawal
information with the model form and the terms of sale. The legal texts come from /legal/order-mail.json of this
site (the build writes it from the same constants the legal pages print: src/legal/plain.ts), fetched by
legal_pack(); without them the email is not sent (it is retried: "legal_unavailable").

When this deployment takes NEW orders (drafts and checkout; ordering_problem()): Stripe configured, and
  - a LIVE key only together with RESEND_API_KEY (the file may only be made after the order confirmation email,
    which confirms the withdrawal waiver, went out, see confirmation()), CRON_SECRET (the daily deletions) and
    complete legal texts (legal_problem(): /legal/order-mail.json readable, the seller's facts filled in, its
    "missing" list empty);
  - a TEST key only where test_orders_allowed(): never on production.
Without that, /api/order draft and arrange and /api/checkout answer 503 payments_not_configured and nothing is
stored, exactly as before payments existed.

One order = one private folder (store.py), orders/<order>/:
  order.json                   made with the first draft eye: created_at, key_sha, lang, and the latest checkout
  draft/eye_<n>.json           the eye as uploaded: pad, the two files below, their sizes and sha256, upload time.
                               Written last, so it only ever points at complete files.
  draft/eye_<n>_crop_<id>.<ext>     the deglared crop the preview was made from, bytes exactly as uploaded
  draft/eye_<n>_preview_<id>.<ext>  the exact /api/enhance preview the customer approved
  paid.json                    created once, never overwritten (the idempotency of every paid path): the session,
                               amount, customer email, and the spec that was paid for (from the session metadata)
  extra_payment_<id>.json      a SECOND paid Checkout Session for an order that was already paid (the owner is
                               told to refund it)
  mail_delivery.json           the order confirmation (delivery) email: claimed before sending, marked sent after.
                               Nothing is made for a paid order until it says "sent" (confirmation()).
  eye_<n>.jpg / eye_<n>.json   the 4K masters (/api/master_eye's own files)
  artwork_<digest>.jpg/.json   the artwork (/api/master_compose's own files)
  delivery.json                which artwork is this order's delivery, and whether it waits for a person
  review.json                  a person must look at this order first (a render was refused, a draft is missing,
                               the confirmation email cannot go out)
  release.json                 the owner looked and released a delivery that waited for review
  note_<kind>.json             an owner note of this kind was sent (once per kind)
  making.json                  the first time /api/order make started a render (the start of performance: the
                               right of withdrawal ends here, api/_lib/withdraw.py)
  withdrawal_<id>.json         a withdrawal statement (name, email, time, outcome; withdraw.py), with
                               withdrawal_<id>_ack.json (its receipt email), withdrawal_<id>_note.json (the owner's
                               note) and withdrawal.json (the latest one, no personal data: what the order page shows)
  withdrawal-first-<outcome>.json / withdrawal-to-<id>.json   the withdrawal function's marks: which statement
                               was the first with its outcome, and receipts that went to another address than the
                               payment email (no personal data)
  withdrawn.json               the contract is withdrawn (or a payment settling at withdrawal): nothing is made
  deleted.json / expired.json  the files are deleted (on request, after a withdrawal, or 12 months after payment)
Outside the order folders: ticketuse/<day>/<id>.json (the one order each work ticket made), draftlog/<day>/
(<bytes>-<id>.json, one per uploaded draft eye: the daily ceiling), withdrawlog/<day>/ (the withdrawal function's
slots: statements per order, statements that matched no order, receipts, owner notes; no personal data),
withdrawaddr/<yymm>/ (neutral receipts per address and month; a hash, no address), withdrawals/<yymm>/
(statements that match no order of ours), withdrawdue/ (receipts to send again), cleanup/ (what the daily clean-up
must do later, the days it finished, cleanup/digest/<day>/: the statements for the owner's daily digest, and
cleanup/review/<order>.json: a paid order held for review, index_review(), for the owner's reminder after
REVIEW_REMIND_HOURS), notes/ (owner notes not tied to an order) and marks/sold_live.json (the first live payment
was recorded here: sells()). The admin panel's log of an order, ops/orderlog/<order>/ (api/_lib/ops.py), belongs to
the order record: it is deleted with it (drop_orderlog) whenever an order goes completely, and kept with the
records of a paid order.
The daily clean-up (api/_lib/cleanup.py) removes unpaid orders after 26 h, the images of withdrawn orders after 14
days, the files of paid orders 12 months after payment (the records stay), and the markers after a few days.

Prices are computed here and nowhere else on the server (never from the client): 1 eye Studio Black 19.97 EUR,
1 eye on an art background 24.97, 2 eyes 39.97, each further eye +15.00, up to 8. Digital only."""
import os, re, json, time, hmac, html, calendar, hashlib, secrets, threading
import requests
from . import iris as L
from . import store

STRIPE_API = "https://api.stripe.com"
RESEND_API = "https://api.resend.com"
STRIPE_VERSION = "2026-08-26.dahlia"     # pinned: every request says which API it was written against
SITE_DEFAULT = "https://snapeyes.com"
CONTACT = "info@snapeyes.com"
MAIL_FROM_DEFAULT = "SnapEyes <info@snapeyes.com>"
# The seller as the emails sign. The confirmation email takes it from the legal pack (src/landing/config.ts SELLER:
# representative and phone appear there once the owner sets them); these lines are only for the short emails when
# the pack cannot be read.
SELLER = {"en": 'MB "Portretizuokis", company code 305605052, Gedimino g. 22A-14, LT-44319 Kaunas, Lithuania',
          "de": "MB „Portretizuokis“, Unternehmenscode 305605052, Gedimino g. 22A-14, LT-44319 Kaunas, Litauen"}
LEGAL_PACK_PATH = "/legal/order-mail.json"
LEGAL_CACHE = 600            # seconds a fetched legal pack is used before it is fetched again
LEGAL_STALE = 86400          # a pack this old is still used when a fresh fetch fails
MAIL_SLOW = 900              # the owner is told when a paid order's confirmation has not gone out after this long

CURRENCY = "eur"
PRICE_ONE_STUDIO = 1997      # 1 eye, Studio Black
PRICE_ONE_ART = 2497         # 1 eye, any of the five art backgrounds
PRICE_TWO = 3997             # 2 eyes
PRICE_EXTRA = 1500           # each eye after the second
MAX_EYES = L.MULTI_MAX       # 8
LANGS = ("en", "de")
STYLE_NAMES = {"studio_black": "Studio Black", "celestial_gold": "Celestial Gold", "deep_nebula": "Deep Nebula",
               "emerald_aurora": "Emerald Aurora", "obsidian_smoke": "Obsidian Smoke", "supernova": "Supernova"}

DRAFT_TTL = 24 * 3600        # an unpaid order can be paid for 24 h after its first eye was uploaded
SESSION_MIN = 1800 + 120     # Stripe: a Checkout Session lives at least 30 min; with less draft time left: expired
WEBHOOK_TOLERANCE = 300      # seconds between Stripe's signature time and now
CLAIM_STALE = 180            # a mail claim older than this without "sent" belongs to an invocation that died
DRAFT_DAY_MB = 250           # default daily ceiling of unpaid uploads (SNAPEYES_DRAFT_DAY_MB)
PURGE_HOURS = 26             # the daily clean-up deletes unpaid orders older than this (a draft lives 24 h)
MARKER_DAYS = 3              # ticketuse/ and draftlog/ day folders older than this are removed
PREVIOUS_SESSIONS = 3        # how many of an order's latest Checkout Sessions a new checkout closes first
DRAFT_ORDER_MAX = 30         # uploads one unpaid order may take per day (8 eyes, each retaken a few times)

# The withdrawal waiver (EU consumer law for digital content: the consumer expressly agrees that performance starts
# before the withdrawal period ends and acknowledges losing the right). /api/checkout refuses without it and
# records this version, the time and a fingerprint of the text in the order's language. Show exactly this text.
CONSENT_VERSION = "2026-09-29.1"
CONSENT_TEXT = {
    "en": ("I expressly agree that SnapEyes starts making my digital artwork right away, before the withdrawal period "
           "ends. I know that I lose my right of withdrawal once this has started."),
    "de": ("Ich stimme ausdrücklich zu, dass SnapEyes sofort, vor Ablauf der Widerrufsfrist, mit der Erstellung meines "
           "digitalen Kunstwerks beginnt. Mir ist bekannt, dass ich dadurch mein Widerrufsrecht verliere, sobald damit "
           "begonnen wurde."),
}
# Every consent text ever shown, by version: an order's confirmation email quotes the text its customer ticked, also
# after CONSENT_TEXT changes (add the new version here, keep the old ones).
CONSENT_TEXTS = {CONSENT_VERSION: CONSENT_TEXT}
SUBMIT_NOTE = {   # shown by Stripe above its Pay button (custom_text.submit)
    "en": ("You are buying a digital file (JPEG, 4096 px). No print and no frame are shipped. You agreed that we start "
           "right away and that your right of withdrawal ends once we have started."),
    "de": ("Sie kaufen eine digitale Datei (JPEG, 4096 px). Es wird kein Druck und kein Rahmen versendet. Sie haben "
           "zugestimmt, dass wir sofort beginnen und Ihr Widerrufsrecht damit erlischt."),
}
ITEM_DESC = {
    "en": "Digital file only: JPEG, 4096 px on the longest side. No print, no frame.",
    "de": "Nur digitale Datei: JPEG, 4096 px an der längsten Seite. Kein Druck, kein Rahmen.",
}

_SK = re.compile(r"^(sk|rk)_(test|live)_[A-Za-z0-9]{10,247}$")
_WHSEC = re.compile(r"^whsec_[A-Za-z0-9+/=]{16,200}$")
_RESEND = re.compile(r"^re_[A-Za-z0-9_]{10,200}$")
_SITE = re.compile(r"^(https://[a-z0-9.-]+(:[0-9]{1,5})?|http://(localhost|127\.0\.0\.1)(:[0-9]{1,5})?)$")
_TEST_BASE = re.compile(r"^http://(localhost|127\.0\.0\.1):[0-9]{1,5}$")
_EMAIL = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]{1,64}@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
                    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$")
_FROM = re.compile(r"^[^\x00-\x1f\x7f<>]{0,80}<[^\x00-\x1f\x7f<>\s]{3,200}>$|^[^\x00-\x1f\x7f<>\s]{3,200}$")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
KEY_RE = re.compile(r"^[a-f0-9]{32}$")
SID_RE = re.compile(r"^cs_(test|live)_[A-Za-z0-9]{8,240}$")


class PayNotConfigured(RuntimeError):
    """No usable Stripe key and webhook secret on this deployment."""


class PayBusy(RuntimeError):
    """Stripe did not answer in time or answered 429/5xx: a retry later can succeed."""


class PayError(RuntimeError):
    """Stripe refused the request (a 4xx other than 429). The message names the status and Stripe's error code."""


# ----------------------------------------------------------------------------- configuration
def _env(name):
    return store._clean(os.environ.get(name))


def stripe_key():
    v = _env("STRIPE_SECRET_KEY")
    return v if _SK.fullmatch(v) else ""


def webhook_secrets():
    return [s for s in (store._clean(x) for x in _env("STRIPE_WEBHOOK_SECRET").split(",")) if _WHSEC.fullmatch(s)]


def stripe_configured():
    """True when checkout can open: a well-formed secret key AND a webhook secret (environment only)."""
    return bool(stripe_key()) and bool(webhook_secrets())


def stripe_live():
    return stripe_key().split("_")[1:2] == ["live"]


def resend_key():
    v = _env("RESEND_API_KEY")
    return v if _RESEND.fullmatch(v) else ""


def email_configured():
    return bool(resend_key())


def site():
    """The site the Stripe return links and the emails point at: SNAPEYES_SITE, else https://snapeyes.com; on a
    Vercel Preview (the owner's test purchase) the preview deployment itself, so Stripe returns there."""
    v = _env("SNAPEYES_SITE").rstrip("/")
    if v and _SITE.fullmatch(v):
        return v
    if on_vercel() and not on_production():
        u = _env("VERCEL_URL").lower()
        if re.fullmatch(r"[a-z0-9][a-z0-9.-]{2,200}", u):
            return "https://" + u
    return SITE_DEFAULT


def mail_from():
    v = _env("SNAPEYES_MAIL_FROM")
    return v if v and _FROM.fullmatch(v) and "@" in v else MAIL_FROM_DEFAULT


def owner_mail():
    v = _env("SNAPEYES_OWNER_MAIL")
    return v if v and _EMAIL.fullmatch(v) else CONTACT


def _base(name, default):
    """A test stand-in for Stripe or Resend (a local stub), never on Vercel."""
    if os.environ.get("VERCEL"):
        return default
    v = _env(name).rstrip("/")
    return v if _TEST_BASE.fullmatch(v) else default


def problem():
    """What is missing for payments, in words that never include a value ("" when ready)."""
    why = []
    if not _env("STRIPE_SECRET_KEY"):
        why.append("STRIPE_SECRET_KEY is not set")
    elif not stripe_key():
        why.append("STRIPE_SECRET_KEY is malformed (the value is not logged)")
    if not _env("STRIPE_WEBHOOK_SECRET"):
        why.append("STRIPE_WEBHOOK_SECRET is not set")
    elif not webhook_secrets():
        why.append("STRIPE_WEBHOOK_SECRET is malformed (the value is not logged)")
    return "; ".join(why)


def on_vercel():
    return bool(os.environ.get("VERCEL")) or bool(_env("VERCEL_ENV"))


def on_production():
    """Is this the production deployment? Vercel says so in VERCEL_ENV; a Vercel run that does not say counts as
    production (the safe side). Local runs and the tests are not production."""
    env = _env("VERCEL_ENV").lower()
    if env:
        return env not in ("preview", "development")
    return bool(os.environ.get("VERCEL"))


def test_orders_allowed():
    """May a Stripe TEST-mode payment unlock the 4K files here? Never on production: anyone can pay with Stripe's
    public test card. On a Vercel Preview deployment, or any run on the real bucket, only with
    SNAPEYES_ALLOW_TEST_ORDERS=1. Local runs on a local test folder (STORE_LOCAL_DIR): yes."""
    if on_production():
        return False
    if on_vercel() or not store._local_dir():
        return _env("SNAPEYES_ALLOW_TEST_ORDERS") == "1"
    return True


def ordering_problem():
    """Why this deployment takes no NEW orders (drafts, checkout), in words that never include a value ("" when it
    does): Stripe must be configured; a test key only where test orders are allowed; a LIVE key only together with
      - the confirmation email (RESEND_API_KEY): the file may only be made after it went out;
      - CRON_SECRET (16 characters or more): without it the daily clean-up never runs the deletions the privacy
        policy promises (api/order.py cron_purge answers 503);
      - the legal texts: /legal/order-mail.json readable and complete (legal_problem()), because every order
        confirmation carries them and is not sent without them."""
    why = problem()
    if why:
        return why
    if stripe_live():
        if not email_configured():
            return ("a live STRIPE_SECRET_KEY needs RESEND_API_KEY: the order confirmation email must go out before "
                    "the file is made")
        if len(_env("CRON_SECRET")) < 16:
            return ("a live STRIPE_SECRET_KEY needs CRON_SECRET (16 characters or more): the daily clean-up must run "
                    "the deletions the privacy policy promises")
        legal = legal_problem()
        if legal:
            return "a live STRIPE_SECRET_KEY needs complete legal texts: " + legal
    elif not test_orders_allowed():
        return ("STRIPE_SECRET_KEY is a TEST key and this deployment takes no test orders (production, or a preview "
                "without SNAPEYES_ALLOW_TEST_ORDERS=1)")
    return ""


def ordering_open():
    return not ordering_problem()


SOLD_MARK = "marks/sold_live.json"      # written with the first LIVE payment recorded in this bucket (record_paid)
_SOLD = {"yes": False}                  # this instance saw SOLD_MARK: it never goes away


def sells():
    """Can a contract exist on this deployment? Yes when Stripe is configured with a live key, or a test key where
    test orders count; and, whatever the keys say now, once a LIVE payment was ever recorded in this bucket
    (ever_sold(): the owner may remove the keys to pause sales, and a real customer who then mistypes their order
    number must still have their statement recorded). False only where nothing can have been sold (snapeyes.com
    before launch): the withdrawal function then stores nothing for an order that does not exist (withdraw.py,
    409 no_order)."""
    if stripe_configured() and (stripe_live() or test_orders_allowed()):
        return True
    return ever_sold()


def ever_sold():
    """Was a LIVE payment ever recorded in this bucket (SOLD_MARK)? A storage error counts as yes: when in doubt, a
    withdrawal statement is recorded rather than refused."""
    if _SOLD["yes"]:
        return True
    try:
        seen = store.exists(SOLD_MARK, timeout=6.0)
    except store.StorageNotConfigured:
        return False
    except store.StorageError as e:
        log(f"sold mark not readable ({e}): counted as sold")
        return True
    if seen:
        _SOLD["yes"] = True
    return bool(seen)


def _mark_sold(order):
    """SOLD_MARK, once (record_paid of a live payment). Never raises."""
    if _SOLD["yes"]:
        return
    try:
        store.put(SOLD_MARK, store.json_bytes({"t": int(time.time()), "iso": iso(), "order": order}),
                  "application/json", upsert=False, timeout=6.0)
    except store.StorageExists:
        pass
    except store.StorageError as e:
        log(f"order {order}: sold mark not stored: {e}")
        return
    _SOLD["yes"] = True


def session_counts(sess):
    """Does a paid Checkout Session count as a payment here? A live one always; a test one where test orders are
    allowed."""
    return isinstance(sess, dict) and (sess.get("livemode") is True or test_orders_allowed())


def paid_counts(paid):
    """Does this paid record unlock the files here? The same rule for the stored record (paid.json)."""
    return isinstance(paid, dict) and (paid.get("livemode") is True or test_orders_allowed())


def scrub(s):
    """No key, webhook secret, order access key or signed-link token may reach a log line or a reply."""
    s = L._scrub(str(s))
    for name in ("STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "RESEND_API_KEY", "SNAPEYES_SUPABASE_SERVICE_KEY",
                 "SNAPEYES_TICKET_SECRET", "CRON_SECRET", "SNAPEYES_ADMIN_SECRET"):
        for part in _env(name).split(","):
            part = part.strip()
            if len(part) >= 8:
                s = s.replace(part, "***")
    s = re.sub(r"\b(sk|rk|pk)_(test|live)_[A-Za-z0-9]{4,}", r"\1_\2_***", s)
    s = re.sub(r"\bwhsec_[A-Za-z0-9+/=]{4,}", "whsec_***", s)
    s = re.sub(r"\bre_[A-Za-z0-9]{6,}_[A-Za-z0-9_]{4,}", "re_***", s)
    s = re.sub(r"([?&](k|token)=)[A-Za-z0-9._%-]+", r"\1***", s)
    return s


def log(msg):
    print("snapeyes pay: " + scrub(msg)[:500], flush=True)


def start_clock():
    """The invocation deadline for a handler that does not go through L.run (the webhook reads its raw body)."""
    L._LOCAL.deadline = time.time() + L.BUDGET


def parallel(fns, join_pad=1.0):
    """Run a few storage or HTTP calls at once, each under this invocation's deadline (time_left is per thread).
    Returns their results in order; the first exception is raised after all have finished."""
    d = L.deadline()
    out, errs = [None] * len(fns), [None] * len(fns)

    def one(i, f):
        L._LOCAL.deadline = d
        try:
            out[i] = f()
        except BaseException as e:  # noqa: carried to the caller
            errs[i] = e

    threads = [threading.Thread(target=one, args=(i, f), daemon=True) for i, f in enumerate(fns)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(max(1.0, L.time_left() + join_pad))
    for t, e in zip(threads, errs):
        if e is not None:
            raise e
        if t.is_alive():
            raise store.StorageError("parallel: a call did not finish in time")
    return out


def iso(ts=None):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() if ts is None else ts))


# ----------------------------------------------------------------------------- serving
def serve(req, name, fn, gate=True):
    """Run an order endpoint the way store.serve runs the paid ones (the 503 without storage first, then L.run with
    its gates, JSON parsing and error replies), with the payment errors mapped too. gate=False is for GET: no JSON
    content type to check and nothing that spends is reachable from it."""
    if gate:
        if store.refuse_unconfigured(req, name):
            return
    elif not store.configured():
        print(f"snapeyes {name} refused: storage not configured: {store.problem()}", flush=True)
        L.send_json(req, 503, {"ok": False, "reason": "storage_not_configured", "error": "Ordering is not open yet.",
                               "retry": False})
        return
    box = store._StatusReq(req)

    def wrapped(body):
        try:
            return fn(body)
        except store.StorageNotConfigured:
            a = store.Answer(503, "storage_not_configured", "Ordering is not open yet.", False)
        except store.StorageError as e:
            log(f"{name} storage error: {e}")
            a = store.busy("storage_busy", 10, "Our storage did not answer. Please try again in a moment.")
        except PayNotConfigured as e:
            log(f"{name} payments not configured: {e}")
            a = store.Answer(503, "payments_not_configured", "Ordering is not open yet.", False)
        except PayBusy as e:
            log(f"{name} payment service busy: {e}")
            a = store.busy("payments_busy", 10, "The payment service did not answer. Please try again in a moment.")
        except PayError as e:
            log(f"{name} payment service refused: {e}")
            a = store.Answer(502, "payments_error", "We could not reach the payment page. Please try again later, or "
                             "write to info@snapeyes.com.", False)
        except store.Answer as e:
            a = e
        box.status, box.retry_after = a.status, a.retry_after
        return dict(a.body)
    L.run(box, wrapped, gate=gate)


# ----------------------------------------------------------------------------- prices and the order spec
def price_cents(eyes, style):
    """The price in euro cents, from the number of eyes and the style only."""
    n = int(eyes)
    if not 1 <= n <= MAX_EYES:
        raise L.ClientError(f"An artwork holds 1 to {MAX_EYES} eyes.")
    if n == 1:
        return PRICE_ONE_STUDIO if style == "studio_black" else PRICE_ONE_ART
    return PRICE_TWO + (n - 2) * PRICE_EXTRA


def clean_text(v, n):
    return _CONTROL.sub("", v)[:n].strip() if isinstance(v, str) else ""


def lang_of(v):
    return v if isinstance(v, str) and v in LANGS else "en"


def _int(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float) and v == v and v == int(v):
        return int(v)
    if isinstance(v, str) and re.fullmatch(r"[0-9]{1,2}", v.strip()):
        return int(v.strip())
    return None


def spec_from(src):
    """The artwork an order is for: {eyes, style, layout, names, title, lang}, validated (ClientError otherwise).
    src is the checkout request, or a paid session's metadata (all strings)."""
    if not isinstance(src, dict):
        raise L.ClientError("Send a JSON object.")
    n = _int(src.get("eyes"))
    if n is None or not 1 <= n <= MAX_EYES:
        raise L.ClientError(f"Choose between 1 and {MAX_EYES} eyes.")
    style = src.get("style")
    if not isinstance(style, str) or style not in L.STYLES:
        raise L.ClientError("Choose one of the styles: " + ", ".join(L.STYLES) + ".")
    layout = src.get("layout")
    if layout in (None, ""):
        layout = L.multi_layout(n)
    elif not isinstance(layout, str) or layout not in L.layouts_for(n):
        raise L.ClientError(f"{n} eye{'s' if n > 1 else ''} can use: " + ", ".join(L.layouts_for(n)) + ".")
    return {"eyes": n, "style": style, "layout": layout, "names": clean_text(src.get("names"), 60),
            "title": clean_text(src.get("title"), 40), "lang": lang_of(src.get("lang"))}


def item_name(spec):
    n, style = spec["eyes"], STYLE_NAMES.get(spec["style"], spec["style"])
    if spec["lang"] == "de":
        return f"SnapEyes-Iris-Kunstwerk, {n} {'Auge' if n == 1 else 'Augen'}, {style}, digitale Datei 4096 px"
    return f"SnapEyes iris artwork, {n} {'eye' if n == 1 else 'eyes'}, {style}, 4096 px digital file"


def amount_text(cents, lang):
    s = f"{int(cents) // 100}.{int(cents) % 100:02d}"
    return (s.replace(".", ",") if lang == "de" else s) + " EUR"


def price_text(cents, lang):
    """A price as the site shows it: "€19.97" in English, "19,97 €" in German (the customer's emails)."""
    try:
        c = int(cents)
    except (TypeError, ValueError):
        c = 0
    s = f"{c // 100}.{c % 100:02d}"
    return f"{s.replace('.', ',')} €" if lang == "de" else f"€{s}"


# ----------------------------------------------------------------------------- orders and their access key
def order_path(order, name):
    return f"orders/{store.check_order(order)}/{name}"


def access_key(order):
    """The order's access key: an HMAC of the order id with the ticket secret (32 hex, 128 bits). The order page
    link and the emails carry it; storage keeps only its fingerprint (key_sha)."""
    store.check_order(order)
    return hmac.new(L._ticket_secret(), b"snapeyes-order-access-v1:" + order.encode("ascii"),
                    hashlib.sha256).hexdigest()[:32]


def key_sha(k):
    return hashlib.sha256(b"snapeyes-order-key-v1:" + str(k).encode("ascii", "replace")).hexdigest()[:32]


def order_url(order, k, lang="en", session=False):
    """The order page link. It always names the ORDER's language (en too), so an English order opened in a
    German-language browser stays English: the page reads ?lang= before the browser's language."""
    return f"{site()}/order?o={order}&k={k}&lang={lang_of(lang)}" + ("&s={CHECKOUT_SESSION_ID}" if session else "")


def withdraw_url(order, k, lang="en"):
    """The order page in its WITHDRAWAL mode (src/order/withdraw.ts withdrawHref): it opens the form with the
    button "Withdraw from contract here" and only reads the order's status, so opening it never starts making the
    file (the normal order page does, and with that the right of withdrawal ends). The confirmation email's
    withdrawal paragraph links here."""
    return f"{site()}/order?o={order}&k={k}&withdraw=1&lang={lang_of(lang)}"


def bad_link():
    return store.Answer(403, "bad_link", "This order link is not valid. Please open the link from your email again, "
                        "or write to info@snapeyes.com.", False)


def new_order(lang, order=None):
    """Create an order (order.json, created atomically) and return (order, k, record). order: tests and the admin
    script only; the site always lets this pick a random id."""
    for _ in range(3):
        oid = order or (time.strftime("%y%m%d", time.gmtime()) + "-" + secrets.token_hex(8))
        k = access_key(oid)
        now = int(time.time())
        rec = {"v": 1, "order": oid, "created_at": now, "created": iso(now), "key_sha": key_sha(k), "lang": lang_of(lang)}
        try:
            store.put(order_path(oid, "order.json"), store.json_bytes(rec), "application/json", upsert=False)
            return oid, k, rec
        except store.StorageExists:
            if order:
                raise
    raise store.StorageError("new order: no free id after 3 tries")


def load_order(order, k):
    """The order's record when k is its access key; otherwise a 403 that does not say whether the order exists."""
    if not isinstance(order, str) or not store.ORDER_RE.fullmatch(order) or not isinstance(k, str) or not KEY_RE.fullmatch(k):
        raise bad_link()
    rec = store.get_json(order_path(order, "order.json"), timeout=8.0)
    want = rec.get("key_sha") if isinstance(rec, dict) else None
    if not isinstance(want, str) or not hmac.compare_digest(want, key_sha(k)):
        raise bad_link()
    return rec


def expires_at(rec):
    try:
        return int(rec.get("created_at")) + DRAFT_TTL
    except (TypeError, ValueError, AttributeError):
        return 0


def draft_expired(rec, margin=0):
    return expires_at(rec) - margin <= time.time()


def write_order(order, rec):
    store.put(order_path(order, "order.json"), store.json_bytes(rec), "application/json", upsert=True)


def day(ts=None):
    return time.strftime("%y%m%d", time.gmtime(time.time() if ts is None else ts))


def ticket_path(ticket):
    """Where the one order a work ticket made is written down: ticketuse/<the day the ticket expires>/<digest>."""
    try:
        exp = int(str(ticket).split(".")[1])
    except (IndexError, ValueError):
        exp = int(time.time())
    return f"ticketuse/{day(exp)}/{hashlib.sha256(str(ticket).encode('utf-8')).hexdigest()[:32]}.json"


def order_for_ticket(ticket, lang):
    """The order a draft without order and k goes into: (order, k, record, created). One work ticket has at most
    ONE unpaid order. The first draft with it makes the order; a repeat with the same ticket (a reply lost on the
    way, a second tab) gets that same order back while it is still open. Once that order is PAID, the same photo
    may start one new order (a second artwork is a new purchase: /try then starts over with the same eyes). An
    order that can no longer take eyes otherwise (expired, its link cannot be rebuilt): PermissionError, and the
    page asks for the photo again."""
    path = ticket_path(ticket)
    prev = store.get_json(path, timeout=8.0)
    if isinstance(prev, dict) and isinstance(prev.get("order"), str) and store.ORDER_RE.fullmatch(prev["order"]) \
            and any(parallel([lambda: store.exists(order_path(prev["order"], "paid.json"), timeout=8.0),
                              lambda: store.exists(order_path(prev["order"], "withdrawn.json"), timeout=8.0)])):
        # that order is paid (or withdrawn): a new artwork from the same photo is a new order
        order, k, rec = new_order(lang)
        store.put(path, store.json_bytes({"order": order, "t": int(time.time()), "after": prev["order"]}),
                  "application/json", upsert=True, timeout=8.0)
        log(f"order {order}: a new order from the photo of paid or withdrawn order {prev['order']}")
        return order, k, rec, True
    if prev is None:
        order, k, rec = new_order(lang)
        try:
            store.put(path, store.json_bytes({"order": order, "t": int(time.time())}), "application/json",
                      upsert=False, timeout=8.0)
            return order, k, rec, True
        except store.StorageExists:
            # another request with this ticket won the race: ours goes, theirs is used
            try:
                store.delete(order_path(order, "order.json"), timeout=5.0, retry=False)
            except store.StorageError as e:
                log(f"order {order}: loser of a ticket race not removed: {e}")
            prev = store.get_json(path, timeout=8.0)
    other = prev.get("order") if isinstance(prev, dict) else None
    rec = None
    if isinstance(other, str) and store.ORDER_RE.fullmatch(other):
        rec = store.get_json(order_path(other, "order.json"), timeout=8.0)
    k = link_key(other, rec) if isinstance(rec, dict) else None
    if not k or draft_expired(rec) or store.exists(order_path(other, "paid.json"), timeout=8.0):
        raise PermissionError("order draft: this work ticket's order can take no more eyes")
    log(f"order {other}: the same work ticket again, the same order")
    return other, k, rec, False


def draft_day_limit():
    """Bytes of unpaid uploads accepted per UTC day (SNAPEYES_DRAFT_DAY_MB, default 250, 10 to 20000)."""
    v = _env("SNAPEYES_DRAFT_DAY_MB")
    mb = int(v) if re.fullmatch(r"[0-9]{1,6}", v) else DRAFT_DAY_MB
    return max(10, min(mb, 20000)) << 20


def _order_tag(order):
    return hashlib.sha256(str(order).encode("utf-8")).hexdigest()[:10]


def draft_room(nbytes, order=None):
    """Refuse an upload when today's unpaid uploads plus this one pass the daily ceiling (503 uploads_paused), so
    anonymous drafts can never fill the bucket that holds the paid files; and when this one order already had
    DRAFT_ORDER_MAX uploads today (429 too_many_uploads: retaking one eye over and over). Counted from
    draftlog/<today>/: one marker per stored upload, named <bytes>-<order tag>-<id>.json."""
    rows = [r for r in store.list_folder(f"draftlog/{day()}", limit=1000, timeout=8.0) if not r["folder"]]
    marks = [m for m in (re.match(r"^([0-9]{1,9})-([0-9a-f]{10})-", r["name"]) for r in rows) if m]
    used = sum(int(m.group(1)) for m in marks)
    if order is not None and sum(1 for m in marks if m.group(2) == _order_tag(order)) >= DRAFT_ORDER_MAX:
        log(f"order {order}: {DRAFT_ORDER_MAX} uploads today, refused")
        raise store.Answer(429, "too_many_uploads", "This order had many uploads today. Please continue tomorrow, or "
                           "write to info@snapeyes.com.", False)
    if len(rows) < 1000 and used + nbytes <= draft_day_limit():
        return
    log(f"uploads paused: {used} bytes in {len(rows)} uploads today, limit {draft_day_limit()}")
    note_once(f"notes/uploads_paused_{day()}.json", "uploads_paused",
              "SnapEyes: uploads paused for today",
              f"Today's unpaid eye uploads reached {used // (1 << 20)} MB in {len(rows)} uploads (the ceiling is "
              f"{draft_day_limit() >> 20} MB, SNAPEYES_DRAFT_DAY_MB). New uploads are refused until 00:00 UTC; paid "
              f"orders are not affected.\nIf this is real demand, raise SNAPEYES_DRAFT_DAY_MB on Vercel. If not, "
              f"someone is filling the storage: the daily clean-up removes unpaid orders after {PURGE_HOURS} h.\n")
    raise store.Answer(503, "uploads_paused", "We are not taking new uploads for the moment. Please try again later, "
                       "or write to info@snapeyes.com.", True, 3600)


def draft_logged(nbytes, order):
    """The marker draft_room() counts (best effort: a lost marker undercounts one upload)."""
    try:
        store.put(f"draftlog/{day()}/{int(nbytes)}-{_order_tag(order)}-{secrets.token_hex(6)}.json", b"{}",
                  "application/json", upsert=False, timeout=5.0, retry=False)
    except store.StorageError as e:
        log(f"draft log marker not stored: {e}")


# ----------------------------------------------------------------------------- Stripe
def _stripe(method, path, params=None, idem=None, timeout=15.0):
    """One Stripe API call inside the deadline. A GET, or a POST with an idempotency key, is tried once more after a
    connection error or a 429/5xx when the second attempt still fits. Exceptions name only the call and the type:
    an exception's text can hold the request."""
    key = stripe_key()
    if not key:
        raise PayNotConfigured("STRIPE_SECRET_KEY is not set or malformed")
    url = _base("STRIPE_API_BASE", STRIPE_API) + path
    headers = {"Authorization": "Bearer " + key, "Stripe-Version": STRIPE_VERSION}
    if idem:
        headers["Idempotency-Key"] = idem
    label = f"stripe {method} {path.split('?')[0][:80]}"
    can_retry = method == "GET" or bool(idem)
    for attempt in (1, 2):
        t = min(timeout, L.time_left() - 3.0)
        if t < 3.0:
            raise PayBusy(f"{label}: out of time")
        try:
            r = requests.request(method, url, data=params, headers=headers, timeout=t)
        except requests.RequestException as e:
            if can_retry and attempt == 1 and L.time_left() > t + 6.0:
                time.sleep(0.5)
                continue
            raise PayBusy(f"{label}: {type(e).__name__}") from None
        except Exception as e:  # noqa: not only RequestException, and never the exception's text
            raise PayError(f"{label}: {type(e).__name__}") from None
        if r.status_code in (429, 500, 502, 503, 504) and can_retry and attempt == 1 and L.time_left() > t + 6.0:
            r.close()
            time.sleep(1.0)
            continue
        return r
    raise PayBusy(f"{label}: no attempt left")


def _stripe_err(r, label):
    try:
        e = r.json().get("error") or {}
    except (ValueError, AttributeError):
        e = {}
    return scrub(f"{label}: HTTP {r.status_code} {e.get('type')} {e.get('code')} {str(e.get('message') or '')[:160]}")


def _raise_for(r, label):
    msg = _stripe_err(r, label)
    if r.status_code in (429, 500, 502, 503, 504):
        raise PayBusy(msg)
    if r.status_code in (401, 403):
        raise PayNotConfigured(msg)
    raise PayError(msg)


def create_session(order, k, spec, amount, consent, expires):
    """A Stripe Checkout Session for this order (mode payment, EUR, one line item, dynamic payment methods, no
    Stripe Tax). Returns Stripe's session object (id, url, ...)."""
    lang = spec["lang"]
    params = [
        ("mode", "payment"),
        ("success_url", order_url(order, k, lang, session=True)),
        # no k here: /try may one day carry an analytics script, and the page keeps order and k in sessionStorage.
        # lang always (en too): the customer comes back in the order's language, whatever the browser says
        ("cancel_url", f"{site()}/try?checkout=cancelled&o={order}&lang={lang}"),
        ("locale", lang),
        ("client_reference_id", order),
        ("expires_at", str(int(expires))),
        ("line_items[0][quantity]", "1"),
        ("line_items[0][price_data][currency]", CURRENCY),
        ("line_items[0][price_data][unit_amount]", str(int(amount))),
        ("line_items[0][price_data][product_data][name]", item_name(spec)),
        ("line_items[0][price_data][product_data][description]", ITEM_DESC[lang]),
        ("custom_text[submit][message]", SUBMIT_NOTE[lang]),
        ("payment_intent_data[description]", f"SnapEyes order {order}"),
        ("payment_intent_data[metadata][order]", order),
    ]
    meta = {"order": order, "key_sha": key_sha(k), "eyes": str(spec["eyes"]), "style": spec["style"],
            "layout": spec["layout"], "names": spec["names"], "title": spec["title"], "lang": lang,
            "amount": str(int(amount)), "consent_version": consent["version"], "consent_at": consent["at"]}
    for name, v in meta.items():
        if v != "":          # an empty metadata value would unset the key at Stripe
            params.append((f"metadata[{name}]", v))
    r = _stripe("POST", "/v1/checkout/sessions", params, idem=f"snapeyes-checkout-{order}-{secrets.token_hex(8)}")
    if r.status_code != 200:
        _raise_for(r, "stripe create session")
    try:
        sess = r.json()
    except ValueError:
        raise PayBusy("stripe create session: unreadable reply") from None
    sid, url = sess.get("id") if isinstance(sess, dict) else None, sess.get("url") if isinstance(sess, dict) else None
    if not (isinstance(sid, str) and SID_RE.fullmatch(sid) and isinstance(url, str) and url.startswith("https://")):
        raise PayError("stripe create session: the reply has no session id or no https url")
    return sess


def retrieve_session(sid):
    """Stripe's Checkout Session, or None when there is no such session (or the id is not one)."""
    if not isinstance(sid, str) or not SID_RE.fullmatch(sid):
        return None
    r = _stripe("GET", f"/v1/checkout/sessions/{sid}", timeout=10.0)
    if r.status_code == 404:
        return None
    if r.status_code != 200:
        _raise_for(r, "stripe retrieve session")
    try:
        sess = r.json()
    except ValueError:
        raise PayBusy("stripe retrieve session: unreadable reply") from None
    return sess if isinstance(sess, dict) else None


def expire_session(sid):
    """Close an open Checkout Session so it can no longer be paid. Returns the session as Stripe has it afterwards:
    "expired", or, when it was no longer open (the customer paid a moment ago), as it is."""
    r = _stripe("POST", f"/v1/checkout/sessions/{sid}/expire", [], idem=f"snapeyes-expire-{sid}"[:255], timeout=10.0)
    if r.status_code == 200:
        try:
            sess = r.json()
        except ValueError:
            sess = None
        if isinstance(sess, dict):
            return sess
    elif r.status_code not in (400, 404, 409):
        _raise_for(r, "stripe expire session")
    # not open any more, or an unreadable reply: ask what it is now
    return retrieve_session(sid)


def order_sessions(rec, n=PREVIOUS_SESSIONS):
    """The ids of the order's latest Checkout Sessions, newest first."""
    ids = []
    co = rec.get("checkout") if isinstance(rec, dict) else None
    earlier = list(rec.get("sessions") or []) if isinstance(rec, dict) and isinstance(rec.get("sessions"), list) else []
    for sid in [co.get("session_id") if isinstance(co, dict) else None] + earlier[::-1]:
        if isinstance(sid, str) and SID_RE.fullmatch(sid) and sid not in ids:
            ids.append(sid)
    return ids[:n]


def close_open_sessions(order, rec):
    """Before a new Checkout Session is made for an order, its earlier ones must stop being payable: otherwise the
    customer can pay the old tab AND the new one. Open sessions are expired at Stripe. Returns (paid session or
    None, settling): a session the customer has already paid, or one completed with a method that settles later."""
    ids = order_sessions(rec)
    if not ids:
        return None, False
    found = parallel([lambda s=s: retrieve_session(s) for s in ids])
    paid, settling = None, False
    for sid, sess in zip(ids, found):
        if not session_matches(sess, order, rec):
            continue
        if sess.get("status") == "open":
            sess = expire_session(sid)
            gone = isinstance(sess, dict) and sess.get("status") == "expired"
            log(f"order {order}: earlier checkout {sid} {'expired' if gone else 'was no longer open'}")
            if not session_matches(sess, order, rec):
                continue
        if session_paid(sess) and session_counts(sess):
            paid = paid or sess
        elif sess.get("status") == "complete" and session_counts(sess):
            settling = True
    return paid, settling


def session_matches(sess, order, rec):
    """Was this session made by /api/checkout for this order? The metadata carries the order id and the fingerprint
    of its access key, both written by the server."""
    if not isinstance(sess, dict) or sess.get("object") != "checkout.session" or sess.get("mode") != "payment":
        return False
    meta = sess.get("metadata") if isinstance(sess.get("metadata"), dict) else {}
    want = rec.get("key_sha") if isinstance(rec, dict) else None
    return (meta.get("order") == order and isinstance(want, str) and isinstance(meta.get("key_sha"), str)
            and hmac.compare_digest(meta["key_sha"], want) and str(sess.get("currency") or "").lower() == CURRENCY)


def session_paid(sess):
    return isinstance(sess, dict) and sess.get("payment_status") == "paid" and sess.get("status") == "complete"


# ----------------------------------------------------------------------------- the paid record
def get_paid(order, timeout=8.0):
    rec = store.get_json(order_path(order, "paid.json"), timeout=timeout)
    return rec if isinstance(rec, dict) and rec.get("paid") is True else None


def _paid_spec(sess, rec):
    """What was paid for: the session's metadata (the server wrote it and the client cannot change it); the
    order record's checkout block for that same session when the metadata is unreadable."""
    try:
        return spec_from(sess.get("metadata") or {})
    except (L.ClientError, ValueError):
        co = rec.get("checkout") if isinstance(rec, dict) else None
        if isinstance(co, dict) and co.get("session_id") == sess.get("id") and isinstance(co.get("spec"), dict):
            try:
                return spec_from(co["spec"])
            except (L.ClientError, ValueError):
                pass
    return None


def consent_text(version, lang):
    """The exact waiver text of a consent version in a language, or None for a version this code never showed."""
    t = CONSENT_TEXTS.get(version) if isinstance(version, str) else None
    return t.get(lang_of(lang)) if isinstance(t, dict) else None


def consent_record(meta, rec, sess, lang):
    """The customer's consent as paid.json keeps it: version and time from the session's metadata (written by the
    server at checkout), the language, and the exact text they ticked: the order record's copy for this very
    session, else the text of that version."""
    version, at = meta.get("consent_version"), meta.get("consent_at")
    co = rec.get("checkout") if isinstance(rec, dict) else None
    text = None
    if isinstance(co, dict) and co.get("session_id") == sess.get("id") and isinstance(co.get("consent"), dict):
        c = co["consent"]
        if c.get("version") == version and isinstance(c.get("text"), str):
            text = c["text"]
    text = text or consent_text(version, lang)
    return {"version": version if isinstance(version, str) else None, "at": at if isinstance(at, str) else None,
            "lang": lang_of(lang), "text": text,
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16] if text else None}


def paid_consent(order, rec, paid):
    """The consent a paid order's confirmation quotes ({version, at, lang, text}), or None when none is recorded
    (then the waiver cannot be confirmed, and the right of withdrawal would not end)."""
    c = paid.get("consent") if isinstance(paid, dict) else None
    if not isinstance(c, dict) or not isinstance(c.get("version"), str) or not isinstance(c.get("at"), str):
        return None
    lang = lang_of(c.get("lang") or (paid.get("spec") or {}).get("lang"))
    text = c.get("text") if isinstance(c.get("text"), str) else None
    if not text:
        co = rec.get("checkout") if isinstance(rec, dict) else None
        cc = co.get("consent") if isinstance(co, dict) and co.get("session_id") == paid.get("session_id") else None
        text = cc.get("text") if isinstance(cc, dict) and cc.get("version") == c["version"] else None
        text = text if isinstance(text, str) else consent_text(c["version"], lang)
    return dict(c, lang=lang, text=text) if text else None


def record_paid(order, rec, sess, source, event_id=None):
    """Mark the order paid, once: paid.json is created atomically and never overwritten, so a replayed webhook
    or a second order-page check finds it and changes nothing. Returns (paid record, new)."""
    spec = _paid_spec(sess, rec)
    if spec is None:
        cur = get_paid(order)
        if cur is None:
            raise PayError(f"order {order}: the paid session carries no readable order spec")
        if cur.get("session_id") != sess.get("id"):
            # the order was paid before: this is a second payment, and it must still reach the owner
            extra_payment(order, cur, {"session_id": sess.get("id"), "amount_total": sess.get("amount_total"),
                                       "currency": str(sess.get("currency") or "").lower(),
                                       "livemode": bool(sess.get("livemode")), "payment_intent": sess.get("payment_intent")
                                       if isinstance(sess.get("payment_intent"), str) else None,
                                       "email": None, "paid_iso": iso(), "source": source, "spec": None})
        return cur, False
    meta = sess.get("metadata") if isinstance(sess.get("metadata"), dict) else {}
    cd = sess.get("customer_details") if isinstance(sess.get("customer_details"), dict) else {}
    email = cd.get("email") or sess.get("customer_email") or None
    email = email if isinstance(email, str) and _EMAIL.fullmatch(email.strip()) else None
    amount = sess.get("amount_total")
    now = int(time.time())
    paid = {"paid": True, "order": order, "session_id": sess.get("id"), "payment_intent": sess.get("payment_intent")
            if isinstance(sess.get("payment_intent"), str) else None, "amount_total": amount,
            "currency": str(sess.get("currency") or "").lower(), "livemode": bool(sess.get("livemode")),
            "email": email.strip() if email else None, "paid_at": now, "paid_iso": iso(now),
            "source": source, "event_id": event_id if isinstance(event_id, str) else None, "spec": spec,
            "consent": consent_record(meta, rec, sess, spec["lang"])}
    want = price_cents(spec["eyes"], spec["style"])
    if amount != want:
        paid["amount_mismatch"] = {"expected": want}
        log(f"order {order}: paid {amount} but the spec costs {want} (recorded, delivered as paid)")
    try:
        store.put(order_path(order, "paid.json"), store.json_bytes(paid), "application/json", upsert=False)
        log(f"order {order} PAID via {source}: {amount} {paid['currency']} {spec['eyes']} eye(s) {spec['style']} "
            f"live={paid['livemode']}")
        if paid["livemode"]:
            _mark_sold(order)
        if withdrawn(order):
            # the customer withdrew while this payment was still settling (or an old tab was paid after they
            # withdrew): nothing is made, no confirmation goes out, and the owner refunds it
            log(f"order {order}: PAID after its withdrawal: refund it")
            owner_note(order, "paid_after_withdrawal",
                       f"SnapEyes: order {order} was paid after it was withdrawn, please refund {amount_text(amount or 0, 'en')}",
                       f"Order {order} was withdrawn by the customer before this payment arrived "
                       f"({amount_text(amount or 0, 'en')}, {'live' if paid['livemode'] else 'TEST mode'}, Stripe session "
                       f"{paid['session_id']}, payment {paid['payment_intent']}).\nNothing is made for the order. Please "
                       f"refund the payment in the Stripe Dashboard (Payments, search {paid['payment_intent'] or paid['session_id']}, "
                       f"Refund) within 14 days of the withdrawal.\nStatus: python scripts/order_admin.py status {order}\n")
        return paid, True
    except store.StorageExists:
        cur = get_paid(order) or paid
        if cur.get("session_id") != paid["session_id"]:
            extra_payment(order, cur, paid)
        return cur, False


def extra_payment(order, cur, extra):
    """A second paid Checkout Session for an order that is already paid: the customer was charged twice. Never
    silent: it is stored next to the order (extra_payment_<id>.json), logged with its amount, and the owner is told
    to refund it. The order itself stays as the first payment made it."""
    sid = str(extra.get("session_id") or "")
    tag = hashlib.sha256(sid.encode("utf-8")).hexdigest()[:16]
    rec = dict(extra, paid=False, extra_payment=True, first_session=cur.get("session_id"))
    try:
        store.put(order_path(order, f"extra_payment_{tag}.json"), store.json_bytes(rec), "application/json",
                  upsert=False)
    except store.StorageExists:
        return            # recorded and told before (a replayed event)
    amount = amount_text(extra.get("amount_total") or 0, "en")
    log(f"order {order}: EXTRA PAYMENT {amount} session {sid} payment {extra.get('payment_intent')} (the order was "
        f"paid by {cur.get('session_id')}): REFUND IT")
    spec = extra.get("spec") or {}
    owner_note(order, "extra_" + tag[:12], f"SnapEyes: order {order} was paid twice, please refund {amount}",
               f"Order {order} was already paid ({amount_text(cur.get('amount_total') or 0, 'en')}, Stripe session "
               f"{cur.get('session_id')}).\nA second Checkout Session of the same order was paid too:\n"
               f"  amount   {amount} ({'live' if extra.get('livemode') else 'TEST mode'})\n"
               f"  session  {sid}\n  payment  {extra.get('payment_intent')}\n  customer {extra.get('email') or 'no email'}\n"
               f"  it was for {spec.get('eyes')} eye(s), style {spec.get('style')}\n"
               f"The order is delivered as the FIRST payment made it. Please refund the second payment in the Stripe "
               f"Dashboard (Payments, search {extra.get('payment_intent') or sid}, Refund), and write to the customer if "
               f"they wanted the second version instead.\nStatus: python scripts/order_admin.py status {order}\n")


def confirm_paid(order, rec, s=None):
    """(paid record, pending). The webhook's paid.json when it is there; otherwise, when the webhook has not
    arrived yet, the Checkout Session itself (the id the success page carries, and the order's latest one) is asked
    of Stripe: payment_status paid, and the metadata names this order and its key. pending is "processing" when
    the customer completed checkout with a method that settles later. A test-mode session is not a payment where
    test orders are not allowed. PayBusy/PayError propagate."""
    paid = get_paid(order)
    if paid:
        return paid, None
    if not stripe_key():
        return None, None
    ids = []
    co = rec.get("checkout") if isinstance(rec, dict) else None
    for sid in (s, co.get("session_id") if isinstance(co, dict) else None):
        if isinstance(sid, str) and SID_RE.fullmatch(sid) and sid not in ids:
            ids.append(sid)
    pending = None
    for sid in ids:
        sess = retrieve_session(sid)
        if not session_matches(sess, order, rec):
            continue
        if not session_counts(sess):
            log(f"order {order}: session {sid} is a TEST payment and this deployment takes none, not recorded")
            continue
        if session_paid(sess):
            paid, new = record_paid(order, rec, sess, "order_page")
            if new:
                after_paid(order, rec, paid)
            return paid, None
        if sess.get("status") == "complete":
            pending = "processing"
    return None, pending


# ----------------------------------------------------------------------------- webhook signatures
def verify_signature(payload, header, secrets_list, now=None, tolerance=WEBHOOK_TOLERANCE):
    """Stripe's scheme: Stripe-Signature "t=<unix>,v1=<hex>[,v1=...]", v1 = HMAC-SHA256(secret, "<t>.<raw body>").
    Checked on the raw bytes before anything parses them, constant-time, and only when t is within tolerance of now
    (either way). True or False, never an exception."""
    try:
        if not isinstance(payload, (bytes, bytearray)) or not isinstance(header, str) or len(header) > 4096:
            return False
        t, sigs = None, []
        for item in header.split(","):
            k, _, v = item.strip().partition("=")
            if k == "t" and re.fullmatch(r"[0-9]{1,12}", v):
                t = int(v)
            elif k == "v1" and re.fullmatch(r"[0-9a-f]{64}", v):
                sigs.append(v)
        if t is None or not sigs:
            return False
        if abs((time.time() if now is None else now) - t) > tolerance:
            return False
        signed = str(t).encode("ascii") + b"." + bytes(payload)
        ok = False
        for sec in secrets_list or ():
            want = hmac.new(sec.encode("utf-8"), signed, hashlib.sha256).hexdigest()
            for got in sigs:
                ok = hmac.compare_digest(want, got) or ok
        return ok
    except Exception:  # noqa: a malformed header is a refusal, never a crash
        return False


# ----------------------------------------------------------------------------- email (Resend)
def send_mail(to, subject, text, idem, html_body=None):
    """One email through Resend: plain text, and the same content as simple HTML when html_body is given. Returns
    "sent", "off" (no key), "bad_address", "transient" (try again later) or "failed" (Resend refused: the domain,
    the key or the request)."""
    key = resend_key()
    if not key:
        return "off"
    to = to.strip() if isinstance(to, str) else ""
    if not _EMAIL.fullmatch(to):
        return "bad_address"
    t = min(10.0, L.time_left() - 2.0)
    if t < 2.0:
        return "transient"
    body = {"from": mail_from(), "to": [to], "subject": subject, "text": text, "reply_to": CONTACT}
    if html_body:
        body["html"] = html_body
    try:
        r = requests.post(_base("RESEND_API_BASE", RESEND_API) + "/emails", json=body, timeout=t,
                          headers={"Authorization": "Bearer " + key, "Idempotency-Key": idem[:256]})
    except requests.RequestException as e:
        log(f"mail {idem}: {type(e).__name__}")
        return "transient"
    except Exception as e:  # noqa
        log(f"mail {idem}: {type(e).__name__}")
        return "failed"
    if r.status_code in (200, 201, 202):
        return "sent"
    log(f"mail {idem}: HTTP {r.status_code} {r.text[:200]}")
    return "transient" if r.status_code in (429, 500, 502, 503, 504) else "failed"


def claim_once(path, stale=CLAIM_STALE):
    """Claim a one-time job (an email): True for the one caller that may do it now. A claim left "sending" by an
    invocation that died is taken over after `stale` seconds."""
    mine = {"state": "sending", "t": round(time.time(), 3), "id": secrets.token_hex(6)}
    try:
        store.put(path, store.json_bytes(mine), "application/json", upsert=False, timeout=8.0)
        return True
    except store.StorageExists:
        pass
    cur = store.get_json(path, timeout=8.0)
    if isinstance(cur, dict) and cur.get("state") in ("sent", "failed"):
        return False
    try:
        age = time.time() - float(cur.get("t")) if isinstance(cur, dict) else stale + 1
    except (TypeError, ValueError):
        age = stale + 1
    if age < stale:
        return False
    store.put(path, store.json_bytes(mine), "application/json", upsert=True, timeout=8.0)
    return True


def _mark(path, state, **extra):
    try:
        if state == "retry":
            store.delete(path, timeout=6.0)
        else:
            store.put(path, store.json_bytes(dict(extra, state=state, t=round(time.time(), 3))), "application/json",
                      upsert=True, timeout=6.0)
    except store.StorageError as e:
        log(f"claim {path} not updated: {e}")


# ----------------------------------------------------------------------------- the legal texts for the emails
_LEGAL = {"pack": None, "t": 0.0, "failed": 0.0}
_LEGAL_LOCK = threading.Lock()
LEGAL_RETRY = 60             # after a failed fetch, the pack is not fetched again for this long (the last good one or
                             # None is used): a public endpoint that asks for it cannot make every call wait


def _legal_ok(pack):
    """Is this the build's legal pack (src/legal/plain.ts LegalMailPack), with every text the email needs?"""
    try:
        s = pack["seller"]
        for lang in LANGS:
            for doc in ("withdrawal", "terms"):
                d = pack["docs"][lang][doc]
                if not (isinstance(d["text"], str) and len(d["text"]) > 400 and isinstance(d["title"], str)
                        and isinstance(d["url"], str) and d["url"].startswith("https://")):
                    return False
            if not (isinstance(s["company"][lang], str) and isinstance(s["address"][lang], str)):
                return False
        return (isinstance(s["code"], str) and isinstance(s["email"], str) and isinstance(s.get("phone", ""), str)
                and isinstance(s.get("representative", ""), str) and isinstance(pack.get("updated"), str))
    except (KeyError, TypeError):
        return False


def legal_pack(fresh=False, quick=False):
    """The legal texts of this site (/legal/order-mail.json: the withdrawal information with the model form, the
    terms of sale, the seller), or None when they cannot be read. Fetched from this deployment's own site (on a
    Preview that may sit behind Vercel's login, snapeyes.com is asked next) and kept LEGAL_CACHE seconds; a pack up
    to LEGAL_STALE old is used when a new fetch fails. quick (the ordering gate and /api/health, which public pages
    ask often): no new fetch within LEGAL_RETRY of a failed one. Tests point LEGAL_PACK_BASE at a local stub."""
    now = time.time()
    with _LEGAL_LOCK:
        pack, t, failed = _LEGAL["pack"], _LEGAL["t"], _LEGAL.get("failed", 0.0)
    if pack is not None and not fresh and now - t < LEGAL_CACHE:
        return pack
    if quick and not fresh and now - failed < LEGAL_RETRY:
        return pack if pack is not None and now - t < LEGAL_STALE else None
    test = _base("LEGAL_PACK_BASE", "")
    bases = [test] if test else list(dict.fromkeys([site(), SITE_DEFAULT]))
    for base in bases:
        tt = min(6.0, L.time_left() - 3.0)
        if tt < 1.0:
            break
        try:
            r = requests.get(base + LEGAL_PACK_PATH, timeout=tt, headers={"Accept": "application/json"})
            got = r.json() if r.status_code == 200 else None
        except Exception as e:  # noqa: any failure is "not readable now"; never the exception's text
            log(f"legal pack from {base}: {type(e).__name__}")
            continue
        if isinstance(got, dict) and _legal_ok(got):
            with _LEGAL_LOCK:
                _LEGAL["pack"], _LEGAL["t"], _LEGAL["failed"] = got, time.time(), 0.0
            return got
        log(f"legal pack from {base}: HTTP {r.status_code}, not usable")
    with _LEGAL_LOCK:
        _LEGAL["failed"] = time.time()
    if pack is not None and now - t < LEGAL_STALE:
        return pack
    return None


def legal_problem():
    """Why the legal texts do not allow LIVE sales, in words ("" when they do): /legal/order-mail.json must be
    readable (legal_pack: both languages, the withdrawal information and the terms), the seller's company, company
    code, address and email must be filled in, and the build's own list of required facts still empty ("missing",
    src/legal/plain.ts missingLegalFacts) must be empty. Facts the owner decided to leave out ("waived", today the
    phone number) do not count here: that is the owner's accepted risk, and the pages never claim them."""
    pack = legal_pack(quick=True)
    if pack is None:
        return f"{LEGAL_PACK_PATH} cannot be read or is incomplete"
    s = pack.get("seller") or {}
    empty = [f"seller.{k}" for k in ("code", "email") if not str(s.get(k) or "").strip()]
    empty += [f"seller.{k}.{lang}" for k in ("company", "address") for lang in LANGS
              if not str((s.get(k) or {}).get(lang) or "").strip()]
    if empty:
        return f"{LEGAL_PACK_PATH} has empty required facts: {', '.join(empty)}"
    missing = pack.get("missing", [])
    if not isinstance(missing, list) or not all(isinstance(x, str) for x in missing):
        return f"{LEGAL_PACK_PATH} has an unreadable \"missing\" list"
    if missing:
        return (f"{LEGAL_PACK_PATH} lists required facts that are still missing: "
                f"{', '.join(re.sub(r'[^A-Za-z0-9_.-]', '', x)[:40] for x in missing[:8])}")
    return ""


def seller_lines(lang, pack=None):
    """The seller as an email signs: company and code, address, representative and phone when set, email."""
    s = (pack or {}).get("seller") if isinstance(pack, dict) else None
    if not isinstance(s, dict):
        return SELLER[lang_of(lang)].replace(", Gedimino", "\nGedimino") + f"\n{'E-Mail' if lang == 'de' else 'Email'}: {CONTACT}"
    de = lang == "de"
    out = [f"{s['company'][lang]}, {'Unternehmenscode' if de else 'company code'} {s['code']}", s["address"][lang]]
    if s.get("representative"):
        out.append(f"{'Vertreten durch' if de else 'Represented by'}: {s['representative']}")
    if s.get("phone"):
        out.append(f"{'Telefon' if de else 'Phone'}: {s['phone']}")
    out.append(f"{'E-Mail' if de else 'Email'}: {s.get('email') or CONTACT}")
    return "\n".join(out)


# ----------------------------------------------------------------------------- email layout
_MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
           "November", "December")


def when_text(ts, lang, seconds=False):
    """A moment for a customer: "29 September 2026, 10:15 UTC" / "29.09.2026, 10:15 Uhr UTC". ts: unix seconds
    or an ISO text as the records keep it."""
    if isinstance(ts, str):
        try:
            ts = calendar.timegm(time.strptime(ts.strip()[:19], "%Y-%m-%dT%H:%M:%S"))
        except ValueError:
            return ts
    try:
        g = time.gmtime(float(ts))
    except (TypeError, ValueError, OverflowError):
        return str(ts)
    hm = f"{g.tm_hour:02d}:{g.tm_min:02d}" + (f":{g.tm_sec:02d}" if seconds else "")
    if lang == "de":
        return f"{g.tm_mday:02d}.{g.tm_mon:02d}.{g.tm_year}, {hm} Uhr UTC"
    return f"{g.tm_mday} {_MONTHS[g.tm_mon - 1]} {g.tm_year}, {hm} UTC"


def date_text(day_iso, lang):
    """A date for a customer from "YYYY-MM-DD": "29 September 2026" / "29.09.2026"."""
    try:
        g = time.strptime(str(day_iso)[:10], "%Y-%m-%d")
    except ValueError:
        return str(day_iso)
    return f"{g.tm_mday:02d}.{g.tm_mon:02d}.{g.tm_year}" if lang == "de" else f"{g.tm_mday} {_MONTHS[g.tm_mon - 1]} {g.tm_year}"


def quoted(text, lang):
    return f"„{text}“" if lang == "de" else f"“{text}”"


def render_mail(blocks, lang, title):
    """(text, html) of one email from blocks, so both parts always say the same:
      ("p", text)            a paragraph (line breaks kept)
      ("h", text)            a heading; the next block follows it directly
      ("rows", [(k, v)])     label: value lines
      ("link", url)          a link on its own line
      ("quote", text)        the customer's consent, set off
      ("rule",)              a separator before the attached legal texts
      ("doc", text)          a legal text as plain text (the build's own line breaks kept)"""
    esc = lambda s: html.escape(str(s), quote=True)
    t, h = [], []
    after_heading = False
    for b in blocks:
        kind = b[0]
        if kind == "h":
            part, hp = b[1], f'<h2 style="font-size:17px;line-height:1.3;margin:26px 0 8px">{esc(b[1])}</h2>'
        elif kind == "p":
            part, hp = b[1], f'<p style="margin:0 0 12px">{esc(b[1]).replace(chr(10), "<br>")}</p>'
        elif kind == "rows":
            part = "\n".join(f"{k}: {v}" for k, v in b[1])
            # one "label: value" line each: wraps in every mail client and at any width (no table columns)
            hp = '<div style="margin:0 0 12px">' + "".join(
                f'<p style="margin:0 0 4px"><span style="color:#555">{esc(k)}:</span> {esc(v)}</p>' for k, v in b[1]) + "</div>"
        elif kind == "link":
            part = b[1]
            hp = (f'<p style="margin:0 0 12px;word-break:break-all;overflow-wrap:anywhere"><a href="{esc(b[1])}" '
                  f'style="color:#1a4fd6">{esc(b[1])}</a></p>')
        elif kind == "quote":
            part = "    " + b[1]
            hp = (f'<blockquote style="margin:0 0 12px;padding:8px 12px;border-left:3px solid #999;background:#f6f6f6">'
                  f'{esc(b[1])}</blockquote>')
        elif kind == "rule":
            part, hp = "_" * 64, '<hr style="border:0;border-top:1px solid #ccc;margin:28px 0">'
        elif kind == "doc":
            part = b[1]
            hp = (f'<div style="white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word;font-size:13px;'
                  f'line-height:1.5;color:#333">{esc(b[1])}</div>')
        else:
            continue
        if t:
            t.append("\n" if after_heading else "\n\n")
        t.append(part)
        h.append(hp)
        after_heading = kind == "h"
    text = "".join(t) + "\n"
    doc = (f'<!doctype html><html lang="{lang_of(lang)}"><head><meta charset="utf-8">'
           f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title></head>'
           f'<body style="margin:0;padding:24px 16px;background:#ffffff;color:#1a1a1a;font-family:Arial,Helvetica,'
           f'sans-serif;font-size:15px;line-height:1.5"><div style="max-width:640px;margin:0 auto">{"".join(h)}'
           f'</div></body></html>')
    return text, doc


LAYOUT_NAMES = {   # as the order page names them (src/order/copy.ts layouts)
    "en": {"single": "Single", "duo": "Side by side", "fusion": "Fusion", "triangle": "Triangle", "row": "In a row",
           "grid": "Grid", "galaxy": "Galaxy"},
    "de": {"single": "Einzeln", "duo": "Nebeneinander", "fusion": "Fusion", "triangle": "Dreieck",
           "row": "In einer Reihe", "grid": "Raster", "galaxy": "Galaxie"},
}


# ----------------------------------------------------------------------------- the order confirmation
def confirmation_mail(order, paid, k, pack, consent):
    """The order confirmation (subject, text, html) in the order's language: the contract on a durable medium.
    Sent before anything is made (confirmation()). It holds the order page link, the seller, what was bought, the
    final price without VAT, the customer's consent with its recorded time and exact text, how to withdraw (with the
    link to the order's withdrawal form, withdraw_url(): the order page link itself starts making the file), the
    full withdrawal information with the model form and the full terms of sale (legal_pack(), the site's own
    texts)."""
    spec = paid.get("spec") or {}
    lang = lang_of(spec.get("lang"))
    de = lang == "de"
    n = int(spec.get("eyes") or 1)
    link = order_url(order, k, lang)
    wlink = withdraw_url(order, k, lang)
    price = price_text(paid.get("amount_total") or 0, lang)
    docs = pack["docs"][lang]
    wd, terms = docs["withdrawal"], docs["terms"]
    layout = LAYOUT_NAMES[lang].get(spec.get("layout") or "", "")
    rows = [("Bestellnummer" if de else "Order number", order),
            ("Vertragsschluss" if de else "Contract date", when_text(paid.get("paid_at"), lang)),
            ("Kunstwerk" if de else "Artwork", item_name(dict(spec, lang=lang, eyes=n))
             + (f", {'Anordnung' if de else 'layout'} {layout}" if n > 1 and layout else ""))]
    if spec.get("names"):
        rows.append(("Namen auf dem Kunstwerk" if de else "Names on the artwork", spec["names"]))
    if spec.get("title"):
        rows.append(("Titel auf dem Kunstwerk" if de else "Title on the artwork", spec["title"]))
    if de:
        rows += [("Lieferung", "eine digitale Datei (JPEG, 4096 px an der längsten Seite) auf Ihrer Bestellseite; es "
                               "wird kein Druck und kein Rahmen versendet"),
                 ("Preis", f"{price}. Das ist der Endpreis: Wir sind nicht umsatzsteuerlich registriert, daher wird "
                           f"keine Umsatzsteuer berechnet."),
                 ("Zahlung", "bezahlt über Stripe")]
        subject = f"Ihre SnapEyes-Bestellung {order}: Bestellbestätigung"
        blocks = [
            ("p", "Guten Tag,"),
            ("p", "vielen Dank für Ihre Bestellung. Diese E-Mail bestätigt Ihren Vertrag mit uns. Bitte bewahren Sie "
                  "sie auf: Sie enthält Ihre Bestellung, Ihre Zustimmung zum sofortigen Beginn, die Widerrufsbelehrung "
                  "mit dem Muster-Widerrufsformular und unsere AGB."),
            ("h", "Ihre Bestellseite"),
            ("link", link),
            ("p", "Sobald Sie diese Seite öffnen, beginnen wir mit der Erstellung Ihres Kunstwerks (meist ist es in "
                  "wenigen Minuten fertig), und dort laden Sie die Datei herunter. Bitte geben Sie diesen Link nicht "
                  "weiter: Jede Person, die ihn hat, kann Ihr Kunstwerk herunterladen."),
            ("h", "Ihre Bestellung"),
            ("rows", rows),
            ("h", "Ihre Zustimmung zum sofortigen Beginn"),
            ("p", f"Vor der Zahlung haben Sie am {when_text(consent['at'], lang)} bei diesem Text das Häkchen gesetzt:"),
            ("quote", quoted(consent["text"], lang)),
            ("p", "Wir bestätigen Ihre ausdrückliche Zustimmung und Ihre Kenntnisnahme. Mit der Erstellung Ihrer Datei "
                  "beginnen wir erst, nachdem diese E-Mail versandt ist. Mit diesem Beginn erlischt Ihr Widerrufsrecht."),
            ("h", "Ihr Widerrufsrecht"),
            ("p", "Bis wir begonnen haben, können Sie den Vertrag widerrufen: mit der Schaltfläche „Vertrag hier "
                  "widerrufen“ auf der Widerrufsseite Ihrer Bestellung. Dieser Link öffnet sie, ohne dass wir mit der "
                  "Erstellung Ihrer Datei beginnen (anders als der Link zu Ihrer Bestellseite oben):"),
            ("link", wlink),
            ("p", "Sie können auch per E-Mail an info@snapeyes.com oder mit dem Muster-Widerrufsformular widerrufen. "
                  "Die vollständige Widerrufsbelehrung steht unten in dieser E-Mail."),
            ("h", "Unsere AGB"),
            ("p", f"Für Ihre Bestellung gelten unsere Allgemeinen Geschäftsbedingungen in der Fassung vom "
                  f"{date_text(pack['updated'], lang)}. Der vollständige Text steht am Ende dieser E-Mail; Sie finden "
                  f"die AGB auch hier:"),
            ("link", terms["url"]),
            ("p", "Fragen? Antworten Sie einfach auf diese E-Mail."),
            ("p", "Mit freundlichen Grüßen\nSnapEyes"),
            ("p", seller_lines(lang, pack)),
        ]
    else:
        rows += [("Delivery", "a digital file (JPEG, 4096 px on the longest side) on your order page; no print and no "
                              "frame are shipped"),
                 ("Price", f"{price}. This is the final price: we are not registered for VAT, so no VAT is charged."),
                 ("Payment", "paid through Stripe")]
        subject = f"Your SnapEyes order {order}: order confirmation"
        blocks = [
            ("p", "Hello,"),
            ("p", "thank you for your order. This email confirms your contract with us. Please keep it: it holds your "
                  "order, your consent to the immediate start, the withdrawal information with the model withdrawal "
                  "form, and our terms of sale."),
            ("h", "Your order page"),
            ("link", link),
            ("p", "When you open it, we start making your artwork (it is usually ready within a few minutes), and you "
                  "download the file there. Please keep this link to yourself: anyone who has it can download your "
                  "artwork."),
            ("h", "Your order"),
            ("rows", rows),
            ("h", "Your consent to the immediate start"),
            ("p", f"Before paying, on {when_text(consent['at'], lang)}, you ticked this box:"),
            ("quote", quoted(consent["text"], lang)),
            ("p", "We confirm your express consent and your acknowledgement. We start making your file only after this "
                  "email has been sent. Once we have started, your right of withdrawal has ended."),
            ("h", "Your right of withdrawal"),
            ("p", "Until we have started, you can withdraw from the contract: with the button “Withdraw from contract "
                  "here” on the withdrawal page of your order. This link opens it without starting to make your file "
                  "(unlike the order page link above):"),
            ("link", wlink),
            ("p", "You can also withdraw by email to info@snapeyes.com or with the model withdrawal form. The full "
                  "withdrawal information is below in this email."),
            ("h", "Our terms of sale"),
            ("p", f"Our terms of sale as of {date_text(pack['updated'], lang)} apply to your order. Their full "
                  f"text is at the end of this email; you can also read them here:"),
            ("link", terms["url"]),
            ("p", "Questions? Simply reply to this email."),
            ("p", "Kind regards\nSnapEyes"),
            ("p", seller_lines(lang, pack)),
        ]
    blocks += [("rule",), ("doc", wd["text"]), ("rule",), ("doc", terms["text"])]
    text, html_body = render_mail(blocks, lang, subject)
    return subject, text, html_body


def ready_mail(order, paid, k):
    """The short "it is ready" email scripts/order_admin.py release sends after a held delivery was checked:
    (subject, text, html)."""
    lang = lang_of((paid.get("spec") or {}).get("lang"))
    link = order_url(order, k, lang)
    pack = legal_pack()
    if lang == "de":
        subject = "Ihr SnapEyes-Kunstwerk ist fertig"
        blocks = [("p", "Guten Tag,"), ("p", "Ihr Iris-Kunstwerk ist fertig und geprüft. Sie laden es auf Ihrer "
                                              "Bestellseite herunter:"),
                  ("link", link), ("p", f"Bestellung: {order}"), ("p", "Fragen? Antworten Sie einfach auf diese E-Mail."),
                  ("p", "Mit freundlichen Grüßen\nSnapEyes"), ("p", seller_lines(lang, pack))]
    else:
        subject = "Your SnapEyes artwork is ready"
        blocks = [("p", "Hello,"), ("p", "your iris artwork is ready and checked. Download it on your order page:"),
                  ("link", link), ("p", f"Order: {order}"), ("p", "Questions? Simply reply to this email."),
                  ("p", "Kind regards\nSnapEyes"), ("p", seller_lines(lang, pack))]
    text, html_body = render_mail(blocks, lang, subject)
    return subject, text, html_body


def link_key(order, rec):
    """The order's access key rebuilt from the ticket secret, or None when the secret changed since the order was
    made (then no link can be rebuilt, and the stored fingerprint says so)."""
    k = access_key(order)
    want = rec.get("key_sha") if isinstance(rec, dict) else None
    return k if isinstance(want, str) and hmac.compare_digest(want, key_sha(k)) else None


def withdrawn(order, timeout=8.0):
    """Was this order withdrawn (withdrawn.json, api/_lib/withdraw.py)? Then nothing is made and no confirmation
    goes out."""
    return store.exists(order_path(order, "withdrawn.json"), timeout=timeout)


def deliver_mail(order, rec, paid, idem_suffix=""):
    """The order confirmation email (it confirms the order and the withdrawal waiver on a durable medium), at most
    once per order. Returns "sent", "done" (sent, failed or being sent before), "off", "no_address", "no_consent"
    (no consent recorded: nothing to confirm), "withdrawn" (the customer withdrew first: none is sent),
    "legal_unavailable" (the legal texts could not be read: nothing sent, try again), "transient" (released, so a
    retried webhook or the next order-page check sends it) or "failed"."""
    if not email_configured():
        return "off"
    if not paid.get("email"):
        return "no_address"
    k = link_key(order, rec)
    if k is None:
        log(f"order {order}: confirmation email NOT sent, the ticket secret changed since the order was made")
        return "failed"
    if withdrawn(order):
        return "withdrawn"
    consent = paid_consent(order, rec, paid)
    if consent is None:
        log(f"order {order}: confirmation email NOT sent, no consent is recorded for this order")
        return "no_consent"
    pack = legal_pack()
    if pack is None:
        log(f"order {order}: confirmation email waits, the legal texts ({LEGAL_PACK_PATH}) could not be read")
        return "legal_unavailable"
    path = order_path(order, "mail_delivery.json")
    if not claim_once(path):
        return "done"
    subject, text, html_body = confirmation_mail(order, paid, k, pack, consent)
    res = send_mail(paid["email"], subject, text, f"snapeyes-delivery-{order}{idem_suffix}", html_body)
    _mark(path, "retry" if res == "transient" else ("sent" if res == "sent" else "failed"), result=res,
          legal=pack.get("updated"), consent=consent.get("version"))
    log(f"order {order}: confirmation email {res}")
    return res


MAIL_WAIT = ("transient", "done", "legal_unavailable")     # deliver_mail results that are retried, not held
MAIL_HOLD = ("failed", "bad_address", "no_address", "no_consent")   # results that hold the order for the owner


def after_paid(order, rec, paid):
    """The order page (or checkout, or the clean-up) confirmed a payment before the webhook did: the confirmation
    email and the owner's note go out now (each once; the webhook finds them claimed). Best effort here: nothing is
    made for the order until confirmation() finds the email sent, and it tries again itself."""
    try:
        deliver_mail(order, rec, paid)
    except Exception as e:  # noqa: never costs the customer their order page
        log(f"order {order}: confirmation email from the order page failed: {type(e).__name__} {e}")
    note_paid(order, paid)


# ----------------------------------------------------------------------------- the confirmation comes first
MAIL_REVIEW = "confirmation_email"     # review.json reasons of orders held because their confirmation did not go out


def confirmation_needed(paid):
    """Must the order confirmation email have gone out before anything is made? Whenever email is configured, and
    always for a live payment: under § 356 (5) no. 2 BGB (Art. 16 (m) of the directive) the right of withdrawal
    lapses only when performance began AFTER the confirmation was provided on a durable medium."""
    return email_configured() or (isinstance(paid, dict) and paid.get("livemode") is True)


def confirmation(order, rec, paid, cur=None, send=True):
    """Where the order confirmation stands before anything is made for a paid order:
      "sent"     it went out (or none is needed: a test order where email is off); making may start
      "waiting"  it is being sent, or a retry is due (Resend busy, the legal texts not readable): ask again shortly,
                 make nothing yet; after MAIL_SLOW the owner is told once
      "held"     it cannot go out (Resend refused, no or bad address, no consent recorded, email off for a live
                 payment): the order is held for review and the owner was told; nothing is made until they send it
    cur: mail_delivery.json when the caller has read it already. send: try to send it now when nobody has."""
    if not confirmation_needed(paid):
        return "sent"
    if cur is None:
        cur = store.get_json(order_path(order, "mail_delivery.json"), timeout=8.0)
    state = cur.get("state") if isinstance(cur, dict) else None
    if state == "sent":
        return "sent"
    if not email_configured():
        hold_confirmation(order, paid, "off")
        return "held"
    if state == "failed":
        hold_confirmation(order, paid, str(cur.get("result") or "failed"))
        return "held"
    if not send:
        return "waiting"
    res = deliver_mail(order, rec, paid)
    if res == "sent":
        return "sent"
    if res == "withdrawn":
        return "waiting"         # the status call shows the order as withdrawn; nothing is made
    if res in MAIL_WAIT:
        mail_slow(order, paid, res)
        return "waiting"
    hold_confirmation(order, paid, res)
    return "held"


def mail_slow(order, paid, why):
    """Tell the owner once when a paid order's confirmation has waited more than MAIL_SLOW (the customer's page
    says it is on its way, and nothing is made until it went out)."""
    try:
        age = time.time() - float(paid.get("paid_at") or time.time())
    except (TypeError, ValueError):
        age = 0
    if age < MAIL_SLOW or why == "done":
        return
    reason = ("the legal texts for the email could not be read from " + site() + LEGAL_PACK_PATH
              if why == "legal_unavailable" else "Resend did not take it (busy or unreachable)")
    owner_note(order, "mail_slow", f"SnapEyes: order {order} still waits for its confirmation email",
               f"Order {order} was paid {int(age // 60)} minutes ago, but its order confirmation email has not gone out: "
               f"{reason}.\nNothing is made before it has. It is tried again whenever the order page asks and when "
               f"Stripe retries the webhook. If it does not go out soon, check {site()}{LEGAL_PACK_PATH} and Resend, then:\n"
               f"  python scripts/order_admin.py resend-mail {order}\n")


def mark_review(order, reason, eye=0):
    """review.json: a person must look at this order before anything more is made or delivered. An existing mark
    (an earlier reason) is kept. Never raises."""
    now = int(time.time())
    try:
        store.put(order_path(order, "review.json"), store.json_bytes({"reason": reason, "eye": eye, "t": now,
                                                                      "iso": iso(now)}),
                  "application/json", upsert=False, timeout=8.0)
    except store.StorageExists:
        pass
    except store.StorageError as e:
        log(f"order {order}: review mark not stored: {e}")
    index_review(order, now)


REVIEW_INDEX = "cleanup/review"    # paid orders held for a person: cleanup/review/<order>.json {"t": when held}
REVIEW_REMIND_HOURS = 24           # held this long, the owner gets one reminder (the terms promise the file in 48 h;
                                   # the daily run lands 24-48 h after the hold, so always before the promise)


def index_review(order, t=None):
    """Note that a paid order is held for a person (review.json, or an artwork waiting for release): the daily
    clean-up reminds the owner of it once it has waited REVIEW_REMIND_HOURS (cleanup._reviews) and drops the note
    when the hold is gone. The first note of an order is kept (upsert=False). Written wherever an order is held:
    mark_review, order.py _to_review and compose, the admin panel's recompose. Never raises."""
    try:
        store.put(f"{REVIEW_INDEX}/{order}.json", store.json_bytes({"t": int(t or time.time())}), "application/json",
                  upsert=False, timeout=6.0)
    except store.StorageExists:
        pass
    except Exception as e:  # noqa: the hold itself and its note stand; only the later reminder is at stake
        log(f"order {order}: review index not stored: {type(e).__name__} {e}")


def hold_confirmation(order, paid, why):
    """The confirmation email cannot go out: the order is held (review.json) and the owner is told how to go on."""
    why = re.sub(r"[^a-z_]", "", str(why))[:30] or "failed"
    log(f"order {order}: confirmation email {why}: HELD, nothing is made until it went out")
    mark_review(order, f"{MAIL_REVIEW}_{why}")
    owner_note(order, "mail", f"SnapEyes: order {order} is paid, but its confirmation email did not go out",
               f"Order {order} is paid ({amount_text(paid.get('amount_total') or 0, 'en')}, "
               f"{'live' if paid.get('livemode') else 'TEST mode'}), but the order confirmation email could not be sent "
               f"({why}).\nNothing is made for this order yet: the file may only be made after the customer has the "
               f"confirmation, because it confirms their withdrawal waiver (otherwise they keep the right of "
               f"withdrawal).\nCustomer: {paid.get('email') or 'no email'}\n\n"
               f"Fix the cause (RESEND_API_KEY, the snapeyes.com domain at Resend), then:\n"
               f"  python scripts/order_admin.py resend-mail {order}\n"
               f"If you sent the confirmation yourself (for example to a corrected address; it must hold the same "
               f"texts: the order, the consent, the withdrawal information and the terms):\n"
               f"  python scripts/order_admin.py mailed-by-hand {order}\n"
               f"Either one lets the order page go on.\nStatus: python scripts/order_admin.py status {order}\n")


# ----------------------------------------------------------------------------- owner notes
def note_once(path, kind, subject, text):
    """A short note to the owner (SNAPEYES_OWNER_MAIL, default info@snapeyes.com), once per claim path. Always
    logged; never raises."""
    log(f"NOTE {kind}: {subject}")
    try:
        if not email_configured():
            return "off"
        if not claim_once(path):
            return "done"
        res = send_mail(owner_mail(), subject, text, "snapeyes-note-" + path.replace("/", "-")[:200])
        _mark(path, "retry" if res == "transient" else ("sent" if res == "sent" else "failed"), result=res)
        return res
    except Exception as e:  # noqa: a note must never cost an order
        log(f"note {kind} not sent: {type(e).__name__} {e}")
        return "failed"


def owner_note(order, kind, subject, text):
    """note_once for one order: once per order and kind (orders/<order>/note_<kind>.json)."""
    try:
        path = order_path(order, f"note_{kind}.json")
    except Exception as e:  # noqa
        log(f"note {kind} order {order} not sent: {type(e).__name__}")
        return "failed"
    return note_once(path, f"{kind} order {order}", subject, text)


def note_paid(order, paid):
    spec = paid.get("spec") or {}
    subject = f"SnapEyes: new order {order}, {amount_text(paid.get('amount_total') or 0, 'en')}"
    text = (f"Order {order} is paid ({'live' if paid.get('livemode') else 'TEST mode'}).\n"
            f"Eyes: {spec.get('eyes')}, style {spec.get('style')}, layout {spec.get('layout')}\n"
            f"Names: {spec.get('names') or '-'}\nTitle: {spec.get('title') or '-'}\nLanguage: {spec.get('lang')}\n"
            f"Customer: {paid.get('email') or 'no email'}\nStripe session: {paid.get('session_id')}\n"
            f"Status: python scripts/order_admin.py status {order}\n")
    return owner_note(order, "paid", subject, text)


# ----------------------------------------------------------------------------- the daily clean-up
def folder_files(folder):
    """Every object under a folder (recursive), as paths."""
    out = []
    for row in store.list_all(folder):
        p = f"{folder}/{row['name']}"
        out += folder_files(p) if row["folder"] else [p]
    return out


def stripe_verdict(order, rec, record=True):
    """What Stripe says about an UNPAID order's Checkout Sessions before its files are deleted:
      "none"     no session, or none that can still be paid (expired; test sessions where test orders do not count)
      "paid"     a session IS paid: the webhook never arrived. With record, it is recorded now (paid.json; the
                 customer gets the confirmation email and the owner the note, as after any payment)
      "open"     a session is still payable, or completed with a method that settles later: keep the order
      "unknown"  Stripe cannot be asked here (no key, a live session and a test key, no answer): keep the order"""
    ids = order_sessions(rec, n=10)
    if not ids:
        return "none"
    if not stripe_key():
        return "unknown"
    verdict = "none"
    for sid in ids:
        if sid.startswith("cs_test_") and stripe_live():
            continue                  # a test session: never money, and a live key cannot see it
        if sid.startswith("cs_live_") and not stripe_live():
            return "unknown"
        try:
            sess = retrieve_session(sid)
        except (PayBusy, PayError, PayNotConfigured) as e:
            log(f"clean-up: order {order}: Stripe did not answer about {sid}: {e}")
            return "unknown"
        if not session_matches(sess, order, rec):
            continue
        if session_paid(sess) and session_counts(sess):
            if record:
                paid, new = record_paid(order, rec, sess, "cleanup")
                if new:
                    log(f"order {order}: PAID at Stripe but never marked paid here (the webhook did not arrive): "
                        f"recorded by the clean-up")
                    after_paid(order, rec, paid)
            return "paid"
        created = sess.get("created") if isinstance(sess.get("created"), (int, float)) else None
        if sess.get("status") == "open" or (sess.get("status") == "complete" and
                                            (created is None or created > time.time() - SETTLE_DAYS * 86400)):
            verdict = "open"
        # a session completed but still unpaid after SETTLE_DAYS: its delayed payment failed, it is no money
    return verdict


SETTLE_DAYS = 20             # a delayed payment method (SEPA and the like) settles within about 14 business days


def _order_folders(days=None):
    """The order folder names to look at: those of the given yymmdd days, or every one."""
    if days is None:
        return [r["name"] for r in store.list_all("orders") if r["folder"] and store.ORDER_RE.fullmatch(r["name"])]
    return sorted({o for rows in day_folders(days).values() for o in rows})


def day_folders(days):
    """{yymmdd: [order folder names made that day]} for the given days, listed 8 days at a time."""
    days = sorted(set(days))
    out = {}
    for i in range(0, len(days), 8):
        batch = days[i:i + 8]
        rows = parallel([lambda d=d: store.list_all("orders", search=d + "-") for d in batch])
        for d, rs in zip(batch, rows):
            out[d] = sorted(r["name"] for r in rs if r["folder"] and r["name"].startswith(d + "-")
                            and store.ORDER_RE.fullmatch(r["name"]))
    return out


def purge_unpaid(hours=PURGE_HOURS, yes=False, out=None, days=None, stop_left=8.0, names=None, markers=True):
    """Delete UNPAID orders older than `hours` (their eye photos and records), and (markers) the ticketuse/,
    draftlog/ and withdrawlog/ markers older than MARKER_DAYS days. An order with a Checkout Session is asked of
    Stripe first (stripe_verdict): a paid one is recorded as paid instead of deleted, one still open or settling is
    kept, and nothing is deleted when Stripe cannot be asked. Without yes nothing changes anywhere (Stripe is still
    asked, nothing recorded). names: the order folders to look at; else those of the given yymmdd days; else every
    order folder. Stops when less than stop_left seconds of the invocation are left (more: true). Returns the counts,
    "left": the unpaid orders still there (too young, kept, or not reached), and "kept_orders": those kept because
    Stripe could not vouch for them (the daily clean-up asks again about them: cleanup/kept/)."""
    say = out or log
    cutoff = time.time() - hours * 3600
    res = {"deleted": 0, "kept": 0, "recorded": 0, "markers": 0, "more": False, "left": [], "kept_orders": []}
    names = list(names) if names is not None else _order_folders(days)
    left = set()
    todo = []                     # (order, record) of the unpaid orders old enough, read 8 at a time
    for i in range(0, len(names), 8):
        if L.time_left() < stop_left:
            res["more"] = True
            left.update(names[i:])
            break
        batch = names[i:i + 8]
        facts = parallel([lambda o=o: (store.exists(f"orders/{o}/paid.json"), store.get_json(f"orders/{o}/order.json"))
                          for o in batch])
        for order, (is_paid, rec) in zip(batch, facts):
            made = rec.get("created_at") if isinstance(rec, dict) else None
            if is_paid or not isinstance(rec, dict):
                continue          # paid, or a folder that is not a draft order (test runs): left alone
            if isinstance(made, (int, float)) and made <= cutoff:
                todo.append((order, rec))
            else:
                left.add(order)   # a young draft
    for n, (order, rec) in enumerate(todo):
        if L.time_left() < stop_left:
            res["more"] = True
            left.update(o for o, _ in todo[n:])
            break
        verdict = stripe_verdict(order, rec, record=yes)
        if verdict == "paid":
            res["recorded"] += 1
            say(f"{'RECORDED' if yes else 'would record'} {order} as PAID: Stripe has a paid session for it")
            continue
        if verdict in ("open", "unknown"):
            res["kept"] += 1
            res["kept_orders"].append(order)
            left.add(order)
            say(f"keep {order} made {rec.get('created')}: its Stripe session is "
                f"{'still open or settling' if verdict == 'open' else 'unknown here (no Stripe key or no answer)'}")
            continue
        files = folder_files(f"orders/{order}")
        say(f"{'DELETE' if yes else 'would delete'} unpaid {order} made {rec.get('created')}: {len(files)} files")
        if yes:
            # order.json last, so a run that stops half way leaves an order this clean-up finds again; the admin
            # log of the order goes with its record, before order.json
            rest = [p for p in files if not p.endswith("/order.json")]
            store.delete_many(rest)
            drop_orderlog(order, out=say)
            store.delete_many([p for p in files if p.endswith("/order.json")])
        else:
            left.add(order)
        res["deleted"] += 1
    if markers and not res["more"]:
        res["markers"] = purge_markers(yes, stop_left, res)
    res["left"] = sorted(left)
    return res


MARKER_TOPS = ("ticketuse", "draftlog", "withdrawlog")


def purge_markers(yes, stop_left, res=None):
    """Remove the per-day marker folders (ticketuse/, draftlog/, withdrawlog/) older than MARKER_DAYS. Returns how
    many files went (or would go)."""
    old = day(time.time() - MARKER_DAYS * 86400)
    n = 0
    for top in MARKER_TOPS:
        for row in store.list_all(top):
            if L.time_left() < stop_left:
                if res is not None:
                    res["more"] = True
                return n
            if row["folder"] and re.fullmatch(r"[0-9]{6}", row["name"]) and row["name"] < old:
                files = folder_files(f"{top}/{row['name']}")
                if yes:
                    store.delete_many(files)
                n += len(files)
    return n


# What stays of a PAID order once its files are deleted (on request, after a withdrawal, or 12 months after payment):
# the order's records, no images. The privacy policy ("Order records") keeps them as proof of the contract and for
# accounting: order.json and paid.json (order number, date, price, payment, email, the artwork's details, consent),
# the email and note marks, the withdrawal statements, and the marks that say what happened.
KEEP_NAMES = ("order.json", "paid.json", "mail_delivery.json", "deleted.json", "expired.json", "withdrawn.json",
              "withdrawal.json", "making.json", "refunded.json")
KEEP_PREFIXES = ("note_", "extra_payment_", "withdrawal_", "withdrawal-")


def kept_record(path):
    name = path.rsplit("/", 1)[-1]
    return name in KEEP_NAMES or name.startswith(KEEP_PREFIXES)


def erase_files(order, why, yes=True, out=None):
    """Delete an order's files: all of them when it is unpaid (its admin log, ops/orderlog/<order>/, with them:
    nothing of the order stays); for a paid order everything but its records (kept_record), and its admin log stays
    with them. deleted.json is written first, so the order page says "deleted" (410) even if a run stops half way.
    Returns (files deleted or to delete, files in all)."""
    say = out or log
    files = folder_files(f"orders/{order}")
    paid = store.exists(f"orders/{order}/paid.json")
    gone = [p for p in files if not kept_record(p)] if paid else files
    say(f"{'DELETE' if yes else 'would delete'} {'paid' if paid else 'unpaid'} {order} ({why}): {len(gone)} of "
        f"{len(files)} files")
    if yes and paid:
        store.put(f"orders/{order}/deleted.json", store.json_bytes({"t": int(time.time()), "iso": iso(), "why": why}),
                  "application/json", upsert=True)
    if yes and gone:
        store.delete_many([p for p in gone if not p.endswith("/order.json")])
        if not paid:
            drop_orderlog(order, out=say)
        store.delete_many([p for p in gone if p.endswith("/order.json")])
    return len(gone), len(files)


ORDERLOG_TOP = "ops/orderlog"      # the admin panel's log of one order (api/_lib/ops.py audit): part of its record


def drop_orderlog(order, yes=True, out=None):
    """Delete the admin panel's log of an order (ops/orderlog/<order>/) when the order goes completely (an unpaid
    order, a lab test): the privacy policy keeps those entries only "with that order's record, for as long as the
    record is kept". A paid order's records stay, and its log with them (never call this for one). Best effort:
    what a failed call leaves is found by the daily clean-up (cleanup._orphan_logs). Returns how many files went
    (or would go)."""
    say = out or log
    try:
        files = folder_files(f"{ORDERLOG_TOP}/{order}")
        if yes and files:
            store.delete_many(files)
    except store.StorageError as e:
        log(f"order {order}: admin log not deleted (the daily clean-up retries): {e}")
        return 0
    if files:
        say(f"{'DELETE' if yes else 'would delete'} the admin log of {order}: {len(files)} entries")
    return len(files)


PAID_KEEP_DAYS = 365         # the files of a paid order are kept 12 months after payment (privacy policy), then go


def expire_paid(days_kept=PAID_KEEP_DAYS, yes=False, out=None, names=None, stop_left=8.0):
    """Delete the files of PAID orders paid more than days_kept days ago (their records stay: erase_files), once
    (expired.json). names: the order folders to look at (the daily run's), else every order folder. Returns
    {expired, files, left, more}: left = paid orders among names that are not due yet (or not reached)."""
    say = out or log
    cutoff = time.time() - days_kept * 86400
    names = list(names) if names is not None else _order_folders(None)
    res = {"expired": 0, "files": 0, "left": [], "more": False}
    left = set()
    for i in range(0, len(names), 8):
        if L.time_left() < stop_left:
            res["more"] = True
            left.update(names[i:])
            break
        batch = names[i:i + 8]
        facts = parallel([lambda o=o: (get_paid(o), store.exists(f"orders/{o}/expired.json")) for o in batch])
        for order, (paid, done) in zip(batch, facts):
            if not paid or done:
                continue
            t = paid.get("paid_at")
            if not isinstance(t, (int, float)) or t >= cutoff:
                left.add(order)
                continue
            if L.time_left() < stop_left:
                res["more"] = True
                left.add(order)
                continue
            n, _ = erase_files(order, f"kept {days_kept} days after payment", yes, say)
            if yes:
                store.put(f"orders/{order}/expired.json", store.json_bytes({"t": int(time.time()), "iso": iso(),
                                                                           "paid_at": t}),
                          "application/json", upsert=True)
            else:
                left.add(order)
            res["expired"] += 1
            res["files"] += n
    res["left"] = sorted(left)
    return res
