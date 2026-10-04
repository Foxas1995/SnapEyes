// wave-pv: the page side of the sealed preview (src/try/multi.ts sealedFor, src/try/checkout.ts runCheckout's draft
// upload), with a fake API. Loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results, prints nothing.
import { sealedFor, composeSide, keptSealed, type Eye } from '../../src/try/multi';
import { runCheckout, takeSnapshot, saveSnapshot } from '../../src/try/checkout';
import { COPY } from '../../src/try/copy';

type Rec = { path: string; body?: Record<string, unknown> };

export async function run(): Promise<Array<[string, boolean, string?]>> {
  const out: Array<[string, boolean, string?]> = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);

  const full = 'S1024', m768 = 'S768', m560 = 'S560';
  const e = { sealed: full, sealedSizes: { '768': m768, '560': m560 } };
  check('sealedFor: 1-2 eyes take the full sealed iris', sealedFor(e, 1) === full && sealedFor(e, 2) === full);
  check('sealedFor: 3-4 eyes take 768, 5-8 take 560', sealedFor(e, 3) === m768 && sealedFor(e, 4) === m768 && sealedFor(e, 5) === m560 && sealedFor(e, 8) === m560);
  check('sealedFor: a kept copy with one size only still composes (nearest size)',
    sealedFor({ sealedSizes: { '768': m768 } }, 2) === m768 && sealedFor({ sealedSizes: { '768': m768 } }, 6) === m768
    && sealedFor({ sealedSizes: { '560': m560 } }, 3) === m560 && sealedFor({ sealed: full }, 7) === full);
  check('sealedFor: an eye from an older server (no sealed copy) -> null (the images path)', sealedFor({}, 1) === null && sealedFor({}, 5) === null);
  check('composeSide unchanged', composeSide(2) === null && composeSide(3) === 768 && composeSide(5) === 560);
  // the smaller copy kept for the way back from Stripe (TryApp keepForReturn): 1-2 eyes drop the 560, 3+ eyes the full
  // one, so any number of eyes on the way back still composes from a copy of at least 768 px where one was kept
  const small12 = { sealed: full, sealedSizes: { '768': m768 } }, small3 = { sealedSizes: { '768': m768, '560': m560 } };
  check('sealedFor on a kept 1-2 eye copy: full for 1-2, 768 for 3-8',
    sealedFor(small12, 1) === full && sealedFor(small12, 3) === m768 && sealedFor(small12, 7) === m768);
  check('sealedFor on a kept 3+ eye copy: 768 for 1-4 eyes, 560 for 5-8',
    sealedFor(small3, 1) === m768 && sealedFor(small3, 2) === m768 && sealedFor(small3, 4) === m768 && sealedFor(small3, 6) === m560);
  const k2 = keptSealed(e, 2), k3 = keptSealed(e, 3), k8 = keptSealed(e, 8);
  check('keptSealed: 1-2 eyes keep the full copy and 768 (560 left out)',
    JSON.stringify(k2) === JSON.stringify({ sealed: full, sealedSizes: { '768': m768 } }));
  check('keptSealed: 3+ eyes keep 768 and 560 (the full copy left out)',
    JSON.stringify(k3) === JSON.stringify({ sealedSizes: { '768': m768, '560': m560 } }) && JSON.stringify(k8) === JSON.stringify(k3));
  check('keptSealed: from any kept copy every eye count composes from at least 768 px',
    [1, 2, 3, 4].every((n) => [k2, k3].every((k) => [full, m768].includes(sealedFor(k, n) ?? '')))
    && [5, 8].every((n) => sealedFor(k3, n) === m560 && sealedFor(k2, n) === m768));
  check('keptSealed: an older eye (no sealed copies) and a full-only eye stay valid',
    JSON.stringify(keptSealed({}, 1)) === '{}' && JSON.stringify(keptSealed({}, 5)) === '{}'
    && keptSealed({ sealed: full }, 6).sealed === full && keptSealed({ sealed: full }, 1).sealed === full);
  // the line under the artwork (src/try/copy.ts): square only for the single-eye artwork, number and unit kept together
  const NB = String.fromCharCode(0xa0), DASH = [String.fromCharCode(0x2013), String.fromCharCode(0x2014)];
  for (const lg of ['en', 'de'] as const) {
    const r = COPY[lg].result;
    const sq = r.previewFile(true), wide = r.previewFile(false);
    const all = r.previewReduced + sq + wide;
    check(`${lg}: the preview line promises 50 x 50 cm only for the square artwork, the longest side otherwise`,
      sq.includes(`50${NB}x${NB}50${NB}cm`) && !wide.includes(`50${NB}x`) && wide.includes(`4096${NB}px`)
      && (lg === 'en' ? wide.includes('longest side') : wide.includes('längsten Seite')), wide);
    check(`${lg}: no en or em dash in the preview line`, !DASH.some((d) => all.includes(d)));
  }

  const eye = (id: string, sealed?: string): Eye => ({
    id, before: 'data:image/jpeg;base64,AAAA', image: `DISPLAY-${id}`, thumb: 'data:image/jpeg;base64,BBBB', pad: 1.12,
    fallback: false, usedSr: false, stored: false, glarePct: 0, sample: false, colourOff: false,
    ...(sealed ? { sealed, sealedSizes: { '768': `${sealed}-768`, '560': `${sealed}-560` } } : {}),
    draft: { crop: `CROP-${id}`, ticket: 'work.1.x', until: Date.now() + 600_000 },
  });

  const reply = <T,>(status: number, data: T | null, reason = '') => ({ ok: status >= 200 && status < 300 && reason === '', status, data, reason, error: '', retry: false, retryAfter: 0 });
  const calls: Rec[] = [];
  let draftAnswer: (b: Record<string, unknown>) => ReturnType<typeof reply> = () => reply(200, { ok: true, order: 'o1', k: 'k'.repeat(32), eye: 1, created: true, expires_at: Math.floor(Date.now() / 1000) + 86400 });
  const api = (async (path: string, opts: { body?: Record<string, unknown> } = {}) => {
    calls.push({ path, body: opts.body });
    if (path === '/api/order' && opts.body?.action === 'draft') return draftAnswer(opts.body);
    if (path === '/api/checkout') return reply(200, { ok: true, url: 'https://checkout.stripe.test/c/pay/x', expires_at: Math.floor(Date.now() / 1000) + 3600 });
    return reply(200, { ok: true });
  }) as never;

  const inp = (eyes: Eye[]) => ({ eyes, style: 'deep_nebula', layout: 'single' as const, names: '', lang: 'en' as const, ref: null });
  let r = await runCheckout(inp([eye('a', 'SEALED-a')]), () => {}, api);
  const d = calls.find((c) => c.body?.action === 'draft')?.body ?? {};
  check('draft uploads the sealed preview, never the display copy', r.kind === 'redirect' && d.sealed === 'SEALED-a' && !('preview' in d)
    && d.crop === 'CROP-a' && !JSON.stringify(calls).includes('DISPLAY-a'), JSON.stringify(d));

  calls.length = 0;
  r = await runCheckout(inp([eye('b')]), () => {}, api);
  const d2 = calls.find((c) => c.body?.action === 'draft')?.body ?? {};
  check('an eye from an older server uploads its clean image as preview (old form)', r.kind === 'redirect' && d2.preview === 'DISPLAY-b' && !('sealed' in d2), JSON.stringify(d2));

  for (const reason of ['preview_expired', 'preview_invalid']) {
    calls.length = 0;
    draftAnswer = () => reply(reason === 'preview_expired' ? 410 : 400, { ok: false, reason }, reason);
    r = await runCheckout(inp([eye('c', 'SEALED-c')]), () => {}, api);
    check(`draft refused ${reason} -> that eye is taken again (stale)`, r.kind === 'stale' && JSON.stringify((r as { eyes: number[] }).eyes) === '[1]', JSON.stringify(r));
  }

  // the snapshot kept for the way back from Stripe accepts eyes with sealed copies and refuses a malformed one
  const snapEye = (x: Record<string, unknown>) => ({ id: 'e1', before: 'b', image: 'i', thumb: 't', pad: 1.12, fallback: false, usedSr: false, stored: false, glarePct: 0, sample: false, colourOff: false, ...x });
  const store = new Map<string, string>();
  (globalThis as unknown as { window: unknown }).window = { sessionStorage: { getItem: (k: string) => store.get(k) ?? null, setItem: (k: string, v: string) => { store.set(k, v); }, removeItem: (k: string) => { store.delete(k); } } };
  saveSnapshot({ v: 1, order: 'o1', at: Date.now(), style: 's', layoutWant: null, names: '', eyes: [snapEye({ sealed: 'S', sealedSizes: { '768': 'x' } }) as never] });
  const ok = takeSnapshot('o1');
  saveSnapshot({ v: 1, order: 'o1', at: Date.now(), style: 's', layoutWant: null, names: '', eyes: [snapEye({ sealedSizes: { '768': 5 } }) as never] });
  const bad = takeSnapshot('o1');
  check('snapshot with sealed copies comes back; a malformed sealed size is refused', !!ok && ok.eyes[0].sealed === 'S' && bad === null);
  return out;
}
