# -*- coding: utf-8 -*-
"""Test harness for the payments backend: a fake Stripe + Resend (one local HTTP stub), and the real API handlers
(api/order.py, checkout.py, stripe_webhook.py, health.py) served over HTTP in this process, on a local store folder.
No real key is used: the Stripe key and webhook secret are synthetic."""
import os, sys, io, json, time, hmac, shutil, hashlib, secrets, threading, importlib.util, base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh (it names the checkout under test)")
API = os.path.join(REPO, "api")

SK = "sk_test_" + "Fake0123456789abcdefGHIJ"
WHSEC = "whsec_" + "c3ludGhldGljLXNlY3JldC1mb3ItdGVzdHM="
RESEND = "re_Fake1234_abcdefghijklmnop"


class Fake:
    """Shared state of the stub: sessions, requests seen, emails sent, failures to inject."""
    sessions = {}
    creates = []          # (params dict, headers dict)
    retrieves = []
    expires = []          # session ids asked to expire
    emails = []
    fail_create = []      # a list of HTTP codes to answer the next create calls with
    fail_mail = []
    legal = None          # the legal pack the stub serves at /legal/order-mail.json (the build's own file)
    legal_fail = 0        # answer the next n legal pack requests with 503
    legal_gets = 0


def _flat(qs):
    return {k: v[0] for k, v in qs.items()}


class StubHandler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _auth(self, want):
        return self.headers.get("Authorization") == "Bearer " + want

    def do_POST(self):
        n = int(self.headers.get("content-length") or 0)
        raw = self.rfile.read(n)
        path = urlsplit(self.path).path
        if path.startswith("/v1/checkout/sessions/") and path.endswith("/expire"):
            # Stripe: only an open session can be expired; otherwise 400 invalid_request_error
            if not self._auth(SK):
                return self._send(401, {"error": {"type": "invalid_request_error", "message": "bad key"}})
            sid = path.split("/")[4]
            Fake.expires.append(sid)
            s = Fake.sessions.get(sid)
            if not s:
                return self._send(404, {"error": {"type": "invalid_request_error", "code": "resource_missing"}})
            if s["status"] != "open":
                return self._send(400, {"error": {"type": "invalid_request_error",
                                                  "message": f"This Checkout Session is {s['status']}."}})
            s["status"] = "expired"
            return self._send(200, s)
        if path == "/v1/checkout/sessions":
            if not self._auth(SK):
                return self._send(401, {"error": {"type": "invalid_request_error", "message": "bad key"}})
            p = _flat(parse_qs(raw.decode("utf-8"), keep_blank_values=True))
            Fake.creates.append((p, dict(self.headers)))
            if Fake.fail_create:
                code = Fake.fail_create.pop(0)
                return self._send(code, {"error": {"type": "api_error", "code": "fake", "message": f"injected {code}"}})
            sid = "cs_test_" + secrets.token_hex(12)
            meta = {k[9:-1]: v for k, v in p.items() if k.startswith("metadata[")}
            sess = {"id": sid, "object": "checkout.session", "mode": p.get("mode"), "status": "open",
                    "payment_status": "unpaid", "currency": p.get("line_items[0][price_data][currency]"),
                    "amount_total": int(p.get("line_items[0][price_data][unit_amount]")), "metadata": meta,
                    "url": f"https://checkout.stripe.test/c/pay/{sid}", "livemode": False, "customer_details": None,
                    "payment_intent": None, "success_url": p.get("success_url"), "expires_at": int(p.get("expires_at"))}
            Fake.sessions[sid] = sess
            return self._send(200, sess)
        if path == "/emails":
            if not self._auth(RESEND):
                return self._send(401, {"message": "bad key"})
            j = json.loads(raw)
            if Fake.fail_mail:
                code = Fake.fail_mail.pop(0)
                return self._send(code, {"message": f"injected {code}"})
            Fake.emails.append((j, self.headers.get("Idempotency-Key")))
            return self._send(200, {"id": "email_" + secrets.token_hex(6)})
        self._send(404, {"error": {"message": "no route"}})

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/legal/order-mail.json":
            Fake.legal_gets += 1
            if Fake.legal_fail:
                Fake.legal_fail -= 1
                return self._send(503, {"error": "injected"})
            if Fake.legal is None:
                with open(os.path.join(REPO, "dist", "legal", "order-mail.json"), encoding="utf-8") as f:
                    Fake.legal = json.load(f)
            return self._send(200, Fake.legal)
        if path.startswith("/v1/checkout/sessions/"):
            if not self._auth(SK):
                return self._send(401, {"error": {"type": "invalid_request_error"}})
            sid = path.rsplit("/", 1)[1]
            Fake.retrieves.append(sid)
            s = Fake.sessions.get(sid)
            return self._send(200, s) if s else self._send(404, {"error": {"type": "invalid_request_error", "code": "resource_missing"}})
        self._send(404, {})


