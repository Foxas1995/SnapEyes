// The checks of the prerendered first screen (src/landing/shell, written into dist/index.html by the heroShell plugin of vite.config.ts).
//   node scripts/check_shell.mjs [--dist dist] [--shots <folder>]        both parts
//   node scripts/check_shell.mjs --rules                                 part 1 only (Node, no browser, no build needed)
//
// Part 1, the decision script (src/landing/shell/scripts.ts) against src/shared/lang.ts detectLang and detectMarket, over a matrix of
// links (?m=, ?lang=), stored choices (localStorage snapeyes.market, snapeyes.lang) and browser languages: the script names the
// visitor's language and market exactly as the two functions do (window.__lpShell), and hides the shell
// never (a script that fails hides it).
// Part 2, in real Chrome on the built page at 375, 768 and 1280 px, in English, German, Lithuanian and Hungarian (and the
// Lithuanian, Hungarian and Australian markets): the shell (the page with its main script blocked: only the static HTML and the inline
// scripts, the swap to the visitor's language included) and the live first screen (React, after the shell has gone) occupy the same
// boxes, with the same styles and the same pixels (the held-back price aside), say the same words and link to the same /try, the
// shell is gone after the handoff, no id is used twice, the honesty words are in the static HTML of every language (the label
// "AI visualisation" and "Printing is not included" inside the picture's frame, the lead names the digital file), the LCP picture
// is preloaded with the srcset of the image.
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';
import { runnerImport } from 'vite';
import { launch, sleep } from './lib/cdp.mjs';
import { serve } from './lib/static.mjs';

const ROOT = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const args = process.argv.slice(2);
const flag = (n) => args.includes(n);
const opt = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const problems = [];
const note = (m) => problems.push(m);

async function load(p) {
  return (await runnerImport(p, { root: ROOT, configFile: false, logLevel: 'silent' })).module;
}

// ------------------------------------------------------------------------------------------------ part 1: the rule
async function rules() {
  const markets = await load('./src/shared/markets.ts');
  const lang = await load('./src/shared/lang.ts');
  const scripts = await load('./src/landing/shell/scripts.ts');
  const all = Object.keys(markets.MARKETS);
  const rule = {
    defaultMarket: markets.DEFAULT_MARKET,
    selectable: markets.SELECTABLE,
    allowed: Object.fromEntries(all.map((m) => [m, lang.marketLangs(m)])),
    own: Object.fromEntries(all.map((m) => [m, lang.marketDefaultLang(m)])),
  };
  const script = scripts.decisionScript(rule);
  const ctxOf = (s) => {
    const preloads = [];
    const doc = { documentElement: { className: '' }, head: { appendChild: (n) => preloads.push(n) }, createElement: () => ({ setAttribute() {} }) };
    const win = {};
    return { doc, preloads, win, sandbox: { URLSearchParams, location: { search: s.search }, localStorage: { getItem: (k) => (k in s.store ? s.store[k] : null) }, navigator: { language: s.nav }, document: doc, window: win } };
  };
  const qm = [null, 'au', 'hu', 'lt', 'AU ', 'xx', 'eu'];
  const ql = [null, 'en', 'de', 'lt', 'hu', 'xx'];
  const sm = [null, 'au', 'hu', 'lt', 'zz'];
  const sl = [null, 'de', 'lt', 'hu', 'fr'];
  const nav = ['en-US', 'de-AT', 'lt', 'hu-HU', 'fr-FR', ''];
  let n = 0;
  const saved = { window: globalThis.window, navigator: Object.getOwnPropertyDescriptor(globalThis, 'navigator') };
  try {
    for (const a of qm) for (const b of ql) for (const c of sm) for (const d of sl) for (const e of nav) {
      const params = new URLSearchParams();
      if (a !== null) params.set('m', a);
      if (b !== null) params.set('lang', b);
      const store = {};
      if (c !== null) store['snapeyes.market'] = c;
      if (d !== null) store['snapeyes.lang'] = d;
      const s = { search: params.size ? `?${params}` : '', store, nav: e };
      // the real rule, in the page's own globals
      globalThis.window = { location: { search: s.search }, localStorage: { getItem: (k) => (k in store ? store[k] : null), setItem() {}, removeItem() {} } };
      Object.defineProperty(globalThis, 'navigator', { value: { language: e }, configurable: true });
      const m = markets.detectMarket();
      const l = lang.detectLang(m);
      const wantHide = false;
      // the script
      const { doc, preloads, win, sandbox } = ctxOf(s);
      vm.runInNewContext(script, sandbox);
      const gotHide = doc.documentElement.className.includes('lp-noshell');
      const said = win.__lpShell;
      n += 1;
      if (gotHide !== wantHide || preloads.length > 0 || !said || said.l !== l || said.m !== m) {
        note(`decision script: ${JSON.stringify(s)} -> market ${m}, language ${l}: the rule says hide ${wantHide}; the script says hide ${gotHide}, language ${said?.l}, market ${said?.m} (and it added ${preloads.length} nodes to the head, it must add none)`);
        if (problems.length > 12) return n;
      }
    }
  } finally {
    globalThis.window = saved.window;
    if (saved.navigator) Object.defineProperty(globalThis, 'navigator', saved.navigator);
  }
  return n;
}

