# -*- coding: utf-8 -*-
"""The /try preview protection (owner decision 2026-09-29): the page never holds the clean restored iris.

/api/enhance used to return the clean 1024 px restoration, and /try showed it in its Before/After slider without a
watermark, so a long press or a screenshot kept a clean file. Now /api/enhance returns (protect()):
  image         display_b64(): an 800 px copy (DISPLAY_SIDE) with the preview watermark crossing the iris itself, in
                the page's language (iris.py WATERMARK_TEXT, drawn by iris._watermark_layer), carrying DISPLAY_MARK in
                its JPEG comment so the server can tell it from a clean preview (is_display);
  sealed        seal() of the exact clean JPEG bytes the old "image" carried. /api/compose and the order draft
                (api/order.py) take it back and open it on the server (unseal), so master_eye's "preview" and its
                preview_sha are exactly the enhance output, as before;
  sealed_sizes  {"768": ..., "560": ...}: the clean iris at the sides /try sends to /api/compose for 3-4 and 5-8 eyes
                (src/try/multi.ts composeSide), sealed the same way but as KIND_COMPOSE (only /api/compose opens them).
                The page cannot shrink a sealed iris itself, and eight 1024 px irises do not fit in one request.

What /try shows of the artwork is watermarked across the irises too: /api/compose previews draw the tile's words
iris.WATERMARK_IRIS times as strong on every iris disc, the strength of the display copy here. For a style of the v3 engine
(api/_lib/styles) the words that lie on an iris are drawn in the IRIS'S OWN FRAME (watermark() below, work package WP10): the same
words, the same angle and the same phase relative to the centre of the disc, scaled to its radius, in every tile, in the 1024 px
preview and in the 800 px display copy, so that the many views of one iris the page can obtain all carry one overlay at one place and
an aligned median of them keeps it (see "the iris-anchored overlay").

Sealing uses the standard library only (the function bundle carries no crypto package):
  blob       = VERSION (1 byte) | KIND (1 byte) | expiry (4 bytes, unix seconds, big endian) | nonce (16 random bytes)
               | ciphertext | tag (32 bytes)                                     version 1, the plain envelope
             = VERSION_V2 | KIND | expiry | nonce | eye_id (8 bytes) | profile length (2 bytes, big endian) | profile
               | ciphertext | tag                                                version 2 ("seal v2", work package WP3)
  eye_id     the first 16 hex digits of the sha256 of the clean 1024 px preview bytes (KIND_ORDER's plaintext), written identically
             into all three blobs of an eye (the order copy and the two compose copies, whose own bytes differ); for a KIND_ORDER
             blob it is checked against the plaintext on opening
  profile    the eye's profile (api/_lib/styles/eye.py EyeProfile.to_wire: canonical JSON, zlib, at most PROFILE_MAX bytes): what
             was measured once at /api/enhance (colour class, ring colours, pupil, gate results). It sits in the AUTHENTICATED
             part (the tag covers it, so a page cannot change a byte of it) but is not encrypted: it is derived numbers, never an
             image. Zero length: the profile was not measured (enhance ran short of time), the gate is then unknown.
  seal() writes version 1 unless it is given an eye id or a profile; protect() always gives both. A version 1 blob (at most
  SEAL_TTL old after the deploy of v2) still opens: it carries no profile, so its gate is unknown (hard styles answer "reseal").
  KIND       = KIND_ORDER for "sealed" (the exact enhance output: the only kind an order's draft or /api/master_eye
               opens), KIND_COMPOSE for the smaller "sealed_sizes" copies (only /api/compose opens those), so a 560 px
               compose copy can never become the preview a 4K file is made from
  ciphertext = the clean bytes XOR a keystream of HMAC-SHA256(k_enc, nonce | block counter (8 bytes, big endian)),
               32 bytes per block: a stream cipher in counter mode with HMAC-SHA256 as its pseudorandom function
  tag        = HMAC-SHA256(k_mac, VERSION | KIND | expiry | nonce | ciphertext): encrypt then MAC. The tag is checked
               (in constant time) before the kind or the expiry is believed or a byte is decrypted, so a changed blob
               never decrypts.
  k_enc, k_mac: HMAC-SHA256 of the ticket secret (iris._ticket_secret, server only) under their own labels, so neither
               is the ticket key itself and no work ticket's signature can pass as a tag.
A fresh random nonce per seal: two seals of the same image share nothing. The blob travels as standard base64 text.
SEAL_TTL is long on purpose (48 h): a sealed iris opens only into a watermarked preview (/api/compose) or, with a
fresh work ticket, into an order draft, so the expiry bounds how long a page may keep one, not what it can unlock."""
import os, io, math, time, hmac, base64, hashlib, binascii
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from . import iris as L

