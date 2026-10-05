// The taste gate (motion spec 5.7): the patterns that make a quiet, expensive page look like a template, found in the source.
//   npm run check:taste              report mode: prints every hit and exits 0
//   node scripts/check_taste.mjs --strict    exits 1 when there is a hit outside the allowlist
// It reads src/**/*.ts, tsx and css except src/admin (the owner's panel keeps its own look), strips comments (the rules are quoted in comments),
// and matches whole class tokens ("animate-pulse" does not fire on "animate-pulse-slow"). The allowlist names FILES, with a reason, in this file:
// an effect that really needs an exception goes in there in the same commit that adds it. Report mode exists because the gate cannot pass on
// today's code (the debt is in /try, /order and src/index.css, which the next phase migrates): the last commit of that phase flips it to --strict.
//
// What it refuses: animate-pulse, animate-spin, animate-bounce, animate-ping (loops: BR-3); text-shadow and gradient text (BR-4: no neon);
// filter blur (AC-2, and a blur on the page's own surfaces costs frames); font-black (the display type is 500 and 600); a gold gradient fill
// on a button (one flat pill); backdrop blur outside the two fixed bars, which are the page's only blurred surfaces; a gold glow above .28 alpha.
import { readdirSync, readFileSync } from 'node:fs';
import { join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const strict = process.argv.includes('--strict');

/** file (relative to the root, forward slashes) -> why it may carry a blurred surface */
const ALLOW_BLUR = {
  'src/landing/css/header.css': 'the fixed header: one of the two blurred surfaces, static, 64 px high',
  'src/landing/css/sticky.css': 'the sticky phone bar: the other blurred surface, static',
  'src/landing/css/base.css': 'the "AI visualisation" chip over a picture: a known debt (charter AC-2 wants a solid chip), still blurred 6 px; decide with the owner',
  'src/landing/css/hero.css': 'the in-frame chip of the first screen, the same debt as base.css',
};

function* walk(dir) {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, e.name);
    if (e.isDirectory()) {
      if (relative(ROOT, p).split('\\').join('/') === 'src/admin') continue;
      yield* walk(p);
    } else if (/\.(ts|tsx|css)$/.test(e.name)) yield p;
  }
}

/** The source without its comments: block comments everywhere, line comments in ts and tsx (not the // of a URL). Line numbers are kept. */
function strip(text, css) {
  let out = text.replace(/\/\*[\s\S]*?\*\//g, (m) => m.replace(/[^\n]/g, ' '));
  if (!css) out = out.replace(/(^|[^:'"`\\])\/\/[^\n]*/g, (m, a) => a + ' '.repeat(m.length - a.length));
  return out;
}

const TOKEN = (name) => new RegExp(`(?<![\\w-])${name}(?![\\w-])`);
const RULES = [
  ['animate-pulse', TOKEN('animate-pulse')],
  ['animate-spin', TOKEN('animate-spin')],
  ['animate-bounce', TOKEN('animate-bounce')],
  ['animate-ping', TOKEN('animate-ping')],
  ['text-shadow', /(?<![\w-])text-shadow\s*:/],
  ['filter blur', /(?<![-\w])filter\s*:[^;}\n]*blur\(/],
  ['text-gold-gradient', TOKEN('text-gold-gradient')],
  ['font-black', TOKEN('font-black')],
  ['gold gradient fill (bg-gradient-to-r with the gold hexes)', /bg-gradient-to-r[^"'`\n]*#(f5c542|d4af37)|#(f5c542|d4af37)[^"'`\n]*bg-gradient-to-r/i],
  ['backdrop blur', /backdrop-blur|backdrop-filter\s*:/],
];
const GOLD = /rgba?\(\s*245[\s,]+197[\s,]+66\s*(?:[,/]\s*([.\d]+))?\s*\)/g;

const hits = [];
for (const file of walk(join(ROOT, 'src'))) {
  const rel = relative(ROOT, file).split('\\').join('/');
  const css = rel.endsWith('.css');
  const lines = strip(readFileSync(file, 'utf8'), css).split('\n');
  lines.forEach((line, i) => {
    for (const [name, re] of RULES) {
      if (!re.test(line)) continue;
      if (name === 'backdrop blur' && ALLOW_BLUR[rel]) continue;
      hits.push({ rule: name, file: rel, line: i + 1, text: line.trim().slice(0, 110) });
    }
    // a gold glow: a shadow of the gold with a blur of 12 px or more, no negative spread, and an alpha above .28 (a contact shadow has a negative spread)
    if (/(box|drop)-shadow|shadow-\[/.test(line)) {
      for (const m of line.matchAll(GOLD)) {
        const alpha = m[1] === undefined ? 1 : parseFloat(m[1]);
        const before = line.slice(0, m.index);
        const nums = [...before.matchAll(/(-?[\d.]+)px/g)].map((x) => parseFloat(x[1])).slice(-4);
        const blur = nums.length >= 3 ? nums[nums.length - (nums.length === 4 ? 2 : 1)] : 0;
        const spread = nums.length === 4 ? nums[3] : 0;
        if (alpha > 0.28 && blur >= 12 && spread >= 0) hits.push({ rule: 'gold glow above .28', file: rel, line: i + 1, text: line.trim().slice(0, 110) });
      }
    }
  });
}

// a second @keyframes with the same name anywhere in the CSS: names are global, so the later chunk's definition silently replaces the keyframes of an
// animation that is already running (2026-10-05: lp-sweep in hero.css and wall.css made the hero glint a white slab for every visitor)
const seenFrames = new Map();
for (const file of walk(join(ROOT, 'src'))) {
  if (!file.endsWith('.css')) continue;
  const rel = relative(ROOT, file).split('\\').join('/');
  strip(readFileSync(file, 'utf8'), true).split('\n').forEach((line, i) => {
    for (const m of line.matchAll(/@keyframes\s+([\w-]+)/g)) {
      const first = seenFrames.get(m[1]);
      if (first) hits.push({ rule: 'duplicate @keyframes name', file: rel, line: i + 1, text: `${m[1]} is also defined in ${first}` });
      else seenFrames.set(m[1], `${rel}:${i + 1}`);
    }
  });
}

const byRule = new Map();
for (const h of hits) byRule.set(h.rule, (byRule.get(h.rule) ?? 0) + 1);
for (const h of hits) console.log(`${h.rule}: ${h.file}:${h.line}  ${h.text}`);
console.log(hits.length ? `\ntaste: ${hits.length} hit(s) in ${new Set(hits.map((h) => h.file)).size} file(s): ${[...byRule].map(([r, n]) => `${r} ${n}`).join(', ')}${strict ? '' : ' (report mode: not an error)'}` : '\ntaste ok: none of the patterns of motion spec 5.7');
process.exit(strict && hits.length ? 1 : 0);
