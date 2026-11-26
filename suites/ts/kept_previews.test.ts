// The page Peržiūros of /admin (src/admin/Previews.tsx; api/_lib/keep.py, api/_lib/ops.py a_kept; the owner's decision of 2026-11-26): a step's outcome in words (an
// accepted photo with its verdict, a refused one with the reason in Lithuanian, a restoration and its gate, a shown preview and its style), its codes on one line
// (the numbers measured and the anonymous context), the page drawn with a visit, and the photo step's visit (src/shared/visit.ts: random, per page load, never
// stored). Pure page code, loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results.
import { readFileSync } from 'node:fs';
import { codesText, outcomeText, type KeptStep } from '../../src/admin/Previews';
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
  return out;
}
