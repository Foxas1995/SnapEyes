// The owner's insights of 2026-10-20 on the result screen of /try: the card that says in plain words what the studio did to the photo (insight 1) and what the photo
// goes through (insight 5), and the colour note that says what helps instead of "a retake in soft daylight" (insight 3). The real ResultView, rendered on the server
// (as reveal_page.test.ts does), in the four languages; run by scripts/run_ts_tests.mjs.
import { readFileSync } from 'node:fs';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { type Eye } from '../../src/try/multi';
import { COPY, setCopyLang } from '../../src/try/copy';
import { ResultView } from '../../src/try/ResultView';
import { emptyPicker } from '../../src/try/StylePicker';
import { emptyWords } from '../../src/try/Words';
import { NO_OPTS } from '../../src/try/picker';
import { LANGS } from '../../src/shared/lang';
import { parseReveal, revealGeometry, tightFit } from '../../src/reveal/revealMath';

export async function run(): Promise<Array<[string, boolean, string?]>> {
  const out: Array<[string, boolean, string?]> = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);
  const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#x27;');
  const KEYS = ['title', 'glare', 'sharp', 'colour', 'lid', 'nothing', 'quality'] as const;

  // ---- the words, four languages
  for (const l of LANGS) {
    const d = COPY[l].result.did as Record<string, string>;
    check(`${l}: the card has its seven lines, all different and none empty`, KEYS.every((k) => typeof d[k] === 'string' && d[k].length > 8) && new Set(KEYS.map((k) => d[k])).size === KEYS.length, JSON.stringify(d).slice(0, 200));
    check(`${l}: the quality line names the crop's 1400 px and the file's 4096 px, and the file only in the conditional (ordering is not open yet)`,
      d.quality.includes('1400') && d.quality.includes('4096') && /would|würde|būtų|készülne/.test(d.quality), d.quality);
    const c = COPY[l].result.colourOff;
    check(`${l}: the colour note no longer says "our colour check" or "soft daylight", names the flash and a torch from the side, and says that a result one likes can stay`,
      !/colour check|Farbprüfung|spalvų patikra|színellenőrzés|soft daylight|weichem Tageslicht|švelnioje dienos|lágy nappali/i.test(c)
        && /flash|Blitz|blykst|vaku/i.test(c) && /torch|Taschenlampe|žibintuvėl|zseblámpa/i.test(c) && /carry on|weiter|tęsti|folytasd/i.test(c), c);
  }

  // ---- the real ResultView
  const base = { pupil: [0.001, 0], shift: [0, 0], edge: [0.95, 1.02], rho: 0.26, cls: 'round', soft: false, lid: 0 };
  const okRv = { ...base, ok: true, drift: 1.2 };
  const eyeOf = (rvIn: unknown, extra: Record<string, unknown> = {}) => ({
    id: 'e1', before: 'data:image/jpeg;base64,B', image: 'DISPLAY', thumb: 'data:image/jpeg;base64,T', pad: 1.12, fallback: false, usedSr: false, stored: false, glarePct: 0,
    sample: false, colourOff: false, reveal: parseReveal(rvIn) ?? undefined,
    wide: rvIn ? { url: 'data:image/jpeg;base64,W', uncovered: 0, side: 1024, geometry: revealGeometry(tightFit(400), parseReveal(rvIn)!) } : undefined, ...extra,
  }) as unknown as Eye;
  const noop = () => {};
  const page = (eye: Eye) => renderToStaticMarkup(createElement(ResultView, {
    eyes: [eye], selectedId: eye.id, onSelect: noop, onRemove: noop, onRetake: noop, onAdd: noop, onMove: noop, art: undefined, staleArt: undefined, composeError: null, onRetryCompose: noop,
    picker: emptyPicker(1), layout: null, layoutOptions: [], onLayout: noop, opts: NO_OPTS, onOpts: noop, words: emptyWords(1), onStartOver: noop, purchase: null,
  }));
  const card = (h: string) => {
    const i = h.indexOf('data-testid="what-we-did"');
    if (i < 0) return null;
    const j = h.indexOf('</div>', i);
    return h.slice(i, j);
  };
  const D = COPY.en.result.did;
  const lines = (c: string) => KEYS.filter((k) => k !== 'title' && k !== 'quality' && c.includes(esc(D[k])));
  type Want = { lines: string[] | null };
  const cases: Array<[string, Eye, Want]> = [
    ['the plain slider, a reflection and a lid filled, the colour fine', eyeOf(undefined, { glarePct: 3.1, lidPct: 2.4 }), { lines: ['glare', 'sharp', 'colour', 'lid', 'nothing'] }],
    ['the Reveal with its promise, no reflection, no lid', eyeOf(okRv), { lines: ['sharp', 'colour'] }],
    ['the Reveal, the colour check failed, a lid filled', eyeOf(okRv, { colourOff: true, lidPct: 6 }), { lines: ['sharp', 'lid'] }],
    ['the plain slider, the colour check failed, a reflection', eyeOf(undefined, { colourOff: true, glarePct: 0.5 }), { lines: ['glare', 'sharp'] }],
    ['a reflection under the line of before (0.3 %), lidPct of an older page absent', eyeOf(undefined, { glarePct: 0.3 }), { lines: ['sharp', 'colour', 'nothing'] }],
    ['the AI-generated sample eye', eyeOf(okRv, { sample: true }), { lines: null }],
  ];
  setCopyLang('en');
  for (const [name, eye, want] of cases) {
    let h = '';
    try { h = page(eye); } catch (e) { check(`ResultView renders: ${name}`, false, e instanceof Error ? e.message : String(e)); continue; }
    const c = card(h);
    if (want.lines === null) {
      check(`ResultView, ${name}: no card (the sample is no photo of the visitor's)`, c === null);
      continue;
    }
    check(`ResultView, ${name}: the card says ${want.lines.join(', ')} and the quality line`,
      c !== null && JSON.stringify(lines(c)) === JSON.stringify(want.lines) && c.includes(esc(D.title)) && c.includes(esc(D.quality)), c ? lines(c).join() : 'no card');
    check(`ResultView, ${name}: the card comes after the before/after and the colour note, before the sentence that says where the colour comes from`,
      h.indexOf('data-testid="what-we-did"') < h.indexOf('data-testid="transparency"') && (!eye.colourOff || h.indexOf('data-testid="colour-off"') < h.indexOf('data-testid="what-we-did"')));
    check(`ResultView, ${name}: "no new colours" never stands beside the colour note, nor twice with the Reveal's promise`,
      !(c.includes(esc(D.nothing)) && (h.includes('data-testid="colour-off"') || h.includes('data-testid="promise"'))));
  }
  check('the line "Reflection removed." of before is gone (the card says it), and no dictionary keeps its key', !page(eyeOf(undefined, { glarePct: 3 })).includes('Reflection removed.')
    && LANGS.every((l) => !('reflection' in (COPY[l].result as Record<string, unknown>))));
  for (const l of LANGS) {
    setCopyLang(l);
    const h = page(eyeOf(undefined, { glarePct: 2, lidPct: 3 }));
    const d = COPY[l].result.did;
    check(`${l}: the card speaks the page's language (its title, the lid line and the quality line)`, h.includes(esc(d.title)) && h.includes(esc(d.lid)) && h.includes(esc(d.quality)));
  }
  setCopyLang('en');
  const app = readFileSync('src/try/TryApp.tsx', 'utf8');
  check('the eye remembers the share of the iris /api/deglare filled under a lid (its lid_pct), so the card can say it only when it was done',
    /lidPct: typeof d\.lid_pct === 'number' \? d\.lid_pct : 0/.test(app));
  return out;
}
