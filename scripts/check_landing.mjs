// The checks of the landing page as a whole, in real Chrome, against a build (dist/) served the way Vercel serves it, with a stub of
// the two API calls the page makes (/api/health, /api/checkout). Not part of `vite build` (it needs Chrome and takes minutes);
// run it after a build:
//   npm run build && npm run check:landing
//   node scripts/check_landing.mjs [--dist dist] [--only labels,phrases,...] [--quick] [--axe <axe.min.js>] [--mutate "<js>"]
// (--mutate runs a snippet in every settled page, a deliberate defect to see that a check really fails: documented in the README.)
//
// What it checks (each name is a value of --only):
//   labels     every picture area of the page (hero, wall stage, the four rooms, the polished edge, the crop, the tiles of the
//              style gallery, the closing scene) carries its label ("Example", "AI visualisation", "Example photo", in the
//              page's own language) INSIDE the picture; every picture has alt, width and height
//   phrases    no "ready to print", "druckfertig", "100 percent", "museum glass" (the banned claims of scripts/check_texts.mjs) in the
//              visible text, in any of the four languages; "Ordering opens soon" in exactly three places while ordering is not
//              open and in none once it is (the stub flips); "Printing is not part of your order" where the prototype has it
//   dashes     no en or em dash and no spaced hyphen in any text node, alt, aria-label, title or the head of the page
//   anchors    a link to #section lands on the section (fresh load, so the lazy sections must have caught up), and the header's links
//   focus      the focus stays on the control after an arrow key (roving groups) and after a click on a language or currency button;
//              the Reveal's native range answers the keys
//   overflow   no horizontal scroll, nothing beyond the edge, no clipped button and no word cut in the middle at 280, 320, 375,
//              768, 1024 and 1280 px (and more with the full run) in English, German, Lithuanian and Hungarian
//   links      every legal link carries ?lang= and the market's edition (m=au, m=hu); every call to action goes to /try in the language
//   ordering   the closed and the open states: the bar, the pricing notice, the FAQ item about ordering
//   axe        axe-core with every <details> open, in eight states (needs axe-core: --axe, AXE_CORE, or node_modules/axe-core)
//   resilience each lazy chunk of the page blocked in turn (a flaky network, a new deploy): the header, the hero and the footer stay, the page is
//              not blank and does not reload itself in a loop
//   skew       a new deploy under an open page (the old chunk is a 404 and the server's index.html names another script): the page reloads
//              itself once, not in a loop; a chunk that fails while index.html is still the page's own does not reload it
//   stall      one chunk whose request is never answered (a stalled connection) does not hold the sections behind it back
//   glass      the frosted blur of the header, the hero chip and the sticky phone button is really applied (a build that dropped the unprefixed
//              backdrop-filter once left it off in Chrome, Edge and Firefox)
//   shellclick a tap on a language button of the static first screen BEFORE the page's script has run switches the language, remembers it,
//              keeps the focus on the new button, and the page that React then starts speaks that language
//   offers     the offer of another currency: A$ only to a reader of English or German (the Australian edition has no other language), the
//              forint offer to every language
//   vitals     phone, slow 4G, CPU x4 (BUILD_PLAN section 5): LCP under 2.5 s (a warning above the 1.6 s target), CLS under 0.05, with
//              the ordering flip mocked (the stub answers "open" after 2.5 s: the bar sentence changes in a page that is on screen)
// Exit code 1 when any check fails.
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { launch, sleep } from './lib/cdp.mjs';
import { serve } from './lib/static.mjs';
import { checkoutAnswer } from './lib/stubapi.mjs';

const ROOT = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const args = process.argv.slice(2);
const flag = (n) => args.includes(n);
const opt = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const dist = resolve(opt('--dist', join(ROOT, 'dist')));
const quick = flag('--quick');
const only = opt('--only') ? new Set(opt('--only').split(',')) : null;
const wants = (name) => !only || only.has(name);

const LANGS = ['en', 'de', 'lt', 'hu'];
const COPY = Object.fromEntries(LANGS.map((l) => [l, JSON.parse(readFileSync(join(ROOT, `src/landing/copy/${l}.json`), 'utf8'))]));
const BANNED = /ready to print|print[- ]ready|druckfertig|druckbereit|100 ?(percent|%|prozent)|museum[- ]?glass|museumsglas/i;
const WIDTHS = quick ? [280, 375, 1280] : [280, 320, 375, 768, 1024, 1280];

const problems = [];
const notes = [];
const fail = (check, msg) => { problems.push(`${check}: ${msg}`); console.log(`  FAIL ${check}: ${msg}`); };
const info = (check, msg) => { notes.push(`${check}: ${msg}`); console.log(`  note ${check}: ${msg}`); };
const pass = (check, msg) => console.log(`  ok   ${check}: ${msg}`);

// ---------------------------------------------------------------------------------------------------- the server and its API stub
const stub = { open: false, suggest: null, delay: 0 };
// a pretend new deploy for the skew check: from the second request for / on the server's index.html names another script, and the chunk is gone
const skew = { on: false, chunk: '', rootHits: 0, mainFile: '', hang: false };
const handler = (req, res) => {
  const url = new URL(req.url, 'http://x');
  const json = (o) => { res.writeHead(200, { 'content-type': 'application/json', 'cache-control': 'no-store' }); res.end(JSON.stringify(o)); };
  const later = (o) => setTimeout(() => json(o), stub.delay);
  if (skew.on && url.pathname === '/' && ++skew.rootHits > 1) {
    const html = readFileSync(join(dist, 'index.html'), 'utf8').split(skew.mainFile).join('/assets/main-NEWDEPLOY.js');
    res.writeHead(200, { 'content-type': 'text/html', 'cache-control': 'no-store' });
    res.end(html);
    return true;
  }
  if (skew.on && skew.hang && skew.chunk && url.pathname.includes(skew.chunk)) return true;   // a stalled connection: the request is never answered
  if (skew.on && skew.chunk && url.pathname.includes(skew.chunk)) { res.writeHead(404, { 'content-type': 'text/plain' }); res.end('gone'); return true; }
  if (url.pathname === '/api/health') { later({ stripe: true, stripe_live: false, email: false }); return true; }
  if (url.pathname === '/api/checkout') { later(checkoutAnswer(ROOT, { open: stub.open, suggest: stub.suggest })); return true; }
  if (url.pathname.startsWith('/api/')) { res.writeHead(404, { 'content-type': 'application/json' }); res.end('{}'); return true; }
  return false;
};
if (!existsSync(join(dist, 'index.html'))) { console.error(`no build in ${dist}: run npm run build first`); process.exit(2); }
const site = await serve(dist, { vercelFile: join(ROOT, 'vercel.json'), handler });
const origin = `http://127.0.0.1:${site.port}`;
const chrome = await launch();

