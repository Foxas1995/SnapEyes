# -*- coding: utf-8 -*-
"""styles.plates: the plate library, read only. The plates are generated photographs of powder, crowns of liquid, flames, spirals and
star dust that the plate styles draw their matter from (the iris itself is always the customer's). This module is the loader and the
picker the engines call; everything it knows was decided offline and baked into api/_lib/plates_registry.py (scripts/bake_plates_registry.py):
nothing is fitted, scanned, measured or written at run time, because a function's folder is read-only and a warm instance renders for hours.

Where a plate lives
  1K file      in the bundle of the four rendering functions: api/_assets/plates/<family>/<file> (previews and the collision family read these)
  4K file      in private storage, plates/v1/<family>/<file>, for the plates an engine can fetch at a master: fetch_4k() reads the local cache
               first (/tmp/snapeyes_plates/<sha12><ext>, written under a temporary name and renamed, capped at 256 MB with the least recently
               used deleted; a hit is used only when its size and sha256 are the registry's), else the bucket, checks the sha256 of what came back against the registry, and decodes it. A missing object, a
               wrong size or a wrong hash raises PlateUnavailable: the engine never draws with another plate (the order is held for the owner)

The pick (the engines' own rule, the plate workflow's registry.pick ported without its curation half)
  a plate is chosen by min(candidates, key=sha256(seed | family | plate id)): deterministic, the same in a preview and in the master
  a library is APPEND-ONLY: every plate has since (the plates version it arrived in) and until (0, or the first version that ignores it), and
  every pick takes the version of the spec (pv), so a plate added later can never change the picture of an older order, and a retired plate still
  answers an old version. A plate that is not usable (the soft spirals, the v2 flames, ...) has a record and no file and is never picked.

The surface the ported engines use (the same names the prototype's registry had): plates(), pick(), pick_n(), Pick, Plate (image, side, void,
void_diam, strong_angle, strength, place), MAX_UPSCALE, WEAK_STRENGTH, ResolutionError, NoPlate. Module state is bounded: two decoded 1K
plates, two decoded 4K plates, one record table.
"""
from __future__ import annotations

import hashlib
import io
import math
import os
import tempfile
import threading
import uuid

import numpy as np
from PIL import Image, ImageOps

from .. import plates_registry as REG
from .. import styles_registry as SR
from .core import BoundedCache

MAX_UPSCALE = 1.1
WEAK_STRENGTH = 0.08                 # below this the strong side is noise: the plate is treated as direction-free
FADE_DEFAULT = 0.035                 # soft border of a placed plate, share of the plate side
STORAGE_PREFIX = "plates/v1"
GET_MAX_BYTES = 16 << 20             # the largest 4K plate (a PNG of 8.5 MB) with room
CACHE_CAP_BYTES = 256 << 20
CACHE_NAME = "snapeyes_plates"

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "_assets")
BUNDLE = os.path.join(ASSETS, "plates")

_TABLE = REG.PLATES_REGISTRY["plates"]
_FAMILIES = REG.PLATES_REGISTRY["families"]
_IMG1 = BoundedCache(2)
_IMG4 = BoundedCache(2)
_io_lock = threading.Lock()


class ResolutionError(RuntimeError):
    """The plate would have to be enlarged more than MAX_UPSCALE at its largest file."""


class NoPlate(LookupError):
    """No plate matches the request (at this plates version)."""


class PlateUnavailable(RuntimeError):
    """A plate the render needs is not there or is not the plate the registry names: why is missing (no object, or no bundled file), size,
    sha256, no_4k (the registry has no 4K file for it). The engine does not substitute another plate: the caller holds the order."""

    def __init__(self, plate_id, why, detail=""):
        super().__init__(f"plate {plate_id}: {why}" + (f" ({detail})" if detail else ""))
        self.plate_id, self.why = plate_id, why


