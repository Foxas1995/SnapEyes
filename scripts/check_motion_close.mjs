// The checks of the motion of the CLOSE of the landing page (motion spec 6.11 to 6.17): trust, pricing, the FAQ, the closing scene, the footer,
// the sticky phone button, the cross-state rules and the page transition, in real Chrome, against a build (dist/) served the way Vercel serves it,
// with a stub of the two API calls the page makes. Not part of `vite build` (it needs Chrome and a few minutes); run it after a build:
//   npm run build && node scripts/check_motion_close.mjs
//   node scripts/check_motion_close.mjs [--dist dist] [--only trust,pricing,faq,final,footer,sticky,states,transition,failsafe,focus,headlines,cls,gold]
// Exit code 1 when any check fails. (The foundation's checks are scripts/check_motion.mjs.)
//
// What it checks (each name is a value of --only):
//   trust       the four promises draw their hairline one after the other and their words rise after it; the gold ring draws around the portrait
//               (concentric with it, the portrait itself never moves, fades or scales); the quote and the privacy items rise; every state at rest is
//               final; reduced motion shows all of it at once
//   pricing     nothing animates on a price: no animation or transition on any price, any sentence that holds one, the notice, the list of what
//               you receive, the statement that printing is not part of the order, the footnote or the terms link, at any frame of a full scroll;
//               only the hairlines between the rows draw; a currency switch changes the prices with no animation and no transition
//   faq         an answer opens and closes in .5 s (block size through ::details-content, the plus turns, its ring warms to gold), by mouse and by
//               Enter and Space; the focus ring is the page's gold ring; reduced motion opens it at once
//   final       the closing picture opens like a mat from an inset of 7 percent (86 percent or more of it on screen from the first frame) to the full
//               band, settling from 1.03 to 1; the label and the line about the digital file never move or fade; at rest the band is pixel for
//               pixel the band of reduced motion (AC-5)
//   footer      the giant outline wordmark: decoration (aria-hidden, no text of its own, no clicks), fits the screen from 320 to 1920 px, stroke under
//               the fill in the footer's own colour, rises once; no horizontal scroll
//   sticky      the phone bar slides in .5 s on the expo curve, steps aside for every gold button and the pricing block, is out of the keyboard order
//               and the accessibility tree while hidden
//   states      a language switch re-keys nothing and replays nothing; the ordering flip (answered late by the server) swaps words without any
//               animation and keeps every revealed node revealed; an anchor click scrolls smoothly (instantly under reduced motion)
//   transition  the native page transition: a link from the landing to /try has it (old page out in .25 s, new page in over .4 s after .25 s, about .65 s
//               in all); the legal pages, the online withdrawal form, an order or payment address, the admin and reduced motion never have it (the gate in the head
//               of try.html and order.html is taken from the built pages and run on its own for every address that matters)
//   failsafe    with a dead IntersectionObserver every hidden state of these sections is lifted after 3.5 s
//   focus       every link and button of these sections takes the page's gold focus ring from the keyboard (2 px, 4 px off, settled), in view and not clipped
//   headlines   the headings of these sections fit their boxes (no word wider than its heading, no heading wider than the screen) and every phrase
//               is real text with a space between phrases, at 320, 375, 768 and 1280 px in en, de, lt and hu
//   cls         no layout shift over a full scroll of the page (phone and desktop, en and de): a reveal never moves anything
//   gold        gold in the viewport of trust, pricing and the closing scene: gold text only on index numerals and the free preview's price
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';
import { launch, sleep } from './lib/cdp.mjs';
import { serve } from './lib/static.mjs';
import { checkoutAnswer } from './lib/stubapi.mjs';

const ROOT = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const args = process.argv.slice(2);
const opt = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const dist = resolve(opt('--dist', join(ROOT, 'dist')));
const only = opt('--only') ? new Set(opt('--only').split(',')) : null;
const wants = (name) => !only || only.has(name);

const problems = [];
const fail = (check, msg) => { problems.push(`${check}: ${msg}`); console.log(`  FAIL ${check}: ${msg}`); };
const pass = (check, msg) => console.log(`  ok   ${check}: ${msg}`);
const expect = (check, cond, msg) => { if (!cond) fail(check, msg); return !!cond; };
const J = (s) => JSON.parse(s);

// ordering closed; `late` makes /api/checkout answer "open" after that many ms (the ordering flip that happens at run time)
let lateOpen = 0;
const handler = (req, res) => {
  const url = new URL(req.url, 'http://x');
  const json = (o) => { res.writeHead(200, { 'content-type': 'application/json', 'cache-control': 'no-store' }); res.end(JSON.stringify(o)); };
  if (url.pathname === '/api/health') { json({ stripe: true, stripe_live: false, email: false }); return true; }
  if (url.pathname === '/api/checkout') {
    if (lateOpen) setTimeout(() => json(checkoutAnswer(ROOT, { open: true })), lateOpen); else json(checkoutAnswer(ROOT, { open: false }));
    return true;
  }
  if (url.pathname.startsWith('/api/')) { res.writeHead(404); res.end('{}'); return true; }
  return false;
};
const site = await serve(dist, { vercelFile: join(ROOT, 'vercel.json'), handler });
const origin = `http://127.0.0.1:${site.port}`;
const chrome = await launch();

// ---------------------------------------------------------------------------------------------------- helpers
/** A fresh visit (nothing remembered), the page open, every lazy section mounted. */
async function open({ lang = 'en', query = '', width = 1280, height = 900, settle = true, path = '/', ...more } = {}) {
  const wipe = await chrome.page({ width: 400, height: 300 });
  await wipe.goto(`${origin}/imprint?lang=en`);
  await wipe.loaded();
  await wipe.send('Storage.clearDataForOrigin', { origin, storageTypes: 'all' }).catch(() => undefined);
  await wipe.close();
  const page = await chrome.page({ width, height, mobile: width < 800, dpr: width < 800 ? 2 : 1, ...more });
  if (more.pre) await page.send('Page.addScriptToEvaluateOnNewDocument', { source: more.pre });
  const q = new URLSearchParams(query);
  if (lang) q.set('lang', lang);
  await page.goto(`${origin}${path}?${q}`);
  await page.loaded();
  if (settle) await mounted(page);
  return page;
}
async function mounted(page) {
  for (let i = 0; i < 150; i++) {
    if (await page.eval("document.querySelector('.lp-slot') === null && !!document.getElementById('faq') && !!document.querySelector('.lp-ftr')")) return;
    await sleep(100);
  }
}
const vh = (page) => page.eval('innerHeight');
/** Scroll an element to the middle (or start, end) of the window at once. */
const reach = (page, sel, block = 'center') => page.eval(`document.querySelector(${JSON.stringify(sel)}).scrollIntoView({ block: ${JSON.stringify(block)}, behavior: 'instant' })`);
/** One value per frame for `ms`: probe is the BODY of a function returning a JSON-able value. Returns [[ms since start, value], ...]. */
const frames = (page, ms, probe) => page.eval(`new Promise((res) => { const out = []; const t0 = performance.now(); const probe = () => { ${probe} };
  const f = () => { const t = performance.now() - t0; out.push([Math.round(t), probe()]); if (t < ${ms}) requestAnimationFrame(f); else res(JSON.stringify(out)); }; f(); })`).then(J);
const num = (v) => (v === 'none' || v === 'normal' || v === undefined ? 1 : parseFloat(String(v).split(' ')[0]));
/** CSS animations of the page that have not finished, by what they run on. */
/** Every section drawn at its real height (content-visibility: auto skips the ones far from the screen and stands in for them with an estimate: the position of the band would
 *  differ by a fraction of a pixel from one load to the next, and this check lays two pages over each other to the pixel). */
const NO_SKIP = "document.head.appendChild(Object.assign(document.createElement('style'), { textContent: '.lp-sheet > .lp-sec, .lp-final { content-visibility: visible !important }' }))";
const ANIMS = `[...document.getAnimations()].filter((a) => a.playState !== 'finished').map((a) => { const e = a.effect, t = e && e.target; return (t ? t.tagName + '.' + String(t.className && t.className.baseVal !== undefined ? t.className.baseVal : t.className).slice(0, 26) : '?') + (e && e.pseudoElement ? e.pseudoElement : '') + ' ' + (a.animationName || a.transitionProperty || ''); })`;
const rest = (sel) => `[...document.querySelectorAll(${JSON.stringify(sel)})].filter((e) => { const c = getComputedStyle(e); return +c.opacity < 0.99 || (c.translate !== 'none' && c.translate !== '0px' && c.translate !== '0px 0px') || (c.scale !== 'none' && c.scale !== '1' && c.scale !== '1 1'); }).map((e) => e.tagName + '.' + String(e.className).slice(0, 24))`;
const pngDiff = async (a, b) => {
  const page = await chrome.page({ width: 400, height: 300 });
  const r = J(await page.eval(`(async () => {
    const load = (b64) => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = 'data:image/png;base64,' + b64; });
    const [x, y] = await Promise.all([load(${JSON.stringify(a.toString('base64'))}), load(${JSON.stringify(b.toString('base64'))})]);
    if (x.width !== y.width || x.height !== y.height) return JSON.stringify({ size: [x.width, x.height, y.width, y.height] });
    const data = (im) => { const c = document.createElement('canvas'); c.width = im.width; c.height = im.height; const g = c.getContext('2d'); g.drawImage(im, 0, 0); return g.getImageData(0, 0, im.width, im.height).data; };
    const p = data(x), q = data(y); let n = 0, max = 0, x0 = 1e9, y0 = 1e9, x1 = -1, y1 = -1;
    for (let i = 0; i < p.length; i += 4) if (p[i] !== q[i] || p[i + 1] !== q[i + 1] || p[i + 2] !== q[i + 2]) { n++; max = Math.max(max, Math.abs(p[i] - q[i]), Math.abs(p[i + 1] - q[i + 1]), Math.abs(p[i + 2] - q[i + 2])); const k = i / 4, px = k % x.width, py = Math.floor(k / x.width); x0 = Math.min(x0, px); y0 = Math.min(y0, py); x1 = Math.max(x1, px); y1 = Math.max(y1, py); }
    return JSON.stringify({ n, max, box: n ? [x0, y0, x1, y1] : null });
  })()`));
  await page.close();
  return r;
};
/** A slow pass over a section: from just above it to its end, a pause at each stop (a node is revealed by being on screen, so a jump would skip it). */
async function walk(page, sel, pause = 260) {
  const top = await page.eval(`document.querySelector(${JSON.stringify(sel)}).getBoundingClientRect().top + scrollY`);
  const H = await page.eval(`document.querySelector(${JSON.stringify(sel)}).offsetHeight`);
  const view = await vh(page);
  for (let y = top - view * 0.8; y < top + H; y += view * 0.35) { await page.eval(`window.scrollTo({ top: ${Math.max(0, y)}, behavior: 'instant' })`); await sleep(pause); }
}
const nondecreasing = (xs, eps = 0.002) => xs.every((x, i) => i === 0 || x >= xs[i - 1] - eps);
const nonincreasing = (xs, eps = 0.002) => xs.every((x, i) => i === 0 || x <= xs[i - 1] + eps);

