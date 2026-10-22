// The language switch in the middle of the capture flow of /try (QA of 2026-10-20): the server's own sentences (api/analyze.py: the quality message and the tips) and the preview
// watermark of the restoration (api/enhance.py draws it into the pixels of the display copy, in the language of the request) stayed in the old language after the visitor switched
// the page's language during the quality step, while the analysis ran, or while the restoration ran.
//   npm run build && node scripts/check_lang_switch.mjs [--dist dist]        real Chrome on the built page, the stand-in API of scripts/lib/flowstub.mjs, four languages
// For each of the four languages as the start (and the next one, then the one after it, as the target), on a phone:
//   quality   a shot whose circle did not lock stops at the quality step (since 2026-10-22 a usable shot, a middling one included, goes straight on: the step shows the one
//             line of a shot the studio cannot restore, no tips); its message is in the page's language; a switch changes it at once (the words come with the analysis in every
//             language, quality.words), twice in a row, and nothing of the old language is left
//   analysis  a switch while the analysis runs (the answer was asked for in the old language): the quality step, when it comes, speaks the new one
//   marks     (a middling shot, which goes straight to the restoration) a switch after the restoration asks the server for the display copy again in the new language (/api/enhance {redisplay}, one call per switch, in that language, with the
//             sealed preview, and the picture on screen is the new one), and never when the language has not changed
//   running   a switch while the restoration runs: the answer comes in the old language (wm), the page asks for it again in the new one, once
// The stand-in does not draw a watermark: it answers the display copy of the other language with another picture, which the check sees on screen.
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { launch, sleep } from './lib/cdp.mjs';
import { serve } from './lib/static.mjs';
import { flowApi } from './lib/flowstub.mjs';

const ROOT = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const args = process.argv.slice(2);
const dist = resolve(args.includes('--dist') ? args[args.indexOf('--dist') + 1] : join(ROOT, 'dist'));
const PHOTO = join(ROOT, 'public', 'assets', 'sample_eye_blue_1789706902835.jpg');
const LANGS = ['en', 'de', 'lt', 'hu'];
const problems = [];
let n = 0;
const fail = (c, m) => { problems.push(`${c}: ${m}`); console.log(`  FAIL ${c}: ${m}`); };
const ok = (c, cond, m) => { n++; if (!cond) fail(c, m); return !!cond; };

const api = flowApi(ROOT, { wait: { analyze: 300, deglare: 300, enhance: 400, compose: 300, tile: 150 } });
api.setSentences(true);
const site = await serve(dist, { vercelFile: join(ROOT, 'vercel.json'), handler: api.handler });
const origin = `http://127.0.0.1:${site.port}`;
const chrome = await launch();

const waitFor = async (page, expr, ms = 20000) => {
  const t0 = Date.now();
  for (;;) {
    let v = false;
    try { v = await page.eval(expr); } catch { /* the page is busy */ }
    if (v) return true;
    if (Date.now() - t0 > ms) return false;
    await sleep(60);
  }
};
async function setFile(page, selector, path) {
  const { root } = await page.send('DOM.getDocument', { depth: 0 });
  const { nodeId } = await page.send('DOM.querySelector', { nodeId: root.nodeId, selector });
  await page.send('DOM.setFileInputFiles', { files: [path], nodeId });
}
async function open(lang) {
  const wipe = await chrome.page({ width: 400, height: 300 });
  await wipe.goto(`${origin}/imprint?lang=en`);
  await wipe.loaded();
  await wipe.send('Storage.clearDataForOrigin', { origin, storageTypes: 'all' }).catch(() => undefined);
  await wipe.close();
  const page = await chrome.page({ width: 390, height: 844, mobile: true, dpr: 1 });
  await page.goto(`${origin}/try?lang=${lang}`);
  await page.loaded();
  await waitFor(page, "!!document.querySelector('input[type=file][multiple]')");
  await sleep(2600);       // the capture screen has finished its own entrance
  return page;
}
const text = (page) => page.eval('document.body.innerText');
const switchTo = (page, l) => page.eval(`(() => { const b = document.querySelector('header button[lang="${l}"]'); if (!b) return false; b.click(); return true; })()`);
// the quality step shows the server's one line of a shot it cannot use, no tips (2026-10-22): the message alone carries the language
const marks = (l) => [`Message [${l}]`];
/** does the quality step say exactly the sentences of language l, and nothing of the other three? */
async function says(page, l, ms = 6000) {
  const want = marks(l);
  const good = await waitFor(page, `(() => { const t = document.body.innerText; return ${JSON.stringify(want)}.every((w) => t.includes(w)); })()`, ms);
  const t = await text(page);
  const stale = LANGS.filter((x) => x !== l).flatMap((x) => marks(x)).filter((w) => t.includes(w));
  return { good, stale };
}
const calls = () => api.stats.enhance.filter((c) => c.redisplay).map((c) => c.lang);

