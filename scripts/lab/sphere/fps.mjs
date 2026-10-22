// LAB: the frame rate of the centrepiece prototypes in real time, in headless Chrome with the CPU slowed four times (a mid-range Android phone is
// about that much slower than a desktop's core), through the production build of the lab page (./vite.lab.config.mjs).
//
//   node scripts/lab/sphere/fps.mjs <base url> <out.json> [--cpu 4] [--soft] [--piece globe|ring]
//
// Chrome runs with its GPU (a phone composites on its GPU) unless --soft, which forces software compositing (the worst case). For each prototype and
// each screen (phone 412 x 915 at pixel ratio 2.625 with touch, desktop 1440 x 900 with a mouse) a script plays in real time: the piece alone, a
// swipe or a drag and its inertia, a tap that opens or brings an artwork to the front, and for the ring a few swipes. Per phase:
//   fps        animation frames per second (requestAnimationFrame callbacks, the page's own loop runs in them)
//   p95 / max  frame intervals, ms; dropped: intervals over 25 ms (a missed 60 Hz frame)
//   main       the renderer's main thread busy per frame, ms (CDP Performance.TaskDuration, in throttled time)
//   own        the piece's own code per frame, ms (src/lab/sphere/motion.ts loop, timed in the page)
import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { Page, chromePath, sleep } from '../../lib/cdp.mjs';

const args = process.argv.slice(2);
const base = args[0] || 'http://127.0.0.1:5282';
const outPath = args[1] || 'fps.json';
const cpu = Number(args.includes('--cpu') ? args[args.indexOf('--cpu') + 1] : 4);
const soft = args.includes('--soft');
const only = args.includes('--piece') ? args[args.indexOf('--piece') + 1] : '';

async function launchChrome() {
  const port = 9300 + Math.floor(Math.random() * 600);
  const profile = mkdtempSync(join(tmpdir(), 'sx-fps-'));
  const proc = spawn(chromePath(), [
    '--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, '--hide-scrollbars', '--no-first-run', '--no-default-browser-check',
    '--mute-audio', '--force-color-profile=srgb', '--disable-extensions', '--disable-background-networking', '--disable-features=ResamplingInputEvents',
    ...(soft ? ['--disable-gpu'] : ['--ignore-gpu-blocklist', '--enable-gpu-rasterization']), 'about:blank',
  ], { stdio: 'ignore' });
  for (let i = 0; i < 120; i++) {
    try {
      if ((await fetch(`http://127.0.0.1:${port}/json/version`)).ok) break;
    } catch { await sleep(250); }
  }
  return {
    async page(view) {
      const t = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' })).json();
      const ws = new WebSocket(t.webSocketDebuggerUrl);
      await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
      const p = new Page(ws, { port }, t.id);
      await p.send('Page.enable');
      await p.send('Runtime.enable');
      await p.send('Performance.enable');
      await p.send('Emulation.setDeviceMetricsOverride', { width: view.width, height: view.height, deviceScaleFactor: view.dpr, mobile: view.mobile });
      if (view.mobile) await p.send('Emulation.setTouchEmulationEnabled', { enabled: true });
      await p.send('Emulation.setCPUThrottlingRate', { rate: cpu });
      return p;
    },
    async close() {
      proc.kill();
      await sleep(500);
      try { rmSync(profile, { recursive: true, force: true }); } catch { /* the OS cleans the temp folder */ }
    },
  };
}