VERSION = 1                  # the plain envelope, what seal() writes without an eye id
VERSION_V2 = 2               # seal v2: eye id and profile in the authenticated header
VERSIONS = (VERSION, VERSION_V2)
EYE_ID_BYTES = 8             # 16 hex digits
PROFILE_LEN_BYTES = 2
PROFILE_MAX = 8192           # a profile after zlib (api/_lib/styles/eye.py MAX_PROFILE_BYTES)
KIND_ORDER = 1               # "sealed": the exact enhance output, what an order's preview is made from
KIND_COMPOSE = 2             # "sealed_sizes": a smaller copy, only ever composed into a watermarked preview
KINDS_ALL = (KIND_ORDER, KIND_COMPOSE)
NONCE_BYTES = 16
TAG_BYTES = 32
HEAD_BYTES = 1 + 1 + 4 + NONCE_BYTES
SEAL_TTL = 48 * 3600
SEALED_B64_MAX = 1_700_000   # a sealed 1024 px enhance preview: api/order.py PREVIEW_B64_MAX (1.6 M) plus the envelope
_LABEL = b"snapeyes-preview-seal-v1:"

DISPLAY_SIDE = 800           # the display copy's side: what the slider shows, never the file an order is made from
DISPLAY_QUALITY = 85
DISPLAY_TILE = 1.0           # (before WP10) the watermark tile's scale as a share of the side; the display copy's words are now iris-anchored
                             # (display_image: the tile is drawn for the iris disc, ANCHOR_TILE disc diameters wide) and this is unused
DISPLAY_PAD = 1.12           # the crop padding every page sends (the iris radius is 1 / (2 pad) of the square): the display copy's disc
DISPLAY_ALPHA = L.WATERMARK_IRIS   # the tile's opacity times this: iris.py draws it at 40/255 over a whole artwork,
                             # and at that strength the words vanish into the fibres of an iris alone (140/255 here,
                             # as on the iris discs of an /api/compose preview)
DISPLAY_SHADOW = L.WATERMARK_IRIS_SHADOW   # a soft dark copy of the words (1 px down and right, 1 px blur) under the
                             # white ones, so they read on a pale blue iris as well as on a dark brown one
DISPLAY_MARK = b"snapeyes:display:v1"   # the display copy's JPEG comment
COMPOSE_SIDES = (768, 560)   # src/try/multi.ts composeSide: 3-4 eyes, 5-8 eyes
COMPOSE_QUALITY = 90         # as the page encoded those copies itself before (canvas JPEG 0.9)


class SealError(ValueError):
    """A sealed preview that is not one this server made, or that was changed on its way."""


class SealExpired(SealError):
    """A sealed preview older than SEAL_TTL."""


def _keys():
    s = L._ticket_secret()
    return hmac.digest(s, _LABEL + b"enc", "sha256"), hmac.digest(s, _LABEL + b"mac", "sha256")


