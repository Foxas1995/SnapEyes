// WP9: the page code around the Reveal that needs the page's own modules (src/try/multi.ts, checkout.ts, copy.ts), so it runs through Vite's module runner
// (scripts/run_ts_tests.mjs) and returns its results, printing nothing. The arithmetic of the Reveal is src/reveal/*.test.ts (node:test).
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { savedEye, type Eye } from '../../src/try/multi';
import { saveSnapshot, takeSnapshot } from '../../src/try/checkout';
import { COPY } from '../../src/try/copy';
import { ResultView } from '../../src/try/ResultView';
import { emptyPicker } from '../../src/try/StylePicker';
import { emptyWords } from '../../src/try/Words';
import { NO_OPTS } from '../../src/try/picker';
import { LANGS } from '../../src/shared/lang';
import { parseReveal, revealGeometry, tightFit, valueText } from '../../src/reveal/revealMath';

export async function run(): Promise<Array<[string, boolean, string?]>> {
  const out: Array<[string, boolean, string?]> = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);

  // ---- the saved copy for the way back from Stripe's page: no wide frame, no draft, the numbers stay
  const reveal = parseReveal({ pupil: [0.001, 0], shift: [0, 0], edge: [0.95, 1.02], ok: true, rho: 0.26, cls: 'round', soft: false, drift: 0.4, lid: 0 })!;
  const frameUrl = 'data:image/jpeg;base64,' + 'A'.repeat(4000);
  const eye = {
    id: 'e1', before: 'data:image/jpeg;base64,BEFORE', image: 'DISPLAY', thumb: 'T', pad: 1.12, fallback: false, usedSr: false, stored: false, glarePct: 0, sample: false,
    colourOff: false, sealed: 'S', draft: { crop: 'C', ticket: 'TK', until: 1 }, reveal,
    wide: { url: frameUrl, uncovered: 0, side: 1024, geometry: { plan: { mode: 'wide', rf: 0.335 }, box: [0, 0, 1, 1], cut: 0.5, disc: {}, restored: {} } },
  } as unknown as Eye;
  const kept = savedEye(eye) as Record<string, unknown>;
  check('savedEye: the wide frame and the draft stay out of the copy kept for the way back', !('wide' in kept) && !('draft' in kept), Object.keys(kept).join());
  check('savedEye: everything else stays, the Reveal numbers (about 150 bytes) with it', kept.reveal === reveal && kept.before === eye.before && kept.image === 'DISPLAY' && kept.sealed === 'S' && kept.id === 'e1');
  const store = new Map<string, string>();
  (globalThis as unknown as { window: unknown }).window = { sessionStorage: { getItem: (k: string) => store.get(k) ?? null, setItem: (k: string, v: string) => { store.set(k, v); }, removeItem: (k: string) => { store.delete(k); } } };
  const saved = saveSnapshot({ v: 1, order: 'o9', at: Date.now(), style: 's', layoutWant: null, names: '', eyes: [savedEye(eye) as never] });
  const text = [...store.values()].join('');
  check('the snapshot in sessionStorage holds no wide frame (not one byte of it) and no work ticket', saved && !text.includes(frameUrl.slice(40, 200)) && !text.includes('"wide"') && !text.includes('TK'), text.slice(0, 160));
  const back = takeSnapshot('o9');
  const be = back?.eyes[0] as unknown as Record<string, unknown> | undefined;
  check('the way back finds the eye with its Reveal numbers and its crop, and no frame (the page builds the tight frame again from the crop)',
    !!be && parseReveal(be.reveal)?.ok === true && be.before === eye.before && !('wide' in be));

  // ---- the words: four languages, the same keys, the claims the owner and the review ruled out are not there
  const KEYS = ['photo', 'iris', 'art', 'slider', 'valueText', 'drag', 'promise', 'stripTitle', 'stripIntro', 'stripIntroPair', 'noCut', 'softTip', 'frameWide', 'frameTight'];
  const rev = (l: (typeof LANGS)[number]) => COPY[l].result.reveal as unknown as Record<string, string>;
  for (const l of LANGS) {
    const r = rev(l);
    check(`${l}: the Reveal copy has all ${KEYS.length} strings, each a plain trimmed sentence or label`,
      JSON.stringify(Object.keys(r).sort()) === JSON.stringify([...KEYS].sort()) && KEYS.every((k) => typeof r[k] === 'string' && r[k].length > 1 && r[k] === r[k].trim()), Object.keys(r).join());
    check(`${l}: valueText holds the placeholder and the slider says a whole number`, r.valueText.includes('{n}') && /\d/.test(valueText(49.6, r.valueText)) && !valueText(49.6, r.valueText).includes('{n}'), valueText(49.6, r.valueText));
    const all = KEYS.map((k) => r[k]).join(' | ');
    check(`${l}: no claim of uniqueness, no "best", no proof line about identical pixels, no dash`,
      !/unique|one of a kind|never repeated|no two alike|handmade|most chosen|\bbest\b|identical|pixel/i.test(all) && !new RegExp('[' + String.fromCharCode(0x2012, 0x2013, 0x2014, 0x2015) + ']').test(all), all.slice(0, 120));
    check(`${l}: the promise says the iris is restored, never recoloured and never swapped (the landing page's words), not that nothing is redrawn`,
      !/redrawn|never redraw/i.test(r.promise) && r.promise.length > 40, r.promise);
  }
  check('de, lt and hu are not the English words (a string kept in English by mistake would be flagged by the build too, not for one word labels)',
    (['de', 'lt', 'hu'] as const).every((l) => KEYS.filter((k) => !['art'].includes(k)).every((k) => rev(l)[k] !== rev('en')[k])));
  check('the no-cut note and the strip lines are different strings (nothing is said twice)', new Set(KEYS.map((k) => rev('en')[k])).size === KEYS.length);

  // ---- what the result page prints around the Reveal (the real ResultView, rendered on the server with the eye's own numbers): the promise line and the colour warning
  // never stand together (review of WP9: "we never recolour your iris" beside "our colour check says this restoration drifted" contradicted itself on the p09f eye)
  const en = COPY.en.result;
  const geomOf = (rvIn: unknown) => revealGeometry(tightFit(400), parseReveal(rvIn)!);
  const base = { pupil: [0.001, 0], shift: [0, 0], edge: [0.95, 1.02], rho: 0.26, cls: 'round', soft: false, lid: 0 };
  const eyeOf = (rvIn: unknown, extra: Record<string, unknown> = {}) => ({
    id: 'e1', before: 'data:image/jpeg;base64,B', image: 'DISPLAY', thumb: 'data:image/jpeg;base64,T', pad: 1.12, fallback: false, usedSr: false, stored: false, glarePct: 0,
    sample: false, colourOff: false, reveal: parseReveal(rvIn) ?? undefined,
    wide: rvIn ? { url: 'data:image/jpeg;base64,W', uncovered: 0, side: 1024, geometry: geomOf(rvIn) } : undefined, ...extra,
  }) as unknown as Eye;
  const noop = () => {};
  const page = (eye: Eye) => renderToStaticMarkup(createElement(ResultView, {
    eyes: [eye], selectedId: eye.id, onSelect: noop, onRemove: noop, onRetake: noop, onAdd: noop, onMove: noop, art: undefined, staleArt: undefined, composeError: null, onRetryCompose: noop,
    picker: emptyPicker(1), layout: null, layoutOptions: [], onLayout: noop, opts: NO_OPTS, onOpts: noop, words: emptyWords(1), onStartOver: noop, purchase: null,
  }));
  const has = (h: string, id: string) => h.includes(`data-testid="${id}"`);
  const okRv = { ...base, ok: true, drift: 1.2 };
  const cases: Array<[string, Eye, { view: string; promise: boolean; colour: boolean }]> = [
    ['the cut shown, the colour fine', eyeOf(okRv), { view: 'reveal-hero', promise: true, colour: false }],
    ['the cut shown, but the colour check of the restoration itself failed (colourOff)', eyeOf(okRv, { colourOff: true }), { view: 'reveal-hero', promise: false, colour: true }],
    ['the cut withheld because the colour drifted (the p09f case, 19.7)', eyeOf({ ...base, ok: false, drift: 19.7 }), { view: 'reveal-withheld', promise: false, colour: true }],
    ['the cut withheld by registration alone (the colour is fine)', eyeOf({ ...base, ok: false, drift: 1.2 }), { view: 'reveal-withheld', promise: true, colour: false }],
    ['the plain slider (no numbers), the colour check failed', eyeOf(undefined, { colourOff: true }), { view: 'none', promise: false, colour: true }],
    ['the AI-generated sample eye', eyeOf(okRv, { sample: true }), { view: 'none', promise: false, colour: false }],
  ];
  for (const [name, eye, want] of cases) {
    let h = '';
    try { h = page(eye); } catch (e) { check(`ResultView renders: ${name}`, false, e instanceof Error ? e.message : String(e)); continue; }
    const view = has(h, 'reveal-hero') ? 'reveal-hero' : has(h, 'reveal-withheld') ? 'reveal-withheld' : 'none';
    check(`ResultView, ${name}: shows ${want.view}, the promise line ${want.promise ? 'is' : 'is not'} there, the colour warning ${want.colour ? 'is' : 'is not'} there`,
      view === want.view && has(h, 'promise') === want.promise && has(h, 'colour-off') === want.colour && h.includes(want.promise ? COPY.en.result.reveal.promise : 'never-printed-sentinel') === want.promise,
      `${view} promise=${has(h, 'promise')} colour=${has(h, 'colour-off')}`);
    if (want.colour) {
      check(`ResultView, ${name}: the colour warning comes before the transparency sentence, and the sentence that says where the colour comes from stays`,
        h.indexOf(en.colourOff) >= 0 && h.indexOf(en.colourOff) < h.indexOf(en.transparency) && has(h, 'transparency'), [h.indexOf(en.colourOff), h.indexOf(en.transparency)].join());
    }
  }
  check('ResultView, the withheld colour case still says why there is no cut and still offers the retake (the review asked for exactly this case to be shown honestly)',
    (() => { const h = page(cases[2][1]); return h.includes(en.reveal.noCut) && h.includes(en.colourOff) && !h.includes(en.reveal.promise); })());
  return out;
}