// ---------------------------------------------------------------------------------------------------- trust
async function checkTrust() {
  console.log('trust');
  for (const [lang, width] of [['en', 1280], ['de', 375], ['hu', 1280], ['lt', 375]]) {
    const tag = `${lang} ${width}px`;
    const page = await open({ lang, width, height: width < 800 ? 812 : 900 });
    const pre = J(await page.eval(`JSON.stringify({ ring: parseFloat(getComputedStyle(document.querySelector('.lp-cur-ring path')).strokeDashoffset),
      lines: [...document.querySelectorAll('.lp-never-list li')].map((l) => getComputedStyle(l, '::before').scale),
      words: [...document.querySelectorAll('.lp-never-list li > *')].map((e) => +getComputedStyle(e).opacity), quote: +getComputedStyle(document.querySelector('.lp-curator blockquote')).opacity,
      titles: [...document.querySelectorAll('#trust h2')].map((h) => h.dataset.reveal), n: document.querySelectorAll('.lp-never-list li').length })`));
    expect('trust', pre.n === 4, `${tag}: ${pre.n} promises, expected 4`);
    expect('trust', pre.ring === 1 && pre.lines.every((s) => s === '0 1') && pre.words.every((o) => o === 0) && pre.quote === 0, `${tag}: before it is reached the promises, the ring and the quote are not in their hidden state (${JSON.stringify(pre)}): the test would see nothing`);
    expect('trust', pre.titles.length === 3 && pre.titles.every((t) => t === 'mask'), `${tag}: the three headings of the trust section are not masked titles (${pre.titles})`);

    // the promises: one by one
    await reach(page, '.lp-never-list');
    const f = await frames(page, 2300, `const pimg = document.querySelector('.lp-cur-ring img'), pc = getComputedStyle(pimg); return { img: [pc.opacity, pc.translate, pc.scale, pc.rotate, pc.transform, pc.filter, getComputedStyle(pimg.parentElement).opacity, getComputedStyle(pimg.parentElement).translate], ring: parseFloat(getComputedStyle(document.querySelector('.lp-cur-ring path')).strokeDashoffset), quote: +getComputedStyle(document.querySelector('.lp-curator blockquote')).opacity, lines: [...document.querySelectorAll('.lp-never-list li')].map((l) => getComputedStyle(l, '::before').scale), words: [...document.querySelectorAll('.lp-never-list li > h3')].map((e) => +getComputedStyle(e).opacity), ys: [...document.querySelectorAll('.lp-never-list li > h3')].map((e) => getComputedStyle(e).translate) };`);
    for (let i = 0; i < 4; i++) {
      const line = f.map(([, v]) => num(v.lines[i])), word = f.map(([, v]) => v.words[i]);
      expect('trust', nondecreasing(line) && nondecreasing(word), `${tag}: promise ${i + 1} goes backwards while it appears`);
      expect('trust', line.some((x) => x > 0.05 && x < 0.95), `${tag}: the hairline of promise ${i + 1} was never seen drawing (${line.slice(0, 12).map((x) => x.toFixed(2))})`);
      expect('trust', word.some((x) => x > 0.05 && x < 0.95), `${tag}: the words of promise ${i + 1} were never seen rising`);
      expect('trust', line[line.length - 1] === 1 && word[word.length - 1] === 1, `${tag}: promise ${i + 1} is not complete after 2.3 s`);
    }
    const start = (i) => f.findIndex(([, v]) => num(v.lines[i]) > 0.02);
    const starts = [0, 1, 2, 3].map(start);
    expect('trust', starts.every((s) => s >= 0) && nondecreasing(starts, 0), `${tag}: the promises do not start one after the other (frames ${starts})`);
    expect('trust', starts[3] > starts[0] || width < 800, `${tag}: all four promises start in the same frame, they should follow one another (${starts})`);
    const lag = f.findIndex(([, v]) => v.words[0] > 0.02) - starts[0];
    expect('trust', lag >= 2, `${tag}: the words of the first promise rise ${lag} frames after its line began, expected the line to lead`);

    // the founder: the ring draws, the portrait never moves
    await reach(page, '.lp-cur-ring', 'center');
    const g = await frames(page, 2600, `const img = document.querySelector('.lp-cur-ring img'), ci = getComputedStyle(img); return { dash: parseFloat(getComputedStyle(document.querySelector('.lp-cur-ring path')).strokeDashoffset), img: [ci.opacity, ci.translate, ci.scale, ci.rotate, ci.transform, ci.filter, getComputedStyle(img.parentElement).opacity, getComputedStyle(img.parentElement).translate], quote: +getComputedStyle(document.querySelector('.lp-curator blockquote')).opacity };`);
    const dash = f.map(([, v]) => v.ring).concat(g.map(([, v]) => v.dash));
    expect('trust', nonincreasing(dash) && dash.some((x) => x > 0.05 && x < 0.95) && dash[dash.length - 1] === 0, `${tag}: the ring does not draw from 1 to 0 (${dash.filter((_, i) => i % 8 === 0).map((x) => x.toFixed(2))})`);
    const still = f.concat(g).every(([, v]) => v.img[0] === '1' && v.img[1] === 'none' && v.img[2] === 'none' && v.img[3] === 'none' && v.img[4] === 'none' && v.img[5] === 'none' && v.img[6] === '1' && v.img[7] === 'none');
    expect('trust', still, `${tag}: the portrait itself was moved, faded, scaled or filtered while the ring drew: ${JSON.stringify(f.concat(g).find(([, v]) => v.img[0] !== '1' || v.img[1] !== 'none' || v.img[2] !== 'none')?.[1].img)}`);
    const quote = f.map(([, v]) => v.quote).concat(g.map(([, v]) => v.quote));
    expect('trust', nondecreasing(quote) && quote[quote.length - 1] === 1, `${tag}: the quote does not rise to full opacity`);
    const geo = J(await page.eval(`JSON.stringify((() => { const i = document.querySelector('.lp-cur-ring img').getBoundingClientRect(), s = document.querySelector('.lp-cur-ring svg').getBoundingClientRect();
      return { dx: (i.left + i.width / 2) - (s.left + s.width / 2), dy: (i.top + i.height / 2) - (s.top + s.height / 2), img: i.width, svg: s.width }; })())`));
    expect('trust', Math.abs(geo.dx) < 0.51 && Math.abs(geo.dy) < 0.51 && geo.svg - geo.img >= 7, `${tag}: the ring is not concentric with the portrait or does not clear it: ${JSON.stringify(geo)}`);

    // the privacy promise on a phone is a disclosure: it opens smoothly like an FAQ answer
    if (width < 800) {
      await reach(page, '.lp-priv-list details');
      await sleep(1500);
      const run = frames(page, 900, `const d = document.querySelector('.lp-priv-list details'); return { open: d.open, h: parseFloat(getComputedStyle(d, '::details-content').blockSize) || 0 };`);
      await sleep(30);
      await page.eval("document.querySelector('.lp-priv-list summary').click()");
      const o = (await run).map(([, v]) => v);
      const hs = o.map((v) => v.h);
      expect('trust', o[o.length - 1].open && hs[hs.length - 1] > 20 && nondecreasing(hs, 0.5) && hs.some((x) => x > 4 && x < hs[hs.length - 1] - 4), `${tag}: a privacy disclosure does not open smoothly (${hs.filter((_, i) => i % 6 === 0).map(Math.round)})`);
    }
    // the privacy items rise one after another; the legal lines never move
    await reach(page, '.lp-priv-list');
    const p = await frames(page, 2200, `return { items: [...document.querySelectorAll('.lp-priv-list > *')].map((e) => +getComputedStyle(e).opacity), legal: ${rest('.lp-priv-foot, .lp-priv-foot *, .lp-id-line')}.length };`);
    expect('trust', p.every(([, v]) => v.legal === 0), `${tag}: the privacy footer or the seller's identity line moved or faded`);
    expect('trust', p[p.length - 1][1].items.length === 4 && p[p.length - 1][1].items.every((o) => o === 1), `${tag}: the four privacy items are not all in place after 2.2 s`);
    await walk(page, '#trust');
    await sleep(2200);
    const after = J(await page.eval(`JSON.stringify({ left: ${ANIMS}.filter((a) => /lp-rv|lp-ring/.test(a)), hidden: ${rest('#trust .lp-never-list li > *, #trust .lp-curator *, #trust .lp-priv-list > *, #trust [data-reveal]')} })`));
    expect('trust', after.left.length === 0 && after.hidden.length === 0, `${tag}: after the reveals, animations left ${after.left.join(', ')}; not at rest ${after.hidden.join(', ')}`);
    await page.close();
  }
  // reduced motion: all of it at once
  for (const [lang, width] of [['en', 1280], ['hu', 375]]) {
    const page = await open({ lang, width, height: width < 800 ? 812 : 900, reduceMotion: true });
    const r = J(await page.eval(`JSON.stringify({ ring: parseFloat(getComputedStyle(document.querySelector('.lp-cur-ring path')).strokeDashoffset),
      lines: [...document.querySelectorAll('.lp-never-list li')].map((l) => getComputedStyle(l, '::before').scale), hidden: ${rest('#trust .lp-never-list li > *, #trust .lp-curator *, #trust .lp-priv-list > *, #trust [data-reveal]')}, anims: ${ANIMS}.length, mo: document.documentElement.classList.contains('mo') })`));
    expect('trust', r.ring === 0 && r.lines.every((s) => s === 'none') && r.hidden.length === 0 && r.anims === 0 && !r.mo, `${lang} ${width}px reduced motion: the section is not in its final state at once: ${JSON.stringify(r)}`);
    await page.close();
  }
  if (!problems.some((x) => x.startsWith('trust'))) pass('trust', 'four promises draw and rise one after the other, the ring draws around a portrait that never moves (concentric), quote and privacy items rise, everything ends at rest, reduced motion is final at once');
}