// ---------------------------------------------------------------------------------------------------- page helpers
/** Open the page, wait until every lazy section is in, scroll through so every lazy picture loads, back to the top. */
async function open({ lang = 'en', query = '', width = 1280, height = 900, details = false, settle = true, hash = '', ...more } = {}) {
  // every case starts as a first visit: the page remembers a chosen language and market (localStorage), and a market left over from the
  // case before (?m=au) would change the next one (another shell, another currency, no Lithuanian button)
  const wipe = await chrome.page({ width: 400, height: 300 });
  await wipe.goto(`${origin}/imprint?lang=en`);
  await wipe.loaded();
  await wipe.send('Storage.clearDataForOrigin', { origin, storageTypes: 'all' }).catch(() => undefined);
  await wipe.close();
  const page = await chrome.page({ width, height, mobile: width < 800, dpr: width < 800 ? 2 : 1, ...more });
  const q = new URLSearchParams(query);
  if (lang) q.set('lang', lang);
  await page.goto(`${origin}/?${q}${hash}`);
  await page.loaded();
  if (settle) {
    for (let i = 0; i < 100; i++) {
      if (await page.eval("document.querySelector('.lp-slot') === null && !!document.getElementById('faq') && !!document.querySelector('.lp-ftr')")) break;
      await sleep(100);
    }
    const H = await page.eval('document.documentElement.scrollHeight');
    for (let y = 0; y < H + 200; y += Math.round(height * 0.7)) { await page.eval(`window.scrollTo({ top: ${y}, behavior: 'instant' })`); await sleep(50); }
    await page.eval('Promise.all([...document.images].map((i) => (i.complete ? 1 : new Promise((r) => { i.onload = i.onerror = r; setTimeout(r, 4000); }))))');
    if (details) await page.eval("document.querySelectorAll('details').forEach((d) => (d.open = true))");
    await page.eval("window.scrollTo({ top: 0, behavior: 'instant' })");
    await sleep(400);
    // a deliberate defect for the negative tests of this script itself: --mutate "<js>" runs in every page that settled
    if (opt('--mutate')) await page.eval(opt('--mutate'));
  }
  return page;
}
const KEYS = { ArrowRight: 39, ArrowLeft: 37, ArrowDown: 40, Home: 36, End: 35 };
async function key(page, k) {
  await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: k, code: k, windowsVirtualKeyCode: KEYS[k] });
  await page.send('Input.dispatchKeyEvent', { type: 'keyUp', key: k, code: k, windowsVirtualKeyCode: KEYS[k] });
  await sleep(250);
}
/** Every section drawn at its real height: a section far from the screen is skipped (content-visibility: auto, css/base.css), and a skipped one has no innerText and is not seen by a script that measures. */
const NO_SKIP = "document.head.appendChild(Object.assign(document.createElement('style'), { textContent: '.lp-sheet > .lp-sec, .lp-final { content-visibility: visible !important }' }))";
const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

// ---------------------------------------------------------------------------------------------------- labels
async function checkLabels() {
  console.log('labels');
  for (const lang of LANGS) for (const width of [375, 1280]) {
    const c = COPY[lang];
    const page = await open({ lang, width });
    const r = JSON.parse(await page.eval(`(() => {
      const AREAS = [['hero', '.lp-hero-frame', '.lp-frame-chip', 1], ['stage', '#stage', '.lp-vis-chip', 1], ['rooms', '#rail figure > div', '.lp-vis-chip', 4],
        ['edge', '.lp-edge-img', '.lp-vis-chip', 1], ['crop', '.lp-cu-img', '.lp-cu-badge', 1], ['final', '.lp-final', '.lp-final-chip', 1],
        ...(innerWidth >= 768 ? [['reveal', '.lp-rv-frame', '.lp-rv-who', 1]] : [])];
      const out = { miss: [], texts: {}, imgs: [], tiles: 0, tilesWithPhotoChip: 0, legend: !!document.querySelector('.lp-legend') };
      for (const [name, sel, chip, n] of AREAS) {
        const boxes = [...document.querySelectorAll(sel)];
        if (boxes.length < n) out.miss.push(name + ': ' + boxes.length + ' of ' + n + ' areas found');
        for (const b of boxes) {
          if (!b.querySelector('img')) out.miss.push(name + ': an area without a picture');
          const ch = b.querySelector(chip);
          if (!ch || !ch.textContent.trim()) { out.miss.push(name + ': no label'); continue; }
          (out.texts[name] ||= []).push(ch.querySelector('b') ? ch.querySelector('b').textContent.trim() : ch.textContent.trim());
        }
      }
      for (const i of document.querySelectorAll('main img')) {
        if (i.getAttribute('alt') === null) out.imgs.push('no alt: ' + (i.currentSrc || i.src).split('/').pop());
        if (!i.getAttribute('width') || !i.getAttribute('height')) out.imgs.push('no size: ' + (i.currentSrc || i.src).split('/').pop());
      }
      return JSON.stringify(out);
    })()`));
    const problemsHere = [...r.miss, ...r.imgs.slice(0, 5)];
    const wantVis = c.example.vis;
    for (const name of ['hero', 'stage', 'rooms', 'edge', 'final']) for (const t of r.texts[name] || []) if (t !== wantVis) problemsHere.push(`${name} label "${t}", the language says "${wantVis}"`);
    // the pinned scene's frame is the founder's own eye and says so in the picture (charter AC-8), whatever the chips are doing
    for (const t of r.texts.reveal || []) if (t !== c.example.mantas) problemsHere.push(`reveal frame label "${t}", the language says "${c.example.mantas}"`);
    if (width >= 768 && !(r.texts.reveal || []).length) problemsHere.push('the pinned scene has no label of whose eye it is');
    if (!r.legend) problemsHere.push('the styles legend line is missing (it is the label of the flat artworks)');
    // the other people's eyes carry "Example photo": pick the brown eye of the first group, every tile of it shows a chip
    const chips = await page.eval(`(async () => {
      document.querySelector('#gEyeChips [role=radio]:nth-child(3)')?.click();
      await new Promise((r) => setTimeout(r, 700));
      const tiles = [...document.querySelectorAll('.lp-tile-img')].filter((t) => t.offsetParent);
      return JSON.stringify([tiles.length, tiles.filter((t) => [...t.querySelectorAll('.lp-chip-ex')].some((c) => getComputedStyle(c).visibility !== 'hidden' && c.textContent.trim() === ${JSON.stringify(c.example.photo)})).length]);
    })()`);
    const [tiles, withChip] = JSON.parse(chips);
    if (!tiles || withChip !== tiles) problemsHere.push(`with another person's eye ${withChip} of ${tiles} tiles carry "${c.example.photo}"`);
    if (problemsHere.length) fail('labels', `${lang} ${width}px: ${problemsHere.join('; ')}`);
    else pass('labels', `${lang} ${width}px: every picture area is labelled, every picture has alt and size`);
    await page.close();
  }
}

