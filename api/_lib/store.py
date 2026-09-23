# -*- coding: utf-8 -*-
"""Private storage for the paid deliverables: a tiny Supabase Storage REST client, plus the few rules the two paid
endpoints (/api/master_eye, /api/master_compose) share.

Environment (server side only):
  SNAPEYES_SUPABASE_URL          https://<project>.supabase.co
  SNAPEYES_SUPABASE_SERVICE_KEY  the service_role JWT or an sb_secret_ key. It bypasses row level security, so it
                                 lives in this process alone: it travels in request headers, never in a URL, a log
                                 line, an error message or a reply. A value that is not a plain ASCII token (for
                                 example one that picked up an invisible BOM on its way into `vercel env add`) is
                                 cleaned of invisible characters, and if it is still not a token the storage counts
                                 as not configured: the key is never put into a header it could crash, because
                                 that crash's text would carry the whole key into the log.
  SNAPEYES_BUCKET                default "snapeyes-private". The bucket must be PRIVATE: before the first write in a
                                 container the bucket is read back and a public bucket is refused. Files leave only
                                 through signed_url(). Nothing here creates buckets or changes their settings.

STORE_LOCAL_DIR (tests only): a local folder that stands in for the bucket, so the endpoints can be exercised
without a Supabase project. It is ignored whenever VERCEL is set, so a stray variable on a deployment cannot make
it write customer files to its own disk.

Every call respects the invocation deadline (iris.time_left): a request that cannot finish before the function is
killed is not started, and each timeout is cut to the time that is left.

Errors: StorageNotConfigured when the environment is missing (the endpoints answer 503 before any work),
StorageError for everything else (StorageExists when put() may not overwrite an existing object)."""
import os, re, time, json, uuid, shutil, threading, pathlib
from urllib.parse import quote
import requests
from .iris import time_left

DEFAULT_BUCKET = "snapeyes-private"
MIN_LEFT = 2.0               # seconds: below this no storage request is started
GET_MAX_BYTES = 64 << 20     # a stored master is ~3-9 MB; anything far larger is not one of ours
SIGNED_MAX = 7 * 86400       # the longest link we hand out: a link that never expires is not private
_PATH = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9_.-]{0,79}(/[A-Za-z0-9_-][A-Za-z0-9_.-]{0,79}){0,7}$")
_BUCKET = re.compile(r"^[a-z0-9][a-z0-9._-]{1,62}$")
_URL = re.compile(r"^(https://[A-Za-z0-9.-]+(:[0-9]{1,5})?|http://(localhost|127\.0\.0\.1)(:[0-9]{1,5})?)$")
_KEY = re.compile(r"^[A-Za-z0-9._-]{20,4096}$")     # a JWT (base64url and dots) or an sb_secret_ key
_INVISIBLE = "".join(map(chr, (0xFEFF, 0x200B, 0x200C, 0x200D, 0x2060, 0x00A0, 0x180E)))   # BOM, zero-width, no-break space


class StorageError(RuntimeError):
    """A storage call failed. The message names the operation, the object path and the HTTP status; it never
    carries the service key or a signed link."""


class StorageNotConfigured(StorageError):
    def __init__(self, why="SNAPEYES_SUPABASE_URL and SNAPEYES_SUPABASE_SERVICE_KEY are not set"):
        super().__init__("storage not configured: " + why)


class StorageExists(StorageError):
    """put(..., upsert=False) found an object at that path already."""


# ----------------------------------------------------------------------------- configuration
def _clean(v):
    """An env value without surrounding whitespace or invisible characters (BOM, zero-width, no-break space)."""
    v = str(v or "")
    prev = None
    while v != prev:
        prev = v
        v = v.strip().strip(_INVISIBLE)
    return v


def _env():
    url = _clean(os.environ.get("SNAPEYES_SUPABASE_URL")).rstrip("/")
    key = _clean(os.environ.get("SNAPEYES_SUPABASE_SERVICE_KEY"))
    bucket = _clean(os.environ.get("SNAPEYES_BUCKET")) or DEFAULT_BUCKET
    return url, key, bucket


def _local_dir():
    """The test stand-in folder, or "" (always "" on Vercel)."""
    if os.environ.get("VERCEL"):
        return ""
    return _clean(os.environ.get("STORE_LOCAL_DIR"))


