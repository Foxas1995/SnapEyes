// A small Chrome DevTools Protocol driver for the checks of the landing page (Node 22 or newer, no dependencies: the
// WebSocket is Node's own). Real Chrome, headless, its own throw-away profile. Used by scripts/legal_look.mjs,
// scripts/check_shell.mjs and scripts/measure_landing.mjs.
//   Chrome's path: the CHROME_PATH environment variable, else the usual install places.
import { spawn } from 'node:child_process';
import { existsSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const CANDIDATES = [
  process.env.CHROME_PATH,
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  '/usr/bin/google-chrome',
  '/usr/bin/chromium',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
].filter(Boolean);

export function chromePath() {
  const p = CANDIDATES.find((c) => existsSync(c));
  if (!p) throw new Error('Chrome not found: set CHROME_PATH');
  return p;
}

export class Page {
  constructor(ws, browser, targetId) {
    this.ws = ws;
    this.browser = browser;
    this.targetId = targetId;
    this.n = 0;
    this.waiting = new Map();
    this.events = [];
    this.listeners = [];
    ws.onmessage = (m) => {
      const d = JSON.parse(m.data);
      if (d.id && this.waiting.has(d.id)) {
        this.waiting.get(d.id)(d);
        this.waiting.delete(d.id);
      } else if (d.method) {
        this.events.push(d);
        for (const l of this.listeners) l(d);
      }
    };
  }

  send(method, params = {}) {
    const id = ++this.n;
    return new Promise((res, rej) => {
      this.waiting.set(id, (d) => (d.error ? rej(new Error(`${method}: ${JSON.stringify(d.error)}`)) : res(d.result)));
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  on(fn) {
    this.listeners.push(fn);
  }

  /** Evaluate an expression in the page (awaits promises, returns the value). */
  async eval(expression) {
    const r = await this.send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error(`eval: ${JSON.stringify(r.exceptionDetails.exception?.description || r.exceptionDetails)}`);
    return r.result.value;
  }

  async goto(url, settle = 0) {
    await this.send('Page.navigate', { url });
    if (settle) await sleep(settle);
  }

  /** Wait until document.readyState is complete (and web fonts are loaded). */
  async loaded(timeout = 15000) {
    const t0 = Date.now();
    for (;;) {
      try {
        if (await this.eval("document.readyState === 'complete'")) break;
      } catch { /* the page is navigating */ }
      if (Date.now() - t0 > timeout) throw new Error('page did not load');
      await sleep(60);
    }
    await this.eval('document.fonts && document.fonts.ready.then(() => true)');
  }

  /** PNG screenshot slices of the whole page (Chrome cannot make one texture above 16k px). Returns Buffers. */
  async fullShots(slice = 4000) {
    const m = await this.eval('JSON.stringify({h: document.documentElement.scrollHeight, w: document.documentElement.clientWidth})');
    const { h, w } = JSON.parse(m);
    const out = [];
    for (let y = 0; y < h; y += slice) {
      const r = await this.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true, clip: { x: 0, y, width: w, height: Math.min(slice, h - y), scale: 1 } });
      out.push(Buffer.from(r.data, 'base64'));
    }
    return out;
  }

  async shot(clip) {
    const p = { format: 'png' };
    if (clip) {
      p.clip = { x: clip[0], y: clip[1], width: clip[2], height: clip[3], scale: 1 };
      p.captureBeyondViewport = true;
    }
    const r = await this.send('Page.captureScreenshot', p);
    return Buffer.from(r.data, 'base64');
  }

  async close() {
    try { this.ws.close(); } catch { /* already closed */ }
    await fetch(`http://127.0.0.1:${this.browser.port}/json/close/${this.targetId}`).catch(() => undefined);
  }
}

export async function launch({ args = [] } = {}) {
  const port = 9300 + Math.floor(Math.random() * 600);
  const profile = mkdtempSync(join(tmpdir(), 'snapeyes-cdp-'));
  const proc = spawn(chromePath(), [
    '--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, '--disable-gpu', '--hide-scrollbars',
    '--no-first-run', '--no-default-browser-check', '--mute-audio', '--force-color-profile=srgb', '--font-render-hinting=none',
    '--disable-lcd-text', '--disable-extensions', '--disable-background-networking', ...args, 'about:blank',
  ], { stdio: 'ignore' });
  let up = false;
  for (let i = 0; i < 120 && !up; i++) {
    try { up = (await fetch(`http://127.0.0.1:${port}/json/version`)).ok; } catch { await sleep(250); }
  }
  if (!up) { proc.kill(); throw new Error('Chrome did not start'); }
  const browser = {
    port,
    /** A new tab. opts: width, height, dpr, mobile, reduceMotion, colorScheme, cpu (slowdown rate), throttle {latency, down, up} (bytes/s), noJs, vitals (install the LCP and CLS observers before the page runs) */
    async page(opts = {}) {
      const t = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' })).json();
      const ws = new WebSocket(t.webSocketDebuggerUrl);
      await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
      const p = new Page(ws, browser, t.id);
      await p.send('Page.enable');
      await p.send('Runtime.enable');
      await p.send('Network.enable');
      await p.send('Emulation.setDeviceMetricsOverride', { width: opts.width || 1280, height: opts.height || 900, deviceScaleFactor: opts.dpr || 1, mobile: !!opts.mobile });
      if (opts.mobile) await p.send('Emulation.setTouchEmulationEnabled', { enabled: true });
      const features = [];
      if (opts.reduceMotion) features.push({ name: 'prefers-reduced-motion', value: 'reduce' });
      if (opts.colorScheme) features.push({ name: 'prefers-color-scheme', value: opts.colorScheme });
      if (features.length) await p.send('Emulation.setEmulatedMedia', { features });
      if (opts.noJs) await p.send('Emulation.setScriptExecutionDisabled', { value: true });
      if (opts.throttle) {
        await p.send('Network.emulateNetworkConditions', { offline: false, latency: opts.throttle.latency, downloadThroughput: opts.throttle.down, uploadThroughput: opts.throttle.up });
        await p.send('Network.setCacheDisabled', { cacheDisabled: true });
      }
      if (opts.cpu) await p.send('Emulation.setCPUThrottlingRate', { rate: opts.cpu });
      if (opts.vitals) await p.send('Page.addScriptToEvaluateOnNewDocument', { source: VITALS });
      return p;
    },
    async close() {
      proc.kill();
      await sleep(400);
      try { rmSync(profile, { recursive: true, force: true }); } catch { /* the profile may still be locked: the OS cleans the temp folder */ }
    },
  };
  return browser;
}

// LCP, CLS (with the elements that moved), long tasks, paints: installed before the page's own scripts run
const VITALS = `
window.__lcp = []; window.__cls = 0; window.__shifts = []; window.__tbt = 0; window.__paint = {};
try { new PerformanceObserver((l) => { for (const e of l.getEntries()) window.__lcp.push([Math.round(e.startTime), e.element ? e.element.tagName + ' ' + ((e.element.currentSrc || e.element.src || '').split('/').pop() || (e.element.textContent || '').slice(0, 30)) : '', e.size]); }).observe({ type: 'largest-contentful-paint', buffered: true }); } catch (e) {}
try { new PerformanceObserver((l) => { for (const e of l.getEntries()) if (!e.hadRecentInput) { window.__cls += e.value; window.__shifts.push([Math.round(e.startTime), +e.value.toFixed(4), (e.sources || []).map((s) => { const n = s.node; return n ? (n.id ? '#' + n.id : (n.className && typeof n.className === 'string' ? '.' + n.className.split(' ')[0] : n.nodeName)) : '?'; }).slice(0, 3).join(',')]); } }).observe({ type: 'layout-shift', buffered: true }); } catch (e) {}
try { new PerformanceObserver((l) => { for (const e of l.getEntries()) window.__tbt += Math.max(0, e.duration - 50); }).observe({ type: 'longtask', buffered: true }); } catch (e) {}
try { new PerformanceObserver((l) => { for (const e of l.getEntries()) window.__paint[e.name] = Math.round(e.startTime); }).observe({ type: 'paint', buffered: true }); } catch (e) {}
`;
