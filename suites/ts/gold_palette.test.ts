// The gold of the pages (2026-10-22, palette A: the owner chose the logo's metal for the page, "A metalic geriausiai atrodo tiek puslapiui tiek logo").
// One source, src/index.css: the root's tokens (--gold-primary, --gold-rgb, --gold-light, --gold-pale, the metal) and two copies that Tailwind needs as
// literals (@theme inline). What is checked here, without a browser: the copies agree with the root (the theme, the 404 page, the fallbacks of the pages'
// plain HTML), the contrasts stay at WCAG AA, every primary button wears the class gold-metal, and no visitor page's code writes the old gold any more
// (the logo's own lines excepted: another branch replaces them). The browser half: the colour pins of check:motion, check:motion:close, check:motion:sections,
// check:motion:flow and check:reveal read the new gold.
import { readdirSync, readFileSync, statSync } from 'node:fs';

type Row = [string, boolean, string?];
const read = (p: string) => readFileSync(p, 'utf8').replace(/\r\n/g, '\n');

/** The custom properties of the first rule that matches `selector` (a plain text search; enough for these files). */
function props(css: string, from: string): Record<string, string> {
  const at = css.indexOf(from);
  const body = css.slice(css.indexOf('{', at) + 1, css.indexOf('}', at));
  const out: Record<string, string> = {};
  for (const m of body.replace(/\/\*[\s\S]*?\*\//g, '').matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) out[m[1]] = m[2].trim();
  return out;
}
const rgbOf = (hex: string) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
const lum = (hex: string) => {
  const [r, g, b] = rgbOf(hex).map((c) => { const s = c / 255; return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4; });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const contrast = (a: string, b: string) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
const stops = (gradient: string) => [...gradient.matchAll(/#[0-9a-f]{6}/gi)].map((m) => m[0].toLowerCase());

function files(dir: string, acc: string[] = []): string[] {
  for (const n of readdirSync(dir)) {
    const p = `${dir}/${n}`;
    if (statSync(p).isDirectory()) { if (p !== 'src/admin') files(p, acc); }
    else if (/\.(tsx?|css|html|json)$/.test(n)) acc.push(p);
  }
  return acc;
}

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);
  const css = read('src/index.css');
  const root = props(css, '  :root {');
  const theme = props(css, '@theme inline');
  const gold = root['--gold-primary'];

  check('the utilities\' copies are the root\'s values (--color-gold is --gold-primary, --color-gold-light is --gold-light)',
    theme['--color-gold'] === gold && theme['--color-gold-light'] === root['--gold-light'], JSON.stringify({ theme, gold, light: root['--gold-light'] }));
  check('--gold-rgb is --gold-primary as a triplet (the translucent golds: rgb(var(--gold-rgb) / a))', root['--gold-rgb'] === rgbOf(gold).join(' '), `${root['--gold-rgb']} / ${gold}`);
  check('the palette is the one the owner chose (palette A: accent #c49a59, light #e0bc74, the metal from #f4e0a0 to #b98d50)',
    gold === '#c49a59' && root['--gold-light'] === '#e0bc74' && stops(root['--metal']).join() === '#f4e0a0,#e0bd77,#cba05d,#b98d50', JSON.stringify(root));

  const nf = read('src/notfound/notfound.html');
  const local = props(nf, ':root {');
  check('the 404 page (a page of its own, no stylesheet of the site) carries the same gold, metal and ink',
    local['--gold'] === gold && local['--gold-rgb'] === root['--gold-rgb'] && local['--metal'] === root['--metal'] && local['--metal-ink'] === root['--metal-ink'], JSON.stringify(local));
  const html = ['try.html', 'order.html', 'imprint.html', 'privacy.html', 'terms.html', 'withdrawal.html'];
  const fallbacks = html.flatMap((p) => [...read(p).matchAll(/var\(--gold-primary,\s*(#[0-9a-f]{6})\)/gi)].map((m) => [p, m[1].toLowerCase()]));
  check('the plain HTML of the pages (the email link without JavaScript, the message when the page cannot load) reads the token, its fallback the same gold',
    fallbacks.length === 12 && fallbacks.every(([, v]) => v === gold), JSON.stringify(fallbacks));

  const BG = '#07090e', CARD = '#0b0e17';
  const metal = ['--metal', '--metal-hi', '--metal-press', '--metal-knob'].flatMap((k) => stops(root[k]));
  const worst = Math.min(...metal.map((s) => contrast(root['--metal-ink'], s)));
  check('WCAG AA: the accent, the light and the pale gold are text of 4.5:1 or more on the page and on a card of /try', [gold, root['--gold-light'], root['--gold-pale']].every((c) => contrast(c, BG) >= 4.5 && contrast(c, CARD) >= 4.5),
    [gold, root['--gold-light'], root['--gold-pale']].map((c) => `${c} ${contrast(c, BG).toFixed(2)}`).join(', '));
  check('WCAG AA: the words on the metal are 4.5:1 or more on every stop of the button at rest, on hover, pressed and of the knob', worst >= 4.5, `lowest ${worst.toFixed(2)} on ${metal.length} stops`);

  const landing = readdirSync('src/landing').filter((n) => n.endsWith('.tsx')).map((n) => read(`src/landing/${n}`)).join('\n');
  const pills = [...landing.matchAll(/className="([^"]*\blp-btn-gold\b[^"]*)"/g)].map((m) => m[1]);
  const tools = ['src/try/TryApp.tsx', 'src/try/BuyCard.tsx', 'src/order/ui.tsx'].map(read).join('\n');
  const fx = [...tools.matchAll(/['"`](fx-gold\b[^'"`]*)['"`]/g)].map((m) => m[1]);
  check('every primary button wears the metal: the landing\'s gold pills and the gold buttons of /try and /order carry the class gold-metal',
    pills.length === 7 && pills.every((c) => /\bgold-metal\b/.test(c)) && fx.length === 3 && fx.every((c) => /\bgold-metal\b/.test(c)), JSON.stringify({ pills, fx }));

  const OLD = /#f5c542|#ffd666|#f7d77a|#d4af37|#b8860b|245[\s,]+197[\s,]+66/i;
  const LOGO = /<circle|SNAP<span|aria-label="SnapEyes"/;    // the logo's own lines: v3-logo replaces them
  const left = [...files('src'), ...html, 'index.html'].flatMap((p) => read(p).split('\n').map((l, i) => [p, i + 1, l] as const)).filter(([, , l]) => OLD.test(l) && !LOGO.test(l));
  check('no visitor page\'s code writes the old gold (#f5c542 and its family), the logo\'s own lines excepted', left.length === 0, left.map(([p, n]) => `${p}:${n}`).join(' '));
  return out;
}