try {
  for (let i = 0; i < LANGS.length; i++) {
    const [a, b, c] = [LANGS[i], LANGS[(i + 1) % 4], LANGS[(i + 2) % 4]];
    const tag = `${a} -> ${b} -> ${c}`;

    // ---- the quality step
    api.stats.enhance.length = 0; api.setShot('unlocked'); api.setWait({ analyze: 300 });
    let page = await open(a);
    await setFile(page, 'input[type=file][multiple]', PHOTO);
    let r = await says(page, a);
    ok('quality', r.good && !r.stale.length, `${tag}: the quality step does not speak ${a} (${JSON.stringify(r)})`);
    await switchTo(page, b);
    r = await says(page, b);
    ok('quality', r.good && !r.stale.length, `${tag}: after the switch to ${b} the message is not ${b} (${JSON.stringify(r)})`);
    await switchTo(page, c);
    r = await says(page, c);
    ok('quality', r.good && !r.stale.length, `${tag}: after the second switch to ${c} the message is not ${c} (${JSON.stringify(r)})`);
    ok('quality', calls().length === 0, `${tag}: a switch in the quality step asked the server for something (${calls()})`);
    await page.close();

    // ---- a switch while the analysis runs (the request left in `a`)
    api.setWait({ analyze: 2200 });
    page = await open(a);
    await setFile(page, 'input[type=file][multiple]', PHOTO);
    await sleep(500);
    await switchTo(page, b);
    r = await says(page, b, 9000);
    ok('analysis', r.good && !r.stale.length, `${tag}: a switch while the analysis ran: the quality step is not ${b} (${JSON.stringify(r)})`);
    await page.close();

    // ---- the watermark after the restoration
    api.setShot('ok'); api.setWait({ analyze: 300, enhance: 400 }); api.stats.enhance.length = 0;
    page = await open(a);
    await setFile(page, 'input[type=file][multiple]', PHOTO);
    const arrived = await waitFor(page, "!!document.querySelector('[data-testid=artwork]')", 30000);
    ok('marks', arrived, `${tag}: the flow did not reach the result`);
    if (arrived) {
      ok('marks', api.stats.enhance.filter((x) => !x.redisplay).map((x) => x.lang).join() === a, `${tag}: the restoration was asked for in ${api.stats.enhance.map((x) => x.lang)}, expected ${a}`);
      await sleep(1500);
      ok('marks', calls().length === 0, `${tag}: the picture was asked for again with no switch (${calls()})`);
      await switchTo(page, b);
      const gotB = await (async () => { for (let k = 0; k < 100; k++) { if (calls().includes(b)) return true; await sleep(60); } return false; })();
      ok('marks', gotB && calls().filter((x) => x === b).length === 1, `${tag}: after the switch to ${b} the display copy was asked for ${calls().filter((x) => x === b).length} times in ${b} (${calls()})`);
      ok('marks', await waitFor(page, `[...document.querySelectorAll('img')].some((i) => i.src.startsWith(${JSON.stringify((b === 'en' ? api.restoredDataUrl : api.secondDataUrl).slice(0, 160))}))`, 8000), `${tag}: the picture of ${b} is not on screen after the switch`);
      await switchTo(page, c);
      const gotC = await (async () => { for (let k = 0; k < 100; k++) { if (calls().includes(c)) return true; await sleep(60); } return false; })();
      ok('marks', gotC && calls().length === 2 && calls()[1] === c, `${tag}: after the second switch the calls are ${calls()}, expected one in ${b} then one in ${c}`);
      ok('marks', await waitFor(page, `[...document.querySelectorAll('img')].some((i) => i.src.startsWith(${JSON.stringify((c === 'en' ? api.restoredDataUrl : api.secondDataUrl).slice(0, 160))}))`, 8000), `${tag}: the picture of ${c} is not on screen`);
      // the same language again is no change
      await switchTo(page, c);
      await sleep(900);
      ok('marks', calls().length === 2, `${tag}: pressing the language that is already on asked again (${calls()})`);
    }
    await page.close();

    // ---- a switch while the restoration runs
    api.setWait({ analyze: 300, enhance: 2500 }); api.stats.enhance.length = 0;
    page = await open(a);
    await setFile(page, 'input[type=file][multiple]', PHOTO);
    await waitFor(page, "!!document.querySelector('.wk-disc')", 10000);
    await sleep(900);
    await switchTo(page, b);
    const done = await waitFor(page, "!!document.querySelector('[data-testid=artwork]')", 40000);
    ok('running', done, `${tag}: the flow did not reach the result`);
    if (done) {
      const got = await (async () => { for (let k = 0; k < 100; k++) { if (calls().includes(b)) return true; await sleep(60); } return false; })();
      ok('running', got && api.stats.enhance.filter((x) => !x.redisplay).map((x) => x.lang).join() === a && calls().join() === b, `${tag}: restoration asked in ${api.stats.enhance.filter((x) => !x.redisplay).map((x) => x.lang)}, the picture again in ${calls()}: expected ${a} then ${b}`);
    }
    await page.close();
    console.log(`  done ${tag}`);
  }
} finally {
  await chrome.close();
  await site.close();
}
if (problems.length) {
  console.error(`language switch check FAILED (${problems.length} of ${n}):\n  ${problems.join('\n  ')}`);
  process.exit(1);
}
console.log(`language switch check ok: ${n} checks, four languages as the start, in the quality step, during the analysis, after and during the restoration`);
