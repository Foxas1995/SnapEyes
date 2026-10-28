// The head of the landing page as a crawler reads it, per language (QA of 2026-10-20: / , ?lang=de, ?lang=lt and ?lang=hu were byte-identical HTML:
// English og:title, og:description and og:locale, og:url always the root, no canonical, English words on the share picture).
//   npm run build && node scripts/check_langheads.mjs [--dist dist] [--browser]
//   node scripts/check_langheads.mjs --dist <an older build> --vercel <its vercel.json>      the old one-file build fails (that is the point of the check)
//
// Without a browser and without any script, over HTTP, as a crawler (user agent facebookexternalhit, no Accept-Language, no cookies), against a server that
// answers the way the Vercel deployment does (scripts/lib/static.mjs: the file system first, then the rewrites of vercel.json):
//   1. the build has the five editions (dist/lp/en.html, de, lt, hu, hr) and NO dist/index.html (a file for / would answer before any rewrite: Vercel checks
//      the file system first, proven on the CLI's own build output), every rewrite of vercel.json names a clean path ("/lp/de", never ".html", which the
//      cleanUrls redirect catches) that is a file of the build, and no file of the build answers the source of a rewrite;
//   2. /, /?lang=en, de, lt, hu, hr, ?lang=de&m=au, ?m=lt, ?m=hu, ?lang=en&m=hu, an unknown or upper-case ?lang= are answered 200 at once (no redirect) with the
//      edition of the language the link asks for, whose html lang, title, description, canonical, hreflang, og:url, og:locale (and its three alternates), og:title,
//      og:description, og:image (+ width, height, alt) and twitter tags are the ones the page's own copy (src/landing/copy/<lang>.json meta), src/shared/lang.ts and
//      src/landing/shell/share.json give, with exactly one canonical, the page's own address (English at /, the others at /?lang=xx);
//   3. the four editions differ in their head and in nothing else (the body is byte for byte the same), so the language is one thing and the page another;
//   4. the share pictures: the English card and one per language, 1200 x 630, JPEG, under 150 kB each, and every one of them different; the words of the three
//      made ones are what scripts/make_og_cards.py draws from the copy (it is run with --check when Python and Pillow are there);
//   5. /try (one file for every language) has its share tags, with an absolute https://snapeyes.com picture that is a file of the build;
//   6. the source index.html still says what the share.json says in English (the alt text), so the English edition and the template cannot drift.
// With --browser, in real Chrome (the page's script runs): every edition keeps its own head once the script has run and the first screen has been taken over
// (a visitor who runs the script is not worse off than a crawler), and a switch of the language on the page changes title, canonical and og:url to the new one.
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync, statSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { runnerImport } from 'vite';
import { launch, sleep } from './lib/cdp.mjs';
import { LANDING_DIR, SITE_ORIGIN, landingFile, readHead } from './lib/langheads.mjs';
import { serve } from './lib/static.mjs';

const ROOT = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const args = process.argv.slice(2);
const opt = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const dist = resolve(opt('--dist', join(ROOT, 'dist')));
const vercelFile = resolve(opt('--vercel', join(ROOT, 'vercel.json')));
const problems = [];
const fail = (m) => problems.push(m);
const UA = 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)';
const LANGS = ['en', 'de', 'lt', 'hu', 'hr'];
const CARD_MAX = 150_000;

const load = async (p) => (await runnerImport(p, { configFile: false, logLevel: 'silent' })).module;
const langMod = await load('./src/shared/lang.ts');
const readJson = (p) => JSON.parse(readFileSync(join(ROOT, p), 'utf8').replace(/^﻿/, ''));
const share = readJson('src/landing/shell/share.json');
const metas = Object.fromEntries(LANGS.map((l) => [l, readJson(`src/landing/copy/${l}.json`).meta]));
const vercel = JSON.parse(readFileSync(vercelFile, 'utf8'));

