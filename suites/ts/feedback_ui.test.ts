// The anonymous feedback box on the page (2026-10-20): its words in the four languages (the same six chips as the server's, the limit, the privacy line), its markup (a labelled group of six native
// radio buttons, no e-mail field, a hidden honeypot only once a chip is chosen, quiet until the server says yes and after the place has been answered), where /try places it (after the price on the
// result screen, under the card that asks for another photo and outside its alert), that it stores nothing in the browser, and the owner's page (Atsiliepimai: the words, the line under a text,
// the wiring). Pure page code, loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results.
import { readFileSync } from 'node:fs';
import { createElement as h } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { COPY, setCopyLang } from '../../src/try/copy';
import { FeedbackBox } from '../../src/try/Feedback';
import { CHIPS, TEXT_MAX, forgetAnswered, markAnswered } from '../../src/shared/feedback';
import { FB_PLACE_LT, FB_RESULT_LT, FB_RETAKE_LT, FB_TEXT_LT, fbChipLt, valueLt, type FeedbackText } from '../../src/admin/traffic';
import { metaText, whenText } from '../../src/admin/Feedback';

type Row = [string, boolean, string?];
const LANGS = ['en', 'de', 'lt', 'hu'] as const;
const read = (p: string) => readFileSync(new URL(`../../${p}`, import.meta.url), 'utf8');
const html = (el: Parameters<typeof renderToStaticMarkup>[0]) => renderToStaticMarkup(el);
const count = (s: string, re: RegExp) => (s.match(re) ?? []).length;

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);
  const dash = new RegExp('[' + [0x2012, 0x2013, 0x2014, 0x2015].map((c) => String.fromCharCode(c)).join('') + ']');

  // ------------------------------------------------------------------------------------------ the words
  const keysOf = (o: object) => Object.keys(o).join();
  check('every language has the same six chips on the result screen and the same six on the card that asks for another photo, the server\'s codes in the server\'s order',
    LANGS.every((l) => keysOf(COPY[l].feedback.chips.result) === CHIPS.result.join() && keysOf(COPY[l].feedback.chips.retake) === CHIPS.retake.join()), LANGS.map((l) => keysOf(COPY[l].feedback.chips.result)).join(' | '));
  const strings = (l: (typeof LANGS)[number]) => {
    const f = COPY[l].feedback;
    return [f.title.result, f.title.retake, f.hint.result, f.hint.retake, ...Object.values(f.chips.result), ...Object.values(f.chips.retake), f.textLabel, f.textHint, f.send, f.sending, f.thanks, f.textDropped, f.textLost, f.failed, f.privacy];
  };
  check('no sentence of the box is empty, none holds an en or em dash, and the six chips of a place read differently', LANGS.every((l) => strings(l).every((s) => s.trim().length > 0 && !dash.test(s))
    && new Set(Object.values(COPY[l].feedback.chips.result)).size === 6 && new Set(Object.values(COPY[l].feedback.chips.retake)).size === 6), LANGS.filter((l) => strings(l).some((s) => !s.trim() || dash.test(s))).join());
  check('the counter prints the length and the limit (300) in every language', LANGS.every((l) => /57/.test(COPY[l].feedback.count(57, TEXT_MAX)) && /300/.test(COPY[l].feedback.count(57, TEXT_MAX))) && TEXT_MAX === 300);
  check('the line under the box says it is anonymous and that a text goes after 90 days, in every language (the privacy policy says the same)', LANGS.every((l) => /90/.test(COPY[l].feedback.privacy)), LANGS.map((l) => COPY[l].feedback.privacy).join(' | '));
  check('the hint asks the visitor not to write names, e-mail addresses or telephone numbers (the server drops the last two)', ['Names|names', 'Namen', 'vardų', 'nevet'].every((w, i) => new RegExp(w).test(COPY[LANGS[i]].feedback.textHint)), LANGS.map((l) => COPY[l].feedback.textHint).join(' | '));

  // ------------------------------------------------------------------------------------------ the markup
  for (const l of LANGS) {
    setCopyLang(l);
    forgetAnswered();
    const F = COPY[l].feedback;
    const r = html(h(FeedbackBox, { where: 'result', ctx: 'solo.powder', eyes: 1, on: true }));
    check(`${l}: the result box is a labelled group of six native radio buttons with the chips' words, in order`, count(r, /type="radio"/g) === 6 && /<section[^>]*aria-labelledby=/.test(r) && /<legend class="sr-only">/.test(r)
      && Object.values(F.chips.result).every((w, i, a) => r.indexOf(w.replace(/&/g, '&amp;')) > (i ? r.indexOf(a[i - 1].replace(/&/g, '&amp;')) : -1)), r.slice(0, 200));
    const k = html(h(FeedbackBox, { where: 'retake', ctx: 'too_blurry', on: true }));
    check(`${l}: the retake box has its own six`, count(k, /type="radio"/g) === 6 && Object.values(F.chips.retake).every((w) => k.includes(w)) && k.includes(F.title.retake) && r.includes(F.title.result), k.slice(0, 200));
    check(`${l}: no e-mail field, no name field, no text field before a chip is chosen, and the privacy policy is one link away in this language`, !/type="email"|type="tel"|name="name"|name="email"/.test(r) && !/<textarea/.test(r) && !/<input type="text"/.test(r)
      && new RegExp(`href="[^"]*privacy[^"]*lang=${l}`).test(r) && r.includes(F.privacy), r.slice(-300));
  }
  setCopyLang('en');
  forgetAnswered();
  check('quiet: until the server says yes the box is not on the page at all', html(h(FeedbackBox, { where: 'result' })) === '' && html(h(FeedbackBox, { where: 'retake' })) === '');
  markAnswered('result');
  check('and once a place has been answered in this visit it does not ask again there (the other place still does)', html(h(FeedbackBox, { where: 'result', on: true })) === '' && html(h(FeedbackBox, { where: 'retake', on: true })) !== '');
  forgetAnswered();

  // ------------------------------------------------------------------------------------------ the source: where it stands and what it may do
  const box = read('src/try/Feedback.tsx');
  const code = box.replace(/[/][/].*$/gm, '').replace(/[/][*][\s\S]*?[*][/]/g, '');
  check('the box has a label for the field, the limit and a described hint, a status for the thanks, an alert for a failure and a visible focus ring on its chips and button',
    /<label className="flex flex-col gap-1">/.test(code) && /aria-describedby/.test(code) && /role="status"/.test(code) && /role="alert"/.test(code) && /peer-focus-visible:outline/.test(code) && /maxLength=\{TEXT_MAX\}/.test(code) && /min-h-\[44px\]/.test(code));
  check('the honeypot is out of the way of a person: out of the tab order, hidden from a screen reader, no autocomplete, and only rendered once a chip is chosen', /tabIndex=\{-1\}/.test(code) && /aria-hidden="true"/.test(code) && /autoComplete="off"/.test(code) && /\{chip && \(/.test(code));
  check('it sends nothing until Send: the chips only set state, the one request is made by the form\'s submit', /onChange=\{\(\) => setChip\(c\)\}/.test(code) && /onSubmit=\{\(e\) => void submit\(e\)\}/.test(code) && count(code, /send\(/g) === 1);
  check('it takes no focus and writes nothing to the browser: no autoFocus, no focus() call, no cookie, no storage', !/autoFocus|[.]focus\(/.test(code) && !/document[.]cookie|localStorage|sessionStorage/.test(code));
  const result = read('src/try/ResultView.tsx');
  const iPurchase = result.indexOf('{p.purchase}');
  const iBox = result.indexOf('<FeedbackBox where="result"');
  const iStart = result.indexOf('onClick={p.onStartOver}');
  check('on the result screen the box comes after the price card, never before it, and only once a preview is on screen (p.art)', iPurchase > 0 && iBox > iPurchase && iStart > iBox && /\{p\.art && <FeedbackBox where="result"/.test(result));
  const guide = read('src/try/RetakeGuide.tsx');
  check('under the card that asks for another photo the box stands outside the alert (it changes as it is used and an alert would read every change aloud)', guide.indexOf('<FeedbackBox where="retake"') > guide.indexOf('</div>') && /role="alert"/.test(guide) && guide.indexOf('<FeedbackBox') > guide.lastIndexOf('</div>'));
  const app = read('src/try/TryApp.tsx');
  check('/try asks the server once, with the counter\'s answer, and passes the block reason as the box\'s context at both places it shows the card', /noteFeedback\(h\.feedback\)/.test(app) && count(app, /<RetakeGuide [^>]*code=\{blockCode\(/g) === 2);
  check('the box is shown nowhere but /try: no other page imports it', !/Feedback/.test(read('src/order/OrderApp.tsx')) && !/src\/try\/Feedback|shared\/feedback/.test(read('src/landing/shell/scripts.ts')) && !/shared\/feedback/.test(read('src/legal/main.tsx')));

  // ------------------------------------------------------------------------------------------ the owner's page
  check('the owner\'s words for the chips cover every chip the page sends, in both places', CHIPS.result.every((c) => FB_RESULT_LT[c] && fbChipLt('result', c) === FB_RESULT_LT[c]) && CHIPS.retake.every((c) => FB_RETAKE_LT[c] && fbChipLt('retake', c) === FB_RETAKE_LT[c]) && fbChipLt('result', 'new') === 'new');
  check('the counts of the chips, of a chip with the style on screen or the block reason, and of what became of a text read in words', valueLt('fb_result', 'colour') === FB_RESULT_LT.colour && valueLt('fb_retake', 'device') === FB_RETAKE_LT.device
    && valueLt('fb_style', 'colour:solo.gold') === `${FB_RESULT_LT.colour}: Celestial Gold` && /^Nesuprantu, kas negerai: /.test(valueLt('fb_block', 'unclear:too_blurry')) && valueLt('fb_block', 'unclear:never_seen') === `${FB_RETAKE_LT.unclear}: never_seen`
    && valueLt('fb_text', 'contact') === FB_TEXT_LT.contact && valueLt('fb_text', 'unknown') === 'unknown', [valueLt('fb_style', 'colour:solo.gold'), valueLt('fb_block', 'unclear:too_blurry')].join(' | '));
  const row: FeedbackText = { id: '20261020-123105-0123456789ab', day: '2026-10-20', at: '123105', t: 1792488665, w: 'result', c: 'colour', x: 'solo.gold', eyes: 2, txt: 'Per šalta', src: 'fb', med: 'paid', cmp: 'se-p0-test', trm: 'lt-a1-eye', cnt: 'a1-lt-s1', dev: 'ios', br: 'ig', cc: 'lt', lang: 'lt', market: 'lt' };
  check('the line under a text says when (UTC), where, which style, how many eyes, the source, the device, the browser, the language and the country', whenText(row) === '2026-10-20 12:31'
    && metaText(row) === `2026-10-20 12:31 UTC · ${FB_PLACE_LT.result} · Celestial Gold · 2 akys · Facebook (reklama) / mokama / se-p0-test / lt-a1-eye / a1-lt-s1 · iPhone / iPad · Instagram programa · Lietuvių · LT`, metaText(row));
  check('and a text with no classes has only what it knows', metaText({ id: 'x', day: '2026-10-20', at: '010203', t: 1, w: 'retake', c: 'only', txt: 'a' }) === `2026-10-20 01:02 UTC · ${FB_PLACE_LT.retake}`);
  const page = read('src/admin/Feedback.tsx');
  const pageCode = page.replace(/[/][/].*$/gm, '');
  check('the page shows a text as a text node (never markup), asks before it deletes one, and makes its requests only through the call it is given', !/dangerouslySetInnerHTML|innerHTML/.test(pageCode) && /ConfirmDialog/.test(pageCode) && /danger: true/.test(pageCode) && !/\bfetch\(|localStorage/.test(pageCode) && /call<[^>]*>\('feedback_delete'/.test(pageCode));
  const adminApp = read('src/admin/AdminApp.tsx');
  check('the admin app has the Atsiliepimai tab in the visitors group and the action exists on the server', /\['feedback', 'Atsiliepimai'\]/.test(adminApp) && /route\.page === 'feedback'/.test(adminApp) && read('api/_lib/ops.py').includes('"feedback": a_feedback') && read('api/_lib/ops.py').includes('"feedback_delete": audited('));
  check('no page of the owner\'s feedback view holds an en or em dash', !dash.test(page) && !dash.test(read('src/try/Feedback.tsx')) && !dash.test(read('src/shared/feedback.ts')));
  return out;
}
