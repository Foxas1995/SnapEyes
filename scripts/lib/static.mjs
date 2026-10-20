// A static server for a Vite build (dist/) that behaves like the site's Vercel deployment: cleanUrls (/terms serves
// terms.html), the rewrites of vercel.json, the headers of vercel.json, brotli or gzip for text files. For the checks only
// (scripts/legal_look.mjs, scripts/check_headers.mjs, scripts/measure_landing.mjs); never used in production.
//
// The order of Vercel's routing, as the CLI's own build output has it (.vercel/output/config.json, read on 2026-10-20): the redirects of
// cleanUrls (a path that ends in .html, or in /index, is a 308 to its clean path), then the FILE SYSTEM, then the rewrites of vercel.json
// in the order they are written (a rewrite is only tried when no file answers the path, so a file for / would shadow every rewrite for /),
// each with its `has` conditions; a rewrite's destination is looked up again (a file under its clean path), and a destination that ends in
// .html would be caught by the cleanUrls redirect, so here it is answered with that 308 and a check sees it.
import { createServer } from 'node:http';
import { readFileSync, existsSync, statSync } from 'node:fs';
import { extname, join, normalize, sep } from 'node:path';
import { brotliCompressSync, gzipSync, constants } from 'node:zlib';

const TYPES = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml', '.webp': 'image/webp', '.avif': 'image/avif', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
  '.woff2': 'font/woff2', '.txt': 'text/plain; charset=utf-8', '.xml': 'application/xml', '.ico': 'image/x-icon', '.webmanifest': 'application/manifest+json',
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

/** The destination of the first rewrite of vercel.json that answers (pathname, query), or null. Only the conditions the site uses are known: `has` of
 *  type query; any other condition, a missing list or a :placeholder in a destination stops with an error, so that the emulation never answers
 *  a rule it does not understand. A query value is matched as a whole (a string is the pattern). */
export function rewriteFor(vercel, pathname, query) {
  for (const rule of vercel.rewrites || []) {
    if (!sourceToRegExp(rule.source).test(pathname)) continue;
    if (rule.missing) throw new Error(`static.mjs: a rewrite with "missing" is not emulated (${rule.source})`);
    if (/:[A-Za-z_]/.test(rule.destination)) throw new Error(`static.mjs: a rewrite destination with a :placeholder is not emulated (${rule.destination})`);
    let ok = true;
    for (const h of rule.has || []) {
      if (h.type !== 'query') throw new Error(`static.mjs: a rewrite condition of type ${h.type} is not emulated (${rule.source})`);
      const v = query.get(h.key);
      if (v === null || (h.value !== undefined && !new RegExp(`^(?:${h.value})$`).test(v))) { ok = false; break; }
    }
    if (ok) return rule.destination;
  }
  return null;
}

/** The file a path is answered from, as the file system of the deployment: the file itself, a directory's index.html, or with cleanUrls the .html of an
 *  extension-less path. Null when there is none. */
function fileFor(dir, vercel, pathname) {
  const p = pathname.endsWith('/') ? `${pathname}index.html` : pathname;
  const file = normalize(join(dir, p));
  if (!file.startsWith(normalize(dir) + sep) && file !== normalize(dir)) return null;
  if (existsSync(file) && !statSync(file).isDirectory()) return file;
  if (vercel.cleanUrls && !extname(p) && existsSync(`${file}.html`)) return `${file}.html`;
  return null;
}

export function serve(dir, { port = 0, vercelFile, compress = true, handler } = {}) {
  let vercel = { cleanUrls: true };
  try { vercel = JSON.parse(readFileSync(vercelFile || join(dir, '..', 'vercel.json'), 'utf8')); } catch { /* no vercel.json next to the build: clean URLs, no headers */ }
  const cache = new Map();
  const server = createServer((req, res) => {
    // a check may answer some requests itself (a stub of /api/health and /api/checkout): handler(req, res) returns true when it did
    if (handler && handler(req, res)) return;
    const [rawPath, rawQuery = ''] = (req.url || '/').split('?');
    const pathname = decodeURIComponent(rawPath);
    if (pathname.split('/').includes('..')) { res.writeHead(403).end(); return; }
    let file = fileFor(dir, vercel, pathname);
    if (!file) {
      // no file answers: the rewrites of vercel.json, then the answer of what they name
      const dest = rewriteFor(vercel, pathname, new URLSearchParams(rawQuery));
      if (dest !== null && vercel.cleanUrls && /\.html$/.test(dest)) {
        // the cleanUrls redirect (^/(.*)\.html/?$, 308) would catch it
        res.writeHead(308, { location: dest.slice(0, -5) || '/' }).end();
        return;
      }
      file = dest !== null ? fileFor(dir, vercel, dest) : null;
      if (!file) {
        // Vercel answers a path nothing serves with the project's 404.html (status 404), or its own page when there is none
        const nf = fileFor(dir, vercel, '/404');
        if (nf) { const body = readFileSync(nf); res.writeHead(404, { 'content-type': TYPES['.html'], 'content-length': body.length, 'cache-control': 'public, max-age=0, must-revalidate' }); res.end(req.method === 'HEAD' ? undefined : body); return; }
        res.writeHead(404, { 'content-type': 'text/plain' }).end('not found');
        return;
      }
    }
    const ext = extname(file);
    const headers = { 'content-type': TYPES[ext] || 'application/octet-stream', ...headersFor(vercel, pathname) };
    if (!headers['cache-control']) headers['cache-control'] = 'public, max-age=0, must-revalidate';
    let body = readFileSync(file);
    const accept = String(req.headers['accept-encoding'] || '');
    if (compress && COMPRESSIBLE.has(ext) && body.length > 256) {
      const enc = /\bbr\b/.test(accept) ? 'br' : /\bgzip\b/.test(accept) ? 'gzip' : '';
      if (enc) {
        // the key holds the modification time: a rebuild gives index.html another content of the same length (the hashes in it)
        const key = `${enc}:${file}:${statSync(file).mtimeMs}:${body.length}`;
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