# ----------------------------------------------------------------------------- the registry
def known(plate_id):
    return plate_id in _TABLE


def record(plate_id):
    return _TABLE[plate_id]


def family_ids():
    return tuple(_FAMILIES)


def visible(rec, pv=None):
    """Is this plate one a spec of plates version pv may pick? Usable, arrived by then, not retired by then."""
    pv = SR.PLATES_VERSION if pv is None else int(pv)
    return bool(rec["usable"]) and rec["since"] <= pv and (not rec["until"] or pv < rec["until"])


def families(pv=None):
    """{family: number of plates a spec of version pv may pick}."""
    out = {}
    for rec in _TABLE.values():
        if visible(rec, pv):
            out[rec["family"]] = out.get(rec["family"], 0) + 1
    return out


def ids(family=None, pv=None):
    return tuple(i for i, r in _TABLE.items() if (family is None or r["family"] == family) and visible(r, pv))


def storage_path(plate_id):
    """The private-storage object of a plate's 4K file."""
    rec = _TABLE[plate_id]
    return f"{STORAGE_PREFIX}/{rec['family']}/{rec['k4']['file']}"


def bundle_path(plate_id):
    rec = _TABLE[plate_id]
    return os.path.join(BUNDLE, rec["family"], rec["k1"]["file"])


def needed(plate_ids):
    """What a plan must know about the 4K plates it will fetch (the plan's plates_needed): [{id, family, path, sha256, bytes}] of those that
    have a 4K file, in the order given. Checkout verifies each exists in storage before the customer pays."""
    out = []
    for pid in plate_ids:
        rec = _TABLE[pid]
        if rec["k4"]:
            out.append({"id": pid, "family": rec["family"], "path": storage_path(pid), "sha256": rec["k4"]["sha256"], "bytes": rec["k4"]["bytes"]})
    return out


def missing_in_storage(plate_ids, store=None):
    """The ids among those given whose 4K object is not in storage (store.exists on each: the object itself, never a listing)."""
    if store is None:
        from .. import store as _store
        store = _store
    return [p["id"] for p in needed(plate_ids) if not store.exists(p["path"])]


# ----------------------------------------------------------------------------- reading the files
def _mode(rec):
    return "L" if rec["mono"] else "RGB"


def load_1k(plate_id):
    """The 1K plate from the bundle: a PIL image ('L' for a mono plate, 'RGB' for a colour one), the last two kept. PlateUnavailable when
    the bundle has no such file (a function that excludes the plates, or a plate that is not usable)."""
    got = _IMG1.get(plate_id)
    if got is not None:
        return got
    rec = _TABLE.get(plate_id)
    if rec is None or not rec["k1"]:
        raise PlateUnavailable(plate_id, "missing", "no 1K file in the registry")
    path = bundle_path(plate_id)
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        raise PlateUnavailable(plate_id, "missing", "not in this function's bundle") from None
    if len(data) != rec["k1"]["bytes"]:
        raise PlateUnavailable(plate_id, "size", "the bundled file is not the one the registry names")
    im = Image.open(io.BytesIO(data))
    im.load()
    return _IMG1.put(plate_id, im.convert(_mode(rec)))


def cache_dir():
    d = os.environ.get("STYLE_PLATE_CACHE", "").strip()
    return d or os.path.join(tempfile.gettempdir(), CACHE_NAME)


def _cache_cap():
    try:
        mb = float(os.environ.get("STYLE_PLATE_CACHE_MB", "").strip())
        return int(min(max(mb, 8.0), 4096.0) * (1 << 20))
    except ValueError:
        return CACHE_CAP_BYTES


def _cache_file(rec):
    k4 = rec["k4"]
    return os.path.join(cache_dir(), k4["sha256"][:12] + os.path.splitext(k4["file"])[1])


