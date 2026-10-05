// Review of WP12: the owner's order detail reads the names of a new order (a list, one per eye) as well as the old text (src/admin/orderWords.ts), and the page sends the
// second identity of the artwork on screen, plan8_core, beside plan8 (src/try/composeApi.ts pictureOf, src/try/checkout.ts runCheckout: api/checkout.py takes its own plan
// when only the choices the pixels decided differ, and only then). Pure page code, loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results.
import { namesText } from '../../src/admin/orderWords';
import { pictureOf } from '../../src/try/composeApi';
import { runCheckout } from '../../src/try/checkout';
import type { Eye } from '../../src/try/multi';

type Row = [string, boolean, string?];

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);

  check('namesText: a list of names is "Anna, Max" (what the order detail prints, never a bare list or "[object Object]")', namesText(['Anna', 'Max']) === 'Anna, Max' && namesText(['Jūratė']) === 'Jūratė');
  check('namesText: an old order\'s text is the text itself, trimmed', namesText('Anna;Max') === 'Anna;Max' && namesText('  Anna  ') === 'Anna');
  check('namesText: nothing, empty entries, numbers and objects are no names', namesText(undefined) === '' && namesText(null) === '' && namesText([]) === '' && namesText(['', ' ', 'Max']) === 'Max'
    && namesText(['A', 3, null, { a: 1 }, 'B']) === 'A, B' && namesText(12) === '' && namesText({ a: 1 }) === '');

  const pic = pictureOf({ image: 'QUJD', width: 1024, height: 683, layout: 'pair', canvas: '3:2', design_used: 'infinity', plan8: 'abcd1234', plan8_core: 'ef567890', opts: {} });
  const old = pictureOf({ image: 'QUJD', width: 10, height: 10, plan8: 'abcd1234' });
  check('pictureOf: the picture carries plan8_core when the server says it, and null when it does not (an older server)', !!pic && pic.plan8 === 'abcd1234' && pic.plan8Core === 'ef567890' && !!old && old.plan8Core === null
    && pictureOf({ image: 'QUJD', plan8_core: 12 })?.plan8Core === null);

  const mk = (id: string): Eye => ({
    id, before: 'data:image/jpeg;base64,AAAA', image: `DISPLAY-${id}`, thumb: 'data:image/jpeg;base64,BBBB', pad: 1.12, fallback: false, usedSr: false, stored: false, glarePct: 0, sample: false,
    colourOff: false, sealed: `SEALED-${id}`, draft: { crop: `CROP-${id}`, ticket: 'work.1.x', until: Date.now() + 600_000 },
  });
  type Rec = { path: string; body?: Record<string, unknown> };
  const rec: Rec[] = [];
  const api = (() => async (path: string, o: { body?: Record<string, unknown> } = {}) => {
    rec.push({ path, body: o.body });
    if (path === '/api/order') return { ok: true, status: 200, data: { order: 'ord1', k: 'k1', eye: 1, created: true, expires_at: Math.floor(Date.now() / 1000) + 7200 }, reason: '', error: '', retry: false, retryAfter: 0 };
    return { ok: true, status: 200, data: { url: 'https://checkout.stripe.test/x', order: 'ord1', expires_at: 1 }, reason: '', error: '', retry: false, retryAfter: 0 };
  })() as never;
  const base = { eyes: [mk('a')], style: 'grp.collision', layout: 'trio', names: 'Anna', lang: 'en' as const, ref: null };
  const last = () => rec.filter((r) => r.path === '/api/checkout').at(-1)?.body ?? {};
  await runCheckout({ ...base, plan8: 'abcd1234', plan8Core: 'ef567890' }, () => undefined, api);
  check('runCheckout sends plan8_core beside plan8', last().plan8 === 'abcd1234' && last().plan8_core === 'ef567890', JSON.stringify(last()));
  rec.length = 0;
  await runCheckout({ ...base, plan8: 'abcd1234' }, () => undefined, api);
  check('runCheckout sends no plan8_core when the picture had none (an older server: the old request)', last().plan8 === 'abcd1234' && !('plan8_core' in last()), JSON.stringify(last()));
  rec.length = 0;
  await runCheckout({ ...base, plan8Core: 'ef567890' }, () => undefined, api);
  check('runCheckout sends neither when there is no plan8 (the core alone compares nothing)', !('plan8' in last()) && !('plan8_core' in last()), JSON.stringify(last()));
  return out;
}