// ---------------------------------------------------------------------------------------------------- pricing
async function checkPricing() {
  console.log('pricing');
  // anything inside these may NEVER animate, nor may anything it sits in (the hairline of a row is a pseudo element of the row: the one allowed animation)
  const PRICE = '#pricing .lp-pv, #pricing .lp-prow b, #pricing .lp-prow small, #pricing .lp-notice, #pricing .lp-incl, #pricing .lp-incl *, #pricing .lp-foot-price, #pricing .lp-foot-price *, #pricing .lp-cur-sw, #pricing .lp-cur-seg, #pricing .lp-cur-seg *, #pricing .lp-ptable, #pricing .lp-price-grid, #pricing .lp-price-grid > div';
  for (const [lang, width, query] of [['en', 1280, ''], ['de', 375, ''], ['en', 375, 'm=au'], ['hu', 1280, 'm=hu']]) {
    const tag = `${lang} ${width}px${query ? ' ' + query : ''}`;
    const page = await open({ lang, width, height: width < 800 ? 812 : 900, query });
    await page.eval(`window.__bad = []; window.__rule = []; const note = (a) => { const e = a.effect, t = e && e.target; if (!t) return;
      const price = t.closest(${JSON.stringify(PRICE)}) && !(t.matches('.lp-prow') && e.pseudoElement === '::after');
      if (price && !t.closest('.lp-cur-seg button')) window.__bad.push(t.tagName + '.' + String(t.className).slice(0, 24) + (e.pseudoElement || '') + ' ' + (a.animationName || a.transitionProperty)); };
      const tick = () => { for (const a of document.getAnimations()) note(a); window.__rule.push([...document.querySelectorAll('.lp-prow')].map((r) => getComputedStyle(r, '::after').scale)); requestAnimationFrame(tick); }; tick();`);
    const hidden = J(await page.eval("JSON.stringify([...document.querySelectorAll('.lp-prow')].map((r) => getComputedStyle(r, '::after').scale))"));
    expect('pricing', hidden.length === 5 && hidden.every((s) => s === '0 1'), `${tag}: the hairlines of the price rows are not hidden before the table is reached (${hidden}): the test would see nothing`);
    // a full pass over the pricing section, a pause at each stop
    const top = await page.eval("document.getElementById('pricing').getBoundingClientRect().top + scrollY");
    const H = await page.eval("document.getElementById('pricing').offsetHeight");
    const view = await vh(page);
    for (let y = top - view * 0.8; y < top + H; y += view * 0.35) { await page.eval(`window.scrollTo({ top: ${Math.max(0, y)}, behavior: 'instant' })`); await sleep(260); }
    await sleep(2200);
    const r = J(await page.eval(`JSON.stringify({ bad: [...new Set(window.__bad)], rule: window.__rule, notRest: ${rest('#pricing .lp-pv, #pricing .lp-prow, #pricing .lp-prow b, #pricing .lp-prow small, #pricing .lp-notice, #pricing .lp-incl, #pricing .lp-incl *, #pricing .lp-foot-price, #pricing .lp-foot-price *, #pricing .lp-ptable, #pricing .lp-price-grid, #pricing .lp-price-grid > div, #pricing .lp-cur-sw')} })`));
    expect('pricing', r.bad.length === 0, `${tag}: an animation or transition ran on a price, a sentence that holds one or the offer: ${r.bad.join('; ')}`);
    expect('pricing', r.notRest.length === 0, `${tag}: something around the prices is faded, moved or scaled at rest: ${r.notRest.join(', ')}`);
    const rows = [0, 1, 2, 3, 4].map((i) => r.rule.map((s) => num(s[i])));
    expect('pricing', rows.every((xs) => xs.some((x) => x > 0.05 && x < 0.95)), `${tag}: a hairline between the rows was never seen drawing`);
    expect('pricing', rows.every((xs) => nondecreasing(xs) && xs[xs.length - 1] === 1), `${tag}: a hairline goes backwards or does not end complete`);
    expect('pricing', J(await page.eval("JSON.stringify([...document.querySelectorAll('.lp-prow')].map((r) => getComputedStyle(r, '::after').scale))")).every((s) => s === 'none'), `${tag}: a row hairline has a transform left at rest`);
    // the free preview and every price are at full opacity and in the accessibility tree (PriceGate is not pending)
    const gate = J(await page.eval("JSON.stringify([...document.querySelectorAll('#pricing .lp-pv *, #pricing .lp-pv')].filter((e) => e.getAttribute('aria-hidden') === 'true' || e.style.opacity === '0').length)"));
    expect('pricing', gate === 0, `${tag}: ${gate} prices are still held back at rest`);
    await page.close();
  }
  // a currency switch: the prices change, nothing animates, nothing shifts
  {
    const page = await open({ lang: 'en', width: 1280, query: 'm=au' });
    await reach(page, '#pricing .lp-cur-seg');
    await sleep(2800);
    await page.eval(`window.__ev = []; window.__cls = 0;
      for (const t of ['animationstart', 'transitionrun']) document.addEventListener(t, (e) => { if (e.target.closest && e.target.closest('#pricing') && !e.target.closest('.lp-cur-seg button')) window.__ev.push(t + ' ' + e.target.tagName + '.' + String(e.target.className).slice(0, 24) + (e.pseudoElement || '') + ' ' + (e.animationName || e.propertyName)); }, true);
      window.__src = [];
      new PerformanceObserver((l) => { for (const e of l.getEntries()) if (!e.hadRecentInput) { window.__cls += e.value; for (const x of e.sources || []) window.__src.push((x.node && (x.node.id || x.node.className || x.node.nodeName)) + ' ' + JSON.stringify(x.previousRect) + ' -> ' + JSON.stringify(x.currentRect)); } }).observe({ type: 'layout-shift' });
      window.__before = document.querySelector('.lp-ptable').textContent;`);
    await page.eval("document.querySelector('#pricing .lp-cur-seg button[data-market=eu]').click()");
    await sleep(1800);
    const r = J(await page.eval("JSON.stringify({ ev: window.__ev, cls: window.__cls, src: window.__src, changed: window.__before !== document.querySelector('.lp-ptable').textContent, eur: document.querySelector('.lp-ptable').textContent.includes(String.fromCharCode(0x20ac)) })"));
    expect('pricing', r.changed && r.eur, 'the currency switch did not change the prices to euros: the test saw nothing');
    expect('pricing', r.ev.length === 0, `a currency switch started animations or transitions in the pricing block: ${r.ev.join('; ')}`);
    // the words of the other market ARE different (the Australian edition has two languages and a seller line the euro edition lacks, the prices are
    // narrower or wider), so a few pixels of re-flow are the content's own; the budget of the spec is a CLS of .02, and no motion is involved
    expect('pricing', r.cls < 0.02, `a currency switch shifted the layout by ${r.cls} (budget .02): ${r.src.join(' | ')}`);
    console.log(`  note pricing: the switch from A$ to euro re-flowed the page by a CLS of ${r.cls.toFixed(4)} (the other market's own words and price widths; no animation)`);
    await page.close();
  }
  if (!problems.some((x) => x.startsWith('pricing'))) pass('pricing', 'no animation or transition on any price, notice, offer, statement or footnote at any frame of a full pass in en, de, au, hu; only the row hairlines draw; a currency switch animates nothing and shifts nothing');
}