def problem():
    """Why there is nowhere to keep files, in words that never include a value ("" when configured)."""
    if _local_dir():
        return ""
    url, key, bucket = _env()
    if not url or not key:
        return "SNAPEYES_SUPABASE_URL and SNAPEYES_SUPABASE_SERVICE_KEY are not set"
    if not _URL.fullmatch(url):
        return "SNAPEYES_SUPABASE_URL is not an https URL"
    if not _KEY.fullmatch(key):
        return "SNAPEYES_SUPABASE_SERVICE_KEY is malformed (not a plain ASCII token; the value is not logged)"
    if not _BUCKET.fullmatch(bucket):
        return "SNAPEYES_BUCKET is not a valid bucket name"
    return ""


def configured():
    """True when there is somewhere to keep files. Cheap (environment only, no request)."""
    return not problem()


def _require():
    """(url, key, bucket) for a Supabase call. Callers take the STORE_LOCAL_DIR branch before this."""
    why = problem()
    if why:
        raise StorageNotConfigured(why)
    return _env()


def _check_path(path):
    if not isinstance(path, str) or len(path) > 300 or not _PATH.fullmatch(path):
        raise StorageError("storage: refused an invalid object path")
    return path


def _safe(text):
    """Error text from the storage API, trimmed, with the key blanked in case anything ever echoes it."""
    s = str(text or "")[:200]
    for v in {_env()[1], str(os.environ.get("SNAPEYES_SUPABASE_SERVICE_KEY") or "")}:
        if len(v) >= 8:
            s = s.replace(v, "***")
    return s


def _headers(key, extra=None):
    # Supabase: "Send publishable and secret keys on the apikey header, not on Authorization: Bearer" (an
    # sb_secret_ key is not a JWT). The legacy service_role key is a JWT and is also sent as the bearer.
    h = {"apikey": key}
    if key.startswith("eyJ") and key.count(".") == 2:
        h["Authorization"] = "Bearer " + key
    if extra:
        h.update(extra)
    return h


def _obj(url, bucket, path, kind="object"):
    return f"{url}/storage/v1/{kind}/{quote(bucket)}/{quote(path, safe='/')}"


def _call(op, method, url, timeout, retry=True, **kw):
    """One HTTP request inside the deadline. A connection error or a 502/503/504 is tried once more when retry is
    on and the second attempt still fits; anything else is returned for the caller to judge. Every failure of the
    request itself becomes a StorageError that names only the operation and the exception type: an exception's
    text can hold the URL or, for a header that cannot be encoded, the header value."""
    for attempt in (1, 2):
        left = time_left()
        if left < MIN_LEFT:
            raise StorageError(f"{op}: out of time ({left:.1f} s left)")
        t = max(1.0, min(timeout, left - 1.0))
        try:
            r = requests.request(method, url, timeout=t, **kw)
        except Exception as e:  # noqa: not only RequestException: a UnicodeEncodeError would carry the key
            if retry and attempt == 1 and isinstance(e, requests.RequestException) and time_left() > t + MIN_LEFT + 1.0:
                time.sleep(0.5)
                continue
            raise StorageError(f"{op}: {type(e).__name__}") from None
        if retry and r.status_code in (502, 503, 504) and attempt == 1 and time_left() > t + MIN_LEFT + 1.0:
            r.close()
            time.sleep(0.5)
            continue
        return r
    raise StorageError(f"{op}: no attempt left")


def _missing(r):
    """Supabase answers a missing object with 404, or with 400 and statusCode "404" / not_found in the body. A 404
    from the router itself ("Route GET:... not found") is not a missing object: that is an API this client does
    not know, and it must not read as "nothing stored here"."""
    text = r.text or ""
    if r.status_code == 404:
        try:
            msg = str(json.loads(text).get("message") or "")
        except (ValueError, AttributeError):
            msg = ""
        return not (msg.startswith("Route ") and msg.endswith(" not found"))
    return r.status_code == 400 and ('"404"' in text or "not_found" in text or "not found" in text.lower())


# ----------------------------------------------------------------------------- the private-bucket guard
_PRIVATE = {}
_PRIVATE_LOCK = threading.Lock()