// ---------------------------------------------------------------------------------------------------- phrases and ordering
async function checkPhrases() {
  console.log('phrases');
  for (const lang of LANGS) {
    const c = COPY[lang];
    const soon = c.bar.soon.split('. ')[0].replace(/\.$/, '');
    for (const state of ['closed', 'open']) {
      stub.open = state === 'open';
      stub.delay = 0;
      const page = await open({ lang, details: true });
      // wait for the answer of the stub to have been used
      await sleep(600);
      // innerText leaves out what is not rendered, and a section far from the screen is skipped (content-visibility, css/base.css): draw them all first
      await page.eval(NO_SKIP);
      await sleep(300);
      const text = await page.eval('document.body.innerText');
      const html = await page.eval('document.documentElement.outerHTML');
      const soonCount = (text.match(new RegExp(esc(soon), 'gi')) || []).length;
      const bad = BANNED.exec(text) || BANNED.exec(html.replace(/<script[\s\S]*?<\/script>/g, ''));
      const msgs = [];
      if (bad) msgs.push(`the banned claim "${bad[0]}"`);
      if (state === 'closed' && soonCount !== 3) msgs.push(`"${soon}" appears ${soonCount} times (bar, pricing notice, FAQ: exactly 3)`);
      if (state === 'open' && soonCount !== 0) msgs.push(`ordering is open and "${soon}" still appears ${soonCount} times`);
      if (lang === 'en' || lang === 'de') {
        const printing = lang === 'en' ? /Printing is not part of your order/gi : /Der Druck gehört nicht zur Bestellung/gi;
        const n = (text.match(printing) || []).length;
        if (n !== 6) msgs.push(`the line "printing is not part of your order" appears ${n} times (6: hero caption, wall, pricing, FAQ, polished edge, closing)`);
      }
      if (state === 'open') {
        const bar = await page.eval("document.getElementById('barText').textContent");
        if (bar !== c.bar.open) msgs.push(`the bar says "${bar}", the copy's open sentence is "${c.bar.open}"`);
      }
      if (msgs.length) fail('phrases', `${lang} ${state}: ${msgs.join('; ')}`);
      else pass('phrases', `${lang} ordering ${state}: no banned claim${state === 'closed' ? `, "${soon}" in 3 places` : ', no "opens soon"'}`);
      await page.close();
    }
  }
  stub.open = false;
}

// ---------------------------------------------------------------------------------------------------- dashes
async function checkDashes() {
  console.log('dashes');
  for (const lang of LANGS) {
    for (const m of ['', 'au']) {
      if (m && lang !== 'en' && lang !== 'de') continue;
      const page = await open({ lang, query: m ? `m=${m}` : '', details: true });
      const found = JSON.parse(await page.eval(String.raw`(() => {
        const DASH = new RegExp('[' + String.fromCharCode(0x2012, 0x2013, 0x2014, 0x2015, 0x2212) + ']'), SPACED = new RegExp('(^|[\\s' + String.fromCharCode(160) + '])-([\\s' + String.fromCharCode(160) + ']|$)');
        const bad = [];
        const check = (where, s) => { if (s && (DASH.test(s) || SPACED.test(s))) bad.push(where + ': ' + s.trim().slice(0, 60)); };
        const w = document.createTreeWalker(document.documentElement, NodeFilter.SHOW_TEXT);
        let n; while ((n = w.nextNode())) if (!/^(SCRIPT|STYLE)$/.test(n.parentElement.tagName)) check('text', n.nodeValue);
        for (const e of document.querySelectorAll('[alt],[aria-label],[title],[placeholder],meta[content]')) for (const a of ['alt', 'aria-label', 'title', 'placeholder', 'content']) check(a, e.getAttribute(a));
        check('title', document.title);
        return JSON.stringify(bad.slice(0, 8));
      })()`));
      if (found.length) fail('dashes', `${lang}${m ? ' ' + m : ''}: ${found.join(' | ')}`);
      else pass('dashes', `${lang}${m ? ' ' + m : ''}: none in any text node, alt, aria-label, title or the head`);
      await page.close();
    }
  }
}

// ---------------------------------------------------------------------------------------------------- anchors
async function checkAnchors() {
  console.log('anchors');
  const ids = ['reveal', 'wall', 'sizes', 'more', 'styles', 'how', 'pricing', 'closeups', 'trust', 'privacy', 'faq', 'final'];
  const cases = [['en', 375], ['en', 768], ['en', 1280], ['de', 375], ['lt', 1280], ['hu', 375]];
  for (const [lang, width] of quick ? cases.slice(0, 2) : cases) {
    const miss = [];
    for (const id of ids) {
      const page = await open({ lang, width, settle: false, hash: `#${id}` });
      // the hook lands the section once every lazy section is in: wait for that, no scrolling by us
      for (let i = 0; i < 80; i++) { if (await page.eval("document.querySelector('.lp-slot') === null && !!document.getElementById('faq')")) break; await sleep(100); }
      await sleep(700);
      const r = JSON.parse(await page.eval(`JSON.stringify((() => { const e = document.getElementById(${JSON.stringify(id)}); if (!e) return null; return { top: Math.round(e.getBoundingClientRect().top), max: Math.round(document.documentElement.scrollHeight - innerHeight - scrollY) }; })())`));
      // the section's top sits under the fixed header (scroll-padding-top 92 px); a section near the end may not be able to get there
      if (!r) miss.push(`#${id} does not exist`);
      else if (!(Math.abs(r.top - 92) <= 30 || (r.max <= 2 && r.top >= 0 && r.top < 92 + 30))) miss.push(`#${id} is ${r.top}px from the top (wanted about 92)`);
      await page.close();
    }
    if (miss.length) fail('anchors', `${lang} ${width}px, address with a fragment: ${miss.join('; ')}`);
    else pass('anchors', `${lang} ${width}px: ${ids.length} fragments land within 30 px of the header`);
  }
  // clicks on the header's links, desktop
  const page = await open({ lang: 'en', width: 1280 });
  const bad = [];
  for (const id of ['reveal', 'wall', 'styles', 'how', 'pricing', 'faq']) {
    await page.eval("window.scrollTo({ top: 0, behavior: 'instant' })");
    await sleep(200);
    await page.eval(`document.querySelector('#nav a[href="#${id}"]').click()`);
    await sleep(1600);
    const top = await page.eval(`Math.round(document.getElementById(${JSON.stringify(id)}).getBoundingClientRect().top)`);
    if (Math.abs(top - 92) > 30) bad.push(`#${id}: ${top}px`);
  }
  if (bad.length) fail('anchors', `a click on the header's link lands elsewhere: ${bad.join(', ')}`);
  else pass('anchors', "the header's six links land within 30 px of the header");
  await page.close();
}