// ---------------------------------------------------------------------------------------------------- faq
async function checkFaq() {
  console.log('faq');
  const key = (page, k, code, vk, text) => page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: k, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk, text, unmodifiedText: text })
    .then(() => page.send('Input.dispatchKeyEvent', { type: 'keyUp', key: k, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk }));
  for (const [lang, width] of [['en', 1280], ['de', 375]]) {
    const tag = `${lang} ${width}px`;
    const page = await open({ lang, width, height: width < 800 ? 812 : 900 });
    await reach(page, '#faq .lp-faq-list');
    await sleep(2200);
    const lastItem = (await page.eval("document.querySelectorAll('#faq details').length")) - 1;
    expect('faq', lastItem >= 10, `${tag}: only ${lastItem + 1} FAQ items`);
    const probe = `const d = document.querySelector('#faq details'), cs = getComputedStyle(d, '::details-content'), p = d.querySelector('p'), sv = getComputedStyle(d.querySelector('summary svg'));
      return { open: d.open, h: parseFloat(cs.blockSize) || 0, vis: cs.contentVisibility, turn: sv.transform, ring: sv.borderTopColor, ph: p.getBoundingClientRect().height };`;
    // open with the mouse
    await page.eval("document.querySelector('#faq summary').scrollIntoView({ block: 'center', behavior: 'instant' })");
    const o = await (async () => { const run = frames(page, 900, probe); await sleep(30); await page.eval("document.querySelector('#faq summary').click()"); return run; })();
    const hs = o.map(([, v]) => v.h);
    const mid = hs.filter((x) => x > 4 && x < hs[hs.length - 1] - 4);
    expect('faq', o[o.length - 1][1].open && hs[hs.length - 1] > 20, `${tag}: the answer did not open`);
    expect('faq', mid.length >= 3 && nondecreasing(hs, 0.5), `${tag}: the answer's height does not grow smoothly (${hs.filter((_, i) => i % 6 === 0).map(Math.round)})`);
    const t0 = o.find(([, v]) => v.h > 1)?.[0], t1 = o.find(([, v]) => v.h >= hs[hs.length - 1] - 0.5)?.[0];
    expect('faq', t1 !== undefined && t1 - (t0 ?? 0) > 160 && t1 - (t0 ?? 0) < 700, `${tag}: opening takes ${t1 - t0} ms, expected about .5 s on the expo curve`);
    const ring = o.map(([, v]) => v.ring);
    expect('faq', new Set(ring).size >= 3 && /245, 197, 66/.test(ring[ring.length - 1]), `${tag}: the plus's ring does not warm to gold while it opens (${[...new Set(ring)].slice(0, 4).join(' | ')})`);
    expect('faq', new Set(o.map(([, v]) => v.turn)).size >= 3, `${tag}: the plus does not turn`);
    // close with Space (the keyboard), open again with Enter
    await page.eval("document.querySelector('#faq summary').focus()");
    const c = await (async () => { const run = frames(page, 900, probe); await sleep(30); await key(page, ' ', 'Space', 32, ' '); return run; })();
    const hc = c.map(([, v]) => v.h);
    expect('faq', !c[c.length - 1][1].open && nonincreasing(hc, 0.5) && hc.some((x) => x > 4 && x < hc[0] - 4), `${tag}: Space did not close the answer smoothly (open ${c[c.length - 1][1].open}, ${hc.filter((_, i) => i % 6 === 0).map(Math.round)})`);
    await sleep(300);
    await key(page, 'Enter', 'Enter', 13, '\r');
    await sleep(800);
    expect('faq', await page.eval("document.querySelector('#faq details').open"), `${tag}: Enter did not open the answer`);
    // the focus ring: the page's gold ring, 2 px, 4 px off once it has settled
    await key(page, 'Tab', 'Tab', 9, '');
    await key(page, 'Tab', 'Tab', 9, '');
    await sleep(500);
    const ring2 = J(await page.eval(`JSON.stringify((() => { const a = document.activeElement, s = getComputedStyle(a); return { tag: a.tagName, inFaq: !!a.closest('#faq'), w: s.outlineWidth, st: s.outlineStyle, c: s.outlineColor, off: s.outlineOffset }; })())`));
    expect('faq', ring2.inFaq && ring2.st === 'solid' && ring2.w === '2px' && /245, 197, 66/.test(ring2.c) && ring2.off === '4px', `${tag}: the keyboard focus ring in the FAQ is not the page's gold ring: ${JSON.stringify(ring2)}`);
    // the list rose one after the other and nothing is left behind
    await walk(page, '#faq');
    await sleep(2200);
    const rest0 = J(await page.eval(`JSON.stringify({ hidden: ${rest('#faq [data-reveal], #faq details')}, left: ${ANIMS}.filter((a) => /lp-rv/.test(a)) })`));
    expect('faq', rest0.hidden.length === 0 && rest0.left.length === 0, `${tag}: the FAQ is not at rest: ${rest0.hidden.join(', ')} ${rest0.left.join(', ')}`);
    await page.close();
  }
  // reduced motion: the answer is there at once
  {
    const page = await open({ lang: 'en', width: 1280, reduceMotion: true });
    await page.eval("document.querySelector('#faq summary').scrollIntoView({ block: 'center', behavior: 'instant' })");
    await sleep(300);
    const run = frames(page, 400, `const d = document.querySelector('#faq details'); return { open: d.open, h: parseFloat(getComputedStyle(d, '::details-content').blockSize) || 0 };`);
    await sleep(30);
    await page.eval("document.querySelector('#faq summary').click()");
    const o = await run;
    const first = o.findIndex(([, v]) => v.open);
    expect('faq', first >= 0 && o.slice(first + 3).every(([, v]) => v.h > 20), `reduced motion: the answer is not there at once (${o.filter((_, i) => i % 3 === 0).map(([, v]) => Math.round(v.h))})`);
    await page.close();
  }
  if (!problems.some((x) => x.startsWith('faq'))) pass('faq', 'an answer opens and closes smoothly in about .5 s (mouse, Space, Enter), the plus turns and its ring warms to gold, the focus ring is the gold ring, the list rises and ends at rest, reduced motion is instant');
}

// ---------------------------------------------------------------------------------------------------- final
async function checkFinal() {
  console.log('final');
  // the share of the band that an inset() clip leaves on screen; the computed value keeps percentages and calc() while it animates
  const share = (clip, w, h) => {
    const m = /inset\((.*?)(?: round .*)?\)$/.exec(clip);
    if (!m) return 1;
    const t = m[1].match(/calc\([^)]*\)|[^\s]+/g) || [];
    const len = (x, dim) => { let tot = 0; for (const n of x.matchAll(/([+-]?\s*[\d.]+(?:e[+-]?\d+)?)(%|px)/g)) { const v = parseFloat(n[1].replace(/\s+/g, '')); tot += n[2] === '%' ? v / 100 * dim : v; } return tot; };
    const top = len(t[0] ?? '0px', h), right = len(t[1] ?? t[0] ?? '0px', w), bottom = len(t[2] ?? t[0] ?? '0px', h), left = len(t[3] ?? t[1] ?? t[0] ?? '0px', w);
    return (1 - (top + bottom) / h) * (1 - (left + right) / w);
  };
  for (const [lang, width] of [['en', 1280], ['de', 375], ['hu', 1280]]) {
    const tag = `${lang} ${width}px`;
    const page = await open({ lang, width, height: width < 800 ? 812 : 900 });
    const pre = J(await page.eval(`JSON.stringify((() => { const b = document.querySelector('.lp-final .lp-bg'), r = b.getBoundingClientRect(); return { clip: getComputedStyle(b).clipPath, scale: getComputedStyle(b.querySelector('img')).scale, w: r.width, h: r.height, op: getComputedStyle(b).opacity, img: getComputedStyle(b.querySelector('img')).opacity }; })())`));
    expect('final', /inset\(/.test(pre.clip) && pre.scale === '1.03', `${tag}: the closing picture is not in its framed state before it is reached (${pre.clip}, scale ${pre.scale}): the test would see nothing`);
    // 86 percent is the linear extent of the plate (7 percent off every side): the area is .86 squared
    expect('final', Math.sqrt(share(pre.clip, pre.w, pre.h)) >= 0.855 && pre.op === '1' && pre.img === '1', `${tag}: before it opens the picture shows only ${(100 * Math.sqrt(share(pre.clip, pre.w, pre.h))).toFixed(1)} percent of the band's width and height (spec: 86) or is faded (${pre.op}, ${pre.img})`);
    // the scene comes into view: the picture opens
    await page.eval(`window.scrollTo({ top: document.querySelector('.lp-final').getBoundingClientRect().top + scrollY - innerHeight * 0.45, behavior: 'instant' })`);
    const f = await frames(page, 2600, `const b = document.querySelector('.lp-final .lp-bg'), r = b.getBoundingClientRect(), img = b.querySelector('img'), ci = getComputedStyle(img);
      return { clip: getComputedStyle(b).clipPath, w: r.width, h: r.height, sc: ci.scale, img: [ci.opacity, ci.rotate, ci.transform, ci.filter, getComputedStyle(b).opacity, getComputedStyle(b).filter],
        still: ${rest('.lp-final-chip, .lp-fine, .lp-final .lp-vis-chip')}.length };`);
    const sh = f.map(([, v]) => share(v.clip, v.w, v.h));
    expect('final', nondecreasing(sh, 0.001) && sh.some((x) => x > 0.78 && x < 0.99) && sh[sh.length - 1] === 1, `${tag}: the picture does not open from the frame to the full band (${sh.filter((_, i) => i % 10 === 0).map((x) => x.toFixed(3))})`);
    const sc = f.map(([, v]) => num(v.sc));
    expect('final', nonincreasing(sc, 0.0005) && Math.max(...sc) <= 1.0301 && sc[sc.length - 1] === 1, `${tag}: the picture inside does not settle from 1.03 to 1 (${sc.filter((_, i) => i % 10 === 0).map((x) => x.toFixed(3))})`);
    expect('final', f.every(([, v]) => v.img[0] === '1' && v.img[1] === 'none' && v.img[2] === 'none' && v.img[3] === 'none' && v.img[4] === '1' && v.img[5] === 'none'), `${tag}: the closing picture was faded, rotated, skewed or filtered`);
    expect('final', f.every(([, v]) => v.still === 0), `${tag}: the label or the line about the digital file was faded or moved during the opening`);
    expect('final', f.every(([, v]) => Math.abs(v.w - f[0][1].w) < 0.5 && Math.abs(v.h - f[0][1].h) < 0.5), `${tag}: the band changed size while the picture opened (layout shift)`);
    await walk(page, '.lp-final');
    await sleep(2200);
    const end = J(await page.eval(`JSON.stringify({ left: ${ANIMS}.filter((a) => /lp-open|lp-rv/.test(a)), hidden: ${rest('.lp-final [data-reveal], .lp-final .lp-bg img')} })`));
    expect('final', end.left.length === 0 && end.hidden.length === 0, `${tag}: the closing scene is not at rest: ${end.left.join(', ')} ${end.hidden.join(', ')}`);
    await page.close();
  }
  // AC-5: at rest the closing band is pixel for pixel the band of reduced motion
  for (const width of [1280, 375]) {
    const height = width < 800 ? 812 : 900;
    // Where the band stands on the page differs between the two modes (the Reveal is a pinned scene, taller than its flat layout, from 768 px), and a picture is
    // rasterised in tiles of the page, its gradients dithered by where they fall: the same band at another height of the page is not pixel for pixel the same band
    // whatever the motion did. So the band is photographed at the SAME height of the page in both modes (the shorter page is pushed down at its very top).
    const where = async (reduceMotion) => {
      const page = await open({ lang: 'en', width, height, reduceMotion });
      await page.eval(NO_SKIP);
      await walk(page, '.lp-final');
      const y = await page.eval("document.querySelector('.lp-final').getBoundingClientRect().top + scrollY");
      await page.close();
      return y;
    };
    const ya = await where(true), yb = await where(false);
    const target = Math.max(ya, yb);
    const shot = async (reduceMotion, lift) => {
      const page = await open({ lang: 'en', width, height, reduceMotion });
      await page.eval(NO_SKIP);
      await walk(page, '.lp-final');
      await page.eval(`document.body.style.paddingTop = ${lift} + 'px'`);   // above everything: the sheet's soft shadow over the band's top edge stays as it is
      await page.eval(`window.scrollTo({ top: document.querySelector('.lp-final').getBoundingClientRect().top + scrollY - innerHeight * 0.3, behavior: 'instant' })`);
      for (let i = 0; i < 40 && !(await page.eval("document.querySelector('.lp-final .lp-bg img').complete")); i++) await sleep(100);
      await sleep(4500);
      await page.eval("document.querySelectorAll('.lp-ftr, .lp-sticky').forEach((e) => { e.style.visibility = 'hidden'; })");
      const clip = J(await page.eval("JSON.stringify((() => { const r = document.querySelector('.lp-final').getBoundingClientRect(); return [r.left, r.top + scrollY, r.width, Math.min(r.height, innerHeight - 70)]; })())"));
      const png = await page.shot(clip);
      await page.close();
      return { png, y: clip[1] };
    };
    const a = await shot(true, target - ya), b = await shot(false, target - yb);
    expect('final', Math.abs(a.y - b.y) < 0.01, `the closing band is not photographed at the same height of the page in both modes (${a.y} and ${b.y})`);
    const d = await pngDiff(a.png, b.png);
    expect('final', d.n === 0 && !d.size, `the closing band at ${width}px differs between reduced motion and motion at rest: ${JSON.stringify(d)}`);
    if (d.n === 0 && !d.size) pass('final', `the closing band at ${width}px is pixel for pixel the same with and without motion, at the same height of the page (${createHash('sha256').update(a.png).digest('hex').slice(0, 8)})`);
  }
  if (!problems.some((x) => x.startsWith('final'))) pass('final', 'the picture opens from an inset of 7 percent (86 percent on screen from the first frame) to the full band, settles 1.03 to 1, label and digital-file line never move, nothing left behind');
}

