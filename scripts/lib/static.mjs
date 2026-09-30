// A static server for a Vite build (dist/) that behaves like the site's Vercel deployment: cleanUrls (/terms serves
// terms.html), the headers of vercel.json, brotli or gzip for text files. For the checks only (scripts/legal_look.mjs,
// scripts/check_headers.mjs, scripts/measure_landing.mjs); never used in production.
import { createServer } from 'node:http';
import { readFileSync, existsSync, statSync } from 'node:fs';
import { extname, join, normalize, sep } from 'node:path';
import { brotliCompressSync, gzipSync, constants } from 'node:zlib';

const TYPES = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml', '.webp': 'image/webp', '.avif': 'image/avif', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
  '.woff2': 'font/woff2', '.txt': 'text/plain; charset=utf-8', '.xml': 'application/xml', '.ico': 'image/x-icon',
};
const COMPRESSIBLE = new Set(['.html', '.js', '.css', '.json', '.svg', '.txt', '.xml']);

/** vercel.json "source" (path-to-regexp) as a RegExp: (.*) any path, :name(regex) that regex, :name one segment. */
export function sourceToRegExp(source) {
  let s = '';
  for (let i = 0; i < source.length;) {
    const rest = source.slice(i);
    const named = /^:[A-Za-z_]\w*/.exec(rest);
    if (named) {
      i += named[0].length;
      if (source[i] === '(') {
        const group = balanced(source.slice(i));
        s += group;
        i += group.length;
      } else s += '[^/]+';
    } else if (rest[0] === '(') {
      const group = balanced(rest);
      s += group;
      i += group.length;
    } else {
      s += rest[0].replace(/[.*+?^${}|[\]\\]/g, '\\$&');
      i += 1;
    }
  }
  return new RegExp(`^${s}$`);
}

// the parenthesised group at the start of text, with its nested groups: "(a(b)c)d" gives "(a(b)c)"
function balanced(text) {
  let depth = 0;
  for (let j = 0; j < text.length; j++) {
    if (text[j] === '\\') { j++; continue; }
    if (text[j] === '(') depth++;
    if (text[j] === ')' && --depth === 0) return text.slice(0, j + 1);
  }
  throw new Error(`unbalanced group in ${text}`);
}

/** The headers vercel.json gives a path (every matching rule, later rules win). */
export function headersFor(vercel, pathname) {
  const out = {};
  for (const rule of vercel.headers || []) {
    if (sourceToRegExp(rule.source).test(pathname)) for (const h of rule.headers) out[h.key.toLowerCase()] = h.value;
  }
  return out;
}

export function serve(dir, { port = 0, vercelFile, compress = true } = {}) {
  let vercel = { cleanUrls: true };
  try { vercel = JSON.parse(readFileSync(vercelFile || join(dir, '..', 'vercel.json'), 'utf8')); } catch { /* no vercel.json next to the build: clean URLs, no headers */ }
  const cache = new Map();
  const server = createServer((req, res) => {
    let pathname = decodeURIComponent((req.url || '/').split('?')[0]);
    if (pathname.endsWith('/')) pathname += 'index.html';
    let file = normalize(join(dir, pathname));
    if (!file.startsWith(normalize(dir) + sep) && file !== normalize(dir)) { res.writeHead(403).end(); return; }
    if (!existsSync(file) || statSync(file).isDirectory()) {
      if (vercel.cleanUrls && !extname(pathname) && existsSync(`${file}.html`)) file = `${file}.html`;
      else { res.writeHead(404, { 'content-type': 'text/plain' }).end('not found'); return; }
    }
    const ext = extname(file);
    const headers = { 'content-type': TYPES[ext] || 'application/octet-stream', ...headersFor(vercel, pathname) };
    if (!headers['cache-control']) headers['cache-control'] = 'public, max-age=0, must-revalidate';
    let body = readFileSync(file);
    const accept = String(req.headers['accept-encoding'] || '');
    if (compress && COMPRESSIBLE.has(ext) && body.length > 256) {
      const enc = /\bbr\b/.test(accept) ? 'br' : /\bgzip\b/.test(accept) ? 'gzip' : '';
      if (enc) {
        const key = `${enc}:${file}:${body.length}`;
        if (!cache.has(key)) cache.set(key, enc === 'br' ? brotliCompressSync(body, { params: { [constants.BROTLI_PARAM_QUALITY]: 5 } }) : gzipSync(body, { level: 6 }));
        body = cache.get(key);
        headers['content-encoding'] = enc;
        headers.vary = 'Accept-Encoding';
      }
    }
    headers['content-length'] = body.length;
    res.writeHead(200, headers);
    res.end(req.method === 'HEAD' ? undefined : body);
  });
  return new Promise((resolve) => server.listen(port, '127.0.0.1', () => resolve({ server, port: server.address().port, close: () => new Promise((r) => server.close(r)) })));
}