def ensure_private(timeout=8.0, retry=True):
    """Refuse to work with a public bucket. Read once per container and remembered only when it passed."""
    if _local_dir():
        return True
    url, key, bucket = _require()
    with _PRIVATE_LOCK:
        if _PRIVATE.get((url, bucket)):
            return True
    r = _call(f"bucket {bucket}", "GET", f"{url}/storage/v1/bucket/{quote(bucket)}", timeout, retry,
              headers=_headers(key))
    if r.status_code != 200:
        raise StorageError(f"bucket {bucket}: HTTP {r.status_code} {_safe(r.text)}")
    try:
        j = r.json()
    except ValueError:
        raise StorageError(f"bucket {bucket}: unreadable reply") from None
    public = j.get("public") if isinstance(j, dict) else None
    if public is not False:
        raise StorageError(f"bucket {bucket} is not private (public={public!r}); refusing to store customer files there")
    with _PRIVATE_LOCK:
        _PRIVATE[(url, bucket)] = True
    return True


# ----------------------------------------------------------------------------- operations
def _local_file(d, path):
    return pathlib.Path(d, *path.split("/"))


def put(path, data, content_type, upsert=False, timeout=30.0, retry=True):
    """Store bytes at path. upsert=False never overwrites (StorageExists instead) and is atomic: of two requests
    that race for the same path exactly one wins, so it can claim a slot. Returns the path."""
    _check_path(path)
    if not isinstance(data, (bytes, bytearray)):
        raise StorageError(f"put {path}: data must be bytes")
    d = _local_dir()
    if d:
        f = _local_file(d, path)
        f.parent.mkdir(parents=True, exist_ok=True)
        tmp = f.with_name(f"{f.name}.{uuid.uuid4().hex}.part")
        tmp.write_bytes(bytes(data))
        try:
            if upsert:
                os.replace(tmp, f)
            else:
                try:
                    os.link(tmp, f)      # create-if-absent in one step, like the bucket's own 409
                except FileExistsError:
                    raise StorageExists(f"put {path}: already exists") from None
        finally:
            if tmp.exists():
                tmp.unlink()
        return path
    url, key, bucket = _require()
    ensure_private()
    r = _call(f"put {path}", "POST", _obj(url, bucket, path), timeout, retry, data=bytes(data),
              headers=_headers(key, {"Content-Type": content_type, "x-upsert": "true" if upsert else "false"}))
    if r.status_code in (200, 201):
        return path
    if r.status_code == 409 or (r.status_code == 400 and ('"409"' in r.text or "Duplicate" in r.text or "already exists" in r.text)):
        raise StorageExists(f"put {path}: already exists")
    raise StorageError(f"put {path}: HTTP {r.status_code} {_safe(r.text)}")


def get(path, max_bytes=GET_MAX_BYTES, timeout=30.0, retry=True):
    """The bytes stored at exactly this path, or None when there is no such object."""
    _check_path(path)
    d = _local_dir()
    if d:
        f = _local_file(d, path)
        if not f.is_file():
            return None
        if f.stat().st_size > max_bytes:
            raise StorageError(f"get {path}: larger than {max_bytes} bytes")
        return f.read_bytes()
    url, key, bucket = _require()
    r = _call(f"get {path}", "GET", _obj(url, bucket, path, "object/authenticated"), timeout, retry,
              headers=_headers(key), stream=True)
    try:
        if _missing(r):
            return None
        if r.status_code != 200:
            raise StorageError(f"get {path}: HTTP {r.status_code} {_safe(r.text)}")
        buf = bytearray()
        for chunk in r.iter_content(1 << 20):
            buf += chunk
            if len(buf) > max_bytes:
                raise StorageError(f"get {path}: larger than {max_bytes} bytes")
        return bytes(buf)
    except StorageError:
        raise
    except Exception as e:  # noqa: a broken download names only its type
        raise StorageError(f"get {path}: {type(e).__name__}") from None
    finally:
        r.close()


def exists(path, timeout=10.0, retry=True):
    """Is there an object at exactly this path? Asked of the object itself (GET /object/info/authenticated/...),
    never read from a folder listing: Supabase lists a folder case-insensitively, so a listing of orders/ABCD
    also shows the files of orders/abcd."""
    _check_path(path)
    d = _local_dir()
    if d:
        return _local_file(d, path).is_file()
    url, key, bucket = _require()
    r = _call(f"exists {path}", "GET", _obj(url, bucket, path, "object/info/authenticated"), timeout, retry,
              headers=_headers(key))
    try:
        if r.status_code == 200:
            return True
        if _missing(r):
            return False
        raise StorageError(f"exists {path}: HTTP {r.status_code} {_safe(r.text)}")
    finally:
        r.close()


