// The legal pages (/terms /privacy /imprint /withdrawal) must look and read exactly as before whatever happens to the
// landing page's CSS. This measures them in real Chrome and compares two builds:
//   node scripts/legal_look.mjs save <dist dir> <baseline.json> [--shots <folder>]     measure a build, write the baseline
//   node scripts/legal_look.mjs compare <dist dir> <baseline.json> [--shots <folder>]  measure a build, compare to a baseline
// Per page (4 documents x 4 languages x phone and desktop width, plus the Australian and Hungarian editions) it keeps
//   * the pixels: a hash of the full page screenshot,
//   * the layout: every element's box and a hash of ALL its computed styles (html and body included), and its text,
//   * the page's height and width.
// The baseline comes from the build BEFORE a change (git stash or another worktree), the comparison from the build after
// it. A difference names the first elements that moved or changed style. Also checked on every page of the build:
// none of the CSS files a legal, /try, /order or /admin page loads holds a landing rule (the prefix lp-, the layer
// "landing" with rules in it), so the landing CSS cannot reach them.
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { launch } from './lib/cdp.mjs';
import { serve } from './lib/static.mjs';

const DOCS = ['terms', 'privacy', 'imprint', 'withdrawal'];
const LANGS = ['en', 'de', 'lt', 'hu'];
const WIDTHS = [375, 1280];
const CASES = [];
for (const d of DOCS) for (const l of LANGS) for (const w of WIDTHS) CASES.push({ path: `/${d}?lang=${l}`, width: w });
for (const d of ['terms', 'withdrawal']) {
  CASES.push({ path: `/${d}?lang=en&m=au`, width: 1280 });
  CASES.push({ path: `/${d}?lang=hu&m=hu`, width: 1280 });
}

// Two Tailwind theme variables that the old landing's markup (backdrop-blur-xl, max-w-xl) made the build write into the root of every
// page, inherited by every element, and that nothing reads any more (checked below: no stylesheet of the build holds var(--blur-xl)
// or var(--container-xl)). They stay out of the style fingerprint, so deleting the old landing does not look like a change of the
// legal pages; the pixels, every box and every other property still have to be identical. The baseline must be taken with the same list.
const IGNORED_VARIABLES = ['--blur-xl', '--container-xl'];

// in the page: one record per element (tag, class, box, hash of every computed style, own text)
const COLLECT = `(() => {
  const SKIP = new Set(${JSON.stringify(IGNORED_VARIABLES)});
  const fnv = (s) => { let h = 0x811c9dc5; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193); } return (h >>> 0).toString(16); };
  const out = [];
  for (const el of document.querySelectorAll('html, body, body *')) {
    if (el.tagName === 'SCRIPT' || el.tagName === 'NOSCRIPT' || el.tagName === 'STYLE') continue;
    const cs = getComputedStyle(el);
    // custom properties come in no fixed order: sort by name
    const names = []; for (let i = 0; i < cs.length; i++) names.push(cs[i]); names.sort();
    let s = '';
    for (const n of names) if (!SKIP.has(n)) s += n + ':' + cs.getPropertyValue(n) + ';';
    const r = el.getBoundingClientRect();
    const own = Array.from(el.childNodes).filter((n) => n.nodeType === 3).map((n) => n.textContent).join('');
    out.push([el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (typeof el.className === 'string' && el.className ? '.' + el.className.trim().split(/\\s+/).slice(0, 3).join('.') : ''),
      [r.left, r.top + scrollY, r.width, r.height].map((v) => Math.round(v * 100) / 100), fnv(s), fnv(own), out.length < 6 ? s : undefined]);
  }
  return JSON.stringify({ h: document.documentElement.scrollHeight, w: document.documentElement.scrollWidth, title: document.title, els: out });
})()`;

const sha = (buf) => createHash('sha256').update(buf).digest('hex').slice(0, 16);

async function measure(dir, shotsDir) {
  const site = await serve(dir, { vercelFile: resolve(dir, '..', 'vercel.json') });
  const chrome = await launch();
  const result = {};
  try {
    for (const c of CASES) {
      const page = await chrome.page({ width: c.width, height: 900, mobile: c.width < 500, dpr: 1 });
      const origin = `http://127.0.0.1:${site.port}`;
      await page.goto(`${origin}/imprint?lang=en`);
      await page.loaded();
      await page.send('Storage.clearDataForOrigin', { origin, storageTypes: 'all' }).catch(() => undefined);
      await page.goto(`${origin}${c.path}`);
      await page.loaded();
      await page.eval('new Promise((r) => setTimeout(r, 500))');
      const rec = JSON.parse(await page.eval(COLLECT));
      const shots = await page.fullShots();
      const key = `${c.path} @${c.width}`;
      result[key] = { h: rec.h, w: rec.w, title: rec.title, n: rec.els.length, shot: sha(Buffer.concat(shots.map((b) => Buffer.from(sha(b))))), dom: sha(JSON.stringify(rec.els)), els: rec.els };
      if (shotsDir) {
        mkdirSync(shotsDir, { recursive: true });
        shots.forEach((b, i) => writeFileSync(join(shotsDir, `${c.path.replace(/[^a-z0-9]+/gi, '_')}_${c.width}_${i}.png`), b));
      }
      await page.close();
    }
  } finally {
    await chrome.close();
    await site.close();
  }
  return result;
}

