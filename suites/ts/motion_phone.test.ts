// The page code of the scenes made for phones (the owner's request of 2026-10-17): what can be decided without a browser. The engine's helper for the phone (src/motion/phone.ts) run against
// a stand-in window; the two media queries that decide who gets the pinned scene (768 px and up, or the phone's), proved to partition the widths; the Reveal's script (the table of the cut, the
// aperture, the line, the ring, the chips and the steps, shared by the desktop scene and the phone's); and the stylesheets: every rule that styles a phone scene is inside the one phone
// condition and carries html.mo:not(.mo-fail), so that no phone rule can ever reach a desktop, a visitor who asked for reduced motion or a page whose engine gave up. The browser half is
// scripts/check_motion_phone.mjs. Loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results, prints nothing.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { PHONE_QUERY, PIN_QUERY } from '../../src/landing/useScenePinned';
import { lend, put, scrub, whenPhone } from '../../src/motion/phone';
import { APERTURE_END, APERTURE_R, APERTURE_START, CUT_END, CUT_START, STEP_AT, STEP_GOTO, sceneState } from '../../src/landing/revealScript';

type R = Array<[string, boolean, string?]>;
const read = (p: string) => readFileSync(join(process.cwd(), p), 'utf8').replace(/\r\n/g, '\n');

