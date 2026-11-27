// The soft photo and the camera-first blur refusal (the owner, 2026-11-26: a paid visitor shot ten close-ups of one eye with the front camera, nine were refused
// as too blurry at Detail 11 to 12, and she never saw a preview). What this holds:
//   1. src/try/soft.ts: an offer from the first blur refusal on when a refused photo of the visit carried a soft ticket (the owner, 2026-11-27: a visitor's
//      good first photo was refused by the pattern line, her second for another reason, and the offer that waited for two blur refusals never showed); none when
//      nothing was eligible (no soft ticket, another reason, a stale ticket); the continue goes on with the best such photo (the highest Detail), as an
//      accepted weak one whose work ticket is the soft ticket, and the page's own rules (usable, blockOf) then let it through;
//   2. the words: the blur refusal's error, retakeLine and first step start with the back camera sentence in all eight languages, the old camera step is gone
//      from the list, the soft line and button exist and are short, and nothing has a long dash;
//   3. the wiring: the page counts soft_offer and soft_go, sends soft on the restoration, and the order path never reads blocked.
import { readFileSync } from 'node:fs';
import { COPY } from '../../src/try/copy';
import { LANGS } from '../../src/shared/lang';
import { blockOf, usable, type Analysis, type Quality } from '../../src/try/shots';
import { SOFT_AFTER, isBlur, isSoft, keepSoft, offerSoft, softAnalysis, type SoftPick } from '../../src/try/soft';

type Row = [string, boolean, string?];
const read = (p: string) => readFileSync(new URL(`../../${p}`, import.meta.url), 'utf8');

