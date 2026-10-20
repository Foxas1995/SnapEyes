// The owner's insights of 2026-10-20 on the result screen of /try: the card that says in plain words what the studio did to the photo (insight 1) and what the photo
// goes through (insight 5), and the colour note that says what helps instead of "a retake in soft daylight" (insight 3). The real ResultView, rendered on the server
// (as reveal_page.test.ts does), in the four languages; run by scripts/run_ts_tests.mjs.
// His feedback of the same evening, from his own phone ("the before and after that slides is the most important thing", "so much text", "what is that cut?",
// "why does the start say REALLY?"): the before/after leads every eye, at most three short check lines under it, everything longer in ONE closed disclosure on the
// same screen (folded, never deleted), no sentence twice, no iris size in pixels, one line about the pupil only when it is wide, and a calm first screen.
import { readFileSync } from 'node:fs';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { type Eye, PUPIL_WIDE, pupilWide } from '../../src/try/multi';
import { COPY, setCopyLang } from '../../src/try/copy';
import { ResultView } from '../../src/try/ResultView';
import { emptyPicker } from '../../src/try/StylePicker';
import { emptyWords } from '../../src/try/Words';
import { NO_OPTS } from '../../src/try/picker';
import { LANGS } from '../../src/shared/lang';
import { CROP_MAX_PX } from '../../src/try/crop';
import { AI_MATERIAL_PUBLISHED } from '../../src/shared/aiMaterial';
import { parseReveal, revealGeometry, tightFit } from '../../src/reveal/revealMath';

