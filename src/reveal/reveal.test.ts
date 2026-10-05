// node --test src/reveal/reveal.test.ts   (scripts/run_ts_tests.mjs runs it with the other page tests)
// I18, the page half of what /api/enhance hands over (work package WP9): the server's "reveal" field is read defensively, the three things the page
// can show for an eye (the cut, the strip without the cut, the plain slider) follow from it, the p09f case is withheld, the frame built from the client
// crop (the way back from Stripe's page, where the wide frame is gone) is the tight one, and reduced motion has no motion at all.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { DRIFT_FAIL, PUPIL_CUT, SNAP, parseReveal, planFrame, revealGeometry, revealView, snapCut, stripFadeMs, sweepFor, tightFit, withheldByColour, type Aspect, type Fit } from './revealMath.ts';

interface Vec { eye: string; aspect: Aspect; fit: Fit; params: Record<string, unknown>; expect: ReturnType<typeof revealGeometry> }
const vectors: Vec[] = JSON.parse(readFileSync(new URL('./vectors.json', import.meta.url), 'utf8'));
const square = vectors.filter((v) => v.aspect[0] === v.aspect[1]);

// what api/_lib/styles/reveal.py wire() sends for a clean eye (scripts/styles_tests/data/reveal_goldens.json, case blue_clean)
const WIRE = { pupil: [0.0005, 0.0001], rho: 0.2635, cls: 'round', shift: [0.0, 0.0], edge: [0.95, 1.0252], ok: true, soft: false, drift: 0.3, lid: 0.0 };

test('parseReveal reads the server wire dict and gives back the numbers as typed values', () => {
  const r = parseReveal(JSON.parse(JSON.stringify(WIRE)));
  assert.ok(r);
  assert.deepEqual([r.pupil, r.shift, r.edge, r.ok, r.rho, r.cls, r.soft, r.drift, r.lid], [[0.0005, 0.0001], [0, 0], [0.95, 1.0252], true, 0.2635, 'round', false, 0.3, 0]);
  assert.equal(r.ia, undefined);
  assert.equal(parseReveal({ ...WIRE, ia: 1.4 })?.ia, 1.4);
});

test('parseReveal refuses anything that is not what the server sends: the page then keeps the plain slider', () => {
  for (const bad of [null, undefined, 'x', 3, [], {}, { ...WIRE, ok: 'yes' }, { ...WIRE, ok: undefined }, { ...WIRE, pupil: [0] }, { ...WIRE, pupil: [0, 'a'] }, { ...WIRE, pupil: [0, NaN] },
    { ...WIRE, shift: null }, { ...WIRE, edge: [0.95, Infinity] }, { ...WIRE, pupil: undefined }]) {
    assert.equal(parseReveal(bad), null, JSON.stringify(bad));
  }
  const odd = parseReveal({ ...WIRE, cls: 'cat', rho: 'big', soft: 1, drift: null, lid: NaN, ia: 5 });
  assert.ok(odd && odd.cls === undefined && odd.rho === undefined && odd.soft === undefined && odd.drift === undefined && odd.lid === undefined && odd.ia === undefined);
});

test('what the page shows: the cut when ok, the strip without the cut when withheld, the plain slider without numbers and for the sample eye', () => {
  const ok = parseReveal(WIRE), no = parseReveal({ ...WIRE, ok: false });
  assert.equal(revealView(ok), 'cut');
  assert.equal(revealView(no), 'strip');
  assert.equal(revealView(null), 'plain');
  assert.equal(revealView(undefined), 'plain');
  assert.equal(revealView(ok, true), 'plain');
  assert.equal(revealView(no, true), 'plain');
});

test('the colour gate: withheld by colour only when ok is false and the drift is over 8 dE00 (then the colour check advice shows for that eye)', () => {
  assert.equal(DRIFT_FAIL, 8);
  assert.equal(withheldByColour(parseReveal({ ...WIRE, ok: false, drift: 19.7 })), true);
  assert.equal(withheldByColour(parseReveal({ ...WIRE, ok: false, drift: 7.9 })), false);     // withheld by registration
  assert.equal(withheldByColour(parseReveal({ ...WIRE, ok: true, drift: 9 })), false);
  assert.equal(withheldByColour(null), false);
});

test('the p09f case against the vectors: only the hazel eye (drift 19.7) is withheld among the ten calibration eyes; the strip shows, the colour advice shows', () => {
  const eyes = new Map(square.map((v) => [v.eye, v]));
  const human = ['own215120', 'drv_d01', 'drv_w04', 'drv_w02', 'drv_w03', 'p05i', 'p09f', 'drv_w08', 'drv_d04', 'drv_d05'];
  for (const id of human) {
    const rv = parseReveal(eyes.get(id)!.params);
    assert.ok(rv, id);
    assert.equal(revealView(rv), id === 'p09f' ? 'strip' : 'cut', id);
  }
  const p09f = parseReveal(eyes.get('p09f')!.params)!;
  assert.equal(p09f.drift, 19.7);
  assert.equal(withheldByColour(p09f), true);
  assert.equal(human.filter((id) => withheldByColour(parseReveal(eyes.get(id)!.params))).join(), 'p09f');
});