def _xor(k_enc, nonce, data):
    n = len(data)
    if not n:
        return b""
    keyed = hmac.new(k_enc, digestmod=hashlib.sha256)   # the keyed state is copied per block: twice as fast as
    blocks = []                                         # hmac.digest() recomputing the key pads every time
    for i in range((n + 31) // 32):
        h = keyed.copy()
        h.update(nonce + i.to_bytes(8, "big"))
        blocks.append(h.digest())
    ks = b"".join(blocks)
    return (int.from_bytes(data, "big") ^ int.from_bytes(ks[:n], "big")).to_bytes(n, "big")


def eye_id_of(data):
    """The eye id of the clean 1024 px preview bytes: the first 16 hex digits of their sha256 (api/_lib/styles/eye.py eye_id_of is
    the same formula; the order draft stores it as preview.sha256[:16])."""
    return hashlib.sha256(bytes(data)).hexdigest()[:16]


def _profile_wire(profile, eye_id):
    """The wire bytes of a profile (an EyeProfile, or the bytes it made), checked against its eye."""
    if profile is None:
        return b""
    if isinstance(profile, (bytes, bytearray)):
        wire = bytes(profile)
    else:
        if getattr(profile, "eye_id", None) != eye_id:
            raise ValueError("the profile belongs to another eye")
        wire = profile.to_wire()
    if len(wire) > PROFILE_MAX:
        raise ValueError("profile too large")
    return wire


def seal(data, ttl=SEAL_TTL, now=None, kind=KIND_ORDER, eye_id=None, profile=None):
    """The bytes encrypted and authenticated with the server's key, as base64 text for a JSON reply. kind: KIND_ORDER
    (the enhance output an order may be made from) or KIND_COMPOSE (a copy only /api/compose opens). With an eye_id (16 hex) or a
    profile (an EyeProfile or its wire bytes) the blob is a version 2 seal that carries them in its authenticated header; without
    either it is the version 1 envelope, byte for byte as before."""
    if not isinstance(data, (bytes, bytearray)) or not data:
        raise ValueError("nothing to seal")
    if kind not in KINDS_ALL:
        raise ValueError("unknown seal kind")
    if eye_id is None and profile is not None and not isinstance(profile, (bytes, bytearray)):
        eye_id = getattr(profile, "eye_id", None)
    if eye_id is not None and not (isinstance(eye_id, str) and len(eye_id) == 2 * EYE_ID_BYTES
                                   and all(c in "0123456789abcdef" for c in eye_id)):
        raise ValueError("eye id: 16 hex digits")
    if eye_id is None and profile is not None:
        raise ValueError("a profile needs its eye id")
    exp = int(time.time() if now is None else now) + int(ttl)
    k_enc, k_mac = _keys()
    nonce = os.urandom(NONCE_BYTES)
    head = bytes([VERSION, kind]) + exp.to_bytes(4, "big") + nonce
    if eye_id is not None:
        wire = _profile_wire(profile, eye_id)
        head = bytes([VERSION_V2]) + head[1:] + bytes.fromhex(eye_id) + len(wire).to_bytes(PROFILE_LEN_BYTES, "big") + wire
    body = head + _xor(k_enc, nonce, bytes(data))
    return base64.b64encode(body + hmac.digest(k_mac, body, "sha256")).decode("ascii")


def _open(s, now, kinds):
    """(plaintext, header) of a sealed blob: header = {v, kind, eye_id (hex or None), profile (wire bytes, may be empty)}. Every
    refusal of unseal() is made here: the tag first, then the kind and the expiry."""
    if not isinstance(s, str) or not s:
        raise SealError("no sealed preview")
    if len(s) > SEALED_B64_MAX:
        raise SealError("sealed preview too large")
    try:
        raw = base64.b64decode(s, validate=True)
    except (binascii.Error, ValueError):
        raise SealError("sealed preview is not base64") from None
    if len(raw) < HEAD_BYTES + 1 + TAG_BYTES or raw[0] not in VERSIONS:
        raise SealError("not a sealed preview")
    body, tag = raw[:-TAG_BYTES], raw[-TAG_BYTES:]
    k_enc, k_mac = _keys()
    if not hmac.compare_digest(tag, hmac.digest(k_mac, body, "sha256")):
        raise SealError("sealed preview does not verify")
    if body[1] not in kinds:
        raise SealError("sealed preview of another kind")
    if int.from_bytes(body[2:6], "big") < (time.time() if now is None else now):
        raise SealExpired("sealed preview expired")
    v, pos, eye_id, wire = body[0], HEAD_BYTES, None, b""
    if v == VERSION_V2:
        if len(body) < pos + EYE_ID_BYTES + PROFILE_LEN_BYTES + 1:
            raise SealError("not a sealed preview")
        eye_id = body[pos:pos + EYE_ID_BYTES].hex()
        pos += EYE_ID_BYTES
        n = int.from_bytes(body[pos:pos + PROFILE_LEN_BYTES], "big")
        pos += PROFILE_LEN_BYTES
        if n > PROFILE_MAX or len(body) < pos + n + 1:
            raise SealError("not a sealed preview")
        wire, pos = body[pos:pos + n], pos + n
    plain = _xor(k_enc, body[6:HEAD_BYTES], body[pos:])
    if v == VERSION_V2 and body[1] == KIND_ORDER and eye_id_of(plain) != eye_id:
        raise SealError("sealed preview does not match its id")    # an order seal's id is the hash of its own bytes
    return plain, {"v": v, "kind": body[1], "eye_id": eye_id, "profile": wire}


def unseal(s, now=None, kinds=KINDS_ALL):
    """The bytes seal() was given. SealError for anything this server did not seal or that was changed (the tag is
    checked first) and for a seal of a kind the caller does not take (kinds), SealExpired for a blob past its
    expiry."""
    return _open(s, now, kinds)[0]


def unseal_full(s, now=None, kinds=KINDS_ALL):
    """(bytes, meta): unseal() and what the blob says about its eye. meta = {v (1 or 2), kind, eye_id, profile}. eye_id: 16 hex, from
    a version 2 header, or the sha256 prefix of the plaintext of a version 1 KIND_ORDER blob (its own bytes are the clean
    preview), else None (a version 1 compose copy: its bytes are not the preview's). profile: the sealed EyeProfile, or None
    (version 1, or a version 2 whose profile was not measured: the gate is unknown). Same refusals as unseal(); a profile that
    does not parse is a SealError too (the tag already vouches that this server wrote it, so this is a bug, not an attack)."""
    plain, h = _open(s, now, kinds)
    eye_id, prof = h["eye_id"], None
    if h["profile"]:
        from .styles import eye as EYE            # imported here: opening a seal must not load the profile code unless one is carried
        try:
            prof = EYE.EyeProfile.from_wire(h["profile"])
        except EYE.ProfileError:
            raise SealError("sealed preview carries an unreadable profile") from None
        if prof.eye_id != eye_id:
            raise SealError("sealed profile belongs to another eye")
    if eye_id is None and h["v"] == VERSION and h["kind"] == KIND_ORDER:
        eye_id = eye_id_of(plain)
    return plain, {"v": h["v"], "kind": h["kind"], "eye_id": eye_id, "profile": prof}


# (expired, unreadable) per page language
REFUSALS = {
    "en": ("This preview is too old. Please take the photo again.",
           "We could not read this preview. Please take the photo again."),
    "de": ("Diese Vorschau ist zu alt. Bitte fotografieren Sie Ihr Auge erneut.",
           "Wir konnten diese Vorschau nicht lesen. Bitte fotografieren Sie Ihr Auge erneut."),
    "lt": ("Ši peržiūra per sena. Nufotografuokite savo akį dar kartą.",
           "Nepavyko nuskaityti šios peržiūros. Nufotografuokite savo akį dar kartą."),
    "hu": ("Ez az előnézet túl régi. Kérjük, fotózd le újra a szemed.",
           "Ezt az előnézetet nem tudtuk beolvasni. Kérjük, fotózd le újra a szemed."),
}


def refusal(e, lang=None):
    """The customer's sentence for a sealed preview that was refused, in the page's language."""
    words = REFUSALS.get(lang or L.page_lang(), REFUSALS["en"])
    return words[0] if isinstance(e, SealExpired) else words[1]


# ----------------------------------------------------------------------------- the iris-anchored overlay (WP10)
# The overlay that lies on an iris is ONE picture, made once for a disc of ANCHOR_R0 px (the tile of words at the angle of the watermark,
# iris._watermark_layer, drawn ANCHOR_TILE disc diameters wide), and resampled into every view of the iris by that view's disc (centre and radius):
# the same words, the same angle, the same phase relative to the centre of the disc, scaled to its radius. A page can obtain many views of
# one iris (a batch of up to six tiles, the 1024 px preview, the 800 px display copy of the Reveal) whose iris pixels are identical (T1), so
# with the overlay in a different place on the iris in each of them, the aligned median of those views would remove it; with this overlay
# every view has it at the same place, and a median keeps it. The tile outside the discs stays the legacy one, anchored to the canvas
# (iris._watermark_layer): only the iris is the product. Where a layout turns an iris, the disc carries its rotation as a fourth number
# (cx, cy, r, rot in degrees, counter clockwise) and the overlay is turned with it, so that it stays the same in the iris's frame.
ANCHOR_R0 = 512               # the canonical overlay's disc radius, in its own pixels
ANCHOR_WINDOW = 1.15          # the overlay covers this many disc radii around the centre (half side): the disc, its feathered rim and a little more
ANCHOR_RMIN = 16.0            # a disc smaller than this (pixels) is not marked (the canvas tile stays); no layout draws one that small
ANCHOR_SIDE = 2 * int(round(ANCHOR_R0 * ANCHOR_WINDOW + 5.0 * ANCHOR_R0 / ANCHOR_RMIN))   # the canonical picture: the window plus the slack of the smallest disc
ANCHOR_TILE = L.WM_DISC       # the tile's scale as a multiple of the disc diameter (1.33, as the legacy multi-eye preview)
ANCHOR_RIM = 4.0              # the overlay fades over this many pixels at the disc's rim (iris._iris_mark)
_CANON = {}                   # words -> the canonical overlay (uint8, ANCHOR_SIDE square); at most one per language


def _canon(text):
    a = _CANON.get(text)
    if a is None:
        a = np.asarray(L._watermark_layer(ANCHOR_SIDE, ANCHOR_SIDE, ANCHOR_TILE * 2.0 * ANCHOR_R0, text).getchannel("A"), np.uint8)
        while len(_CANON) >= 4:                        # four languages: a bound, not a cache that can grow
            _CANON.pop(next(iter(_CANON)))
        _CANON[text] = a
    return a


def anchored_alpha(text, cx, cy, r, box, rot=0.0):
    """The canonical overlay as one disc's view sees it: float32 (h, w) of the tile's own opacity (0 to 1, the words at 40/255) over the integer pixel
    box (x0, y0, x1, y1) of the view, for a disc at (cx, cy) of radius r (pixel centres at +0.5), turned rot degrees counter clockwise. A resampling of
    the canonical picture with the box as the source region, so a disc centre between pixels moves the words by that fraction of a pixel."""
    canon = _canon(text)
    side = float(canon.shape[0])
    c0, k = side / 2.0, ANCHOR_R0 / float(r)
    x0, y0, x1, y1 = box
    src = Image.fromarray(canon, "L")
    if rot:
        src = src.rotate(float(rot), resample=Image.BICUBIC)
    sbox = tuple(min(max(v, 0.0), side) for v in (c0 + (x0 - cx) * k, c0 + (y0 - cy) * k, c0 + (x1 - cx) * k, c0 + (y1 - cy) * k))
    return np.asarray(src.resize((x1 - x0, y1 - y0), Image.LANCZOS, box=sbox), np.float32) / np.float32(255.0)


def _windows(W, H, discs):
    """[(cx, cy, r, rot, x0, y0, x1, y1)] of the discs the overlay can mark on a W x H canvas: finite numbers, a radius of at least ANCHOR_RMIN pixels and a
    window that reaches the canvas (a disc given as (cx, cy, r) or (cx, cy, r, rot) in canvas pixels). A disc that is not in this list is not marked."""
    wins = []
    for d in discs or ():
        try:
            cx, cy, r = float(d[0]), float(d[1]), float(d[2])
            rot = float(d[3]) if len(d) > 3 and d[3] else 0.0
        except (TypeError, ValueError, IndexError):
            continue
        if not (math.isfinite(cx) and math.isfinite(cy) and math.isfinite(rot) and math.isfinite(r) and r >= ANCHOR_RMIN):
            continue
        half = int(math.ceil(ANCHOR_WINDOW * r)) + 2
        x0, y0 = max(0, int(math.floor(cx - half))), max(0, int(math.floor(cy - half)))
        x1, y1 = min(int(W), int(math.ceil(cx + half))), min(int(H), int(math.ceil(cy + half)))
        if x1 > x0 and y1 > y0:
            wins.append((cx, cy, r, rot, x0, y0, x1, y1))
    return wins


def _cover(W, H):
    """Discs that tile a whole W x H canvas (their windows touch), for a picture whose engine reported fewer discs than it has eyes: drawn with the
    "window" weight they put the overlay on every pixel, at the iris strength. A fallback that fails strong: the picture is never left with the faint
    canvas tile alone (the legacy engine's mark), which is not enough protection for an iris."""
    u = float(min(W, H))
    r = 0.22 * u
    step = 2.0 * ANCHOR_WINDOW * r
    return [((i + 0.5) * step, (j + 0.5) * step, r) for j in range(int(math.ceil(H / step))) for i in range(int(math.ceil(W / step)))]


def _anchored(W, H, discs, text, mask="disc"):
    """(A, M, box) or None: the white alpha of the iris overlay (the tile's words WATERMARK_IRIS times as opaque, as iris._iris_mark) and the weight
    of the overlay against the canvas tile, as float32 (h, w) over box = (x0, y0, x1, y1), the union of the discs' windows inside the canvas. mask
    "disc": the weight is 1 inside the disc and fades to 0 over ANCHOR_RIM pixels at its rim (outside it the canvas tile is untouched); "window": 1
    over the whole window (the display copy, which is nothing but the iris). Where discs overlap the disc with the larger weight wins, the first on a tie."""
    wins = _windows(W, H, discs)
    if not wins:
        return None
    X0, Y0 = min(w[4] for w in wins), min(w[5] for w in wins)
    X1, Y1 = max(w[6] for w in wins), max(w[7] for w in wins)
    A = np.zeros((Y1 - Y0, X1 - X0), np.float32)
    M = np.zeros_like(A)
    for cx, cy, r, rot, x0, y0, x1, y1 in wins:
        want = np.minimum(np.float32(1.0), anchored_alpha(text, cx, cy, r, (x0, y0, x1, y1), rot) * np.float32(L.WATERMARK_IRIS))
        if mask == "window":
            m = np.ones_like(want)
        else:
            dy = (np.arange(y0, y1, dtype=np.float32) + np.float32(0.5 - cy))[:, None]
            dx = (np.arange(x0, x1, dtype=np.float32) + np.float32(0.5 - cx))[None, :]
            m = np.clip((np.float32(r + 2.0) - np.sqrt(dx * dx + dy * dy)) / np.float32(ANCHOR_RIM), 0, 1)
        sl = (slice(y0 - Y0, y1 - Y0), slice(x0 - X0, x1 - X0))
        better = m > M[sl]
        A[sl] = np.where(better, want, A[sl])
        M[sl] = np.maximum(M[sl], m)
    return A, M, (X0, Y0, X1, Y1)


def _paint(region, A, shade):
    """The words over a region (float32 (h, w, 3), 0 to 255): a soft dark copy of them (1 px down and right, 1 px blur, WATERMARK_IRIS_SHADOW of their
    opacity, shade being the opacity it is made from) under the white ones, as iris._iris_mark draws them."""
    sh = np.zeros_like(A)
    sh[1:, 1:] = shade[:-1, :-1] * np.float32(L.WATERMARK_IRIS_SHADOW)
    sh = np.asarray(Image.fromarray(np.round(sh * 255.0).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0)), np.float32) / np.float32(255.0)
    out = region * (np.float32(1.0) - sh[..., None])
    return out * (np.float32(1.0) - A[..., None]) + np.float32(255.0) * A[..., None]