def _evict(keep, cap):
    """Least recently used files out of the cache folder until it holds at most cap bytes (the file just written stays)."""
    try:
        d = cache_dir()
        rows = []
        for n in os.listdir(d):
            p = os.path.join(d, n)
            try:
                st = os.stat(p)
            except OSError:
                continue
            if n.endswith(".part"):
                continue
            rows.append((st.st_mtime, p, st.st_size))
        total = sum(r[2] for r in rows)
        for _mt, p, sz in sorted(rows):
            if total <= cap:
                break
            if p == keep:
                continue
            try:
                os.remove(p)
                total -= sz
            except OSError:
                pass
    except OSError:
        pass


def _read_4k(plate_id, rec):
    """The bytes of a 4K file: the local cache when it holds the right bytes (size and sha256, so a file that was cut, edited or damaged on
    the disk is never drawn from; hashing 8 MB takes a few milliseconds), else the bucket (sha256 checked) and then the cache."""
    k4 = rec["k4"]
    path = _cache_file(rec)
    try:
        if os.path.getsize(path) == k4["bytes"]:
            with open(path, "rb") as f:
                data = f.read()
            if len(data) == k4["bytes"] and hashlib.sha256(data).hexdigest() == k4["sha256"]:
                try:
                    os.utime(path, None)                             # recently used
                except OSError:
                    pass
                return data
    except OSError:
        pass
    from .. import store
    data = store.get(storage_path(plate_id), max_bytes=GET_MAX_BYTES)   # a StorageError stays: the step's busy path retries it
    if data is None:
        raise PlateUnavailable(plate_id, "missing", "no such object in storage")
    if len(data) != k4["bytes"]:
        raise PlateUnavailable(plate_id, "size", f"{len(data)} bytes, the registry says {k4['bytes']}")
    if hashlib.sha256(data).hexdigest() != k4["sha256"]:
        raise PlateUnavailable(plate_id, "sha256", "the object is not the plate the registry names")
    tmp = f"{path}.{uuid.uuid4().hex}.part"
    try:                                                              # atomic: a temporary name, then a rename (two writers cannot tear a file)
        os.makedirs(cache_dir(), exist_ok=True)
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
        _evict(path, _cache_cap())
    except OSError:
        pass                                                          # a read-only or full /tmp, or (Windows) a file another writer has open: no cache write, the plate is still good
    finally:
        try:
            os.remove(tmp)                                            # our temporary file is never left behind (after a rename it is already gone)
        except OSError:
            pass
    return data


def fetch_4k(plate_id):
    """The 4K plate: cache, else storage; decoded ('L' or 'RGB'), the last two kept. PlateUnavailable for a missing, short or wrong object
    (never another plate), no_4k for a plate the registry holds no 4K file of."""
    got = _IMG4.get(plate_id)
    if got is not None:
        return got
    rec = _TABLE.get(plate_id)
    if rec is None or not rec["k4"]:
        raise PlateUnavailable(plate_id, "no_4k", "the registry has no 4K file for it")
    data = _read_4k(plate_id, rec)
    im = Image.open(io.BytesIO(data))
    im.load()
    return _IMG4.put(plate_id, im.convert(_mode(rec)))


def clear_memory():
    _IMG1.clear()
    _IMG4.clear()


# ----------------------------------------------------------------------------- Plate, Pick: the surface of the prototype's registry
def _seed_int(seed, family, salt):
    return int.from_bytes(hashlib.sha256(f"{seed}|{family}|{salt}".encode("utf-8")).digest()[:8], "big")


def _wrap(a):
    return (a + 180.0) % 360.0 - 180.0


def _match(rec, where):
    for k, v in (where or {}).items():
        allowed = [str(x) for x in (v if isinstance(v, (list, tuple, set)) else [v])]
        if str((rec.get("variables") or {}).get(k, rec.get(k))) not in allowed:
            return False
    return True


