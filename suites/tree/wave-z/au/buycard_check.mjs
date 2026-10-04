// The /try buy card rendered to HTML (react-dom/server through Vite's module runner) with ordering open, per market
// and language: which checkbox text and which line under it a customer sees. Prints JSON for test_au.py.
// Run with the repo as the working directory: node <this file>
import { createRequire } from 'node:module';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const req = createRequire(join(process.cwd(), 'package.json'));
const { runnerImport } = await import(pathToFileURL(req.resolve('vite')).href);
const opt = { configFile: false, logLevel: 'silent' };

const store = new Map();
function fakeWindow(search) {
  globalThis.window = {
    location: { search, href: `https://snapeyes.com/try${search}` },
    localStorage: { getItem: (k) => (store.has(k) ? store.get(k) : null), setItem: (k, v) => store.set(k, String(v)), removeItem: (k) => store.delete(k) },
    sessionStorage: { getItem: () => null, setItem() {}, removeItem() {} },
    history: { replaceState() {} },
    addEventListener() {}, removeEventListener() {},
  };

}

const ENTRY = pathToFileURL(join(process.argv[2], 'buycard_entry.ts')).pathname.replace(/^\/([A-Za-z]:)/, '$1');
const out = {};
const eye = { id: 'e1', before: '', image: '', thumb: '', pad: 1.1, fallback: false, usedSr: false, stored: true, glarePct: 0, sample: false, colourOff: false };
for (const [name, search, lang] of [['au_en', '?m=au&lang=en', 'en'], ['au_de', '?m=au&lang=de', 'de'], ['eu_en', '?m=eu&lang=en', 'en'], ['lt_de', '?m=lt&lang=de', 'de']]) {
  store.clear();
  fakeWindow(search);
  // a fresh module graph per market: the page's market is detected once per page load
  const R = req('react');
  const S = req('react-dom/server');
  const { module: B } = await runnerImport(ENTRY, opt);
  B.setCopyLang(lang);
  const server = {
    en: 'SERVER EU EN', de: 'SERVER EU DE',
    markets: { au: { en: 'SERVER AU EN', de: 'SERVER AU DE' } },
  };
  const props = {
    eyes: [eye], style: 'studio_black', styleName: 'Studio Black', ordering: { open: true, consent: server }, preview: 'ready',
    stale: [], onRetake() {}, waiver: false, onWaiver() {}, busy: false, step: null, error: null, onBuy() {},
  };
  const html = S.renderToStaticMarkup(R.createElement(B.BuyCard, props));
  const noServer = S.renderToStaticMarkup(R.createElement(B.BuyCard, { ...props, ordering: { open: true } }));
  out[name] = { html, noServer };
}
console.log(JSON.stringify(out));
