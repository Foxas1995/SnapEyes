// The landing page in the three states of the owner's catalogue a visitor can meet, in real Chrome, against a build (dist/) served the way Vercel serves it:
//
//   closed        nothing ticked and ordering closed (the state of the release): every tile says Soon, no price anywhere, the bar and the pricing notice say "Ordering opens soon"
//   open_none     ordering OPEN with nothing ticked (a deployment that takes orders before the owner switches a style on): the same page, no price anywhere
//   one           one style ticked live: that tile (and the price rows and the hero line that belong to its class) show the price, everything else says Soon, the group lines say
//                 "More styles soon." and "Free preview now. Ordering for this group opens soon.", the bar and the notice switch to their open sentences
//   ceilings      every live ceiling ticked (five singles and the Trio; every pair, Radiance and the larger families stay Soon)
//
//   node scripts/check_landing_states.mjs [--dist dist] [--api stub|dev] [--langs en,de] [--widths 375,1280] [--only closed,one,...] [--shots <folder>]      (npm run check:states)
//
// --api stub (default) answers GET /api/health and GET /api/checkout from the registry (scripts/lib/stubapi.mjs). --api dev starts the REAL dev API (scripts/dev_api_state.py: the
// api/ code of this checkout, the owner's override stood in for, no model, no Stripe call) once per state and the page talks to that. The expectations are made from the answer the
// page itself fetched (an independent reading, not the page's helpers): which tile can be bought, which price rows, which line under each group, whether the hero line shows, what the bar,
// the pricing notice, the combo card and the FAQ answer say. Also: every tile heading is a registry name, no console error, no horizontal scroll, no heading cut off. Exit code 1 when
// any check fails. Not part of `vite build` (it needs Chrome); run it after a build.
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { request } from 'node:http';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { launch, sleep } from './lib/cdp.mjs';
import { serve } from './lib/static.mjs';
import { checkoutAnswer, firstLiveOneEyeStyle } from './lib/stubapi.mjs';
import { loadRegistry } from './styles_source.mjs';

const ROOT = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const args = process.argv.slice(2);
const opt = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const dist = resolve(opt('--dist', join(ROOT, 'dist')));
const api = opt('--api', 'stub');
const LANGS = opt('--langs', 'en,de').split(',');
const WIDTHS = opt('--widths', '375,1280').split(',').map(Number);
const only = opt('--only') ? new Set(opt('--only').split(',')) : null;
const shots = opt('--shots') ? resolve(opt('--shots')) : null;
const PYTHON = process.env.PYTHON || 'python';

const COPY = Object.fromEntries(['en', 'de', 'lt', 'hu'].map((l) => [l, JSON.parse(readFileSync(join(ROOT, `src/landing/copy/${l}.json`), 'utf8'))]));
const registry = loadRegistry(ROOT);
const styles = registry.styles;
const oneStyle = firstLiveOneEyeStyle(ROOT);

// the tile table and the gallery, as the build loads them (Vite's module runner: the page's own files)
const { runnerImport } = await import('vite');
const load = async (p) => (await runnerImport(p, { configFile: false, logLevel: 'silent', root: ROOT })).module;
const TILE_STYLE = (await load('./src/landing/tileStyle.ts')).TILE_STYLE;
const GALLERY = (await load('./src/landing/assets.data.ts')).GALLERY;

const STATES = [
  { key: 'closed', title: 'nothing ticked, ordering closed', stub: { open: false, ticked: false } },
  { key: 'open_none', title: 'ordering open, nothing ticked', stub: { open: true, ticked: false } },
  { key: 'one', title: 'one style ticked live', stub: { open: true, ticked: [oneStyle] } },
  { key: 'ceilings', title: 'every live ceiling ticked', stub: { open: true, ticked: true } },
].filter((s) => !only || only.has(s.key));

const problems = [];
const fail = (where, msg) => { problems.push(`${where}: ${msg}`); console.log(`  FAIL ${where}: ${msg}`); };
let checks = 0;
const ok = (cond, where, msg) => { checks += 1; if (!cond) fail(where, msg); return cond; };

