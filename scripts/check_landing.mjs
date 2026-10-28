// The checks of the landing page as a whole, in real Chrome, against a build (dist/) served the way Vercel serves it, with a stub of
// the two API calls the page makes (/api/health, /api/checkout). Not part of `vite build` (it needs Chrome and takes minutes);
// run it after a build:
//   npm run build && npm run check:landing
//   node scripts/check_landing.mjs [--dist dist] [--only labels,phrases,...] [--quick] [--axe <axe.min.js>] [--mutate "<js>"]
// (--mutate runs a snippet in every settled page, a deliberate defect to see that a check really fails: documented in the README.)
//
// What it checks (each name is a value of --only):
//   labels     every picture area of the page (wall stage, the four rooms, the polished edge, the crop, the tiles of the
//              style gallery, the closing scene) carries its label ("Example", "Visualisation", "Example photo", in the
//              page's own language: one word since the lean pass of 2026-10-22, no "AI" in it) INSIDE the picture; the hero's globe of artworks
//              (2026-10-22) carries its honest line under the stage, in its own figure ("our own eye and example photos, not customers"), and every
//              artwork on it is a button that says whose eyes it shows; every picture has alt, width and height
//   phrases    no "ready to print", "druckfertig", "100 percent", "museum glass" (the banned claims of scripts/check_texts.mjs) in the
//              visible text, in any of the four languages; "Ordering opens soon" in exactly three places while ordering is not
//              open and in none once it is (the stub flips); "Printing is not part of your order" exactly in the price list and the FAQ
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
//              not blank and does not reload itself in a loop; with the globe's chunk blocked the hero keeps its poster, whole
//   skew       a new deploy under an open page (the old chunk is a 404 and the server's index.html names another script): the page reloads
//              itself once, not in a loop; a chunk that fails while index.html is still the page's own does not reload it
//   stall      one chunk whose request is never answered (a stalled connection) does not hold the sections behind it back
//   glass      the frosted blur of the header and the sticky phone button is really applied (a build that dropped the unprefixed
//              backdrop-filter once left it off in Chrome, Edge and Firefox), and nothing on the hero's globe blurs the artworks (charter AC-2)
//   shellclick a tap on a language button of the static first screen BEFORE the page's script has run switches the language, remembers it,
//              keeps the focus on the new button, and the page that React then starts speaks that language
//   offers     the offer of another currency: A$ only to a reader of English or German (the Australian edition has no other language), the
//              forint offer to every language
//   guide      (2026-10-22) the guide video of the first step of "How it works" (src/shared/GuideVideo.tsx): on a phone it asks for no video file while the first
//              screens are read, then for the page language's square cut when its step comes near, plays it muted and inline while half of it is on screen
//              and stops when it leaves; under reduced motion it shows its poster with a play button and asks for nothing; the poster holds the box (no shift)
//   globe      (2026-10-22) the hero's globe (src/landing/globe): its chunk is asked for only after the page's load, and not while the hero is off the
//              screen; reduced motion keeps it still and a tap opens an artwork in place; the keyboard (one tab stop, the arrows, Enter onto the button,
//              Escape back to the artwork, the closed words out of the tab order); a tap shows the style's name, whose eyes it shows, Soon while
//              ordering is closed, and one button to /try in the page's language; a tap beside it closes it; a vertical swipe on it scrolls the page
//              and a sideways one turns it without scrolling; (the owner's review of 2026-10-23) after an upward drag it goes on turning that way
//              at its calm speed, with no swing back to the equator, and no disc lies outside the sphere's outline, at rest or tilted
//   vitals     phone, slow 4G, CPU x4 (BUILD_PLAN section 5): LCP under 2.5 s (a warning above the 1.6 s target), CLS under 0.05, with
//              the ordering flip mocked (the stub answers "open" after 2.5 s: the bar sentence changes in a page that is on screen)
// Exit code 1 when any check fails.
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { launch, sleep } from './lib/cdp.mjs';
import { landingFile } from './lib/langheads.mjs';
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

