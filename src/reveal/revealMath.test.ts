// node --test src/reveal/revealMath.test.ts   (Node 24 runs TypeScript directly; scripts/run_ts_tests.mjs runs it with the other page tests)
// T16 for the page's arithmetic: the geometry equals what designs/presentation.py computed for the same photos, the cut snaps within
// +-3 % of the pupil cut, the keys and the double tap do what section 4.2 says, reduced motion has no sweep.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { CARD_ASPECT, PUPIL_CUT, RF, RF_SNAP_MAX, SNAP, checkFit, chooseRf, contextBox, edgePair, entersSnap, keyCut, maskCss, maskStops, photoBox, revealGeometry, snapCut, stripFadeMs, sweepFor, tightNeeded, tightRf, toggleCut, uncoveredShare, uncoveredWindow, valueText, type Aspect, type Fit } from './revealMath.ts';

interface Vec { eye: string; aspect: Aspect; fit: Fit; params: { pupil: [number, number]; shift: [number, number]; edge: [number, number]; ok: boolean; ia?: number }; expect: ReturnType<typeof revealGeometry>; context: [number, number, number, number] }
const vectors: Vec[] = JSON.parse(readFileSync(new URL('./vectors.json', import.meta.url), 'utf8'));

const near = (a: number, b: number, tol: number, what: string) => assert.ok(Math.abs(a - b) <= tol, `${what}: ${a} vs ${b}`);

test('geometry equals the numpy reference for every eye and both frames (1:1 page, 4:5 card)', () => {
  assert.ok(vectors.length >= 30);      // 10 calibration eyes and 9 animals, each at 1:1 and 4:5
  for (const v of vectors) {
    const g = revealGeometry(v.fit, v.params, v.aspect);
    assert.equal(g.plan.mode, v.expect.plan.mode, `${v.eye} ${v.aspect} mode`);
    near(g.plan.rf, v.expect.plan.rf, 1e-9, `${v.eye} rf`);
    v.expect.box.forEach((b, i) => near(g.box[i], b, 1e-6, `${v.eye} box[${i}]`));
    for (const k of ['cx', 'cy', 'w', 'h', 'left', 'top'] as const) {
      near(g.disc[k], v.expect.disc[k], 1e-9, `${v.eye} disc.${k}`);
      near(g.restored[k], v.expect.restored[k], 1e-9, `${v.eye} restored.${k}`);
    }
    near(g.disc.e0, v.expect.disc.e0, 1e-9, 'e0');
    near(g.disc.e1, v.expect.disc.e1, 1e-9, 'e1');
    near(g.disc.ia, v.expect.disc.ia, 1e-9, 'ia');
    assert.ok(g.disc.e0 >= 0.9 - 1e-9, `${v.eye} e0 ${g.disc.e0}`);
  }
});

test('the context crop box equals the numpy reference for every eye and every frame, and stays inside the photo', () => {
  for (const v of vectors) {
    const b = contextBox(v.fit, v.params);
    assert.deepEqual(b, v.context, `${v.eye} ${v.aspect}`);
    assert.ok(b[0] >= 0 && b[1] >= 0 && b[2] <= v.fit.W && b[3] <= v.fit.H && b[2] > b[0] && b[3] > b[1]);
    // it holds the 4:5 window (and so the 1:1 one) apart from the part of it beyond the photo
    const g = revealGeometry(v.fit, v.params, CARD_ASPECT);
    assert.ok(b[0] <= Math.max(0, g.box[0]) + 1 && b[1] <= Math.max(0, g.box[1]) + 1 && b[2] >= Math.min(v.fit.W, g.box[2]) - 1 && b[3] >= Math.min(v.fit.H, g.box[3]) - 1, `${v.eye} holds the window`);
  }
});

test('the frame is centred on the pupil and the disc is a square of side 2 rf (an ellipse 2 rf x 2 rf / ia for an oval iris)', () => {
  for (const v of vectors) {
    const g = revealGeometry(v.fit, v.params, v.aspect);
    near(g.disc.w, 2 * g.plan.rf * 100, 1e-9, 'disc.w');
    near(g.disc.h, ((2 * g.plan.rf * 100) * (v.aspect[0] / v.aspect[1])) / (v.params.ia ?? 1), 1e-9, 'disc.h');
    // the pupil sits at the frame centre: the disc centre is offset by exactly -pupil x rf (in W units)
    near(g.disc.cx, 50 - v.params.pupil[0] * g.plan.rf * 100, 1e-9, 'cx');
    // the restored image square (side D / (2 R_FRAC) = 1.12 D) is centred on the disc
    near(g.restored.cx, g.disc.cx, 1e-9, 'restored cx');
    near(g.restored.w / g.disc.w, 1.12, 1e-9, 'pad ratio');
  }
});

