// WP9: the page code around the Reveal that needs the page's own modules (src/try/multi.ts, checkout.ts, copy.ts), so it runs through Vite's module runner
// (scripts/run_ts_tests.mjs) and returns its results, printing nothing. The arithmetic of the Reveal is src/reveal/*.test.ts (node:test).
import { savedEye, type Eye } from '../../src/try/multi';
import { saveSnapshot, takeSnapshot } from '../../src/try/checkout';
import { COPY } from '../../src/try/copy';
import { LANGS } from '../../src/shared/lang';
import { parseReveal, valueText } from '../../src/reveal/revealMath';

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
  return out;
}