// ---------------------------------------------------------------------------------------------------- focus
async function checkFocus() {
  console.log('focus');
  const page = await open({ lang: 'en', width: 1280 });
  const active = () => page.eval(`(() => { const a = document.activeElement; if (!a || a === document.body) return 'BODY'; const g = a.closest('[role=tablist],[role=radiogroup],[role=group]'); return (g ? (g.id || g.getAttribute('aria-label') || g.className) : 'none') + '|' + (a.id || a.textContent.trim().slice(0, 16)); })()`);
  // the eye colour dots only exist in the first group of the gallery: they go before the group tabs are moved
  const groups = [['#gEyeChips [aria-checked=true]', 'eye colours'], ['#gTabs [aria-selected=true]', 'style tabs'], ['#reveal .lp-pills [aria-checked=true]', 'reveal eyes'],
    ['#mats [aria-selected=true]', 'material tabs'], ['#arts [aria-checked=true]', 'artworks'], ['#sizeChips [aria-checked=true]', 'size chips']];
  for (const [sel, name] of groups) {
    await page.eval(`document.querySelector(${JSON.stringify(sel)}).scrollIntoView({ block: 'center', behavior: 'instant' }); document.querySelector(${JSON.stringify(sel)}).focus()`);
    const before = await active();
    await key(page, 'ArrowRight');
    const a1 = await active();
    await key(page, 'ArrowRight');
    const a2 = await active();
    const groupOf = (s) => s.split('|')[0];
    if (a1 === 'BODY' || a2 === 'BODY' || groupOf(a1) !== groupOf(before) || groupOf(a2) !== groupOf(before)) fail('focus', `${name}: focus ${before} -> ${a1} -> ${a2} after arrow keys`);
    else if (a1 === before) fail('focus', `${name}: the arrow key did not move to the next control`);
    else pass('focus', `${name}: focus stays in the group after arrow keys (${a1}, ${a2})`);
  }
  // the Reveal's range
  await page.eval("document.querySelector('.lp-cmp-range').scrollIntoView({ block: 'center', behavior: 'instant' }); document.querySelector('.lp-cmp-range').focus()");
  await sleep(1800);
  const v0 = +(await page.eval("document.querySelector('.lp-cmp-range').value"));
  await key(page, 'ArrowRight');
  const v1 = +(await page.eval("document.querySelector('.lp-cmp-range').value"));
  await key(page, 'End');
  const v2 = +(await page.eval("document.querySelector('.lp-cmp-range').value"));
  await key(page, 'Home');
  const v3 = +(await page.eval("document.querySelector('.lp-cmp-range').value"));
  if (!(v1 > v0 && v2 === 100 && v3 === 0)) fail('focus', `the Reveal range answers ArrowRight ${v0} -> ${v1}, End ${v2}, Home ${v3}`);
  else pass('focus', 'the Reveal range is a native range: ArrowRight, End, Home work');
  // language buttons
  for (const [from, to] of [['en', 'de'], ['de', 'lt'], ['lt', 'hu'], ['hu', 'en']]) {
    await page.eval("window.scrollTo({ top: 0, behavior: 'instant' })");
    await page.eval(`document.querySelector('#langSeg button[lang=${to}]').focus(); document.activeElement.click()`);
    await sleep(900);
    const r = JSON.parse(await page.eval(`JSON.stringify({ a: document.activeElement.getAttribute('lang') + ':' + document.activeElement.getAttribute('aria-pressed'), html: document.documentElement.lang, h1: document.getElementById('h1').textContent, url: location.search })`));
    const want = COPY[to].hero.title;
    if (r.a !== `${to}:true` || r.html !== to || r.h1 !== want || !r.url.includes(`lang=${to}`)) fail('focus', `switching ${from} -> ${to}: focus ${r.a}, html lang ${r.html}, h1 "${r.h1.slice(0, 30)}", url ${r.url}`);
    else pass('focus', `language ${from} -> ${to}: focus stays on the button, the page speaks ${to} (words, html lang, address)`);
  }
  await page.close();
  // currency (ordering open: the page prints a price only for a style that can be bought now, so the closed page has no price to be in euro or A$)
  stub.open = true;
  const au = await open({ lang: 'en', query: 'm=au' });
  await au.eval("document.querySelector('#pricing .lp-cur-seg button[data-market=eu]').scrollIntoView({ block: 'center', behavior: 'instant' }); document.querySelector('#pricing .lp-cur-seg button[data-market=eu]').focus(); document.activeElement.click()");
  await sleep(900);
  const cur = JSON.parse(await au.eval(`(() => { const c = document.getElementById('pricing').cloneNode(true); c.querySelectorAll('.lp-cur-sw').forEach((e) => e.remove()); const t = c.textContent; return JSON.stringify({ pressed: document.activeElement.getAttribute('aria-pressed'), data: document.activeElement.getAttribute('data-market'), eur: t.includes(String.fromCharCode(0x20ac)), aud: t.includes('A$'), url: location.search }); })()`));
  if (cur.pressed !== 'true' || !cur.eur || cur.aud) fail('focus', `currency switch to euro: pressed ${cur.pressed}, euro ${cur.eur}, A$ left ${cur.aud}`);
  else pass('focus', 'currency A$ -> euro: focus stays on the button, every price of the pricing block is in euro');
  await au.close();
  stub.open = false;
}

