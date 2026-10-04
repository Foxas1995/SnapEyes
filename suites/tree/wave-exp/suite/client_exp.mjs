// The page side of the price experiments (src/shared/pricing.ts, src/shared/markets.ts priceMinor with a ladder,
// src/try/checkout.ts runCheckout's request), through Vite's module runner exactly as the build loads it, against real
// server replies that test_experiments.py captured (the file named by argv[3]). Prints PASS/FAIL lines.
// Run with the repo as the working directory: node <this file> <this folder> <captured.json>
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { webcrypto } from 'node:crypto';

const req = createRequire(join(process.cwd(), 'package.json'));
const { runnerImport } = await import(pathToFileURL(req.resolve('vite')).href);
const opt = { configFile: false, logLevel: 'silent' };
const HERE = process.argv[2];
const CAP = JSON.parse(readFileSync(process.argv[3], 'utf8'));
const ENTRY = pathToFileURL(join(HERE, 'client_entry.ts')).pathname.replace(/^\/([A-Za-z]:)/, '$1');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

let n = 0, bad = 0;
function check(name, ok, detail = '') {
  n++;
  if (!ok) bad++;
  console.log((ok ? 'PASS ' : 'FAIL ') + name + (ok ? '' : `   <- ${typeof detail === 'string' ? detail : JSON.stringify(detail)}`));
}

/** A fresh page: a new module graph, a fake window with a working (or broken) localStorage, a fetch that records.
 *  POSTs are the funnel events (sent); GETs are the second request with the visitor id (gets), answered by `answer(headers)`
 *  (an object, or null for a failed request). */
async function page({ search = '', store = new Map(), storage = 'ok', session = new Map(), answer = null, gpc = false } = {}) {
  const sent = [];
  const gets = [];
  const replaced = [];
  const ls = storage === 'throws'
    ? { getItem() { throw new Error('blocked'); }, setItem() { throw new Error('blocked'); }, removeItem() { throw new Error('blocked'); } }
    : storage === 'forgets'
      ? { getItem: () => null, setItem() {}, removeItem() {} }
      : { getItem: (k) => (store.has(k) ? store.get(k) : null), setItem: (k, v) => { store.set(k, String(v)); }, removeItem: (k) => { store.delete(k); } };
  globalThis.window = {
    location: { search, pathname: '/', hash: '', href: `https://snapeyes.com/${search}` },
    localStorage: ls,
    sessionStorage: { getItem: (k) => (session.has(k) ? session.get(k) : null), setItem: (k, v) => { session.set(k, String(v)); }, removeItem: (k) => { session.delete(k); } },
    history: { state: null, replaceState(_s, _t, url) { replaced.push(String(url)); } },
    crypto: webcrypto,
    navigator: gpc ? { globalPrivacyControl: true } : {},
  };
  globalThis.fetch = (url, init) => {
    const method = init?.method || 'GET';
    if (method === 'POST') {
      sent.push({ url: String(url), method, body: init?.body ? JSON.parse(init.body) : null });
      return Promise.resolve({ ok: true });
    }
    gets.push({ url: String(url), headers: init?.headers || {} });
    const a = answer ? answer(init?.headers || {}) : null;
    return a ? Promise.resolve({ ok: true, json: async () => a }) : Promise.resolve({ ok: false, json: async () => ({}) });
  };
  const { module } = await runnerImport(ENTRY, opt);
  return { X: module, sent, gets, replaced, store };
}

const STYLES = ['studio_black', 'celestial_gold', 'deep_nebula', 'emerald_aurora', 'obsidian_smoke', 'supernova'];
const rule = (l, eyes, style) => (eyes <= 1 ? (style === 'studio_black' ? l.one_eye_studio_black : l.one_eye_art) : l.two_eyes + (eyes - 2) * l.each_further_eye);
const VID = /^[a-f0-9]{32}$/;
const DAY = 86400;