// ------------------------------------------------------------------------------------------------ part 2: the built page in Chrome
const LANDMARKS = ['.lp-topbar', '.lp-hdr', '.lp-hdr .lp-logo', '.lp-nav', '.lp-seg', '.lp-hdr .lp-btn-line', '.lp-hero', '.lp-eyebrow', '#h1', '.lp-lead', '.lp-cta-row', '#ctaHero', '.lp-link-quiet',
  '.lp-micro', '.lp-computer-hint', '.lp-hero-fig', '.lp-hero-frame', '#heroImg', '.lp-frame-chip', '.lp-disc', '.lp-disc-label', '#heroCap'];
const STYLE_PROPS = ['color', 'font-size', 'font-family', 'font-weight', 'line-height', 'letter-spacing', 'background-color', 'opacity', 'display', 'position', 'border-radius', 'padding-top', 'margin-top', 'object-fit', 'text-transform'];

const MEASURE = `(() => {
  const L = ${JSON.stringify(LANDMARKS)}, P = ${JSON.stringify(STYLE_PROPS)};
  const out = {};
  for (const sel of L) {
    const el = document.querySelector(sel);
    if (!el) { out[sel] = null; continue; }
    const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
    out[sel] = { box: [r.left, r.top + scrollY, r.width, r.height].map((v) => Math.round(v * 100) / 100), style: P.map((p) => cs.getPropertyValue(p)).join('|') };
  }
  out['.lp-micro li'] = Array.from(document.querySelectorAll('.lp-micro li')).map((li) => { const r = li.getBoundingClientRect(); return [r.left, r.top + scrollY, r.width, r.height].map((v) => Math.round(v * 100) / 100); });
  out.ids = (() => { const seen = {}, dup = []; for (const e of document.querySelectorAll('[id]')) { if (seen[e.id]) dup.push(e.id); seen[e.id] = 1; } return dup; })();
  out.shell = !!document.getElementById('shell') && getComputedStyle(document.getElementById('shell')).display !== 'none';
  out.words = [document.documentElement.lang, document.getElementById('h1').textContent, document.getElementById('barText').textContent, document.getElementById('ctaHero').textContent, document.querySelector('.lp-hdr .lp-btn-line').getAttribute('href'), document.getElementById('ctaHero').getAttribute('href'), document.querySelector('.lp-link-quiet').textContent, document.getElementById('heroCap').textContent, [...document.querySelectorAll('#langSeg button')].map((b) => b.textContent + b.getAttribute('aria-pressed')).join(',')].join(' | ');
  out.bar = getComputedStyle(document.documentElement).getPropertyValue('--bar-h');
  return JSON.stringify(out);
})()`;
const HIDE_PRICE = `(() => { const s = document.createElement('style'); s.textContent = '.lp-price, .lp-glint { visibility: hidden !important }'; document.head.appendChild(s); })()`;
const sha = (b) => createHash('sha256').update(b).digest('hex').slice(0, 16);


