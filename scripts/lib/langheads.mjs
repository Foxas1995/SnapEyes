// The language editions of the landing page's HTML, made at build time (vite.config.ts langPages plugin) and read by the checks.
//
// WHY: a crawler (Facebook, WhatsApp, LinkedIn, iMessage, Slack) does not run the page's script, so it reads the share tags of the
// HTML it is sent. index.html used to be one file for /, /?lang=de, /?lang=lt and /?lang=hu (and now /?lang=hr): every share card said English, with
// the English picture and og:url / canonical of the root, and the page's own script (src/landing/lang.tsx applyLandingHead)
// corrected the head only for visitors who run it. Now the build writes one file per language, each with its own title,
// description, og:*, twitter:*, og:locale, og:url, canonical and share picture, and vercel.json rewrites the language links to the
// right file, so a crawler and a browser are given the same head, without any script.
//
// WHERE THE FILES ARE: dist/lp/en.html, de.html, lt.html, hu.html and hr.html (served at /lp/en and so on, the clean URLs of Vercel's
// cleanUrls). There is NO dist/index.html: Vercel checks the file system BEFORE the rewrites of vercel.json (verified with the CLI's
// own build output, .vercel/output/config.json: the routes of the rewrites come after {"handle": "filesystem"}), so an index.html
// would answer / by itself and no rewrite for / could ever fire. A rewrite's destination is the clean path with no ".html" (the
// cleanUrls routes redirect any path that ends in .html with a 308 and the file is registered under its clean path).
//
// The texts come from where the page takes them at run time: src/landing/copy/<lang>.json meta (title, description, share
// description, og:locale), src/shared/lang.ts for the locales and the address of each language (English at /, the others at
// ?lang=), and src/landing/shell/share.json for the alt text of the share picture. The pictures are made by scripts/make_og_cards.py.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

export const SITE_ORIGIN = 'https://snapeyes.com';
export const LANDING_DIR = 'lp';
export const LANG_ORDER = ['en', 'de', 'lt', 'hu', 'hr'];

/** The file of a language's edition inside dist (and the path of the page's copy of it in the repository's own build). */
export const landingFile = (lang) => `${LANDING_DIR}/${lang}.html`;
/** The path a rewrite of vercel.json sends the language to: the clean URL of the file, no ".html". */
export const landingRoute = (lang) => `/${LANDING_DIR}/${lang}`;
/** The share picture of a language: the English card is the founder's own (made by hand), the others are made from it (scripts/make_og_cards.py). */
export const ogImagePath = (lang) => (lang === 'en' ? '/assets/atelier/og-founder-eye.jpg' : `/assets/atelier/og-founder-eye-${lang}.jpg`);

export const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

/** What a language's head says, from the files the page itself reads. lang: the table of src/shared/lang.ts (LOCALES, LANGS, langQuery). */
export function headData(root, lang, l) {
  const read = (p) => JSON.parse(readFileSync(join(root, p), 'utf8').replace(/^﻿/, ''));
  const meta = read(`src/landing/copy/${l}.json`).meta;
  const share = read('src/landing/shell/share.json');
  if (!meta || !share[l]?.alt) throw new Error(`share head of ${l}: the copy's meta or share.json's alt is missing`);
  return {
    lang: l,
    title: meta.title,
    description: meta.description,
    shareDescription: meta.shareDescription,
    locale: lang.LOCALES[l].og,
    alternates: lang.LANGS.filter((x) => x !== l).map((x) => lang.LOCALES[x].og),
    url: `${SITE_ORIGIN}/${lang.langQuery(l)}`,
    image: `${SITE_ORIGIN}${ogImagePath(l)}`,
    alt: share[l].alt,
  };
}

// every rule: [what it finds in the page, what it is replaced with]; a rule that finds nothing stops the build, so a change of the
// head in index.html cannot quietly leave a language with the English tag
const tag = (attr, key) => new RegExp(`(<meta ${attr}="${key.replace(/[.:]/g, '\\$&')}" content=")[^"]*(" ?\\/?>)`);