export async function run(): Promise<Array<[string, boolean, string?]>> {
  const out: Array<[string, boolean, string?]> = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);
  const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#x27;');
  const KEYS = ['title', 'glare', 'sharp', 'colour', 'lid', 'nothing', 'quality'] as const;
  const LINES = ['glare', 'sharp', 'colour', 'lid'] as const;
  const text = (d: Record<string, unknown>, k: string): string => (k === 'quality' ? (d[k] as (n: number) => string)(CROP_MAX_PX) : String(d[k]));
  const words = (s: string) => s.trim().split(/\s+/).length;
  // the four dashes the owner rules out (U+2012 to U+2015), built from their codes so that this file holds none itself (as scripts/check_texts.mjs does)
  const DASH = new RegExp('[' + String.fromCharCode(0x2012, 0x2013, 0x2014, 0x2015) + ']');

  // ---- the words, four languages
  for (const l of LANGS) {
    const d = COPY[l].result.did as unknown as Record<string, unknown>;
    check(`${l}: the card has its seven lines, all different and none empty`, KEYS.every((k) => text(d, k).length > 8) && new Set(KEYS.map((k) => text(d, k))).size === KEYS.length, JSON.stringify(d).slice(0, 200));
    check(`${l}: the four check lines are short (at most 8 words each)`, LINES.every((k) => words(text(d, k)) <= 8), LINES.map((k) => words(text(d, k))).join());
    check(`${l}: the colour line says the light was balanced and nothing about where the colours come from (the transparency sentence says that, once)`,
      !/photo|Foto|nuotrauk|fotó/i.test(text(d, 'colour')), text(d, 'colour'));
    const q = text(d, 'quality');
    check(`${l}: the quality line names the crop's ${CROP_MAX_PX} px (the page's own cut, src/try/crop.ts) and the file's 4096 px, and the file only in the conditional (ordering is not open yet)`,
      q.includes(`${CROP_MAX_PX} px`) && q.includes('4096') && /would|würde|būtų|készülne/.test(q), q);
    const c = COPY[l].result.colourOff;
    check(`${l}: the colour note no longer says "our colour check" or "soft daylight", names the flash and a torch from the side, and says that a result one likes can stay`,
      !/colour check|Farbprüfung|spalvų patikra|színellenőrzés|soft daylight|weichem Tageslicht|švelnioje dienos|lágy nappali/i.test(c)
        && /flash|Blitz|blykst|vaku/i.test(c) && /torch|Taschenlampe|žibintuvėl|zseblámpa/i.test(c) && /carry on|weiter|tęsti|folytasd/i.test(c), c);
    const pw = COPY[l].result.pupilWide;
    check(`${l}: the pupil line is one short sentence that says more light helps`, /light|Licht|šviesos|fény/i.test(pw) && words(pw) <= 12 && (pw.match(/[.!?]/g) ?? []).length === 1, pw);
    check(`${l}: the disclosure has a short title`, COPY[l].result.how.length > 3 && words(COPY[l].result.how) <= 4, COPY[l].result.how);
    const r = COPY[l].result as unknown as Record<string, unknown>;
    check(`${l}: the iris size in pixels and the drag lines are gone from the dictionary`, !('irisPx' in r) && !('drag' in r) && !('drag' in (r.reveal as Record<string, unknown>)));
  }

  // ---- the real ResultView
  const base = { pupil: [0.001, 0], shift: [0, 0], edge: [0.95, 1.02], rho: 0.26, cls: 'round', soft: false, lid: 0 };
  const okRv = { ...base, ok: true, drift: 1.2 };
  const eyeOf = (rvIn: unknown, extra: Record<string, unknown> = {}) => ({
    id: 'e1', before: 'data:image/jpeg;base64,B', image: 'DISPLAY', thumb: 'data:image/jpeg;base64,T', pad: 1.12, fallback: false, usedSr: false, stored: false, glarePct: 0,
    sample: false, colourOff: false, reveal: parseReveal(rvIn) ?? undefined, diameterPx: 702,
    wide: rvIn ? { url: 'data:image/jpeg;base64,W', uncovered: 0, side: 1024, geometry: revealGeometry(tightFit(400), parseReveal(rvIn)!) } : undefined, ...extra,
  }) as unknown as Eye;
  const noop = () => {};
  const page = (eye: Eye) => renderToStaticMarkup(createElement(ResultView, {
    eyes: [eye], selectedId: eye.id, onSelect: noop, onRemove: noop, onRetake: noop, onAdd: noop, onMove: noop, art: undefined, staleArt: undefined, composeError: null, onRetryCompose: noop,
    picker: emptyPicker(1), layout: null, layoutOptions: [], onLayout: noop, opts: NO_OPTS, onOpts: noop, words: emptyWords(1), onStartOver: noop, purchase: null,
  }));
  const at = (h: string, id: string) => h.indexOf(`data-testid="${id}"`);
  const has = (h: string, id: string) => at(h, id) >= 0;
  // the card: from its start to the end of its disclosure
  const card = (h: string) => {
    const i = at(h, 'what-we-did');
    if (i < 0) return null;
    const j = h.indexOf('</details>', i);
    return h.slice(i, j < 0 ? undefined : j);
  };
  const ulOf = (c: string) => c.slice(c.indexOf('<ul'), c.indexOf('</ul>'));
  const D = COPY.en.result.did;
  const lines = (c: string) => LINES.filter((k) => ulOf(c).includes(esc(D[k])));
  type Want = { hero: 'reveal-hero' | 'slider-hero'; lines: string[] | null; tail: 'promise' | 'nothing' | 'none'; colour: boolean };
  const cases: Array<[string, Eye, Want]> = [
    ['the plain slider, a reflection and a lid filled, the colour fine: the colour line steps aside (three lines at most)', eyeOf(undefined, { glarePct: 3.1, lidPct: 2.4 }),
      { hero: 'slider-hero', lines: ['glare', 'sharp', 'lid'], tail: 'nothing', colour: false }],
    ['the Reveal with its promise, no reflection, no lid', eyeOf(okRv), { hero: 'reveal-hero', lines: ['sharp', 'colour'], tail: 'promise', colour: false }],
    ['the Reveal, the colour check failed, a lid filled', eyeOf(okRv, { colourOff: true, lidPct: 6 }), { hero: 'reveal-hero', lines: ['sharp', 'lid'], tail: 'none', colour: true }],
    ['the plain slider, the colour check failed, a reflection', eyeOf(undefined, { colourOff: true, glarePct: 0.5 }), { hero: 'slider-hero', lines: ['glare', 'sharp'], tail: 'none', colour: true }],
    ['a reflection under the line of before (0.3 %), lidPct of an older page absent', eyeOf(undefined, { glarePct: 0.3 }), { hero: 'slider-hero', lines: ['sharp', 'colour'], tail: 'nothing', colour: false }],
    ['the Reveal withheld because the colour drifted (the p09f case, 19.7): the plain slider and the colour note', eyeOf({ ...base, ok: false, drift: 19.7 }, { glarePct: 2 }),
      { hero: 'slider-hero', lines: ['glare', 'sharp'], tail: 'none', colour: true }],
    ['the Reveal withheld by registration alone (the colour is fine): the plain slider, the promise in the disclosure', eyeOf({ ...base, ok: false, drift: 1.2 }),
      { hero: 'slider-hero', lines: ['sharp', 'colour'], tail: 'promise', colour: false }],
    ['the AI-generated sample eye', eyeOf(okRv, { sample: true, pupil: 0.55 }), { hero: 'slider-hero', lines: null, tail: 'none', colour: false }],
  ];
  setCopyLang('en');
  for (const [name, eye, want] of cases) {
    let h = '';
    try { h = page(eye); } catch (e) { check(`ResultView renders: ${name}`, false, e instanceof Error ? e.message : String(e)); continue; }
    const other = want.hero === 'reveal-hero' ? 'slider-hero' : 'reveal-hero';
    check(`ResultView, ${name}: the before/after is ${want.hero === 'reveal-hero' ? 'the Reveal' : 'the plain slider'}, first under its heading, and no strip, no note about a cut, no frame note`,
      has(h, want.hero) && !has(h, other) && !['reveal-withheld', 'no-cut', 'strip-section', 'frame-note'].some((id) => has(h, id)) && !/\bcut\b/i.test(h.replace(/<[^>]+>/g, ' ')),
      [want.hero, has(h, want.hero), has(h, other)].join());
    check(`ResultView, ${name}: the iris size in pixels is not printed`, !h.includes('Iris in your photo') && !h.includes('702'));
    check(`ResultView, ${name}: the colour note ${want.colour ? 'is' : 'is not'} there`, has(h, 'colour-off') === want.colour);
    const c = card(h);
    if (want.lines === null) {
      check(`ResultView, ${name}: no card and no disclosure (the sample is no photo of the visitor's), no pupil line`, c === null && !has(h, 'how-it-works') && !has(h, 'pupil-hint'));
      continue;
    }
    check(`ResultView, ${name}: the card says ${want.lines.join(', ')} (at most three lines)`,
      c !== null && JSON.stringify(lines(c)) === JSON.stringify(want.lines) && lines(c).length <= 3 && c.includes(esc(D.title)), c ? lines(c).join() : 'no card');
    check(`ResultView, ${name}: the card comes after the before/after and the colour note`,
      at(h, want.hero) < at(h, 'what-we-did') && (!want.colour || at(h, 'colour-off') < at(h, 'what-we-did')));
    const det = h.slice(at(h, 'how-it-works'), h.indexOf('</details>', at(h, 'how-it-works')));
    check(`ResultView, ${name}: ONE disclosure, closed until opened, inside the card`,
      (h.match(/data-testid="how-it-works"/g) ?? []).length === 1 && /<details data-testid="how-it-works"[^>]*>/.test(h) && !/<details data-testid="how-it-works"[^>]*\sopen/.test(h) && !!c && c.includes('data-testid="how-it-works"'));
    check(`ResultView, ${name}: the disclosure holds the transparency sentence, the camera's quality${AI_MATERIAL_PUBLISHED ? ', the shared library' : ''} and ${want.tail === 'none' ? 'neither the promise nor "nothing painted on top"' : `the ${want.tail} line`}`,
      det.includes(esc(COPY.en.result.transparency)) && det.includes(esc(D.quality(CROP_MAX_PX))) && (!AI_MATERIAL_PUBLISHED || det.includes(esc(COPY.en.result.aiMaterial)))
        && has(det, 'promise') === (want.tail === 'promise') && has(det, 'nothing') === (want.tail === 'nothing'));
    check(`ResultView, ${name}: the colour warning comes before the transparency sentence, and every long sentence is in the disclosure, none outside it`,
      (!want.colour || h.indexOf(esc(COPY.en.result.colourOff)) < h.indexOf(esc(COPY.en.result.transparency)))
        && [COPY.en.result.transparency, COPY.en.result.aiMaterial, COPY.en.result.reveal.promise, D.nothing, D.quality(CROP_MAX_PX)].every((s) => h.split(esc(s)).length - 1 === (det.includes(esc(s)) ? 1 : 0)));
    check(`ResultView, ${name}: "no new colours" never stands beside the colour note, nor with the Reveal's promise`,
      !(h.includes(esc(D.nothing)) && (has(h, 'colour-off') || has(h, 'promise'))));
  }
  check('the line "Reflection removed." of before is gone (the card says it), and no dictionary keeps its key', !page(eyeOf(undefined, { glarePct: 3 })).includes('Reflection removed.')
    && LANGS.every((l) => !('reflection' in (COPY[l].result as Record<string, unknown>))));

  // ---- the pupil line: only for a wide pupil (the photo's, else the restored one's), never for the sample
  check(`PUPIL_WIDE is 0.40 (the radius the engine treats as dilated, api/_lib/pupilgeo.py DISC_PUPIL_MAX)`, PUPIL_WIDE === 0.4);
  const pupilCases: Array<[string, Eye, boolean]> = [
    ['the photo\'s pupil 0.45 of the iris radius (the owner\'s photos: 0.41 to 0.52)', eyeOf(okRv, { pupil: 0.45 }), true],
    ['the photo\'s pupil exactly 0.40', eyeOf(undefined, { pupil: 0.4 }), true],
    ['the photo\'s pupil 0.30 (daylight)', eyeOf(okRv, { pupil: 0.3 }), false],
    ['no reading on the photo, the restored pupil 0.42', eyeOf({ ...okRv, rho: 0.42 }), true],
    ['no reading on the photo, the restored pupil 0.26', eyeOf(okRv), false],
    ['the photo\'s reading wins over the restored one (0.31 against 0.44)', eyeOf({ ...okRv, rho: 0.44 }, { pupil: 0.31 }), false],
    ['no reading at all (an older server)', eyeOf(undefined), false],
    ['the AI-generated sample with a wide pupil', eyeOf(undefined, { sample: true, pupil: 0.6 }), false],
  ];
  for (const [name, eye, want] of pupilCases) {
    const h = page(eye);
    check(`the pupil line, ${name}: ${want ? 'shown, once, under the before/after and before the card' : 'not shown'}`,
      pupilWide(eye) === want && has(h, 'pupil-hint') === want && (!want || ((h.match(/data-testid="pupil-hint"/g) ?? []).length === 1 && at(h, 'pupil-hint') < at(h, 'what-we-did') && h.includes(esc(COPY.en.result.pupilWide)))));
  }

  for (const l of LANGS) {
    setCopyLang(l);
    const h = page(eyeOf(undefined, { glarePct: 2, lidPct: 3, pupil: 0.5 }));
    const d = COPY[l].result.did;
    check(`${l}: the card speaks the page's language (its title, the lid line, the disclosure's title and quality line, the pupil line)`,
      h.includes(esc(d.title)) && h.includes(esc(d.lid)) && h.includes(esc(COPY[l].result.how)) && h.includes(esc(d.quality(CROP_MAX_PX))) && h.includes(esc(COPY[l].result.pupilWide)));
  }
  setCopyLang('en');

  // ---- no "cut" in any customer sentence of /try (the owner did not know the word: "what is that cut?"), nor in the landing's Reveal
  const cutWord = /pjūv|\bcut\b|\bcutting\b|\bschnitt\b|schnitt\b(?<!ausschnitt|zuschnitt)|\bvágás|pupillenschnitt/i;
  const strings = (o: unknown, path = ''): Array<[string, string]> => {
    if (typeof o === 'string') return [[path, o]];
    if (typeof o === 'function') { try { const v = (o as (...a: unknown[]) => unknown)(1400, 2, 3); return typeof v === 'string' ? [[path, v]] : []; } catch { return []; } }
    if (o && typeof o === 'object') return Object.entries(o).flatMap(([k, v]) => strings(v, path ? `${path}.${k}` : k));
    return [];
  };
  for (const l of LANGS) {
    const bad = strings(COPY[l]).filter(([, s]) => cutWord.test(s));
    check(`${l}: no sentence of /try names a "cut" (pjūvis, Schnitt, vágás)`, bad.length === 0, bad.map(([p]) => p).join());
    const landing = JSON.parse(readFileSync(`src/landing/copy/${l}.json`, 'utf8')) as { reveal: { intro: string; introWeb: string }; hero: { discAlt: string } };
    const lb = [landing.reveal.intro, landing.reveal.introWeb, landing.hero.discAlt].filter((s) => cutWord.test(s));
    check(`${l}: the landing's Reveal says nothing about a cut either`, lb.length === 0, lb.join(' | '));
  }

  // ---- the first screen: calm and short
  for (const l of LANGS) {
    const cp = COPY[l].capture;
    const head = `${cp.titleA}${cp.titleB}`;
    check(`${l}: the headline does not insist ("REALLY", "FOR REAL", "TIKRAI", "GANZ ECHT", "TÉNYLEG") and has no dash`,
      !/really|for real|tikrai|ganz echt|wirklich|tényleg|igazán/i.test(head) && !DASH.test(head), head);
    check(`${l}: the line under the headline is one short sentence`, (cp.lead.match(/[.!?](\s|$)/g) ?? []).length === 1 && words(cp.lead) <= 14, cp.lead);
    check(`${l}: four numbered steps, each short`, cp.steps.length === 4 && cp.steps.every((s, i) => s.title.startsWith(`${i + 1}.`) && words(s.text) <= 12), cp.steps.map((s) => words(s.text)).join());
    check(`${l}: the disclosure of the other tips has its title`, typeof cp.moreTips === 'string' && cp.moreTips.length > 3 && words(cp.moreTips) <= 3, cp.moreTips);
  }
  const app = readFileSync('src/try/TryApp.tsx', 'utf8');
  const tips = app.slice(app.indexOf('data-testid="more-tips"'), app.indexOf('</details>', app.indexOf('data-testid="more-tips"')));
  check('the open eye, the 3-5 shots and the pair are inside the closed "More tips" disclosure of the first screen, not beside the four steps',
    tips.includes('T.capture.stepsOpenMore') && tips.includes('T.capture.stepsShotsMore') && tips.includes('T.capture.helper') && !/<details data-testid="more-tips"[^>]*\sopen/.test(app)
      && app.split('T.capture.stepsShotsMore').length === 2 && app.split('T.capture.helper').length === 2);
  check('the eye remembers the share of the iris /api/deglare filled under a lid (its lid_pct), so the card can say it only when it was done',
    /lidPct: typeof d\.lid_pct === 'number' \? d\.lid_pct : 0/.test(app));
  check('the eye remembers the pupil measured on its photo (/api/analyze quality.pupil_size), for the pupil line',
    /pupil: a\.quality\.pupil_size/.test(app));
  check('the crop the page cuts and the size the quality line names are one constant (src/try/crop.ts), so the sentence cannot drift from the cut',
    /Math\.min\(CROP_MAX_PX, Math\.round\(S\)\)/.test(app) && !/Math\.min\(\d+, Math\.round\(S\)\)/.test(app));
  return out;
}
