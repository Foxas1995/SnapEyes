# -*- coding: utf-8 -*-
"""The cases of the Reveal's server half (work package WP9): pairs of a crop and the restoration made from it, built from the synthetic irises
of synth_iris.py (a real eye is biometric data and is never committed). One module, two readers: record_reveal_goldens_scratch.py runs the
cases on the SCRATCH prototype (designs/presentation.py) and test_reveal.py runs the same cases on api/_lib/styles/reveal.py and compares.

A pair is (crop, restored): `restored` is the 1024 px synthetic restoration, `crop` is the deglared crop it was made from (at 400 px, blurred
two pixels: a phone's version of the same iris). The recipes break the pair on purpose in the ways the verdict has to tell apart:
  clean       a rigid copy: registration trusted, colour the same        ok
  shift       the crop shifted 3 px (0.0066 R) and 2 px: the registration corrects it, spread stays tiny         ok, shift near (-0.0066, -0.0043)
  warm        the crop's colour changed (R x 1.25, B x 0.75): the restored colour is no longer the photo's       withheld, colour (drift over 8)
  warm_mild   a mild change (R x 1.08, B x 0.92)       ok, drift under 6
  rot1        the restoration turned one degree: the halves of the ring disagree about the shift by more than 0.005 R     withheld, registration
  scale102    the restoration enlarged 2 percent: the same       withheld, registration
  flat        no structure at all: the gradients do not correlate        withheld, registration
Every recipe is deterministic (Pillow, numpy, no random number).
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter

import synth_iris as SI

CROP_SIDE = 400
BLUR = 2.0


def _crop_of(rest, blur=BLUR, side=CROP_SIDE):
    return rest.filter(ImageFilter.GaussianBlur(blur)).resize((side, side), Image.LANCZOS)


def _shift(im, dx, dy):
    return im.transform(im.size, Image.AFFINE, (1, 0, -dx, 0, 1, -dy), resample=Image.BICUBIC)


def _warm(im, gr, gb):
    a = np.asarray(im).astype(np.float32)
    a[..., 0] *= gr
    a[..., 2] *= gb
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def _scaled(im, side, crop):
    big = im.resize((side, side), Image.LANCZOS)
    return big.crop((crop, crop, crop + im.size[0], crop + im.size[1]))


def _pair(fixture, how):
    rest = SI.make(**SI.FIXTURES[fixture])
    if how == "clean":
        return _crop_of(rest), rest
    if how == "shift":
        return _crop_of(_shift(rest, 3, 2)), rest
    if how == "warm":
        return _crop_of(_warm(rest, 1.25, 0.75)), rest
    if how == "warm_mild":
        return _crop_of(_warm(rest, 1.08, 0.92)), rest
    if how == "rot1":
        return _crop_of(rest), rest.rotate(1, resample=Image.BICUBIC)
    if how == "scale102":
        return _crop_of(rest), _scaled(rest, 1044, 10)
    if how == "flat":
        flat = Image.new("RGB", (1024, 1024), (60, 60, 60))
        return _crop_of(flat), flat
    raise ValueError(how)


# key -> (fixture, recipe, what the verdict must be: (ok, code))
CASES = {
    "blue_clean": ("blue_round", "clean", (True, "ok")),
    "dark_brown_clean": ("dark_brown_round", "clean", (True, "ok")),
    "grey_clean": ("grey_round", "clean", (True, "ok")),
    "amber_slit_clean": ("amber_slit", "clean", (True, "ok")),
    "dark_brown_bar_clean": ("dark_brown_bar", "clean", (True, "ok")),
    "blue_lid_clean": ("blue_lid", "clean", (True, "ok")),
    "blue_shift": ("blue_round", "shift", (True, "ok")),
    "blue_warm": ("blue_round", "warm", (False, "colour")),
    "blue_warm_mild": ("blue_round", "warm_mild", (True, "ok")),
    "blue_rot1": ("blue_round", "rot1", (False, "registration")),
    "blue_scale102": ("blue_round", "scale102", (False, "registration")),
    "flat": ("blue_round", "flat", (False, "registration")),
}


def pair(key):
    """(crop, restored) of a case, as PIL RGB images."""
    fixture, how, _ = CASES[key]
    return _pair(fixture, how)