def _badge(out, accent, u, lang=None, note=None):
    """The badge at the top centre (and the optional note under it), drawn as iris._watermark draws it, on the picture itself: a pill cut to its
    measured text and filled opaque first, so drawing it a second time over itself gives the same pixels."""
    badge = L.WATERMARK_TEXT.get(lang or L.page_lang(), L.WATERMARK_TEXT["en"])[1]
    W, H = out.size
    d = ImageDraw.Draw(out)
    fp = L._font("PlusJakartaSans.ttf", int(u * 0.016), "Bold")
    half = min(W / 2.0 - 2.0, d.textlength(badge, font=fp) / 2.0 + u * 0.022)
    d.rounded_rectangle((W / 2.0 - half, u * 0.03, W / 2.0 + half, u * 0.07), radius=int(u * 0.02), fill=(0, 0, 0, 200), outline=accent)
    d.text((W / 2, u * 0.05), badge, font=fp, fill=accent, anchor="mm")
    if note:
        fn, txt = L._font("PlusJakartaSans.ttf", int(u * 0.014), "Bold"), str(note).upper()
        hn = min(W / 2.0 - 2.0, d.textlength(txt, font=fn) / 2.0 + u * 0.016)
        d.rounded_rectangle((W / 2.0 - hn, u * 0.077, W / 2.0 + hn, u * 0.107), radius=int(u * 0.015), fill=(0, 0, 0, 200))
        d.text((W / 2, u * 0.092), txt, font=fn, fill=accent, anchor="mm")
    return out


