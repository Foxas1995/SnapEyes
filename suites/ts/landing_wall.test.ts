// The wall chapter, the rooms, the gallery's wall views, the edge close-up and the closing scene show only what is sold (the owner's decision of 2026-11-25:
// "taip, dėk naujus vaizdus į Tavo siena"). Until that day the stage showed aluminium in an office, a framed print with a mat, 3:2 plates and standoff screws, and
// no poster; the print offer (api/_lib/print_offer.py) sells acrylic glass 30/40/60 cm, glossy metal 30/40/60 cm, canvas on a wooden stretcher frame 40/60 cm, a
// 50 cm poster, acrylic blocks of 10 and 20 cm and a keyring, all square but the keyring. This file holds the page's pictures and words to that.
// Pure page code, loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results, prints nothing.
import { readFileSync } from 'node:fs';
import en from '../../src/landing/copy/en.json';
import de from '../../src/landing/copy/de.json';
import lt from '../../src/landing/copy/lt.json';
import hu from '../../src/landing/copy/hu.json';
import hr from '../../src/landing/copy/hr.json';
import fi from '../../src/landing/copy/fi.json';
import et from '../../src/landing/copy/et.json';
import lv from '../../src/landing/copy/lv.json';
import type { LandingCopy } from '../../src/landing/copy/types';
import { GALLERY, MORE, STAGE, WALL_THUMBS } from '../../src/landing/assets.data';
import { ARTS, DEFAULT_MATERIAL, MATERIALS, artFor, glintFor, hasScene } from '../../src/landing/wallScenes';
import { printProducts } from '../../src/shared/prints';

type Row = [string, boolean, string?];
const COPIES = { en, de, lt, hu, hr, fi, et, lv } as unknown as Record<string, LandingCopy>;
const LANGS = ['en', 'de', 'lt', 'hu', 'hr', 'fi', 'et', 'lv'] as const;
const DASH = new RegExp('[' + [0x2012, 0x2013, 0x2014, 0x2015].map((c) => String.fromCharCode(c)).join('') + ']');
/** The words of things that are not sold, in the eight languages: aluminium, a framed print, a mat, a standoff. */
const NOT_SOLD = /alumin|alumiin|alumīn|framed|gerahmt|įrėmin|keretez|uokviren|kehystet|raamitud|ierāmēt|passepartout|paspart|paspis|standoff|abstandhalter|távtartó|distancer|seinäkiinnike|distantshoidik|distancer/i;
/** A label on a picture: removed on purpose (2026-11-24 and 2026-11-25). */
const LABEL = /visuali|vizuali|havainnekuv|example photo|pavyzdinė nuotrauka|beispielfoto/i;

