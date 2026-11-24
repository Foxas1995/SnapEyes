// The largest print the site suggests is ONE size, said the same everywhere (the owner's decision of 2026-11-24: 60 x 60 cm; the landing said 50 x 50 cm while
// the /try page said "up to 60 x 60 cm" under the artwork and the print offer sold a 60 cm acrylic). The number lives in src/landing/sizeScale.ts (the last of
// SIZES); the copy restates it in words in eight languages (the facts {printMax} and {printMaxCm}, the last rung of the size guide, the density of the FAQ answer
// "Can I print it?"), the /try page in a sentence of its own, the print offer in its largest product. This file holds them to each other, so that the next change
// of the size cannot leave one of them behind. The density is stated as a number (4096 px / (60 cm / 2.54) = 173 pixels per inch), not praised.
// Pure page code, loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results, prints nothing.
import en from '../../src/landing/copy/en.json';
import de from '../../src/landing/copy/de.json';
import lt from '../../src/landing/copy/lt.json';
import hu from '../../src/landing/copy/hu.json';
import hr from '../../src/landing/copy/hr.json';
import fi from '../../src/landing/copy/fi.json';
import et from '../../src/landing/copy/et.json';
import lv from '../../src/landing/copy/lv.json';
import type { LandingCopy } from '../../src/landing/copy/types';
import { DEFAULT_SIZE, FILE_PX, FLOOR, PERSON, SIZES, SOFA, ppi, squares, viewBoxFor } from '../../src/landing/sizeScale';
import { SCENE_SIZE } from '../../src/landing/wallScenes';
import { COPY as TRY } from '../../src/try/copy';
import { printProducts } from '../../src/shared/prints';

type Row = [string, boolean, string?];
const COPIES = { en, de, lt, hu, hr, fi, et, lv } as unknown as Record<string, LandingCopy>;
const LANGS = ['en', 'de', 'lt', 'hu', 'hr', 'fi', 'et', 'lv'] as const;
/** A no-break space reads as a space here: the copy writes "60 cm" with one so that the number and its unit never part. */
const plain = (s: string) => s.replace(/ /g, ' ');

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);
  const MAX = SIZES[SIZES.length - 1];

  check('the size guide: 20, 30, 40 and 60 cm, the largest chosen at first, and the density of the 4096 px file at each is 520, 347, 260 and 173 pixels per inch',
    SIZES.join() === '20,30,40,60' && MAX === 60 && DEFAULT_SIZE === MAX && FILE_PX === 4096 && SIZES.map((cm) => ppi(cm)).join() === '520,347,260,173',
    SIZES.map((cm) => ppi(cm)).join());

  // the drawing is to scale and still fits: no square on another, the row centred over the sofa, clear of the person, above the sofa, inside the phone's crop
  const sq = squares();
  const gaps = sq.slice(1).map((q, i) => Math.round(q.x - (sq[i].x + sq[i].side)));
  const left = sq[0].x, right = sq[sq.length - 1].x + sq[sq.length - 1].side;
  const [vx, vy, vw] = viewBoxFor(true);
  check('the drawing: the four squares 34 units apart, their row centred over the sofa, clear of the person, above the sofa\'s back and inside the crop a phone shows',
    gaps.every((g) => g === 34) && Math.abs((left + right) / 2 - (SOFA.x + SOFA.w / 2)) < 0.01 && right < PERSON.x - 72 && sq.every((q) => q.y + q.side + 30 < FLOOR - SOFA.h)
      && sq.every((q) => q.x > vx && q.y > vy && q.x + q.side < vx + vw), `gaps ${gaps.join()}, row ${left} to ${right}, top ${Math.min(...sq.map((q) => q.y))}`);

  for (const l of LANGS) {
    const c = COPIES[l];
    const printit = c.faq.items.find((i) => i.id === 'printit') as { a: string; aPrints?: string };
    const answers = [printit.a, printit.aPrints ?? ''];
    const last = c.sizes.rungs[c.sizes.rungs.length - 1], third = c.sizes.rungs[c.sizes.rungs.length - 2];
    check(`${l}: the copy's facts say ${MAX} x ${MAX} cm and ${MAX} cm, the size guide's rungs are the drawing's sizes and its title names the fact`,
      plain(c.facts.printMax) === `${MAX} × ${MAX} cm` && plain(c.facts.printMaxCm) === `${MAX} cm` && c.sizes.rungs.map((r) => r.cm).join() === SIZES.join()
        && c.sizes.title.includes('{printMax}'), `${plain(c.facts.printMax)} / ${plain(c.facts.printMaxCm)} / ${c.sizes.rungs.map((r) => r.cm).join()}`);
    check(`${l}: the largest rung does not borrow the word of the 40 cm one (260 pixels per inch): at 173 it says from where the print is sharp`,
      last.cm === MAX && last.b !== third.b && last.b.length > third.b.length, `${third.b} / ${last.b}`);
    check(`${l}: "Can I print it?" in both wordings names the density of the largest size as a number (${ppi(MAX)}) and of 30 cm (${ppi(30)}), lists ${MAX} cm among `
      + 'its examples, recommends up to {printMax} and says what lies above {printMaxCm}; the 50 cm and its 208 are gone',
      answers.every((a) => a.includes(String(ppi(MAX))) && a.includes(String(ppi(30))) && plain(a).includes(`${MAX} cm`) && !/\b208\b/.test(a) && !/\b50\b/.test(a)
        && a.split('{printMax}').length === 2 && a.split('{printMaxCm}').length === 3));
    const t = TRY[l].result;
    check(`${l}: the /try page says the same under the artwork (${MAX} x ${MAX} cm for the square file, ${MAX} cm on the longest side otherwise)`,
      plain(t.previewFile(true)).includes(`${MAX} x ${MAX} cm`) && plain(t.previewFile(false)).includes(`${MAX} cm`) && !t.previewFile(true).includes('50') && t.previewFile(true).includes('4096'),
      t.previewFile(true));
  }

  const sold = printProducts(false).map((p) => p.cm);
  check('no print is sold larger than the size the page suggests, and the largest one sold is that size',
    sold.length > 0 && Math.max(...sold) === MAX, sold.join());
  // a caption under a wall picture names the size the artwork is DRAWN at in that picture (40 to 55 cm), not the largest print: it stays "about 50 cm"
  check('the wall captions keep the size of their pictures (about 50 cm), written like a fact of the copy, and do not follow the largest print',
    SCENE_SIZE === '50 cm' && LANGS.every((l) => COPIES[l].facts.printMaxCm !== SCENE_SIZE && COPIES[l].wall.captionsSize.acrylic.includes('{size}')));
  return out;
}
