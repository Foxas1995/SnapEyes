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
iris.WATERMARK_IRIS times as strong on every iris disc (iris._watermark discs), the strength of the display copy here.

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
import os, io, time, hmac, base64, hashlib, binascii
from PIL import Image, ImageFilter
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
DISPLAY_TILE = 1.0           # the watermark tile's scale as a share of the side (iris.py's own scale for a square
                             # artwork): three rows of words cross the iris disc
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


# ----------------------------------------------------------------------------- the display copy
def display_image(clean, lang=None):
    """The restored iris as the page shows it: DISPLAY_SIDE px with the preview tile (iris._watermark_layer, the words
    of WATERMARK_TEXT in lang, the requesting page's language when not given) drawn across the whole square, iris
    included, at DISPLAY_ALPHA its artwork strength over a soft dark shadow."""
    side = DISPLAY_SIDE
    im = clean.convert("RGB")
    if im.size != (side, side):
        im = im.resize((side, side), Image.LANCZOS)
    words = L.WATERMARK_TEXT.get(lang or L.page_lang(), L.WATERMARK_TEXT["en"])[0]
    alpha = L._watermark_layer(side, side, side * DISPLAY_TILE, words).getchannel("A")
    alpha = alpha.point(lambda v: min(255, int(round(v * DISPLAY_ALPHA))))
    out = im.convert("RGBA")
    zero = Image.new("L", (side, side), 0)
    if DISPLAY_SHADOW:
        shade = Image.new("L", (side, side), 0)
        shade.paste(alpha.point(lambda v: int(round(v * DISPLAY_SHADOW))), (1, 1))
        out = Image.alpha_composite(out, Image.merge("RGBA", (zero, zero, zero, shade.filter(ImageFilter.GaussianBlur(1.0)))))
    white = Image.new("L", (side, side), 255)
    out = Image.alpha_composite(out, Image.merge("RGBA", (white, white, white, alpha)))
    return out.convert("RGB")


def display_b64(clean, lang=None):
    buf = io.BytesIO()
    display_image(clean, lang).save(buf, "JPEG", quality=DISPLAY_QUALITY, comment=DISPLAY_MARK)
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
    sizes = {}
    for s in COMPOSE_SIDES:
        buf = io.BytesIO()
        clean_im.convert("RGB").resize((s, s), Image.LANCZOS).save(buf, "JPEG", quality=COMPOSE_QUALITY)
        sizes[str(s)] = seal(buf.getvalue(), kind=KIND_COMPOSE, eye_id=eid, profile=wire)
    return {"image": display_b64(clean_im, lang), "sealed": seal(clean_bytes, kind=KIND_ORDER, eye_id=eid, profile=wire),
            "sealed_sizes": sizes}