const strings = (o: unknown): string[] => (typeof o === 'string' ? [o] : Array.isArray(o) ? o.flatMap(strings) : o && typeof o === 'object' ? Object.values(o).flatMap(strings) : []);

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);
  const sold = printProducts(false);
  const kinds = [...new Set(sold.map((p) => p.kind))];

  check('the stage\'s materials are exactly the kinds sold that hang or stand (not the keyring, which the rooms show) and the phone, in the order acrylic glass, glossy metal, canvas, poster, block, phone; no framed print; it opens on glossy metal',
    MATERIALS.join() === 'acrylic,metal,canvas,poster,block,phone' && kinds.filter((k) => k !== 'keyring').every((k) => (MATERIALS as readonly string[]).includes(k))
      && MATERIALS.every((m) => m === 'phone' || kinds.includes(m as never)) && DEFAULT_MATERIAL === 'metal' && Object.keys(STAGE).join() === MATERIALS.join(),
    `${MATERIALS.join()} / sold ${kinds.join()}`);

  const room = (m: string, a: string) => STAGE[m as keyof typeof STAGE][a as never] as { base: string } | undefined;
  check('acrylic glass, glossy metal and canvas are the same sofa room at 60 cm (a pick changes only the print), with our own eye, Universe and the square trio for the family; the poster lies on a table, the block stands on a desk',
    ['eye', 'universe', 'family'].every((a) => {
      const art = a === 'eye' ? 'radiance' : a === 'family' ? 'trio' : a;
      return room('acrylic', a)?.base === `m/living_acrylic60__${art}__tight` && room('metal', a)?.base === `m/living_metal60__${art}__tight` && room('canvas', a)?.base === `m/living_canvas60__${art}__tight`
        && room('block', a)?.base === `m/desk_block20__${art}__tight`;
    }) && room('poster', 'eye')?.base === 'm/table_poster50__radiance__tight' && room('poster', 'universe')?.base === 'm/table_poster50__universe__tight',
    JSON.stringify(STAGE.metal));

  check('the pair and every 3:2 artwork are off the prints: the pair is on the phone only, the poster has no family; a pick of a print while the pair is chosen falls back to one eye; the phone keeps its four scenes',
    ARTS.join() === 'eye,universe,family,collision' && MATERIALS.every((m) => (m === 'phone') === hasScene(m, 'collision')) && !hasScene('poster', 'family')
      && artFor('acrylic', 'collision') === 'eye' && artFor('phone', 'collision') === 'collision' && Object.keys(STAGE.phone).length === 4
      && !JSON.stringify({ STAGE, MORE, GALLERY }).match(/3x2|framed|office_|hotel_|cafe_|shelf_|macro_|gallery_/) && WALL_THUMBS.family === 'art/wallthumb_family_96',
    JSON.stringify(Object.fromEntries(MATERIALS.map((m) => [m, Object.keys(STAGE[m])]))));

  check('the glint (the light band of a polished print) is on acrylic glass and glossy metal only, one box (the 60 cm print over the sofa), never on canvas, the poster, the block or the phone',
    JSON.stringify(glintFor('acrylic')) === JSON.stringify(glintFor('metal')) && !!glintFor('acrylic') && (['canvas', 'poster', 'block', 'phone'] as const).every((m) => glintFor(m) === null),
    JSON.stringify(glintFor('acrylic')));

  check('"More ways to see it" shows five prints that are sold, at the size drawn: glossy metal 40 cm over a sideboard, canvas 40 cm in a hall, the 20 and 10 cm blocks, the 20 cm block in hands, the keyring',
    MORE.map((r) => `${r.id}=${r.base}`).join() === 'sideboard=m/sideboard_metal40__universe__tight,hall=m/hall_canvas40__radiance__tight,blocks=m/desk_block20and10__radiance__tight,hands=m/hands_block20__radiance__tight,keyring=m/table_keyring__radiance__tight'
      && LANGS.every((l) => COPIES[l].more.scenes.map((s) => s.id).join() === MORE.map((r) => r.id).join()),
    MORE.map((r) => r.id).join());

  check('the gallery\'s wall view: the two single styles of our own eye on a square 60 cm acrylic glass print; the pair has none (its picture was a 3:2 plate)',
    GALLERY.one.filter((t) => t.wallOwn).map((t) => `${t.id}=${t.wallOwn!.base}`).join() === 'radiance=m/wall_acrylic60__radiance__sq,universe=m/wall_acrylic60__universe__sq'
      && [...GALLERY.two, ...GALLERY.family].every((t) => !t.wall));

  const closeups = readFileSync('src/landing/CloseUps.tsx', 'utf8'), closing = readFileSync('src/landing/ClosingScene.tsx', 'utf8');
  check('the edge close-up is the corner of an acrylic glass print without a screw, the closing scene the study with a square 60 cm print',
    /asset\('m\/closeup_acrylic__universe__wide'/.test(closeups) && /asset\('m\/study_acrylic60__radiance__wide'/.test(closing) && !/macro_acrylic|study_acrylic_3x2/.test(closeups + closing));

  for (const l of LANGS) {
    const c = COPIES[l];
    // the line under the stage that says whose eyes the family and the pair show (wall.eyesNote) is not a label on a picture and stays as the owner left it
    const { eyesNote: _whose, ...wall } = c.wall;
    const words = strings([wall, c.more, c.closeups.edgeTitle, c.closeups.edgeAlt, c.final.imageAlt, c.faq.items.find((i) => i.id === 'material')]);
    const bad = words.filter((s) => NOT_SOLD.test(s) || LABEL.test(s) || DASH.test(s) || /\{size\}/.test(s) && /about|etwa|maždaug|kb\.|otprilike|noin|umbes|apmēram/i.test(s));
    check(`${l}: the words of the wall, the rooms, the edge and the closing scene name no aluminium, no framed print, no mat, no standoff, carry no picture label and no dash, and a caption states its size without "about"; `
      + 'the compare table has the four wall kinds that are sold and says every print is square',
      bad.length === 0 && c.wall.compare.cols.length === 4 && c.wall.compare.rows.every((r) => r.v.length === 4) && Object.keys(c.wall.materials).join() === MATERIALS.join()
        && Object.keys(c.wall.captionsSize).join() === MATERIALS.filter((m) => m !== 'phone').join() && Object.keys(c.wall.arts).join() === ARTS.join(),
      bad.join(' | '));
  }
  const m = en.wall.materials;
  check('en: the canvas is on a wooden stretcher frame and ready to hang (no frame needed), the poster comes without a frame and rolled, the block stands on a shelf or desk',
    m.canvas.facts.join('|') === 'On a wooden stretcher frame|Ready to hang|No frame needed' && m.poster.facts.join('|') === 'Printed on paper|Without a frame|Arrives rolled'
      && m.block.facts.includes('Stands on a shelf or desk') && m.metal.n === 'Glossy metal' && m.acrylic.n === 'Acrylic glass');
  return out;
}