/** Compare two PNGs in Chrome itself (canvas): how many pixels differ by more than 8 in any channel, and where. */
async function pngDiff(chrome, a, b) {
  const page = await chrome.page({ width: 400, height: 300 });
  const expr = `(async () => {
    const load = (b64) => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = 'data:image/png;base64,' + b64; });
    const [x, y] = await Promise.all([load(${JSON.stringify(a.toString('base64'))}), load(${JSON.stringify(b.toString('base64'))})]);
    if (x.width !== y.width || x.height !== y.height) return JSON.stringify({ size: [x.width, x.height, y.width, y.height] });
    const data = (im) => { const c = document.createElement('canvas'); c.width = im.width; c.height = im.height; const g = c.getContext('2d'); g.drawImage(im, 0, 0); return g.getImageData(0, 0, im.width, im.height).data; };
    const p = data(x), q = data(y);
    let n = 0, x0 = 1e9, y0 = 1e9, x1 = -1, y1 = -1;
    for (let i = 0; i < p.length; i += 4) {
      if (Math.abs(p[i] - q[i]) > 8 || Math.abs(p[i + 1] - q[i + 1]) > 8 || Math.abs(p[i + 2] - q[i + 2]) > 8) {
        n++;
        const k = i / 4, px = k % x.width, py = Math.floor(k / x.width);
        x0 = Math.min(x0, px); y0 = Math.min(y0, py); x1 = Math.max(x1, px); y1 = Math.max(y1, py);
      }
    }
    return JSON.stringify({ n, box: n ? [x0, y0, x1, y1] : null });
  })()`;
  const r = JSON.parse(await page.eval(expr));
  await page.close();
  return r;
}

function close(a, b, tol = 0.51) {
  return a.length === b.length && a.every((v, i) => Math.abs(v - b[i]) <= tol);
}