// ---------------------------------------------------------------------------------------------------- the API: a stub, or the real dev API in each state
const dev = new Map();
let current = STATES[0];
function proxy(req, res, port) {
  const p = request({ host: '127.0.0.1', port, path: req.url, method: req.method, headers: { accept: 'application/json' } }, (r) => {
    res.writeHead(r.statusCode || 502, { 'content-type': 'application/json', 'cache-control': 'no-store' });
    r.pipe(res);
  });
  p.on('error', () => { res.writeHead(502).end('{}'); });
  p.end();
}
const handler = (req, res) => {
  const url = new URL(req.url, 'http://x');
  if (!url.pathname.startsWith('/api/')) return false;
  if (api === 'dev') {
    if (url.pathname === '/api/health' || url.pathname === '/api/checkout') { proxy(req, res, dev.get(current.key).port); return true; }
  } else {
    const json = (o) => { res.writeHead(200, { 'content-type': 'application/json', 'cache-control': 'no-store' }); res.end(JSON.stringify(o)); };
    if (url.pathname === '/api/health') { json({ stripe: true, stripe_live: false, email: false }); return true; }
    if (url.pathname === '/api/checkout') { json(checkoutAnswer(ROOT, current.stub)); return true; }
  }
  res.writeHead(404, { 'content-type': 'application/json' }).end('{}');
  return true;
};

async function startDev() {
  let port = 5071;
  for (const s of STATES) {
    const proc = spawn(PYTHON, ['scripts/dev_api_state.py', '--state', s.key, '--port', String(port)], { cwd: ROOT, stdio: 'ignore', env: { ...process.env, PYTHONIOENCODING: 'utf-8' } });
    dev.set(s.key, { proc, port });
    port += 1;
  }
  for (const [key, d] of dev) {
    let up = false;
    for (let i = 0; i < 160 && !up; i++) {
      try { up = (await fetch(`http://127.0.0.1:${d.port}/api/health`)).ok; } catch { await sleep(250); }
    }
    if (!up) throw new Error(`the dev API of the state ${key} did not start on port ${d.port}`);
  }
}

if (!existsSync(join(dist, 'index.html'))) { console.error(`no build in ${dist}: run npm run build first`); process.exit(2); }
if (api === 'dev') await startDev();
const site = await serve(dist, { vercelFile: join(ROOT, 'vercel.json'), handler });
const origin = `http://127.0.0.1:${site.port}`;
const chrome = await launch();

// ---------------------------------------------------------------------------------------------------- what the page shows (runs in the page: a real function, serialised)
function collect(group) {
  const norm = (s) => s.split(/\s+/).join(' ').trim();
  const shown = (el) => {
    if (!el) return false;
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && Number(s.opacity) > 0.01 && !el.closest('[inert]') && el.closest('[aria-hidden="true"]') === null;
  };
  const grid = document.querySelector('#gGrid');
  const tiles = grid ? [...grid.querySelectorAll('figure.lp-tile')].map((f) => {
    const h3 = f.querySelector('h3');
    const price = f.querySelector('.lp-price');
    const soon = f.querySelector('.lp-soon');
    return {
      key: f.dataset.k, state: f.dataset.state, name: h3 ? norm(h3.textContent || '') : '',
      nameCut: h3 ? h3.scrollWidth > h3.clientWidth + 1 : true,
      soon: !!soon && shown(soon), soonText: soon ? norm(soon.textContent || '') : '',
      price: !!price && !soon && shown(price) && /\d/.test(price.textContent || ''), priceText: price ? norm(price.textContent || '') : '',
    };
  }) : [];
  const combo = document.querySelector('#gGrid .lp-combo');
  const line = document.querySelector('#gIntro .lp-gline');
  const rows = [...document.querySelectorAll('#pricing .lp-ptable .lp-prow')].map((r) => {
    const v = r.querySelector('.lp-pv');
    const soon = v ? v.querySelector('.lp-soon') : null;
    return { title: norm((r.querySelector('b') || {}).textContent || ''), note: norm((r.querySelector('small') || {}).textContent || ''), value: v ? norm(v.textContent || '') : '', soon: !!soon, price: !!v && !soon && /\d/.test(v.textContent || '') && shown(v) };
  });
  const hero = document.querySelector('main li.lp-price');
  const faq = document.querySelector('#faq-other');
  if (faq) faq.open = true;
  return {
    group,
    tiles,
    intro: norm((document.querySelector('#gIntro') || {}).textContent || ''),
    line: line ? norm(line.textContent || '') : null,
    combo: combo ? { title: norm((combo.querySelector('h3') || {}).textContent || ''), body: norm((combo.querySelector('p') || {}).textContent || '') } : null,
    rows,
    notice: norm((document.querySelector('#pricing .lp-notice') || {}).textContent || ''),
    hero: hero ? { visible: shown(hero) && !hero.hasAttribute('inert'), text: norm(hero.textContent || '') } : null,
    faqOther: faq ? norm((faq.querySelector('p') || {}).textContent || '') : null,
    body: norm(document.body.innerText || ''),
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
  };
}

