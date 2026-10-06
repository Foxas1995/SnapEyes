// The API of /try and /order as a stand-in with the models stubbed, for the checks that run against a build with no server behind it
// (scripts/check_motion_flow.mjs). It answers what the pages ask for, with the pictures that are already in the repository (the site's own sample eye),
// and it TAKES TIME on purpose, so that the waiting screens can be looked at. No image model, no Gemini call, no key, no Stripe, no store: nothing here
// can reach beyond this machine. The shapes are the ones of api/analyze.py, deglare.py, enhance.py, compose.py and order.py (read from the real answers of
// the dev API with its models stubbed, and from the page code that parses them: src/try/shots.ts, picker.ts, composeApi.ts, src/order/api.ts).
//
//   POST /api/analyze     one good shot, the iris in the middle, a work ticket
//   POST /api/deglare     the crop back, nothing changed
//   POST /api/enhance     the restored picture (the display copy: the stub does not draw a watermark, the check says so where it matters)
//   POST /api/compose     the tile list of one eye (a live style, a second one, one that opens soon), the large preview, the 480 px tiles
//   GET  /api/order       the scripted order: states making, pending, ready, review (api.setOrder), its eyes made one at a time
//   POST /api/order       action make (one eye) and compose (the artwork): each takes `make` ms, then the order is one step on
//   GET  /api/checkout, /api/health   the same stand-in as scripts/lib/stubapi.mjs (ordering closed)
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { checkoutAnswer } from './stubapi.mjs';
import { loadRegistry, ceilingOf } from '../styles_source.mjs';

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const body = (req) => new Promise((resolve) => { const c = []; req.on('data', (d) => c.push(d)); req.on('end', () => { try { resolve(JSON.parse(Buffer.concat(c).toString('utf8') || '{}')); } catch { resolve({}); } }); });

