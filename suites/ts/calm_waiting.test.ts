// The owner's phone test of 2026-11-26 (calm): the waiting screens show finished artworks (src/try/Slideshow.tsx), and the result screen has less text around the
// price (src/try/ResultView.tsx, BuyCard.tsx, Words.tsx, Feedback.tsx). Pure page code and the page's source, loaded through Vite's module runner by
// scripts/run_ts_tests.mjs; returns its results.
import { readFileSync, statSync, existsSync } from 'node:fs';
import { SLIDES, SHOW_MS, slideUrl } from '../../src/try/Slideshow';
import { ASSET_HASH } from '../../src/landing/assets';
import { QUOTA_SHOW_AT } from '../../src/try/ResultView';
import { T, setCopyLang } from '../../src/try/copy';

type Row = [string, boolean, string?];

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);
  const LANGS = ['en', 'de', 'lt', 'hu', 'hr', 'fi', 'et', 'lv'] as const;
  const DASH = new RegExp('[' + String.fromCharCode(0x2013, 0x2014) + ']');

  // ---- the slideshow
  const rows = SLIDES.map(([name, hash], i) => {
    const file = `public${slideUrl(i)}`;
    const known = (ASSET_HASH as Record<string, readonly [string, number, number, number]>)[`art/${name}`];
    return { name, ok: !!known && known[0] === hash && existsSync(file), bytes: existsSync(file) ? statSync(file).size : 0, w: known?.[1] ?? 0 };
  });
  check('6 to 8 pictures, each one of the landing\'s own example artworks (its file and content hash), 480 px webp, at most 40 KB',
    rows.length >= 6 && rows.length <= 8 && rows.every((r) => r.ok && r.w === 480 && r.bytes > 0 && r.bytes <= 40_960), JSON.stringify(rows.map((r) => [r.name, r.ok, r.bytes])));
  const styles = new Set(SLIDES.map(([n]) => n.replace(/^duo_/, 'duo ').split('_')[0]));
  check('different styles, a pair among them', styles.size >= 6 && SLIDES.some(([n]) => n.startsWith('duo_')), [...styles].join());
  check('about 4 s a picture', SHOW_MS >= 3500 && SHOW_MS <= 5000);
  const lines = LANGS.map((l) => { setCopyLang(l); return T.working.slidesLine; });
  setCopyLang('en');
  check('one short line in every language (at most 7 words, no dash, no AI word), none borrowed from English',
    lines.every((x) => typeof x === 'string' && x.split(/\s+/).length <= 7 && !DASH.test(x) && !/\b(AI|DI|KI|MI|UI|TI|TEK)\b/.test(x)) && lines.slice(1).every((x) => x !== lines[0]), lines.join(' | '));
  const show = readFileSync('src/try/Slideshow.tsx', 'utf8');
  check('nothing loads before the first analysis has left the page, one picture at a time, decoded off the main thread, a picture that fails is skipped',
    show.includes('await afterSent();') && show.includes("img.decoding = 'async';") && show.includes('await img.decode();') && show.includes('next = load(at);')
      && /catch \{\s*return null;/.test(show));
  check('reduced motion: one still picture, no fade, no zoom', show.includes("matchMedia?.('(prefers-reduced-motion: reduce)')") && show.includes('if (still) { at = shown; return; }')
    && show.includes('if (still) return;'));
  check('no label on the pictures (alt is empty, the line is outside the square), the square reserved', show.includes('alt=""') && !/Pavyzdys|Vizualizacija|Example|Sample/.test(show.replace(/\/\/.*$/gm, '').replace(/\/\*[\s\S]*?\*\//g, ''))
    && show.includes('style={{ width: size, height: size }}'));
  const app = readFileSync('src/try/TryApp.tsx', 'utf8');
  check('the page opens the gate right after it sends /api/analyze, and one element serves both waiting steps (the show goes on from analysing to restoring)',
    app.includes("if (path === '/api/analyze') analyzeSent();") && (app.match(/<Slideshow /g) ?? []).length === 1 && app.includes("(step === 'analyzing' || step === 'processing') && <Slideshow"));

  // ---- the result screen around the price
  const rv = readFileSync('src/try/ResultView.tsx', 'utf8');
  check('no line under the two buttons while another eye fits; the free previews shown only from 2 left',
    !rv.includes('T.result.addHint(') && QUOTA_SHOW_AT === 2 && rv.includes('p.quota.left <= QUOTA_SHOW_AT'));
  const opens = LANGS.map((l) => { setCopyLang(l); return T.picker.names.open; });
  setCopyLang('en');
  check('the words\' one button in every language, short, starting with "+"', opens.every((x) => x.startsWith('+ ') && x.split(/\s+/).length <= 6 && !DASH.test(x)), opens.join(' | '));
  const fb = readFileSync('src/try/Feedback.tsx', 'utf8');
  check('the feedback box under the result: the heading and the chips, no paragraph (the retake box keeps its line)', fb.includes("{where !== 'result' && <p className=\"text-[11px] text-zinc-400\">{F.hint[where]}</p>}"));
  return out;
}
