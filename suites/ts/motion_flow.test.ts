// I3: the motion of /try and /order (src/motion/flow.css, flow.ts, flowLogic.ts, Tick.tsx, EyeRing.tsx, ArtImage.tsx, CaptureDiagram.tsx, src/try/Working.tsx).
// What can be decided without a browser: the decisions (a file that became ready while the visit was open, the card that is on screen, the sweep), the markup of the
// pieces (the waiting arc, the drawn check, the rings, the diagram, the screens), and the contract of the stylesheet read as text (nothing moves outside
// prefers-reduced-motion: no-preference, the resting look is the finished look, no blur, no filter, no glow above .28, one source for the tokens). The browser half is
// scripts/check_motion_flow.mjs (reduced motion, the failsafe, the aperture frame by frame, nothing looping that should not).
// Loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results, prints nothing.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { SWEEP, cardOf, hasSwept, intoReady, markSwept, moved, sweepAt } from '../../src/motion/flowLogic';
import { Arc, Dot, Tick, Waiting } from '../../src/motion/Tick';
import { EyeRing } from '../../src/motion/EyeRing';
import { ArtImage } from '../../src/motion/ArtImage';
import { CaptureDiagram } from '../../src/motion/CaptureDiagram';
import { Working } from '../../src/try/Working';
import { setCopyLang } from '../../src/try/copy';

type R = Array<[string, boolean, string?]>;