def watermark(img, accent, discs, lang=None, note=None, n_eyes=None):
    """The free preview of a picture of the v3 engine: img (PIL RGB, the clean render) with the preview watermark, as a new image. Everything
    outside the discs is exactly iris._watermark's (the faint tile of words over the whole canvas, anchored to the canvas, and the badge); on each
    disc (cx, cy, r[, rot]: the visible iris disc in canvas pixels, pixel centres at +0.5) the canvas tile is replaced by the iris-anchored
    overlay at the strength of the display copy (see the module text). An engine never draws any of it: the paid file has none.
    n_eyes: how many irises the picture holds. When fewer discs than that can be marked (an engine that reported none, or one too few: a bug of
    that engine, never a customer's doing), the whole canvas gets the overlay at the iris strength instead of the faint canvas tile alone: a
    picture of an iris is never left with the legacy mark. None: no check (the legacy callers and the tests of the tile itself)."""
    W, H = img.size
    u = min(W, H)
    live = [d for d in (discs or ()) if len(d) >= 3]
    wins = _windows(W, H, live)                     # the discs the overlay can mark (a disc of a few pixels or one that is not a number is not one)
    dia = max((2.0 * w[2] for w in wins), default=float(u))
    base = L._watermark(img, accent, u, tile_u=min(float(u), L.WM_DISC * dia), note=note, lang=lang)
    mask = "disc"
    if n_eyes is not None and len(wins) < int(n_eyes):
        print(f"snapeyes watermark: {len(wins)} markable discs for {int(n_eyes)} eyes, the whole canvas is marked", flush=True)
        live, mask = _cover(W, H), "window"
    if not live:
        return base
    words = L.WATERMARK_TEXT.get(lang or L.page_lang(), L.WATERMARK_TEXT["en"])[0]
    got = _anchored(W, H, live, words, mask)
    if got is None:
        return base
    A, M, box = got
    painted = _paint(np.asarray(img.convert("RGB").crop(box), np.float32), A, A * M)
    cur = np.asarray(base.crop(box), np.float32)
    m = M[..., None]
    region = np.where(m > 0, np.round(cur * (np.float32(1.0) - m) + painted * m), cur)
    base.paste(Image.fromarray(np.clip(region, 0, 255).astype(np.uint8)), (box[0], box[1]))
    return _badge(base, accent, u, lang, note)


