// The finish of the release (2026-10-06): the page-code half of what the four reviews found (the server half is scripts/styles_tests/test_release_fixes.py, the browser half
// scripts/check_motion_flow.mjs). What can be decided without a browser: the pages /try and /order fail open (a message with a way out when their script cannot load, a noscript
// on /try), the slider of the result is a slider for the keyboard, the words that were missing exist in four languages, the grey of the small helper texts reads on the dark
// page, forced colours keep the menu button and the gold buttons, focus and announcements are wired.
// Loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results, prints nothing.
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { CompareSlider } from '../../src/try/CompareSlider';
import { T, setCopyLang } from '../../src/try/copy';

type R = Array<[string, boolean, string?]>;

const read = (p: string) => readFileSync(join(process.cwd(), p), 'utf8').replace(/\r\n/g, '\n');
const files = (dir: string, acc: string[] = []): string[] => {
  for (const n of readdirSync(join(process.cwd(), dir))) {
    const rel = `${dir}/${n}`;
    if (statSync(join(process.cwd(), rel)).isDirectory()) files(rel, acc);
    else if (/\.(tsx?|css)$/.test(n)) acc.push(rel);
  }
  return acc;
};

export async function run(): Promise<R> {
  const out: R = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);

  // ---- /try and /order fail open (perf-a11y M2)
  const tryHtml = read('try.html'), orderHtml = read('order.html');
  const failsafe = (h: string) => /addEventListener\('error'[\s\S]*?t\.tagName === 'SCRIPT' && t\.type === 'module'[\s\S]*?\}, true\)/.test(h) && /setTimeout\(show, 10000\)/.test(h)
    && /role', 'alert'/.test(h) && /vite:preloadError/.test(h) && /snapeyes\.skewReload/.test(h) && h.indexOf('<script>\n      (function () {') < h.indexOf('<script type="module"');
  check('/try and /order carry the load failsafe BEFORE their module script: a failed module script or no render within 10 s writes a role=alert message with a reload button and the support address into #root, and a failed chunk reloads once a minute at most',
    failsafe(tryHtml) && failsafe(orderHtml), '');
  for (const [name, h] of [['try.html', tryHtml], ['order.html', orderHtml]] as const) {
    const words = /var words = \{([\s\S]*?)\};/.exec(h)?.[1] ?? '';
    check(`${name}: the failsafe has its words in English, German, Lithuanian and Hungarian, each with the sentence, the way out and the button`,
      (['en', 'de', 'lt', 'hu'] as const).every((l) => new RegExp(`${l}: \\['[^']{15,}', '[^']{15,}', '[^']{3,}'\\]`).test(words)), words.slice(0, 80));
  }
  check('/try has a noscript with the support address (it was blank without JavaScript); /order keeps its own',
    /<noscript>[\s\S]*mailto:info@snapeyes\.com[\s\S]*<\/noscript>/.test(tryHtml) && /<noscript>[\s\S]*mailto:info@snapeyes\.com[\s\S]*<\/noscript>/.test(orderHtml), '');
  check('/try says its colour scheme and theme colour like the other pages (its checkbox, file input and scrollbars use the dark scheme)', /<meta name="color-scheme" content="dark" \/>/.test(tryHtml) && /<meta name="theme-color" content="#07090e" \/>/.test(tryHtml), '');
  const bad = String.fromCharCode(0x2013, 0x2014, 0x2012, 0x2015);
  check('no dash in the two pages or in the failsafe words', [tryHtml, orderHtml].every((h) => ![...h].some((c) => bad.includes(c))), '');

  // ---- the slider of the result is a slider for the keyboard (M5)
  const slider = (lang: 'en' | 'de' | 'lt' | 'hu') => { setCopyLang(lang); return renderToStaticMarkup(createElement(CompareSlider, { before: 'data:,a', after: 'data:,b' })); };
  const en = slider('en');
  check('the frame of the before and after slider is role=slider, in the tab order, named, with a value from 0 to 100 and a spoken value ("photo 50 percent")',
    /role="slider"/.test(en) && /tabindex="0"/.test(en) && /aria-valuemin="0"/.test(en) && /aria-valuemax="100"/.test(en) && /aria-valuenow="50"/.test(en) && /aria-valuetext="photo 50 percent"/.test(en)
    && new RegExp(`aria-label="${T.result.sliderLabel}"`).test(slider('en')), en.slice(0, 300));
  const labels = (['en', 'de', 'lt', 'hu'] as const).map((l) => { const h = slider(l); return /aria-label="([^"]+)"/.exec(h)?.[1] ?? ''; });
  check('the slider is named in four languages, four different words', new Set(labels).size === 4 && labels.every((s) => s.length > 10), labels.join(' | '));
  const src = read('src/try/CompareSlider.tsx');
  check('the arrows move the cut by 5, the page keys by 10, Home and End to the ends, and a key ends the sweep like a touch; the focus ring is drawn on the frame',
    /ArrowLeft/.test(src) && /ArrowRight/.test(src) && /'PageDown' \? -10/.test(src) && /'PageUp' \? 10/.test(src) && /'Home' \? 0/.test(src) && /'End' \? 100/.test(src) && /stopSweep\.current\(\)/.test(src.split('const onKey')[1] ?? '')
    && /focus-visible:outline-\[#f5c542\]/.test(src), '');

  // ---- the words that were missing, in four languages (M3, M5, H-M1)
  const keys = ['sliderLabel', 'sliderValue', 'previewReady', 'aiMaterial'] as const;
  for (const key of keys) {
    const vals = (['en', 'de', 'lt', 'hu'] as const).map((l) => { setCopyLang(l); return String((T.result as Record<string, unknown>)[key] ?? ''); });
    check(`/try result.${key}: a sentence in each of the four languages, all different${key === 'sliderValue' ? ', each with the token {n}' : ''}`,
      new Set(vals).size === 4 && vals.every((v) => v.length > 8 && (key !== 'sliderValue' || v.includes('{n}'))), vals.map((v) => v.slice(0, 30)).join(' | '));
  }
  setCopyLang('en');

  // ---- focus, announcements, the error (M3), the tile name (minor 6)
  const app = read('src/try/TryApp.tsx');
  check('/try moves focus to the step\'s heading after every step change (all three h1 carry the ref and tabindex -1), announces the preview by a polite live region that is always mounted, and the error banner is role=alert',
    (app.match(/ref=\{stepHead\} tabIndex=\{-1\}/g) ?? []).length === 3 && /stepHead\.current\?\.focus\(\{ preventScroll: true \}\)/.test(app) && /<p role="status" data-testid="announce" className="sr-only">\{announce\}<\/p>/.test(app)
    && /<div role="alert" className="fx-note mb-4/.test(app) && /setAnnounce\(arriving \? T\.result\.previewReady : ''\)/.test(app) && /if \(stepped\)/.test(app), '');
  check('the style tile name wraps (no truncate): the names are cut by wider text spacing otherwise', /break-words leading-tight">\{t\.name\}/.test(read('src/try/StylePicker.tsx')) && !/min-w-0 truncate">\{t\.name\}/.test(read('src/try/StylePicker.tsx')), '');

  // ---- contrast (M4): the grey of the small helper texts of the tools reads on the dark page (zinc-400 is 7.5 to 7.8 : 1, zinc-500 is 4.0 : 1)
  const allowed: Record<string, number> = { 'src/try/BuyCard.tsx': 1, 'src/try/ResultView.tsx': 1 };       // both are DISABLED states (no contrast rule for an inactive control)
  const used: Record<string, number> = {};
  for (const dir of ['src/try', 'src/order', 'src/shared', 'src/motion', 'src/reveal']) for (const f of files(dir)) { const n = (read(f).match(/text-zinc-500/g) ?? []).length; if (n) used[f] = n; }
  check('no text-zinc-500 in the tools except the two disabled states (the photo notice, the quality helper lines, the order number, the tag and the file details were 4.0 : 1)',
    JSON.stringify(used) === JSON.stringify(allowed) && !/placeholder:text-zinc-600/.test(read('src/order/WithdrawPanel.tsx')), JSON.stringify(used));

  // ---- forced colours (M6)
  const header = read('src/landing/css/header.css'), flow = read('src/motion/flow.css');
  check('forced colours: the bars of the landing\'s menu button take CanvasText (a currentColor bar vanished on the canvas), a flat gold button of the tools gets a border and a pressed button an outline',
    /@media \(forced-colors: active\) \{\s*\.lp-menu-btn span, \.lp-menu-btn span::before, \.lp-menu-btn span::after \{ background: CanvasText; \}/.test(header)
    && /@media \(forced-colors: active\) \{\s*\.fx-gold \{ border: 1px solid ButtonText; \}\s*:root:has\(> body\.fx\) \[aria-pressed="true"\] \{ outline: 2px solid Highlight; outline-offset: -2px; \}/.test(flow), '');

  // ---- the order page shows the copy made for the screen (A-M1), the model words (P-M5) are in the error table of the languages' pages
  const order = read('src/order/OrderApp.tsx'), api = read('src/order/api.ts');
  check('the order page asks for the display copy: the Download type names display_url, display_width and display_height, and the ready card shows display_url when there is one',
    /display_url\?: string; display_width\?: number \| null; display_height\?: number \| null/.test(api) && /src=\{d\.display_url \?\? d\.url\}/.test(order), '');
  return out;
}
