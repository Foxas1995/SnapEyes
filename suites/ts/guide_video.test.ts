// The guide video (2026-10-22, the owner: "our explanation is not good ... the clearer the better, sales depend on it"): our own animated guide to photographing an eye,
// no voice, its words burnt in, one square file per language of the site in public/assets/howto, shown on the capture screen of /try and in the first step of the
// landing's "How it works" (one file, cached for both; the 9:16 cut is delivered for phones full screen and social posts and is not on the site). Made outside the
// repository from an HTML composition (suites/baseline.md section 50 says where and how). What can be decided without a browser: the files (every language, small
// enough for a phone, a poster beside each at the size the pages declare, the moov box before the media data so that a browser can start at once, no sound track),
// the words of the one button in every language, and that both pages ask for the page language's file. The browser half: check:motion:flow (guide, reduced) and
// check:landing (guide).
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { LANGS } from '../../src/shared/lang';
import { COPY } from '../../src/try/copy';

type Row = [string, boolean, string?];
const read = (p: string) => readFileSync(p, 'utf8').replace(/\r\n/g, '\n');

/** The top level boxes of an MP4 file: [type, size] in order. */
function boxes(buf: Buffer): Array<[string, number]> {
  const out: Array<[string, number]> = [];
  for (let at = 0; at + 8 <= buf.length;) {
    let size = buf.readUInt32BE(at);
    const type = buf.toString('latin1', at + 4, at + 8);
    if (size === 1) size = Number(buf.readBigUInt64BE(at + 8));
    if (size < 8) break;
    out.push([type, size]);
    at += size;
  }
  return out;
}

/** The track handlers of an MP4 file ('vide', 'soun'): every hdlr box inside the moov box. */
function handlers(buf: Buffer): string[] {
  const out: string[] = [];
  for (let i = buf.indexOf('hdlr', 0, 'latin1'); i >= 0; i = buf.indexOf('hdlr', i + 4, 'latin1')) out.push(buf.toString('latin1', i + 12, i + 16));
  return out;
}

/** Width and height of a baseline or progressive JPEG (its first SOF marker). */
function jpegSize(buf: Buffer): [number, number] | null {
  if (buf[0] !== 0xff || buf[1] !== 0xd8) return null;
  for (let at = 2; at + 9 < buf.length;) {
    if (buf[at] !== 0xff) return null;
    const m = buf[at + 1];
    const len = buf.readUInt16BE(at + 2);
    if (m >= 0xc0 && m <= 0xcf && m !== 0xc4 && m !== 0xc8 && m !== 0xcc) return [buf.readUInt16BE(at + 7), buf.readUInt16BE(at + 5)];
    at += 2 + len;
  }
  return null;
}

// the cut as the pages declare it (src/try/TryApp.tsx, src/landing/HowItWorks.tsx): the poster's width and height, and the most bytes a file may weigh
// (version 5 of 2026-10-22 is 42 s with camera moves instead of 28.7 s: the owner's limit is about 0.8 MB)
const CUT = { w: 720, h: 720, max: 800_000 };

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);

  const rows = LANGS.map((l) => {
    const v = readFileSync(`public/assets/howto/howto-11-${l}.mp4`), p = readFileSync(`public/assets/howto/howto-11-${l}.jpg`);
    const types = boxes(v).map((x) => x[0]);
    return { l, bytes: v.length, ftyp: types[0] === 'ftyp', fast: types.indexOf('moov') >= 0 && types.indexOf('moov') < types.indexOf('mdat'), tracks: handlers(v), poster: jpegSize(p), posterBytes: statSync(`public/assets/howto/howto-11-${l}.jpg`).size };
  });
  check(`a video file for every language of the site, an MP4 whose moov box comes before its media data (a browser can start at once), at most ${CUT.max} bytes`,
    rows.every((r) => r.ftyp && r.fast && r.bytes > 50_000 && r.bytes <= CUT.max), JSON.stringify(rows.map((r) => [r.l, r.bytes, r.fast])));
  check('a picture track and no sound track (it plays muted; no music, no voice)', rows.every((r) => r.tracks.includes('vide') && !r.tracks.includes('soun')), JSON.stringify(rows.map((r) => [r.l, r.tracks])));
  check(`a poster beside each file at the size the pages declare (${CUT.w} x ${CUT.h}: the box is held before it loads), under 80 kB`,
    rows.every((r) => r.poster !== null && r.poster[0] === CUT.w && r.poster[1] === CUT.h && r.posterBytes < 80_000), JSON.stringify(rows.map((r) => [r.l, r.poster, r.posterBytes])));
  check('the site carries only the files the pages ask for: the video and its poster in every language, nothing else in public/assets/howto',
    readdirSync('public/assets/howto').sort().join() === LANGS.flatMap((l) => [`howto-11-${l}.jpg`, `howto-11-${l}.mp4`]).sort().join(), readdirSync('public/assets/howto').join());

  // both pages ask for the page language's file, with the size of the poster
  const tryApp = read('src/try/TryApp.tsx'), how = read('src/landing/HowItWorks.tsx');
  const call = (head: string) => new RegExp(`<GuideVideo ${head}src=\\{\`/assets/howto/howto-11-\\$\\{lang\\}\\.mp4\`\\} poster=\\{\`/assets/howto/howto-11-\\$\\{lang\\}\\.jpg\`\\} w=\\{720\\} h=\\{720\\}`);
  check('/try: the capture screen shows the guide in the page\'s language above the steps, at most 40 percent of the window tall (the photo button stays on the first screen)',
    call('key=\\{lang\\} ').test(tryApp) && tryApp.indexOf('<GuideVideo') < tryApp.indexOf('data-testid="capture-guide"') && tryApp.includes("width: 'min(100%, 40vh)'") && !/CaptureDiagram/.test(tryApp));
  check('the landing: the first step of "How it works" shows the guide in the page\'s language instead of the camera phone (the owner: it showed the eye far too close)',
    call('').test(how) && !/kind="camera"/.test(how) && !/lp-cam/.test(read('src/landing/css/how.css')));

  // the one button says what it does, in every language, on both pages
  const landing = Object.fromEntries(LANGS.map((l) => [l, JSON.parse(readFileSync(`src/landing/copy/${l}.json`, 'utf8')).how]));
  check('the button of the guide says what it does in every language (play, pause), the same words on /try and on the landing, and no language borrows the English',
    LANGS.every((l) => COPY[l].capture.videoPlay && COPY[l].capture.videoPause && COPY[l].capture.videoPlay !== COPY[l].capture.videoPause
      && landing[l].videoPlay === COPY[l].capture.videoPlay && landing[l].videoPause === COPY[l].capture.videoPause)
    && LANGS.filter((l) => l !== 'en').every((l) => COPY[l].capture.videoPlay !== COPY.en.capture.videoPlay && COPY[l].capture.videoPause !== COPY.en.capture.videoPause),
    JSON.stringify(LANGS.map((l) => [l, COPY[l].capture.videoPlay, landing[l].videoPlay])));
  check('the camera phone\'s "2x" left the landing copy with the drawing that used it (no unused key in any language)', LANGS.every((l) => !('phoneZoom' in landing[l])));
  return out;
}