// ---------------------------------------------------------------------------------------------------- overflow
const PROBE = String.raw`(() => {
  const out = { cut: [], clip: [], over: [] };
  const vis = (el) => { const r = el.getBoundingClientRect(); if (!r.width || !r.height) return false; const cs = getComputedStyle(el); return cs.visibility !== 'hidden' && cs.display !== 'none'; };
  const name = (el) => (el.id ? '#' + el.id : el.tagName.toLowerCase() + '.' + String(el.className).split(' ')[0]);
  for (const root of [document.getElementById('main'), document.querySelector('header.lp-hdr'), document.querySelector('footer')].filter(Boolean)) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = walker.nextNode())) {
      const el = n.parentElement;
      if (!el || !vis(el) || /^(SCRIPT|STYLE)$/.test(el.tagName)) continue;
      if (el.closest('[aria-hidden="true"]') && !el.closest('.lp-vis-chip, .lp-frame-chip')) continue;
      const re = new RegExp('[^\\s\\-' + String.fromCharCode(0x2010, 0x2011) + ']+', 'g'); let m;
      while ((m = re.exec(n.nodeValue))) {
        if (m[0].length < 5) continue;
        const rg = document.createRange(); rg.setStart(n, m.index); rg.setEnd(n, m.index + m[0].length);
        const rects = [...rg.getClientRects()].filter((r) => r.width > 0.5);
        if (rects.length < 2) continue;
        const tops = rects.map((r) => Math.round(r.top));
        if (Math.max(...tops) - Math.min(...tops) <= 4) continue;
        // broken across lines: fine when the word would fit its box on one line (hyphenation), a cut when it cannot
        let box = el; while (getComputedStyle(box).display.startsWith('inline') && box.parentElement) box = box.parentElement;
        const bs = getComputedStyle(box);
        const avail = box.clientWidth - parseFloat(bs.paddingLeft) - parseFloat(bs.paddingRight);
        const probe = document.createElement('span');
        probe.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap;hyphens:manual;overflow-wrap:normal';
        probe.textContent = m[0];
        el.appendChild(probe);
        const one = probe.getBoundingClientRect().width;
        probe.remove();
        if (one > avail + 0.5) out.cut.push(name(el) + ': ' + m[0] + ' (' + Math.round(one) + ' px in ' + Math.round(avail) + ')');
      }
    }
  }
  const iw = document.documentElement.clientWidth;
  out.sw = document.documentElement.scrollWidth; out.iw = iw;
  const inScroller = (e) => { let p = e.parentElement; while (p && p !== document.body) { const cs = getComputedStyle(p); if (/(auto|scroll|hidden|clip)/.test(cs.overflowX) && p.scrollWidth >= p.clientWidth) return true; p = p.parentElement; } return false; };
  for (const e of document.querySelectorAll('body *')) {
    const r = e.getBoundingClientRect(); if (!r.width || !r.height) continue;
    if (getComputedStyle(e).position === 'fixed') continue;
    if (r.right > iw + 1 && !inScroller(e)) out.over.push(name(e) + ' r=' + Math.round(r.right));
  }
  for (const e of document.querySelectorAll('a.lp-btn, button, .lp-pill, .lp-nav a, .lp-seg button, .lp-chip-ex, .lp-vis-chip, summary, [role=tab], [role=radio]')) {
    if (!vis(e)) continue;
    if (e.scrollWidth > e.clientWidth + 2 && getComputedStyle(e).overflowX !== 'visible') out.clip.push((e.textContent || '').trim().slice(0, 30));
    if (e.matches('a.lp-btn') && e.getBoundingClientRect().width > iw - 2) out.clip.push('wider than the screen: ' + (e.textContent || '').trim().slice(0, 30));
  }
  return JSON.stringify(out);
})()`;
async function checkOverflow() {
  console.log('overflow');
  // ordering closed at every width; ordering open (other words in the pricing block, the FAQ and the phone picture of step 2) at the narrow ones
  for (const lang of LANGS) {
    const bad = [];
    for (const [open_, widths] of [[false, WIDTHS], [true, [320, 375, 1280]]]) {
      stub.open = open_;
      for (const width of widths) {
        const page = await open({ lang, width, details: true });
        await sleep(open_ ? 500 : 0);
        const r = JSON.parse(await page.eval(PROBE));
        const here = [];
        if (r.cut.length) here.push(`word cut: ${[...new Set(r.cut)].slice(0, 5).join(' | ')}`);
        if (r.sw > r.iw) here.push(`horizontal scroll ${r.sw} > ${r.iw}`);
        if (r.over.length) here.push(`beyond the edge: ${r.over.slice(0, 4).join(', ')}`);
        if (r.clip.length) here.push(`clipped: ${[...new Set(r.clip)].slice(0, 4).join(' | ')}`);
        if (here.length) bad.push(`${width}px${open_ ? ' ordering open' : ''}: ${here.join('; ')}`);
        await page.close();
      }
    }
    stub.open = false;
    if (bad.length) fail('overflow', `${lang}: ${bad.join(' // ')}`);
    else pass('overflow', `${lang}: no overflow, no cut word, no clipped button at ${WIDTHS.join(', ')} px (and with ordering open at 320, 375, 1280)`);
  }
}

// ---------------------------------------------------------------------------------------------------- links
async function checkLinks() {
  console.log('links');
  const cases = [['en', ''], ['de', ''], ['lt', ''], ['hu', ''], ['en', 'm=au'], ['de', 'm=au'], ['hu', 'm=hu'], ['lt', 'm=lt']];
  for (const [lang, m] of quick ? cases.slice(0, 5) : cases) {
    const page = await open({ lang, query: m });
    const r = JSON.parse(await page.eval(`JSON.stringify({ legal: [...document.querySelectorAll('#legalNav a')].map((a) => a.getAttribute('href')), try: [...document.querySelectorAll('a.lp-btn-gold, a.lp-btn-line')].map((a) => a.getAttribute('href')).filter((h) => !h.startsWith('mailto:')) })`));
    const market = m.replace('m=', '');
    const msgs = [];
    if (r.legal.length !== 5) msgs.push(`${r.legal.length} legal links (4 documents and the withdrawal function)`);
    for (const h of r.legal) {
      if (!new RegExp(`^/(privacy|terms|withdrawal|imprint|order)\\?[^#]*lang=${lang}(&|$)`).test(h)) msgs.push(`${h} has no lang=${lang}`);
      if (market && !h.includes(`m=${market}`)) msgs.push(`${h} lacks m=${market}`);
      if (!market && /[?&]m=/.test(h)) msgs.push(`${h} names a market on the default market`);
    }
    for (const h of r.try) {
      if (!h.startsWith(`/try?lang=${lang}`)) msgs.push(`call to action ${h}`);
      if (market && !h.includes(`m=${market}`)) msgs.push(`call to action ${h} lacks m=${market}`);
    }
    if (!r.try.length) msgs.push('no call to action found');
    if (msgs.length) fail('links', `${lang} ${m || 'default market'}: ${[...new Set(msgs)].slice(0, 5).join('; ')}`);
    else pass('links', `${lang} ${m || 'default market'}: ${r.legal.length} legal links and ${r.try.length} calls to action carry the language${market ? ' and m=' + market : ''}`);
    await page.close();
  }
}