test('the cut sits at 50 percent of the frame, exactly (the vectors say 0.5), and snaps there within 3 percent', () => {
  assert.equal(PUPIL_CUT, 50);
  for (const v of vectors) assert.ok(Math.abs(revealGeometry(v.fit, v.params as never, v.aspect).cut - 0.5) <= 0.005, v.eye);
  for (const p of [47, 49.2, 50, 50.7, 53]) assert.equal(snapCut(p), 50);
  assert.equal(SNAP, 3);
});

test('the frame built from the client crop (after a return from Stripe, the wide frame is gone) is the tight one, the same for any side and the crop of the vectors', () => {
  const a = planFrame(tightFit(1000, 1.12)), b = planFrame(tightFit(318, 1.12)), c = planFrame(tightFit(1400, 1.12));
  assert.deepEqual([a.mode, b.mode, c.mode], ['tight', 'tight', 'tight']);
  assert.ok(Math.abs(a.rf - 0.45) < 1e-12 && a.rf === b.rf && b.rf === c.rf);
  // the calibration eye that exists only as a crop: its fit in the vectors IS this fit (r = side / (2 pad)), and its geometry is what tightFit gives
  const own = square.find((v) => v.eye === 'own215120')!;
  const mine = revealGeometry(tightFit(own.fit.W, 1.12), own.params as never);
  assert.deepEqual(mine.plan, own.expect.plan);
  for (const k of ['cx', 'cy', 'w', 'h', 'left', 'top'] as const) assert.ok(Math.abs(mine.disc[k] - own.expect.disc[k]) < 1e-9, k);
  // the pad of the crop is part of the fit: a 1.2 crop has a smaller iris share, and the frame stays the tight one
  const f = tightFit(1000, 1.2);
  assert.ok(Math.abs(f.r - 1000 / 2.4) < 1e-9 && planFrame(f).mode === 'tight');
});

test('reduced motion: no sweep, no fade, the pupil cut from the start', () => {
  const r = sweepFor(true);
  assert.deepEqual([r.from, r.to, r.delayMs, r.durationMs], [PUPIL_CUT, PUPIL_CUT, 0, 0]);
  for (const col of [0, 1, 2]) assert.deepEqual(stripFadeMs(col, true), { delay: 0, duration: 0 });
  assert.ok(sweepFor(false).durationMs > 0 && stripFadeMs(2, false).duration > 0);
});

test('the restored half sits on pure black (#000, the browser check read rgb(0, 0, 0)) and nothing is drawn around the iris: no border, ring, outline, shadow, stroke or blur on the layers', () => {
  const src = readFileSync(new URL('./Reveal.tsx', import.meta.url), 'utf8');
  const layer = src.split('\n').find((l) => l.includes('data-testid="restored-layer"')) ?? '';
  const disc = src.slice(src.indexOf('export const RestoredDisc'), src.indexOf('interface Props'));
  const draws = /\b(border|ring|outline|shadow|stroke|blur|drop-shadow|filter|backdrop)\b/;
  assert.match(layer, /\bbg-black\b/);
  assert.doesNotMatch(layer, draws);
  assert.doesNotMatch(disc, /boxShadow|filter|outline|border|stroke|textShadow/);
  // the mask is the whole edge treatment, and it comes from the numbers the server measured (zone A untouched: e0 never below 0.95)
  assert.match(disc, /maskImage: mask/);
  const css = readFileSync(new URL('../index.css', import.meta.url), 'utf8');
  assert.doesNotMatch(css, /--color-black\s*:/);      // Tailwind's own black is #000
  // the photo layer takes no filter either: the left half is the customer's photo, untouched
  const photoLine = src.split('\n').find((l) => l.includes('layer P: the customer')) ?? '';
  assert.match(photoLine, /untouched/);
});

test('no component of the Reveal writes text on the picture: the only words are the two pills outside the artwork and the handle has no label', () => {
  const src = readFileSync(new URL('./Reveal.tsx', import.meta.url), 'utf8') + readFileSync(new URL('./RevealStrip.tsx', import.meta.url), 'utf8');
  assert.doesNotMatch(src, /fillText|<text\b|textContent\s*=|SnapEyes|snapeyes/);
});

test('every wire dict the server side goldens hold (scripts/styles_tests/data/reveal_goldens.json: twelve cases) is read by parseReveal, and the view follows ok', () => {
  const gold = JSON.parse(readFileSync(new URL('../../scripts/styles_tests/data/reveal_goldens.json', import.meta.url), 'utf8')).cases as Record<string, { params: Record<string, unknown> }>;
  const keys = Object.keys(gold);
  assert.ok(keys.length >= 12);
  for (const k of keys) {
    const rv = parseReveal(gold[k].params);
    assert.ok(rv, k);
    assert.equal(revealView(rv), gold[k].params.ok ? 'cut' : 'strip', k);
    assert.equal(rv.ok, gold[k].params.ok, k);
    // the wide frame of such an eye is built the way the page builds it: a tight crop here (no photo), the geometry is finite
    const g = revealGeometry(tightFit(1000), rv);
    assert.ok(Number.isFinite(g.disc.left) && Number.isFinite(g.disc.top) && g.plan.mode === 'tight', k);
  }
  assert.deepEqual(keys.filter((k) => !gold[k].params.ok).sort(), ['blue_rot1', 'blue_scale102', 'blue_warm', 'flat']);
});