const LANGS = ['en', 'de', 'lt', 'hu', 'hr'];
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
    const html = readFileSync(join(dist, landingFile('en')), 'utf8').split(skew.mainFile).join('/assets/main-NEWDEPLOY.js');
    res.writeHead(200, { 'content-type': 'text/html', 'cache-control': 'no-store' });
    res.end(html);
    return true;
  }
  if (skew.on && skew.hang && skew.chunk && url.pathname.includes(skew.chunk)) return true;   // a stalled connection: the request is never answered
  if (skew.on && skew.chunk && url.pathname.includes(skew.chunk)) { res.writeHead(404, { 'content-type': 'text/plain' }); res.end('gone'); return true; }
  if (url.pathname === '/api/health') { later({ stripe: true, stripe_live: false, email: false }); return true; }
  if (url.pathname === '/api/checkout') { later(checkoutAnswer(ROOT, { open: stub.open, suggest: stub.suggest, ticked: stub.ticked ?? stub.open })); return true; }
  if (url.pathname.startsWith('/api/')) { res.writeHead(404, { 'content-type': 'application/json' }); res.end('{}'); return true; }
  return false;
};
if (!existsSync(join(dist, landingFile('en')))) { console.error(`no build in ${dist}: run npm run build first`); process.exit(2); }
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
      const AREAS = [['hero', '.lp-hero-fig', '.lp-globe-note', 1], ['stage', '#stage', '.lp-vis-chip', 1], ['rooms', '#rail figure > div', '.lp-vis-chip', 4],
        ['edge', '.lp-edge-img', '.lp-vis-chip', 1], ['crop', '.lp-cu-img', '.lp-cu-badge', 1], ['final', '.lp-final', '.lp-final-chip', 1],
        ['reveal', '.lp-rv-frame', '.lp-rv-who', 1]];   // the pinned scene's frame (768 px and up) and the phone's own (up to 767 px): both are here with motion allowed
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
      // the globe's artworks (once its chunk is in): each a button whose label ends with whose eyes it shows
      out.discs = [...document.querySelectorAll('#heroGlobe .lp-gl-disc')].map((b) => b.tagName + '|' + (b.getAttribute('aria-label') || ''));
      for (const i of document.querySelectorAll('main img')) {
        if (i.getAttribute('alt') === null) out.imgs.push('no alt: ' + (i.currentSrc || i.src).split('/').pop());
        if (!i.getAttribute('width') || !i.getAttribute('height')) out.imgs.push('no size: ' + (i.currentSrc || i.src).split('/').pop());
      }
      return JSON.stringify(out);
    })()`));
    const problemsHere = [...r.miss, ...r.imgs.slice(0, 5)];
    const wantVis = c.example.vis;
    for (const name of ['stage', 'rooms', 'edge', 'final']) for (const t of r.texts[name] || []) if (t !== wantVis) problemsHere.push(`${name} label "${t}", the language says "${wantVis}"`);
    // the globe shows flat artworks (our own eye and example photos), not a visualisation: its line says so, and each artwork says whose eyes it shows
    for (const t of r.texts.hero || []) if (t !== c.hero.globeNote) problemsHere.push(`hero line "${t}", the language says "${c.hero.globeNote}"`);
    const prov = [c.styles.eyeNote.own, c.styles.eyeNote.other, c.styles.mixed];
    if (r.discs.length !== 32) problemsHere.push(`the globe has ${r.discs.length} artworks on the page (32)`);
    const unlabelled = r.discs.filter((d) => !d.startsWith('BUTTON|') || !prov.some((p) => d.endsWith(`, ${p}`)));
    if (unlabelled.length) problemsHere.push(`globe artworks without a button label of whose eyes they show: ${unlabelled.slice(0, 3).join(' / ')}`);
    // the pinned scene's frame (the desktop's, the phone's own) is the founder's own eye and says so in the picture (charter AC-8), whatever the chips are doing
    for (const t of r.texts.reveal || []) if (t !== c.example.mantas) problemsHere.push(`reveal frame label "${t}", the language says "${c.example.mantas}"`);
    if (!(r.texts.reveal || []).length) problemsHere.push('the pinned scene has no label of whose eye it is');
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
      // the markup is read without its scripts and without inline style attributes: a CSS length (the guide video's width: 100%, 2026-10-22) is not a claim
      const bad = BANNED.exec(text) || BANNED.exec(html.replace(/<script[\s\S]*?<\/script>/g, '').replace(/\sstyle="[^"]*"/g, ''));
      const msgs = [];
      if (bad) msgs.push(`the banned claim "${bad[0]}"`);
      if (state === 'closed' && soonCount !== 3) msgs.push(`"${soon}" appears ${soonCount} times (bar, pricing notice, FAQ: exactly 3)`);
      if (state === 'open' && soonCount !== 0) msgs.push(`ordering is open and "${soon}" still appears ${soonCount} times`);
      if (lang === 'en' || lang === 'de') {
        const printing = lang === 'en' ? /Printing is not part of your order/gi : /Der Druck gehört nicht zur Bestellung/gi;
        const n = (text.match(printing) || []).length;
        // said once where it matters (the lean pass of 2026-10-22, the owner: "too much text"): the price list and the FAQ answer about printing (the tile line of a
        // printed piece with its price, styles.wallFile, only appears when such a tile is on its wall view and can be bought)
        if (n !== 2) msgs.push(`the line "printing is not part of your order" appears ${n} times (2: the price list, the FAQ)`);
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
  for (const [from, to] of [['en', 'de'], ['de', 'lt'], ['lt', 'hu'], ['hu', 'hr'], ['hr', 'en']]) {
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
  const cases = [['en', ''], ['de', ''], ['lt', ''], ['hu', ''], ['hr', ''], ['en', 'm=au'], ['de', 'm=au'], ['hu', 'm=hu'], ['lt', 'm=lt']];
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
  const SECTIONS = ['Reveal', 'Wall', 'StyleGallery', 'HowItWorks', 'Pricing', 'CloseUps', 'Trust', 'Faq', 'ClosingScene', 'SizeGuide', 'MoreRooms', 'Globe'];
  // the chunks that are no section of their own: the two inside the wall and the hero's globe
  const INNER = ['SizeGuide', 'MoreRooms', 'Globe'];
  const picked = quick ? ['Faq', 'Wall', 'SizeGuide', 'Globe'] : SECTIONS;
  for (const name of picked) {
    const file = files.find((f) => f.startsWith(`${name}-`));
    if (!file) { fail('resilience', `no chunk ${name}-*.js in ${dist}/assets: the section list of this check is out of date`); continue; }
    const page = await openBlocked([`*/assets/${file}`]);
    await sleep(1500);
    await page.eval('window.__marker = 1');
    await sleep(5500);
    const r = JSON.parse(await page.eval(`JSON.stringify({ hdr: !!document.getElementById('hdr'), hero: !!document.querySelector('.lp-hero h1'), ftr: !!document.querySelector('.lp-ftr'),
      poster: (() => { const i = document.querySelector('#root #heroImg'); return !!i && i.complete && i.naturalWidth > 0 && getComputedStyle(i).opacity === '1'; })(), globe: !!document.querySelector('#heroGlobe .lp-gl'),
      root: document.getElementById('root').childElementCount, h: document.documentElement.scrollHeight,
      marker: window.__marker === 1, others: document.querySelectorAll('main > section.lp-sec, main > .lp-sheet > section.lp-sec, main > section.lp-final').length })`));
    const msgs = [];
    if (!page.blocked.some((u) => u.includes(file))) msgs.push(`the block did not apply (no request for ${file} was stopped), so nothing was tested`);
    if (!r.hdr || !r.hero || !r.ftr) msgs.push(`the page lost ${[!r.hdr && 'the header', !r.hero && 'the hero', !r.ftr && 'the footer'].filter(Boolean).join(', ')}`);
    if (!r.root) msgs.push('React left #root empty (a blank page)');
    // the blocked section is the one that is missing: the others are all there
    const total = SECTIONS.filter((s) => !INNER.includes(s)).length;
    if (!INNER.includes(name) && r.others !== total - 1) msgs.push(`${r.others} sections are on the page, ${total - 1} expected (the blocked one missing, the others there)`);
    if (name === 'Globe' && r.others !== total) msgs.push(`${r.others} sections are on the page, ${total} expected (the globe's chunk is no section)`);
    if (name === 'Globe' && (!r.poster || r.globe)) msgs.push(`without the globe's chunk the hero must keep its poster, whole (poster shown: ${r.poster}, a globe: ${r.globe})`);
    if (r.h < 2500) msgs.push(`the page is ${r.h} px high: the other sections are gone too`);
    if (!r.marker) msgs.push('the page reloaded itself');
    if (msgs.length) fail('resilience', `${name} blocked: ${msgs.join('; ')}`);
    else pass('resilience', `${name} blocked: the page stays (${r.others} sections, ${r.h} px, no reload)`);
    await page.close();
  }
}