// ------------------------------------------------------------------------------------------ 1. the price rule with a ladder
{
  const { X } = await page();
  let all = true, count = 0, first = '';
  for (const [key, d] of Object.entries(CAP.definitions)) {
    for (const [name, v] of Object.entries(d.variants)) {
      for (const [m, l] of Object.entries(v.prices)) {
        for (let eyes = 1; eyes <= 8; eyes++) {
          for (const style of STYLES) {
            const got = X.M.priceMinor(eyes, style, m, l);
            count++;
            if (got !== rule(l, eyes, style)) { all = false; first ||= `${key}/${name}/${m}/${eyes}/${style}: ${got}`; }
          }
        }
      }
    }
  }
  check(`client priceMinor with a variant's ladder = the server's rule for every experiment, variant, market, eyes and style (${count})`, all && count > 0, first);
  check('client priceMinor without a ladder is still the standard price', X.M.priceMinor(2, 'studio_black', 'au') === CAP.base.au.two_eyes && X.M.priceMinor(3, 'studio_black', 'eu') === CAP.base.eu.two_eyes + CAP.base.eu.each_further_eye);
}

// ------------------------------------------------------------------------------------------ 2. when an id exists at all
const anyReply = CAP.replies.extra_eye_eur_extra10;
{
  // nothing runs: nothing is created, stored or sent
  const p0 = await page({ answer: () => anyReply.reply });
  const out0 = await p0.X.P.noteCheckoutInfo(CAP.plain);
  check('no test runs: no visitor id is created, nothing is stored, no second request is made',
    p0.store.size === 0 && p0.gets.length === 0 && p0.sent.length === 0 && out0 === CAP.plain, [...p0.store.keys()]);
  check('...the standard ladder shows, the page is ready, there is no token', p0.X.P.pricingReady() === true && p0.X.P.experimentToken() === null
    && JSON.stringify(p0.X.P.effectiveList('eu')) === JSON.stringify(CAP.base.eu));
  check('visitorId(false) with nothing stored is null (asking never creates)', p0.X.P.visitorId(false) === null && p0.store.size === 0);

  // a test runs, but not for this visitor's market
  const pA = await page({ search: '?m=au', answer: () => anyReply.reply });
  await pA.X.P.noteCheckoutInfo(CAP.plain_running);
  check('a test runs for eu and lt, the visitor is in au: no id is created and no second request is made',
    pA.store.get('snapeyes.vid') === undefined && pA.gets.length === 0 && pA.X.P.experimentToken() === null
    && JSON.stringify(pA.X.P.effectiveList('au')) === JSON.stringify(CAP.base.au), [...pA.store.keys()]);
  check('...the exp_markets list only names markets of the site', CAP.plain_running.exp_markets.every((m) => ['eu', 'lt', 'au', 'hu'].includes(m)));

  // a test runs for this visitor's market
  const pE = await page({ answer: () => anyReply.reply });
  const outE = await pE.X.P.noteCheckoutInfo(CAP.plain_running);
  const stored = JSON.parse(pE.store.get('snapeyes.vid') || 'null');
  check('a test runs for the visitor\'s market: an id is created (32 hex and the day it was made) only now', !!stored && VID.test(stored.id) && Math.abs(stored.t - Date.now() / 1000) < 60, stored);
  check('...and asked again with the id in the header X-Snapeyes-Visitor, never in the address',
    pE.gets.length === 1 && pE.gets[0].url === '/api/checkout' && pE.gets[0].headers['X-Snapeyes-Visitor'] === stored.id && !pE.gets[0].url.includes(stored.id), pE.gets);
  check('...the page uses the second answer (the variant\'s ladder and token), and hands it back to the caller',
    outE === anyReply.reply && pE.X.P.experimentToken() === anyReply.reply.exp_token && JSON.stringify(pE.X.P.effectiveList(anyReply.market)) === JSON.stringify(anyReply.ladder));
  check('...the visit event carries the token and the market, no visitor id', pE.sent.length === 1 && pE.sent[0].body.exp_event === 'visit'
    && pE.sent[0].body.exp_token === anyReply.reply.exp_token && !JSON.stringify(pE.sent[0].body).includes(stored.id), pE.sent);
  check('visitorId() now returns the same id (sticky), also on a new page load', pE.X.P.visitorId() === stored.id && (await page({ store: pE.store })).X.P.visitorId() === stored.id);

  // ids are random, a damaged or expired one is replaced
  const ids = new Set();
  for (let i = 0; i < 20; i++) ids.add((await page()).X.P.visitorId());
  check('20 fresh browsers get 20 different ids', ids.size === 20 && [...ids].every((x) => VID.test(x)));
  const dmg = await page({ store: new Map([['snapeyes.vid', JSON.stringify({ id: 'not-an-id', t: Date.now() / 1000 })]]) });
  const fixed = dmg.X.P.visitorId();
  check('a damaged stored id is replaced by a good one', VID.test(fixed) && fixed !== 'not-an-id');
  const old = 'a'.repeat(32);
  const exp = await page({ store: new Map([['snapeyes.vid', JSON.stringify({ id: old, t: Date.now() / 1000 - 91 * DAY })]]) });
  check('an id older than 90 days is not used: visitorId(false) says none and removes it', exp.X.P.visitorId(false) === null && !exp.store.has('snapeyes.vid'));
  const exp2 = await page({ store: new Map([['snapeyes.vid', JSON.stringify({ id: old, t: Date.now() / 1000 - 91 * DAY })]]) });
  const renewed = exp2.X.P.visitorId(true);
  check('...and visitorId(true) draws a new one', VID.test(renewed) && renewed !== old);
  const young = await page({ store: new Map([['snapeyes.vid', JSON.stringify({ id: old, t: Date.now() / 1000 - 89 * DAY })]]) });
  check('an id 89 days old is still used', young.X.P.visitorId(false) === old);
  const future = await page({ store: new Map([['snapeyes.vid', JSON.stringify({ id: old, t: Date.now() / 1000 + 10 * DAY })]]) });
  check('an id dated in the future is not trusted (replaced)', future.X.P.visitorId(true) !== old);

  // storage that does not work
  const t = await page({ storage: 'throws', answer: () => anyReply.reply });
  await t.X.P.noteCheckoutInfo(CAP.plain_running);
  check('storage that throws: no id, no second request, the standard prices', t.X.P.visitorId() === null && t.gets.length === 0 && t.X.P.experimentToken() === null && t.X.P.pricingReady());
  const f = await page({ storage: 'forgets', answer: () => anyReply.reply });
  await f.X.P.noteCheckoutInfo(CAP.plain_running);
  check('storage that accepts but forgets: no id (the assignment could not be sticky), no second request', f.X.P.visitorId() === null && f.gets.length === 0 && f.X.P.experimentToken() === null);

  // the second request fails or answers nothing usable
  const fail = await page({ answer: () => null });
  const outF = await fail.X.P.noteCheckoutInfo(CAP.plain_running);
  check('the second request fails: the standard prices, ready, no token, the plain answer handed back, no event',
    fail.gets.length === 1 && fail.X.P.experimentToken() === null && fail.X.P.pricingReady() && outF === CAP.plain_running && fail.sent.length === 0);
  const noTok = await page({ answer: () => ({ ...CAP.plain_running, prices: CAP.plain_running.prices }) });
  await noTok.X.P.noteCheckoutInfo(CAP.plain_running);
  check('an answer without a token (the test stopped meanwhile): the standard prices, no token', noTok.X.P.experimentToken() === null && JSON.stringify(noTok.X.P.effectiveList('eu')) === JSON.stringify(CAP.base.eu));

  // the test is over: what it left in the browser is removed
  const over = await page({ store: new Map([['snapeyes.vid', JSON.stringify({ id: old, t: Date.now() / 1000 })], ['snapeyes.pricing', '{}'], ['snapeyes.expseen', '{"a@1":{"visit":1}}']]) });
  await over.X.P.noteCheckoutInfo(CAP.plain);
  check('when no test runs any more the visitor id, the stored answer and the funnel notes are all removed', over.store.size === 0, [...over.store.keys()]);
  // a test in other markets only: an id made earlier is kept (a currency switch must not re-draw the variant) but not sent
  const other = await page({ search: '?m=au', store: new Map([['snapeyes.vid', JSON.stringify({ id: old, t: Date.now() / 1000 })]]), answer: () => anyReply.reply });
  await other.X.P.noteCheckoutInfo(CAP.plain_running);
  check('a test in other markets only: an existing id is kept, never sent, and not used', other.store.has('snapeyes.vid') && other.gets.length === 0 && other.X.P.experimentToken() === null);

  // the visitor switches the currency: the id is made (and the variant drawn) when a test runs there, and stays the same on the way back
  const sw = await page({ search: '?m=au', answer: (h) => ({ ...anyReply.reply, _id: h['X-Snapeyes-Visitor'] }) });
  await sw.X.P.noteCheckoutInfo(CAP.plain_running);
  check('visitor in au, test in eu and lt: nothing made yet', !sw.store.has('snapeyes.vid') && sw.gets.length === 0);
  sw.X.M.setMarket('eu');
  await sleep(50);
  const idEu = JSON.parse(sw.store.get('snapeyes.vid') || 'null');
  check('...switching the currency to eu makes the id and asks with it (a test runs there now)', !!idEu && sw.gets.length === 1 && sw.gets[0].headers['X-Snapeyes-Visitor'] === idEu.id && sw.X.P.experimentToken() === anyReply.reply.exp_token);
  sw.X.M.setMarket('au');
  await sleep(50);
  check('...back to au: the standard prices, and the id stays stored (not re-drawn)', sw.X.P.experimentToken() === null && JSON.parse(sw.store.get('snapeyes.vid')).id === idEu.id);
  sw.X.M.setMarket('eu');
  await sleep(50);
  check('...and back to eu: asked with the very same id (the same variant)', sw.gets.length === 2 && sw.gets[1].headers['X-Snapeyes-Visitor'] === idEu.id);
}

