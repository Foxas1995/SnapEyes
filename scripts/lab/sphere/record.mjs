// LAB: a screen recording of a centrepiece prototype, frame by frame, with a scripted swipe, drag, tap or key (headless Chrome through
// scripts/lib/cdp.mjs). The page runs on its own virtual clock (?rec, src/lab/sphere/motion.ts): every frame the recorder sends the input of that
// moment, moves the clock one frame and takes the picture, so the video is the page's own motion at an exact 60 frames per second, whatever the
// speed of this machine. The frame rate the page reaches in real time is measured separately (./fps.mjs).
//
//   node scripts/lab/sphere/record.mjs <scenario.json> <out dir> [base url]
//
// scenario: { "url": "/src/lab/sphere.html?p=globe&lang=lt&ui=0", "device": "phone" | "desktop", "fps": 60, "seconds": 14,
//             "events": [ { "at": 2000, "swipe": [[330, 420], [80, 440]], "ms": 260 },     // a finger (phone) or the mouse (desktop), CSS px
//                         { "at": 6000, "tap": "nebula" },                                  // the centre of that artwork's button, or [x, y]
//                         { "at": 9000, "key": "ArrowRight" } ],
//             "stills": [ { "at": 1500, "name": "idle" } ] }
// Frames go to <out dir>/frames/f00000.jpg, stills to <out dir>/<name>.png; ffmpeg turns the frames into the MP4 (./encode.sh).
import { launch, sleep } from '../../lib/cdp.mjs';
import { mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const [scenarioPath, out, base = 'http://127.0.0.1:5281'] = process.argv.slice(2);
const sc = JSON.parse(readFileSync(scenarioPath, 'utf8'));
const fps = sc.fps ?? 60;
const step = 1000 / fps;
const frames = Math.round((sc.seconds ?? 12) * fps);
const phone = sc.device !== 'desktop';
const view = phone ? { width: 412, height: 915, dpr: 2, mobile: true } : { width: 1440, height: 900, dpr: 1, mobile: false };

rmSync(join(out, 'frames'), { recursive: true, force: true });
mkdirSync(join(out, 'frames'), { recursive: true });

// no input resampling: Chrome would move a finger to where it predicts it at the frame's time, and the frames here are not real time
const chrome = await launch({ args: ['--disable-features=ResamplingInputEvents,ResamplingScrollEvents'] });
const page = await chrome.page({ ...view, reduceMotion: !!sc.reduceMotion });
const errors = [];
const consoleLines = [];
page.on((d) => {
  if (d.method === 'Runtime.exceptionThrown') errors.push(d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text);
  if (d.method === 'Runtime.consoleAPICalled' && process.env.SX_DEBUG) consoleLines.push(d.params.args.map((a) => a.value ?? a.description).join(' '));
});
await page.goto(base + sc.url);
await page.loaded(30000);
for (let i = 0; i < 300; i++) {
  if (await page.eval('!!(window.__sx && window.__sx.ready)')) break;
  await sleep(100);
}
// every picture decoded, the fonts in
await page.eval('Promise.all([...document.images].map((i) => i.decode().catch(() => 0))).then(() => document.fonts.ready).then(() => true)');
await sleep(300);
if (process.env.SX_DEBUG) await page.eval(`(() => { for (const t of ['pointerdown','pointermove','pointerup','pointercancel','click']) document.addEventListener(t, (e) => console.log(t, e.pointerType || '', Math.round(e.clientX), window.__sx.state().mode), true); return 1 })()`);

// the input queue: each event becomes one or more inputs at frame times
const inputs = [];
const where = async (target) => (Array.isArray(target) ? { x: target[0], y: target[1] } : await page.eval(`window.__sx.where(${JSON.stringify(target)})`));
for (const e of sc.events ?? []) {
  if (e.swipe) {
    const [[x0, y0], [x1, y1]] = e.swipe;
    const n = Math.max(2, Math.round((e.ms ?? 250) / step));
    // a finger eases in and out of a swipe; the mouse the same
    for (let k = 0; k <= n; k++) {
      const p = k / n;
      const q = p < 0.5 ? 2 * p * p : 1 - 2 * (1 - p) * (1 - p);
      inputs.push({ at: e.at + k * step, kind: k === 0 ? 'down' : 'move', x: x0 + (x1 - x0) * q, y: y0 + (y1 - y0) * q });
    }
    inputs.push({ at: e.at + (n + 1) * step + (e.hold ?? 0), kind: 'up' });
  } else if (e.tap !== undefined) {
    inputs.push({ at: e.at, kind: 'tap', target: e.tap });
  } else if (e.key) {
    inputs.push({ at: e.at, kind: 'key', key: e.key });
  } else if (e.scroll) {
    inputs.push({ at: e.at, kind: 'scroll', y: e.scroll });
  }
}
inputs.sort((a, b) => a.at - b.at);

const KEYS = { ArrowRight: 39, ArrowLeft: 37, ArrowUp: 38, ArrowDown: 40, Enter: 13, Escape: 27, Tab: 9 };
let last = { x: 0, y: 0 };
async function send(i) {
  if (i.kind === 'key') {
    const code = KEYS[i.key] ?? 0;
    await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: i.key, code: i.key, windowsVirtualKeyCode: code });
    await page.send('Input.dispatchKeyEvent', { type: 'keyUp', key: i.key, code: i.key, windowsVirtualKeyCode: code });
    return;
  }
  if (i.kind === 'scroll') {
    await page.eval(`window.scrollTo(0, ${i.y})`);
    return;
  }
  if (i.kind === 'tap') {
    const p = await where(i.target);
    if (!p) throw new Error(`tap: no ${JSON.stringify(i.target)}`);
    if (phone) {
      await page.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: p.x, y: p.y }] });
      await page.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    } else {
      await page.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: p.x, y: p.y });
      await page.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: p.x, y: p.y, button: 'left', buttons: 1, clickCount: 1 });
      await page.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: p.x, y: p.y, button: 'left', buttons: 0, clickCount: 1 });
    }
    return;
  }
  const x = i.x ?? last.x;
  const y = i.y ?? last.y;
  last = { x, y };
  if (phone) {
    const type = i.kind === 'down' ? 'touchStart' : i.kind === 'move' ? 'touchMove' : 'touchEnd';
    await page.send('Input.dispatchTouchEvent', { type, touchPoints: i.kind === 'up' ? [] : [{ x, y }] });
  } else {
    const type = i.kind === 'down' ? 'mousePressed' : i.kind === 'move' ? 'mouseMoved' : 'mouseReleased';
    await page.send('Input.dispatchMouseEvent', { type, x, y, button: 'left', buttons: i.kind === 'up' ? 0 : 1, clickCount: i.kind === 'move' ? 0 : 1 });
  }
}