/** width and height of a JPEG, from its first start-of-frame marker. */
function jpegSize(buf) {
  if (buf[0] !== 0xff || buf[1] !== 0xd8) return null;
  for (let i = 2; i + 9 < buf.length;) {
    if (buf[i] !== 0xff) { i++; continue; }
    const m = buf[i + 1];
    if (m === 0xd8 || (m >= 0xd0 && m <= 0xd7) || m === 0x01 || m === 0xff) { i += m === 0xff ? 1 : 2; continue; }
    const len = buf.readUInt16BE(i + 2);
    if ((m >= 0xc0 && m <= 0xc3) || (m >= 0xc5 && m <= 0xc7) || (m >= 0xc9 && m <= 0xcb) || (m >= 0xcd && m <= 0xcf)) return { h: buf.readUInt16BE(i + 5), w: buf.readUInt16BE(i + 7) };
    i += 2 + len;
  }
  return null;
}

// ---------------------------------------------------------------------------------------------------- 1. the build and the rewrites
if (existsSync(join(dist, 'index.html'))) fail(`dist/index.html exists: a file for / answers before any rewrite of vercel.json (Vercel checks the file system first), so /?lang=de would be given the English page; the build must write dist/${LANDING_DIR}/<lang>.html only`);
for (const l of LANGS) if (!existsSync(join(dist, landingFile(l)))) fail(`dist/${landingFile(l)} is missing`);
const rewrites = vercel.rewrites ?? [];
if (!rewrites.length) fail('vercel.json has no rewrites: nothing sends the language links to their editions');
for (const r of rewrites) {
  if (/\.html$/.test(r.destination) || /:[A-Za-z_]/.test(r.destination)) fail(`vercel.json: the rewrite of ${r.source} goes to ${r.destination}: the destination is the clean path of the file, no ".html" (the cleanUrls redirect would catch it) and no placeholder`);
  else if (!existsSync(join(dist, `${r.destination}.html`)) && !existsSync(join(dist, r.destination, 'index.html'))) fail(`vercel.json: the rewrite of ${r.source} goes to ${r.destination}, which is no file of the build`);
  // a plain path as the source: no file of the build answers it (the file system is checked first)
  if (/^\/[\w/.-]*$/.test(r.source)) {
    const p = r.source.slice(1);
    for (const f of r.source === '/' ? ['index.html'] : [`${p}.html`, `${p}/index.html`, p]) {
      if (existsSync(join(dist, f)) && statSync(join(dist, f)).isFile()) fail(`vercel.json: a file of the build (${f}) answers ${r.source} before the rewrite is tried`);
    }
  }
}
for (const l of LANGS) {
  const has = rewrites.some((r) => r.source === '/' && (r.has ?? []).some((h) => h.type === 'query' && h.key === 'lang' && h.value === l) && r.destination === `/${LANDING_DIR}/${l}`);
  if (!has) fail(`vercel.json: no rewrite of /?lang=${l} to /${LANDING_DIR}/${l}`);
}
const last = rewrites.at(-1);
if (!last || last.source !== '/' || last.has || last.destination !== `/${LANDING_DIR}/en`) fail(`vercel.json: the last rewrite is not the plain / to /${LANDING_DIR}/en`);

// ---------------------------------------------------------------------------------------------------- 2. what a crawler is given
const expected = (l) => {
  const q = langMod.langQuery(l);
  const url = `${SITE_ORIGIN}/${q}`;
  return {
    htmlLang: langMod.LOCALES[l].html,
    title: metas[l].title,
    description: metas[l].description,
    canonical: url,
    ogUrl: url,
    ogLocale: langMod.LOCALES[l].og,
    ogLocaleAlt: LANGS.filter((x) => x !== l).map((x) => langMod.LOCALES[x].og),
    ogTitle: metas[l].title,
    ogDescription: metas[l].shareDescription,
    ogImage: `${SITE_ORIGIN}/assets/atelier/og-founder-eye${l === 'en' ? '' : `-${l}`}.jpg`,
    ogImageAlt: share[l].alt,
    twitterTitle: metas[l].title,
    twitterDescription: metas[l].shareDescription,
  };
};
const HREFLANG = { en: `${SITE_ORIGIN}/`, de: `${SITE_ORIGIN}/?lang=de`, lt: `${SITE_ORIGIN}/?lang=lt`, hu: `${SITE_ORIGIN}/?lang=hu`, hr: `${SITE_ORIGIN}/?lang=hr`, 'x-default': `${SITE_ORIGIN}/` };