// ------------------------------------------------------------------------------------------ 2b. the opt-out
{
  const seed = () => new Map([['snapeyes.vid', JSON.stringify({ id: 'b'.repeat(32), t: Date.now() / 1000 })], ['snapeyes.pricing', '{"t":1}'], ['snapeyes.expseen', '{"a@1":{"visit":1}}'], ['snapeyes.lang', 'de']]);
  const off = await page({ search: '?pricetest=off&lang=de', store: seed(), answer: () => anyReply.reply });
  check('?pricetest=off: the opt-out note is kept, the id, the stored answer and the funnel notes are removed, other entries stay',
    off.store.get('snapeyes.notest') === '1' && !off.store.has('snapeyes.vid') && !off.store.has('snapeyes.pricing') && !off.store.has('snapeyes.expseen') && off.store.get('snapeyes.lang') === 'de', [...off.store.entries()]);
  check('...the parameter is taken out of the address and the other one stays', off.replaced.length === 1 && off.replaced[0] === '/?lang=de', off.replaced);
  await off.X.P.noteCheckoutInfo(CAP.plain_running);
  check('...then no id is made, no second request is sent, and the standard prices show', off.gets.length === 0 && !off.store.has('snapeyes.vid') && off.X.P.experimentToken() === null
    && off.X.P.visitorId() === null && off.X.P.optedOut() === true && JSON.stringify(off.X.P.effectiveList('eu')) === JSON.stringify(CAP.base.eu));
  const again = await page({ store: off.store, answer: () => anyReply.reply });
  await again.X.P.noteCheckoutInfo(CAP.plain_running);
  check('...it lasts: a new page load of the same browser is still out of the test', again.gets.length === 0 && again.X.P.optedOut() === true && again.X.P.experimentToken() === null);
  const on = await page({ search: '?pricetest=on', store: off.store, answer: () => anyReply.reply });
  check('?pricetest=on takes the opt-out back (the note is removed)', !on.store.has('snapeyes.notest') && on.X.P.optedOut() === false && on.replaced[0] === '/');
  await on.X.P.noteCheckoutInfo(CAP.plain_running);
  check('...and the visitor takes part again (an id is made, the variant drawn)', on.gets.length === 1 && on.X.P.experimentToken() === anyReply.reply.exp_token);
  const gpc = await page({ gpc: true, store: seed(), answer: () => anyReply.reply });
  check('the Global Privacy Control signal counts as the opt-out: opted out, no id is used',
    gpc.X.P.optedOut() === true && gpc.X.P.visitorId() === null);
  await gpc.X.P.noteCheckoutInfo(CAP.plain_running);
  check('...no second request, no token, the standard prices, even with an id stored from before',
    gpc.gets.length === 0 && gpc.X.P.experimentToken() === null && JSON.stringify(gpc.X.P.effectiveList('eu')) === JSON.stringify(CAP.base.eu));
  const gpcOn = await page({ gpc: true, search: '?pricetest=on', store: new Map(), answer: () => anyReply.reply });
  await gpcOn.X.P.noteCheckoutInfo(CAP.plain_running);
  check('...and ?pricetest=on does not override the browser signal', gpcOn.X.P.optedOut() === true && gpcOn.gets.length === 0);
  const junk = await page({ search: '?pricetest=maybe', store: seed() });
  check('any other value of the parameter does nothing', !junk.store.has('snapeyes.notest') && junk.store.has('snapeyes.vid') && junk.replaced.length === 0);
  const tv = await page({ search: '?pricetest=off', storage: 'throws' });
  check('the opt-out with a storage that throws does not break the page', tv.X.P.visitorId() === null);
}