// ---------------------------------------------------------------------------------------------------- an independent reading of the catalogue's answer
function reading(answer) {
  const live = new Map();
  if (answer && Array.isArray(answer.styles)) {
    for (const s of answer.styles) for (const [n, st] of Object.entries(s.stages || {})) if (st === 'live') { if (!live.has(s.id)) live.set(s.id, new Set()); live.get(s.id).add(Number(n)); }
  }
  const open = !!answer && answer.ok !== false && answer.open === true && answer.orderable_max_eyes >= 1;
  const eyes = new Set();
  if (open) for (const set of live.values()) for (const n of set) eyes.add(n);
  const buyable = (id, n) => open && live.has(id) && live.get(id).has(n);
  let several = 1;
  while (several < 8 && eyes.has(several + 1)) several += 1;
  if (several < 2) several = 0;
  return { open, live, eyes, buyable, several, max: open ? Math.max(...eyes, 0) : 0 };
}

async function openPage(lang, width) {
  const wipe = await chrome.page({ width: 400, height: 300 });
  await wipe.goto(`${origin}/imprint?lang=en`);
  await wipe.loaded();
  await wipe.send('Storage.clearDataForOrigin', { origin, storageTypes: 'all' }).catch(() => undefined);
  await wipe.close();
  const height = width < 800 ? 812 : 900;
  const page = await chrome.page({ width, height, mobile: width < 800, dpr: width < 800 ? 2 : 1 });
  const errors = [];
  page.on((e) => {
    if (e.method === 'Runtime.exceptionThrown') errors.push(`exception: ${e.params.exceptionDetails?.exception?.description || e.params.exceptionDetails?.text}`);
    if (e.method === 'Runtime.consoleAPICalled' && e.params.type === 'error') errors.push(`console.error: ${(e.params.args || []).map((a) => a.value ?? a.description ?? '').join(' ').slice(0, 200)}`);
    if (e.method === 'Log.entryAdded' && e.params.entry.level === 'error' && !/favicon/.test(e.params.entry.url || '')) errors.push(`log: ${e.params.entry.text} ${e.params.entry.url || ''}`.slice(0, 240));
  });
  await page.send('Log.enable').catch(() => undefined);
  await page.goto(`${origin}/?lang=${lang}`);
  await page.loaded();
  for (let i = 0; i < 100; i++) {
    if (await page.eval("document.querySelector('.lp-slot') === null && !!document.getElementById('faq') && !!document.querySelector('.lp-ftr')")) break;
    await sleep(100);
  }
  const H = await page.eval('document.documentElement.scrollHeight');
  for (let y = 0; y < H + 200; y += Math.round(height * 0.7)) { await page.eval(`window.scrollTo({ top: ${y}, behavior: 'instant' })`); await sleep(40); }
  await page.eval('Promise.all([...document.images].map((i) => (i.complete ? 1 : new Promise((r) => { i.onload = i.onerror = r; setTimeout(r, 4000); }))))');
  await page.eval("window.scrollTo({ top: 0, behavior: 'instant' })");
  await sleep(700);
  return { page, errors };
}