# ----------------------------------------------------------------------------- the display copy
def display_image(clean, lang=None, pad=DISPLAY_PAD):
    """The restored iris as the page shows it: DISPLAY_SIDE px with the iris-anchored overlay (words of WATERMARK_TEXT in lang, the requesting page's
    language when not given) over the whole square, iris included, at the strength of the discs of a preview, over a soft dark shadow. pad is the crop
    padding the iris was cut with (the disc has radius 1 / (2 pad) of the side, centred): the overlay is the one every tile and preview of that
    iris carries, in the same place on the iris."""
    side = DISPLAY_SIDE
    im = clean.convert("RGB")
    if im.size != (side, side):
        im = im.resize((side, side), Image.LANCZOS)
    words = L.WATERMARK_TEXT.get(lang or L.page_lang(), L.WATERMARK_TEXT["en"])[0]
    try:
        pad = float(pad)
        pad = pad if 1.0 <= pad <= 2.0 else DISPLAY_PAD
    except (TypeError, ValueError):
        pad = DISPLAY_PAD
    got = _anchored(side, side, [(side / 2.0, side / 2.0, side * L.iris_radius_frac(pad))], words, mask="window")
    if got is None:
        return im
    A, M, box = got
    painted = _paint(np.asarray(im.crop(box), np.float32), A, A)
    out = im.copy()
    out.paste(Image.fromarray(np.clip(np.round(painted), 0, 255).astype(np.uint8)), (box[0], box[1]))
    return out