// ------------------------------------------------------------------------------------------ 3. what the server said
for (const [label, cap] of Object.entries(CAP.replies)) {
  const market = cap.market;
  const search = market === 'eu' ? '' : `?m=${market}`;
  const { X, sent, gets, store } = await page({ search, answer: () => cap.reply });
  await X.P.noteCheckoutInfo(CAP.plain_both);
  const list = X.P.effectiveList(market);
  check(`${label}: the page's ladder for ${market} is the variant's ladder from the server`, JSON.stringify(list) === JSON.stringify(cap.ladder), list);
  check(`${label}: the token is kept for the checkout`, X.P.experimentToken() === cap.reply.exp_token);
  check(`${label}: ready, and the same object until something changes`, X.P.pricingReady() === true && X.P.effectiveList(market) === list);
  check(`${label}: one visit event, with the token and the market, no visitor id`, sent.length === 1 && sent[0].url === '/api/checkout' && sent[0].method === 'POST'
    && sent[0].body.exp_event === 'visit' && sent[0].body.exp_token === cap.reply.exp_token && sent[0].body.market === market
    && !JSON.stringify(sent[0].body).includes('snapeyes.vid') && !('v' in sent[0].body) && !JSON.stringify(sent[0].body).includes(JSON.parse(store.get('snapeyes.vid')).id), sent);
  await X.P.noteCheckoutInfo(CAP.plain_both);
  check(`${label}: a second answer sends no second visit (once per visitor and run of the experiment)`, sent.length === 1 && gets.length === 2, [sent.length, gets.length]);
  X.P.notePreview(3, 'deep_nebula', market);
  X.P.notePreview(4, 'deep_nebula', market);
  const prev = sent.filter((s) => s.body.exp_event === 'preview');
  check(`${label}: one preview event (eyes and style, once)`, prev.length === 1 && prev[0].body.eyes === 3 && prev[0].body.style === 'deep_nebula' && prev[0].body.exp_token === cap.reply.exp_token, prev);
  const again = await page({ store, search, answer: () => cap.reply });
  await again.X.P.noteCheckoutInfo(CAP.plain_both);
  check(`${label}: a reload of the same browser sends no visit again`, again.sent.length === 0, again.sent);
  const seen = JSON.parse(store.get('snapeyes.expseen'));
  const mine = cap.reply.experiments.find((e) => e.markets.includes(market));
  const run = mine.run;
  check(`${label}: what was sent is remembered per experiment and RUN (a new run of the test counts its visitors anew)`,
    Object.keys(seen).length === 1 && Object.keys(seen)[0] === `${mine.key}@${run}` && seen[Object.keys(seen)[0]].visit === 1 && seen[Object.keys(seen)[0]].preview === 1, seen);
  const nextRun = { ...cap.reply, experiments: cap.reply.experiments.map((e) => ({ ...e, run: run + 1000 })) };
  const again2 = await page({ store, search, answer: () => nextRun });
  await again2.X.P.noteCheckoutInfo(CAP.plain_both);
  check(`${label}: after the test was stopped and started again (a new run) the visit is sent again`, again2.sent.length === 1 && again2.sent[0].body.exp_event === 'visit', again2.sent);
  // a returning visitor sees the price of the variant at once, before any answer
  const back = await page({ store, search });
  check(`${label}: a returning visitor's page starts with the stored ladder and token (no flash of the standard price)`,
    JSON.stringify(back.X.P.effectiveList(market)) === JSON.stringify(cap.ladder) && back.X.P.experimentToken() === cap.reply.exp_token && back.X.P.pricingReady(), back.X.P.effectiveList(market));
  // the server later says nothing runs: the ladder, the token and the id are dropped
  await X.P.noteCheckoutInfo(CAP.plain);
  check(`${label}: when the server stops naming the experiment, the standard ladder, no token, and nothing left in the browser`,
    X.P.experimentToken() === null && JSON.stringify(X.P.effectiveList(market)) === JSON.stringify(CAP.base[market])
    && !store.has('snapeyes.vid') && !store.has('snapeyes.pricing') && !store.has('snapeyes.expseen'), [...store.keys()]);
}