class Plate:
    """One usable plate. rec is its record of plates_registry.py."""

    def __init__(self, plate_id):
        rec = _TABLE[plate_id]
        self.rec = rec
        self.id = plate_id
        self.family = rec["family"]
        self.mono = bool(rec["mono"])
        self.variables = rec.get("variables") or {}
        v = rec.get("void")
        self.void = (v[0], v[1], v[2]) if v else None
        self.void_diam = rec.get("void_diam")
        self.strong_angle = rec.get("strong_angle")
        self.strength = rec.get("strength", 0.0)
        self.reach = None                                  # the per-angle reach was a plate QA measurement: not read at run time
        self.score = rec.get("score")

    def __repr__(self):
        return f"Plate({self.id}, void {self.void_diam}, strong {self.strong_angle} / {self.strength})"

    def has_4k(self):
        return bool(self.rec["k4"])

    def image(self, lod="4k"):
        """PIL image of the LOD ('L' for mono plates, 'RGB' for colour plates): 1k from the bundle, 4k from the cache or storage."""
        return load_1k(self.id) if str(lod).lower() == "1k" else fetch_4k(self.id)

    def side(self, lod):
        return self.rec["k4" if str(lod).lower() == "4k" else "k1"].get("px") or (4096 if str(lod).lower() == "4k" else 1024)

    def max_R_px(self, lod="4k"):
        """Largest void radius (px) this plate can be placed at without enlarging its LOD more than MAX_UPSCALE."""
        return MAX_UPSCALE * self.void[2] * self.side(lod)

    def place(self, W, H, cx, cy, R, rotation_deg=0.0, mirror=False, lod="auto", edge_fade=FADE_DEFAULT, strict=True, r_scale=1.0):
        """Register the plate on a W x H canvas: the plate's fitted void circle lands on the circle (cx, cy, R * r_scale) px (pixel-centre
        continuous coordinates). rotation_deg: counter-clockwise on screen about the void centre (after mirror). edge_fade: the outer share of
        the plate side fades to black so a plate edge inside the canvas never shows. Returns (arr, info): arr float32 0..1, (H, W) for mono
        plates or (H, W, 3); info {lod, scale, upscale, src_px, rotation_deg, mirror}. A plate without a 4K file is placed from its 1K file
        only (a ResolutionError when that would enlarge it too much)."""
        if self.void is None:
            raise ValueError(f"{self.id} has no void (a sprite sheet)")
        R = float(R) * float(r_scale)
        vcx, vcy, vr = self.void
        lods = ["1k", "4k"] if str(lod).lower() == "auto" else [str(lod).lower()]
        if "4k" in lods and not self.has_4k():
            lods = [x for x in lods if x != "4k"] or ["1k"]
        chosen, s = None, None
        for l in lods:
            side = self.side(l)
            s_l = R / (vr * side)                                  # canvas px per plate px
            if s_l <= MAX_UPSCALE or l == lods[-1]:
                chosen, s = l, s_l
                break
        if s > MAX_UPSCALE + 1e-9 and strict:
            raise ResolutionError(f"{self.id}: void radius {R:.0f} px needs x{s:.2f} of the {chosen} plate (limit x{MAX_UPSCALE}); "
                                  f"largest R for this plate is {self.max_R_px(chosen):.0f} px")
        im = self.image(chosen)
        side = im.size[0]
        cx_s, cy_s = vcx * side, vcy * side
        if mirror:
            im = ImageOps.mirror(im)
            cx_s = side - cx_s
        k = 1
        if s < 0.7:                                                # shrinking a lot: box-reduce first, then resample
            k = max(2, int(round(0.9 / s)))
            while side % k:
                k -= 1
            if k > 1:
                im = im.reduce(k)
                side //= k
                cx_s, cy_s, s = cx_s / k, cy_s / k, s * k
        if edge_fade and edge_fade > 0:
            a = np.asarray(im)
            ramp = np.clip(np.minimum(np.arange(side) + 0.5, side - np.arange(side) - 0.5) / (edge_fade * side), 0, 1)
            ramp = (ramp * ramp * (3 - 2 * ramp)).astype(np.float32)
            m = ramp[:, None] * ramp[None, :]
            a = (a * (m if a.ndim == 2 else m[..., None]) + 0.5).astype(np.uint8)
            im = Image.fromarray(a)
        th = math.radians(rotation_deg)
        c, sn = math.cos(th), math.sin(th)
        a_, b_ = c / s, -sn / s
        d_, e_ = sn / s, c / s
        c0 = cx_s - (a_ * cx + b_ * cy)
        f0 = cy_s - (d_ * cx + e_ * cy)
        out = im.transform((int(W), int(H)), Image.AFFINE, (a_, b_, c0, d_, e_, f0), resample=Image.BICUBIC, fillcolor=0 if im.mode == "L" else (0, 0, 0))
        arr = np.asarray(out, np.float32) / 255.0
        return arr, {"lod": chosen, "scale": s / k if k > 1 else s, "upscale": max(1.0, s / k if k > 1 else s), "src_px": im.size[0] * k,
                     "rotation_deg": rotation_deg, "mirror": bool(mirror)}