const stills = new Map((sc.stills ?? []).map((s) => [Math.round(s.at / step), s.name]));
const log = [];
let q = 0;
for (let f = 0; f < frames; f++) {
  const t = f * step;
  let sent = false;
  while (q < inputs.length && inputs[q].at <= t + 0.01) {
    await send(inputs[q++]);
    sent = true;
  }
  // let the page take the input in a frame of its own: a touch still queued when the next capture starts is mapped in device pixels
  if (sent) await page.eval('new Promise((r) => requestAnimationFrame(() => r(1)))');
  await page.eval(`window.__sx.step(${f === 0 ? 0 : step})`);
  // captureBeyondViewport must stay false: a capture that resizes the view for a moment maps the next touch in device pixels
  const r = await page.send('Page.captureScreenshot', { format: 'jpeg', quality: 93, captureBeyondViewport: false, fromSurface: true });
  writeFileSync(join(out, 'frames', `f${String(f).padStart(5, '0')}.jpg`), Buffer.from(r.data, 'base64'));
  if (stills.has(f)) {
    const png = await page.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false, fromSurface: true });
    writeFileSync(join(out, `${stills.get(f)}.png`), Buffer.from(png.data, 'base64'));
  }
  if (f % fps === 0) log.push(`${(t / 1000).toFixed(1)} s ${JSON.stringify(await page.eval('window.__sx.state()'))}`);
}
writeFileSync(join(out, 'log.txt'), [...log, ...(errors.length ? ['ERRORS', ...errors] : []), ...(consoleLines.length ? ['CONSOLE', ...consoleLines] : [])].join('\n') + '\n');
console.log(`${frames} frames, ${inputs.length} inputs${errors.length ? `, ${errors.length} page errors` : ''}`);
await page.close();
await chrome.close();