// a market no experiment covers: no visit is sent for it, and the standard ladder stays
{
  const cap = CAP.replies.extra_eye_eur_extra10;
  const { X, sent } = await page({ answer: () => cap.reply });
  await X.P.noteCheckoutInfo(CAP.plain_running);
  const before = sent.length;
  X.P.noteVisit('hu');
  check('a visit in a market no experiment covers sends no event', sent.length === before, sent);
  check('...and the standard ladder shows there', JSON.stringify(X.P.effectiveList('hu')) === JSON.stringify(CAP.base.hu));
}
// nonsense from the server changes nothing
{
  const cap = CAP.replies.extra_eye_eur_extra10;
  for (const [label, bad] of [
    ['a malformed token', { ...cap.reply, exp_token: 'x1.not-a-token' }],
    ['a token that is not a string', { ...cap.reply, exp_token: 7 }],
    ['experiments that are not a list', { ...cap.reply, experiments: 'x' }],
    ['a negative price', { ...cap.reply, markets: { eu: { prices: { one_eye_studio_black: -1, one_eye_art: 1, two_eyes: 1, each_further_eye: 1 } } } }],
    ['a market without a ladder', { ...cap.reply, markets: { lt: cap.reply.markets.lt } }],
  ]) {
    const { X, sent } = await page({ answer: () => bad });
    await X.P.noteCheckoutInfo(CAP.plain_running);
    check(`${label} from the server is ignored (standard prices, no token, no event)`,
      X.P.experimentToken() === null && JSON.stringify(X.P.effectiveList('eu')) === JSON.stringify(CAP.base.eu) && sent.length === 0, sent);
  }
  const { X } = await page();
  X.P.noteInfoUnavailable();
  check('an unreachable server ends the wait with the standard prices', X.P.pricingReady() === true && X.P.experimentToken() === null);
}
// a 409 price_changed
{
  const cap = CAP.replies.extra_eye_eur_extra10;
  const { X } = await page({ answer: () => cap.reply });
  await X.P.noteCheckoutInfo(CAP.plain_running);
  X.P.noteChanged({ amount: 5000, prices: CAP.base.eu, market: 'eu' });
  check('price_changed without a new token: the ladder is the server\'s, the token is gone', JSON.stringify(X.P.effectiveList('eu')) === JSON.stringify(CAP.base.eu) && X.P.experimentToken() === null);
  await X.P.noteCheckoutInfo(CAP.plain_running);
  X.P.noteChanged({ amount: 5000, prices: cap.ladder, market: 'eu', exp_token: cap.reply.exp_token });
  check('price_changed with a re-signed token keeps the variant', X.P.experimentToken() === cap.reply.exp_token);
  const merged = X.P.listFor('eu', { each_further_eye: 1234, two_eyes: -5, bogus: 9 });
  check('listFor lets a partial server list override only its valid keys', merged.each_further_eye === 1234 && merged.two_eyes === cap.ladder.two_eyes);
}