class Pick:
    """The result of pick(): a plate plus how to orient it. place() forwards rotation and mirror."""

    def __init__(self, plate, rotation_deg, mirror, weak_direction, warning=""):
        self.plate, self.rotation_deg, self.mirror = plate, float(rotation_deg), bool(mirror)
        self.weak_direction, self.warning = bool(weak_direction), warning

    @property
    def strong_angle(self):
        """Screen angle of the placed plate's strong side (None for direction-free plates)."""
        if self.plate.strong_angle is None or self.weak_direction:
            return None
        a = 180.0 - self.plate.strong_angle if self.mirror else self.plate.strong_angle
        return (a + self.rotation_deg) % 360.0

    def place(self, W, H, cx, cy, R, **kw):
        kw.setdefault("rotation_deg", self.rotation_deg)
        kw.setdefault("mirror", self.mirror)
        return self.plate.place(W, H, cx, cy, R, **kw)

    def __repr__(self):
        return f"Pick({self.plate.id}, rot {self.rotation_deg:.1f}, mirror {self.mirror}, strong {self.strong_angle})"


def plates(family, pv=None, **where):
    """The plates of a family a spec of version pv may pick, filtered by variables (a value or a list of values), best score first."""
    out = [Plate(i) for i, r in _TABLE.items() if r["family"] == family and visible(r, pv) and _match(r, where)]
    out.sort(key=lambda p: (-(p.score or 0), p.id))
    return out


def _orient(plate, wanted, allow_mirror):
    """(rotation, mirror) with the smallest |rotation| that puts the plate's strong side at `wanted`."""
    a = plate.strong_angle
    best = (_wrap(wanted - a), False)
    if allow_mirror:
        m = (_wrap(wanted - (180.0 - a)), True)
        if abs(m[0]) < abs(best[0]):
            best = m
    return best