// ---------------------------------------------------------------------------------------------------- ordering
async function checkOrdering() {
  console.log('ordering');
  for (const lang of ['en', 'de']) {
    const c = COPY[lang];
    stub.open = false;
    const closed = await open({ lang });
    const t0 = JSON.parse(await closed.eval(`JSON.stringify({ bar: document.getElementById('barText').textContent, faq: [...document.querySelectorAll('#faq summary')].map((s) => s.textContent.trim()) })`));
    await closed.close();
    stub.open = true;
    const opened = await open({ lang });
    await sleep(500);
    const t1 = JSON.parse(await opened.eval(`JSON.stringify({ bar: document.getElementById('barText').textContent, faq: [...document.querySelectorAll('#faq summary')].map((s) => s.textContent.trim()), notice: document.querySelector('#pricing').innerText })`));
    await opened.close();
    stub.open = false;
    const msgs = [];
    if (t0.bar !== c.bar.soon) msgs.push(`closed: the bar says "${t0.bar}"`);
    if (t1.bar !== c.bar.open) msgs.push(`open: the bar says "${t1.bar}"`);
    const item = c.faq.items.find((i) => i.qOpen);
    if (item) {
      if (!t0.faq.includes(item.q)) msgs.push(`closed: the FAQ lacks "${item.q}"`);
      if (!t1.faq.includes(item.qOpen)) msgs.push(`open: the FAQ lacks "${item.qOpen}"`);
    }
    if (msgs.length) fail('ordering', `${lang}: ${msgs.join('; ')}`);
    else pass('ordering', `${lang}: closed and open states show their own bar sentence and FAQ question`);
  }
}

// ---------------------------------------------------------------------------------------------------- axe
async function checkAxe() {
  console.log('axe');
  const path = [opt('--axe'), process.env.AXE_CORE, join(ROOT, 'node_modules/axe-core/axe.min.js')].find((p) => p && existsSync(p));
  if (!path) { info('axe', 'skipped: axe-core is not installed (pass --axe <axe.min.js> or set AXE_CORE; the repository takes no new dependency)'); return; }
  const AXE = readFileSync(path, 'utf8');
  const states = [['en', 375, ''], ['en', 1280, ''], ['de', 375, ''], ['lt', 375, ''], ['hu', 375, ''], ['hu', 1280, ''], ['en', 1280, 'm=au'], ['en', 1280, 'open']];
  for (const [lang, width, state] of quick ? states.slice(0, 3) : states) {
    stub.open = state === 'open';
    const page = await open({ lang, width, query: state.startsWith('m=') ? state : '', details: true });
    await page.eval(NO_SKIP);   // axe judges what is rendered: a section far from the screen is skipped (content-visibility) and would pass for free
    await sleep(500);
    await page.eval(AXE);
    const r = JSON.parse(await page.eval(`axe.run(document, { resultTypes: ['violations'] }).then((r) => JSON.stringify(r.violations.map((v) => [v.id, v.impact, v.nodes.length, v.nodes.slice(0, 2).map((n) => n.target.join(' '))])))`));
    if (r.length) fail('axe', `${lang} ${width}px ${state}: ${r.map((v) => `${v[0]} (${v[1]}, ${v[2]}: ${v[3].join(' ; ')})`).join(', ')}`);
    else pass('axe', `${lang} ${width}px ${state || 'default'}: 0 violations with every details open`);
    await page.close();
  }
  stub.open = false;
}

// ---------------------------------------------------------------------------------------------------- vitals
async function checkVitals() {
  console.log('vitals');
  const phone = { width: 375, height: 812, mobile: true, dpr: 2.6, vitals: true, cpu: 4, throttle: { latency: 150, down: 200000, up: 93750 }, settle: false };
  const runs = [];
  for (let i = 0; i < (quick ? 1 : 3); i++) {
    stub.open = true;
    stub.delay = 2500;
    const page = await open({ lang: 'en', ...phone });
    await sleep(9500);
    const v = JSON.parse(await page.eval(`JSON.stringify({ lcp: window.__lcp.at(-1), cls: window.__cls, shifts: window.__shifts, bar: document.getElementById('barText').textContent })`));
    await page.close();
    runs.push(v);
    if (v.bar !== COPY.en.bar.open) fail('vitals', `the ordering flip did not reach the page (the bar says "${v.bar}")`);
  }
  stub.open = false;
  stub.delay = 0;
  const lcps = runs.map((r) => r.lcp[0]).sort((a, b) => a - b);
  const worstCls = Math.max(...runs.map((r) => r.cls));
  if (lcps[lcps.length - 1] > 2500) fail('vitals', `phone LCP ${lcps.join(', ')} ms: over the 2.5 s budget`);
  else if (lcps[Math.floor(lcps.length / 2)] > 1600) info('vitals', `phone LCP median ${lcps[Math.floor(lcps.length / 2)]} ms is over the 1.6 s target (${lcps.join(', ')})`);
  else pass('vitals', `phone slow 4G LCP ${lcps.join(', ')} ms (element ${runs[0].lcp[1]}), under the 1.6 s target`);
  if (worstCls > 0.05) fail('vitals', `CLS ${worstCls.toFixed(4)} with the ordering flip: ${JSON.stringify(runs.find((r) => r.cls === worstCls).shifts)}`);
  else pass('vitals', `CLS ${runs.map((r) => r.cls.toFixed(4)).join(', ')} with the ordering flip after 2.5 s (budget 0.05)`);
  // A visitor the server places in Australia: the offer of A$ comes with the API answer, which the head of index.html asked for at the first
  // byte and React waited for (at most 350 ms) before its first render: with an answer in 1.2 s the offer is part of that render and
  // moves nothing; with an answer after 3 s it is added above the hero afterwards, as it always was, and that is a note, not a verdict.
  for (const [delay, judged] of [[1200, true], [3000, false]]) {
    stub.suggest = 'au';
    stub.delay = delay;
    const hint = await open({ lang: 'en', ...phone });
    await sleep(delay + 5500);
    const h = JSON.parse(await hint.eval('JSON.stringify({ cls: window.__cls, offered: !!document.querySelector(".lp-market") })'));
    await hint.close();
    stub.suggest = null;
    stub.delay = 0;
    if (judged) {
      if (!h.offered) fail('vitals', `a visitor the server places in Australia (answer after ${delay} ms): the offer of A$ did not appear`);
      else if (h.cls > 0.05) fail('vitals', `the offer of A$ (answer after ${delay} ms) moved the page: CLS ${h.cls.toFixed(3)}`);
      else pass('vitals', `the offer of A$ for a visitor placed in Australia (answer after ${delay} ms) is in the first render: CLS ${h.cls.toFixed(4)}`);
    } else {
      info('vitals', `the same offer with an answer after ${delay} ms: CLS ${h.cls.toFixed(3)} (${h.offered ? 'it came after the first render and pushed the hero down' : 'not offered'})`);
    }
  }
}