test('wide frames use D 0.67 to 0.70 W, tight frames D = 0.90 W (the cap) or a little more when the photo is cropped tighter than the pad', () => {
  for (const v of vectors) {
    const g = revealGeometry(v.fit, v.params, v.aspect);
    assert.ok(uncoveredShare(g.box, v.fit.W, v.fit.H) <= 0.15 + 1e-9, `${v.eye} ${v.aspect} uncovered`);
    if (g.plan.mode === 'wide') {
      assert.ok(2 * g.plan.rf >= 0.67 - 1e-9 && 2 * g.plan.rf <= 2 * RF_SNAP_MAX + 1e-9, `${v.eye} wide D ${2 * g.plan.rf}`);
    } else {
      assert.ok(2 * g.plan.rf >= 0.9 - 1e-9 && 2 * g.plan.rf <= 0.98 + 1e-9, `${v.eye} tight D ${2 * g.plan.rf}`);
    }
  }
});

test('the 4:5 card is wide only when the 1:1 frame is wide (a tall window needs more photo); otherwise the card is the 1:1 frame', () => {
  const card = vectors.filter((v) => v.aspect[0] === CARD_ASPECT[0]);
  assert.ok(card.length > 0);
  let wide45 = 0, fallback = 0;
  for (const v of card) {
    const sq = vectors.find((s) => s.eye === v.eye && s.aspect[0] === s.aspect[1]);
    assert.ok(sq);
    if (v.expect.plan.mode === 'wide') { wide45++; assert.equal(sq.expect.plan.mode, 'wide', `${v.eye} card wide needs a wide 1:1 frame`); }
    else if (sq.expect.plan.mode === 'wide') fallback++;
  }
  assert.ok(wide45 > 0 && fallback >= 0);
});

test('a window that leaves the photo by a sliver zooms (up to D 0.70) and stays inside; a bigger excursion keeps D 0.67 (clamped) or goes tight', () => {
  const sliver: Fit = { cx: 1000, cy: 500, r: 200, W: 2000, H: 1000 };        // 1:1 window at D 0.67 is 597 px wide: fits the height 1000 only when centred
  const one = chooseRf({ cx: 300, cy: 500, r: 200, W: 1000, H: 1000 }, RF, [0, 0], [1, 1]);   // window left edge at 300 - 298.5: inside, no zoom needed
  assert.equal(one.rf, RF);
  const tiny = chooseRf({ cx: 295, cy: 500, r: 200, W: 1000, H: 1000 }, RF, [0, 0], [1, 1]);   // 3.5 px beyond the left edge: zoom
  assert.ok(tiny.rf > RF && tiny.rf <= RF_SNAP_MAX && tiny.ok);
  assert.ok(uncoveredWindow({ cx: 295, cy: 500, r: 200, W: 1000, H: 1000 }, [0, 0], [0, 0], tiny.rf, [1, 1]) <= 1e-9);
  const more = chooseRf({ cx: 230, cy: 500, r: 200, W: 1000, H: 1000 }, RF, [0, 0], [1, 1]);  // 68 px beyond: no zoom can fix it, clamped at D 0.67
  assert.equal(more.rf, RF);
  assert.equal(more.ok, true);                                                  // 11 % of the window uncovered: allowed
  assert.equal(chooseRf({ cx: 200, cy: 500, r: 200, W: 1000, H: 1000 }, RF, [0, 0], [1, 1]).ok, false);   // 16 %: the tight frame
  assert.equal(tightNeeded({ cx: 60, cy: 500, r: 200, W: 1000, H: 1000 }, [0, 0], [1, 1]), true);
  assert.equal(tightNeeded({ cx: 500, cy: 500, r: 450, W: 1000, H: 1000 }, [0, 0], [1, 1]), true);   // D 0.9 of the short side
  assert.equal(tightNeeded({ cx: 1500, cy: 1000, r: 200, W: 3000, H: 2000 }, [0, 0], [1, 1]), false);
  assert.ok(sliver.r > 0);
});

test('the registration shift enters the window (a tight crop never invents a sliver of clamp)', () => {
  const crop: Fit = { cx: 500, cy: 500, r: 446.4, W: 1000, H: 1000 };           // the client crop: iris 0.4464 of the side
  const a = tightRf(crop, [0, 0], [1, 1], [0, 0]);
  const b = tightRf(crop, [0, 0], [1, 1], [0.05, 0.0]);
  assert.equal(a, 0.45);
  assert.ok(b >= a);
  assert.ok(uncoveredWindow(crop, [0, 0], [0.05, 0], b, [1, 1]) <= 0.15);
});

