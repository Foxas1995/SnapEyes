// The live camera inside /try (?cam=1, 2026-11-26; src/try/livecam): the pure parts. When it is on (the address, then the tab's sessionStorage),
// whether the browser can try at all, the zoom choice (the track's own 2x when it reaches it, otherwise our 2x crop), the crop, how a failure is
// classed (each class gives way to the capture input), the anonymous codes (a megapixel class, never the size) and the owner's plain line; the
// page wiring (lazy chunk, fallback to the capture input, the codes on the beacon and the analysis); the server's side of the codes (api/_lib/events.py
// CAPTURE). Loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results.
import { readFileSync } from 'node:fs';
import {
  BURST, CAM_KEY, DARK_LUMA, INAPP_BOTTOM, INAPP_TOP, MAX_TAKES, camOn, centreCrop, chooseStill, chooseZoom, circleCentre, debugLine, failClass, inApp, liveCap, liveSupported,
  meanLuma, photoSettings, resClass, stillVerdict, takeBurst, tooDark, viewInsets, zoomCode,
} from '../../src/try/livecam/logic';
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

  const z = [chooseZoom({ zoom: { min: 1, max: 10 } }), chooseZoom({ zoom: { min: 1, max: 2 } }), chooseZoom({ zoom: { min: 1, max: 1.5 } }), chooseZoom({}), chooseZoom(null), chooseZoom({ zoom: { min: 2.5, max: 8 } }),
    chooseZoom({ zoom: { min: 1, max: 2.6 } }), chooseZoom({}, 12e6), chooseZoom({}, 8e6), chooseZoom({ zoom: { max: 1.5 } }, 12e6)];
  check('the zoom (2026-11-26, 3x where it is real): the track own up to 3x from a max of 2 (never above its max, never under its min); our crop 3x only on a still of about 12 MP, 2x otherwise',
    z[0].mode === 'track' && z[0].value === 3 && z[1].mode === 'track' && z[1].value === 2 && z[2].mode === 'css' && z[3].mode === 'css' && z[4].mode === 'css'
      && z.slice(2, 5).every((x) => x.value === 2) && z[5].mode === 'track' && z[5].value === 3 && z[6].value === 2.6 && z[7].mode === 'css' && z[7].value === 3
      && z[8].value === 2 && z[9].mode === 'css' && z[9].value === 3 && zoomCode(2) === 'z2' && zoomCode(2.6) === 'z3' && zoomCode(3) === 'z3', JSON.stringify(z));
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
  const geo = { vvH: 780, vvTop: 0, inner: 866, screen: 915 };
  const line = debugLine({ geo, method: 'still', video: { w: 3840, h: 2160 }, asked: { w: 4000, h: 3000 }, got: { w: 2000, h: 1500 }, zoom: 'css', zoomValue: 2, torch: true });
  const line2 = debugLine({ geo, method: null, video: { w: 2160, h: 3840 }, asked: null, got: null, zoom: 'track', zoomValue: 2, torch: false });
  const line3 = debugLine({ geo, method: 'frame', video: { w: 1920, h: 1080 }, asked: null, got: { w: 960, h: 540 }, zoom: 'css', zoomValue: 2, torch: false });
  const DOT = ` ${String.fromCharCode(0xb7)} `;
  check('the owner\'s line on the camera view: the geometry the browser reports, the still asked and got (or the video, or a frame), the zoom and the light',
    line === ['vv 780/0 in 866 sc 915', 'still 4000x3000 > 2000x1500', 'zoom 2x crop', 'light yes'].join(DOT)
      && line2 === ['vv 780/0 in 866 sc 915', 'video 2160x3840', 'zoom 2x track', 'light no'].join(DOT) && line3.includes(`frame 960x540${DOT}zoom 2x crop`), `${line} | ${line2} | ${line3}`);
  const st = [chooseStill({ imageWidth: { min: 160, max: 4000 }, imageHeight: { min: 120, max: 3000 } }), chooseStill({ imageWidth: { max: 8000 }, imageHeight: { max: 6000 } }),
    chooseStill({ imageWidth: { max: 1920 }, imageHeight: { max: 1080 } }), chooseStill({}), chooseStill(null)];
  check('the still asked of ImageCapture: the largest offered, at most 4096 px long and about 12 MP, the camera\'s shape kept; none when nothing is offered',
    st[0]?.w === 4000 && st[0]?.h === 3000 && !!st[1] && st[1].w <= 4096 && st[1].w * st[1].h <= 12e6 && Math.abs(st[1].w / st[1].h - 4 / 3) < 0.01 && st[2]?.w === 1920 && st[3] === null && st[4] === null,
    JSON.stringify(st));
  const fbUa = 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/131 Mobile Safari/537.36 [FB_IAB/MESSENGER;FBAV/480.0]';
  check('the Facebook, Messenger and Instagram browsers keep the controls out of the top 72 and the bottom 100 px; Chrome and Safari do not; the circle sits in the middle of what is surely visible',
    inApp(fbUa) && inApp('Instagram 350.0 Android') && inApp('[FBAN/FBIOS;FBAV/450]') && !inApp('Mozilla/5.0 (Linux; Android 14) Chrome/131 Mobile Safari/537.36') && !inApp('iPhone Safari/604.1')
      && viewInsets(true).top === INAPP_TOP && viewInsets(true).bottom === INAPP_BOTTOM && INAPP_TOP === 72 && INAPP_BOTTOM === 100 && viewInsets(false).top === 0
      && circleCentre(866, 72, 100) === 419 && circleCentre(800, 0, 0) === 400, String(circleCentre(866, 72, 100)));
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
    app.includes("const loadCamera = () => import('./livecam/LiveCamera');") && app.includes('const LiveCamera = lazy(loadCamera);') && !/from '\.\/livecam\/LiveCamera'/.test(app)
      && app.includes('useEffect(() => { if (CAM) void loadCamera().catch(() => undefined); }, []);') && app.includes('if (CAM && !liveFailRef.current && liveSupported(navigator, window.isSecureContext))')
      && app.includes("nativeCamera(CAM ? { how: 'native', lfail: liveFailRef.current ?? 'unsupported' } : { how: 'native' })"));
  check('a failure of the live camera opens the capture input by itself, with the failure\'s class in the codes and no error text',
    app.includes("const onLiveFail = (why: LiveFail) => { liveFailRef.current = why; setLiveFail(why); setLive(false); nativeCamera({ how: 'native', lfail: why }); };") && !/onLiveFail[^\n]*setError/.test(app));
  const start = app.slice(app.indexOf('const startCamera = () => {'), app.indexOf('const onLiveFail'));
  check('the camera is asked inside the tap (getUserMedia before anything is awaited), and the view is handed the promise',
    start.includes('try { asked = navigator.mediaDevices.getUserMedia(VIDEO); }') && !/\bawait\b/.test(start) && start.indexOf('getUserMedia') < start.indexOf('setLive(true)')
      && app.includes('<LiveCamera stream={liveStreamRef.current'));
  check('?cam=1 only: the capture screen says in one small grey line why the live camera gave way on this page',
    app.includes('{CAM && liveFail && <p data-testid="cam-fail" className="text-[10px] text-zinc-400 text-center">cam: {liveFail}</p>}'));
  check('after one failure every later tap on this page goes straight to the capture input (a late programmatic open may be refused by the browser)',
    app.includes('const liveFailRef = useRef<LiveFail | null>(null);'));
  check('the burst goes into the multi-photo path of a gallery pick, as live, and the codes ride on the photo beacon and on every analysis',
    app.includes("void onFiles(files, 'live')") && app.includes("count('photo', T.lang, currentMarket(), { cap: capRef.current })") && app.includes('device: { ...deviceInfo(source), cap: capRef.current }'));
  check('the photo step is sent once per set, with the codes: by the gallery and the live burst (onFiles) and by the first shot of the capture input (94249b3)',
    app.includes("if (!shotsRef.current.length) { photoAt = Date.now(); count('photo', T.lang, currentMarket(), { cap: capRef.current }); }")
      && (app.match(/count\('photo'/g) ?? []).length === 2);
  const cam = readFileSync('src/try/livecam/LiveCamera.tsx', 'utf8');
  check('the camera view: rear camera at up to 3840 x 2160, playsInline and muted, stopped on close, on unmount and when the page is hidden; torch only when the track has one',
    readFileSync('src/try/livecam/logic.ts', 'utf8').includes("facingMode: { ideal: 'environment' }") && cam.includes('playsInline muted') && cam.includes("document.addEventListener('visibilitychange', hidden)")
      && /return \(\) => \{[^}]*stop\(\)/.test(cam) && cam.includes('{torch.has && (') && cam.includes('window.ImageCapture'));
  check('the view: the page behind locked and given back, sized from visualViewport, no pan; the largest still asked, a plain one when that fails, no crop on a real zoom',
    cam.includes("html.style.overflow = 'hidden'; body.style.overflow = 'hidden';") && cam.includes('window.scrollTo(was.x, was.y);') && cam.includes("vv?.addEventListener('scroll', fit)")
      && cam.includes("touchAction: 'none', overscrollBehavior: 'contain'") && cam.includes('size = chooseStill(pc); settings = photoSettings(size, (pc as { fillLightMode?: unknown }).fillLightMode);')
      && cam.includes('if (settings) { try { still = await ic.takePhoto(settings); } catch { settings = null; size = null; still = await ic.takePhoto(); } }')
      && cam.includes("const crop = zoom.mode === 'css' ? zoom.value : 1;") && !cam.includes('burst = Math.min(burst, 3)') && cam.includes('bmp.close();'));

  // ---- the burst keeps usable pictures only (2026-11-26: with the torch on, two burnt white and two dark stills), the darkness warning, no flash
  const px = (v: number, n = 16) => { const a = new Uint8ClampedArray(n * 4); for (let i = 0; i < n; i++) { a[i * 4] = v; a[i * 4 + 1] = v; a[i * 4 + 2] = v; a[i * 4 + 3] = 255; } return a; };
  check('the mean luma of RGBA pixels; too dark under 70; a picture over 235 is burnt, under 25 black, else usable',
    Math.round(meanLuma(px(0))) === 0 && Math.round(meanLuma(px(255))) === 255 && Math.round(meanLuma(px(100))) === 100 && DARK_LUMA === 70 && tooDark(69) && !tooDark(70)
      && stillVerdict(252) === 'burnt' && stillVerdict(10) === 'black' && stillVerdict(43) === 'ok' && stillVerdict(120) === 'ok');
  const run = async (lumas: number[]) => {
    const seen: number[] = [];
    const r = await takeBurst((i) => Promise.resolve(i < lumas.length ? { luma: lumas[i], i } : null), (k) => seen.push(k));
    return { r, seen };
  };
  const ra = await run([252, 250, 120, 10, 130, 125]);
  check('a stubbed camera giving white, white, good, black, good, good: 6 takes, the 3 good ones kept, 2 burnt and 1 black thrown away, the count never goes back',
    ra.r.takes === 6 && ra.r.kept.map((p) => p.i).join() === '2,4,5' && ra.r.burnt === 2 && ra.r.black === 1 && !ra.r.fallback && ra.seen.every((k, i) => i === 0 || k >= ra.seen[i - 1]) && Math.max(...ra.seen) <= BURST,
    JSON.stringify({ kept: ra.r.kept.map((p) => p.i), takes: ra.r.takes, seen: ra.seen }));
  const rb = await run([120, 121, 122, 123, 124, 125]);
  const rc = await run([252, 250, 249, 10, 5, 240]);
  check('four good ones: 4 takes and done; none good in 6 takes: the two closest to grey are sent anyway (the server answers something)',
    rb.r.takes === BURST && rb.r.kept.length === 4 && rb.seen.join() === '1,2,3,4' && rc.r.takes === MAX_TAKES && rc.r.fallback && rc.r.kept.length === 2 && rc.r.kept.map((p) => p.i).sort().join() === '3,5',
    JSON.stringify({ b: rb.seen, c: rc.r.kept.map((p) => p.i) }));
  check('the still asked without a flash where the camera lists fillLightMode off; the size alone, or nothing (a plain takePhoto) otherwise',
    JSON.stringify(photoSettings({ w: 4000, h: 3000 }, ['auto', 'off', 'flash'])) === JSON.stringify({ imageWidth: 4000, imageHeight: 3000, fillLightMode: 'off' })
      && JSON.stringify(photoSettings(null, ['off'])) === JSON.stringify({ fillLightMode: 'off' }) && JSON.stringify(photoSettings({ w: 10, h: 5 }, ['flash'])) === JSON.stringify({ imageWidth: 10, imageHeight: 5 })
      && photoSettings(null, undefined) === null);
  const lt = debugLine({ geo, method: 'still', video: { w: 3840, h: 2160 }, asked: { w: 4000, h: 3000 }, got: { w: 4000, h: 3000 }, takes: { n: 6, burnt: 2, black: 0 }, zoom: 'track', zoomValue: 2, torch: true });
  check('the facts line says how many takes and why some were thrown away', lt.includes(`takes 6, burnt 2${DOT}zoom 2x track`) && !lt.includes('black'), lt);
  check('the dark code at the tap rides with the burst\'s codes, and the admin reads it',
    JSON.stringify(liveCap('still', 4000, 3000, 'track', true, true)) === JSON.stringify({ how: 'live', lm: 'still', lres: 'mp12', zoom: 'track', torch: 'yes', dark: 'yes' })
      && capText({ how: 'live', dark: 'yes' }).includes('tamsu yra') && liveCap('frame', 100, 100, 'css', false, false, 3).zv === 'z3' && capText({ how: 'live', zoom: 'css', zv: 'z3' }).includes('3x'));
  check('the live tab tips: its second line says only the distance, about 15 cm (it zooms by itself); the page without ?cam=1 keeps 2x and 10 cm',
    LANGS.every((l) => { setCopyLang(l); const ok = T.capture.liveStep.includes('15') && !T.capture.liveStep.includes('10') && T.capture.steps[1].includes('10') && T.capture.steps[1].includes('2'); setCopyLang('en'); return ok; })
      && app.includes('(CAM ? T.capture.steps.map((s, i) => (i === 1 ? T.capture.liveStep : s)) : T.capture.steps)'));
  const darks = LANGS.map((l) => { setCopyLang(l); return [T.capture.liveDark, T.capture.liveBurst(4), T.capture.liveStill, T.capture.liveDone, T.capture.steps[0]]; });
  setCopyLang('en');
  check('the new words in every language: the darkness warning, the burst line with its number, hold still, done, and the mirror tip first among the four steps',
    darks.every((w) => w.every((x) => typeof x === 'string' && x.length > 1 && x.length <= 60) && w[1].includes('4')) && darks.slice(1).every((w) => w[0] !== darks[0][0] && w[4] !== darks[0][4])
      && darks[2][4].startsWith('Vienas?'), JSON.stringify(darks.map((w) => w[4])));
  const cam2 = readFileSync('src/try/livecam/LiveCamera.tsx', 'utf8');
  check('the view: the dark line replaces the second line (the shutter stays usable), the light button gets a gold ring while dark, the shutter waits after the torch is switched, the meter stops during the burst',
    cam2.includes('<p data-testid="live-dark"') && cam2.includes("${dark && !torch.on ? 'ring-2 ring-gold' : ''}") && cam2.includes('disabled={!ready || busy || settling}')
      && cam2.includes('if (!ready || busy || finished) return;') && cam2.includes('window.clearInterval(id)') && !/disabled=\{[^}]*dark/.test(cam2));

  // the server side
  const ev = readFileSync('api/_lib/events.py', 'utf8');
  check('the server keeps only the known codes (events.CAPTURE) on the photo beacon and the analysis, and the analysis puts them in the kept JSON',
    ev.includes('def capture_codes(cap):') && /for _kind in \("analyze", "hit"\):/.test(ev) && readFileSync('api/_lib/counter.py', 'utf8').includes('f.update(E.capture_codes(body.get("cap")))')
      && (readFileSync('api/analyze.py', 'utf8').match(/"cap": E\.capture_codes/g) ?? []).length === 2);
  return out;
}