const LINKS = [
  ['/', 'en'], ['/?lang=en', 'en'], ['/?lang=de', 'de'], ['/?lang=lt', 'lt'], ['/?lang=hu', 'hu'], ['/?lang=hr', 'hr'],
  ['/?lang=de&m=au', 'de'], ['/?lang=de&m=hu', 'de'], ['/?m=lt', 'lt'], ['/?m=hu', 'hu'], ['/?lang=en&m=hu', 'en'], ['/?m=au', 'en'], ['/?m=eu', 'en'],
  ['/?lang=fr', 'en'], ['/?lang=DE', 'en'], ['/?utm_source=facebook&fbclid=abc', 'en'], ['/?utm_source=x&lang=lt', 'lt'],
];

const site = await serve(dist, { vercelFile });
const origin = `http://127.0.0.1:${site.port}`;
const bodies = {};
const fetched = {};
const link = (l) => (l === 'en' ? '/' : `/?lang=${l}`);
try {
  for (const [link, l] of LINKS) {
    let res;
    try { res = await fetch(origin + link, { redirect: 'manual', headers: { 'user-agent': UA, accept: '*/*' } }); } catch (e) { fail(`${link}: ${e instanceof Error ? e.message : e}`); continue; }
    if (res.status !== 200) { fail(`${link}: status ${res.status}${res.headers.get('location') ? ` to ${res.headers.get('location')}` : ''}, not 200 at once`); continue; }
    const html = await res.text();
    fetched[link] = html;
    const got = readHead(html);
    const want = expected(l);
    for (const [k, v] of Object.entries(want)) {
      const g = got[k];
      if (JSON.stringify(g) !== JSON.stringify(v)) fail(`${link} (${l}): ${k} is ${JSON.stringify(g)}, expected ${JSON.stringify(v)}`);
    }
    if (got.canonicals !== 1) fail(`${link}: ${got.canonicals} canonical links, expected exactly one`);
    if (JSON.stringify(got.hreflang) !== JSON.stringify(HREFLANG)) fail(`${link}: the hreflang alternates are ${JSON.stringify(got.hreflang)}`);
    for (const [k, v] of [['ogType', 'website'], ['ogSiteName', 'SnapEyes'], ['ogImageWidth', '1200'], ['ogImageHeight', '630'], ['twitterCard', 'summary_large_image']]) if (got[k] !== v) fail(`${link}: ${k} is ${JSON.stringify(got[k])}, expected ${JSON.stringify(v)}`);
    if (got.twitterImage !== got.ogImage) fail(`${link}: twitter:image differs from og:image`);
    if (!bodies[l]) bodies[l] = html.slice(html.indexOf('<body'));
    else if (bodies[l] !== html.slice(html.indexOf('<body'))) fail(`${link}: the body differs from the other links of ${l}`);
  }
  // the 404 of an unknown path stays a 404 (a rewrite must not swallow it)
  const nf = await fetch(`${origin}/no-such-page`, { redirect: 'manual', headers: { 'user-agent': UA } });
  if (nf.status !== 404) fail(`/no-such-page: status ${nf.status}, expected 404 (a rewrite swallowed it?)`);
  for (const direct of ['/index.html', '/index']) {
    const r = await fetch(origin + direct, { redirect: 'manual' });
    if (r.status === 200) fail(`${direct}: answered 200 (there is no index.html in the build; on Vercel it is a 308 to /)`);
  }

  // ------------------------------------------------------------------------------------------ 3. the editions differ in their head and nothing else
  for (const a of LANGS) for (const b of LANGS) {
    if (a >= b || !bodies[a] || !bodies[b]) continue;
    if (bodies[a] !== bodies[b]) fail(`the body of the ${a} and the ${b} edition differ (only the head may)`);
    const ha = readHead(fetched[link(a)] ?? ''), hb = readHead(fetched[link(b)] ?? '');
    for (const k of ['title', 'description', 'ogTitle', 'ogDescription', 'ogUrl', 'canonical', 'ogImage', 'ogImageAlt', 'ogLocale', 'twitterTitle', 'htmlLang']) {
      if (ha[k] && ha[k] === hb[k]) fail(`the ${a} and the ${b} edition have the same ${k}: ${JSON.stringify(ha[k]).slice(0, 80)}`);
    }
  }
  // English must still be the English the page always had (the copy's own meta)
  const en = readHead(fetched['/'] ?? '');
  if (en.title !== metas.en.title || en.ogImage !== `${SITE_ORIGIN}/assets/atelier/og-founder-eye.jpg`) fail('the English edition is not the English page');

  // ------------------------------------------------------------------------------------------ 4. the share pictures
  const cards = [];
  for (const l of LANGS) {
    const file = join(dist, 'assets', 'atelier', `og-founder-eye${l === 'en' ? '' : `-${l}`}.jpg`);
    if (!existsSync(file)) { fail(`the share picture of ${l} is not in the build (${file})`); continue; }
    const buf = readFileSync(file);
    const size = jpegSize(buf);
    if (!size || size.w !== 1200 || size.h !== 630) fail(`${l} share picture: ${size ? `${size.w}x${size.h}` : 'not a JPEG'}, expected 1200x630`);
    if (buf.length > CARD_MAX) fail(`${l} share picture: ${buf.length} bytes, over ${CARD_MAX}`);
    cards.push([l, buf.length, buf.toString('base64')]);
    const served = await fetch(`${origin}/assets/atelier/og-founder-eye${l === 'en' ? '' : `-${l}`}.jpg`, { headers: { 'user-agent': UA } });
    if (served.status !== 200 || !/image\/jpeg/.test(served.headers.get('content-type') ?? '')) fail(`${l} share picture: served as ${served.status} ${served.headers.get('content-type')}`);
  }
  for (let i = 0; i < cards.length; i++) for (let j = i + 1; j < cards.length; j++) if (cards[i][2] === cards[j][2]) fail(`the share pictures of ${cards[i][0]} and ${cards[j][0]} are the same file`);
  const py = spawnSync('python', [join(ROOT, 'scripts', 'make_og_cards.py'), '--check'], { encoding: 'utf8' });
  if (py.error || /No module named/.test(py.stderr ?? '')) console.log('  note: python with Pillow and fontTools not found, the words of the cards were not compared with what make_og_cards.py draws');
  else if (py.status !== 0) fail(`scripts/make_og_cards.py --check: ${(py.stdout + py.stderr).trim().split('\n').slice(-4).join(' | ')}`);

  // ------------------------------------------------------------------------------------------ 5. /try
  const tryHtml = readFileSync(join(dist, 'try.html'), 'utf8');
  const og = (k) => new RegExp(`<meta (?:property|name)="${k}" content="([^"]*)"`).exec(tryHtml)?.[1];
  for (const k of ['og:type', 'og:site_name', 'og:url', 'og:locale', 'og:title', 'og:description', 'og:image', 'og:image:alt', 'twitter:card', 'twitter:title', 'twitter:description', 'twitter:image']) if (!og(k)) fail(`/try has no ${k}`);
  if (og('og:url') !== `${SITE_ORIGIN}/try`) fail(`/try: og:url is ${og('og:url')}`);
  if (!/^https:\/\/snapeyes\.com\/assets\/[\w./-]+\.jpg$/.test(og('og:image') ?? '') || !existsSync(join(dist, (og('og:image') ?? '').replace(SITE_ORIGIN, '')))) fail(`/try: og:image ${og('og:image')} is not an absolute picture of the build`);
  if (!/noindex/.test(tryHtml)) fail('/try lost its robots noindex');

  // ------------------------------------------------------------------------------------------ 6. the template
  const src = readFileSync(join(ROOT, 'index.html'), 'utf8');
  if (/<link rel="canonical"/.test(src)) fail('index.html (the template) has a static canonical: the build writes one per edition');
  const alt = /<meta property="og:image:alt" content="([^"]*)"/.exec(src)?.[1];
  if (alt !== share.en.alt) fail(`index.html's og:image:alt (${alt}) is not share.json's English alt text (${share.en.alt})`);

  // ------------------------------------------------------------------------------------------ the page's own script (--browser)
  if (args.includes('--browser') && !problems.length) {
    const chrome = await launch();
    try {
      const wipe = async () => {
        const p = await chrome.page({ width: 400, height: 300 });
        await p.goto(`${origin}/imprint?lang=en`);
        await p.loaded();
        await p.send('Storage.clearDataForOrigin', { origin, storageTypes: 'all' }).catch(() => undefined);
        await p.close();
      };
      const probe = `JSON.stringify({ lang: document.documentElement.lang, title: document.title, canonical: [...document.querySelectorAll('link[rel=canonical]')].map((l) => l.href),
        ogUrl: document.querySelector('meta[property="og:url"]')?.content, ogLocale: document.querySelector('meta[property="og:locale"]')?.content,
        ogTitle: document.querySelector('meta[property="og:title"]')?.content, ogImage: document.querySelector('meta[property="og:image"]')?.content,
        booted: !!document.getElementById('root')?.firstElementChild && !document.getElementById('shell') && !!document.getElementById('faq'),
        buttons: [...document.querySelectorAll('#langSeg button')].map((b) => b.getAttribute('lang')) })`;
      for (const l of LANGS) {
        await wipe();
        const page = await chrome.page({ width: 1280, height: 900 });
        await page.goto(`${origin}/${l === 'en' ? '' : `?lang=${l}`}`);
        await page.loaded();
        let st = null;
        for (let i = 0; i < 150; i++) {
          st = JSON.parse(await page.eval(probe));
          if (st.booted) break;
          await sleep(100);
        }
        const want = expected(l);
        if (!st.booted) fail(`browser ${l}: the page did not boot (React did not take over the first screen)`);
        if (st.lang !== l) fail(`browser ${l}: <html lang> is ${st.lang} once the script has run`);
        if (st.title !== want.title || st.ogTitle !== want.ogTitle || st.ogUrl !== want.ogUrl || st.ogLocale !== want.ogLocale) fail(`browser ${l}: the head changed under the script: ${JSON.stringify([st.title, st.ogTitle, st.ogUrl, st.ogLocale])}`);
        if (st.canonical.length !== 1 || st.canonical[0] !== want.canonical) fail(`browser ${l}: canonical links ${JSON.stringify(st.canonical)}`);
        if (st.ogImage !== want.ogImage) fail(`browser ${l}: og:image is ${st.ogImage}`);
        // the language switch of the live page: to every other language and back
        for (const to of LANGS.filter((x) => x !== l)) {
          const clicked = await page.eval(`(() => { const b = document.querySelector('#langSeg button[lang="${to}"]'); if (!b) return false; b.click(); return true; })()`);
          if (!clicked) { fail(`browser ${l} -> ${to}: no language button for ${to}`); continue; }
          let after = null;
          for (let i = 0; i < 100; i++) {
            await sleep(100);
            after = JSON.parse(await page.eval(probe));
            if (after.lang === to && after.title === metas[to].title) break;
          }
          const w = expected(to);
          if (after.lang !== to || after.title !== w.title || after.ogTitle !== w.ogTitle || after.ogUrl !== w.ogUrl || after.ogLocale !== w.ogLocale || after.canonical.length !== 1 || after.canonical[0] !== w.canonical) {
            fail(`browser ${l} -> ${to}: the head after the switch is ${JSON.stringify([after.lang, after.title, after.ogUrl, after.ogLocale, after.canonical])}`);
          }
        }
        await page.close();
      }
    } finally {
      await chrome.close();
    }
  }
} finally {
  await site.close();
}

if (problems.length) {
  console.error(`language heads check FAILED (${problems.length}):\n  ${problems.slice(0, 40).join('\n  ')}${problems.length > 40 ? `\n  ... and ${problems.length - 40} more` : ''}`);
  process.exit(1);
}
console.log(`language heads check ok: ${LINKS.length} links answered 200 at once with their edition's head (${LANGS.length} editions, no dist/index.html, ${rewrites.length} rewrites), share pictures 1200x630 under ${CARD_MAX / 1000} kB, /try has its share tags${args.includes('--browser') ? ', the page boots and switches language in Chrome with its head intact' : ''}`);