async function browser(dist, shotsDir) {
  const site = await serve(dist, { vercelFile: join(ROOT, 'vercel.json') });
  const chrome = await launch();
  const origin = `http://127.0.0.1:${site.port}`;
  const html = readFileSync(join(dist, 'index.html'), 'utf8');
  // the page's own script is started by the inline loader after the LCP picture (vite.config.ts lateMainScript), so it is in the loader, not in a tag
  const mainJs = /var M="(\/assets\/main-[^"]+\.js)"/.exec(html)?.[1];
  if (!mainJs) note('dist/index.html: the loader of the page script is missing');
  if (/<script type="module"[^>]*src=/.test(html) || /<link rel="modulepreload"/.test(html)) note('dist/index.html: a module script or modulepreload is still in the head (it would compete with the LCP picture)');
  // every page starts as a first visit: the page remembers the market of a ?m= link (localStorage), which would change the next page
  const fresh = async (opts) => {
    const p = await chrome.page(opts);
    await p.goto(`${origin}/imprint?lang=en`);
    await p.loaded();
    await p.send('Storage.clearDataForOrigin', { origin, storageTypes: 'all' }).catch(() => undefined);
    return p;
  };
  const LANGS = ['en', 'de', 'lt', 'hu'];
  const COPY = Object.fromEntries(LANGS.map((l) => [l, JSON.parse(readFileSync(join(ROOT, `src/landing/copy/${l}.json`), 'utf8'))]));
  try {
    // static HTML facts (what a crawler or a script-less visitor gets): the English shell, and a template per other language
    const shellHtml = html.slice(html.indexOf('<div id="shell"'), html.indexOf('<div id="root">'));
    const decode = (s) => s.replace(/&#x27;/g, "'").replace(/&quot;/g, '"').replace(/&amp;/g, '&');
    const pre = /<link rel="preload" as="image"[^>]*imagesrcset="([^"]+)"[^>]*imagesizes="([^"]+)"/.exec(html.slice(0, html.indexOf('<body')));
    if (!pre) note('head: no preload of the LCP picture');
    const parts = { en: shellHtml.slice(0, shellHtml.indexOf('<template')) };
    for (const l of LANGS) if (l !== 'en') {
      const a = shellHtml.indexOf(`<template id="tpl-${l}">`);
      parts[l] = a < 0 ? '' : shellHtml.slice(a, shellHtml.indexOf('</template>', a));
      if (a < 0) note(`static HTML: the ${l} first screen (template tpl-${l}) is missing`);
    }
    for (const l of LANGS) {
      const copy = COPY[l];
      const f = (s) => s.replace(/\{(\w+)\}/g, (w, k) => copy.facts[k] ?? w);
      const text = decode(parts[l]);
      for (const [what, s] of [['the label inside the picture frame', copy.hero.chipTitle], ['its second line', copy.hero.chipBody], ['the lead (digital file, printing not included)', f(copy.hero.lead)],
        ['the caption', copy.hero.caption], ['the bar sentence', copy.bar.soon], ['the picture alt text', copy.hero.imageAlt]]) {
        if (!text.includes(s)) note(`static HTML (${l}): ${what} is missing ("${s.slice(0, 50)}")`);
      }
      if (!/<div class="lp-frame-chip"[^>]*><b>[^<]+<\/b><span>[^<]+<\/span><\/div><\/div>/.test(parts[l])) note(`static HTML (${l}): the label is not inside the picture frame (.lp-hero-frame)`);
      if (!/<img id="heroImg"[^>]*fetchpriority="high"/i.test(parts[l])) note(`static HTML (${l}): the hero picture is not fetchpriority=high`);
      const img = /<img id="heroImg" src="([^"]+)" srcSet="([^"]+)" sizes="([^"]+)"/i.exec(parts[l]);
      if (pre && (!img || pre[1] !== img[2] || pre[2] !== img[3])) note(`head: the preload srcset or sizes differs from the hero image of the ${l} shell`);
      if (!/class="lp-price"[^>]*inert/.test(parts[l])) note(`static HTML (${l}): the price line is not held back`);
      if (/€\s?\d|\d\s?€|A\$\s?\d/.test(parts[l].replace(/class="lp-price"[\s\S]*?<\/li>/g, ''))) note(`static HTML (${l}): a price is printed outside the held-back line`);
    }

    // the shell (main script blocked) against the live first screen, for every language and the markets with a language of their own
    const sizes = [[375, 812, true], [768, 1024, false], [1280, 800, false]];
    const cases = [['en', '/', 'eu'], ['de', '/?lang=de', 'eu'], ['lt', '/?lang=lt', 'eu'], ['hu', '/?lang=hu', 'eu'], ['lt', '/?m=lt', 'lt'], ['hu', '/?m=hu', 'hu'], ['en', '/?m=au', 'au'], ['de', '/?m=au&lang=de', 'au']];
    const shots = [];
    for (const [lang, url, market] of cases) {
      for (const [w, h, mobile] of sizes) {
        if (market !== 'eu' && w !== 375) continue;
        const tag = `${lang}${market === 'eu' ? '' : ' m=' + market} ${w}px`;
        // 1. the shell: the page with its main script blocked, so nothing but the static HTML and the inline scripts has run
        const a = await fresh({ width: w, height: h, mobile, dpr: 1, reduceMotion: true });
        await a.send('Network.setBlockedURLs', { urls: [`*${mainJs}`] });
        await a.goto(`${origin}${url}`);
        await a.loaded();
        await sleep(400);
        await a.eval(HIDE_PRICE);
        const shellM = JSON.parse(await a.eval(MEASURE));
        const shellPng = await a.shot();
        await a.close();
        // 2. the live first screen
        const b = await fresh({ width: w, height: h, mobile, dpr: 1, reduceMotion: true });
        await b.goto(`${origin}${url}`);
        await b.loaded();
        for (let i = 0; i < 100; i++) {
          if (await b.eval("!document.getElementById('shell') && !!document.querySelector('#root .lp-hero')")) break;
          await sleep(100);
        }
        await sleep(700);
        await b.eval(HIDE_PRICE);
        const liveM = JSON.parse(await b.eval(MEASURE));
        const livePng = await b.shot();
        const templates = await b.eval("document.querySelectorAll('template[id^=\"tpl-\"]').length");
        await b.close();
        if (!shellM.shell) note(`${tag}: the shell is not on screen before React`);
        if (liveM.shell) note(`${tag}: the shell is still on screen after React took over`);
        if (templates) note(`${tag}: ${templates} language templates are still in the page after the handoff`);
        if (liveM.ids.length) note(`${tag}: ids used twice in the live page: ${liveM.ids.join(', ')}`);
        if (shellM.ids.length) note(`${tag}: ids used twice in the shell page: ${shellM.ids.join(', ')}`);
        if (shellM.bar !== liveM.bar) note(`${tag}: --bar-h is ${shellM.bar} in the shell and ${liveM.bar} in the live page`);
        if (shellM.words !== liveM.words) note(`${tag}: the shell says "${shellM.words}", the live page "${liveM.words}"`);
        if (shellM.words.split(' | ')[0] !== lang) note(`${tag}: the shell's html lang is ${shellM.words.split(' | ')[0]}`);
        if (shellM.words.split(' | ')[1] !== COPY[lang].hero.title) note(`${tag}: the shell's title is "${shellM.words.split(' | ')[1]}", the copy says "${COPY[lang].hero.title}"`);
        for (const sel of LANDMARKS) {
          const x = shellM[sel], y = liveM[sel];
          if (!x || !y) { note(`${tag}: ${sel} is missing in the ${x ? 'live page' : 'shell'}`); continue; }
          if (!close(x.box, y.box)) note(`${tag}: ${sel} box ${x.box} in the shell, ${y.box} live`);
          if (x.style !== y.style) note(`${tag}: ${sel} styles differ: ${x.style} | ${y.style}`);
        }
        const lx = shellM['.lp-micro li'], ly = liveM['.lp-micro li'];
        // the held-back price line is made in the default currency: on the forint and the Australian dollar markets its text (invisible) is another width
        const sameBox = (bx, i) => (['hu', 'au'].includes(market) && i === lx.length - 1 ? close(bx.slice(0, 2), ly[i].slice(0, 2)) && Math.abs(bx[3] - ly[i][3]) <= 0.51 : close(bx, ly[i]));
        if (lx.length !== ly.length || lx.some((bx, i) => !sameBox(bx, i))) note(`${tag}: the micro line items differ: ${JSON.stringify(lx)} | ${JSON.stringify(ly)}`);
        if (shotsDir) {
          mkdirSync(shotsDir, { recursive: true });
          writeFileSync(join(shotsDir, `shell_${lang}_${market}_${w}.png`), shellPng);
          writeFileSync(join(shotsDir, `live_${lang}_${market}_${w}.png`), livePng);
        }
        shots.push([tag, sha(shellPng), sha(livePng)]);
        // an antialiasing speck on the edge of a rounded shadow may differ by a pixel; more than a handful is a real difference
        const d = await pngDiff(chrome, shellPng, livePng);
        if (d.size || d.n > 30) note(`${tag}: the first screen pixels differ between the shell and the live page: ${d.size ? `sizes ${d.size}` : `${d.n} pixels, ${d.box}`} (run with --shots and compare the shell_ and live_ pictures)`);
        else console.log(`${tag}: shell and live first screen: ${d.n} pixels differ by more than 8 of ${w * h}`);
      }
    }
    // a German browser on the plain address has the German shell
    {
      const p = await fresh({ width: 375, height: 812, mobile: true, reduceMotion: true });
      await p.send('Emulation.setLocaleOverride', { locale: 'de-DE' }).catch(() => undefined);
      await p.send('Network.setUserAgentOverride', { userAgent: 'Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36', acceptLanguage: 'de-DE' }).catch(() => undefined);
      await p.send('Network.setBlockedURLs', { urls: [`*${mainJs}`] });
      await p.goto(`${origin}/`);
      await p.loaded();
      await sleep(300);
      const r = JSON.parse(await p.eval("JSON.stringify([!!document.getElementById('shell') && getComputedStyle(document.getElementById('shell')).display !== 'none', document.getElementById('h1').textContent, document.documentElement.lang])"));
      if (!r[0] || r[1] !== COPY.de.hero.title || r[2] !== 'de') note(`a German browser on /: the shell is ${r[0] ? '' : 'not '}on screen with "${r[1]}" and html lang ${r[2]}, it should be the German one`);
      await p.close();
    }
    return shots;
  } finally {
    await chrome.close();
    await site.close();
  }
}

const n = await rules();
if (!problems.length) console.log(`decision script: ${n} combinations of link, stored choice and browser language agree with detectLang and detectMarket`);
if (!flag('--rules')) {
  const dist = resolve(opt('--dist', join(ROOT, 'dist')));
  if (!existsSync(join(dist, 'index.html'))) {
    console.error(`no build at ${dist}: run npm run build first`);
    process.exit(2);
  }
  const shots = await browser(dist, opt('--shots', null));
  console.log(`shell against live first screen: ${shots.map(([t]) => t).join(', ')} compared (boxes, styles, pixels)`);
}
if (problems.length) {
  console.error(`shell check FAILED (${problems.length}):\n  ${problems.join('\n  ')}`);
  process.exit(1);
}
console.log('shell check ok');