_TICKETS = [0, int(time.time())]


def fresh_ticket():
    """A work ticket no other call used: one ticket makes at most one order now. A ticket is exact to the second
    (work.<expiry>.<hmac>), so each one gets its own expiry, counted down from the start of the run."""
    sys.path.insert(0, API)
    from _lib import iris as L
    _TICKETS[0] += 1
    msg = f"work.{_TICKETS[1] + 900 - _TICKETS[0]}"
    return msg + "." + hmac.new(L._ticket_secret(), msg.encode(), hashlib.sha256).hexdigest()[:32]


def pay_session(sid, email="kunde@example.com"):
    s = Fake.sessions[sid]
    s.update(status="complete", payment_status="paid", customer_details={"email": email},
             payment_intent="pi_test_" + secrets.token_hex(6))
    return s


def signed_event(obj, typ="checkout.session.completed", t=None, secret=WHSEC, eid=None):
    ev = {"id": eid or ("evt_test_" + secrets.token_hex(8)), "object": "event", "type": typ, "livemode": False,
          "data": {"object": obj}}
    body = json.dumps(ev).encode()
    t = int(time.time()) if t is None else t
    sig = hmac.new(secret.encode(), f"{t}.".encode() + body, hashlib.sha256).hexdigest()
    return body, f"t={t},v1={sig}"


def setup_env(store_dir, stub_port, fresh=True):
    for k in ("VERCEL", "SNAPEYES_SUPABASE_URL", "SNAPEYES_SUPABASE_SERVICE_KEY", "SNAPEYES_SITE", "SNAPEYES_MAIL_FROM",
              "SNAPEYES_OWNER_MAIL", "VERCEL_ENV", "SNAPEYES_ALLOW_TEST_ORDERS", "SNAPEYES_DRAFT_DAY_MB", "CRON_SECRET",
              "LEGAL_PACK_BASE"):
        os.environ.pop(k, None)
    if fresh and os.path.isdir(store_dir):
        shutil.rmtree(store_dir)
    os.makedirs(store_dir, exist_ok=True)
    os.environ.update({"STORE_LOCAL_DIR": store_dir, "SNAPEYES_TICKET_SECRET": "paybackend-test-secret",
                       "STRIPE_SECRET_KEY": SK, "STRIPE_WEBHOOK_SECRET": WHSEC, "RESEND_API_KEY": RESEND,
                       "STRIPE_API_BASE": f"http://127.0.0.1:{stub_port}", "RESEND_API_BASE": f"http://127.0.0.1:{stub_port}",
                       "LEGAL_PACK_BASE": f"http://127.0.0.1:{stub_port}",
                       "PYTHONIOENCODING": "utf-8"})


def start_stub():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), StubHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


MODS = {}


def start_api():
    sys.path.insert(0, API)
    for name in ("order", "checkout", "stripe_webhook", "health"):
        spec = importlib.util.spec_from_file_location(name, os.path.join(API, name + ".py"))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        MODS[name] = m

    class D(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _r(self):
            name = urlsplit(self.path).path.rstrip("/").rsplit("/", 1)[-1]
            m = MODS.get(name)
            if not m:
                self.send_response(404)
                self.end_headers()
                return
            m.handle(self)
        do_GET = do_POST = _r

    srv = ThreadingHTTPServer(("127.0.0.1", 0), D)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def jpeg_b64(side=256, seed=1, fmt="JPEG", w=None, h=None):
    import numpy as np
    from PIL import Image
    rng = np.random.default_rng(seed)
    a = rng.integers(0, 255, size=(h or side, w or side, 3), dtype=np.uint8)
    buf = io.BytesIO()
    Image.fromarray(a).save(buf, fmt, **({"quality": 90} if fmt == "JPEG" else {}))
    return base64.b64encode(buf.getvalue()).decode()