def copy(src, dst, timeout=10.0, retry=True):
    """Copy one object to a new path inside the bucket, server side (no download). Never overwrites dst."""
    _check_path(src)
    _check_path(dst)
    d = _local_dir()
    if d:
        a, b = _local_file(d, src), _local_file(d, dst)
        if not a.is_file():
            raise StorageError(f"copy {src}: no such object")
        if b.exists():
            raise StorageExists(f"copy {dst}: already exists")
        b.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(a, b)
        return dst
    url, key, bucket = _require()
    r = _call(f"copy {src}", "POST", f"{url}/storage/v1/object/copy", timeout, retry,
              json={"bucketId": bucket, "sourceKey": src, "destinationKey": dst}, headers=_headers(key))
    if r.status_code in (200, 201):
        return dst
    if r.status_code == 409 or (r.status_code == 400 and ('"409"' in r.text or "Duplicate" in r.text or "already exists" in r.text)):
        raise StorageExists(f"copy {dst}: already exists")
    raise StorageError(f"copy {src}: HTTP {r.status_code} {_safe(r.text)}")


def signed_url(path, seconds):
    """A time-limited download link for a private object (at most SIGNED_MAX seconds). The link is a bearer
    credential: hand it to the customer, never write it to a log."""
    _check_path(path)
    seconds = int(max(60, min(SIGNED_MAX, int(seconds))))
    d = _local_dir()
    if d:
        f = _local_file(d, path)
        if not f.is_file():
            raise StorageError(f"sign {path}: no such object")
        return f.resolve().as_uri() + f"?expires={int(time.time()) + seconds}"
    url, key, bucket = _require()
    r = _call(f"sign {path}", "POST", _obj(url, bucket, path, "object/sign"), 10.0,
              json={"expiresIn": seconds}, headers=_headers(key))
    if r.status_code != 200:
        raise StorageError(f"sign {path}: HTTP {r.status_code} {_safe(r.text)}")
    try:
        j = r.json()
    except ValueError:
        j = None
    rel = (j.get("signedURL") or j.get("signedUrl") or "") if isinstance(j, dict) else ""
    rel = rel if isinstance(rel, str) else ""
    if rel.startswith("https://"):
        return rel
    if not rel.startswith("/"):
        raise StorageError(f"sign {path}: no link in the reply")
    return f"{url}/storage/v1{rel}"


def delete(path, timeout=10.0, retry=True):
    """Remove one object. True when something was removed, False when there was nothing there."""
    _check_path(path)
    d = _local_dir()
    if d:
        f = _local_file(d, path)
        try:
            f.unlink()
            return True
        except FileNotFoundError:
            return False
    url, key, bucket = _require()
    r = _call(f"delete {path}", "DELETE", f"{url}/storage/v1/object/{quote(bucket)}", timeout, retry,
              json={"prefixes": [path]}, headers=_headers(key))
    if r.status_code != 200:
        raise StorageError(f"delete {path}: HTTP {r.status_code} {_safe(r.text)}")
    try:
        return bool(r.json())
    except ValueError:
        return True


# ----------------------------------------------------------------------------- the stored file format
_SRGB = None


def srgb_icc():
    """An sRGB ICC profile to embed, so a viewer or print shop reads the colours as they were made. b"" when
    the Pillow build has no littleCMS (then the file is written without a profile, which viewers take as sRGB)."""
    global _SRGB
    if _SRGB is None:
        try:
            from PIL import ImageCms
            _SRGB = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
        except Exception:  # noqa: a missing profile must not cost an order
            _SRGB = b""
    return _SRGB


def jpeg_bytes(im, quality=95):
    """The stored format of every deliverable: baseline JPEG, 4:4:4 (no chroma subsampling: iris fibres are
    colour detail), sRGB profile embedded, no other metadata."""
    import io
    buf = io.BytesIO()
    kw = {"quality": int(quality), "subsampling": 0}
    icc = srgb_icc()
    if icc:
        kw["icc_profile"] = icc
    im.convert("RGB").save(buf, "JPEG", **kw)
    return buf.getvalue()


def json_bytes(obj):
    return json.dumps(obj, ensure_ascii=True, sort_keys=True).encode("utf-8")


def get_json(path, timeout=10.0, retry=True):
    """A small JSON record (an eye's or an artwork's), or None when it is missing or unreadable."""
    raw = get(path, max_bytes=64 << 10, timeout=timeout, retry=retry)
    if raw is None:
        return None
    try:
        obj = json.loads(raw)
    except ValueError:
        return None
    return obj if isinstance(obj, dict) else None