test('every input is validated: a fit that cannot be framed throws, clamps are the numpy ones', () => {
  const ok: Fit = { cx: 500, cy: 500, r: 100, W: 1000, H: 1000 };
  assert.doesNotThrow(() => checkFit(ok));
  for (const bad of [{ ...ok, r: 0 }, { ...ok, r: -5 }, { ...ok, r: 0.5 }, { ...ok, cx: NaN }, { ...ok, r: Infinity }, { ...ok, r: 50 * ok.W }, { ...ok, W: 0 }]) {
    assert.throws(() => checkFit(bad), Error);
    assert.throws(() => revealGeometry(bad, { pupil: [0, 0], shift: [0, 0], edge: [0.95, 0.99] }), Error);
  }
  assert.deepEqual(edgePair([0.95, 0.95]), [0.95, 0.955]);
  assert.deepEqual(edgePair([0.99, 0.95]), [0.99, 0.995]);
  assert.deepEqual(edgePair([NaN, 1.0]), [0.985, 1.0]);
  assert.deepEqual(edgePair(undefined), [0.985, 1.015]);
  const g = revealGeometry(ok, { pupil: [1, 1], shift: [5, 5], edge: [0.95, 0.99] });     // clamped to 0.30 and 0.06
  const h = revealGeometry(ok, { pupil: [0.3, 0.3], shift: [0.06, 0.06], edge: [0.95, 0.99] });
  assert.deepEqual(g.box, h.box);
  assert.ok(Object.values(g.disc).every((x) => Number.isFinite(x)));
});

test('photoBox is resolution independent and moves opposite to the shift', () => {
  const fit: Fit = { cx: 800, cy: 600, r: 150, W: 2000, H: 1200 };
  const a = photoBox(fit, [0, 0], 0.335, [0, 0]);
  const b = photoBox(fit, [0, 0], 0.335, [0.01, 0]);
  near(a[2] - a[0], fit.r / 0.335, 1e-9, 'width');
  near(b[0] - a[0], -0.01 * fit.r, 1e-9, 'shift');
});

test('the mask stops are the smoothstep of the restored edge', () => {
  const s = maskStops(0.935, 0.995, 12);
  assert.equal(s[0].alpha, 1);
  near(s[1].pos, 0.935, 1e-12, 'first');
  near(s[s.length - 1].pos, 0.995, 1e-12, 'last');
  assert.equal(s[s.length - 1].alpha, 0);
  near(s[7].alpha, 0.5, 1e-9, 'mid');
  for (let i = 1; i < s.length; i++) assert.ok(s[i].alpha <= s[i - 1].alpha);
  assert.match(maskCss(0.935, 0.995), /^radial-gradient\(closest-side, rgba\(0,0,0,1\.0000\) 0\.00%, /);
});

test('snap: within +-3 % of the pupil cut the cut sits exactly on it', () => {
  for (const p of [47.0, 47.01, 50, 50.4, 52.99, 53]) assert.equal(snapCut(p), PUPIL_CUT, String(p));
  for (const p of [46.99, 53.01, 0, 100, 12]) assert.notEqual(snapCut(p), PUPIL_CUT, String(p));
  assert.equal(snapCut(-5), 0);
  assert.equal(snapCut(140), 100);
  assert.equal(SNAP, 3);
  assert.equal(entersSnap(60, 52), true);
  assert.equal(entersSnap(52, 50), false);
  assert.equal(entersSnap(40, 20), false);
});

test('keys: arrows step 2 %, Home 0, End 100, Enter snaps to the pupil cut, other keys are ignored', () => {
  assert.equal(keyCut(50, 'ArrowRight'), 52);
  assert.equal(keyCut(50, 'ArrowLeft'), 48);
  assert.equal(keyCut(99, 'ArrowRight'), 100);
  assert.equal(keyCut(1, 'ArrowLeft'), 0);
  assert.equal(keyCut(73, 'Home'), 0);
  assert.equal(keyCut(73, 'End'), 100);
  assert.equal(keyCut(73, 'Enter'), 50);
  assert.equal(keyCut(73, 'Tab'), null);
  assert.equal(keyCut(73, 'a'), null);
});

test('double tap toggles pupil cut, all photo, all restored, pupil cut', () => {
  assert.equal(toggleCut(50), 100);
  assert.equal(toggleCut(100), 0);
  assert.equal(toggleCut(0), 50);
  assert.equal(toggleCut(37), 50);
});

test('the arrival sweep: 400 ms wait, 900 ms, 100 -> 50; none with reduced motion', () => {
  const s = sweepFor(false);
  assert.deepEqual([s.from, s.to, s.delayMs, s.durationMs], [100, 50, 400, 900]);
  assert.equal(s.easing, 'cubic-bezier(.2,.7,.2,1)');
  const r = sweepFor(true);
  assert.deepEqual([r.from, r.to, r.delayMs, r.durationMs], [50, 50, 0, 0]);
  assert.deepEqual(stripFadeMs(2, false), { delay: 1000, duration: 500 });
  assert.deepEqual(stripFadeMs(2, true), { delay: 0, duration: 0 });
});

test('aria-valuetext says how much of the frame the photo takes, in the words of the page language (a template with {n})', () => {
  assert.equal(valueText(50), 'photo 50 percent');
  assert.equal(valueText(49.6, 'Foto {n} Prozent'), 'Foto 50 Prozent');
  assert.equal(valueText(100, 'nuotrauka {n} %'), 'nuotrauka 100 %');
  assert.equal(valueText(0, 'foto {n} szazalek'), 'foto 0 szazalek');
});