def pick(family, seed, wanted_strong_angle=None, *, exclude=(), max_rotation=45.0, allow_mirror=True, min_strength=0.0, salt="", pv=None,
         **where):
    """Deterministic choice of one plate. seed: any int, str or bytes (hashed with sha256, never Python hash()). pv: the plates version of the
    spec: plates that arrived later, or were retired by then, are not candidates. wanted_strong_angle: screen degrees (0 = right, 90 = up)
    where the plate's strong side must point; the plate needing the smallest turn wins among those within max_rotation (ties broken by the
    seeded hash). Direction-free plates (strength < WEAK_STRENGTH) are taken as they are. **where filters by variables, e.g.
    liquid="cognac", strong=["right", "up_right"]. Raises NoPlate when nothing matches."""
    ex = set(exclude)
    cands = [p for p in plates(family, pv, **where) if p.id not in ex]
    if min_strength:
        cands = [p for p in cands if p.strength >= min_strength or p.strength < WEAK_STRENGTH]
    if not cands:
        raise NoPlate(f"no plate for {family} {where}")
    key = lambda p: _seed_int(seed, family, salt + p.id)
    if wanted_strong_angle is None:
        p = min(cands, key=key)
        return Pick(p, 0.0, False, p.strength < WEAK_STRENGTH)
    scored = []
    for p in cands:
        if p.strength < WEAK_STRENGTH or p.strong_angle is None:
            scored.append((0.0, 0.0, False, True, p))
        else:
            rot, mir = _orient(p, wanted_strong_angle, allow_mirror)
            scored.append((abs(rot), rot, mir, False, p))
    within = [t for t in scored if t[0] <= max_rotation]
    warn = ""
    if not within:
        scored.sort(key=lambda t: t[0])
        within = scored[:3]
        warn = f"no {family} plate within {max_rotation:.0f} deg of {wanted_strong_angle:.0f}: turning {within[0][0]:.0f} deg"
    _, rot, mir, weak, p = min(within, key=lambda t: key(t[4]))
    return Pick(p, rot, mir, weak, warn)


def pick_n(family, seed, n, wanted_angles=None, *, max_rotation=45.0, allow_mirror=True, repeat_ok=True, pv=None, **where):
    """n DISTINCT plates (a plate never appears twice in one artwork). wanted_angles: a list of n angles or None. When n is more than the
    plates, they repeat with a different orientation (mirror flipped) and Pick.warning says so, unless repeat_ok=False (NoPlate)."""
    out, used = [], []
    for i in range(n):
        ang = None if wanted_angles is None else wanted_angles[i]
        try:
            pk = pick(family, seed, ang, exclude=used, max_rotation=max_rotation, allow_mirror=allow_mirror, salt=f"#{i}|", pv=pv, **where)
        except NoPlate:
            if not repeat_ok or not used:
                raise
            pk = pick(family, seed, ang, max_rotation=180.0, allow_mirror=True, salt=f"#{i}|", pv=pv, **where)
            pk.mirror = not pk.mirror
            pk.warning = (pk.warning + " ") + "plate repeated (n exceeds the plates)"
        used.append(pk.plate.id)
        out.append(pk)
    return out


# ----------------------------------------------------------------------------- what is where (health, the admin page, the build)
def bundle_status(deep=False):
    """{ok, families: {family: {usable, present, bytes}}, missing: [ids]}: does the bundle hold every usable plate's 1K file with the recorded
    size? deep=True also hashes each file (the test and the admin page do; a health probe only stats)."""
    fams, missing = {}, []
    for pid, rec in _TABLE.items():
        if not rec["usable"]:
            continue
        f = fams.setdefault(rec["family"], {"usable": 0, "present": 0, "bytes": 0})
        f["usable"] += 1
        path = bundle_path(pid)
        try:
            ok = os.path.getsize(path) == rec["k1"]["bytes"]
            if ok and deep:
                with open(path, "rb") as fh:
                    ok = hashlib.sha256(fh.read()).hexdigest() == rec["k1"]["sha256"]
        except OSError:
            ok = False
        if ok:
            f["present"] += 1
            f["bytes"] += rec["k1"]["bytes"]
        else:
            missing.append(pid)
    return {"ok": not missing, "families": fams, "missing": missing}


def storage_ids(families=None):
    """The plates that have a 4K file in the registry, optionally of some families."""
    return tuple(i for i, r in _TABLE.items() if r["usable"] and r["k4"] and (families is None or r["family"] in families))