// ------------------------------------------------------------------------------------------ 4. the checkout request
{
  const { X } = await page();
  const calls = [];
  const reply = (status, data, reason = '') => ({ ok: status >= 200 && status < 300 && reason === '', status, data, reason, error: '', retry: false, retryAfter: 0 });
  let checkoutAnswer = () => reply(200, { ok: true, url: 'https://checkout.stripe.test/c/pay/x', expires_at: Math.floor(Date.now() / 1000) + 3600 });
  const api = async (path, opts = {}) => {
    calls.push({ path, body: opts.body });
    if (path === '/api/order' && opts.body?.action === 'draft') return reply(200, { ok: true, order: 'o1', k: 'k'.repeat(32), eye: 1, created: true, expires_at: Math.floor(Date.now() / 1000) + 86400 });
    if (path === '/api/checkout') return checkoutAnswer(opts.body);
    return reply(200, { ok: true });
  };
  const eye = { id: 'a', before: 'x', image: 'DISPLAY', thumb: 't', pad: 1.12, fallback: false, usedSr: false, stored: false, glarePct: 0, sample: false, colourOff: false, draft: { crop: 'CROP', ticket: 'work.1.x', until: Date.now() + 600_000 } };
  const inp = { eyes: [eye], style: 'deep_nebula', layout: 'single', names: '', lang: 'en', ref: null };
  let r = await X.C.runCheckout({ ...inp, expToken: 'x1.abc.' + 'a'.repeat(32), shown: 4997 }, () => {}, api);
  let post = calls.filter((c) => c.path === '/api/checkout').pop().body;
  check('runCheckout sends the token and the price shown, and nothing that names a variant', r.kind === 'redirect' && post.exp_token === 'x1.abc.' + 'a'.repeat(32) && post.shown === 4997
    && !('variant' in post) && !('prices' in post) && !('amount' in post) && !('exp' in post), post);
  calls.length = 0;
  r = await X.C.runCheckout({ ...inp, ref: null }, () => {}, api);
  post = calls.filter((c) => c.path === '/api/checkout').pop().body;
  check('runCheckout without a token or shown price sends neither (the standard request)', r.kind === 'redirect' && !('exp_token' in post) && !('shown' in post), post);
  checkoutAnswer = () => reply(409, { ok: false, reason: 'price_changed', amount: 5997, prices: CAP.base.eu, market: 'eu', currency: 'EUR' }, 'price_changed');
  r = await X.C.runCheckout({ ...inp, shown: 4997 }, () => {}, api);
  check('a 409 price_changed becomes the outcome price_changed with the server\'s price (never a redirect)', r.kind === 'price_changed' && r.reply.amount === 5997 && r.ref?.order === 'o1', JSON.stringify(r));
  checkoutAnswer = () => reply(409, { ok: false, reason: 'price_changed' }, 'price_changed');
  r = await X.C.runCheckout({ ...inp, shown: 4997 }, () => {}, api);
  check('a price_changed without an amount is a plain failure, not a price', r.kind === 'error', JSON.stringify(r));
  const note = X.N.priceChangedNote;
  check('the price-changed sentence names the price in every language it has and reads English for a language it does not know',
    note('en', 'A$5').includes('A$5') && note('de', '5 €').includes('5 €') && note('de', 'x').includes('geändert') && note('xx', 'A$5') === note('en', 'A$5') && note('lt', 'A$5').includes('A$5'));
}

console.log(`\n${n - bad} of ${n} passed`);
process.exit(bad ? 1 : 0);
