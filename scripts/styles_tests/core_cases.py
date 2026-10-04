# -*- coding: utf-8 -*-
"""The golden cases of the engine core, written once and run twice: record_core_goldens.py runs them on the SCRATCH prototype (fx.core,
fx.layouts, singles_kit.draw_names: the code the owner-approved boards were made with) and writes the SHA-256 of every result into
data/core_goldens.json; test_engine_core.py runs the very same function on the ported modules (api/_lib/styles/core.py, layouts.py,
text.py) and compares. A port is verbatim when every hash is equal. numpy, Pillow and the fixtures of synth_iris only.

run_cases(C, LY, draw_names, fixtures) -> {case name: hex digest or text}
  C           a core module (fx.core or styles.core)          LY   a layouts module (fx.layouts or styles.layouts)
  draw_names  draw_names(img, frame, names, date, colour, log) of the scratch kit or of styles.text
  fixtures    {fixture name: PNG bytes of a synthetic iris}
"""
from __future__ import annotations

import hashlib
import json
import types

import numpy as np
from PIL import Image

IRIS_FIXTURES = ("blue_round", "dark_brown_round", "grey_round", "blue_lid")


def h(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def hs(s):
    return hashlib.sha256(str(s).encode("utf-8")).hexdigest()


def primitive_cases(C):
    out = {}
    rng = np.random.default_rng(5)
    a3 = rng.random((120, 160, 3)).astype(np.float32)
    a2 = rng.random((120, 160)).astype(np.float32)

    # randomness: every stream is PCG64 uniform doubles, so these hashes must never move
    r = C.Rand(123456789, "tag")
    out["rand.uniform"] = h(r.uniform(64))
    out["rand.normal"] = h(C.Rand(123456789, "n").normal(64))
    out["rand.exponential"] = h(C.Rand(123456789, "e").exponential(64, 2.0))
    out["rand.pareto"] = h(C.Rand(123456789, "p").pareto(64, 2.5))
    out["rand.gamma"] = h(C.Rand(123456789, "g").gamma(64, 2.5))
    out["rand.integers"] = h(C.Rand(123456789, "i").integers(64, 3, 41))
    out["seed_for"] = str(C.seed_for(b"abc", 2, "style", "layout"))

    # the float canvas helpers
    out["canvas"] = h(C.canvas(32, 24))
    out["radial_bg"] = h(C.radial_bg(160, 120, 80, 60, 70, "#0B0B0C", "#050505", 1.3))
    for sg in (1.5, 6.0, 25.0):
        out[f"blur.rgb.{sg}"] = h(C.blur(a3, sg))
    out["blur.gray.80"] = h(C.blur(a2, 80.0))
    out["box_reduce.4"] = h(C.box_reduce(a3, 4))
    out["upsample.4"] = h(C.upsample(C.box_reduce(a3, 4), 160, 120, 4))
    g = C.Grid(160, 120, 4)
    rho, th = g.polar(80.0, 60.0, 40.0, 1.15)
    out["grid.polar"] = h(np.stack([rho, th]))
    out["grid.up"] = h(g.up(np.ones((g.h, g.w), np.float32) * 0.5))
    out["work_factor"] = json.dumps([C.work_factor(x) for x in (1.0, 3.0, 12.0, 40.0, 400.0)])
    rho, th = C.polar(160, 120, 80.5, 60.5, 40.0, 1.15)
    out["polar.stretch"] = h(np.stack([rho, th]))
    rho, th = C.polar(160, 120, 80.5, 60.5, 40.0, 1.0, box=(10, 20, 90, 70))
    out["polar.box"] = h(np.stack([rho, th]))
    b = a3 * 1.8
    C.tone_map(b)
    out["tone_map"] = h(b)
    out["dither"] = h(C.dither_quantize(a3, 7, "d"))
    cp = a3.copy()
    C.screen(cp, a3, 0.5)
    C.add(cp, a3, 0.25)
    out["screen_add"] = h(cp)
    out["smoothstep"] = h(C.smoothstep(np.linspace(-0.5, 1.5, 33).astype(np.float32)))
    cp = a3.copy()
    C.fade_rows(cp, 20.0, 80.0, 0.25)
    out["fade_rows"] = h(cp)

    # particles and noise
    lay = np.zeros((120, 160, 3), np.float32)
    xs, ys = rng.random(300) * 160, rng.random(300) * 120
    sig = 0.4 + rng.random(300) * 4.0
    cols = rng.random((300, 3)).astype(np.float32)
    C.splat(lay, xs, ys, sig, cols, amp=0.7)
    out["splat"] = h(lay)
    lay = np.zeros((120, 160, 3), np.float32)
    C.sparkles(lay, xs[:6], ys[:6], 18.0, cols[:6], 0.9, angle=0.3)
    out["sparkles"] = h(lay)
    out["fbm1d"] = h(C.periodic_fbm1d(256, C.Rand(3, "f")))
    out["fbm_polar"] = h(C.fbm_polar(64, 32, C.Rand(3, "g")))
    out["value_noise2d"] = h(C.value_noise2d(160, 120, 6, C.Rand(3, "v")))
    out["particle_count"] = json.dumps([C.particle_count(400, 1024, 1024), C.particle_count(400, 3000, 1000)])

    # colour
    ring = rng.random((360, 3)).astype(np.float32) * 0.6 + 0.1
    out["colour_stats"] = json.dumps(C.colour_stats(ring), sort_keys=True)
    out["colour_class"] = C.colour_class(ring)
    out["effect_palette.own"] = h(C.effect_palette(ring, 1.6, 1.4, cls="own"))
    out["effect_palette.brown"] = h(C.effect_palette(ring, fallback={"dark_brown": {"lift": 1.8, "sat": 1.5, "toward": "#D98A3D", "t": 0.35}},
                                                     cls="dark_brown", hue_deg=12.0))
    out["effect_palette.grey"] = h(C.effect_palette(ring, fallback={"grey": ("#9FB4D0", 0.4)}, cls="grey"))
    out["palette_lut"] = h(C.palette_lut(ring))
    out["angular_lut"] = h(C.angular_lut(ring[:, 0]))
    thv = np.linspace(-3.14, 3.14, 500).astype(np.float32)
    out["angle_index"] = h(C.angle_index(thv))
    out["ring_at"] = h(C.ring_at(ring, thv))
    out["boost_mix_hue"] = h(np.stack([C.boost(ring), C.mix(ring, ring[::-1], 0.3), C.hue_shift(ring, 25.0)]))
    lab = np.stack(np.meshgrid(np.linspace(5, 95, 9), np.linspace(-60, 60, 9), np.linspace(-60, 60, 9)), -1).reshape(-1, 3)
    out["lab_roundtrip"] = h(C.lab_to_srgb(lab))
    out["lch"] = h(np.stack([np.asarray(v) for v in C.lch(ring)]))
    out["from_lch"] = h(C.from_lch(np.full(5, 40.0), np.full(5, 30.0), np.linspace(0, 300, 5)))
    out["rgb01"] = h(np.stack([C.rgb01("#C9B8A0"), C.rgb01((201, 184, 160)), C.rgb01((0.5, 0.25, 1.0))]))
    out["colour_distance"] = repr(round(C.colour_distance(ring[0], ring[100]), 9))
    return out


def iris_cases(C, fixtures):
    out = {}
    irises = []
    for name in IRIS_FIXTURES:
        ir = C.Iris(fixtures[name], name)
        irises.append(ir)
        out[f"{name}.digest"] = ir.digest.hex()[:16]
        out[f"{name}.ease"] = repr(round(float(ir.ease), 9))
        out[f"{name}.ring"] = h(ir.ring)
        out[f"{name}.stats"] = json.dumps(ir.stats, sort_keys=True)
        out[f"{name}.graded256"] = h(ir.graded(C.REF_SIDE))
        out[f"{name}.graded640"] = h(ir.graded(640))
        d = C.place_disc(ir, 384.0, 384.0, 150.0, 0)
        out[f"{name}.disc"] = json.dumps([d.x0, d.y0, d.cx, d.cy, d.R, d.Sd]) + ":" + h(d.g) + ":" + h(d.alpha)
        out[f"{name}.mini"] = h(mini_render(C, ir, d))
    out["design_seed"] = str(C.design_seed(irises, "demo", "single/1:1"))
    return out


def mini_render(C, iris, d, size=768):
    """A small effect drawn only with the core primitives: ground, ring-coloured motes, a glow, sparkles, tone map, dither, the iris last."""
    cv = C.canvas(size, size)
    cv[:] = C.radial_bg(size, size, d.cx, d.cy, 1.6 * d.R, "#0B0B0C", "#050505")
    seed = C.design_seed([iris], "demo", "single/1:1")
    rnd = C.Rand(seed, "motes")
    n = C.particle_count(500, size, size)
    th = rnd.uniform(n, 0.0, C.TWO_PI)
    rr = 1.04 + rnd.exponential(n, 0.30)
    xs, ys = C.at_polar(d, rr, th)
    pal = C.effect_palette(iris.ring)
    col = C.ring_at(pal, th)
    C.splat(cv, xs, ys, 0.0035 * size * (0.4 + rnd.uniform(n)), col, amp=0.8)
    glow = C.blur(cv, 0.02 * size)
    C.screen(cv, glow, 0.5)
    C.sparkles(cv, xs[:5], ys[:5], 0.03 * size, col[:5], 0.9)
    return C.finish(cv, [d], seed)


def layout_cases(LY):
    rows = []
    for fam, n, aspect, mode in LY.all_cases():
        lay = LY.place(fam, n, aspect, 1024, mode)
        LY.check(lay)
        cap = lay.caption
        rows.append([fam, n, aspect, mode, lay.W, lay.H, lay.S, [[round(s.cx, 3), round(s.cy, 3), round(s.r, 3)] for s in lay.slots],
                     [round(v, 3) if isinstance(v, float) else v for v in (cap.u, cap.top, cap.title_y, cap.names_y, cap.footer_y)],
                     [round(v, 3) for v in lay.box]])
    return {"layouts.count": str(len(rows)), "layouts.all": hs(json.dumps(rows))}


def text_cases(draw_names):
    out = {}
    frame = types.SimpleNamespace(W=1024, H=1024, S=1024, text_y=0.93 * 1024)
    for tag, names, date in (("names_date", "Anna & Max", "12.05.2026"), ("names_only", "Lina", ""), ("date_only", "", "2026"),
                             ("long", "Anna Maria Magdalena and Johann Sebastian", "12 May 2026")):
        img = Image.new("RGB", (1024, 1024), (4, 4, 6))
        log = draw_names(img, frame, names, date, "#C9B8A0", [])
        out[f"text.{tag}"] = h(np.asarray(img)) + ":" + json.dumps([[x["kind"], x["text"], x["px"], round(x["baseline"], 3)] for x in log])
    img = Image.new("RGB", (1024, 576), (4, 4, 6))
    f2 = types.SimpleNamespace(W=1024, H=576, S=576, text_y=0.80 * 576)
    log = draw_names(img, f2, "Anna", "2026", (201, 168, 106), [])
    out["text.landscape"] = h(np.asarray(img)) + ":" + str(len(log))
    return out


def run_cases(C, LY, draw_names, fixtures):
    out = {}
    out.update(primitive_cases(C))
    out.update(iris_cases(C, fixtures))
    out.update(layout_cases(LY))
    out.update(text_cases(draw_names))
    return out
