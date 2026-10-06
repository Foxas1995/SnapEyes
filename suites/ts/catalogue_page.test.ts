// WP12: the run-time catalogue as a page reads it (src/shared/catalogue.ts) and the landing page's pricing copy that takes its list of styles and its number of eyes
// from it: GET /api/checkout's styles and orderable_max_eyes are read, an older answer or a bad one keeps the build's fallback, the tokens {max} and {styles} are filled,
// a style the server holds at preview is not listed, and the pricing rows of the four languages carry the tokens and no written number or list.
// Loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results, prints nothing.
import { fallbackCatalogue, fillTokens, readCatalogue } from '../../src/shared/catalogue';
import { COPY } from '../../src/landing/copy';
import { AI_MATERIAL, AI_MATERIAL_PUBLISHED, aiBlocks, aiSentence } from '../../src/shared/aiMaterial';
import { LEGAL_UPDATED } from '../../src/shared/legal';
import { STYLES, styleName, classStyle, EFFECTIVE_DEFAULT, buildStage, ceilingStage, landingStyles } from '../../src/shared/styles';

type R = Array<[string, boolean, string?]>;

export async function run(): Promise<R> {
  const out: R = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);
  const DASH = new RegExp('[' + String.fromCharCode(0x2012, 0x2013, 0x2014, 0x2015) + ']');

  const fb = fallbackCatalogue();
  // WP18: the fallback was "the build's ceilings" (while the legacy styles were live: eight eyes and five art styles). Since the cutover it is the build's reading of the
  // stages with the registry's EFFECTIVE_DEFAULT: the ceilings of the v3 styles are live but held at preview until the owner's tick, the legacy ids are retired, so a page that
  // cannot reach the server promises nothing: no maximum, no list, no id.
  check('the fallback is the build\'s reading of the stages (the ceilings held at the registry\'s effective default): since the cutover nothing is orderable, so no eyes, no art styles, no id',
    fb.max === 0 && fb.styles.length === 0 && fb.one.length === 0 && EFFECTIVE_DEFAULT === 'preview', JSON.stringify(fb));
  check('buildStage is the ceiling held at the effective default for a style of the v3 engine, never for a retired one: the five singles and the Trio are live ceilings and preview here, Elements stays lab, a legacy id is retired',
    buildStage('solo.clean', 1) === 'preview' && buildStage('grp.collision', 3) === 'preview' && buildStage('solo.elements', 1) === 'lab' && buildStage('studio_black', 1) === 'retired' && buildStage('solo.clean', 2) === null
    && ceilingStage('solo.clean', 1) === 'live' && landingStyles().map((s) => s.id).join() === 'solo.powder,solo.universe,solo.splash,solo.gold,solo.clean', landingStyles().map((s) => s.id).join());

  const info = (styles: unknown, max: unknown) => ({ ok: true, open: true, styles, orderable_max_eyes: max });
  const live = (id: string, name: string, stages: Record<string, string>) => ({ id, name, slug: id, group: 'solo', eyes: [1, 8], stages });
  const ids = Object.keys(STYLES);
  const gold = ids.find((id) => STYLES[id].legacy === 0 && STYLES[id].price_class === 'art' && STYLES[id].tile_order > 0 && STYLES[id].eyes[0] === 1)!;
  const clean = ids.find((id) => STYLES[id].price_class === 'black' && STYLES[id].legacy === 0 && STYLES[id].stage !== 'planned')!;
  const goldName = STYLES[gold].name;
  const rc = readCatalogue(info([live(gold, goldName, { '1': 'live' }), live(clean, STYLES[clean].name, { '1': 'live' })], 3));
  check('a catalogue of the server: the number of eyes is its orderable_max_eyes, the list holds the styles of the ART class that are live for one eye (the black class is named by its own row)',
    !!rc && rc.max === 3 && rc.styles.join() === goldName, JSON.stringify(rc));
  const rp = readCatalogue(info([live(gold, goldName, { '1': 'preview' })], 0));
  check('a style the server holds at preview is not in the list (the page shows it as Soon), and nothing orderable is a maximum of 0', !!rp && rp.styles.length === 0 && rp.max === 0, JSON.stringify(rp));
  check('an answer without a catalogue (an older server), with a maximum outside 0 to 8 or of the wrong kind, or that is not an object keeps the fallback (null)',
    readCatalogue({ ok: true }) === null && readCatalogue(info([], 9)) === null && readCatalogue(info([], '3')) === null && readCatalogue(info({}, 3)) === null
    && readCatalogue(null) === null && readCatalogue('x') === null, '');
  const rn = readCatalogue(info([{ id: gold, stages: { '1': 'live' } }, { id: 'unknown.id', stages: { '1': 'live' } }, { id: gold }, 7, null], 2));
  check('malformed entries are skipped, a style without a name takes the registry\'s, an id the registry does not know is not listed', !!rn && rn.styles.join() === goldName && rn.max === 2, JSON.stringify(rn));

  const cat = { max: 3, styles: ['Powder Burst', 'Splash'], one: [] };
  check('fillTokens fills {max} and {styles} (a comma list), every occurrence, and never prints 0 for a number of eyes',
    fillTokens('Two to {max} eyes: {styles}; {styles}', cat) === 'Two to 3 eyes: Powder Burst, Splash; Powder Burst, Splash' && fillTokens('{max}', { max: 0, styles: [], one: [] }) === '1'
    && fillTokens('nothing to fill', cat) === 'nothing to fill', fillTokens('Two to {max} eyes: {styles}', cat));

  check('the black price class is named by its one style from the registry (the row of the landing and the terms)', styleName(classStyle('black')).length > 0 && STYLES[classStyle('black')].price_class === 'black', classStyle('black'));
  for (const lang of ['en', 'de', 'lt', 'hu'] as const) {
    const p = COPY[lang].pricing;
    check(`landing pricing (${lang}): the art row's note is the token {styles}, the group sentence holds {max}, the soon sentence exists, no written list and no written number of eyes`,
      p.artBackgroundNote === '{styles}' && p.severalNote.includes('{max}') && p.severalSoon.length > 20 && !/\d/.test(p.severalNote.replace('{max}', ''))
      && !/Studio Black|Couple Duo|Celestial|Deep Nebula/.test(JSON.stringify(p)) && !('studioBlack' in p) && !('duoLabel' in p) && !DASH.test(JSON.stringify(p)), JSON.stringify(p).slice(0, 300));
    check(`landing pricing (${lang}): the per-eye line prints the maximum it is given, not a written one (perEye(price, 3) holds a 3, perEye(price, 8) an 8)`,
      p.perEye('X', 3).includes('3') && !p.perEye('X', 3).includes('8') && p.perEye('X', 8).includes('8'), `${p.perEye('X', 3)} | ${p.perEye('X', 8)}`);
    const all = JSON.stringify(COPY[lang]);
    check(`the landing page (${lang}) states no number of styles ("six styles", "6 styles") and names no style it cannot sell in its head lines`,
      !/(\b(six|sechs|šeši|hat)\b|\b6\b)\s+(styles?|stile[ns]?|stili\w*|stíl\w*)/i.test(all) && !/in six|in allen sechs|visais šešiais|mind a hat/i.test(all), '');
  }

  // WP18: published by the cutover: every language gives one block and a sentence that ends with it
  check('the AI-made material sentence is written in four languages and PUBLISHED by the cutover (WP18): one block and the sentence for the end of a line, in every language',
    ['en', 'de', 'lt', 'hu'].every((l) => typeof (AI_MATERIAL as Record<string, string>)[l] === 'string' && (AI_MATERIAL as Record<string, string>)[l].length > 150
      && aiBlocks(l as 'en').length === 1 && aiBlocks(l as 'en')[0] === (AI_MATERIAL as Record<string, string>)[l] && aiSentence(l as 'en') === ` ${(AI_MATERIAL as Record<string, string>)[l]}`)
    && AI_MATERIAL_PUBLISHED === true && !DASH.test(JSON.stringify(AI_MATERIAL)), '');
  check('one LEGAL_UPDATED moved with this work (2026-10-06, WP18: the AI-made material sentence entered the terms; it was 2026-10-05 at WP12)', LEGAL_UPDATED === '2026-10-06', LEGAL_UPDATED);
  return out;
}