# ----------------------------------------------------------------------------- orders and their tickets
# An order id names one private folder, orders/<order>/. Lower case only: Supabase compares object names
# case-insensitively in places (its folder search uses lower(name) and ILIKE), so two ids that differ only in case
# must not both exist. No "_" either: in an ILIKE pattern it matches any character.
ORDER_RE = re.compile(r"^[a-z0-9][a-z0-9-]{3,63}$")


def check_order(v):
    """The order id, or ClientError. Ids are made by the site (later by the Stripe webhook), never by a person."""
    from .iris import ClientError
    if not isinstance(v, str) or not ORDER_RE.fullmatch(v):
        raise ClientError("Send a valid order id.")
    return v


def unlock_kind(order):
    """The ticket kind that opens the paid endpoints for this one order: "unlock-<order>". An order id holds no
    dot, so it cannot reach into the ticket's expiry or signature fields. A plain "unlock" ticket (the clean
    /api/compose preview) opens neither paid endpoint, and a ticket for one order opens no other order."""
    return "unlock-" + check_order(order)


# ----------------------------------------------------------------------------- replies the paid endpoints share
class Answer(Exception):
    """A deliberate non-200 JSON reply from a paid endpoint: 409 while an eye is still rendering, 502 when a paid
    render came back unusable (retrying would repeat it), 503 when a retry later can succeed. The body always has
    ok false, a reason code for the client, retry (bool) and a sentence for the customer."""

    def __init__(self, status, reason, error, retry, retry_after=None, **extra):
        super().__init__(reason)
        self.status = int(status)
        self.body = {"ok": False, "reason": reason, "error": error, "retry": bool(retry)}
        if retry_after is not None:
            self.body["retry_after"] = int(retry_after)
        self.body.update(extra)
        self.retry_after = retry_after


def busy(reason, retry_after, error="We are busy for a moment. Please try again shortly."):
    return Answer(503, reason, error, True, retry_after)


class _StatusReq:
    """The request as L.run sees it, except that L.run's 200 becomes the status of an Answer the endpoint raised.
    Everything else (headers, body, the 400/403/415/500 replies) is L.run's own."""

    def __init__(self, req):
        self._req, self.status, self.retry_after = req, None, None

    def __getattr__(self, name):
        return getattr(self._req, name)

    def send_response(self, code, message=None):
        if code == 200 and self.status:
            code = self.status
        if message is None:
            self._req.send_response(code)
        else:
            self._req.send_response(code, message)

    def end_headers(self):
        if self.status and self.retry_after is not None:
            self._req.send_header("Retry-After", str(int(self.retry_after)))
        self._req.end_headers()


def serve(req, name, fn):
    """Run a paid endpoint: the 503 without storage first, then L.run (its gates, JSON parsing and error replies),
    with an Answer mapped to its own status and a StorageError to a retryable 503."""
    from . import iris as L
    if refuse_unconfigured(req, name):
        return
    box = _StatusReq(req)

    def wrapped(body):
        try:
            return fn(body)
        except StorageNotConfigured:
            a = Answer(503, "storage_not_configured", "Ordering is not open yet.", False)
        except StorageError as e:
            print(f"snapeyes {name} storage error:", L._scrub(str(e))[:300], flush=True)
            a = busy("storage_busy", 10, "Our storage did not answer. Please try again in a moment.")
        except Answer as e:
            a = e
        box.status, box.retry_after = a.status, a.retry_after
        return dict(a.body)
    L.run(box, wrapped)


def _drain(req, cap=8 << 20):
    """Read the request body before answering early, so the client is not reset mid-upload."""
    try:
        n = min(int(req.headers.get("content-length") or 0), cap)
        while n > 0:
            chunk = req.rfile.read(min(n, 1 << 20))
            if not chunk:
                break
            n -= len(chunk)
    except Exception:  # noqa: draining is a courtesy
        pass


def refuse_unconfigured(req, name):
    """Answer 503 {ok: false, reason: "storage_not_configured"} and return True when there is no storage. Runs
    after the same header gates L.run applies, so a wrong content type or a foreign origin still gets its
    415 / 403 from L.run, and before the body is parsed, the ticket is checked or anything is spent."""
    from .iris import json_content_type, origin_ok, send_json
    why = problem()
    if json_content_type(req) and origin_ok(req) and why:
        _drain(req)
        print(f"snapeyes {name} refused: storage not configured: {why}", flush=True)
        send_json(req, 503, {"ok": False, "reason": "storage_not_configured", "error": "Ordering is not open yet."})
        return True
    return False
