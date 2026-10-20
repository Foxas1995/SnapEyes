// The anonymous feedback box, the page's half (2026-10-20): src/shared/feedback.ts sends one request when the visitor presses Send (the chip, the context code, the eyes, the text, the honeypot, the
// campaign code, the language and market), never throws, sends no credentials, remembers in memory only that a place was answered, and shows the box only when /api/health says feedback true.
// Pure page code, loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results. (The gate is one scenario per file: the answer is given once per page load.)
import { readFileSync } from 'node:fs';
import { CHIPS, TEXT_MAX, feedbackAsked, forgetAnswered, markAnswered, noteFeedback, sendFeedback, wasAnswered } from '../../src/shared/feedback';

type Row = [string, boolean, string?];
const read = (p: string) => readFileSync(new URL(`../../${p}`, import.meta.url), 'utf8');
const tick = () => new Promise<void>((r) => setTimeout(r, 15));

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);

  const g = globalThis as unknown as Record<string, unknown>;
  g.location = { search: '?utm_source=fb&utm_medium=paid&utm_campaign=se-p0-test&utm_term=lt-a1-eye&utm_content=a1-lt-s1' };
  g.document = { referrer: '' };
  const stored: [string, string][] = [];
  g.sessionStorage = { getItem: () => null, setItem: (k: string, v: string) => { stored.push([k, v]); } };
  g.localStorage = { getItem: () => { throw new Error('the box reads no local storage'); }, setItem: () => { throw new Error('the box writes no local storage'); } };

  // the gate: the box waits for the server and a literal true is the only yes
  let settled: boolean | null = null;
  void feedbackAsked().then((v) => { settled = v; });
  await tick();
  check('before /api/health has answered the box is not offered (the answer is pending)', settled === null);
  noteFeedback('true');
  await tick();
  check('and only a literal true is a yes: the string "true" is a no', settled === false, String(settled));
  noteFeedback(true);
  await tick();
  check('the answer is given once: a later yes changes nothing', settled === false);

  // sending
  const calls: { url: string; init: RequestInit }[] = [];
  const reply = (data: unknown, status = 200): typeof fetch => (async (url: unknown, init?: RequestInit) => {
    calls.push({ url: String(url), init: init ?? {} });
    return { ok: status < 400, status, json: async () => data } as Response;
  }) as typeof fetch;
  const o1 = await sendFeedback({ w: 'result', c: 'colour', x: 'solo.gold', eyes: 2, t: '  too grey  ' }, 'lt', 'lt', reply({ ok: true, counted: true, text: 'kept' }));
  const call = calls[0];
  const body = JSON.parse(String(call.init.body));
  check('a text that was stored comes back as kept', o1 === 'kept', o1);
  check('it is one POST of JSON to /api/checkout (the route that gates the content type), without credentials (no cookie) and kept alive so that closing the page does not lose it',
    calls.length === 1 && call.url === '/api/checkout' && call.init.method === 'POST' && (call.init.headers as Record<string, string>)['Content-Type'] === 'application/json' && call.init.credentials === 'omit' && call.init.keepalive === true, JSON.stringify(call));
  check('the body is the answer (place, chip, style, eyes, the trimmed text and an empty honeypot), the campaign code, the page language and market, and nothing else (no URL, no referrer, no identifier)',
    JSON.stringify(body) === '{"feedback":{"w":"result","c":"colour","x":"solo.gold","eyes":2,"t":"too grey","hp":""},"camp":"utm_source=fb&utm_medium=paid&utm_campaign=se-p0-test&utm_term=lt-a1-eye&utm_content=a1-lt-s1","lang":"lt","market":"lt"}', JSON.stringify(body));
  await sendFeedback({ w: 'retake', c: 'fine' }, 'en', 'eu', reply({ ok: true, counted: true, text: 'none' }));
  const b2 = JSON.parse(String(calls[1].init.body));
  check('with no text, no context and no eyes the body has none of them (and the honeypot stays empty)', JSON.stringify(b2.feedback) === '{"w":"retake","c":"fine","hp":""}' && b2.lang === 'en' && b2.market === 'eu', JSON.stringify(b2));
  await sendFeedback({ w: 'result', c: 'other', t: '   ' }, 'de', 'eu', reply({ ok: true, counted: true, text: 'none' }));
  check('a text of white space only is no text', !('t' in JSON.parse(String(calls[2].init.body)).feedback));
  await sendFeedback({ w: 'result', c: 'other', t: 'x'.repeat(TEXT_MAX + 80) }, 'de', 'eu', reply({ ok: true, counted: true, text: 'kept' }));
  check('a text is cut to 300 characters before it leaves the page', JSON.parse(String(calls[3].init.body)).feedback.t.length === TEXT_MAX && TEXT_MAX === 300);
  await sendFeedback({ w: 'result', c: 'other', hp: 'bot wrote this' }, 'de', 'eu', reply({ ok: true, counted: false }));
  check('whatever the honeypot holds is sent as it is (the server throws such an answer away)', JSON.parse(String(calls[4].init.body)).feedback.hp === 'bot wrote this');

  // what comes back
  const outcome = async (data: unknown, status = 200) => sendFeedback({ w: 'result', c: 'love' }, 'en', 'eu', reply(data, status));
  check('an answer that was counted without a text, or was not counted (a robot, a flood), reads as none: the visitor is thanked either way', (await outcome({ ok: true, counted: true, text: 'none' })) === 'none' && (await outcome({ ok: true, counted: false })) === 'none' && (await outcome({ ok: true, counted: false, on: false })) === 'none');
  check('a text the filter dropped reads as dropped, one that could not be stored as lost', (await outcome({ ok: true, counted: true, text: 'dropped' })) === 'dropped' && (await outcome({ ok: true, counted: true, text: 'lost' })) === 'lost');
  check('an answer the server did not accept, an HTTP error, a reply that is not JSON and a request that fails are all failed, and nothing is thrown',
    (await outcome({ ok: false })) === 'failed' && (await outcome({}, 500)) === 'failed' && (await outcome(null)) === 'failed'
    && (await sendFeedback({ w: 'result', c: 'love' }, 'en', 'eu', (async () => { throw new TypeError('offline'); }) as unknown as typeof fetch)) === 'failed'
    && (await sendFeedback({ w: 'result', c: 'love' }, 'en', 'eu', (async () => ({ ok: true, status: 200, json: async () => { throw new SyntaxError('bad'); } })) as unknown as typeof fetch)) === 'failed');

  // nothing is kept in the browser
  check('the only thing written to the browser is the campaign code of the tab (snapeyes.c), by the counter\'s own function; the box reads and writes no local storage', stored.every(([k]) => k === 'snapeyes.c') && stored.length <= 1, JSON.stringify(stored));
  check('that a place has been answered is remembered in this page\'s memory only', !wasAnswered('result') && (markAnswered('result'), wasAnswered('result')) && !wasAnswered('retake') && (forgetAnswered(), !wasAnswered('result')));
  const src = read('src/shared/feedback.ts').replace(/[/][/].*$/gm, '');
  check('and the module holds no cookie, no storage of its own and no beacon call', !/document[.]cookie|localStorage|sessionStorage|sendBeacon/.test(src));

  // the chips are the server's
  const py = read('api/_lib/feedback.py');
  const list = (name: string) => [...(new RegExp('"' + name + '": [(]([^)]*)[)]').exec(py)?.[1] ?? '').matchAll(/"([a-z]+)"/g)].map((m) => m[1]);
  check('the six chips of each place are the server\'s (api/_lib/feedback.py CHIPS), in the same order', JSON.stringify(CHIPS.result) === JSON.stringify(list('result')) && JSON.stringify(CHIPS.retake) === JSON.stringify(list('retake')) && CHIPS.result.length === 6 && CHIPS.retake.length === 6,
    JSON.stringify([list('result'), list('retake')]));
  check('and so are the limit of the text and the days a text is kept', /\nTEXT_MAX = 300 /.test(py) && /\nRETENTION_DAYS = 90 /.test(py));
  return out;
}
