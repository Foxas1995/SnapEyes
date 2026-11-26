// The live camera inside /try (?cam=1, 2026-11-26; src/try/livecam): the pure parts. When it is on (the address, then the tab's sessionStorage),
// whether the browser can try at all, the zoom choice (the track's own 2x when it reaches it, otherwise our 2x crop), the crop, how a failure is
// classed (each class gives way to the capture input), the anonymous codes (a megapixel class, never the size) and the owner's plain line; the
// page wiring (lazy chunk, fallback to the capture input, the codes on the beacon and the analysis); the server's side of the codes (api/_lib/events.py
// CAPTURE). Loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results.
import { readFileSync } from 'node:fs';
import { CAM_KEY, camOn, centreCrop, chooseZoom, debugLine, failClass, liveCap, liveSupported, resClass } from '../../src/try/livecam/logic';
import { capText } from '../../src/admin/Previews';
import { T, setCopyLang } from '../../src/try/copy';

type Row = [string, boolean, string?];

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);

  const mem = () => { const m = new Map<string, string>(); return { getItem: (k: string) => m.get(k) ?? null, setItem: (k: string, v: string) => void m.set(k, v), removeItem: (k: string) => void m.delete(k), m }; };
  const s1 = mem();
  const on1 = camOn('?cam=1&lang=lt', s1), kept = camOn('?lang=lt', s1), off = camOn('?cam=0', s1), after = camOn('', s1);
  check('on only with ?cam=1, kept for the tab in sessionStorage, ?cam=0 turns it off, and nobody else gets it',
    on1 && kept && !off && !after && !camOn('', mem()) && !camOn('?cam=2', mem()) && camOn('?cam=1', null) && s1.m.get(CAM_KEY) === undefined,
    JSON.stringify([on1, kept, off, after]));
  const throwing = { getItem: () => { throw new Error('x'); }, setItem: () => { throw new Error('x'); }, removeItem: () => { throw new Error('x'); } };
  check('a storage that throws (a private window) still follows the address', camOn('?cam=1', throwing) && !camOn('', throwing));

  check('the browser can try only with getUserMedia on a secure page',
    liveSupported({ mediaDevices: { getUserMedia: () => 0 } }, true) && !liveSupported({ mediaDevices: { getUserMedia: () => 0 } }, false)
      && !liveSupported({}, true) && !liveSupported(undefined, true) && !liveSupported({ mediaDevices: {} }, true));

  const z = [chooseZoom({ zoom: { min: 1, max: 10 } }), chooseZoom({ zoom: { min: 1, max: 2 } }), chooseZoom({ zoom: { min: 1, max: 1.5 } }), chooseZoom({}), chooseZoom(null), chooseZoom({ zoom: { min: 2.5, max: 8 } })];
  check('the zoom: 2x on the track when its zoom reaches 2 (never above its max, never under its min), our 2x crop otherwise',
    z[0].mode === 'track' && z[0].value === 2 && z[1].mode === 'track' && z[1].value === 2 && z[2].mode === 'css' && z[3].mode === 'css' && z[4].mode === 'css'
      && z.slice(2, 5).every((x) => x.value === 2) && z[5].mode === 'track' && z[5].value === 2.5, JSON.stringify(z));
  const c = centreCrop(4000, 3000, 2), c1 = centreCrop(1920, 1080, 1);
  check('the crop of our 2x zoom is the middle half each way (and no crop at 1x)',
    c.sx === 1000 && c.sy === 750 && c.sw === 2000 && c.sh === 1500 && c1.sx === 0 && c1.sw === 1920 && c1.sh === 1080, JSON.stringify([c, c1]));

  const err = (name: string) => Object.assign(new Error(name), { name });
  const classes = ['NotAllowedError', 'SecurityError', 'NotFoundError', 'OverconstrainedError', 'TimeoutError', 'NotSupportedError', 'NotReadableError', 'AbortError'].map((n) => failClass(err(n)));
  check('a failure is classed: denied, no camera, timeout, unsupported, anything else an error (every class gives way to the capture input)',
    classes.join() === 'denied,denied,nocamera,nocamera,timeout,unsupported,error,error' && failClass(null) === 'error' && failClass('x') === 'error', classes.join());

  check('the frame size is only a class of megapixels',
    [resClass(640, 480), resClass(1280, 960), resClass(1920, 1080), resClass(2560, 1920), resClass(3840, 2160), resClass(4032, 3024), resClass(0, 0)].join() === 'mp0,mp1,mp2,mp2,mp8,mp12,mp0');
  const cap = liveCap('still', 4032, 3024, 'track', true);
  check('the codes of a burst: live, the method, the class, the zoom and the torch; nothing exact, nothing that names the device',
    JSON.stringify(cap) === JSON.stringify({ how: 'live', lm: 'still', lres: 'mp12', zoom: 'track', torch: 'yes' }), JSON.stringify(cap));
  const line = debugLine({ method: 'still', w: 4032, h: 3024, zoom: 'track', zoomValue: 2, torch: true });
  const line2 = debugLine({ method: null, w: 1920, h: 1080, zoom: 'css', zoomValue: 2, torch: false });
  check('the owner\'s line on the camera view says what his phone gave', line === 'still 4032x3024, zoom 2x, light yes' && line2 === 'video 1920x1080, zoom 2x by crop, light no', `${line} | ${line2}`);
  check('the admin reads the codes in words', capText(cap) === 'puslapio kamera, tikra nuotrauka, mp12, kameros priartinimas, šviesa yra' && capText({ how: 'native', lfail: 'denied' }) === 'telefono kamera (įvestis), gyva kamera: neleista' && capText(null) === '',
    `${capText(cap)} | ${capText({ how: 'native', lfail: 'denied' })}`);

  // the texts: the hint, the light and the shutter's label in every language, short
  const LANGS = ['en', 'de', 'lt', 'hu', 'hr', 'fi', 'et', 'lv'] as const;
  const words = LANGS.map((l) => { setCopyLang(l); return [T.capture.liveHint, T.capture.liveLight, T.capture.liveShutter, T.buy.close]; });
  setCopyLang('en');
  check('the camera view\'s words in every language: a short hint, the light, the shutter and close, none borrowed from English',
    words.every((w) => w.every((x) => typeof x === 'string' && x.length > 1 && x.length <= 40)) && words.slice(1).every((w) => w[0] !== words[0][0]), JSON.stringify(words.map((w) => w[0])));

  // the page's wiring
  const app = readFileSync('src/try/TryApp.tsx', 'utf8');
  check('/try loads the camera lazily (a chunk of its own), only with ?cam=1, and the gold button keeps the capture input for everybody else',
    /lazy\(\(\) => import\('\.\/livecam\/LiveCamera'\)\)/.test(app) && !/from '\.\/livecam\/LiveCamera'/.test(app) && app.includes('if (CAM && !liveFailRef.current && liveSupported(navigator, window.isSecureContext))')
      && app.includes("nativeCamera(CAM ? { how: 'native', lfail: liveFailRef.current ?? 'unsupported' } : { how: 'native' })"));
  check('a failure of the live camera opens the capture input by itself, with the failure\'s class in the codes and no error text',
    app.includes("const onLiveFail = (why: LiveFail) => { liveFailRef.current = why; setLive(false); nativeCamera({ how: 'native', lfail: why }); };") && !/onLiveFail[^\n]*setError/.test(app));
  check('after one failure every later tap on this page goes straight to the capture input (a late programmatic open may be refused by the browser)',
    app.includes('const liveFailRef = useRef<LiveFail | null>(null);'));
  check('the burst goes into the multi-photo path of a gallery pick, as live, and the codes ride on the photo beacon and on every analysis',
    app.includes("void onFiles(files, 'live')") && app.includes("count('photo', T.lang, currentMarket(), { cap: capRef.current })") && app.includes('device: { ...deviceInfo(source), cap: capRef.current }'));
  check('the photo step is sent once per set, with the codes: by the gallery and the live burst (onFiles) and by the first shot of the capture input (94249b3)',
    app.includes("if (!shotsRef.current.length) { photoAt = Date.now(); count('photo', T.lang, currentMarket(), { cap: capRef.current }); }")
      && (app.match(/count\('photo'/g) ?? []).length === 2);
  const cam = readFileSync('src/try/livecam/LiveCamera.tsx', 'utf8');
  check('the camera view: rear camera at up to 3840 x 2160, playsInline and muted, stopped on close, on unmount and when the page is hidden; torch only when the track has one',
    cam.includes("facingMode: { ideal: 'environment' }") && cam.includes('playsInline muted') && cam.includes("document.addEventListener('visibilitychange', hidden)")
      && /return \(\) => \{[^}]*stop\(\)/.test(cam) && cam.includes('{torch.has && (') && cam.includes('window.ImageCapture'));

  // the server side
  const ev = readFileSync('api/_lib/events.py', 'utf8');
  check('the server keeps only the known codes (events.CAPTURE) on the photo beacon and the analysis, and the analysis puts them in the kept JSON',
    ev.includes('def capture_codes(cap):') && /for _kind in \("analyze", "hit"\):/.test(ev) && readFileSync('api/_lib/counter.py', 'utf8').includes('f.update(E.capture_codes(body.get("cap")))')
      && (readFileSync('api/analyze.py', 'utf8').match(/"cap": E\.capture_codes/g) ?? []).length === 2);
  return out;
}