def storage_status(families=None, store=None, deep=True):
    """{ok, checked, present, missing, sample, why}: is private storage reachable and does it hold the 4K plates (of some families)? exists() on every
    one (the object itself); with deep, one sample is downloaded and hashed. Nothing is written. The plates are expected only once a style that
    fetches them is at preview or above: with nothing expected the answer is ok with checked 0."""
    if store is None:
        from .. import store as _store
        store = _store
    ids_ = storage_ids(families)
    if not ids_:
        return {"ok": True, "checked": 0, "present": 0, "missing": [], "sample": None, "why": "nothing expected"}
    if not store.configured():
        return {"ok": False, "checked": 0, "present": 0, "missing": list(ids_), "sample": None, "why": "storage not configured"}
    present, missing = 0, []
    try:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=8) as pool:                 # one existence request per plate: eight at a time
            for pid, there in pool.map(lambda i: (i, store.exists(storage_path(i))), ids_):
                if there:
                    present += 1
                else:
                    missing.append(pid)
        sample = None
        if deep and present:
            pid = next(i for i in ids_ if i not in missing)
            data = store.get(storage_path(pid), max_bytes=GET_MAX_BYTES)
            sample = {"id": pid, "ok": data is not None and hashlib.sha256(data).hexdigest() == _TABLE[pid]["k4"]["sha256"]}
    except Exception as e:  # noqa: BLE001  a status probe never raises
        return {"ok": False, "checked": present + len(missing), "present": present, "missing": missing, "sample": None,
                "why": f"storage error: {type(e).__name__}"}
    ok = not missing and (sample is None or sample["ok"])
    return {"ok": ok, "checked": len(ids_), "present": present, "missing": missing, "sample": sample, "why": "" if ok else "missing or wrong plates"}


# ----------------------------------------------------------------------------- the health probe (api/health.py)
def expected_families():
    """The plate families a style that customers can see (ceiling preview or live) reads, from the registries (the literal ceiling: no storage
    read here). Empty while every v3 style is in the laboratory or planned: then nothing is expected of the bundle or of storage."""
    from .. import catalogue as CT
    out = set()
    for sid, e in CT.ENGINE.items():
        if not e["engine"] or e["engine"].get("module") == "legacy" or not CT._built(sid):
            continue
        lo, hi = CT.eyes_range(sid)
        if any(CT.ceiling(sid, n) in ("preview", "live") for n in range(lo, hi + 1)):
            out.update(e["plates"])
    return out


def health(store=None):
    """{styles, plates_4k}: two booleans and nothing else, for the public health endpoint.
    styles     the style registry reads (its hash is made), the baked library is the plates version the registry names, and every plate family
               and atlas an engine entry names is in the baked library. The health function does not carry the plates (the seven functions
               that never render exclude them: scripts/check_styles.mjs item 10), so whether the FILES are in the bundle of compose,
               master_compose and order is the build's check (item 8) and the admin action plates_status, which runs in a rendering function.
    plates_4k  storage is reachable and holds one sample of the 4K plates the visible styles fetch (one existence request; the hash of a downloaded
               sample is plates_status's). True with no request at all while no visible style fetches a 4K plate."""
    try:
        from .. import catalogue as CT
        CT.registry_hash()
        ok_styles = REG.PLATES_VERSION == SR.PLATES_VERSION
        for e in CT.ENGINE.values():
            ok_styles = ok_styles and all(f in _FAMILIES for f in e["plates"]) and all(a in REG.PLATES_REGISTRY["atlas"] for a in e["atlas"])
        fams = [f for f in expected_families() if _FAMILIES.get(f, {}).get("store4k")]
    except Exception:  # noqa: BLE001  a probe never raises
        return {"styles": False, "plates_4k": False}
    if not fams:
        return {"styles": bool(ok_styles), "plates_4k": True}
    try:
        if store is None:
            from .. import store as _store
            store = _store
        sample = sorted(storage_ids(fams))[0]
        ok4 = bool(store.configured() and store.exists(storage_path(sample)))
    except Exception:  # noqa: BLE001
        ok4 = False
    return {"styles": bool(ok_styles), "plates_4k": ok4}