// the CSS files each built page loads: <link rel=stylesheet> and the CSS of its modulepreload chunks' siblings
function cssLeaks(dir) {
  const problems = [];
  const rules = /\.lp-[a-z]|\.lp\b|@layer landing\s*\{\s*[^}\s]/;
  for (const f of readdirSync(dir).filter((n) => n.endsWith('.html'))) {
    if (f === 'index.html') continue;
    const html = readFileSync(join(dir, f), 'utf8');
    for (const m of html.matchAll(/<link[^>]+rel="stylesheet"[^>]*href="([^"]+)"/g)) {
      const css = readFileSync(join(dir, m[1].replace(/^\//, '')), 'utf8');
      if (rules.test(css)) problems.push(`${f}: the stylesheet ${m[1]} holds landing rules`);
    }
  }
  // the ignored variables are really unused: a build that reads one of them would hide a change
  const read = (d) => readdirSync(d, { withFileTypes: true }).flatMap((f) => (f.isDirectory() ? read(join(d, f.name)) : f.name.endsWith('.css') ? [readFileSync(join(d, f.name), 'utf8')] : []));
  for (const css of read(dir)) for (const v of IGNORED_VARIABLES) if (css.includes(`var(${v}`)) problems.push(`a stylesheet of the build reads ${v}, which the legal look check leaves out of its fingerprint: take it off IGNORED_VARIABLES`);
  return problems;
}

function diff(base, now) {
  const problems = [];
  for (const key of Object.keys(base)) {
    const a = base[key], b = now[key];
    if (!b) { problems.push(`${key}: not measured`); continue; }
    if (a.h !== b.h || a.w !== b.w) problems.push(`${key}: size ${a.w}x${a.h} became ${b.w}x${b.h}`);
    if (a.title !== b.title) problems.push(`${key}: title changed`);
    if (a.n !== b.n) problems.push(`${key}: ${a.n} elements became ${b.n}`);
    if (a.dom !== b.dom) {
      let shown = 0;
      for (let i = 0; i < Math.min(a.els.length, b.els.length) && shown < 4; i++) {
        const x = a.els[i], y = b.els[i];
        if (JSON.stringify(x.slice(0, 4)) !== JSON.stringify(y.slice(0, 4))) {
          shown++;
          let what = x[0] !== y[0] ? 'element' : JSON.stringify(x[1]) !== JSON.stringify(y[1]) ? `box ${x[1]} became ${y[1]}` : x[2] !== y[2] ? 'computed style' : 'text';
          if (what === 'computed style' && x[4] && y[4]) {
            const pa = Object.fromEntries(x[4].split(';').filter(Boolean).map((t) => [t.slice(0, t.indexOf(':')), t.slice(t.indexOf(':') + 1)]));
            const pb = Object.fromEntries(y[4].split(';').filter(Boolean).map((t) => [t.slice(0, t.indexOf(':')), t.slice(t.indexOf(':') + 1)]));
            const names = [...new Set([...Object.keys(pa), ...Object.keys(pb)])].filter((k) => pa[k] !== pb[k]);
            what = `computed style: ${names.slice(0, 6).map((k) => `${k} ${pa[k]} became ${pb[k]}`).join(', ')}`;
          }
          problems.push(`${key}: #${i} ${x[0]} differs (${what})`);
        }
      }
    }
    if (a.shot !== b.shot) problems.push(`${key}: the pixels differ`);
  }
  return problems;
}

const [mode, dirArg, file, ...rest] = process.argv.slice(2);
if (!['save', 'compare'].includes(mode) || !dirArg || !file) {
  console.error('usage: node scripts/legal_look.mjs save|compare <dist dir> <baseline.json> [--shots <folder>]');
  process.exit(2);
}
const dir = resolve(dirArg);
const shotsAt = rest.indexOf('--shots');
const shotsDir = shotsAt >= 0 ? resolve(rest[shotsAt + 1]) : null;
const now = await measure(dir, shotsDir);
const leaks = cssLeaks(dir);
if (mode === 'save') {
  writeFileSync(file, JSON.stringify(now));
  console.log(`legal look saved: ${Object.keys(now).length} pages, ${Object.values(now).reduce((s, p) => s + p.n, 0)} elements -> ${file}`);
  if (leaks.length) console.log(`note: ${leaks.join('; ')}`);
} else {
  const problems = [...leaks, ...diff(JSON.parse(readFileSync(file, 'utf8')), now)];
  if (problems.length) {
    console.error(`legal look CHANGED (${problems.length}):\n  ${problems.slice(0, Number(process.env.LEGAL_LOOK_SHOW) || 40).join('\n  ')}`);
    process.exit(1);
  }
  console.log(`legal look identical: ${Object.keys(now).length} pages (pixels, every element's box and computed styles, text), no landing rule in any legal, /try, /order or /admin stylesheet`);
}