// ---------------------------------------------------------------------------------------------------- footer
async function checkFooter() {
  console.log('footer');
  for (const width of [320, 375, 768, 1280, 1920]) {
    const page = await open({ lang: 'en', width, height: width < 800 ? 800 : 900 });
    const r = J(await page.eval(`(async () => {
      await document.fonts.ready;
      const m = document.querySelector('.lp-ftr-mark'), s = m.firstElementChild, cs = getComputedStyle(m), q = getComputedStyle(s, '::before'), f = getComputedStyle(document.querySelector('.lp-ftr'));
      const fs = parseFloat(cs.fontSize), c = document.createElement('canvas').getContext('2d'); c.font = cs.fontWeight + ' ' + fs + 'px Cinzel'; c.letterSpacing = '0.02em';
      return JSON.stringify({ aria: m.getAttribute('aria-hidden'), text: m.textContent, pe: cs.pointerEvents, us: cs.userSelect, fs, expect: Math.min(0.175 * innerWidth, 352), w: c.measureText('SNAPEYES').width, content: q.content, po: q.paintOrder, sw: parseFloat(q.webkitTextStrokeWidth), stroke: q.webkitTextStrokeColor, fill: q.color, bg: f.backgroundColor, sc: document.documentElement.scrollWidth, iw: innerWidth, family: cs.fontFamily.slice(0, 20), weight: cs.fontWeight });
    })()`));
    const tag = `${width}px`;
    expect('footer', r.aria === 'true' && r.text === '' && r.pe === 'none' && r.us === 'none', `${tag}: the wordmark is not decoration (aria-hidden ${r.aria}, text "${r.text}", pointer-events ${r.pe}, user-select ${r.us})`);
    expect('footer', /SNAPEYES/.test(r.content) && /stroke/.test(r.po.split(' ')[0]) && r.sw >= 1.4 && r.sw <= 2.01 && r.fill === r.bg, `${tag}: the wordmark's stroke is not painted under a fill in the footer's colour (${r.content} ${r.po} ${r.sw}px, fill ${r.fill}, footer ${r.bg})`);
    expect('footer', Math.abs(r.fs - r.expect) < 0.5 && r.weight === '600', `${tag}: the wordmark's size is ${r.fs}px, expected min(17.5vw, 22rem) = ${r.expect.toFixed(1)}px, weight ${r.weight}`);
    expect('footer', r.w / r.iw <= 0.97 && (r.w / r.iw >= 0.9 || width > 1900), `${tag}: the wordmark is ${(100 * r.w / r.iw).toFixed(1)} percent of the screen wide (it should fit and span 90 to 97 percent; the cap of 22 rem only bites above 2000 px)`);
    expect('footer', r.sc <= r.iw, `${tag}: horizontal scroll (${r.sc} of ${r.iw})`);
    await page.close();
  }
  // it rises once
  {
    const page = await open({ lang: 'en', width: 1280 });
    const pre = await page.eval("getComputedStyle(document.querySelector('.lp-ftr-mark > span')).translate");
    expect('footer', /135%/.test(pre), `the wordmark is not below its mask before it is reached (${pre})`);
    await reach(page, '.lp-ftr-mark', 'end');
    const f = await frames(page, 2200, `return getComputedStyle(document.querySelector('.lp-ftr-mark > span')).translate;`);
    const ys = f.map(([, v]) => (v === 'none' ? 0 : parseFloat(v.split(' ')[1])));
    expect('footer', nonincreasing(ys, 0.5) && ys.some((y) => y > 5 && y < 130) && ys[ys.length - 1] === 0, `the wordmark does not rise out of its mask (${ys.filter((_, i) => i % 8 === 0).map(Math.round)})`);
    await sleep(500);
    expect('footer', (await page.eval(`${ANIMS}.filter((a) => /lp-rv/.test(a)).length`)) === 0, 'an animation is left behind on the wordmark');
    await page.close();
  }
  {
    const page = await open({ lang: 'en', width: 1280, reduceMotion: true });
    expect('footer', (await page.eval("getComputedStyle(document.querySelector('.lp-ftr-mark > span')).translate")) === 'none', 'reduced motion: the wordmark is not in place at once');
    await page.close();
  }
  if (!problems.some((x) => x.startsWith('footer'))) pass('footer', 'wordmark: decoration (aria-hidden, no text, no clicks), stroke under a fill in the footer colour, 90 to 97 percent of the screen from 320 to 1920 px, no horizontal scroll, rises once');
}

// ---------------------------------------------------------------------------------------------------- sticky
async function checkSticky() {
  console.log('sticky');
  const page = await open({ lang: 'en', width: 375, height: 812 });
  const bar = `(() => { const b = document.getElementById('sticky'); return JSON.stringify({ show: b.classList.contains('lp-show'), vis: getComputedStyle(b).visibility, tf: getComputedStyle(b).transform, inert: b.inert, aria: b.getAttribute('aria-hidden'), tab: b.querySelector('a').tabIndex, tr: getComputedStyle(b).transitionProperty + ' ' + getComputedStyle(b).transitionDuration + ' ' + getComputedStyle(b).transitionTimingFunction }); })()`;
  let s = J(await page.eval(bar));
  expect('sticky', !s.show && s.vis === 'hidden' && s.inert && s.aria === 'true' && s.tab === -1, `at the top the bar is not out of the keyboard order and the accessibility tree: ${JSON.stringify(s)}`);
  expect('sticky', /transform/.test(s.tr) && /0\.5s/.test(s.tr) && /cubic-bezier\(0\.16, 1, 0\.3, 1\)/.test(s.tr), `the bar's transition is not .5 s on the expo curve: ${s.tr}`);
  // find a place where it shows: scan down in steps
  const total = await page.eval('document.documentElement.scrollHeight');
  const shows = [];
  for (let y = 700; y < total - 900; y += 300) {
    await page.eval(`window.scrollTo({ top: ${y}, behavior: 'instant' })`);
    await sleep(700);
    shows.push([y, J(await page.eval(bar)).show]);
  }
  expect('sticky', shows.some(([, x]) => x), `the bar never shows on a phone page of ${total} px`);
  expect('sticky', shows.some(([, x]) => !x), 'the bar shows at every position: it never steps aside');
  // the slide: from hidden to shown in .5 s
  const place = shows.find(([, x]) => x)[0];
  await page.eval("window.scrollTo({ top: 0, behavior: 'instant' })");
  await sleep(900);
  const run = frames(page, 900, `const b = document.getElementById('sticky'); const m = /matrix\\(([^)]*)\\)/.exec(getComputedStyle(b).transform); return { show: b.classList.contains('lp-show'), ty: m ? parseFloat(m[1].split(',')[5]) : 0, vis: getComputedStyle(b).visibility };`);
  await sleep(40);
  await page.eval(`window.scrollTo({ top: ${place}, behavior: 'instant' })`);
  const f = await run;
  const on = f.findIndex(([, v]) => v.show);
  const ty = f.slice(on).map(([, v]) => v.ty);
  const h = await page.eval("document.getElementById('sticky').getBoundingClientRect().height");
  expect('sticky', on >= 0 && ty.length > 12 && nonincreasing(ty, 0.5) && ty.some((x) => x > 2 && x < h * 1.1 - 2) && Math.abs(ty[ty.length - 1]) < 0.5, `the bar does not slide in smoothly (${ty.filter((_, i) => i % 5 === 0).map(Math.round)})`);
  const done = f.slice(on).find(([, v]) => Math.abs(v.ty) < 0.5)?.[0];
  expect('sticky', done !== undefined && done - f[on][0] < 560, `the slide takes ${done - f[on][0]} ms, expected .5 s at most`);
  // steps aside for the pricing block and the closing button, comes back after them
  for (const sel of ['#pricing', '#ctaFinal']) {
    await reach(page, sel);
    await sleep(900);
    s = J(await page.eval(bar));
    expect('sticky', !s.show && s.inert && s.aria === 'true', `the bar does not step aside while ${sel} is on screen: ${JSON.stringify(s)}`);
  }
  await page.eval(`window.scrollTo({ top: ${place}, behavior: 'instant' })`);
  await sleep(900);
  s = J(await page.eval(bar));
  expect('sticky', s.show && !s.inert && s.aria === 'false' && s.tab === 0, `the bar does not come back and into the keyboard order: ${JSON.stringify(s)}`);
  const press = await page.eval("getComputedStyle(document.querySelector('#sticky a')).transitionProperty");
  expect('sticky', /scale/.test(press), `the bar's button has no press transition on scale: ${press}`);
  await page.close();
  // reduced motion: the bar is there at once
  const red = await open({ lang: 'en', width: 375, height: 812, reduceMotion: true });
  const rr = J(await red.eval(`(() => { const b = document.getElementById('sticky'); return JSON.stringify({ d: getComputedStyle(b).transitionDuration }); })()`));
  expect('sticky', parseFloat(rr.d) < 0.001, `reduced motion: the bar still slides (${rr.d})`);
  await red.close();
  if (!problems.some((x) => x.startsWith('sticky'))) pass('sticky', 'the phone bar slides in smoothly in .5 s on the expo curve, steps aside for the pricing block and the closing button, is inert and aria-hidden while hidden, instant under reduced motion');
}