/** A stand-in API for the tools. `wait` overrides how long each answer takes (ms). */
export function flowApi(root, { wait = {} } = {}) {
  const w = { analyze: 300, deglare: 800, enhance: 1200, compose: 700, tile: 300, make: 1500, ...wait };
  const file = (n) => readFileSync(join(root, 'public/assets', n)).toString('base64');
  const restored = file('sample_eye_blue_restored.jpg');   // the display picture of the eye and of the first style
  const second = file('sample_eye_blue_before.jpg');       // another picture, so that a second style is a different picture
  const stats = { calls: [], model: 0 };
  // the styles of one eye, read from the registry (api/_lib/styles_registry.py, the one place for ids, names and stages; no id is written here): the first style that
  // can be bought now and is plain black, the first live art style, and one that opens soon
  const reg = loadRegistry(root);
  const one = Object.entries(reg.styles).filter(([, d]) => d.legacy !== 1 && d.eyes[0] <= 1 && d.eyes[1] >= 1).sort((a, b) => a[1].tile_order - b[1].tile_order);
  const pick = (stage, cls) => one.find(([, d]) => ceilingOf(d, 1) === stage && (!cls || d.price_class === cls));
  const [first, second_, soon] = [pick('live', 'black') || pick('live'), pick('live', 'art'), pick('preview')];
  const ids = { first: first[0], second: second_[0], soon: soon[0] };
  const order = { state: 'making', eyes: 3, made: new Set(), pendingUntil: 0, composeMs: w.make };

  const status = () => {
    const st = {
      order: 'i3check', state: order.state, lang: 'en', count: order.eyes, style: ids.first, market: 'eu',
      eyes: Array.from({ length: order.eyes }, (_, i) => ({ eye: i + 1, made: order.made.has(i + 1), uploaded: true, preview_url: '/assets/sample_eye_blue_before.jpg' })),
    };
    if (order.state === 'pending') { st.waiting_for = 'confirmation_email'; if (Date.now() >= order.pendingUntil) { order.state = 'making'; st.state = 'making'; } }
    if (order.state === 'ready') st.download = { url: '/assets/sample_eye_blue_restored.jpg', download_url: '/assets/sample_eye_blue_restored.jpg', width: 1600, height: 1600, bytes: 294739 };
    else if (order.state === 'making' || order.state === 'paid') st.artwork = { done: 0, of: 1 };
    return st;
  };

  const tile = ([id, d], stage, isPick) => ({ id, name: d.name, slug: d.slug, group: d.group, legacy: 0, stage, available: true, why: null, layouts: (d.layouts['1'] || ['single']).slice(0, 1), eyes: 1, price_class: d.price_class, looks: {}, gate: 'advisory', rule: 'lid', pick: isPick });
  const tiles = () => [tile(first, 'live', true), tile(second_, 'live', false), tile(soon, 'preview', false)];
  const pic = (id) => ({ image: id === ids.second ? second : restored, width: 1024, height: 1024, layout: 'single', canvas: null, design_used: id, fallback: null, plan8: null });

  const handler = (req, res) => {
    const url = new URL(req.url, 'http://x');
    if (!url.pathname.startsWith('/api/')) return false;
    const json = (o, code = 200) => { res.writeHead(code, { 'content-type': 'application/json', 'cache-control': 'no-store' }); res.end(JSON.stringify(o)); };
    stats.calls.push(`${req.method} ${url.pathname}`);
    if (url.pathname === '/api/health') { json({ stripe: true, stripe_live: false, email: false, blob_store: false }); return true; }
    if (url.pathname === '/api/checkout') { json(checkoutAnswer(root, { open: false })); return true; }
    void (async () => {
      const b = req.method === 'POST' ? await body(req) : {};
      if (url.pathname === '/api/analyze') {
        await sleep(w.analyze);
        json({
          ok: true, ticket: 'tk-i3', pupil_r: 0.2, fibre: 3, iris: { cx: 0.5, cy: 0.5, r: 0.3 }, pad: 1.12, glare_boxes_crop: [],
          quality: { diameter_px: 600, sharpness: 5, sharpness_label: 'sharp', occlusion_pct: 0, glare: false, locked: true, verdict: 'good', message: 'Great photo', tips: [], detail: 90 },
          targets: { detail_good: 70, detail_ok: 40, min_diameter_px: 280, good_diameter_px: 420, max_shots: 5 },
        });
      } else if (url.pathname === '/api/deglare') {
        await sleep(w.deglare);
        json({ ok: true, crop: String(b.crop || 'AAAA').slice(0, 64) || 'AAAA', glare_pct: 0, changed: false, used_sr: false });
      } else if (url.pathname === '/api/enhance') {
        if (b.sample === true) { json({ ok: false, error: 'the stand-in has no prepared sample' }, 500); return; }
        await sleep(w.enhance);
        json({ ok: true, image: restored, sealed: 'S', sealed_sizes: {}, fidelity: 0.9, used_sr: false, fallback: false, seconds: 2, stored: false, qa: null });
      } else if (url.pathname === '/api/compose') {
        if (b.action === 'help') { json({ ok: true }); return; }
        const list = Array.isArray(b.styles) ? b.styles : null;
        if (list && list.length === 0) {
          json({ ok: true, batch: true, count: 1, size: 480, tiles: tiles(), pick: { id: ids.first, reason: Object.values(first[1].reason || {})[0] || '' }, eyes: [{ eye: 1, eye_id: 'i3eye', cls: 'own', pupil: 'round', gate: { lid: true, fill: true } }] });
        } else if (list) {
          await sleep(w.tile);
          json({ ok: true, batch: true, count: 1, size: 480, tiles: list.map((id) => ({ id, ...pic(id) })) });
        } else {
          await sleep(w.compose);
          json({ ok: true, ...pic(String(b.style || ids.first)) });
        }
      } else if (url.pathname === '/api/order') {
        if (req.method === 'GET') { json(status()); return; }
        await sleep(order.composeMs);
        if (b.action === 'make') { order.made.add(Number(b.eye || 1)); order.state = 'making'; }
        else if (b.action === 'compose') order.state = 'ready';
        json(status());
      } else json({ ok: false, error: 'not here' }, 404);
    })();
    return true;
  };

  return {
    handler, stats,
    /** (re)start the scripted order: scenario making | pending | ready | review, with `eyes` eyes, `made` of them made already */
    setOrder({ scenario = 'making', eyes = 3, made = 0, pendingMs = 20000 } = {}) {
      order.state = scenario; order.eyes = eyes; order.made = new Set(Array.from({ length: made }, (_, i) => i + 1)); order.pendingUntil = Date.now() + pendingMs;
      if (scenario === 'ready') order.made = new Set(Array.from({ length: eyes }, (_, i) => i + 1));
    },
    /** the picture the stand-in sends as the display copy of the first style, as a data URL (to see that the page shows that picture and no other) */
    restoredDataUrl: `data:image/jpeg;base64,${restored}`,
    secondDataUrl: `data:image/jpeg;base64,${second}`,
    /** the ids of the three styles the stand-in offers, from the registry: [the plain one that is live, a live art style, one that opens soon] */
    ids, slugs: { first: first[1].slug, second: second_[1].slug, soon: soon[1].slug },
  };
}
