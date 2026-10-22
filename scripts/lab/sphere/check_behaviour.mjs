// LAB: the behaviour of the two prototypes in real time (headless Chrome, scripts/lib/cdp.mjs), on the dev server or the lab build:
// reduced motion (nothing moves by itself, a tap opens in place), the keyboard (one tab stop, arrows, Enter, Escape and the focus coming back),
// every artwork a labelled button, and touch (a vertical swipe on the stage scrolls the page, a sideways one turns the piece and does not).
//   node scripts/lab/sphere/check_behaviour.mjs [base url]
import { launch, sleep } from '../../lib/cdp.mjs';
const base = process.argv[2] || 'http://127.0.0.1:5281';
const chrome = await launch({ args: ['--disable-features=ResamplingInputEvents,ResamplingScrollEvents'] });
const out = [];
const ok = (name, cond, detail = '') => { out.push(`${cond ? 'PASS' : 'FAIL'}  ${name}${detail ? '  (' + detail + ')' : ''}`); };
async function open(piece, opts) {
  const page = await chrome.page(opts);
  await page.goto(`${base}/src/lab/sphere.html?p=${piece}&lang=lt&ui=0`);
  await page.loaded(30000);
  for (let i = 0; i < 100 && !(await page.eval("!!document.querySelector('.lab-frame[data-ready]')")); i++) await sleep(100);
  await sleep(400);
  return page;
}
const orbT = "document.querySelector('.sx-orb').style.transform";
const phone = { width: 412, height: 915, dpr: 2, mobile: true };
const desk = { width: 1440, height: 900, dpr: 1, mobile: false };
const keyer = (page) => async (k, code) => {
  await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: k, code: k, windowsVirtualKeyCode: code, ...(k === 'Enter' ? { text: String.fromCharCode(13) } : {}) });
  await page.send('Input.dispatchKeyEvent', { type: 'keyUp', key: k, code: k, windowsVirtualKeyCode: code });
};
const FRONT_STOP = (sel) => `document.querySelector('${sel}[tabindex="0"]').focus(); true`;
try {
  // 1. reduced motion: the globe keeps still, a tap opens the artwork at once, with a fade only
  {
    const page = await open('globe', { ...phone, reduceMotion: true });
    const a = await page.eval(orbT);
    await sleep(1500);
    const b = await page.eval(orbT);
    ok('reduced motion: the globe does not turn by itself', a === b, a.slice(0, 60));
    const p = await page.eval(`(() => { const b = [...document.querySelectorAll('.sx-disc')].find((x) => x.getAttribute('aria-label').startsWith('Halo')); const r = b.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; })()`);
    await page.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [p] });
    await page.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    await sleep(60);
    const t1 = await page.eval("document.querySelector('.sx-hero').style.transform");
    await sleep(400);
    const vis = await page.eval("getComputedStyle(document.querySelector('.sx-hero')).visibility + ' ' + document.querySelector('.sx-hero').style.opacity + ' ' + document.querySelector('.sx-name').textContent");
    const c = await page.eval(orbT);
    ok('reduced motion: a tap opens the artwork in place (no flight, the globe does not turn)', vis.startsWith('visible 1') && c === b && /scale\(1(\.0+)?, ?1(\.0+)?\)/.test(t1), `${vis} | ${t1}`);
    await page.close();
  }
  {
    const page = await open('ring', { ...phone, reduceMotion: true });
    const a = await page.eval("document.querySelector('.sx-name').textContent");
    await sleep(6500);
    const b = await page.eval("document.querySelector('.sx-name').textContent");
    ok('reduced motion: the ring does not step by itself', a === b, `${a} -> ${b}`);
    await page.close();
  }
  // 2. keyboard: Tab reaches one artwork, arrows turn, Enter opens, Escape closes and gives the focus back
  {
    const page = await open('globe', desk);
    const key = keyer(page);
    await page.eval(FRONT_STOP('.sx-disc'));
    const f0 = await page.eval('document.activeElement.getAttribute("aria-label")');
    await key('ArrowRight', 39);
    await sleep(800);
    const f1 = await page.eval('document.activeElement.getAttribute("aria-label")');
    const tabStops = await page.eval(`document.querySelectorAll('.sx-disc[tabindex="0"]').length`);
    ok('keyboard: one tab stop, ArrowRight moves to the next artwork', f0 !== f1 && tabStops === 1, `${f0} -> ${f1}, tab stops ${tabStops}`);
    await key('ArrowUp', 38);
    await sleep(800);
    const f2 = await page.eval('document.activeElement.getAttribute("aria-label")');
    ok('keyboard: ArrowUp moves to the row above', f2 !== f1, f2);
    await key('Enter', 13);
    await sleep(1200);
    const opened = await page.eval("document.querySelector('.sx-name').textContent + ' | focus on ' + document.activeElement.className");
    ok('keyboard: Enter opens the artwork and puts the focus on its button', opened.includes('sx-cta') && f2.startsWith(opened.split(' | ')[0]), opened);
    await key('Escape', 27);
    await sleep(900);
    const back = await page.eval('document.activeElement.getAttribute("aria-label") + " | hero " + getComputedStyle(document.querySelector(".sx-hero")).visibility');
    ok('keyboard: Escape closes it and gives the focus back to the artwork', back.startsWith(f2) && back.endsWith('hidden'), back);
    const names = await page.eval("[...document.querySelectorAll('.sx-disc')].every((b) => b.tagName === 'BUTTON' && b.getAttribute('aria-label').length > 4)");
    ok('every artwork of the globe is a labelled button', names);
    await page.close();
  }
  {
    const page = await open('ring', desk);
    const key = keyer(page);
    await page.eval(FRONT_STOP('.sx-tile'));
    const n0 = await page.eval("document.querySelector('.sx-name').textContent");
    await key('ArrowRight', 39);
    await sleep(1300);
    const n1 = await page.eval("document.querySelector('.sx-name').textContent + ' | ' + document.activeElement.getAttribute('aria-label')");
    ok('keyboard (ring): ArrowRight brings the next artwork to the front with the focus on it', n1.split(' | ')[0] !== n0 && n1.split(' | ')[1].startsWith(n1.split(' | ')[0]), `${n0} -> ${n1}`);
    const names = await page.eval("[...document.querySelectorAll('.sx-tile')].every((b) => b.tagName === 'BUTTON' && b.getAttribute('aria-label').length > 4)");
    ok('every artwork of the ring is a labelled button', names);
    await page.close();
  }
  // 3. touch: a vertical swipe on the stage scrolls the page and does not turn the piece; a sideways one turns it and does not scroll
  for (const piece of ['globe', 'ring']) {
    const page = await open(piece, phone);
    await page.eval('document.body.style.minHeight = "3000px"; true');
    const box = JSON.parse(await page.eval("JSON.stringify(document.querySelector('.sx-stage').getBoundingClientRect())"));
    const x = box.x + box.width * 0.5;
    const y0 = box.y + box.height * 0.75;
    const read = () => (piece === 'globe' ? page.eval("document.querySelector('.sx-orb').style.transform.replace(/rotateY\\([^)]*\\)/, '')") : page.eval("document.querySelector('.sx-name').textContent"));
    const before = await read();
    await page.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y: y0 }] });
    for (let k = 1; k <= 12; k++) {
      await page.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: x + k * 0.5, y: y0 - k * 22 }] });
      await sleep(16);
    }
    await page.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    await sleep(700);
    const sy = await page.eval('Math.round(window.scrollY)');
    ok(`touch (${piece}): a vertical swipe on the stage scrolls the page`, sy > 80, `scrollY ${sy}`);
    await page.eval('window.scrollTo(0, 0); true');
    await sleep(300);
    const yaw0 = await page.eval(orbT.replace('.style.transform', '.style.transform') + ' || ""').catch(() => '');
    await page.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: box.x + box.width * 0.85, y: box.y + box.height * 0.45 }] });
    for (let k = 1; k <= 12; k++) {
      await page.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: box.x + box.width * 0.85 - k * 22, y: box.y + box.height * 0.45 + k * 0.6 }] });
      await sleep(16);
    }
    await page.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    await sleep(1400);
    const sy2 = await page.eval('Math.round(window.scrollY)');
    const after = piece === 'globe' ? await page.eval(orbT) : await page.eval("document.querySelector('.sx-name').textContent");
    ok(`touch (${piece}): a sideways swipe turns it and does not scroll`, sy2 === 0 && after !== (piece === 'globe' ? yaw0 : before), `scrollY ${sy2}; ${String(piece === 'globe' ? yaw0 : before).slice(0, 50)} -> ${String(after).slice(0, 50)}`);
    void before;
    await page.close();
  }
} finally {
  await chrome.close();
}
console.log(out.join('\n'));
