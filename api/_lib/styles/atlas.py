# -*- coding: utf-8 -*-
"""styles.atlas: the two sprite atlases the matter of the plate styles is drawn with. Built offline from the plate sheets (the FLAKE, SHARD and
DROPS sheets are not read at run time) and shipped once each in the bundle of the four rendering functions, api/_assets/atlas/:

  chips.npz   345 chips of the iris-coloured powder, 128 px each: lum and mask (uint8, n x 128 x 128) and meta (n x k floats). Powder Burst, the
              collision family and the universe looks draw their chips from it (the prototype kept four byte identical copies, one per family)
  drops.npz   139 droplets of the Splash and Elements styles, rgb (uint8, n x 128 x 128 x 3)

chips() returns a ChipsAtlas (lum and mask as float32 0..1 and a box-reduced mip per size, built on first use); drops() the uint8 array.
Each atlas is read once per process (two files, a few MB each as stored, 45 MB and 20 MB decoded as the engines hold them: the one cache a
warm instance keeps on purpose; the memory guard counts it in each design's peak). The files are checked against the sha256 of the baked
registry on first read: an atlas that is not the one the registry names raises AtlasUnavailable, nothing is drawn with another.
"""
from __future__ import annotations

import hashlib
import io
import os
import threading

import numpy as np

from .. import plates_registry as REG
from . import plates as P

ATLAS_DIR = os.path.join(P.ASSETS, "atlas")
_INFO = REG.PLATES_REGISTRY["atlas"]
_LOCK = threading.Lock()
_CHIPS = None
_DROPS = None


class AtlasUnavailable(RuntimeError):
    """The atlas file is not in this function's bundle or is not the file the registry names."""


def _load(key):
    info = _INFO[key]
    path = os.path.join(ATLAS_DIR, info["file"])
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        raise AtlasUnavailable(f"atlas {key}: not in this function's bundle") from None
    if len(data) != info["bytes"] or hashlib.sha256(data).hexdigest() != info["sha256"]:
        raise AtlasUnavailable(f"atlas {key}: not the file the registry names")
    return np.load(io.BytesIO(data))


class ChipsAtlas:
    """lum, mask: float32 0..1 (n, 128, 128); meta; n. mip(side): the atlas box-reduced to side x side (128, 64, 32, 16), built once. Also
    readable as a dict ("lum", "mask", "meta", "n", "mips"), the way the singles engine used it."""

    def __init__(self, z):
        self.lum = z["lum"].astype(np.float32) / 255.0
        self.mask = z["mask"].astype(np.float32) / 255.0
        self.meta = z["meta"]
        self.n = len(self.lum)
        self.mips = {}

    def mip(self, side):
        if side not in self.mips:
            k = 128 // side
            n = self.n
            self.mips[side] = (self.lum.reshape(n, side, k, side, k).mean((2, 4)).astype(np.float32),
                               self.mask.reshape(n, side, k, side, k).mean((2, 4)).astype(np.float32))
        return self.mips[side]

    def __getitem__(self, key):
        return getattr(self, key)


def chips():
    """The chips atlas (one instance per process)."""
    global _CHIPS
    if _CHIPS is None:
        with _LOCK:
            if _CHIPS is None:
                _CHIPS = ChipsAtlas(_load("chips"))
    return _CHIPS


def drops():
    """The droplet sprites: uint8 (n, 128, 128, 3)."""
    global _DROPS
    if _DROPS is None:
        with _LOCK:
            if _DROPS is None:
                _DROPS = _load("drops")["rgb"]
    return _DROPS


def clear():
    """Let go of both atlases (tests, and a caller that wants its memory back)."""
    global _CHIPS, _DROPS
    with _LOCK:
        _CHIPS = _DROPS = None


def status():
    """{ok, atlases: {key: {present, bytes}}}: are both files in the bundle with the recorded size? (stat only; the hash is checked on read.)"""
    out = {}
    for key, info in _INFO.items():
        try:
            out[key] = {"present": os.path.getsize(os.path.join(ATLAS_DIR, info["file"])) == info["bytes"], "bytes": info["bytes"]}
        except OSError:
            out[key] = {"present": False, "bytes": info["bytes"]}
    return {"ok": all(v["present"] for v in out.values()), "atlases": out}