const PROBE = `(() => {
  window.__sxProf = [];
  const f = window.__fps = { t: [], on: false };
  f.start = () => { f.t = []; window.__sxProf.length = 0; f.on = true; const loop = (ts) => { f.t.push(ts); if (f.on) requestAnimationFrame(loop); }; requestAnimationFrame(loop); };
  f.stop = () => { f.on = false; const t = [...new Set(f.t)]; const iv = t.slice(1).map((x, i) => x - t[i]).sort((a, b) => a - b);
    const own = window.__sxProf.slice().sort((a, b) => a - b);
    const q = (a, p) => (a.length ? a[Math.min(a.length - 1, Math.floor(p * a.length))] : 0);
    return { frames: t.length, ms: t.length > 1 ? t[t.length - 1] - t[0] : 0, p50: q(iv, 0.5), p95: q(iv, 0.95), max: iv.length ? iv[iv.length - 1] : 0,
      dropped: iv.filter((x) => x > 25).length, own50: q(own, 0.5), own95: q(own, 0.95) }; };
  return true;
})()`;

async function metric(page) {
  const m = await page.send('Performance.getMetrics');
  const get = (n) => m.metrics.find((x) => x.name === n)?.value ?? 0;
  return { task: get('TaskDuration'), style: get('RecalcStyleDuration'), layout: get('LayoutDuration'), script: get('ScriptDuration') };
}

async function phase(page, name, play) {
  const m0 = await metric(page);
  await page.eval('window.__fps.start()');
  await play();
  const r = await page.eval('window.__fps.stop()');
  const m1 = await metric(page);
  const per = (k) => (r.frames ? ((m1[k] - m0[k]) * 1000) / r.frames : 0);
  const fps = r.ms ? ((r.frames - 1) * 1000) / r.ms : 0;
  return { phase: name, fps: +fps.toFixed(1), frames: r.frames, p50: +r.p50.toFixed(1), p95: +r.p95.toFixed(1), max: +r.max.toFixed(1), dropped: r.dropped,
    main: +per('task').toFixed(2), style: +per('style').toFixed(2), own50: +r.own50.toFixed(2), own95: +r.own95.toFixed(2) };
}

async function drag(page, touch, from, to, ms) {
  const n = Math.max(4, Math.round(ms / 16));
  const send = (type, x, y) => touch
    ? page.send('Input.dispatchTouchEvent', { type: { down: 'touchStart', move: 'touchMove', up: 'touchEnd' }[type], touchPoints: type === 'up' ? [] : [{ x, y }] })
    : page.send('Input.dispatchMouseEvent', { type: { down: 'mousePressed', move: 'mouseMoved', up: 'mouseReleased' }[type], x, y, button: 'left', buttons: type === 'up' ? 0 : 1, clickCount: type === 'move' ? 0 : 1 });
  await send('down', from[0], from[1]);
  for (let k = 1; k <= n; k++) {
    const p = k / n;
    const q = p < 0.5 ? 2 * p * p : 1 - 2 * (1 - p) * (1 - p);
    await send('move', from[0] + (to[0] - from[0]) * q, from[1] + (to[1] - from[1]) * q);
    await sleep(16);
  }
  await send('up', to[0], to[1]);
}

async function tap(page, touch, p) {
  if (touch) {
    await page.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: p.x, y: p.y }] });
    await page.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  } else {
    await page.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: p.x, y: p.y, button: 'left', buttons: 1, clickCount: 1 });
    await page.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: p.x, y: p.y, button: 'left', buttons: 0, clickCount: 1 });
  }
}

// the centre of a button of the stage that a tap reaches: the front artwork of the ring's side, or a disc near the globe's centre
const PICK = (kind) => `(() => {
  const stage = document.querySelector('.sx-stage'); const box = stage.getBoundingClientRect();
  const sel = ${JSON.stringify(kind)} === 'globe' ? '.sx-disc' : '.sx-tile';
  let best = null, bd = 1e9;
  for (const b of stage.querySelectorAll(sel)) {
    const r = b.getBoundingClientRect(); if (!r.width) continue;
    const x = r.left + r.width / 2, y = r.top + r.height / 2; const e = document.elementFromPoint(x, y); if (!e || !b.contains(e)) continue;
    const want = ${JSON.stringify(kind)} === 'globe' ? Math.hypot(x - (box.left + box.width * 0.62), y - (box.top + box.height * 0.42)) : Math.hypot(x - (box.left + box.width * 0.82), y - (box.top + box.height * 0.5));
    if (want < bd) { bd = want; best = { x, y }; }
  }
  return best;
})()`;

