// The anonymous counter, the page's half (2026-10-20): src/shared/counter.ts sends its beacons only when /api/health says counter true, holds back what comes before that answer, drops it on
// a no, never throws; and the tools call it where the owner's list says (/try opened, a photo chosen, the preview shown, the buy card that cannot be bought, the buy
// button, the order page) and nowhere else (not the admin, not the legal pages). Pure page code, loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results.
import { readFileSync } from 'node:fs';
import { count, note } from '../../src/shared/counter';

type Row = [string, boolean, string?];
const read = (p: string) => readFileSync(new URL(`../../${p}`, import.meta.url), 'utf8');
const tick = () => new Promise<void>((r) => setTimeout(r, 15));

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);

  const g = globalThis as unknown as Record<string, unknown>;
  g.location = { search: '?utm_source=fb&utm_medium=paid&utm_campaign=se-p0-test&utm_term=lt-a1-eye&utm_content=a1-lt-s1' };      // the page the tab was opened on
  g.document = { referrer: '' };
  g.sessionStorage = { getItem: () => null, setItem: () => undefined };
  const sent: { url: string; type: string; body: Promise<string> }[] = [];
  const nav = globalThis.navigator as unknown as Record<string, unknown>;
  const had = Object.getOwnPropertyDescriptor(nav, 'sendBeacon');
  let mode: 'ok' | 'throws' = 'ok';
  Object.defineProperty(nav, 'sendBeacon', {
    configurable: true,
    value: (url: string, data: Blob) => {
      if (mode === 'throws') throw new Error('no beacon');
      sent.push({ url, type: data.type, body: data.text() });
      return true;
    },
  });
  try {
    const A = { count, note };
    A.count('try', 'lt', 'lt');
    A.count('photo', 'lt', 'lt');
    await tick();
    check('before /api/health has answered, a beacon waits and nothing is sent', sent.length === 0, String(sent.length));

    A.note(true);
    await tick();
    const bodies = await Promise.all(sent.map((s) => s.body));
    check('the answer counter true sends what waited, in order, once each', sent.length === 2 && bodies.map((b) => JSON.parse(b).hit).join() === 'try,photo', bodies.join(' '));
    check('a beacon is a POST (sendBeacon) of JSON to /api/checkout, which is what the server\'s content type gate asks for', sent.every((s) => s.url === '/api/checkout' && s.type === 'application/json'), JSON.stringify(sent.map((s) => [s.url, s.type])));
    check('the body is the step, the page language and market and the campaign code, nothing else (no URL, no referrer, no identifier)', bodies[0] === '{"hit":"try","lang":"lt","market":"lt","camp":"utm_source=fb&utm_medium=paid&utm_campaign=se-p0-test&utm_term=lt-a1-eye&utm_content=a1-lt-s1"}', bodies[0]);

    A.count('result', 'de', 'eu', { eyes: 2, took: 31000 });
    await tick();
    check('after a yes a beacon goes out at once, and what the step adds (eyes, took) travels with it', sent.length === 3 && (await sent[2].body) === '{"hit":"result","lang":"de","market":"eu","eyes":2,"took":31000,"camp":"utm_source=fb&utm_medium=paid&utm_campaign=se-p0-test&utm_term=lt-a1-eye&utm_content=a1-lt-s1"}', await sent[2]?.body);

    A.note(true);
    A.note(false);
    await tick();
    check('the answer is given once: a later answer changes nothing and nothing is sent twice', sent.length === 3);

    mode = 'throws';
    const onRej = () => undefined;       // the failed beacon is a rejected promise nobody awaits: the browser logs it, the page never sees it
    process.on('unhandledRejection', onRej);
    let thrown: unknown = null;
    try { A.count('soon', 'en', 'eu'); } catch (e) { thrown = e; }
    await tick();
    process.off('unhandledRejection', onRej);
    mode = 'ok';
    check('a beacon that cannot be sent is the counter\'s failure alone: count() throws nothing at the page', thrown === null);

  } finally {
    if (had) Object.defineProperty(nav, 'sendBeacon', had); else delete nav.sendBeacon;
  }

  // where the pages count
  const landing = read('src/main.tsx') + read('src/landing/ordering.ts');
  const tryApp = read('src/try/TryApp.tsx');
  const orderApp = read('src/order/OrderApp.tsx');
  check('the landing page does not load this module at all (its beacon is the head script, src/landing/shell/scripts.ts counterScript: the landing\'s JavaScript does not grow)', !/shared\/counter/.test(landing));
  check('/try counts: opened, a photo chosen (not the sample eye), the restored eye on screen with the time since the photo, the buy card that cannot be bought (once), the buy button',
    /count\('try', T\.lang, currentMarket\(\)\)/.test(tryApp) && /count\('photo', T\.lang, currentMarket\(\)\)/.test(tryApp) && /if \(!sample\) \{ count\('result'/.test(tryApp) && /took: Date\.now\(\) - photoAt/.test(tryApp)
    && /count\('soon'/.test(tryApp) && /soonRef/.test(tryApp) && /count\('buy'/.test(tryApp) && /noteCounter\(h\.counter\)/.test(tryApp));
  check('the order page counts itself (not the withdrawal form) and reads the answer of /api/health', /count\('order', lang, market\)/.test(orderApp) && /LINK && !WITHDRAW_MODE/.test(orderApp) && /noteCounter\(h\?\.counter\)/.test(orderApp));
  const others = ['src/admin/AdminApp.tsx', 'src/legal/main.tsx', 'src/legal/LegalApp.tsx', 'src/order/WithdrawPanel.tsx', 'src/order/withdraw.ts'].map((p) => [p, read(p)] as const);
  check('the admin panel, the legal pages and the withdrawal form do not count', others.every(([, t]) => !/shared\/counter/.test(t)), others.filter(([, t]) => /shared\/counter/.test(t)).map(([p]) => p).join());
  const mod = read('src/shared/counter.ts').replace(/[/][*][\s\S]*?[*][/]/g, '').replace(/[/][/].*$/gm, '');
  check('the module keeps nothing in the browser but the campaign code (no localStorage, no cookie, no IndexedDB) and sends only to /api/checkout, by sendBeacon',
    !/localStorage|cookie|indexedDB/.test(mod) && (mod.match(/sendBeacon\(/g) ?? []).length === 1 && /sendBeacon\('[/]api[/]checkout'/.test(mod));
  return out;
}