def display_b64(clean, lang=None, pad=DISPLAY_PAD):
    buf = io.BytesIO()
    display_image(clean, lang, pad).save(buf, "JPEG", quality=DISPLAY_QUALITY, comment=DISPLAY_MARK)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def is_display(raw):
    """True for a display copy (DISPLAY_MARK in its JPEG comment), read from the header alone."""
    try:
        im = Image.open(io.BytesIO(raw))
        return im.format == "JPEG" and im.info.get("comment") == DISPLAY_MARK
    except Exception:  # noqa: not an image at all is not a display copy either
        return False


def is_display_b64(s):
    """is_display() of an image sent as base64 text (a data URL too, as iris.b64_to_pil takes it)."""
    if not isinstance(s, str) or not s:
        return False
    if "," in s[:64] and s.strip().startswith("data:"):
        s = s.split(",", 1)[1]
    try:
        return is_display(base64.b64decode(s))
    except (binascii.Error, ValueError):
        return False


def protect(clean_im, clean_bytes, lang=None, profile=None):
    """What /api/enhance hands the page for one restored iris: the display copy and the sealed clean originals.
    clean_bytes: the exact JPEG the page used to get (the order's preview); clean_im: the same image, decoded. All three seals carry
    the eye id (eye_id_of(clean_bytes)); profile (an EyeProfile of that very eye, measured by enhance when it had the time) rides in
    all three too. Without it the seals still carry the id and say that the profile was not measured."""
    eid = eye_id_of(clean_bytes)
    wire = _profile_wire(profile, eid) if profile is not None else b""
    wire = wire or None
    pad = getattr(profile, "pad", None) if profile is not None else None       # the display copy's overlay is anchored to the iris disc: its padding
    sizes = {}
    for s in COMPOSE_SIDES:
        buf = io.BytesIO()
        clean_im.convert("RGB").resize((s, s), Image.LANCZOS).save(buf, "JPEG", quality=COMPOSE_QUALITY)
        sizes[str(s)] = seal(buf.getvalue(), kind=KIND_COMPOSE, eye_id=eid, profile=wire)
    return {"image": display_b64(clean_im, lang, pad if isinstance(pad, float) else DISPLAY_PAD), "sealed": seal(clean_bytes, kind=KIND_ORDER, eye_id=eid, profile=wire),
            "sealed_sizes": sizes}