// ---------------------------------------------------------------------------------------------------- resilience
/** A page with some request URLs blocked from the first byte (Network.setBlockedURLs takes patterns with *). */
async function openBlocked(patterns, { width = 375, height = 812, query = '' } = {}) {
  const wipe = await chrome.page({ width: 400, height: 300 });
  await wipe.goto(`${origin}/imprint?lang=en`);
  await wipe.loaded();
  await wipe.send('Storage.clearDataForOrigin', { origin, storageTypes: 'all' }).catch(() => undefined);
  await wipe.close();
  const page = await chrome.page({ width, height, mobile: width < 800, dpr: width < 800 ? 2 : 1 });
  // a file this browser has fetched before comes from its cache and is never asked for again, so a block would not touch it
  await page.send('Network.setCacheDisabled', { cacheDisabled: true });
  await page.send('Network.setBlockedURLs', { urls: patterns });
  // which requests the block really stopped (a check that blocks nothing proves nothing)
  const urls = new Map();
  page.blocked = [];
  page.on((e) => {
    if (e.method === 'Network.requestWillBeSent') urls.set(e.params.requestId, e.params.request.url);
    if (e.method === 'Network.loadingFailed' && e.params.blockedReason) page.blocked.push(urls.get(e.params.requestId) || '');
  });
  await page.goto(`${origin}/${query}`);
  return page;
}

async function checkResilience() {
  console.log('resilience');
  const files = readdirSync(join(dist, 'assets')).filter((f) => f.endsWith('.js'));
  const SECTIONS = ['Reveal', 'Wall', 'StyleGallery', 'HowItWorks', 'Pricing', 'CloseUps', 'Trust', 'Faq', 'ClosingScene', 'SizeGuide', 'MoreRooms'];
  const picked = quick ? ['Faq', 'Wall', 'SizeGuide'] : SECTIONS;
  for (const name of picked) {
    const file = files.find((f) => f.startsWith(`${name}-`));
    if (!file) { fail('resilience', `no chunk ${name}-*.js in ${dist}/assets: the section list of this check is out of date`); continue; }
    const page = await openBlocked([`*/assets/${file}`]);
    await sleep(1500);
    await page.eval('window.__marker = 1');
    await sleep(5500);
    const r = JSON.parse(await page.eval(`JSON.stringify({ hdr: !!document.getElementById('hdr'), hero: !!document.querySelector('.lp-hero h1'), ftr: !!document.querySelector('.lp-ftr'),
      root: document.getElementById('root').childElementCount, h: document.documentElement.scrollHeight,
      marker: window.__marker === 1, others: document.querySelectorAll('main > section.lp-sec, main > .lp-sheet > section.lp-sec, main > section.lp-final').length })`));
    const msgs = [];
    if (!page.blocked.some((u) => u.includes(file))) msgs.push(`the block did not apply (no request for ${file} was stopped), so nothing was tested`);
    if (!r.hdr || !r.hero || !r.ftr) msgs.push(`the page lost ${[!r.hdr && 'the header', !r.hero && 'the hero', !r.ftr && 'the footer'].filter(Boolean).join(', ')}`);
    if (!r.root) msgs.push('React left #root empty (a blank page)');
    // the blocked section is the one that is missing: the others are all there
    const total = SECTIONS.filter((s) => !['SizeGuide', 'MoreRooms'].includes(s)).length;
    if (!['SizeGuide', 'MoreRooms'].includes(name) && r.others !== total - 1) msgs.push(`${r.others} sections are on the page, ${total - 1} expected (the blocked one missing, the others there)`);
    if (r.h < 2500) msgs.push(`the page is ${r.h} px high: the other sections are gone too`);
    if (!r.marker) msgs.push('the page reloaded itself');
    if (msgs.length) fail('resilience', `${name} blocked: ${msgs.join('; ')}`);
    else pass('resilience', `${name} blocked: the page stays (${r.others} sections, ${r.h} px, no reload)`);
    await page.close();
  }
}

async function checkSkew() {
  console.log('skew');
  const html = readFileSync(join(dist, 'index.html'), 'utf8');
  const main = /\/assets\/main-[\w-]+\.js/.exec(html);
  const faq = readdirSync(join(dist, 'assets')).find((f) => f.startsWith('Faq-') && f.endsWith('.js'));
  if (!main || !faq) { fail('skew', 'no main or Faq chunk in the build'); return; }
  for (const deployed of [true, false]) {
    skew.on = true; skew.rootHits = 0; skew.chunk = faq; skew.mainFile = deployed ? main[0] : '/assets/no-such-script-name.js';
    const page = await openBlocked([], {});
    await sleep(7000);
    const hits1 = skew.rootHits;
    await sleep(3500);
    const hits2 = skew.rootHits;
    skew.on = false;
    const msgs = [];
    if (deployed) {
      if (hits1 !== 3) msgs.push(`/ was asked for ${hits1} times (3 expected: the page, the freshness check, the one reload)`);
      if (hits2 !== hits1) msgs.push(`the page kept asking for / (${hits1} then ${hits2}): a reload loop`);
    } else {
      if (hits1 !== 2) msgs.push(`/ was asked for ${hits1} times (2 expected: the page and the freshness check; more means the page reloaded although only the network failed)`);
    }
    if (msgs.length) fail('skew', `${deployed ? 'a new deploy' : 'a failed chunk, same deploy'}: ${msgs.join('; ')}`);
    else pass('skew', deployed ? 'a new deploy under an open page: reloaded once, no loop' : 'a failed chunk with the same deploy: no reload, the page stays');
    await page.close();
  }
  skew.on = false; skew.chunk = '';
}

async function checkStall() {
  console.log('stall');
  const wall = readdirSync(join(dist, 'assets')).find((f) => f.startsWith('Wall-') && f.endsWith('.js'));
  if (!wall) { fail('stall', 'no Wall chunk in the build'); return; }
  skew.on = true; skew.hang = true; skew.chunk = wall; skew.rootHits = 0; skew.mainFile = '/assets/no-such-script-name.js';
  const page = await openBlocked([], {});
  await sleep(11000);
  const r = JSON.parse(await page.eval(`JSON.stringify({ wallHole: !!document.querySelector('#wall.lp-slot'), mounted: [...document.querySelectorAll('main > section:not(.lp-slot), main > .lp-sheet > section:not(.lp-slot)')].map((s) => s.id).filter(Boolean) })`));
  skew.on = false; skew.hang = false; skew.chunk = '';
  const want = ['reveal', 'styles', 'how', 'pricing', 'closeups', 'trust', 'faq', 'final'];
  const missing = want.filter((id) => !r.mounted.includes(id));
  if (!r.wallHole) fail('stall', 'the stalled section is not waiting as an empty slot');
  else if (missing.length) fail('stall', `with the wall chunk stalled these sections never mounted: ${missing.join(', ')}`);
  else pass('stall', 'the wall chunk stalled: the other eight sections mounted all the same, the wall waits as an empty slot');
  await page.close();
}