const results = [];
for (const state of STATES) {
  current = state;
  console.log(`\n== ${state.key}: ${state.title}${api === 'dev' ? ' (real dev API)' : ' (stub)'}`);
  for (const lang of LANGS) {
    const c = COPY[lang];
    for (const width of WIDTHS) {
      const where = `${state.key} ${lang} ${width}px`;
      const { page, errors } = await openPage(lang, width);
      const answer = await page.eval("fetch('/api/checkout', { cache: 'no-store' }).then((r) => r.json())");
      const read = reading(answer);
      ok(Array.isArray(answer.styles) && typeof answer.orderable_max_eyes === 'number', where, 'GET /api/checkout has no catalogue');
      const seen = {};
      for (const group of ['one', 'two', 'family']) {
        await page.eval(`(() => { const t = document.querySelector('#gtab-${group}'); if (t) { t.scrollIntoView({ block: 'center' }); t.click(); } })()`);
        await sleep(group === 'one' ? 500 : 700);
        const got = await page.eval(`(${collect.toString()})(${JSON.stringify(group)})`);
        seen[group] = got;
        const gwhere = `${where} group ${group}`;
        const wanted = GALLERY[group];
        ok(got.tiles.length === wanted.length && wanted.every((t, i) => got.tiles[i] && got.tiles[i].key === group + t.id), gwhere, `the tiles are ${got.tiles.map((t) => t.key).join()}`);
        let nSale = 0;
        for (const t of wanted) {
          const row = TILE_STYLE[t.id];
          const d = styles[row.id];
          const tile = got.tiles.find((x) => x.key === group + t.id);
          if (!tile) continue;
          const sale = read.buyable(row.id, row.eyes);
          if (sale) nSale += 1;
          const label = `${gwhere} tile ${t.id} (${d.name}, ${row.eyes} eye${row.eyes === 1 ? '' : 's'})`;
          ok(tile.name === d.name, label, `the heading is "${tile.name}", the registry's name is "${d.name}"`);
          ok(!tile.nameCut, label, 'the heading is cut off');
          if (sale) {
            ok(tile.state === 'sale' && tile.price && !tile.soon, label, `can be bought but shows ${tile.price ? 'a price' : 'no price'}${tile.soon ? ' and Soon' : ''} (state ${tile.state}): "${tile.priceText}"`);
          } else {
            ok(tile.state === 'soon' && tile.soon && !tile.price && tile.soonText === c.styles.soonTag, label, `cannot be bought but state ${tile.state}, chip "${tile.soonText}", price ${tile.price} ("${tile.priceText}")`);
          }
        }
        // the line under the intro
        const wantLine = !read.open ? null : nSale === 0 ? c.pricing.severalSoon : nSale < wanted.length ? c.styles.moreSoon : null;
        ok(got.line === wantLine, gwhere, `the line under the intro is ${JSON.stringify(got.line)}, expected ${JSON.stringify(wantLine)}`);
        ok(got.intro.startsWith(c.styles.groupIntro[group]), gwhere, `the intro is "${got.intro}"`);
        // the combo card of the wide groups
        if (group !== 'one') {
          ok(!!got.combo, gwhere, 'no combo card');
          if (got.combo) {
            if (read.several >= 2) ok(got.combo.title === c.styles.comboTitle.replace('{max}', String(read.several)) && /\d/.test(got.combo.body), gwhere, `combo "${got.combo.title}" / "${got.combo.body}"`);
            else ok(got.combo.title === c.styles.comboTitleSoon && got.combo.body === (nSale > 0 ? c.styles.moreSoon : c.pricing.severalSoon) && !/\d/.test(got.combo.title + got.combo.body), gwhere, `combo "${got.combo.title}" / "${got.combo.body}"`);
          }
        }
      }
      // the pricing section, the hero, the bar, the FAQ (they do not depend on the group)
      const g = seen.one;
      const rows = g.rows;
      ok(rows.length === 5, where, `the price table has ${rows.length} rows`);
      if (rows.length === 5) {
        const liveOne = (cls) => [...read.live].some(([id, set]) => read.open && set.has(1) && styles[id].price_class === cls);
        const want = [liveOne('black'), liveOne('art'), read.open && read.eyes.has(2), read.open && read.eyes.has(3)];
        want.forEach((w, i) => {
          const r = rows[i + 1];
          ok(w ? r.price && !r.soon : r.soon && !r.price && r.value === c.styles.soonTag, `${where} price row "${r.title}"`, `${w ? 'can be bought' : 'cannot be bought'} but shows "${r.value}" (soon ${r.soon}, price ${r.price})`);
        });
        const artNote = rows[2].note, twoNote = rows[3].note;
        // the styles a row names are the registry's names of tiles that can be bought: never Radiance (preview) in the art row, never a pair while no pair can be bought
        ok(!artNote.includes('Radiance'), `${where} art row`, `names Radiance, a style that cannot be bought: "${artNote}"`);
        ok(read.eyes.has(2) || !/Collision|Kiss|Infinity/.test(twoNote), `${where} two eyes row`, `names a pair that cannot be bought: "${twoNote}"`);
        if (!read.open) ok(!rows.slice(1).some((r) => /\d/.test(r.note) || r.price), where, 'a price or a number stands in the table while nothing can be bought');
      }
      ok(g.notice === (read.open ? c.pricing.noticeOpen : c.pricing.notice), where, `the pricing notice says "${g.notice}"`);
      ok(g.body.includes(read.open ? c.bar.open : c.bar.soon) && !g.body.includes(read.open ? c.bar.soon : c.bar.open), where, `the bar does not say ${read.open ? 'the open' : 'the soon'} sentence`);
      const heroWant = read.open && [...read.live].some(([, set]) => set.has(1));
      ok(!!g.hero && g.hero.visible === heroWant, where, `the hero's price line is ${g.hero?.visible ? 'shown' : 'held back'} ("${g.hero?.text}"), expected ${heroWant ? 'shown' : 'held back'}`);
      const countInFaq = read.open && read.max >= 2;
      ok(g.faqOther !== null && (countInFaq ? g.faqOther.includes(String(read.max)) : !/\d/.test(g.faqOther)), where, `the FAQ answer about other people's eyes reads "${(g.faqOther || '').slice(0, 90)}"`);
      ok(g.overflow <= 0, where, `the page scrolls sideways by ${g.overflow} px`);
      ok(errors.length === 0, where, `console: ${errors.slice(0, 3).join(' | ')}`);
      if (shots && lang === LANGS[0]) {
        mkdirSync(shots, { recursive: true });
        // a wide window: the whole section; a phone: what the visitor sees (the section scrolled to the top, then the price table), because a clip taller than the window is not
        // painted reliably under mobile emulation
        const take = async (selector, name) => {
          const clip = await page.eval(`(() => { const e = document.querySelector(${JSON.stringify(selector)}); e.scrollIntoView({ block: 'start' }); const r = e.getBoundingClientRect(); return [0, Math.max(0, r.top + window.scrollY), document.documentElement.clientWidth, Math.min(r.height, ${width < 800 ? 812 : 2600})]; })()`);
          await sleep(500);
          writeFileSync(join(shots, `${state.key}_${lang}_${width}_${name}.png`), await page.shot(width < 800 ? undefined : clip));
        };
        for (const group of ['one', 'family']) {
          await page.eval(`(() => { const t = document.querySelector('#gtab-${group}'); if (t) { t.click(); } })()`);
          await sleep(600);
          await take('#styles', group);
        }
        await take('#pricing', 'pricing');
      }
      results.push({ state: state.key, lang, width, open: read.open, tilesForSale: GALLERY.one.concat(GALLERY.two, GALLERY.family).filter((t) => read.buyable(TILE_STYLE[t.id].id, TILE_STYLE[t.id].eyes)).map((t) => t.id) });
      console.log(`  ${problems.some((p) => p.startsWith(where)) ? 'FAIL' : 'ok  '} ${where}: ${read.open ? 'open' : 'closed'}, for sale: ${results[results.length - 1].tilesForSale.join(', ') || 'none'}`);
      await page.close();
    }
  }
}
await chrome.close();
site.server?.close?.();
for (const d of dev.values()) d.proc.kill();
console.log(`\n${checks - problems.length} of ${checks} checks passed${problems.length ? `, ${problems.length} FAILED` : ''} (${api === 'dev' ? 'real dev API' : 'registry stub'}; ${STATES.length} states x ${LANGS.length} languages x ${WIDTHS.length} widths)`);
process.exit(problems.length ? 1 : 0);
