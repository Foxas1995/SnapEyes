// A local viewer of the built page (dist/) that answers the two API calls the landing makes, with no Python, no Stripe and no keys:
//   npm run build
//   node scripts/serve_preview.mjs [--port 5215] [--open] [--suggest au|hu] [--dist dist]
// The page is served the way Vercel serves it (cache headers, clean URLs), so what you see is what the build is. The stub says what the
// flags say:
//   (no flag)       ordering is closed: the three "Ordering opens soon" places, "Free preview" everywhere
//   --open          ordering is open (and the owner has switched on the styles whose ceiling is live: scripts/lib/stubapi.mjs): the bar, the pricing notice and
//                   the FAQ switch to their open sentences, the tiles of those styles and the price rows show their prices, the others stay Soon
//   --suggest au    the server places the visitor in Australia (or hu: Hungary): the offer of A$ (or Ft) above the hero
// Addresses: /  /?lang=de  /?lang=lt  /?lang=hu  /?m=au (A$ prices, the Australian FAQ)  /?m=hu (forints). /try, /order and the legal pages are
// served too, but /try needs the real API to make a preview: this stub only answers /api/health and /api/checkout.
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { serve } from './lib/static.mjs';
import { checkoutAnswer } from './lib/stubapi.mjs';

const ROOT = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const args = process.argv.slice(2);
const opt = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const open = args.includes('--open');
const suggest = opt('--suggest', null);
const dist = resolve(opt('--dist', join(ROOT, 'dist')));
const port = +opt('--port', 5215);

const handler = (req, res) => {
  const url = new URL(req.url, 'http://x');
  const json = (o) => { res.writeHead(200, { 'content-type': 'application/json', 'cache-control': 'no-store' }); res.end(JSON.stringify(o)); };
  if (url.pathname === '/api/health') { json({ stripe: true, stripe_live: false, email: false }); return true; }
  if (url.pathname === '/api/checkout') { json(checkoutAnswer(ROOT, { open, suggest })); return true; }
  if (url.pathname.startsWith('/api/')) { res.writeHead(404, { 'content-type': 'application/json' }); res.end('{}'); return true; }
  return false;
};
const site = await serve(dist, { port, vercelFile: join(ROOT, 'vercel.json'), handler });
console.log(`SnapEyes landing, ordering ${open ? 'OPEN' : 'closed'}${suggest ? `, the server suggests ${suggest}` : ''}: http://127.0.0.1:${site.port}/   (Ctrl+C to stop)`);