// ---------------------------------------------------------------------------------------------------- glass
async function checkGlass() {
  console.log('glass');
  for (const width of [375, 1280]) {
    const page = await open({ lang: 'en', width, settle: false });
    await sleep(2500);
    await page.eval('window.scrollTo({ top: 400, behavior: "instant" })');
    await sleep(500);
    const r = JSON.parse(await page.eval(`JSON.stringify({ hdr: getComputedStyle(document.getElementById('hdr')).backdropFilter, chip: getComputedStyle(document.querySelector('.lp-frame-chip')).backdropFilter, chipBg: getComputedStyle(document.querySelector('.lp-frame-chip')).backgroundColor })`));
    const msgs = [];
    if (!r.hdr || r.hdr === 'none') msgs.push(`the solid header has backdrop-filter "${r.hdr}"`);
    // the chips lie on artwork: nothing blurs it (charter AC-2), the chip is solid enough to read on its own (the two fixed bars are the page's only blurred surfaces)
    if (r.chip !== 'none') msgs.push(`the hero chip blurs the artwork behind it (backdrop-filter "${r.chip}")`);
    const alpha = /rgba?\((?:[^,]+,){3}\s*([\d.]+)\)/.exec(r.chipBg);
    if (!alpha || +alpha[1] < 0.9) msgs.push(`the hero chip is not solid enough without a blur (${r.chipBg})`);
    if (width < 768) {
      await page.eval('window.scrollTo({ top: 1500, behavior: "instant" })');
      await sleep(700);
      const s = await page.eval(`getComputedStyle(document.querySelector('.lp-sticky')).backdropFilter`);
      if (!s || s === 'none') msgs.push(`the sticky phone bar has backdrop-filter "${s}"`);
    }
    if (msgs.length) fail('glass', `${width}px: ${msgs.join('; ')}`);
    else pass('glass', `${width}px: the header${width < 768 ? ' and the sticky bar' : ''} are frosted (${r.hdr}), the hero chip is solid and blurs nothing`);
    await page.close();
  }
}

// ---------------------------------------------------------------------------------------------------- shellclick
async function checkShellClick() {
  console.log('shellclick');
  const page = await openBlocked(['*/assets/main-*.js']);
  await sleep(2500);
  // the static first screen is on screen and React has not started (its script is blocked)
  const before = await page.eval("JSON.stringify({ shell: !!document.getElementById('shell'), root: document.getElementById('root').childElementCount, lang: document.documentElement.lang })");
  const b = JSON.parse(before);
  if (!b.shell || b.root) { fail('shellclick', `the test setup failed (${before})`); await page.close(); return; }
  await page.eval("document.querySelector('#langSeg button[lang=de]').click()");
  await sleep(300);
  const r = JSON.parse(await page.eval(`JSON.stringify({ lang: document.documentElement.lang, pressed: document.querySelector('#langSeg button[aria-pressed=true]')?.getAttribute('lang'),
    focus: document.activeElement?.getAttribute('lang'), stored: localStorage.getItem('snapeyes.lang'), url: location.search, h1: document.querySelector('#shell h1')?.textContent || '' })`));
  const msgs = [];
  if (r.lang !== 'de') msgs.push(`html lang is "${r.lang}"`);
  if (r.pressed !== 'de') msgs.push(`the pressed button is "${r.pressed}"`);
  if (r.focus !== 'de') msgs.push(`the focus is on "${r.focus}" (the markup was replaced)`);
  if (r.stored !== 'de') msgs.push(`the choice was not remembered ("${r.stored}")`);
  if (!/lang=de/.test(r.url)) msgs.push(`the address has "${r.url}"`);
  if (r.h1.trim() !== COPY.de.hero.title) msgs.push(`the headline is "${r.h1.trim().slice(0, 40)}", not the German "${COPY.de.hero.title.slice(0, 40)}"`);
  // and back to English from the German shell (the English markup is kept)
  await page.eval("document.querySelector('#langSeg button[lang=en]').click()");
  await sleep(200);
  const back = await page.eval("document.documentElement.lang + '|' + document.querySelector('#shell h1').textContent");
  if (back !== `en|${COPY.en.hero.title}`) msgs.push(`back to English gives "${back.slice(0, 60)}"`);
  // React starts now (the script is let through) and speaks what the visitor chose
  await page.send('Network.setBlockedURLs', { urls: [] });
  await page.goto(`${origin}/?lang=de`);
  await page.loaded();
  for (let i = 0; i < 60 && !(await page.eval("document.getElementById('root').childElementCount > 0")); i++) await sleep(100);
  const live = JSON.parse(await page.eval("JSON.stringify({ lang: document.documentElement.lang, pressed: document.querySelector('#langSeg button[aria-pressed=true]')?.getAttribute('lang'), shell: !!document.getElementById('shell') })"));
  if (live.lang !== 'de' || live.pressed !== 'de' || live.shell) msgs.push(`after React started: ${JSON.stringify(live)}`);
  if (msgs.length) fail('shellclick', msgs.join('; '));
  else pass('shellclick', 'a tap on DE before React ran switched the first screen, kept the choice and the focus; React then started in German');
  await page.close();
}

// ---------------------------------------------------------------------------------------------------- offers
async function checkOffers() {
  console.log('offers');
  const cases = [
    ['en', 'au', true], ['de', 'au', true], ['lt', 'au', false], ['hu', 'au', false],
    ['en', 'hu', true], ['lt', 'hu', true], ['hu', 'hu', true],
  ];
  for (const [lang, suggest, want] of cases) {
    stub.suggest = suggest;
    stub.delay = 0;
    const page = await open({ lang, width: 375, settle: false });
    await sleep(2500);
    const offered = await page.eval('!!document.querySelector(".lp-market")');
    stub.suggest = null;
    if (offered !== want) fail('offers', `${lang} reader, the server suggests ${suggest}: the offer is ${offered ? 'shown' : 'not shown'}, it should be ${want ? 'shown' : 'not shown'}`);
    else pass('offers', `${lang} reader, the server suggests ${suggest}: ${offered ? 'offered' : 'not offered'}`);
    await page.close();
  }
}

// ---------------------------------------------------------------------------------------------------- run
const checks = { labels: checkLabels, phrases: checkPhrases, dashes: checkDashes, anchors: checkAnchors, focus: checkFocus, overflow: checkOverflow, links: checkLinks, ordering: checkOrdering, axe: checkAxe, resilience: checkResilience, skew: checkSkew, stall: checkStall, glass: checkGlass, shellclick: checkShellClick, offers: checkOffers, vitals: checkVitals };
try {
  for (const [name, fn] of Object.entries(checks)) {
    if (!wants(name)) continue;
    try {
      await fn();
    } catch (e) {
      fail(name, `the check itself stopped: ${e instanceof Error ? e.stack : String(e)}`);
    }
  }
} finally {
  await chrome.close();
  await site.close();
}
console.log(problems.length ? `\nlanding check FAILED (${problems.length}):\n  ${problems.join('\n  ')}` : `\nlanding check ok${notes.length ? ` (${notes.length} notes)` : ''}`);
process.exit(problems.length ? 1 : 0);