const Q: Quality = {
  diameter_px: 640, sharpness: 40, fibre: 2.1, sharpness_label: 'blurry', occlusion_pct: 0, glare: false, locked: true, detail: 11, verdict: 'weak',
  message: '', tips: [], blocked: true, block_reason: 'too_blurry',
};
const refused = (q: Partial<Quality> = {}, soft = true): Analysis => ({
  ok: true, iris: { cx: 0.5, cy: 0.5, r: 0.3 }, quality: { ...Q, ...(soft ? { soft: true } : {}), ...q }, ...(soft ? { soft_ticket: 'work.soft' } : {}),
});
const TTL = 30 * 60 * 1000;

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);

  // ---- 1. the rule
  let pick: SoftPick<string> | null = null;
  let blurs = 0;
  const see = (a: Analysis, file: string, at = 0) => { if (isBlur(a)) { blurs += 1; pick = keepSoft(pick, a, file, at); } };
  check('before any blur refusal: no offer', !offerSoft(0, null, 1, TTL) && !offerSoft(0, { a: refused(), file: 'x', at: 0 }, 1, TTL));
  let first: SoftPick<string> | null = null;
  first = keepSoft(first, refused({ detail: 20 }, false), 'plain', 0);
  check('one blur refusal without a soft ticket: no offer (nothing to go on with)', first === null && !offerSoft(1, first, 1, TTL));
  see(refused({ detail: 11 }), 'one');
  check('one blur refusal with a soft ticket: the offer at once, with the soft photo held (from the second refusal on until 2026-11-27)',
    SOFT_AFTER === 1 && blurs === 1 && !!pick && offerSoft(blurs, pick, 1, TTL));
  see(refused({ detail: 12 }), 'two');
  check('the second blur refusal: the offer stays, with the better photo held', blurs === 2 && offerSoft(blurs, pick, 1, TTL) && pick!.file === 'two');
  see(refused({ detail: 9 }), 'three');
  check('... the continue uses the best soft photo of the visit (the highest Detail), not the latest', pick!.file === 'two' && pick!.a.quality!.detail === 12);
  const go = softAnalysis(pick!.a);
  check('... as an accepted weak photo: its soft ticket is the work ticket, not blocked, no reason, soft, and the page lets it through (usable, no block copy)',
    go.ticket === 'work.soft' && go.quality!.blocked === false && go.quality!.block_reason === null && go.quality!.verdict === 'weak' && go.quality!.soft === true
    && usable(go) && blockOf(go) === null && go.quality!.detail === 12);
  check('... the refused photo itself is not changed', pick!.a.ticket === undefined && pick!.a.quality!.blocked === true);
  check('... nor offered once its ticket is too old to be used', !offerSoft(2, pick, TTL + 1, TTL));

  let none: SoftPick<string> | null = null;
  let n = 0;
  for (const a of [refused({}, false), refused({ detail: 20 }, false), refused({ block_reason: 'too_far' }), refused({ block_reason: 'too_dark' })]) {
    if (isBlur(a)) n += 1;
    none = keepSoft(none, a, 'x', 0);
  }
  check('nothing eligible: two blur refusals without a soft ticket, and soft-flagged refusals for another reason, hold no soft photo and make no offer',
    n === 2 && none === null && !offerSoft(n, none, 1, TTL));
  check('... an accepted photo and a no-eye reply are neither a blur refusal nor soft',
    !isBlur(refused({ blocked: false, block_reason: null })) && !isSoft(refused({ blocked: false, block_reason: null })) && !isBlur({ ok: false }) && !isSoft({ ok: true }));
  check('... a soft flag without a ticket (or a ticket without the flag) is not soft', !isSoft({ ...refused(), soft_ticket: undefined }) && !isSoft(refused({ soft: false })));

  // ---- 2. the words
  const dash = new RegExp('[' + String.fromCharCode(0x2013, 0x2014) + ']');
  const firstSentence = (s: string) => s.slice(0, s.indexOf('.') + 1);
  check('the blur refusal says the camera first in every language: error, retakeLine and the first step start with one back camera sentence, which names the front (selfie) one',
    LANGS.every((l) => {
      const b = COPY[l].quality.blocks.too_blurry;
      const back = firstSentence(b.steps[0]);
      return /\((selfie|selfiju|szelfi|asmenukių)\)/i.test(back) && b.error.startsWith(back + ' ') && b.retakeLine.startsWith(back + ' ');
    }), LANGS.map((l) => firstSentence(COPY[l].quality.blocks.too_blurry.steps[0])).join(' | '));
  check('... the exact LT and EN sentences', COPY.lt.quality.blocks.too_blurry.steps[0].startsWith('Naudokite galinę kamerą, ne priekinę (asmenukių).')
    && COPY.en.quality.blocks.too_blurry.steps[0].startsWith('Use the back camera, not the front (selfie) one.'));
  check('... then light, focus, steady: four steps, the zoom only in the first (the old camera step is folded into it)', LANGS.every((l) => {
    const b = COPY[l].quality.blocks.too_blurry;
    return b.steps.length === 4 && b.steps.slice(1).every((s) => !/2x|2-fach/.test(s)) && /2x|2-fach/.test(b.steps[0]) && b.title.length > 0;
  }));
  check('the soft line and button in every language: short, distinct, no long dash', LANGS.every((l) => {
    const s = COPY[l].quality.soft;
    return s.line.length > 10 && s.line.length <= 80 && s.go.length > 3 && s.go.length <= 32 && !dash.test(s.line + s.go);
  }) && new Set(LANGS.map((l) => COPY[l].quality.soft.go)).size === LANGS.length
    && COPY.lt.quality.soft.line === 'Nuotrauka neryški, todėl daugiau detalių atkursime.' && COPY.lt.quality.soft.go === 'Tęsti su šia nuotrauka');
  check('... and no long dash anywhere in the blur refusal', LANGS.every((l) => !dash.test(JSON.stringify(COPY[l].quality.blocks.too_blurry))));

  // ---- 3. the wiring
  const app = read('src/try/TryApp.tsx');
  check('the page counts the offer once and the continue, and sends soft on the restoration',
    /count\('soft_offer'/.test(app) && /count\('soft_go'/.test(app) && /softCountedRef\.current = true/.test(app) && /soft: true/.test(app));
  check('the counter knows the two new steps', /'soft_offer' \| 'soft_go'/.test(read('src/shared/counter.ts')));
  check('the order path never reads blocked (a soft photo is bought like any weak one)', !/\.blocked\b|\bblocked:|block_reason/.test(read('src/try/checkout.ts').replace(/\/\*[^]*?\*\//g, '')));
  return out;
}
