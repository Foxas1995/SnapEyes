// The page Peržiūros of /admin (src/admin/Previews.tsx; api/_lib/keep.py, api/_lib/ops.py a_kept; the owner's decision of 2026-11-26): a step's outcome in words (an
// accepted photo with its verdict, a refused one with the reason in Lithuanian, a restoration and its gate, a shown preview and its style), its codes on one line
// (the numbers measured and the anonymous context), the page drawn with a visit, and the photo step's visit (src/shared/visit.ts: random, per page load, never
// stored). Pure page code, loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results.
import { readFileSync } from 'node:fs';
import { areaText, attemptsOf, codesText, contextText, missingText, outcomeText, stepTime, type KeptStep } from '../../src/admin/Previews';
import { checkoutLegal } from '../../src/shared/legal';
import { TAB_GROUPS } from '../../src/admin/AdminApp';
import { VISIT } from '../../src/shared/visit';

type Row = [string, boolean, string?];

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);
  const step = (meta: Record<string, unknown> | null, s: KeptStep['step'] = 'analyze'): KeptStep => ({ time: '101530', step: s, meta, pictures: { photo: 'https://x/p.jpg' } });

  const acc = outcomeText(step({ outcome: 'accepted', verdict: 'good' }));
  const ref = outcomeText(step({ outcome: 'refused', reason: 'too_blurry' }));
  const noEye = outcomeText(step({ outcome: 'refused', reason: 'no_eye' }));
  const res = outcomeText(step({ outcome: 'restored', gate: 'lid' }, 'enhance'));
  const shown = outcomeText(step({ outcome: 'shown', style: 'solo.powder' }, 'compose'));
  check('a step\'s outcome in words: accepted with its verdict, refused with the reason in Lithuanian (red), a restoration whose gate failed (red), a shown preview with its style',
    acc?.text === 'Priimta (Gera)' && !acc.bad && ref?.text === 'Atmesta: Per neryški' && ref.bad && noEye?.text === 'Atmesta: Akies nerasta'
      && res?.text === 'Restauruota, vartai: lid' && res.bad && !!shown && shown.text.startsWith('Parodyta: ') && !shown.bad
      && outcomeText(step(null)) === null, JSON.stringify([acc, ref, noEye, res, shown]));
  const codes = codesText(step({ outcome: 'accepted', detail: 92, diameter_px: 570, glare_on_fibres_pct: 0, source: 'camera',
    ctx: { src: 'fb', med: 'paid', cmp: 'spring', dev: 'ios', br: 'safari', lang: 'lt', cc: 'lt' } }));
  check('its codes on one line: the detail, the iris size, the reflection, the source and the anonymous context (campaign, device, browser, language, country)',
    codes.includes('detalumas 92') && codes.includes('rainelė 570 px') && codes.includes('camera') && codes.includes('LT') && codes.includes('Lietuvių'), codes);
  check('the page is in the admin menu as Peržiūros, among the visitors\' pages', TAB_GROUPS.some(([g, pages]) => g === 'Lankytojai ir reklama' && pages.some(([id, l]) => id === 'previews' && l === 'Peržiūros')));
  check('the visit of the photo step: a random value made when the page loads (time and 10 random characters), never put in storage or a cookie',
    /^[a-z0-9]{6,12}-[a-z0-9]{6,12}$/.test(VISIT) && !/localStorage|sessionStorage|document\.cookie/.test(readFileSync('src/shared/visit.ts', 'utf8')), VISIT);
  const tryApp = readFileSync('src/try/TryApp.tsx', 'utf8');
  const composeApi = readFileSync('src/try/composeApi.ts', 'utf8');
  const adminApi = readFileSync('src/admin/api.ts', 'utf8');
  check('the photo step sends the visit with analyze, deglare and enhance (TryApp post) and compose (composeApi); the owner\'s laboratory says nokeep',
    tryApp.includes('visit: VISIT, ...body') && composeApi.includes('visit: VISIT') && adminApi.includes('nokeep: true'));
  const failed = outcomeText(step({ outcome: 'failed', error: 'RuntimeError' }, 'enhance'));
  check('a step that failed (the model failed after the crop was kept): "Nepavyko" with the class of the error, in red', failed?.text === 'Nepavyko (RuntimeError)' && failed.bad, JSON.stringify(failed));
  const a0 = areaText({ area_mb: 123.4, today_mb: 12, cap_mb: 500, visits_today: 40, visits_day_max: 100, held: null });
  const a1 = areaText({ area_mb: 720, today_mb: 300, cap_mb: 500, visits_today: 60, visits_day_max: 100, held: 'cap' });
  const a2 = areaText({ area_mb: 200, today_mb: 150, cap_mb: 500, visits_today: 100, visits_day_max: 100, held: 'day' });
  check('the area line: the size against the cap and the visits of today against the ceiling; when the cap or the ceiling of the day holds keeping back, it says so and names the setting that raises it',
    a0.text.includes('123.4 MB iš 500 MB') && a0.text.includes('40 iš 100') && a0.held === null && !!a1.held && a1.held.includes('SNAPEYES_KEEP_MAX_MB')
      && !!a2.held && a2.held.includes('SNAPEYES_KEEP_VISITS_DAY') && areaText(undefined).held === null, JSON.stringify([a0, a1, a2]));
  const local = new Date('2026-11-26T10:26:17Z');
  const want = [local.getHours(), local.getMinutes(), local.getSeconds()].map((n) => String(n).padStart(2, '0')).join(':');
  check('the time of a step is shown in the time zone of the browser (the files carry UTC); without a day, the UTC time as it is',
    stepTime('2026-11-26', '102617') === want && stepTime(null, '102617') === '10:26:17', `${stepTime('2026-11-26', '102617')} / ${want}`);
  const unread = missingText({ ...step(null), meta_error: true });
  const broke = missingText(step(null));
  check('a step whose record could not be read now says so (not red) and asks to refresh; only a step with no record at all "broke off" (red)',
    unread.text.includes('nepavyko įkelti') && !unread.bad && broke.text.includes('nutrūko') && broke.bad, JSON.stringify([unread, broke]));
  const st = (time: string, s: KeptStep['step']): KeptStep => ({ time, step: s, meta: { outcome: 'x' }, pictures: {} });
  // the tab of the owner on 2026-11-26: four photos and a result, then four more photos seven minutes later
  const at = attemptsOf([st('150157', 'analyze'), st('150157', 'analyze'), st('150158', 'analyze'), st('150212', 'analyze'), st('150306', 'enhance'), st('150322', 'compose'),
    st('150936', 'analyze'), st('150936', 'analyze'), st('150936', 'analyze'), st('150945', 'analyze')]);
  check('a visit is shown as attempts, the newest first: the photos of one go together, then the restoration and the previews that followed; a photo after a result starts the next attempt',
    at.length === 2 && at[0].n === 2 && at[0].time === '150936' && at[0].photos.length === 4 && at[0].rest.length === 0
      && at[1].n === 1 && at[1].photos.length === 4 && at[1].rest.map((x) => x.step).join() === 'enhance,compose', JSON.stringify(at.map((a) => [a.n, a.time, a.photos.length, a.rest.length])));
  const gap = attemptsOf([st('100000', 'analyze'), st('100020', 'analyze'), st('100200', 'analyze')]);
  check('photos sent after a pause are another attempt (two shots of one go, then a retake two minutes later), and steps without a photo first still make one',
    gap.length === 2 && gap[0].photos.length === 1 && gap[1].photos.length === 2 && attemptsOf([st('100000', 'compose')]).length === 1 && attemptsOf([]).length === 0, JSON.stringify(gap.map((a) => a.photos.length)));
  const withCtx = step({ outcome: 'accepted', detail: 9, ctx: { src: 'fb', med: 'paid', dev: 'android', br: 'fb', lang: 'lt', cc: 'lt' } });
  check('the context is written once for an attempt: a photo tile carries its numbers only, the context line the campaign, device, browser, language and country',
    !codesText(withCtx, false).includes('LT') && codesText(withCtx, false).includes('detalumas 9') && contextText(withCtx).includes('LT') && contextText(withCtx).includes('Lietuvių') && contextText(undefined) === '',
    `${codesText(withCtx, false)} | ${contextText(withCtx)}`);
  const us = JSON.stringify(checkoutLegal('en', 'us').photoNotice);
  const eu = JSON.stringify(checkoutLegal('en', 'eu').photoNotice);
  check('the line of the photo step: the US one as before (only to make the artwork: a US visitor is not kept), the EU one without only and without the 30 days', us.includes('used only to make your artwork')
    && !us.includes('30') && eu.includes('Your photo is used to make your artwork.') && !eu.includes('30') && !eu.includes('only'), `${us} | ${eu}`);
  return out;
}