const read = (p: string) => readFileSync(join(process.cwd(), p), 'utf8').replace(/\r\n/g, '\n');
const stripCss = (s: string) => s.replace(/\/\*[\s\S]*?\*\//g, '');

/** The at-rules a declaration sits inside, for every `property: value` of a stylesheet: [property, value, [at-rule preludes], selector]. */
function declarations(css: string): Array<{ prop: string; value: string; at: string[]; sel: string }> {
  const out: Array<{ prop: string; value: string; at: string[]; sel: string }> = [];
  const stack: Array<{ head: string; at: boolean }> = [];
  let buf = '';
  for (const ch of stripCss(css)) {
    if (ch === '{') { stack.push({ head: buf.trim(), at: buf.trim().startsWith('@') }); buf = ''; }
    else if (ch === '}') {
      for (const d of buf.split(';')) {
        const m = /^\s*([a-z-]+|--[\w-]+)\s*:\s*([\s\S]+?)\s*$/.exec(d);
        if (m) out.push({ prop: m[1], value: m[2], at: stack.filter((s) => s.at).map((s) => s.head), sel: stack.filter((s) => !s.at).map((s) => s.head).join(' ') });
      }
      buf = ''; stack.pop();
    } else buf += ch;
  }
  return out;
}

/** The expo curve of the page, cubic-bezier(.16, 1, .3, 1), evaluated (Newton on x, then y): the sweep of the slider must follow it. */
function bezier(t: number): number {
  const [x1, y1, x2, y2] = [0.16, 1, 0.3, 1];
  const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx, cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
  let s = t;
  for (let i = 0; i < 8; i++) { const x = ((ax * s + bx) * s + cx) * s - t; const d = (3 * ax * s + 2 * bx) * s + cx; if (Math.abs(x) < 1e-7 || !d) break; s -= x / d; }
  return ((ay * s + by) * s + cy) * s;
}

export async function run(): Promise<R> {
  const out: R = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);
  const html = (el: Parameters<typeof renderToStaticMarkup>[0]) => renderToStaticMarkup(el);

  // ---- /order: which card is on screen, and whether a file became ready while the visit was open
  check('the file becomes ready while the visit is open: only from a state this visit has seen (not on the first load, not from a state that is not an order state)',
    (['unpaid', 'pending', 'paid', 'making', 'review'] as const).every((s) => intoReady(s, 'ready'))
    && !intoReady(undefined, 'ready') && !intoReady(null, 'ready') && !intoReady('ready', 'ready') && !intoReady('withdrawn', 'ready') && !intoReady('making', 'review') && !intoReady('making', 'making'));
  check('a card is named by what it shows: paid and making are one card, a stop wins over the state, no status yet is the loading card',
    cardOf('paid', null) === 'making' && cardOf('making', null) === 'making' && cardOf('ready', null) === 'ready' && cardOf(undefined, null) === 'load' && cardOf('making', 'network') === 'stop:network' && cardOf(null, 'bad_link') === 'stop:bad_link');
  check('the first card replacing the loading card is the page arriving, not a move; a card replacing another is',
    !moved('load', 'pending') && !moved('load', 'ready') && !moved('making', 'making') && moved('making', 'ready') && moved('pending', 'making') && moved('making', 'stop:network') && moved('stop:network', 'making'));

  // ---- /try: the one sweep of the plain slider
  const pts = [0, 100, 250, 500, 750, 1000, 1500].map(sweepAt);
  check('the slider sweeps from 92 to 50 percent in a second and stays at 50 after it', pts[0] === SWEEP.from && SWEEP.from === 92 && pts[5] === 50 && pts[6] === 50 && SWEEP.to === 50 && SWEEP.delayMs === 400 && SWEEP.durationMs === 1000, pts.join());
  check('the sweep never moves backwards, never leaves 50 to 92', pts.every((v, i) => v >= 50 && v <= 92 && (i === 0 || v <= pts[i - 1])));
  const worst = Math.max(...Array.from({ length: 41 }, (_, i) => { const t = i / 40; return Math.abs(sweepAt(t * SWEEP.durationMs) - (SWEEP.from + (SWEEP.to - SWEEP.from) * bezier(t))); }));
  check('the sweep follows the expo curve of the page (cubic-bezier .16 1 .3 1) to within 3 percent of the frame', worst < 3, worst.toFixed(2));
  check('an eye that has swept never sweeps again in this tab (the slider is keyed by the eye and remounts when the customer comes back to it)',
    !hasSwept('e-motion-1') && (markSwept('e-motion-1'), hasSwept('e-motion-1')) && !hasSwept('e-motion-2'));

  // ---- the pieces
  const tick = html(createElement(Tick));
  check('the drawn check has pathLength 1 on its path (lucide\'s Check has none: a dash of 1 would draw dots), is hidden from assistive technology and has no label of its own',
    /<path d="M3 8.5 6.5 12 13 4.5" pathLength="1"/.test(tick) && tick.includes('aria-hidden="true"') && tick.includes('class="wk-tick"') && !tick.includes('aria-label') && html(createElement(Tick, { still: true })).includes('wk-still'));
  const arc = html(createElement(Arc));
  check('the arc is a circle of pathLength 100 inside a 172 box (stroke-dasharray 22 78 is then exactly 22 percent of the ring), decorative',
    arc.includes('viewBox="0 0 172 172"') && arc.includes('pathLength="100"') && arc.includes('r="85"') && arc.includes('class="wk-arc"') && arc.includes('aria-hidden="true"'));
  check('the dot and the small waiting ring are decorative and carry no text', html(createElement(Dot)) === '<span aria-hidden="true" class="fx-dot"></span>' && html(createElement(Waiting)).includes('wk-mini') && !/>[^<]+</.test(html(createElement(Waiting))));
  const ring = (made: boolean, busy: boolean) => html(createElement(EyeRing, { made, busy, thumb: '/t.jpg' }));
  check('an eye that waits has a dim still ring (no arc, no tick); the one being made has the arc; a made one has its ring closed in the page\'s success class and a check that is not drawn again',
    (() => { const w = ring(false, false), b = ring(false, true), m = ring(true, false); return w.includes('wk-waits') && !w.includes('wk-arc') && !w.includes('class="on"') && b.includes('wk-arc') && !b.includes('wk-waits') && m.includes('class="on"') && m.includes('wk-badge') && m.includes('wk-still') && !m.includes('wk-arc') && !m.includes('fx-fresh'); })());
  const diagram = html(createElement(CaptureDiagram));
  const nbsp = String.fromCharCode(0xa0);
  check('the capture diagram: decorative, four things draw in (seven strokes), one dashed line under a mask, and the only text is "10 cm" with a no-break space',
    diagram.includes('aria-hidden="true"') && (diagram.match(/class="[^"]*\bdr\b/g) ?? []).length === 7 && diagram.includes('<mask') && diagram.includes('stroke-dasharray="3 4"')
    && (diagram.match(/<text[^>]*>[^<]*<\/text>/g) ?? []).length === 1 && diagram.includes(`10${nbsp}cm</text>`));
  const art = html(createElement(ArtImage, { src: 'data:image/jpeg;base64,AAAA', alt: 'Your artwork' }));
  const arriving = html(createElement(ArtImage, { src: 'data:image/jpeg;base64,AAAA', alt: 'Your artwork', arrive: true }));
  check('a picture that was there at the start is in the first render, untouched; an arriving one is put in only after it has decoded (never a flash of the whole picture before its opening)',
    art.includes('<img') && art.includes('alt="Your artwork"') && !art.includes('fx-open') && arriving === '');

  // ---- the waiting screen
  setCopyLang('en');
  const wk = (p: Record<string, unknown>) => html(createElement(Working, { title: 'Restoring your iris…', lines: ['Cutting out your iris', 'Removing reflections', 'Studio macro restoration'], elapsed: 7, ...p } as never));
  const w3 = wk({ image: 'data:image/jpeg;base64,AAAA', enter: true });
  check('processing: the customer\'s own crop stays still inside the disc, the arc is the only moving thing, no percentage, no bar, no spinner and no utility animation',
    w3.includes('class="crop"') && w3.includes('wk-arc') && !/animate-|role="progressbar"|%/.test(w3) && !w3.includes('fx-edge') && w3.includes('fx-step'));
  check('processing: the real steps are a list that is announced as it grows; every line but the one in hand has its drawn check, the one in hand a still dot, the seconds are the real seconds',
    w3.includes('<ul aria-live="polite"') && (w3.match(/wk-tick/g) ?? []).length === 2 && (w3.match(/fx-dot/g) ?? []).length === 1 && w3.includes('>7s<') && !w3.includes('role="status"'));
  check('analysing, before any answer: nothing shows a check for a step that is not done (two steps in hand: two dots), and without a photo yet one thin ring carries the arc',
    (() => { const a = wk({ lines: ['Locating the iris and pupil', 'Measuring size and sharpness'], active: 2 }); return !a.includes('wk-tick') && (a.match(/fx-dot/g) ?? []).length === 2 && a.includes('wk-bare') && !a.includes('class="crop"') && !a.includes('fx-step'); })());
  check('two steps with the same words are two steps (the lines are keyed by place, not by their text)', (() => { const a = wk({ lines: ['Composing', 'Composing', 'Composing'] }); return (a.match(/<li /g) ?? []).length === 3 && (a.match(/wk-tick/g) ?? []).length === 2; })());

  // ---- the stylesheet, read as text
  const flow = read('src/motion/flow.css');
  const tokens = read('src/motion/tokens.css');
  const landing = read('src/motion/motion.css');
  const decl = declarations(flow);
  const NO_PREF = '@media (prefers-reduced-motion: no-preference)';
  const moving = decl.filter((d) => /^(animation|animation-name|animation-delay|transition|transition-duration|transition-property|transition-timing-function)$/.test(d.prop) && !/^(0s|none)$/.test(d.value));
  check('every rule that animates or transitions sits inside prefers-reduced-motion: no-preference (the resting look is the finished look), except the clamp that switches animation off',
    moving.length > 15 && moving.every((d) => d.at.includes(NO_PREF) || (d.at.some((a) => a.includes('reduce')) && /^(none|\.01ms)/.test(d.value)) || d.prop === 'transition-property'),
    moving.filter((d) => !d.at.includes(NO_PREF)).map((d) => `${d.sel} ${d.prop}`).join('; '));
  check('the clamp under reduced motion switches animation off for the page, its pseudo elements included, and ends transitions at once',
    /prefers-reduced-motion: reduce\)\s*\{[^}]*\*::after[^}]*animation: none !important;[^}]*transition-duration: \.01ms !important/.test(stripCss(flow)));
  const frames = [...stripCss(flow).matchAll(/@keyframes\s+([\w-]+)\s*\{((?:[^{}]|\{[^{}]*\})*)\}/g)];
  const ends = (f: RegExpMatchArray) => /\bto\b|100%/.test(f[2]);
  const from = frames.filter((f) => !ends(f)).map((f) => f[1]).sort().join();
  const explicit = frames.filter(ends).map((f) => f[1]).sort().join();
  check('every keyframes of the flow is named fx- or wk-; the ones that end where the element rests have a from only (the element\'s own style is the end: the resting look is the finished look), the six that run to somewhere are the sweep, the turn, the opening, the border\'s warmth and the pass',
    frames.every((f) => /^(fx|wk)-/.test(f[1])) && from === 'fx-draw,fx-fade,fx-pop,fx-rise,fx-scalex,fx-settle,fx-up' && explicit === 'fx-open,fx-pass,fx-sweep,fx-warm,wk-rot', `from: ${from}; explicit: ${explicit}`);
  const gradients: string[] = [];
  for (const m of stripCss(flow).matchAll(/[a-z-]*gradient\(/g)) {
    let depth = 0, i = (m.index ?? 0) + m[0].length - 1;
    const start = m.index ?? 0;
    for (; i < stripCss(flow).length; i++) { const c = stripCss(flow)[i]; if (c === '(') depth++; if (c === ')' && --depth === 0) break; }
    gradients.push(stripCss(flow).slice(start, i + 1));
  }
  check('no blur, no filter, no text shadow, no backdrop, and the only gradients are the two hairlines of gold (the one that sweeps along a frame, the one that passes once around a button) and the mask that cuts the second to 1 px (BR-4, AC-2)',
    !/blur\(|filter\s*:|backdrop|text-shadow|drop-shadow/.test(stripCss(flow)) && gradients.length === 6
    && gradients.every((g) => /^linear-gradient\(90deg, transparent, rgb\(245 197 66 \/ \.6\), transparent\)$/.test(g) || /^conic-gradient\(from var\(--fx-a\), transparent 0 68%, rgb\(245 197 66 \/ \.7\) 96%, transparent 100%\)$/.test(g) || g === 'linear-gradient(#000 0 0)'), gradients.join(' | '));
  check('the only shadow of the flow is a hairline of 1 px and a contact shadow (a negative spread): no halo',
    decl.filter((d) => d.prop === 'box-shadow').length >= 3 && decl.filter((d) => d.prop === 'box-shadow').every((d) => d.value.startsWith('0 0 0 1px') || /\s-\d+px\s+rgb/.test(d.value)));
  check('the aperture is a clip and nothing else: circle(0) to circle(75) at the centre, and it is never given a fill (it exists only while it runs), the frame\'s own border warms and returns',
    /@keyframes fx-open\s*\{\s*from\s*\{\s*clip-path: circle\(0% at 50% 50%\);\s*\}\s*to\s*\{\s*clip-path: circle\(75% at 50% 50%\);\s*\}\s*\}/.test(stripCss(flow))
    && decl.filter((d) => d.prop === 'animation' && /fx-open/.test(d.value)).every((d) => !/\b(forwards|both)\b/.test(d.value)) && /@keyframes fx-warm\s*\{\s*0%, 100%/.test(stripCss(flow)));
  const used = new Set([...stripCss(flow).matchAll(/var\((--[\w-]+)(?:,[^)]*)?\)/g)].map((m) => m[1]));
  const have = new Set([...tokens.matchAll(/(--[\w-]+)\s*:/g)].map((m) => m[1]));
  const local = new Set(['--i', '--sw', '--fx-a', '--gold-primary']);
  check('every custom property the flow reads is a token of src/motion/tokens.css (the landing\'s own) or a local one (--i, --sw, --fx-a, the page\'s --gold-primary)', [...used].every((u) => have.has(u) || local.has(u)), [...used].filter((u) => !have.has(u) && !local.has(u)).join());
  const landingProps = new Set([...stripCss(landing).matchAll(/(--[\w-]+)\s*:/g)].map((m) => m[1]));
  check('the tokens have one source: tokens.css is imported by motion.css and by flow.css, and motion.css defines none of them again',
    /@import '\.\/tokens\.css'/.test(landing) && /@import '\.\/tokens\.css'/.test(flow) && [...have].every((t) => !landingProps.has(t)) && /body\.lp\)?,\s*:root:has\(> body\.fx\)/.test(tokens), [...have].filter((t) => landingProps.has(t)).join());

  // ---- the wiring
  const tryMain = read('src/try/main.tsx'), orderMain = read('src/order/main.tsx'), landingMain = read('src/main.tsx');
  check('/try and /order load the flow stylesheet and pause their loops in a hidden tab; the landing loads neither (the tools\' motion code is loaded only where it is used)',
    [tryMain, orderMain].every((m) => m.includes("'../motion/flow.css'") && m.includes('watchAway()')) && !/flow/.test(landingMain) && !/motion\/(flow|Tick|ArtImage|EyeRing|CaptureDiagram)/.test(read('src/landing/Hero.tsx')));
  check('the bodies of try.html and order.html carry the class fx (the tokens need it) and keep the head script that skips the page transition for an order, a payment or the withdrawal form',
    ['try.html', 'order.html'].every((f) => { const h = read(f); return /<body class="fx /.test(h) && h.includes('skipTransition') && h.includes('(o|k|s|checkout|session_id|withdraw)='); }));
  check('motion.ts, the landing\'s engine, is not imported by the tools (a module both the landing and the tools import becomes a shared chunk the landing must fetch)',
    !/from '\.\.?\/(\.\.\/)?motion\/motion'|from '\.\/motion'/.test(['src/motion/flow.ts', 'src/motion/ArtImage.tsx', 'src/motion/Tick.tsx', 'src/motion/EyeRing.tsx', 'src/try/CompareSlider.tsx', 'src/try/ResultView.tsx', 'src/try/TryApp.tsx', 'src/order/OrderApp.tsx'].map(read).join('\n')));
  const files = ['src/motion/flow.css', 'src/motion/tokens.css', 'src/motion/flow.ts', 'src/motion/flowLogic.ts', 'src/motion/Tick.tsx', 'src/motion/EyeRing.tsx', 'src/motion/ArtImage.tsx', 'src/motion/CaptureDiagram.tsx', 'src/try/Working.tsx'];
  const bad = String.fromCharCode(0x2013, 0x2014, 0x2012, 0x2015, 0x200b, 0x202f, 0xa0, 0xfeff);
  check('no dash, no zero width and no raw no-break space in the new files (the no-break space is written as an escape)', files.every((f) => ![...read(f)].some((c) => bad.includes(c))), files.filter((f) => [...read(f)].some((c) => bad.includes(c))).join());
  return out;
}