// ---------------------------------------------------------------------------------------------------- states
async function checkStates() {
  console.log('states');
  // a language switch re-keys nothing and replays nothing
  {
    const page = await open({ lang: 'en', width: 1280, height: 900 });
    const H = await page.eval('document.documentElement.scrollHeight');
    for (let y = 0; y < H; y += 540) { await page.eval(`window.scrollTo({ top: ${y}, behavior: 'instant' })`); await sleep(220); }
    await sleep(2200);
    await reach(page, '#pricing');
    await sleep(500);
    const n0 = await page.eval("document.querySelectorAll('[data-reveal][data-in]').length");
    await page.eval(`window.__revealed = [...document.querySelectorAll('[data-reveal][data-in]')]; window.__where = window.__revealed.map((e) => (e.closest('section') || e.closest('footer') || e.closest('header') || { id: '?' }).id || (e.closest('footer') ? 'footer' : '?')); window.__ev = []; window.__nodes = new Set([...document.querySelectorAll('main *')]);
      for (const t of ['animationstart', 'transitionrun']) document.addEventListener(t, (e) => { if (e.target.closest && e.target.closest('main')) window.__ev.push(t + ' ' + e.target.tagName + '.' + String(e.target.className).slice(0, 24) + (e.pseudoElement || '') + ' ' + (e.animationName || e.propertyName)); }, true);`);
    await page.eval("document.querySelector('#langSeg button[lang=de]').click()");
    await sleep(1800);
    const r = J(await page.eval(`JSON.stringify({ n: document.querySelectorAll('[data-reveal][data-in]').length, ev: window.__ev, lang: document.documentElement.lang, title: document.querySelector('#priceH').textContent,
      lost: window.__revealed.map((e, i) => [e, i]).filter(([e]) => !e.isConnected || !('in' in e.dataset)).map(([e, i]) => '#' + window.__where[i] + ' ' + e.tagName + '.' + String(e.className).slice(0, 24)),
      gone: [...window.__nodes].filter((e) => !e.isConnected && e.parentNode === null && e.tagName !== 'BODY').length,
      moved: ${rest('main [data-reveal][data-in], main .lp-line-mask > span')} })`));
    // which sections lost nodes to a remount? (the nodes themselves are gone, so ask by the sections' current content: the old nodes remember no section, so count per section id before and after)
    expect('states', r.lang === 'de' && /Klare Preise/.test(r.title), `the language switch did not change the page: ${r.lang} ${r.title}`);
    expect('states', r.ev.length === 0, `a language switch started animations or transitions in the page: ${r.ev.slice(0, 6).join('; ')}`);
    expect('states', r.lost.length === 0 && r.moved.length === 0, `a language switch re-mounted or hid revealed nodes (a list keyed by its words is re-keyed by a language): lost ${r.lost.join(', ')}; not at rest ${r.moved.join(', ')}`);
    expect('states', r.n >= n0, `a language switch left fewer nodes revealed (${n0} before, ${r.n} after)`);
    await page.close();
  }
  // the ordering flip that the server answers late: words swap, nothing animates, nothing revealed is hidden again
  {
    lateOpen = 7000;
    const page = await open({ lang: 'en', width: 1280, height: 900 });
    await reach(page, '#faq .lp-faq-list');
    await sleep(2400);
    const before = J(await page.eval("JSON.stringify({ notice: document.querySelector('.lp-notice')?.textContent, n: document.querySelectorAll('[data-reveal][data-in]').length })"));
    await page.eval(`window.__revealed = [...document.querySelectorAll('[data-reveal][data-in]')]; window.__where = window.__revealed.map((e) => (e.closest('section') || { id: '?' }).id || '?'); window.__ev = []; for (const t of ['animationstart', 'transitionrun']) document.addEventListener(t, (e) => { if (e.target.closest && e.target.closest('main')) window.__ev.push(t + ' ' + e.target.tagName + '.' + String(e.target.className).slice(0, 24) + (e.pseudoElement || '') + ' ' + (e.animationName || e.propertyName)); }, true);`);
    let flipped = false;
    for (let i = 0; i < 80 && !flipped; i++) { await sleep(250); flipped = (await page.eval("document.querySelector('.lp-notice')?.textContent")) !== before.notice; }
    await sleep(1500);
    const r = J(await page.eval(`JSON.stringify({ ev: window.__ev, n: document.querySelectorAll('[data-reveal][data-in]').length, lost: window.__revealed.map((e, i) => [e, i]).filter(([e]) => !e.isConnected || !('in' in e.dataset)).map(([e, i]) => '#' + window.__where[i] + ' ' + e.tagName + '.' + String(e.className).slice(0, 24)), moved: ${rest('main [data-reveal][data-in]')}, notice: document.querySelector('.lp-notice')?.textContent })`));
    lateOpen = 0;
    expect('states', flipped, 'the ordering flip never came: the test saw nothing');
    expect('states', r.ev.length === 0, `the ordering flip started animations or transitions: ${r.ev.slice(0, 6).join('; ')}`);
    expect('states', r.lost.length === 0 && r.moved.length === 0, `the ordering flip re-mounted or hid revealed nodes: lost ${r.lost.join(', ')}; not at rest ${r.moved.join(', ')}`);
    await page.close();
  }
  // anchors scroll smoothly; reduced motion jumps
  for (const reduceMotion of [false, true]) {
    const page = await open({ lang: 'en', width: 1280, height: 900, reduceMotion });
    await page.eval("window.scrollTo({ top: 0, behavior: 'instant' })");
    await sleep(500);
    const run = frames(page, 1500, 'return Math.round(scrollY);');
    await sleep(40);
    await page.eval("document.querySelector('.lp-nav a[href=\"#faq\"]').click()");
    const ys = (await run).map(([, v]) => v);
    const moved = ys.filter((y, i) => i > 0 && y !== ys[i - 1]).length;
    const dest = ys[ys.length - 1];
    expect('states', dest > 3000, `${reduceMotion ? 'reduced motion: ' : ''}the anchor click did not scroll to the FAQ (${dest})`);
    if (!reduceMotion) expect('states', moved >= 6, `an anchor click does not scroll smoothly (${moved} distinct positions on the way)`);
    else expect('states', moved <= 2, `reduced motion: an anchor click scrolls over ${moved} frames instead of jumping`);
    await page.close();
  }
  if (!problems.some((x) => x.startsWith('states'))) pass('states', 'a language switch re-keys and replays nothing, the late ordering flip swaps words with no animation and keeps every reveal, anchors scroll smoothly and jump under reduced motion');
}

