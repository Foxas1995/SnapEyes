// WP6a: the order page's driver (src/order/driver.ts) with a fake API: a compose answer that made progress (one more step of the master plan done, the
// artwork not finished yet) does not spend a reload; an answer that made none still ends the loop after eight; the status carries the artwork's progress;
// a plate that is not ready (plate_retry) is waited out like any busy answer; the progress line of the page exists in four languages.
// Loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results, prints nothing.
import { driveOrder, EMPTY_VIEW, type DriveDeps, type DriveView } from '../../src/order/driver';
import type { OrderStatus } from '../../src/order/api';
import { ORDER_COPY } from '../../src/order/copy';

type R = Array<[string, boolean, string?]>;

export async function run(): Promise<R> {
  const out: R = [];
  const DASH = [String.fromCharCode(0x2013), String.fromCharCode(0x2014)];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);

  const reply = <T,>(status: number, data: T | null, reason = '', retryAfter = 0) =>
    ({ ok: status >= 200 && status < 300 && reason === '', status, data, reason, error: '', retry: reason === 'plate_retry', retryAfter });
  const base = (over: Partial<OrderStatus> = {}): OrderStatus => ({
    order: 'o1', state: 'making', eyes: [{ eye: 1, made: true }], count: 1, style: 'x', layout: 'single', artwork: { done: 0, of: 1, step: 'art' }, ...over,
  });
  const download = { url: 'https://example.test/a.jpg', download_url: 'https://example.test/a.jpg?download=1' };

  const run1 = async (answers: (n: number) => ReturnType<typeof reply>, first: OrderStatus) => {
    const calls: string[] = [];
    const waits: string[] = [];
    let view: DriveView = EMPTY_VIEW;
    let composes = 0;
    const api = (async (path: string, opts: { body?: Record<string, unknown> } = {}) => {
      if (opts.body?.action === 'compose') { composes++; calls.push('compose'); return answers(composes); }
      calls.push(opts.body ? String(opts.body.action) : 'status');
      return reply(200, first);
    }) as unknown as Deps['api'];
    type Deps = DriveDeps;
    const deps: DriveDeps = { api, sleep: async () => {}, now: () => Date.now() };
    await driveOrder({ o: 'o1', k: 'k'.repeat(32), s: null }, deps, (p) => {
      view = { ...view, ...p };
      if (p.wait) waits.push(p.wait.reason);
    }, () => true);
    return { view, composes, calls, waits };
  };

  // ten steps: nine answers of progress, the tenth ready
  const ten = (n: number) => (n < 10
    ? reply(200, base({ artwork: { done: n, of: 10, step: `s${n}` } }))
    : reply(200, base({ state: 'ready', download, artwork: undefined })));
  let r = await run1(ten, base({ artwork: { done: 0, of: 10, step: 's0' } }));
  check('a plan of ten steps: nine compose answers that made progress do not spend a reload, the tenth is ready (without the rule the page stopped after eight)',
    r.composes === 10 && r.view.status?.state === 'ready' && r.view.stop === null, `${r.composes} composes, stop ${r.view.stop}, state ${r.view.status?.state}`);

  // no progress: the answer says making with the same step done each time: the loop still ends after eight rounds
  r = await run1(() => reply(200, base({ artwork: { done: 0, of: 2, step: 'a' } })), base({ artwork: { done: 0, of: 2, step: 'a' } }));
  check('answers that make no progress still end the loop after eight rounds (stop failed): a page cannot spin for ever', r.composes === 8 && r.view.stop === 'failed', `${r.composes} composes, stop ${r.view.stop}`);

  // progress that is not forward (done goes back) is not progress
  let k = 0;
  r = await run1(() => { k++; return reply(200, base({ artwork: { done: k % 2, of: 3, step: 'a' } })); }, base({ artwork: { done: 0, of: 3, step: 'a' } }));
  check('a done count that goes up and down (1, 0, 1, 0 ...) is no progress beyond the first step: the loop is bounded', r.composes <= 20 && r.view.stop === 'failed', `${r.composes} composes, stop ${r.view.stop}`);

  // a plate that is not ready is a busy answer: waited out, then the artwork comes
  r = await run1((n) => (n === 1 ? reply(503, { ok: false, reason: 'plate_retry', retry: true, retry_after: 2 }, 'plate_retry', 2)
    : reply(200, base({ state: 'ready', download, artwork: undefined }))), base());
  check('plate_retry is waited out like a busy answer (a busy pause is shown), then the artwork is ready', r.composes === 2 && r.waits.includes('busy') && r.view.status?.state === 'ready' && r.view.stop === null, `${r.composes} composes, waits ${r.waits}`);

  // a hold (409 in_review) reloads the status and stops there
  r = await run1((n) => reply(409, { ok: false, reason: 'in_review' }, 'in_review'), base());
  check('a held order (409 in_review) asks for the status again and the page shows what the status says (here: still making, so the loop ends after its rounds, never a render loop)', r.composes <= 9, `${r.composes}`);

  // the progress line exists in four languages and says which step of how many
  for (const lang of ['en', 'de', 'lt', 'hu'] as const) {
    const line = ORDER_COPY[lang].making.part(2, 3);
    check(`${lang}: the progress line of a plan with several steps names the step and the count`, line.includes('2') && line.includes('3') && line.length > 12 && !DASH.some((d) => line.includes(d)), line);
  }
  return out;
}