interface Rule { media: string[]; selector: string; body: string }
/** The rules of a stylesheet with the media conditions around each (comments out; keyframes and other at-rules left out; layers looked through). */
function rules(css: string): Rule[] {
  const out: Rule[] = [];
  const walk = (text: string, media: string[]) => {
    let i = 0;
    while (i < text.length) {
      const open = text.indexOf('{', i);
      if (open < 0) break;
      const head = text.slice(i, open).trim();
      let depth = 1, j = open + 1;
      while (j < text.length && depth) { if (text[j] === '{') depth++; else if (text[j] === '}') depth--; j++; }
      const body = text.slice(open + 1, j - 1);
      if (head.startsWith('@media')) walk(body, [...media, head.replace(/\s+/g, ' ')]);
      else if (head.startsWith('@layer') || head.startsWith('@supports')) walk(body, media);
      else if (!head.startsWith('@')) out.push({ media, selector: head, body });
      i = j;
    }
  };
  walk(css.replace(/\/\*[\s\S]*?\*\//g, ''), []);
  return out;
}

/** A tiny evaluator of the media conditions the page uses for its scenes: and-joined (min-width), (max-width), (min-height) in px or rem (16 px) and (prefers-reduced-motion). */
function matches(query: string, w: number, h: number, reduce = false): boolean {
  return query.split(/\s+and\s+/).every((c) => {
    const m = /^\(([a-z-]+):\s*([\w.-]+)\)$/.exec(c.trim());
    if (!m) throw new Error(`a media condition this test does not know: ${c}`);
    const [, k, raw] = m;
    if (k === 'prefers-reduced-motion') return raw === (reduce ? 'reduce' : 'no-preference');
    const v = raw.endsWith('rem') ? parseFloat(raw) * 16 : parseFloat(raw);
    return k === 'min-width' ? w >= v : k === 'max-width' ? w <= v : k === 'min-height' ? h >= v : (() => { throw new Error(`unknown feature ${k}`); })();
  });
}

export async function run(): Promise<R> {
  const out: R = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);

  // ---- who gets which scene: the two queries partition the widths (768 px is the line), the phone's wants a window 540 px tall, the desktop's 560, neither under reduced motion
  let both = 0, neither = 0, wrongPhone = 0, wrongPin = 0;
  for (let w = 200; w <= 2200; w++) for (const h of [480, 539, 540, 559, 560, 700, 844, 1200]) {
    const ph = matches(PHONE_QUERY, w, h), pin = matches(PIN_QUERY, w, h);
    if (ph && pin) both++;
    if (!ph && !pin && w <= 767 && h >= 540) neither++;
    if (ph !== (w <= 767 && h >= 540)) wrongPhone++;
    if (pin !== (w >= 768 && h >= 560)) wrongPin++;
  }
  check('the phone scene and the desktop scene are never wanted together, at any width from 200 to 2200 px and any of eight heights', both === 0, `${both} combinations match both`);
  check('every window up to 767 px and at least 540 px tall wants the phone scene, nothing wider does', wrongPhone === 0 && neither === 0, `${wrongPhone} wrong answers for the phone, ${neither} phones with no scene`);
  check('the desktop scene is wanted from 768 px and 560 px tall exactly as before', wrongPin === 0, `${wrongPin} wrong answers`);
  check('neither scene is wanted under reduced motion', [PHONE_QUERY, PIN_QUERY].every((q) => !matches(q, 390, 844, true) && !matches(q, 1280, 900, true)));
  check('the phone query is written in px, like the stylesheet\'s own phone rules (a rem query would disagree with them on a browser whose default font size is not 16 px)', /max-width: 767px/.test(PHONE_QUERY) && !/rem/.test(PHONE_QUERY));

  // ---- the helper, against a stand-in window: it starts only with html.mo and no mo-fail on a phone, stops when the window stops matching and starts again when it matches
  const classes = new Set<string>(['mo']);
  let mqMatches = true;
  const listeners: Array<() => void> = [];
  const g = globalThis as unknown as Record<string, unknown>;
  g.document = { documentElement: { classList: { contains: (c: string) => classes.has(c) } } };
  g.matchMedia = (q: string) => ({ media: q, get matches() { return mqMatches; }, addEventListener: (_t: string, f: () => void) => { listeners.push(f); }, removeEventListener: (_t: string, f: () => void) => { const i = listeners.indexOf(f); if (i >= 0) listeners.splice(i, 1); } });
  let asked = '';
  g.matchMedia = ((orig) => (q: string) => { asked = q; return (orig as (q: string) => unknown)(q); })(g.matchMedia);
  let started = 0, stopped = 0;
  const stop = whenPhone(() => { started++; return () => { stopped++; }; });
  check('whenPhone asks the browser for a window up to 767 px with motion allowed, nothing else', /^\(max-width: 767px\) and \(prefers-reduced-motion: no-preference\)$/.test(asked), asked);
  check('whenPhone starts the scene at once on a phone with html.mo', started === 1 && stopped === 0, `${started} started, ${stopped} stopped`);
  mqMatches = false; listeners.forEach((f) => f());
  check('whenPhone stops the scene (and cleans up) when the window stops matching', started === 1 && stopped === 1, `${started} started, ${stopped} stopped`);
  mqMatches = true; listeners.forEach((f) => f());
  check('whenPhone starts it again when the window matches again', started === 2 && stopped === 1, `${started} started, ${stopped} stopped`);
  stop();
  check('the cleanup of whenPhone stops the scene and lets go of the listener', stopped === 2 && listeners.length === 0, `${stopped} stopped, ${listeners.length} listeners left`);
  classes.delete('mo');
  let n1 = 0;
  whenPhone(() => { n1++; return () => {}; })();
  check('whenPhone never starts without html.mo (motion not allowed, or no IntersectionObserver)', n1 === 0);
  classes.add('mo'); classes.add('mo-fail');
  let n2 = 0;
  whenPhone(() => { n2++; return () => {}; })();
  check('whenPhone never starts after the failsafe (html.mo-fail)', n2 === 0);
  classes.delete('mo-fail');
  mqMatches = true;
  let got: unknown[] = [];
  const stopScrub = scrub({} as HTMLElement, () => {}, { start: 0.5, end: 0.2 });
  check('scrub does nothing (and does not fail) before the entry has lent the engine', typeof stopScrub === 'function');
  stopScrub();
  lend(((el: unknown, _cb: unknown, opts: unknown) => { got = [el, opts]; return () => { got.push('stopped'); }; }) as never);
  const target = {} as HTMLElement;
  const stopScrub2 = scrub(target, () => {}, { start: 0.85, end: 0.5 });
  check('scrub starts the traverse of the engine on the element with its own start and end, on a phone with html.mo', got[0] === target && JSON.stringify(got[1]) === JSON.stringify({ start: 0.85, end: 0.5 }), JSON.stringify(got));
  stopScrub2();
  check('the cleanup of scrub stops the traverse', got.at(-1) === 'stopped');
  const el = { dataset: {} as Record<string, string>, attrs: {} as Record<string, boolean>, toggleAttribute(n: string, force: boolean) { this.attrs[n] = force; }, style: { v: {} as Record<string, string>, setProperty(k: string, x: string) { this.v[k] = x; } } };
  put(el as unknown as HTMLElement, { '--dp': '0.500', '--gx': '-12.346%' }, 0.5);
  check('put marks the frame once (data-scrub), keeps data-run while the scene is under way and writes every value as it was given', el.dataset.scrub === '' && el.attrs['data-run'] === true && el.style.v['--dp'] === '0.500' && el.style.v['--gx'] === '-12.346%', JSON.stringify([el.dataset, el.attrs, el.style.v]));
  put(el as unknown as HTMLElement, { '--dp': '1.000' }, 1);
  check('put takes data-run away at the end of the scene (progress 1), so that the frame is then the static one, and keeps data-scrub', el.attrs['data-run'] === false && el.dataset.scrub === '' && el.style.v['--dp'] === '1.000');
  put(el as unknown as HTMLElement, { '--dp': '0.990' }, 0.99);
  check('put brings data-run back when the scroll goes back into the scene', el.attrs['data-run'] === true);
  put(el as unknown as HTMLElement, { '--dp': '1.000' }, 0.9996);
  check('put takes data-run away as soon as the value it writes reads 1.000 (from 0.9995 on), so that a printed 1.000 is never a frame that still carries the styles of its scene', el.attrs['data-run'] === false);

  // ---- the Reveal's script (the table of the design, shared by the desktop scene and the phone's)
  const near = (a: number, b: number, t = 0.01) => Math.abs(a - b) <= t;
  const s0 = sceneState(0), s25 = sceneState(0.25), s5 = sceneState(0.5), s56 = sceneState(0.56), s75 = sceneState(0.75), s1 = sceneState(1);
  check('p 0: the phone photo alone, no line, no ring, step 1, the chip says photo', s0.pos === 100 && s0.r === 0 && s0.line === 0 && s0.ring === 0 && s0.step === 0 && s0.chips.join() === 'photo');
  check('p .25: the cut is under way, the line is on, both chips show', near(s25.pos, 100 * (1 - (0.25 - CUT_START) / (CUT_END - CUT_START))) && s25.line === 1 && s25.chips.join() === 'photo,iris' && s25.step === 0);
  check('p .5: the restored iris alone (the cut is at the left edge), step 2, one chip', s5.pos === 0 && s5.r === 0 && s5.step === 1 && s5.chips.join() === 'iris');
  check('p .56: the aperture is about to open, the line is gone', s56.r === 0 && s56.line === 0 && s56.pos === 0);
  check('p .75: the aperture shows the artwork, the ring is on, step 3, the chip says art', near(s75.r, APERTURE_R * (0.75 - APERTURE_START) / (APERTURE_END - APERTURE_START)) && s75.ring > 0.9 && s75.step === 2 && s75.chips.join() === 'art');
  check('p 1: the artwork whole, no ring, no line, step 3', s1.r === APERTURE_R && s1.ring === 0 && s1.line === 0 && s1.step === 2 && s1.chips.join() === 'art');
  const grid = Array.from({ length: 201 }, (_, i) => sceneState(i / 200));
  const mono = (f: (s: ReturnType<typeof sceneState>) => number, dir: number) => grid.every((s, i) => i === 0 || dir * (f(s) - f(grid[i - 1])) >= -1e-9);
  check('across the pin the cut only moves left, the aperture only opens and the step only counts up', mono((s) => s.pos, -1) && mono((s) => s.r, 1) && mono((s) => s.step, 1));
  check('the aperture ends at 72 percent of the frame, which covers the corners (the half diagonal is 70.7)', APERTURE_R === 72 && APERTURE_R > 70.72);
  check('a step button takes the scroll to the inside of its own stretch, away from the thresholds', STEP_GOTO.every((p, i) => sceneState(p).step === i) && STEP_GOTO.every((p, i) => Math.abs(p - STEP_AT[i]) > 0.05 || i === 0));

  // ---- the stylesheets: every phone rule is inside the one phone condition and carries html.mo:not(.mo-fail)
  const PHONE_MEDIA = '@media (max-width: 767px) and (prefers-reduced-motion: no-preference)';
  const FILES: Array<[string, number, RegExp]> = [['src/landing/css/reveal.css', 8, /lp-rvp/], ['src/landing/css/wall.css', 2, /\.lp-stage\[data-(scrub|run)\]/], ['src/landing/css/sizes.css', 4, /\.lp-ruler\[data-draw\]\[data-(scrub|run)\]/], ['src/landing/css/final.css', 3, /\.lp-bg\[data-(scrub|run)\]/], ['src/landing/css/how.css', 1, /\.lp-steps\[data-run\]/]];
  for (const [file, least, mark] of FILES) {
    const all = rules(read(file));
    const scene = all.filter((r) => mark.test(r.selector));
    check(`${file}: ${scene.length} rules style a phone scene (at least ${least}), so this test is not empty`, scene.length >= least);
    const outside = scene.filter((r) => !r.media.includes(PHONE_MEDIA));
    check(`${file}: every phone rule is inside "${PHONE_MEDIA}"`, outside.length === 0, outside.map((r) => r.selector).join(' | '));
    // the selectors of a rule, split at the commas that are not inside parentheses (an :is() list is one selector)
    const parts = (sel: string) => { const out: string[] = []; let depth = 0, cur = ''; for (const ch of sel) { if (ch === '(') depth++; if (ch === ')') depth--; if (ch === ',' && depth === 0) { out.push(cur.trim()); cur = ''; } else cur += ch; } return [...out, cur.trim()]; };
    const bare = scene.flatMap((r) => parts(r.selector)).filter((x) => !x.startsWith('html.mo:not(.mo-fail) '));
    check(`${file}: every selector of a phone rule starts with html.mo:not(.mo-fail)`, bare.length === 0, bare.join(' | '));
    const strays = all.filter((r) => r.media.includes(PHONE_MEDIA) && !mark.test(r.selector));
    check(`${file}: nothing but phone scene rules is inside the phone condition`, strays.length === 0, strays.map((r) => r.selector).join(' | '));
    const wide = scene.filter((r) => r.media.some((m) => /min-width/.test(m)));
    check(`${file}: no phone rule is also under a min-width (a rule that could reach 768 px and up)`, wide.length === 0);
  }
  const reveal = rules(read('src/landing/css/reveal.css')).filter((r) => /lp-rvp/.test(r.selector));
  check('the phone scene of the Reveal pins with position: sticky under the header and a spacer of one screen (100svh, 100vh before it)', reveal.some((r) => /position: sticky/.test(r.body) && /top: calc\(var\(--hdr-h\)/.test(r.body)) && reveal.some((r) => /::after/.test(r.selector) && /height: 100vh; height: 100svh/.test(r.body)));
  check('the step labels of the phone scene shrink with the screen and never outgrow their column (a word that does not fit breaks instead of being cut)', reveal.some((r) => /lp-rv-step span/.test(r.selector) && /font-size: clamp\(11px, 3\.6vw, 14px\)/.test(r.body) && /max-width: 100%/.test(r.body) && /overflow-wrap: anywhere/.test(r.body)));
  check('the phone scene of the Reveal never sets a height in vh alone (the page\'s length must not follow the browser toolbar)', reveal.every((r) => !/height:\s*100vh;?\s*$/.test(r.body.trim())));
  const wall = rules(read('src/landing/css/wall.css')).filter((r) => /\.lp-stage\[data-run\] img/.test(r.selector));
  check('the wall plate never goes beyond a scale of 1.03 and an inset of 7 percent, moves nothing, and carries them only while data-run is on (at the end it is the static plate)', wall.length === 1 && /scale: calc\(1 \+ \.03 \* \(1 - var\(--ps, 1\)\)\)/.test(wall[0].body) && /inset\(calc\(7% \* \(1 - var\(--ps, 1\)\)\)/.test(wall[0].body) && !/translate|transform|rotate|filter/.test(wall[0].body));
  const fin = rules(read('src/landing/css/final.css')).filter((r) => /\.lp-bg\[data-(run|scrub)\]/.test(r.selector));
  check('the closing picture opens from an inset of 7 percent and a scale of 1.03, only while data-run is on, and moves nothing', fin.some((r) => /\[data-run\]/.test(r.selector) && /inset\(calc\(7% \* \(1 - var\(--op\)\)\)/.test(r.body)) && fin.some((r) => /\[data-run\] img/.test(r.selector) && /scale: calc\(1 \+ \.03 \* \(1 - var\(--op\)\)\)/.test(r.body)) && fin.every((r) => !/translate|transform|rotate|filter|opacity/.test(r.body)));
  check('the clock\'s opening of the closing picture stays off for good once the scene has a value (data-scrub), so that the end of the scene does not play it again', fin.some((r) => /\[data-scrub\]/.test(r.selector) && !/\[data-run\]/.test(r.selector) && /animation: none/.test(r.body)));
  const size = rules(read('src/landing/css/sizes.css')).filter((r) => /\[data-(scrub|run)\]/.test(r.selector));
  const sizeValues = size.filter((r) => /\[data-run\]/.test(r.selector));
  check('the size drawing: one rule keeps the clock\'s animations off for good (data-scrub), three rules (outlines, squares, labels) carry the values only while data-run is on, each a clamp from 0 to 1', size.length === 4 && size.filter((r) => /\[data-scrub\]/.test(r.selector) && /animation: none/.test(r.body)).length === 1 && sizeValues.length === 3 && sizeValues.every((r) => /clamp\(0, .*, 1\)/.test(r.body)));
  const how = rules(read('src/landing/css/how.css')).filter((r) => /\.lp-steps\[data-run\]/.test(r.selector));
  check('the hairlines of how it works are scaled only while data-run is on, from the left, by one clamp from 0 to 1, and nothing else moves', how.length === 1 && /scale: clamp\(0, .*, 1\) 1/.test(how[0].body) && /transform-origin: left center/.test(how[0].body) && !/translate|rotate|filter|opacity/.test(how[0].body));

  // ---- the wiring: the phone scene of the Reveal is rendered only while the hook says so, the desktop one is as it was, the scenes use the engine's own track and traverse
  const revealTsx = read('src/landing/Reveal.tsx'), sceneTsx = read('src/landing/RevealScene.tsx');
  check('Reveal.tsx renders the phone scene only when usePhoneScene says so, and only in the layout that is not the desktop\'s', /usePhoneScene\(\)/.test(revealTsx) && /\{phoneScene && <RevealScene eye=\{sceneEye\} phone \/>\}/.test(revealTsx) && /\{pinned \? \(/.test(revealTsx));
  check('RevealScene.tsx keeps the desktop markup (the copy column, the lp-rv-scene wrapper) and adds the phone one behind its `phone` prop', /className="lp-rv-scene"/.test(sceneTsx) && /className="lp-rv-copy"/.test(sceneTsx) && /if \(phone\)/.test(sceneTsx) && /className="lp-rvp"/.test(sceneTsx));
  check('the artwork layer of the phone scene gets its address only when the scene is within 300 px of the screen', /whenNear\(w, \(\) => setArtNear\(true\), '300px'\)/.test(sceneTsx) && /useState\(!phone\)/.test(sceneTsx));
  for (const [file, what] of [['src/landing/WallStage.tsx', 'traverse'], ['src/landing/SizeGuide.tsx', 'traverse'], ['src/landing/ClosingScene.tsx', 'traverse']] as const) {
    const t = read(file);
    check(`${file}: the scene is the engine's ${what} inside whenPhone, written with put() on its own frame element`, new RegExp(`whenPhone\\(\\(\\) => ${what}\\(`).test(t) && /put\(/.test(t) && /from '\.\.\/motion\/phone'/.test(t));
  }
  const howTsx = read('src/landing/HowItWorks.tsx'), mainTsx = read('src/main.tsx');
  check('HowItWorks.tsx does not import the engine (the release gate renders the section on the server, where the engine cannot be loaded): it uses scrub() of phone.ts, which the entry lends the engine to', !/from '\.\.\/motion\/motion'/.test(howTsx) && /import \{ put, scrub \} from '\.\.\/motion\/phone'/.test(howTsx) && /scrub\(rail, \(p\) => put\(rail, \{ '--sp': p\.toFixed\(3\) \}, p\)/.test(howTsx) && /lend\(traverse\)/.test(mainTsx) && /import \{ lend \} from '\.\/motion\/phone'/.test(mainTsx));
  check('the phone helper never writes on html or body (a value inherited from the root would restyle the whole page each frame)', !/documentElement\.style|body\.style/.test(read('src/motion/phone.ts')));
  check('the engine (src/motion/motion.ts) does not mention the phone scenes', !/whenPhone|data-scrub|lp-rvp/.test(read('src/motion/motion.ts')));
  return out;
}