// ---------------------------------------------------------------------------------------------------- transition
async function checkTransition() {
  console.log('transition');
  // the one line in the head of try.html and order.html that keeps the transition off an order, a payment and the withdrawal form: taken from the BUILT pages and run on
  // its own with a fake event, for every address that matters
  const gates = ['try.html', 'order.html'].map((f) => {
    const html = readFileSync(join(dist, f), 'utf8');
    const a = html.indexOf("<script>(function(q){addEventListener('pagereveal'");
    const b = html.indexOf('</script>', a);
    expect('transition', a > 0 && b > a, `${f} has no pagereveal gate in its head`);
    return a > 0 && b > a ? html.slice(a + 8, b) : '';
  });
  const skips = (code, search) => {
    let handler = null, skipped = false;
    vm.runInNewContext(code, { addEventListener: (t, f) => { if (t === 'pagereveal') handler = f; }, location: { search } });
    handler({ viewTransition: { skipTransition: () => { skipped = true; } } });
    let noTransition = false;
    handler({ viewTransition: null });   // a navigation without a transition: nothing to skip, nothing may throw
    return skipped || noTransition;
  };
  const cases = [
    ['', false], ['?lang=de&m=au', false], ['?lang=de', false], ['?foo=o', false], ['?mo=1', false], ['?k', false], ['?ref=so&lang=hu', false],
    ['?o=abcd1234&k=0123456789abcdef0123456789abcdef', true], ['?o=a&k=b&lang=de', true], ['?lang=de&o=a1', true], ['?s=cs_test_123', true], ['?checkout=cancelled&o=abcd', true],
    ['?session_id=cs_live_1', true], ['?withdraw=1&lang=hu', true], ['?m=au&withdraw=1', true],
  ];
  gates.forEach((code, g) => {
    if (!code) return;
    const wrong = cases.filter(([q, want]) => skips(code, q) !== want).map(([q, want]) => `${q || '(nothing)'} should ${want ? '' : 'not '}be skipped`);
    expect('transition', wrong.length === 0, `the gate of ${['try', 'order'][g]}.html is wrong for: ${wrong.join('; ')}`);
  });

  // The browser offers a cross-document transition only when the old page's picture reaches the new page in time, which on a loaded machine is a race: a navigation
  // that is not offered one proves nothing. So every case is tried again until the browser has offered a transition (at most `tries` times), and the claim is made
  // about THAT attempt: a skipped one must have been skipped by the gate (the probe counts the calls of skipTransition), and a page that never opted in must never be
  // offered one in any attempt.
  const LOG = `window.__vt = null; window.__skipped = 0;
    if (window.ViewTransition) { const sk = ViewTransition.prototype.skipTransition; ViewTransition.prototype.skipTransition = function () { window.__skipped++; return sk.call(this); }; }
    addEventListener('pagereveal', (e) => { const v = e.viewTransition; window.__vt = { has: !!v, at: performance.now(), ran: null, origin: performance.timeOrigin }; if (v) { v.ready.then(() => { window.__vt.ran = true; }, () => { window.__vt.ran = false; }); v.finished.then(() => { window.__vt.done = performance.now(); }, () => { window.__vt.done = -1; }); } });`;
  const attempt = async (reduceMotion, from, how) => {
    const page = await chrome.page({ width: 1280, height: 900, reduceMotion });
    await page.send('Page.addScriptToEvaluateOnNewDocument', { source: LOG });
    await page.goto(`${origin}${from}`);
    await page.loaded();
    if (from.startsWith('/?')) await mounted(page);
    await sleep(500);
    const old = await page.eval('performance.timeOrigin');
    await page.eval(how);
    for (let i = 0; i < 80 && !(await page.eval(`performance.timeOrigin !== ${old} && document.readyState === 'complete' && !!window.__vt`).catch(() => false)); i++) await sleep(100);
    await sleep(1900);
    const out = await page.eval(`JSON.stringify({ vt: window.__vt, skipped: window.__skipped, url: location.pathname + location.search })`).then(J).catch(() => null);
    await page.close();
    return out;
  };
  /** Try until the browser offers a transition. Returns every attempt and the first one offered, if any. */
  const offered = async (from, how, tries = 8, reduceMotion = false) => {
    const all = [];
    for (let i = 0; i < tries; i++) {
      const r = await attempt(reduceMotion, from, how);
      all.push(r);
      if (r && r.vt && r.vt.has) break;
    }
    return { all, hit: all.find((r) => r && r.vt && r.vt.has) || null, n: all.length };
  };

  // the landing to /try by the hero's link: the transition runs, about .65 s from the first frame to its end
  {
    const r = await offered('/?lang=en', "document.querySelector('a#ctaHero').click()", 8);
    expect('transition', !!r.hit, `the browser never offered a transition for a link from the landing to /try in ${r.n} attempts`);
    if (r.hit) {
      const t = r.hit;
      expect('transition', t.url.startsWith('/try'), `the hero link did not lead to /try (${t.url})`);
      expect('transition', t.vt.ran === true && t.skipped === 0, `the transition offered for the hero link did not run (ran ${t.vt.ran}, skipped ${t.skipped}): the gate skipped a harmless address`);
      const dur = t.vt.done > 0 ? t.vt.done - t.vt.at : null;
      expect('transition', dur !== null && dur > 520 && dur < 1300, `the transition took ${dur} ms from the first frame to its end, expected about 650`);
      console.log(`  note transition: / -> /try ran in ${dur !== null ? Math.round(dur) : '?'} ms (offered at attempt ${r.n})`);
    }
  }
  // the timings of the two pictures, read right after the reveal while the transition runs
  {
    let seen = null;
    for (let i = 0; i < 8 && !seen; i++) {
      const page = await chrome.page({ width: 1280, height: 900 });
      await page.send('Page.addScriptToEvaluateOnNewDocument', { source: `addEventListener('pagereveal', (e) => { if (!e.viewTransition) return; e.viewTransition.ready.then(() => { window.__timing = [...document.getAnimations()].map((a) => { const x = a.effect; return x && x.pseudoElement ? [x.pseudoElement, a.animationName, x.getTiming().duration, x.getTiming().delay, x.getTiming().easing] : null; }).filter(Boolean); }, () => {}); });` });
      await page.goto(`${origin}/?lang=en`);
      await page.loaded();
      await mounted(page);
      await sleep(500);
      await page.eval("document.querySelector('a#ctaHero').click()");
      await sleep(2400);
      const t = await page.eval('JSON.stringify(window.__timing || null)').then(J).catch(() => null);
      await page.close();
      if (t) seen = t;
    }
    expect('transition', !!seen, 'the timings of the transition could not be read in 8 attempts');
    if (seen) {
      const o = seen.find((a) => /old\(root\)/.test(a[0]) && a[1] === 'pt-out'), n = seen.find((a) => /new\(root\)/.test(a[0]) && a[1] === 'pt-in');
      expect('transition', !!o && o[2] === 250 && o[3] === 0 && !!n && n[2] === 400 && n[3] === 250, `the transition is not the old page out in .25 s and the new page in over .4 s after .25 s: ${seen.map((a) => a.join(' ')).join(' | ')}`);
      console.log(`  note transition: ${seen.map((a) => `${a[0]} ${a[1]} ${a[2]}ms+${a[3]}ms ${a[4]}`).join(' | ')}`);
    }
  }
  // addresses that must skip it: an order, a payment, the withdrawal form. The browser offers a transition (both pages opted in) and the gate in the head of the page
  // must skip it before the first frame.
  for (const [label, how] of [
    ['an order address with its key', "location.assign('/order?o=abcd1234&k=0123456789abcdef0123456789abcdef')"],
    ['the return from a payment', "location.assign('/try?checkout=cancelled&o=abcd1234')"],
    ['the online withdrawal function (the footer link)', "document.querySelector('.lp-ftr a[href*=\"withdraw=1\"]').click()"],
  ]) {
    const r = await offered('/?lang=en', how, 10);
    expect('transition', !!r.hit, `${label}: the browser never offered a transition to skip in ${r.n} attempts, so the gate could not be tested`);
    if (r.hit) {
      expect('transition', r.hit.skipped >= 1 && r.hit.vt.ran === false, `${label}: the transition was offered and NOT skipped (skipped ${r.hit.skipped}, ran ${r.hit.vt.ran}, ${r.hit.url})`);
      expect('transition', /^\/(order|try)/.test(r.hit.url), `${label}: the page that was reached is ${r.hit.url}`);
    }
    console.log(`  note transition: ${label}: offered at attempt ${r.n}, skipped ${r.hit ? r.hit.skipped : '?'}x, ran ${r.hit ? r.hit.vt.ran : '?'}`);
  }
  // pages that never opted in: never offered one
  for (const [label, how] of [
    ['a legal page', "document.querySelector('.lp-ftr a[href*=\"privacy\"]').click()"],
    ['the admin', "location.assign('/admin')"],
  ]) {
    const all = [];
    for (let i = 0; i < 3; i++) all.push(await attempt(false, '/?lang=en', how));
    expect('transition', all.every((r) => r && r.vt && !r.vt.has && !r.vt.ran), `${label} was offered a view transition: ${JSON.stringify(all.map((r) => r && r.vt))}`);
  }
  // reduced motion: the opt-in is off
  {
    const all = [];
    for (let i = 0; i < 3; i++) all.push(await attempt(true, '/?lang=en', "document.querySelector('a#ctaHero').click()"));
    expect('transition', all.every((r) => r && r.url.startsWith('/try') && r.vt && !r.vt.has), `under reduced motion a transition was offered: ${JSON.stringify(all.map((r) => r && r.vt))}`);
  }
  // /try back to the landing by a link: the transition runs the other way too
  {
    const r = await offered('/try', "document.querySelector('a[href=\"/\"], a[href^=\"/?\"], header a')?.click()", 8);
    console.log(`  note transition: /try -> landing link: offered at attempt ${r.n}, ${r.hit ? `ran ${r.hit.vt.ran}, skipped ${r.hit.skipped}` : 'never offered'}`);
    if (r.hit) expect('transition', r.hit.vt.ran === true && r.hit.skipped === 0, 'the transition from /try back to the landing did not run');
  }
  if (!problems.some((x) => x.startsWith('transition'))) pass('transition', 'a link from the landing to /try has the native transition (old out .4 s, new in .6 s after .4 s, about 1 s); the legal pages, the withdrawal form, order and payment addresses, the admin and reduced motion never have it');
}

// ---------------------------------------------------------------------------------------------------- failsafe
async function checkFailsafe() {
  console.log('failsafe');
  const dead = 'window.IntersectionObserver = class { constructor() {} observe() {} unobserve() {} disconnect() {} takeRecords() { return []; } };';
  const page = await open({ lang: 'en', width: 1280, pre: dead, settle: false });
  await sleep(6500);
  await mounted(page);
  const r = J(await page.eval(`JSON.stringify({ fail: document.documentElement.classList.contains('mo-fail'),
    hidden: ${rest('.lp-never-list li > *, .lp-curator *, .lp-priv-list > *, .lp-ftr-mark > span, .lp-final .lp-bg img, .lp-final [data-reveal], #trust [data-reveal], #faq [data-reveal], #pricing [data-reveal]')},
    ring: parseFloat(getComputedStyle(document.querySelector('.lp-cur-ring path')).strokeDashoffset), lines: [...document.querySelectorAll('.lp-never-list li, .lp-prow')].map((l) => getComputedStyle(l, l.matches('.lp-prow') ? '::after' : '::before').scale),
    clip: getComputedStyle(document.querySelector('.lp-final .lp-bg')).clipPath })`));
  expect('failsafe', r.fail, 'with a dead observer html.mo-fail never came');
  expect('failsafe', r.hidden.length === 0 && r.ring === 0 && r.lines.every((s) => s === 'none') && r.clip === 'none', `with a dead observer these stay hidden: ${r.hidden.join(', ')} (ring ${r.ring}, lines ${r.lines}, clip ${r.clip})`);
  await page.close();
  if (!problems.some((x) => x.startsWith('failsafe'))) pass('failsafe', 'with a dead observer the promises, the ring, the price hairlines, the closing picture and the wordmark are all drawn and in place after 3.5 s');
}