async function checkSkew() {
  console.log('skew');
  const html = readFileSync(join(dist, landingFile('en')), 'utf8');
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
    const r = JSON.parse(await page.eval(`JSON.stringify({ hdr: getComputedStyle(document.getElementById('hdr')).backdropFilter,
      blurs: [...document.querySelectorAll('.lp-hero-fig, .lp-hero-fig *')].filter((e) => getComputedStyle(e).backdropFilter !== 'none' || getComputedStyle(e).filter !== 'none').map((e) => e.tagName + '.' + String(e.className).slice(0, 24)) })`));
    const msgs = [];
    if (!r.hdr || r.hdr === 'none') msgs.push(`the solid header has backdrop-filter "${r.hdr}"`);
    // the hero's globe is artwork: nothing on it blurs or filters it (charter AC-2; the two fixed bars are the page's only blurred surfaces). Its old chip over
    // the picture went with the picture (2026-10-22): the honest line is under the stage
    if (r.blurs.length) msgs.push(`something on the hero's globe blurs or filters the artworks: ${r.blurs.slice(0, 4).join(', ')}`);
    if (width < 768) {
      await page.eval('window.scrollTo({ top: 1500, behavior: "instant" })');
      await sleep(700);
      const s = await page.eval(`getComputedStyle(document.querySelector('.lp-sticky')).backdropFilter`);
      if (!s || s === 'none') msgs.push(`the sticky phone bar has backdrop-filter "${s}"`);
    }
    if (msgs.length) fail('glass', `${width}px: ${msgs.join('; ')}`);
    else pass('glass', `${width}px: the header${width < 768 ? ' and the sticky bar' : ''} are frosted (${r.hdr}), nothing on the hero's globe blurs the artworks`);
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
    ['hr', 'au', false], ['hr', 'hu', false],   // Croatian is in the EU edition only: neither the Australian nor the Hungarian edition has its texts
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

// ---------------------------------------------------------------------------------------------------- guide
async function checkGuide() {
  console.log('guide');
  const mp4s = "performance.getEntriesByType('resource').map((e) => e.name).filter((n) => /\\.mp4$/.test(n)).map((n) => n.split('/').pop())";
  const state = `(() => { const g = document.querySelector('#how [data-guide]'); if (!g) return null; const v = g.querySelector('video'), b = g.querySelector('button'), i = g.querySelector('img'); return { state: g.dataset.guide, src: v.getAttribute('src'), paused: v.paused, t: v.currentTime, label: b && b.getAttribute('aria-label'), boxW: Math.round(g.getBoundingClientRect().width), boxH: Math.round(g.getBoundingClientRect().height), vis: Math.round(g.parentElement.getBoundingClientRect().height), poster: i.complete && i.naturalWidth > 0 }; })()`;
  const toHow = async (page) => {
    for (let i = 0; i < 80 && !(await page.eval("!!document.querySelector('#how [data-guide]')")); i++) { await page.eval('window.scrollBy(0, 500)'); await sleep(120); }
    await page.eval("document.querySelector('#how .lp-step').scrollIntoView({ block: 'center', behavior: 'instant' })");
  };
  for (const lang of ['lt', 'en']) {
    const c = COPY[lang];
    const page = await open({ lang, width: 412, height: 915, settle: false });
    await sleep(3000);
    const early = JSON.parse(await page.eval(`JSON.stringify(${mp4s})`));
    await toHow(page);
    const playing = await (async () => { for (let i = 0; i < 60; i++) { const s2 = JSON.parse(await page.eval(`JSON.stringify(${state})`)); if (s2 && !s2.paused && s2.t > 0.3) return s2; await sleep(150); } return JSON.parse(await page.eval(`JSON.stringify(${state})`)); })();
    await page.eval('window.scrollTo({ top: document.documentElement.scrollHeight, behavior: "instant" })');
    await sleep(700);
    const away = JSON.parse(await page.eval(`JSON.stringify(${state})`));
    const asked = JSON.parse(await page.eval(`JSON.stringify(${mp4s})`));
    const here = [];
    if (early.length) here.push(`a video was asked for before its step came near: ${early.join()}`);
    if (!playing || playing.paused || playing.src !== `/assets/howto/howto-11-${lang}.mp4`) here.push(`near its step it does not play the ${lang} file: ${JSON.stringify(playing)}`);
    if (playing && (playing.label !== c.how.videoPause || playing.state !== 'auto')) here.push(`its button while it plays: ${playing && playing.label}`);
    if (playing && Math.abs(playing.boxH - playing.vis) > 2) here.push(`the poster does not hold the square box: ${playing.boxH} of ${playing.vis} px`);
    if (!away || !away.paused) here.push('it still plays once its step has left the screen');
    if (asked.some((n) => n !== `howto-11-${lang}.mp4`)) here.push(`another file was asked for: ${asked.join()}`);
    if (here.length) fail('guide', `${lang} 412px: ${here.join('; ')}`);
    else pass('guide', `${lang} 412px: no video while the first screens are read, the ${lang} square plays when its step is near (${playing.boxW} px), it stops when the step leaves`);
    await page.close();
  }
  // reduced motion: the poster and a play button, nothing asked for until the press; the press plays it once
  const page = await open({ lang: 'de', width: 412, height: 915, settle: false, reduceMotion: true });
  await toHow(page);
  await sleep(1500);
  const still = JSON.parse(await page.eval(`JSON.stringify(${state})`));
  const asked = JSON.parse(await page.eval(`JSON.stringify(${mp4s})`));
  await page.eval("document.querySelector('#how [data-guide] button').click()");
  let pressed = null;
  for (let i = 0; i < 60; i++) { pressed = JSON.parse(await page.eval(`JSON.stringify(${state})`)); if (pressed && !pressed.paused && pressed.t > 0.2) break; await sleep(150); }
  const loop = await page.eval("document.querySelector('#how [data-guide] video').loop");
  const here = [];
  if (!still || still.state !== 'held' || still.src || !still.paused || still.label !== COPY.de.how.videoPlay || !still.poster) here.push(`before the press: ${JSON.stringify(still)}`);
  if (asked.length) here.push(`a video was asked for before the press: ${asked.join()}`);
  if (!pressed || pressed.paused || loop) here.push(`after the press: ${JSON.stringify(pressed)}, loop ${loop}`);
  if (here.length) fail('guide', `reduced motion: ${here.join('; ')}`);
  else pass('guide', 'reduced motion: the poster with a play button, nothing asked for; a press plays it once (no loop)');
  await page.close();
}

// ---------------------------------------------------------------------------------------------------- globe
async function checkGlobe() {
  console.log('globe');
  const globeJs = readdirSync(join(dist, 'assets')).find((f) => /^Globe-[\w-]+\.js$/.test(f));
  if (!globeJs) { fail('globe', `no chunk Globe-*.js in ${dist}/assets`); return; }
  const until = async (page, js, ms = 15000) => { for (let t = 0; t < ms; t += 100) { if (await page.eval(js)) return true; await sleep(100); } return false; };
  const LIVE = "!!document.querySelector('#heroGlobe[data-live] .lp-gl-orb')";
  const ORB = "document.querySelector('.lp-gl-orb').style.transform";
  /** the orb's rotation as a 3 x 3 matrix, row by row, whatever transform functions write it (the browser's own parser) */
  const ORBM = "(() => { const m = new DOMMatrix(document.querySelector('.lp-gl-orb').style.transform); return JSON.stringify([m.m11, m.m21, m.m31, m.m12, m.m22, m.m32, m.m13, m.m23, m.m33]); })()";
  const rot = (t) => (t ? JSON.parse(t) : null);
  const asked = `performance.getEntriesByType('resource').filter((e) => e.name.includes(${JSON.stringify(globeJs)})).map((e) => Math.round(e.startTime))`;
  const tap = async (page, p) => {
    await page.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [p] });
    await page.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  };
  /** the disc at the front: the one under the centre of the sphere */
  const FRONT = `(() => { const s = document.getElementById('heroGlobe').getBoundingClientRect(); const cy = parseFloat(document.getElementById('heroGlobe').querySelector('.lp-gl').style.getPropertyValue('--cy')); const e = document.elementFromPoint(s.left + s.width / 2, s.top + cy); const b = e && e.closest('.lp-gl-disc'); if (!b) return null; const r = b.getBoundingClientRect(); return JSON.stringify({ x: r.left + r.width / 2, y: r.top + r.height / 2, label: b.getAttribute('aria-label') }); })()`;
  const OPENED = `JSON.stringify({ vis: getComputedStyle(document.querySelector('.lp-gl-open')).visibility, op: document.querySelector('.lp-gl-open').style.opacity, tf: document.querySelector('.lp-gl-open').style.transform, name: document.querySelector('.lp-gl-name').textContent, prov: document.querySelector('.lp-gl-prov').textContent, soon: !document.querySelector('.lp-gl-soon').hidden, soonText: document.querySelector('.lp-gl-soon').textContent, href: document.querySelector('.lp-gl-cta').getAttribute('href'), heroHref: document.getElementById('ctaHero').getAttribute('href'), inert: document.querySelector('.lp-gl-info').inert, info: +document.querySelector('.lp-gl-info').style.opacity })`;

  // 1. when the chunk is asked for: after the page's load (the poster, the LCP, first), and not while the hero is off the screen
  {
    const page = await open({ lang: 'lt', width: 412, height: 915, settle: false });
    const live = await until(page, LIVE);
    const t = JSON.parse(await page.eval(`JSON.stringify({ asked: ${asked}, load: Math.round(performance.getEntriesByType('navigation')[0].loadEventEnd), lcp: (() => { const l = performance.getEntriesByType('largest-contentful-paint'); return l.length ? Math.round(l.at(-1).startTime) : -1; })() })`));
    await page.close();
    if (!live || t.asked.length !== 1 || t.asked[0] < t.load) fail('globe', `the globe's chunk: live ${live}, asked at ${t.asked.join(', ')} ms, the page's load ended at ${t.load} ms (it must be asked for once, after the load)`);
    else pass('globe', `the globe's chunk is asked for at ${t.asked[0]} ms, after the page's load (${t.load} ms), and the globe took the poster's place`);
    const away = await open({ lang: 'lt', width: 412, height: 915, settle: false, hash: '#faq' });
    await sleep(4000);
    const off = JSON.parse(await away.eval(`JSON.stringify({ y: Math.round(scrollY), asked: ${asked} })`));
    await away.eval("window.scrollTo({ top: 0, behavior: 'instant' })");
    const back = await until(away, LIVE, 10000);
    await away.close();
    if (off.y < 1000 || off.asked.length || !back) fail('globe', `opened at #faq (scrolled to ${off.y} px): the chunk was asked for ${off.asked.length} times while the hero was off the screen; back at the top the globe came: ${back}`);
    else pass('globe', `opened at #faq: nothing asked for while the hero is off the screen (4 s), the globe comes when the visitor goes back up`);
  }
  // 2. reduced motion: the globe keeps still, a tap opens the artwork in place (no flight, no turn), with its name, whose eyes, Soon (ordering is closed)
  //    and the one button to /try in the page's language; Escape closes it, and a tap beside the opened artwork closes it too
  {
    const page = await open({ lang: 'lt', width: 412, height: 915, settle: false, reduceMotion: true });
    const msgs = [];
    if (!(await until(page, LIVE))) msgs.push('the globe never came');
    else {
      await page.eval('Promise.all([...document.querySelectorAll(".lp-gl img")].filter((i) => i.src).map((i) => i.decode().catch(() => 0))).then(() => 1)');
      const a = await page.eval(ORB);
      await sleep(1500);
      const b = await page.eval(ORB);
      if (a !== b) msgs.push(`it turned by itself (${a} to ${b})`);
      const front = JSON.parse(await page.eval(FRONT));
      await tap(page, front);
      await sleep(400);
      const o = JSON.parse(await page.eval(OPENED));
      const c = await page.eval(ORB);
      const [name, who] = front.label.split(', ');
      if (o.vis !== 'visible' || o.op !== '1' || !/scale\(1(\.0+)?, ?1(\.0+)?\)/.test(o.tf) || c !== b) msgs.push(`a tap did not open it in place: ${JSON.stringify(o)}, the globe ${c === b ? 'kept still' : 'turned'}`);
      if (o.name !== name || o.prov !== who) msgs.push(`the opened artwork says "${o.name}" / "${o.prov}", its disc "${front.label}"`);
      if (!o.soon || o.soonText !== COPY.lt.styles.soonTag) msgs.push(`ordering is closed, the opened artwork does not say "${COPY.lt.styles.soonTag}" (${o.soon ? o.soonText : 'hidden'})`);
      if (!o.href || o.href !== o.heroHref || !/\/try\b.*lang=lt/.test(o.href)) msgs.push(`its button goes to "${o.href}" (the hero's own: "${o.heroHref}")`);
      if (o.inert) msgs.push('the opened words are inert');
      await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
      await page.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
      await sleep(500);
      const shut = JSON.parse(await page.eval(OPENED));
      if (shut.vis !== 'hidden' || !shut.inert) msgs.push(`Escape did not close it: ${JSON.stringify(shut)}`);
      // a tap beside the opened artwork (the empty corner of the stage) closes it
      await tap(page, front);
      await sleep(400);
      const s = JSON.parse(await page.eval("JSON.stringify(document.getElementById('heroGlobe').getBoundingClientRect())"));
      await tap(page, { x: s.left + 14, y: s.top + s.height - 14 });
      await sleep(500);
      const beside = JSON.parse(await page.eval(OPENED));
      if (beside.vis !== 'hidden') msgs.push('a tap beside the opened artwork did not close it');
    }
    await page.close();
    if (msgs.length) fail('globe', `reduced motion 412px: ${msgs.join('; ')}`);
    else pass('globe', 'reduced motion 412px: still; a tap opens the artwork in place with its name, whose eyes, Soon and the button to /try?lang=lt; Escape and a tap beside it close it');
  }
  // 3. the keyboard: one tab stop, the arrows move along a row and to the next row, Enter opens and puts the focus on the button, Escape closes and gives
  //    the focus back to the artwork, Tab from the artwork does not land in the closed words; every artwork is a labelled button
  {
    const page = await open({ lang: 'en', width: 1440, height: 900, settle: false });
    const msgs = [];
    const press = async (k, code) => {
      await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: k, code: k, windowsVirtualKeyCode: code, ...(k === 'Enter' ? { text: String.fromCharCode(13) } : {}) });
      await page.send('Input.dispatchKeyEvent', { type: 'keyUp', key: k, code: k, windowsVirtualKeyCode: code });
    };
    const focused = "(document.activeElement.getAttribute('aria-label') || document.activeElement.className || document.activeElement.tagName)";
    if (!(await until(page, LIVE))) msgs.push('the globe never came');
    else {
      const stops = await page.eval("document.querySelectorAll('#heroGlobe .lp-gl-disc[tabindex=\"0\"]').length");
      const buttons = await page.eval("[...document.querySelectorAll('#heroGlobe .lp-gl-disc')].every((b) => b.tagName === 'BUTTON' && (b.getAttribute('aria-label') || '').length > 4)");
      if (stops !== 1 || !buttons) msgs.push(`${stops} tab stops on the globe (1), every artwork a labelled button: ${buttons}`);
      await page.eval("document.querySelector('#heroGlobe .lp-gl-disc[tabindex=\"0\"]').focus(); 1");
      await press('Tab', 9);
      await sleep(200);
      const next = await page.eval("JSON.stringify({ inInfo: !!document.activeElement.closest('.lp-gl-info'), inGlobe: !!document.activeElement.closest('#heroGlobe') })");
      if (JSON.parse(next).inInfo || JSON.parse(next).inGlobe) msgs.push(`Tab from the artwork stays in the globe or lands in its closed words (${next})`);
      await page.eval("document.querySelector('#heroGlobe .lp-gl-disc[tabindex=\"0\"]').focus(); 1");
      const f0 = await page.eval(focused);
      await press('ArrowRight', 39);
      await sleep(800);
      const f1 = await page.eval(focused);
      await press('ArrowUp', 38);
      await sleep(800);
      const f2 = await page.eval(focused);
      if (f0 === f1 || f1 === f2) msgs.push(`the arrows did not move the focus (${f0} / ${f1} / ${f2})`);
      await press('Enter', 13);
      await sleep(1200);
      const o = JSON.parse(await page.eval(`JSON.stringify({ name: document.querySelector('.lp-gl-name').textContent, on: document.activeElement.className })`));
      if (!o.on.includes('lp-gl-cta') || !f2.startsWith(o.name)) msgs.push(`Enter opened "${o.name}" with the focus on "${o.on}" (the artwork was "${f2}")`);
      await press('Escape', 27);
      await sleep(1000);
      const back = await page.eval(focused);
      const vis = await page.eval("getComputedStyle(document.querySelector('.lp-gl-open')).visibility");
      if (back !== f2 || vis !== 'hidden') msgs.push(`Escape left the focus on "${back}" (the artwork "${f2}"), the opened copy ${vis}`);
    }
    await page.close();
    if (msgs.length) fail('globe', `keyboard 1440px: ${msgs.join('; ')}`);
    else pass('globe', 'keyboard 1440px: one tab stop, the arrows move along and across the rows, Enter opens onto the button, Escape gives the focus back, Tab leaves the globe');
  }
  // 4. touch: a vertical swipe on the globe scrolls the page and does not turn it; a sideways swipe turns it and does not scroll. The orb's orientation
  //    may turn about any axis (src/landing/globe/Globe.tsx): how far it turned is the angle of the rotation from one orientation to the other
  {
    const turned = (a, b) => {
      const A = rot(a), B = rot(b);
      if (!A || !B) return NaN;
      let tr = 0;
      for (let i = 0; i < 9; i++) tr += A[i] * B[i];
      return (Math.acos(Math.max(-1, Math.min(1, (tr - 1) / 2))) * 180) / Math.PI;
    };
    const page = await open({ lang: 'lt', width: 412, height: 915, settle: false });
    const msgs = [];
    if (!(await until(page, LIVE))) msgs.push('the globe never came');
    else {
      const box = JSON.parse(await page.eval("JSON.stringify(document.getElementById('heroGlobe').getBoundingClientRect())"));
      const x = box.left + box.width * 0.5;
      const y0 = box.top + box.height * 0.8;
      const p0 = await page.eval(ORBM);
      const s0 = Date.now();
      await page.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y: y0 }] });
      for (let k = 1; k <= 12; k++) {
        await page.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: x + k * 0.5, y: y0 - k * 22 }] });
        await sleep(16);
      }
      await page.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
      await sleep(700);
      const sy = await page.eval('Math.round(scrollY)');
      const p1 = await page.eval(ORBM);
      // the globe goes on turning by itself meanwhile (6 degrees a second): the swipe may not have turned it by more than that
      const idleTurn = (6 * (Date.now() - s0)) / 1000 + 2;
      if (sy < 80) msgs.push(`a vertical swipe on the globe scrolled the page by ${sy} px`);
      if (!(turned(p0, p1) <= idleTurn)) msgs.push(`a vertical swipe turned the globe by ${turned(p0, p1).toFixed(1)} degrees (its own slow turn: ${idleTurn.toFixed(1)} at most)`);
      await page.eval("window.scrollTo({ top: 0, behavior: 'instant' })");
      await sleep(400);
      const t0 = await page.eval(ORBM);
      const y1 = box.top + box.height * 0.45;
      await page.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: box.left + box.width * 0.85, y: y1 }] });
      for (let k = 1; k <= 12; k++) {
        await page.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: box.left + box.width * 0.85 - k * 22, y: y1 + k * 0.6 }] });
        await sleep(16);
      }
      await page.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
      await sleep(900);
      const sy2 = await page.eval('Math.round(scrollY)');
      const t1 = await page.eval(ORBM);
      if (sy2 !== 0) msgs.push(`a sideways swipe scrolled the page by ${sy2} px`);
      if (!(turned(t0, t1) > 20)) msgs.push(`a sideways swipe turned the globe by ${turned(t0, t1).toFixed(1)} degrees`);
    }
    await page.close();
    if (msgs.length) fail('globe', `touch 412px: ${msgs.join('; ')}`);
    else pass('globe', 'touch 412px: a vertical swipe on the globe scrolls the page and leaves it, a sideways swipe turns it and does not scroll');
  }
  // 5. (the owner's review of 2026-10-23) after an upward drag the globe goes on turning the way it was sent, about the screen's horizontal axis, at its
  //    calm speed, and does not swing back to the equator; and the discs are printed on the one sphere: with only the discs drawn (over a transparent
  //    page) no pixel of them lies outside the sphere's outline, at rest and in the tilted view a drag leaves, at 412 and 1440 px
  for (const [width, height] of [[412, 915], [1440, 900]]) {
    const page = await open({ lang: 'en', width, height, settle: false });
    const msgs = [];
    if (!(await until(page, LIVE))) msgs.push('the globe never came');
    else {
      await sleep(1200);
      /** the turn from orientation a to b: its angle in degrees and its unit axis on the screen (x right, y down, z to the viewer) */
      const between = (a, b) => {
        const A = rot(a), B = rot(b);
        // R = B A^T, row by row
        const R = [0, 1, 2].flatMap((i) => [0, 1, 2].map((j) => B[i * 3] * A[j * 3] + B[i * 3 + 1] * A[j * 3 + 1] + B[i * 3 + 2] * A[j * 3 + 2]));
        const ax = [R[7] - R[5], R[2] - R[6], R[3] - R[1]];
        const l = Math.hypot(...ax) || 1;
        return { deg: (Math.acos(Math.max(-1, Math.min(1, (R[0] + R[4] + R[8] - 1) / 2))) * 180) / Math.PI, axis: ax.map((x) => x / l) };
      };
      /** with only the discs drawn: how far out of the sphere's centre their farthest pixel lies, over the radius of its outline (--A) */
      const reach = async () => {
        await page.eval(`(() => { const s = document.createElement('style'); s.id = 'only-discs'; s.textContent = 'html, body { background: transparent !important } body * { visibility: hidden !important } .lp-gl-orb, .lp-gl-orb * { visibility: visible !important }'; document.head.appendChild(s); return 1; })()`);
        await page.send('Emulation.setDefaultBackgroundColorOverride', { color: { r: 0, g: 0, b: 0, a: 0 } });
        await sleep(150);
        const g = JSON.parse(await page.eval("JSON.stringify((() => { const st = document.querySelector('#heroGlobe .lp-gl'); const r = st.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height, a: parseFloat(st.style.getPropertyValue('--A')), cy: parseFloat(st.style.getPropertyValue('--cy')) }; })())"));
        const shot = await page.send('Page.captureScreenshot', { format: 'png', clip: { x: g.x, y: g.y, width: g.w, height: g.h, scale: 1 } });
        await page.send('Emulation.setDefaultBackgroundColorOverride', {});
        await page.eval("document.getElementById('only-discs').remove(), 1");
        return page.eval(`new Promise((done) => { const im = new Image(); im.onload = () => { const c = document.createElement('canvas'); c.width = im.width; c.height = im.height; const x = c.getContext('2d'); x.drawImage(im, 0, 0); const d = x.getImageData(0, 0, c.width, c.height).data; const k = im.width / ${g.w}; let far = 0; for (let y = 0; y < c.height; y++) for (let i = 0; i < c.width; i++) { if (d[(y * c.width + i) * 4 + 3] < 12) continue; const r = Math.hypot((i + 0.5) / k - ${g.w / 2}, (y + 0.5) / k - ${g.cy}); if (r > far) far = r; } done(JSON.stringify({ far, a: ${g.a} })); }; im.src = 'data:image/png;base64,${shot.data}'; })`).then(JSON.parse);
      };
      const atRest = await reach();
      const box = JSON.parse(await page.eval("JSON.stringify(document.getElementById('heroGlobe').getBoundingClientRect())"));
      const x0 = box.left + box.width / 2;
      const y0 = box.top + box.height * 0.55;
      await page.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: x0, y: y0 });
      await page.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: x0, y: y0, button: 'left', buttons: 1, clickCount: 1 });
      for (let k = 1; k <= 20; k++) {
        await page.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: x0, y: y0 - k * 7, button: 'left', buttons: 1 });
        await sleep(16);
      }
      await page.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: x0, y: y0 - 140, button: 'left', buttons: 0, clickCount: 1 });
      await sleep(2500);
      const a = await page.eval(ORBM);
      await sleep(1000);
      const b = await page.eval(ORBM);
      const t = between(a, b);
      if (!(t.deg > 3 && t.deg < 9.5) || !(Math.abs(t.axis[0]) > 0.9)) msgs.push(`2.5 s after an upward drag the globe turned ${t.deg.toFixed(1)} degrees in a second about (${t.axis.map((v) => v.toFixed(2)).join(', ')}) (it should go on about the screen's horizontal axis at about 6 degrees a second)`);
      const tilted = await reach();
      for (const [when, r] of [['at rest', atRest], ['after the drag', tilted]]) if (!(r.far <= r.a + 1.5)) msgs.push(`${when} a disc reaches ${(r.far - r.a).toFixed(1)} px outside the sphere's outline`);
      if (!msgs.length) pass('globe', `${width}px: after an upward drag it goes on about the horizontal axis (${t.deg.toFixed(1)} degrees a second, no swing back to the equator); no disc outside the outline (farthest ${(atRest.far - atRest.a).toFixed(1)} and ${(tilted.far - tilted.a).toFixed(1)} px from it)`);
    }
    await page.close();
    if (msgs.length) fail('globe', `${width}px: ${msgs.join('; ')}`);
  }
  // 6. ordering open: an artwork whose style can be bought for its number of eyes opens without Soon, and one whose style is still a preview says Soon,
  //    as the gallery's tiles do (the stub's catalogue is the registry's: which styles are live for one eye is read from it, never written here)
  {
    stub.open = true;
    // since 2026-10-27 every one-eye style the picker shows has a live ceiling: the owner's switch holds one of them at preview here (the last live art style in
    // tile order), so the globe has an artwork of each kind to open
    const all = checkoutAnswer(ROOT, { open: true });
    const solosLive = all.styles.filter((s) => s.group === 'solo' && s.stages['1'] === 'live');
    const held = solosLive.length > 1 ? solosLive[solosLive.length - 1].id : null;
    stub.ticked = all.styles.map((s) => s.id).filter((id) => id !== held);
    const cat = checkoutAnswer(ROOT, { open: true, ticked: stub.ticked });
    const names = (stage) => cat.styles.filter((s) => s.group === 'solo' && s.stages['1'] === stage).map((s) => s.name);
    const page = await open({ lang: 'en', width: 412, height: 915, settle: false, reduceMotion: true });
    const msgs = [];
    const seen = [];
    if (!(await until(page, LIVE))) msgs.push('the globe never came');
    else {
      await sleep(1500);
      for (const [stage, wantSoon] of [['live', false], ['preview', true]]) {
        const label = await page.eval(`(() => { const want = ${JSON.stringify(names(stage))}; const b = [...document.querySelectorAll('#heroGlobe .lp-gl-disc')].find((x) => want.includes((x.getAttribute('aria-label') || '').split(', ')[0])); if (!b) return ''; b.focus(); return b.getAttribute('aria-label'); })()`);
        if (!label) { msgs.push(`no artwork of a style that is ${stage} for one eye`); continue; }
        await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13, text: String.fromCharCode(13) });
        await page.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 });
        await sleep(500);
        const o = JSON.parse(await page.eval(OPENED));
        if (o.vis !== 'visible' || o.name !== label.split(', ')[0]) msgs.push(`Enter did not open "${label}": ${JSON.stringify(o)}`);
        if (o.soon !== wantSoon) msgs.push(`ordering is open, "${label}" is ${stage} for one eye, and the opened artwork ${o.soon ? 'says' : 'does not say'} Soon`);
        seen.push(`${label.split(', ')[0]} ${o.soon ? 'Soon' : 'for sale'}`);
        await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
        await page.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
        await sleep(500);
      }
    }
    await page.close();
    stub.open = false;
    stub.ticked = undefined;
    if (msgs.length) fail('globe', `ordering open: ${msgs.join('; ')}`);
    else pass('globe', `ordering open: an artwork whose style can be bought opens without Soon, a preview style says Soon (${seen.join(', ')})`);
  }
}

// ---------------------------------------------------------------------------------------------------- run
const checks = { labels: checkLabels, phrases: checkPhrases, dashes: checkDashes, anchors: checkAnchors, focus: checkFocus, overflow: checkOverflow, links: checkLinks, ordering: checkOrdering, axe: checkAxe, resilience: checkResilience, skew: checkSkew, stall: checkStall, glass: checkGlass, shellclick: checkShellClick, offers: checkOffers, guide: checkGuide, globe: checkGlobe, vitals: checkVitals };
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