/** The final index.html of the build as the edition of one language. */
export function editionOf(html, d) {
  const swap = (re, to, what) => {
    if (!re.test(html)) throw new Error(`langheads: ${what} not found in the page's head (${d.lang})`);
    html = html.replace(re, to);
  };
  swap(/<html lang="[a-z]{2}"/, `<html lang="${d.lang}"`, '<html lang>');
  swap(/<title>[\s\S]*?<\/title>/, () => `<title>${esc(d.title)}</title>`, '<title>');
  const set = (attr, key, value) => swap(tag(attr, key), (_, a, b) => `${a}${esc(value)}${b}`, `${key}`);
  set('name', 'description', d.description);
  set('property', 'og:url', d.url);
  set('property', 'og:locale', d.locale);
  set('property', 'og:title', d.title);
  set('property', 'og:description', d.shareDescription);
  set('property', 'og:image', d.image);
  set('property', 'og:image:alt', d.alt);
  set('name', 'twitter:title', d.title);
  set('name', 'twitter:description', d.shareDescription);
  set('name', 'twitter:image', d.image);
  // the other languages' og:locale values: the block after og:locale is rewritten as a whole
  const alt = /(?:[ \t]*<meta property="og:locale:alternate" content="[^"]*" ?\/?>\r?\n)+/;
  swap(alt, () => d.alternates.map((v) => `    <meta property="og:locale:alternate" content="${esc(v)}" />\n`).join(''), 'og:locale:alternate');
  // one rel=canonical, the page's own address (src/landing/lang.tsx keeps it in step once the script runs); put in front of the language alternates
  if (/<link rel="canonical"/.test(html)) throw new Error('langheads: the source page already has a canonical (the build writes it)');
  swap(/(\s*)<link rel="alternate" hreflang="en"/, (_, ws) => `${ws}<link rel="canonical" href="${esc(d.url)}" />${ws}<link rel="alternate" hreflang="en"`, 'the hreflang block');
  return html;
}

/** The tags of a built edition, read back from its HTML (what a crawler reads): used by the check and by the verification script. */
export function readHead(html) {
  const one = (re) => { const m = re.exec(html); return m ? m[1].replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&') : null; };
  const meta = (attr, key) => one(new RegExp(`<meta ${attr}="${key.replace(/[.:]/g, '\\$&')}" content="([^"]*)"`));
  return {
    htmlLang: one(/<html lang="([^"]*)"/),
    title: one(/<title>([\s\S]*?)<\/title>/),
    description: meta('name', 'description'),
    canonical: one(/<link rel="canonical" href="([^"]*)"/),
    canonicals: (html.match(/<link rel="canonical"/g) || []).length,
    hreflang: Object.fromEntries([...html.matchAll(/<link rel="alternate" hreflang="([^"]+)" href="([^"]*)"/g)].map((m) => [m[1], m[2]])),
    ogUrl: meta('property', 'og:url'),
    ogLocale: meta('property', 'og:locale'),
    ogLocaleAlt: [...html.matchAll(/<meta property="og:locale:alternate" content="([^"]*)"/g)].map((m) => m[1]),
    ogTitle: meta('property', 'og:title'),
    ogDescription: meta('property', 'og:description'),
    ogImage: meta('property', 'og:image'),
    ogImageAlt: meta('property', 'og:image:alt'),
    ogImageWidth: meta('property', 'og:image:width'),
    ogImageHeight: meta('property', 'og:image:height'),
    ogType: meta('property', 'og:type'),
    ogSiteName: meta('property', 'og:site_name'),
    twitterCard: meta('name', 'twitter:card'),
    twitterTitle: meta('name', 'twitter:title'),
    twitterDescription: meta('name', 'twitter:description'),
    twitterImage: meta('name', 'twitter:image'),
  };
}