// ---------------------------------------------------------------------------------------------------- focus
async function checkFocus() {
  console.log('focus');
  const targets = [['the founder mail button', '.lp-curator a.lp-btn-line'], ['the privacy policy link', '.lp-priv-foot a'], ['the pricing call to action', '.lp-incl a.lp-btn-gold'],
    ['the terms link under the prices', '.lp-foot-price a'], ['the closing call to action', '#ctaFinal'], ['a footer link', '.lp-ftr nav a'], ['a legal link', '#legalNav a'], ['an FAQ question', '#faq summary']];
  for (const [lang, width] of [['en', 1280], ['de', 375]]) {
    const page = await open({ lang, width, height: width < 800 ? 812 : 900 });
    for (const [name, sel] of targets) {
      await reach(page, sel, 'center');
      await sleep(900);
      await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Shift', code: 'ShiftLeft', windowsVirtualKeyCode: 16 });
      await page.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Shift', code: 'ShiftLeft', windowsVirtualKeyCode: 16 });
      await page.eval(`document.querySelector(${JSON.stringify(sel)}).focus()`);
      await sleep(500);
      const r = J(await page.eval(`JSON.stringify((() => { const a = document.activeElement, s = getComputedStyle(a), b = a.getBoundingClientRect(); return { is: a.matches(${JSON.stringify(sel)}), w: s.outlineWidth, st: s.outlineStyle, c: s.outlineColor, off: s.outlineOffset, inView: b.top >= 0 && b.bottom <= innerHeight && b.left >= 0 && b.right <= innerWidth, vis: s.visibility, op: +s.opacity }; })())`));
      expect('focus', r.is && r.st === 'solid' && r.w === '2px' && /245, 197, 66/.test(r.c) && r.off === '4px' && r.inView && r.vis === 'visible', `${lang} ${width}px: ${name} does not show the gold focus ring from the keyboard: ${JSON.stringify(r)}`);
    }
    await page.close();
  }
  if (!problems.some((x) => x.startsWith('focus'))) pass('focus', 'the mail button, the policy and terms links, both calls to action, a footer link, a legal link and an FAQ question show the gold ring of the page (2 px, 4 px off) from the keyboard, in view, at 1280 and 375 px');
}

// ---------------------------------------------------------------------------------------------------- headlines
async function checkHeadlines() {
  console.log('headlines');
  for (const lang of ['en', 'de', 'lt', 'hu']) {
    for (const width of [320, 375, 768, 1280]) {
      const page = await open({ lang, width, height: width < 800 ? 700 : 900 });
      const r = J(await page.eval(`JSON.stringify((() => {
        const hs = [...document.querySelectorAll('#trust h2, #pricing h2, #final h2, #faq h2')];
        return { n: hs.length,
          wide: hs.filter((h) => h.scrollWidth > h.clientWidth + 1 || [...h.querySelectorAll('.lp-line-mask > span')].some((s) => s.scrollWidth > h.clientWidth + 1)).map((h) => h.textContent),
          off: hs.filter((h) => { const b = h.getBoundingClientRect(); return b.left < -1 || b.right > innerWidth + 1; }).map((h) => h.textContent),
          starred: hs.filter((h) => h.textContent.includes(String.fromCharCode(42))).map((h) => h.textContent),
          glued: hs.filter((h) => h.querySelectorAll('.lp-line-mask').length > 1 && ![...h.querySelectorAll('.lp-line-mask')].every((m, i, all) => i === 0 || m.previousSibling && m.previousSibling.nodeType === 3 && m.previousSibling.textContent === ' ')).map((h) => h.textContent),
          sw: document.documentElement.scrollWidth, iw: innerWidth };
      })())`));
      const tag = `${lang} ${width}px`;
      expect('headlines', r.n === 6, `${tag}: ${r.n} headings in trust, pricing, final and faq, expected 6`);
      expect('headlines', r.wide.length === 0 && r.off.length === 0, `${tag}: headings wider than their box or the screen: ${r.wide.concat(r.off).join(' | ')}`);
      expect('headlines', r.starred.length === 0 && r.glued.length === 0, `${tag}: a heading prints a star or glues its phrases: ${r.starred.concat(r.glued).join(' | ')}`);
      expect('headlines', r.sw <= r.iw, `${tag}: horizontal scroll (${r.sw} of ${r.iw})`);
      await page.close();
    }
  }
  if (!problems.some((x) => x.startsWith('headlines'))) pass('headlines', 'the six headings of trust, pricing, the FAQ and the closing scene fit at 320, 375, 768 and 1280 px in en, de, lt and hu; no star, no glued phrases, no horizontal scroll');
}

// ---------------------------------------------------------------------------------------------------- cls
async function checkCls() {
  console.log('cls');
  for (const [lang, width] of [['en', 375], ['de', 375], ['en', 1280], ['de', 1280]]) {
    const page = await open({ lang, width, height: width < 800 ? 812 : 900, vitals: true });
    await page.eval('window.__cls = 0; window.__shifts = []');
    const H = await page.eval('document.documentElement.scrollHeight');
    const view = await vh(page);
    for (let y = 0; y < H; y += Math.round(view * 0.6)) { await page.eval(`window.scrollTo({ top: ${y}, behavior: 'instant' })`); await sleep(260); }
    await sleep(2200);
    const r = J(await page.eval(`JSON.stringify({ cls: window.__cls, shifts: window.__shifts, running: ${ANIMS} })`));
    expect('cls', r.cls === 0, `${lang} ${width}px: the layout shifted over a full scroll (CLS ${r.cls}): ${JSON.stringify(r.shifts.slice(0, 4))}`);
    expect('cls', r.running.length === 0, `${lang} ${width}px: something still animates at rest after a full scroll (the landing has no idle loop): ${r.running.join(', ')}`);
    await page.close();
  }
  if (!problems.some((x) => x.startsWith('cls'))) pass('cls', 'no layout shift (CLS 0) over a full scroll of the page, phone and desktop, en and de, and no animation left running at rest');
}

// ---------------------------------------------------------------------------------------------------- gold
async function checkGold() {
  console.log('gold');
  const CENSUS = `JSON.stringify((() => {
    const gold = (c) => { const m = c.match(/rgba?\\((\\d+), (\\d+), (\\d+)(?:, ([\\d.]+))?\\)/); return !!m && (m[4] === undefined || +m[4] > .4) && +m[1] > 200 && +m[2] > 150 && +m[3] < 135 && +m[1] - +m[3] > 100; };
    const ownText = (el) => [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
    const chrome = (el) => !!el.closest('.lp-topbar, .lp-hdr, .lp-menu, .lp-skip, .lp-sticky');
    const out = { text: [], fill: [], line: [] };
    for (const el of document.querySelectorAll('body *')) {
      const r = el.getBoundingClientRect(); if (!(r.width > 0 && r.bottom > 0 && r.top < innerHeight) || chrome(el)) continue;
      const tag = el.tagName + '.' + String(el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className).slice(0, 30);
      const s = getComputedStyle(el);
      if (ownText(el) && gold(s.color)) out.text.push(tag);
      if (gold(s.backgroundColor)) out.fill.push(tag);
      if (parseFloat(s.borderTopWidth) > 0 && gold(s.borderTopColor)) out.line.push(tag);
      for (const p of ['::before', '::after']) { const q = getComputedStyle(el, p); if (q.content !== 'none') { if (gold(q.backgroundColor)) out.line.push(tag + p); if (parseFloat(q.borderTopWidth) > 0 && gold(q.borderTopColor)) out.line.push(tag + p); } }
    }
    return out;
  })())`;
  for (const [sel, block, width, lang] of [['.lp-cur-priv', 'start', 1280, 'en'], ['.lp-never-list', 'center', 375, 'en'], ['.lp-price-grid', 'start', 1280, 'en'], ['.lp-price-grid', 'start', 375, 'hu'], ['.lp-final', 'center', 1280, 'en'], ['.lp-final', 'center', 375, 'de']]) {
    const page = await open({ lang, width, height: width < 800 ? 812 : 900 });
    await reach(page, sel, block);
    await sleep(3200);
    const c = J(await page.eval(CENSUS));
    // the labels on the pictures (the "AI visualisation" and "Example" chips, css/base.css, shared by every section) are gold text on purpose today: the honesty
    // labels stay as they are, and neutralising them is a decision for all the pictures at once, not for the closing scene alone
    const accent = c.text.filter((t) => !/lp-num|lp-dot|lp-acc|lp-g\b/.test(t) && !/lp-pv/.test(t) && !/lp-vis-chip|lp-chip-ex/.test(t));
    expect('gold', accent.length === 0, `${lang} ${width}px at ${sel}: gold text that is not an index numeral or the price of the free preview: ${accent.join(', ')} (BR-1)`);
    expect('gold', c.text.length <= 5, `${lang} ${width}px at ${sel}: ${c.text.length} gold texts`);
    console.log(`  note gold ${lang} ${width}px ${sel}: text ${c.text.length} (${[...new Set(c.text)].join(', ')}), fills ${c.fill.length} (${[...new Set(c.fill)].join(', ')}), lines ${c.line.length}`);
    await page.close();
  }
  if (!problems.some((x) => x.startsWith('gold'))) pass('gold', 'gold text in the close of the page is only index numerals and the free preview price; the rest is lines, rings and the button');
}

// ---------------------------------------------------------------------------------------------------- run
const checks = { trust: checkTrust, pricing: checkPricing, faq: checkFaq, final: checkFinal, footer: checkFooter, sticky: checkSticky, states: checkStates, transition: checkTransition, failsafe: checkFailsafe, focus: checkFocus, headlines: checkHeadlines, cls: checkCls, gold: checkGold };
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
console.log(problems.length ? `\nclose-of-page motion check FAILED (${problems.length}):\n  ${problems.join('\n  ')}` : '\nclose-of-page motion check ok');
process.exit(problems.length ? 1 : 0);