const VIEWS = {
  phone: { width: 412, height: 915, dpr: 2.625, mobile: true },
  desktop: { width: 1440, height: 900, dpr: 1, mobile: false },
};

const chrome = await launchChrome();
const results = [];
let gpuInfo = '';
try {
  for (const piece of ['globe', 'ring'].filter((p) => !only || p === only)) {
    for (const [device, view] of Object.entries(VIEWS)) {
      const page = await chrome.page(view);
      await page.goto(`${base}/src/lab/sphere.html?p=${piece}&lang=lt&ui=0`);
      await page.loaded(30000);
      for (let i = 0; i < 200; i++) {
        if (await page.eval("!!document.querySelector('.lab-frame[data-ready]')")) break;
        await sleep(100);
      }
      await page.eval('Promise.all([...document.images].map((i) => i.decode().catch(() => 0))).then(() => true)');
      if (!gpuInfo) gpuInfo = await page.eval(`(() => { try { const c = document.createElement('canvas').getContext('webgl'); const d = c.getExtension('WEBGL_debug_renderer_info'); return c.getParameter(d.UNMASKED_RENDERER_WEBGL); } catch (e) { return 'no webgl: ' + e.message; } })()`);
      await page.eval(PROBE);
      await sleep(800);
      const touch = view.mobile;
      const box = await page.eval("(() => { const r = document.querySelector('.sx-stage').getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; })()");
      const cy = box.y + box.h * 0.45;
      const rows = [];
      rows.push(await phase(page, 'idle', () => sleep(piece === 'ring' ? 6500 : 5000)));
      rows.push(await phase(page, 'swipe + inertia', async () => {
        await drag(page, touch, [box.x + box.w * 0.8, cy], [box.x + box.w * 0.2, cy + (touch ? 6 : 40)], 280);
        await sleep(2500);
      }));
      if (piece === 'globe') {
        rows.push(await phase(page, 'tap: open', async () => {
          const p = await page.eval(PICK('globe'));
          if (p) await tap(page, touch, p);
          await sleep(1600);
        }));
        rows.push(await phase(page, 'tap: close', async () => {
          await tap(page, touch, { x: box.x + box.w * 0.5, y: box.y + box.h * 0.2 });
          await sleep(1400);
        }));
      } else {
        rows.push(await phase(page, 'three swipes', async () => {
          for (let k = 0; k < 3; k++) {
            await drag(page, touch, [box.x + box.w * 0.75, cy], [box.x + box.w * 0.3, cy], 220);
            await sleep(900);
          }
        }));
        rows.push(await phase(page, 'tap: to the front', async () => {
          const p = await page.eval(PICK('ring'));
          if (p) await tap(page, touch, p);
          await sleep(1500);
        }));
      }
      for (const r of rows) results.push({ piece, device, ...r });
      await page.close();
    }
  }
} finally {
  await chrome.close();
}
const out = { date: new Date().toISOString(), cpuThrottle: cpu, compositing: soft ? 'software (--disable-gpu)' : 'gpu', gpu: gpuInfo, base, results };
writeFileSync(outPath, JSON.stringify(out, null, 2));
console.log(`cpu x${cpu}, ${out.compositing}, ${gpuInfo}`);
console.log('piece   device   phase                fps   p95  max  dropped  main/frame  style/frame  own p50/p95');
for (const r of results) {
  console.log(`${r.piece.padEnd(7)} ${r.device.padEnd(8)} ${r.phase.padEnd(19)} ${String(r.fps).padStart(5)} ${String(r.p95).padStart(5)} ${String(r.max).padStart(5)} ${String(r.dropped).padStart(5)}    ${String(r.main).padStart(6)}      ${String(r.style).padStart(6)}     ${r.own50}/${r.own95}`);
}
