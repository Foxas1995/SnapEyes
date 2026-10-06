// The text check of the build: the site speaks English, German, Lithuanian and Hungarian, and this refuses the build when
//   1. a Lithuanian or Hungarian dictionary (landing page, /try, /order, the checkout wording, the legal pages) has other
//      keys, other value kinds, other array lengths or other function arity than the English one, or a legal text has
//      other section ids, other block kinds or other links (so a language switch keeps every link), or a function has
//      no sample arguments here (add it to SAMPLES when a function is added to a dictionary);
//   2. a string of any language holds an en or em dash (owner rule: no en or em dash anywhere), or a Lithuanian or
//      Hungarian string holds untranslated English (a word of ENGLISH outside the brand names and technical terms of
//      ENGLISH_OK), or one of the typographic slips of the lint (double spaces, a space before a full stop, a straight
//      double quote, a lower-case "jūs" form in Lithuanian);
//   3. an edition of the legal texts is incomplete or wrong: the legal pack (src/legal/plain.ts legalMailPack) lacks a
//      text in a language of its edition (src/shared/legal.ts EDITION_LANGS), the terms of a market's edition do not
//      print that market's prices in its currency (or print another currency's price table), or the sentence naming
//      the contract languages does not name every language the edition can be read in;
//   4. the withdrawal-consent version and the date of the legal texts are malformed, in the future, or (the version)
//      not the one api/_lib/pay.py CONSENT_VERSION says;
//   5. a source file holds an en or em dash (api/_lib/layout_names.py, the one table of the layout words, is read as strings too: the
//      words of every language go through the checks of 2 and 9 like any dictionary string);
//   6. a language of api/analyze.py's customer sentences (TEXT_DE, TEXT_LT, TEXT_HU) lacks a key or a placeholder, or lacks
//      a sentence for a reason a photo can be blocked for;
//   7. the withdrawal waiver (checkbox) or the withdrawal statement is not the same words on the page and on the server,
//      in any language;
//   8. the consent texts (the four languages of the EU edition and the two of the Australian one) are not the ones the
//      fingerprint of the current consent version says (CONSENT_FINGERPRINTS): a changed text needs a new version, in
//      api/_lib/pay.py CONSENT_VERSION and src/shared/legal.ts WITHDRAWAL_CONSENT_VERSION together;
//  10. a string of any language makes a claim the plate styles cannot keep (CLAIMS below: an artwork that is "unique", "one of a kind", "never
//      repeated", "handmade", a "100 percent" close-up, "every fibre", a "best seller", "most chosen" or "most popular"), in the dictionaries, the
//      legal texts, the Lithuanian and Hungarian e-mail sentences and the head of index.html; the powder, crowns and spirals around an iris come from a
//      finite library of plates, so such a word would be untrue (review of 2026-10-04, risk 26). The sentence about AI-made material
//      (src/shared/aiMaterial.ts) is linted like any other string in the four languages while it is unpublished, and is in every terms text once it is
//      published and in none before;
//   9. a Lithuanian or Hungarian string is the very same words as the English or German one (untranslated), or one of
//      the customer sentences in the Python files of those languages (api/_lib/*_lt.py, *_hu.py: the emails, the
//      receipts, the Stripe notes, the analyze tips) holds English or German words or a dash; the refusals of the compose
//      API (api/compose.py WORDS, four languages per key) go through the checks of 2 and 9 like any dictionary string.
//  11. the copy of the NEW landing (src/landing/copy/<lang>.json, one file per language of src/shared/lang.ts LANGS): every
//      language has its file, with the keys, the value kinds, the list lengths, the numbers and the {tokens} of en.json, only
//      tokens the page knows (src/landing/copy/format.ts TOKENS), no dash and no spaced hyphen, none of the banned claims
//      ("ready to print", "100 percent", "museum glass"), the honesty lines where the prototype has them (the labels, "Printing
//      is not part of your order", "Ordering opens soon" in exactly three places), the legal labels and the withdrawal button of
//      src/shared/legal.ts, the facts of src/landing/config.ts, the FAQ ids in the same order and the Australian FAQ answers for
//      ids that exist. Every language has its real translation (no English stand-ins any more), so all four files are
//      linted like every other dictionary.
// vite.config.ts runs it before every build (src/ is loaded through Vite's module runner, as the legal pack is);
// `npm run check:texts` runs it alone. The legal pack the confirmation email carries is checked by checkPack, which the
// build also runs on the very JSON it writes to /legal/order-mail.json (vite.config.ts legalMail), so no untranslated
// English or dash can reach a customer's email through the built file either.
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { createHash } from 'node:crypto';

const LANGS = ['en', 'de', 'lt', 'hu'];
const SHY = new RegExp(String.fromCharCode(0xad), 'g');              // the soft hyphens of the German titles
const NBSP_RE = new RegExp(String.fromCharCode(0xa0), 'g');          // the no-break spaces of prices
const SEPARATOR = new RegExp('[ ' + String.fromCharCode(0xa0) + ']·[ ' + String.fromCharCode(0xa0) + ']', 'g');   // " · " between the parts of a label
const NEW_LANGS = ['lt', 'hu'];
// the four dashes the owner rules out (U+2012 to U+2015), built from their codes so that this file holds none itself
const DASH = new RegExp('[' + String.fromCharCode(0x2012, 0x2013, 0x2014, 0x2015) + ']');

// ------------------------------------------------------------------------------------------ sample arguments
// One entry per function of the copy dictionaries, by its path below the dictionary (see the list a run prints when
// one is missing). Numbers are chosen to exercise plural forms (Lithuanian: 1, 2, 5, 11, 21); strings are as the
// page passes them.
const W = '2026-09-29 13:15';
export const SAMPLES = {
  dec1: [[3.7], [4]], 'errors.requestFailed': [[500]], 'capture.addTitle': [[2]], 'capture.retakeTitle': [[2]],
  'capture.back': [[1], [3], [5]], 'capture.thumbLabel': [[1]], 'working.checking': [[5, 2], [1, 0]],
  'working.measuringShot': [[2, 5]], 'working.restoringEye': [[2]], 'working.composing': [[1], [3]], 'working.elapsed': [[12]],
  'quality.noneUsable': [[2], [3], [5]], 'quality.fullUnusable': [[5], [8]], 'quality.aimFor': [[45]],
  'quality.picked': [[4, 2], [1, 1], [11, 3]], 'quality.pickedRatio': [['3,7'], ['2,5'], ['4,0'], ['10,0']],
  'collector.header': [[2, 5], [1, 5]], 'collector.headerDetail': [[45]], 'collector.shotAlt': [[3]],
  'collector.bestLabel': [[3, 45], [3, undefined]], 'collector.full': [[5, 'X 2 (45)']], 'collector.more': [[1], [3], [11]],
  'collector.lampSkipped': [[1, 'X 3'], [2, 'X 3'], [5, 'X 3']], 'collector.bestIs': [['X 3']],
  'collector.lastFailed': [['Ezen a felvételen nem találtunk szemet.']],
  'result.eyeLabel': [[1]], 'result.retakeEye': [[2]], 'result.removed': [[2]], 'result.irisPx': [[420]],
  'result.previewFile': [[true], [false]], 'result.fileName': [['celestial-gold', 2, false], ['studio-black', 1, true]],
  'result.addHint': [[1], [3], [11]], 'result.full': [[8]], 'result.remove': [[2]], 'result.confirmStartOver': [[3], [5]],
  'price.eyes': [[1, 'Celestial Gold'], [2, 'Kiss Collision'], [4, 'Family Colours'], [11, 'Family Colours']],
  'price.black': [['Clean Iris', '6 990 Ft', '8 990 Ft']],
  'price.duoOffer': [['13 990 Ft']], 'price.extra': [['13 990 Ft', '4 990 Ft', 8]], 'price.sampleNotCounted': [[1], [2], [5]],
  // the style picker (src/try/picker.ts, WP11): one entry per function of the dictionary's picker section
  'picker.countSoon': [[1], [2], [3], [5], [8]], 'picker.retakeFirst': [[1], [2]], 'picker.resealFirst': [[2]],
  'picker.tileAlt': [['Powder Burst']], 'picker.tileMaking': [['Powder Burst']], 'picker.soonLookBuy': [['Vortex'], ['Echo']], 'picker.soonLookNote': [['Vortex'], ['Deep Field']],
  'picker.changed.eyes': [['Collision Infinity', 'Family Colours', 3], ['Powder Burst', 'Kiss Collision', 2], ['Family Colours', 'Celestial Gold', 1]],
  'picker.changed.gate': [['Kiss Collision', 'Powder Burst', 2], ['Family Colours', 'Powder Burst', 5]],
  'picker.changed.reseal': [['Kiss Collision', 'Powder Burst', 1]], 'picker.changed.pupil': [['Kiss Collision', 'Powder Burst']],
  'picker.chipLabel': [[2]], 'picker.advisory': [[[1], 1], [[2], 3], [[1, 3], 4], [[5], 6]],
  'picker.retake.title': [[[1], 1], [[2], 3], [[1, 3], 4], [[2, 3, 5], 6]], 'picker.retake.reseal': [[[1], 1], [[2], 3], [[1, 2], 4]],
  'picker.options.earlierLabel': [[2]], 'picker.options.laterLabel': [[2]], 'picker.names.nameFor': [[1, 1], [2, 3]],
  'picker.names.problem.nameLong': [[2, 24]], 'picker.names.problem.namesLong': [[200]], 'picker.names.problem.glyph': [['Ñ']],
  'picker.names.problem.dateLong': [[20]], 'picker.names.problem.familyLong': [[24]],
  'buy.button': [['13 990 Ft']], 'buy.steps.upload': [[1, 1], [2, 3]], 'buy.sample': [[1], [2]], 'buy.replaceSampleEye': [[2]],
  'buy.stale': [[[1], 1], [[2], 3], [[1, 2, 4], 5], [[5], 6]], 'study.title': [[3, 1], [5, 3]],
  'study.pending': [[[2]], [[1, 3]]],
  orderNo: [['260929-ab12']], 'summary.eyes': [[1], [2], [10]], 'summary.paid': [['13 990 Ft']],
  'summary.inscription': [['Anna & Péter']], 'making.eye': [[1]], 'making.progress': [[1, 3]], 'making.part': [[1, 2], [2, 2]], 'making.elapsed': [[20]],
  'wait.busy': [[10]], 'wait.network': [[10]], 'wait.rendering': [[10]], 'wait.confirming': [[10]],
  'ready.details': [[4096, 2731, '6,2']], 'withdraw.formLead': [['Confirm']], 'withdraw.statement': [['260929-ab12']],
  'withdraw.errors.unmatched': [[W], [null]], 'withdraw.done.received': [[W]], 'withdraw.done.refund': [['13 990 Ft']],
  'withdraw.done.refundBy': [['13 990 Ft', W]], 'withdraw.done.refundStarted': [['13 990 Ft']],
  'withdraw.done.mailSent': [['anna@example.com']], 'withdraw.done.mailLater': [['anna@example.com']],
  'withdraw.done.mailFailed': [['anna@example.com']], 'withdraw.withdrawn.body': [[W]], 'contact.write': [['info@snapeyes.com']],
  'contact.subject': [['260929-ab12']],
};

// ------------------------------------------------------------------------------------------ the lint
// what counts as English inside a Lithuanian or Hungarian string, and what may stay English there
// Words of English (then German) that are nothing else in Lithuanian or Hungarian: function words and the words a shop's
// text is made of. A word that is also a real Lithuanian or Hungarian word is left out on purpose (Hungarian "most",
// "mind", "has", "had", "hat", "mit", "von", "start", "hold"; Lithuanian "man", "per", "ten", "to", "be", "as", "bei"
// and "minutes", which is the Lithuanian "minutes" too), so this list never flags a correct sentence; it catches a
// sentence that was never translated. An English word that is
// meant to stay (a brand, a technical term) goes into ENGLISH_OK.
const WORDS_EN = [
  'the', 'and', 'your', 'you', 'with', 'order', 'photo', 'photos', 'please', 'preview', 'artwork', 'eyes?', 'shot', 'withdraw\\w*',
  'payment', 'download\\w*', 'file', 'files', 'our', 'we', 'are', 'was', 'were', 'will', 'shall', 'have', 'been', 'refund\\w*',
  'contract', 'terms', 'customer', 'email', 'price', 'prices', 'delivery', 'click', 'button',
  'for', 'this', 'that', 'these', 'those', 'from', 'not', 'but', 'can', 'may', 'must', 'would', 'should', 'could', 'about', 'after',
  'before', 'when', 'where', 'which', 'who', 'what', 'why', 'how', 'their', 'them', 'they', 'its', 'she', 'any', 'each', 'every',
  'more', 'other', 'some', 'such', 'than', 'then', 'there', 'here', 'only', 'also', 'just', 'very', 'into', 'upon', 'within',
  'without', 'below', 'above', 'choose', 'select', 'continue', 'upload\\w*', 'privacy', 'policy', 'free', 'view', 'open', 'close',
  'help', 'contact', 'support', 'service', 'account', 'address', 'hours', 'week', 'month', 'year', 'image', 'images',
  'picture', 'sample', 'result', 'results', 'final', 'full', 'good', 'best', 'great', 'next', 'back', 'done', 'again', 'send',
  'keep', 'take', 'made', 'make', 'need', 'want', 'get', 'see', 'new', 'try', 'thank', 'thanks', 'welcome', 'sorry', 'hello',
  'restored?', 'restoring', 'printed', 'print', 'frame', 'ships?', 'shipped', 'shipping', 'sold', 'buy', 'bought', 'paid',
];
const WORDS_DE = [
  'und', 'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einen', 'einem', 'einer', 'ist', 'sind', 'sie', 'ihr', 'ihre',
  'ihren', 'ihrem', 'ihrer', 'wir', 'wird', 'werden', 'wurde', 'wurden', 'oder', 'auch', 'nicht', 'nur', 'für', 'nach',
  'vom', 'zum', 'zur', 'über', 'unter', 'wenn', 'dass', 'aber', 'noch', 'schon', 'bitte', 'bestellung', 'vorschau', 'datei',
  'zahlung', 'widerruf\\w*', 'vertrag', 'kunde', 'kunden', 'preis', 'preise', 'lieferung', 'bestellen', 'hochladen',
  'herunterladen', 'zurück', 'weiter', 'fertig', 'kostenlos', 'auge', 'augen', 'aufnahme', 'bild', 'ihnen', 'uns', 'unser',
  'unsere', 'haben', 'kann', 'können', 'muss', 'müssen', 'soll', 'sollen', 'diese', 'dieser', 'dieses', 'jede', 'jeder', 'alle',
  'alles', 'mehr', 'sehr', 'hier', 'dort', 'heute', 'jetzt', 'dann', 'damit', 'sowie', 'sofort', 'stunden', 'danke',
  'willkommen', 'entschuldigung', 'kunstwerk', 'rechnung', 'kaufen', 'bezahlt',
];
const wordRe = (words) => new RegExp(`(?<![\\p{L}])(${words.join('|')})(?![\\p{L}])`, 'iu');
const ENGLISH = wordRe(WORDS_EN);
const GERMAN = wordRe(WORDS_DE);
// The brand names are English in every language (api/_lib/styles_registry.py names): the eleven names of the v3 catalogue, the held
// and later ones (Elements, Reflection, Infinity Chain, Universe Duo) and the looks inside Universe, so that no string that names
// them is flagged as untranslated English in Lithuanian or Hungarian. Longer names come before the names they contain.
const STYLE_NAMES_OK = [
  'Celestial Gold Duo', 'Radiance Duo', 'Universe Duo', 'Infinity Chain', 'Collision Infinity', 'Clean Infinity', 'Clean Family', 'Clean Iris',
  'Kiss Collision', 'Family Colours', 'Powder Burst', 'Celestial Gold', 'Universe', 'Splash', 'Radiance', 'Elements', 'Reflection',
  'Echo', 'Vortex', 'Deep Field', 'Starfield',
];
const ENGLISH_OK = new RegExp([
  ...STYLE_NAMES_OK,
  'SnapEyes', 'Studio Black', 'Deep Nebula', 'Emerald Aurora', 'Obsidian Smoke', 'Supernova', 'Couple Duo',
  'Private Atelier', 'Studio', 'Gemini API', 'Google Fonts', 'Google Gemini', 'user agent', 'local storage', 'session storage',
  'snapeyes\\.[a-z]+', 'mailto:\\S+', 'https?:\\/\\/\\S+', 'snapeyes\\.com\\/\\S*', 'order\\?\\S*', '\\/order\\S*', '\\/try\\S*',
  '\\.jpg', '\\.png', 'info@snapeyes\\.com', 'example\\.com', 'doc:\\S+', 'Australian Consumer Law', 'GST', 'Stripe', 'Resend',
  'Vercel', 'Supabase', 'Hostinger', 'Apple Pay', 'Google Pay', 'Link', 'PayPal', 'Revolut Pay', 'JPEG', 'PNG', 'PDF', 'px', 'AI',
  'Art\\. 5', 'GDPR', 'Directive', 'Regulation', 'Mantas Bakšys', 'Portretizuokis', 'Global Privacy Control',
  // the style names of the landing's gallery are brand names in every language (longer ones first)
  'Powder Burst', 'Infinity Universe', 'Clean Infinity', 'Family Universe', 'Clean Iris', 'Radiance', 'Splash', 'Universe', 'Infinity', 'Kiss', 'Trio',
].join('|'), 'g');
const LT_LETTERS = 'A-Za-zĄČĘĖĮŠŲŪŽąčęėįšųūž';
const LT_LOWER_JUS = new RegExp(`(^|[^${LT_LETTERS}])(jūs|jūsų|jums|jus|jumis)(?![${LT_LETTERS}])`, 'u');
// words and forms the Lithuanian language review ruled out: calques and non-standard wording ("matosi", "niekas nekuriama"
// where the genitive "nieko nekuriama" is right, "pilno dydžio" for "viso dydžio", ...)
// (the complete list of the Lithuanian pack's own lint, wave-lt tools/check_py.py and check_ts.mjs NONSTANDARD)
const LT_FLAGGED = new RegExp(`(^|[^${LT_LETTERS}])(matosi|matytųsi|matėsi|ilgojoje kraštinėje|niekas nekuriama|niekas nebus kuriama|privalomas pasiūlymas|iš principo|pilno dydžio|pilną dydį|pilnai|priklausomai nuo|pagal ką|pasirodo kad|įtakoja|įtakoti|Gerb\\.)(?![${LT_LETTERS}])`, 'iu');

// Claims the plate styles cannot keep, by language (check 10). The plain word "best" is not here: the FAQ asks for "your best photos". "einmalig" (German
// "once") is not here either: "einmalig in voller Aufloesung" says the file is made once. The Hungarian "egyedi" (custom or unique) is not here: it reads
// "made to order" as often as "unique"; "egyedülálló" and the rest are.
const CLAIMS = {
  en: [/\bunique(?:ly)?\b/i, /\bone[- ]of[- ]a[- ]kind\b/i, /\bnever (?:repeated|repeats)\b/i, /\bno two (?:are )?alike\b/i, /\bhand[- ]?made\b/i,
    /\bhand[- ]?painted\b/i, /\bevery (?:single )?fib(?:re|er)\b/i, /\bbest[- ]?sellers?\b/i, /\bmost (?:chosen|popular)\b/i, /\b100\s?(?:%|per ?cent)/i],
  de: [/einzigartig/i, /\bUnikat/i, /nie wiederholt/i, /keine zwei (?:sind )?gleich/i, /handgemacht|handgefertigt/i, /handgemalt/i, /jede (?:einzelne )?Faser/i,
    /best[- ]?seller/i, /am (?:häufigsten gewählt|beliebtesten)|meistgewählt|beliebteste/i, /\b100\s?(?:%|Prozent)/i],
  lt: [/unikal/i, /nepasikartoj/i, /nė dviejų vienodų/i, /rankų darbo/i, /ranka (?:nupiešt|pieštas)/i, /kiekviena skaidula/i, /perkamiaus/i, /populiariaus/i,
    /dažniausiai (?:renkam|pasirenkam)/i, /\b100\s?(?:%|proc)/i],
  hu: [/egyedülálló/i, /megismételhetetlen/i, /két egyforma sincs/i, /kézzel (?:készült|festett)/i, /minden (?:egyes )?rost/i, /best[- ]?seller/i, /legnépszerűbb/i,
    /legtöbbet választott/i, /\b100\s?(?:%|százalék)/i],
};

/** A claim the plate styles cannot keep in one string (check 10), as a sentence, or null. */
export function claimIn(s, lang) {
  for (const re of CLAIMS[lang] ?? []) {
    const m = s.match(re);
    if (m) return m[0];
  }
  return null;
}

/** typography: false for the strings of the Python files (HTML attributes and code-like strings there are not prose). */
function lint(path, s, lang, out, typography = true) {
  if (DASH.test(s)) out.push(`${path} (${lang}): an en or em dash: ${s.slice(0, 120)}`);
  const claim = claimIn(s, lang);
  if (claim) out.push(`${path} (${lang}): the claim "${claim}", which the plate styles cannot keep (the powder, crowns and spirals around an iris come from a shared library of plates): ${s.slice(0, 120)}`);
  if (!NEW_LANGS.includes(lang)) return;
  const noLinks = s.replace(/\]\([^)]*\)/g, ']');
  if (typography) {
    if (/"/.test(noLinks)) out.push(`${path} (${lang}): a straight double quote (use the language's own): ${s.slice(0, 120)}`);
    if (/[^.]\.\.(?!\.)/.test(s)) out.push(`${path} (${lang}): a double full stop: ${s.slice(0, 120)}`);
    if (/ {2,}/.test(s.replace(SEPARATOR, ' '))) out.push(`${path} (${lang}): a double space: ${JSON.stringify(s.slice(0, 120))}`);
    if (/ [,.;:!?](\s|$)/.test(s)) out.push(`${path} (${lang}): a space before punctuation: ${s.slice(0, 120)}`);
  }
  if (lang === 'lt') {
    const m = s.match(LT_LOWER_JUS);
    if (m) out.push(`${path} (lt): lower-case "${m[2]}" (Jūs, Jūsų, Jums are capitalised): ${s.slice(0, 120)}`);
    const bad = s.match(LT_FLAGGED);
    if (bad) out.push(`${path} (lt): "${bad[2]}" is a wording the language review ruled out: ${s.slice(0, 120)}`);
  }
  const rest = s.replace(ENGLISH_OK, ' ').replace(/\[[^\]]*\]\([^)]*\)/g, (x) => x.replace(/\([^)]*\)$/, ''));
  const e = rest.match(ENGLISH);
  if (e) out.push(`${path} (${lang}): untranslated English "${e[0]}"?: ${s.slice(0, 160)}`);
  const g = rest.match(GERMAN);
  if (g) out.push(`${path} (${lang}): untranslated German "${g[0]}"?: ${s.slice(0, 160)}`);
}

/** A Lithuanian or Hungarian string that is word for word the English or the German one is an untranslated sentence
 *  (one word, a name or a number excepted, and what ENGLISH_OK names). strings: per language, [path, text] pairs. */
function identical(strings, out) {
  const other = new Set();
  for (const l of ['en', 'de']) for (const [, s] of strings[l]) other.add(s.replace(SHY, '').trim());
  for (const l of NEW_LANGS) {
    for (const [path, s] of strings[l]) {
      const t = s.replace(SHY, '').trim();
      if (t.length < 12 || !/\s/.test(t)) continue;
      const rest = t.replace(ENGLISH_OK, ' ').replace(/[^\p{L}]+/gu, ' ').trim();
      if (!/\p{L}{3,} \p{L}{3,}/u.test(rest)) continue;     // only names, numbers and symbols left
      if (other.has(t)) out.push(`${path} (${l}): word for word the English or German text, untranslated?: ${t.slice(0, 140)}`);
    }
  }
}

/** The string literals of a Python file, without comments and docstrings, with the {fields} of an f-string blanked, as
 *  [line, text] pairs. Enough of Python for the flat text files of api/_lib (no nested quotes in an f-string field). */
function pyStrings(text) {
  const out = [];
  const unescape = (s) => s.replace(/\\(u[0-9a-fA-F]{4}|x[0-9a-fA-F]{2}|.)/g, (m, c) => (c[0] === 'u' || c[0] === 'x' ? String.fromCharCode(parseInt(c.slice(1), 16)) : c === 'n' ? '\n' : c === 't' ? '\t' : c));
  let i = 0;
  const n = text.length;
  while (i < n) {
    const c = text[i];
    if (c === '#') { while (i < n && text[i] !== '\n') i++; continue; }
    if (c !== '"' && c !== "'") { i++; continue; }
    const triple = text.startsWith(c.repeat(3), i);
    const prefix = /[A-Za-z]{0,2}$/.exec(text.slice(Math.max(0, i - 2), i))[0].toLowerCase();
    const raw = prefix.includes('r'), fstr = prefix.includes('f');
    const q = triple ? c.repeat(3) : c;
    let j = i + q.length;
    while (j < n && !text.startsWith(q, j)) j += text[j] === '\\' ? 2 : 1;
    const body = text.slice(i + q.length, j);
    const line = text.slice(0, i).split('\n').length;
    i = j + q.length;
    if (triple) continue;                                     // a docstring
    let s = raw ? body : unescape(body);
    if (fstr) s = s.replace(/\{\{|\}\}/g, '').replace(/\{[^{}]*\}/g, ' ');
    s = s.replace(/\{[A-Za-z_][\w.]*\}/g, ' ');                // a format field: its name is code, not a word
    if (/^[a-z_][a-z0-9_]*$/.test(s)) continue;               // a dict key or an identifier
    out.push([line, s]);
  }
  return out;
}

/** The customer sentences of the Python files of Lithuanian and Hungarian (api/_lib/pay_*, withdraw_*, iris_*, analyze_*
 *  for lt and hu): no en or em dash, no untranslated English or German, no flagged Lithuanian wording. */
function checkPyTexts(root, out) {
  for (const l of NEW_LANGS) {
    for (const f of ['pay', 'withdraw', 'iris', 'analyze']) {
      const rel = `api/_lib/${f}_${l}.py`;
      let text;
      try { text = readFileSync(join(root, rel), 'utf8').replace(/\r\n/g, '\n'); } catch { out.push(`${rel}: not found (the text check reads it)`); continue; }
      for (const [line, s] of pyStrings(text)) if (s.length > 2) lint(`${rel}:${line}`, s, l, out, false);
    }
  }
}

/** The customer sentences of the compose API (api/compose.py WORDS: one sentence per refusal key in each of en, de, lt and hu), as
 *  [lang, path, text] triples, so that they go through the checks of a dictionary string (an en or em dash, untranslated English or
 *  German in Lithuanian or Hungarian, the typography lint, a sentence word for word the English one). Every key must have all four
 *  languages. The rest of the file is code and error text the page never shows, and is not read as prose. */
function composeWords(root, out) {
  const rel = 'api/compose.py';
  let text;
  try { text = readFileSync(join(root, rel), 'utf8').replace(/\r\n/g, '\n'); } catch { out.push(`${rel}: not found (the text check reads it)`); return []; }
  const from = text.indexOf('\nWORDS = {');
  const to = from < 0 ? -1 : text.indexOf('\n}\n', from);
  if (from < 0 || to < 0) { out.push(`${rel}: WORDS not found (the text check reads it)`); return []; }
  const triples = [];
  for (const row of text.slice(from, to + 2).matchAll(/^ {4}"([a-z_]+)": \{([^}]*)\}/gm)) {
    const seen = new Set();
    for (const m of row[2].matchAll(/"(en|de|lt|hu)":\s*"((?:[^"\\]|\\.)*)"/g)) {
      let s;
      try { s = JSON.parse(`"${m[2]}"`); } catch { out.push(`${rel}: WORDS.${row[1]}.${m[1]} is not a plain string`); continue; }
      seen.add(m[1]);
      triples.push([m[1], `${rel} WORDS.${row[1]}`, s]);
    }
    for (const l of LANGS) if (!seen.has(l)) out.push(`${rel}: WORDS.${row[1]} has no ${l} sentence`);
  }
  if (!triples.length) out.push(`${rel}: WORDS has no sentence (the text check reads it)`);
  return triples;
}

// ------------------------------------------------------------------------------------------ walking two dictionaries
function callFn(fn, args) {
  try { return fn(...args); } catch (e) { return new Error(String(e)); }
}

/** Compare a dictionary of `lang` with the English one (same shape), and collect every string of `lang` (functions are
 *  called with SAMPLES) into strings. surface: 'landing', 'try', 'order', 'legal' (for the message and the SAMPLES path). */
function walk(en, x, path, lang, surface, out, strings) {
  const ke = typeof en, kx = typeof x;
  if (ke !== kx || Array.isArray(en) !== Array.isArray(x)) {
    out.push(`${surface}.${path} (${lang}): another kind of value than the English one (${Array.isArray(en) ? 'array' : ke} against ${Array.isArray(x) ? 'array' : kx})`);
    return;
  }
  if (ke === 'string') {
    if (!/(^|\.)(doc|section)$/.test(path)) strings.push([`${surface}.${path}`, x]);   // link targets are not words
    return;
  }
  if (ke === 'function') {
    if (en.length !== x.length) out.push(`${surface}.${path} (${lang}): takes ${x.length} arguments, the English function ${en.length}`);
    const sets = SAMPLES[path];
    if (!sets) { out.push(`${surface}.${path}: no sample arguments in scripts/check_texts.mjs SAMPLES (needed to check ${lang})`); return; }
    for (const args of sets) {
      const a = callFn(en, args), b = callFn(x, args);
      if (b instanceof Error) { out.push(`${surface}.${path}(${JSON.stringify(args)}) (${lang}) throws: ${b.message}`); continue; }
      if (a instanceof Error) continue;
      if (typeof b === 'string') strings.push([`${surface}.${path}(${args.map((v) => JSON.stringify(v)).join(', ')})`, b]);
      else out.push(`${surface}.${path}(${JSON.stringify(args)}) (${lang}) does not return a string`);
    }
    return;
  }
  if (Array.isArray(en)) {
    if (en.length !== x.length) out.push(`${surface}.${path} (${lang}): ${x.length} items, the English list ${en.length}`);
    en.forEach((v, i) => { if (i < x.length) walk(v, x[i], `${path}[${i}]`, lang, surface, out, strings); });
    return;
  }
  if (en && typeof en === 'object') {
    // the offer of Australian dollars exists in English and German only: the Australian market has no other language
    const skip = path === 'marketHint' && NEW_LANGS.includes(lang) ? ['aud'] : [];
    const a = Object.keys(en).filter((k) => !skip.includes(k)).sort().join(), b = Object.keys(x ?? {}).sort().join();
    if (a !== b) out.push(`${surface}.${path || '.'} (${lang}): other keys than the English dictionary\n   en: ${a}\n   ${lang}: ${b}`);
    for (const k of Object.keys(en)) if (x && k in x && !skip.includes(k)) walk(en[k], x[k], path ? `${path}.${k}` : k, lang, surface, out, strings);
    return;
  }
  if (path.endsWith('lang')) return;
  if (en !== x && typeof en !== 'boolean') out.push(`${surface}.${path} (${lang}): a value (${String(x)}) where the English one is ${String(en)}`);
}

// ------------------------------------------------------------------------------------------ the legal texts
const kinds = (b) => (typeof b === 'string' ? 's' : 'ul' in b ? `ul${b.ul.length}` : 'dl' in b ? `dl${b.dl.length}` : `box${b.box.length}${b.label ? 'L' : ''}`);
// The Hungarian texts carry what Hungarian law asks for on top of the English ones (the terms' added paragraphs on the
// file's functionality, defects, complaints and out-of-court bodies; the statutory model form has no "delete as
// appropriate" line): for them the paragraphs and the size of a form's box are not compared, everything else is.
const looseKinds = (b) => (typeof b === 'string' ? '' : 'ul' in b ? `ul${b.ul.length}` : 'dl' in b ? `dl${b.dl.length}` : 'box');
const linkList = (blocks) => [...JSON.stringify(blocks).matchAll(/\]\(([^)]+)\)/g)].map((m) => m[1].replace(/lang=[a-z]{2}/, 'lang=?').replace(/subject=[^)"]*/, 'subject=?'));

function checkDoc(id, edition, lang, en, doc, out, strings) {
  const at = `legal ${edition}.${id} (${lang})`;
  if (!doc) { out.push(`${at}: missing`); return; }
  const ids = (d) => d.sections.map((s) => s.id).join(',');
  if (ids(en) !== ids(doc)) out.push(`${at}: other section ids than the English text (${ids(doc)} against ${ids(en)})`);
  en.sections.forEach((s, j) => {
    const t = doc.sections[j];
    if (!t) return;
    const kf = lang === 'hu' ? looseKinds : kinds;
    const a = s.blocks.map(kf).filter(Boolean).join(','), b = t.blocks.map(kf).filter(Boolean).join(',');
    if (a !== b) out.push(`${at}.${s.id}: other block kinds than the English text (${b} against ${a})`);
    const la = linkList(s.blocks), lb = linkList(t.blocks);
    const same = lang === 'hu' ? la.every((x) => lb.includes(x)) : la.join(' ') === lb.join(' ');   // hu: its added paragraphs may link too
    if (!same) out.push(`${at}.${s.id}: other links than the English text
   en: ${la.join(' ')}
   ${lang}: ${lb.join(' ')}`);
  });
  strings.push([`${at}.title`, doc.title.replace(SHY, '')], [`${at}.description`, doc.description]);
  if (doc.lead) strings.push([`${at}.lead`, doc.lead]);
  for (const s of doc.sections) {
    strings.push([`${at}.${s.id}.title`, s.title.replace(SHY, '')]);
    for (const b of s.blocks) {
      if (typeof b === 'string') strings.push([`${at}.${s.id}`, b]);
      else if ('ul' in b) b.ul.forEach((li) => strings.push([`${at}.${s.id}`, li]));
      else if ('dl' in b) b.dl.forEach(([k, v]) => strings.push([`${at}.${s.id}`, k], [`${at}.${s.id}`, v]));
      else b.box.forEach((li) => strings.push([`${at}.${s.id}`, li]));
    }
  }
}

// the sentence of each language's terms that names the contract languages, and how it names each language
const CONTRACT = {
  en: { sentence: /^The contract languages are/, words: { en: 'English', de: 'German', lt: 'Lithuanian', hu: 'Hungarian' } },
  de: { sentence: /^Vertragssprachen sind/, words: { en: 'Englisch', de: 'Deutsch', lt: 'Litauisch', hu: 'Ungarisch' } },
  lt: { sentence: /^Sutarties kalbos:/, words: { en: 'anglų', de: 'vokiečių', lt: 'lietuvių', hu: 'vengrų' } },
  hu: { sentence: /^A szerződés nyelve/, words: { en: 'angol', de: 'német', lt: 'litván', hu: 'magyar' } },
};

const isoDay = (v) => (typeof v === 'string' && /^\d{4}-\d{2}-\d{2}/.test(v) ? v.slice(0, 10) : null);
/** The calendar day it is now in the earliest time zone (UTC+14): a date after it is a date in the future everywhere. */
const latestToday = () => new Date(Date.now() + 14 * 3600 * 1000).toISOString().slice(0, 10);

function sourceFiles(root, dir, acc) {
  let names = [];
  try { names = readdirSync(join(root, dir)); } catch { return acc; }
  for (const n of names) {
    if (n === 'node_modules' || n === '__pycache__' || n === 'assets' || n === '_assets' || n.startsWith('.')) continue;
    const rel = dir ? `${dir}/${n}` : n;
    if (statSync(join(root, rel)).isDirectory()) sourceFiles(root, rel, acc);
    else if (/\.(ts|tsx|mts|mjs|py|html|css|md|xml|txt|json)$/.test(n) && n !== 'package-lock.json') acc.push(rel);
  }
  return acc;
}

/** Every problem found in the legal pack the order confirmation email carries (src/legal/plain.ts legalMailPack, which the
 *  build writes to /legal/order-mail.json: vite.config.ts checks the very JSON it is about to write): every text of every
 *  language of every edition is there, the terms print their market's prices in its currency and no other currency's,
 *  name every contract language of the edition, and no Lithuanian or Hungarian text holds an en or em dash, a typographic
 *  slip or untranslated English. pack: the pack (or the file, parsed); legal, markets: src/shared/legal.ts and markets.ts. */
export function checkPack(pack, legal, markets) {
  const out = [];
  const perEdition = { eu: pack.docs, au: pack.editions.au, hu: pack.editions.hu };
  const money = markets.money;
  const cur = (m) => markets.MARKETS[m].currency;
  const priceTexts = (market, l) => Object.values(markets.MARKETS[market].prices).map((v) => money(v, cur(market), l));
  const editionMarket = { eu: markets.DEFAULT_MARKET, ...legal.EDITION_MARKETS };
  for (const [edition, langs] of Object.entries(legal.EDITION_LANGS)) {
    const docs = perEdition[edition] ?? {};
    for (const l of LANGS) {
      const has = docs[l];
      if (langs.includes(l) && !(has && has.terms && has.withdrawal && has.terms.text.length > 400 && has.withdrawal.text.length > 400)) {
        out.push(`legal pack: the ${edition} edition has no complete ${l} texts`);
        continue;
      }
      if (!langs.includes(l)) { if (has) out.push(`legal pack: the ${edition} edition has ${l} texts that EDITION_LANGS does not list`); continue; }
      const terms = has.terms.text.replace(NBSP_RE, ' ');
      const own = editionMarket[edition];
      // the edition's terms print its own market's four prices, in its currency
      for (const p of priceTexts(own, l)) {
        if (!terms.includes(p.replace(NBSP_RE, ' '))) out.push(`legal pack: the ${edition} edition's ${l} terms do not print the price ${p}`);
      }
      // and no other currency's price table (the euro list in the forint terms, the forint list in the euro ones, ...)
      for (const [m, def] of Object.entries(markets.MARKETS)) {
        if (def.currency === cur(own)) continue;
        for (const p of priceTexts(m, l)) {
          if (terms.includes(p.replace(NBSP_RE, ' '))) out.push(`legal pack: the ${edition} edition's ${l} terms print ${p}, a ${def.currency.toUpperCase()} price of the ${m} market`);
        }
      }
      // the contract languages: every language the edition can be read in, and no other
      const c = CONTRACT[l];
      const para = terms.split('\n').find((x) => c.sentence.test(x));
      if (!para) out.push(`legal pack: the ${edition} edition's ${l} terms do not say which languages the contract is in`);
      else {
        for (const k of LANGS) {
          const named = para.includes(c.words[k]);
          if (langs.includes(k) && !named) out.push(`legal pack: the ${edition} edition's ${l} terms do not name ${k} among the contract languages ("${para.slice(0, 100)}")`);
          if (!langs.includes(k) && named) out.push(`legal pack: the ${edition} edition's ${l} terms name ${k} among the contract languages, but the edition has no ${k} texts ("${para.slice(0, 100)}")`);
        }
      }
    }
  }
  for (const l of LANGS) {
    for (const k of ['company', 'address', 'contact']) if (!String(pack.seller[k][l] ?? '').trim()) out.push(`legal pack: seller.${k}.${l} is empty`);
    for (const [where, t] of [['seller.company', pack.seller.company[l]], ['seller.address', pack.seller.address[l]], ['seller.contact', pack.seller.contact[l]]]) lint(where, t, l, out);
  }
  for (const [ed, docs] of Object.entries(perEdition)) for (const [l, d] of Object.entries(docs)) for (const k of ['terms', 'withdrawal']) lint(`legal pack ${ed}.${l}.${k}`, d[k].text.replace(/\n/g, ' ').replace(/ {2,}/g, ' '), l, out);
  return out;
}

/** The customer sentences of api/analyze.py in every language it answers in: TEXT_DE (api/analyze.py), TEXT_LT
 *  (api/_lib/analyze_lt.py) and TEXT_HU (api/_lib/analyze_hu.py) have the same keys and the same {placeholders}, and every
 *  reason analyze() can block a photo for (BLOCK_MESSAGES) has a sentence in each language and a block on the /try page
 *  (BlockReason in src/try/copy.ts). A key missing from one dictionary would stop every request of that language that
 *  needs it with a KeyError, so this reads the Python files as text and stops the build. */
export function checkAnalyzeTexts(root) {
  const out = [];
  const read = (rel) => { try { return readFileSync(join(root, rel), 'utf8').replace(/\r\n/g, '\n'); } catch { return null; } };
  const entries = (text, name) => {
    const m = new RegExp(`^${name} = \\{\\n([\\s\\S]*?)\\n\\}`, 'm').exec(text ?? '');
    if (!m) return null;
    const parts = m[1].split(/^    "([a-z_]+)":/m);   // ['', key, text, key, text, ...]
    const dict = {};
    for (let i = 1; i < parts.length; i += 2) dict[parts[i]] = [...parts[i + 1].matchAll(/\{([a-z_]+)\}/g)].map((x) => x[1]).sort().join();
    return dict;
  };
  const src = read('api/analyze.py');
  const de = entries(src, 'TEXT_DE');
  if (!de) return ['api/analyze.py: TEXT_DE not found (the text check reads it)'];
  const dicts = { de, lt: entries(read('api/_lib/analyze_lt.py'), 'TEXT_LT'), hu: entries(read('api/_lib/analyze_hu.py'), 'TEXT_HU') };
  const reasons = [...(/^BLOCK_MESSAGES = \{([^}]*)\}/m.exec(src)?.[1] ?? '').matchAll(/"([a-z_]+)":/g)].map((x) => x[1]);
  for (const x of src.matchAll(/^BLOCK_MESSAGES\["([a-z_]+)"\] =/gm)) reasons.push(x[1]);
  if (!reasons.length) out.push('api/analyze.py: BLOCK_MESSAGES not found (the text check reads it)');
  for (const [l, d] of Object.entries(dicts)) {
    if (!d) { out.push(`api/analyze.py texts: the ${l} dictionary was not found`); continue; }
    for (const k of Object.keys(de)) {
      if (!(k in d)) out.push(`api/analyze.py texts: ${l} has no "${k}" sentence (TEXT_DE has it)`);
      else if (d[k] !== de[k]) out.push(`api/analyze.py texts: "${k}" in ${l} has the placeholders {${d[k]}}, TEXT_DE's has {${de[k]}}`);
    }
    for (const k of Object.keys(d)) if (!(k in de)) out.push(`api/analyze.py texts: ${l} has a "${k}" sentence that TEXT_DE lacks`);
    for (const r of reasons) if (!(r in d)) out.push(`api/analyze.py texts: the block reason "${r}" has no ${l} sentence: a photo blocked for it would raise a KeyError`);
  }
  const type = /export type BlockReason =([^;]*);/.exec(read('src/try/copy.ts') ?? '')?.[1] ?? '';
  const page = [...type.matchAll(/'([a-z_]+)'/g)].map((x) => x[1]);
  for (const r of reasons) if (!page.includes(r)) out.push(`src/try/copy.ts BlockReason lacks "${r}", a reason api/analyze.py gives (no block copy in any language)`);
  for (const r of page) if (!reasons.includes(r)) out.push(`src/try/copy.ts BlockReason has "${r}", which api/analyze.py never gives`);
  return out;
}

/** The string that follows `marker` in a Python file: adjacent double-quoted literals, optionally in parentheses
 *  ("a " "b" is "a b"), or null when there is none. The two sentences a customer agrees to are written once in the page
 *  (src/) and once on the server (api/), and have to be the same words. */
function pyValue(text, marker, from = 0) {
  const k = text.indexOf(marker, from);
  if (k < 0) return null;
  let i = k + marker.length, out = '', seen = false;
  for (;;) {
    while (i < text.length && /[\s(]/.test(text[i])) i++;
    if (text[i] !== '"') break;
    let j = i + 1;
    while (j < text.length && text[j] !== '"') j += text[j] === '\\' ? 2 : 1;
    out += JSON.parse(text.slice(i, j + 1));
    seen = true;
    i = j + 1;
  }
  return seen ? out : null;
}

/** sha256 of the consent texts that belong to each consent version (the four languages of the EU edition and the two of the
 *  Australian one, as api/_lib/pay.py has them, in this order: en, de, lt, hu, au en, au de). The version is what an order
 *  records next to its own copy of the text, so a text that changes under the same version would make the record say
 *  something else than what the customer ticked. Changing a consent text means a new CONSENT_VERSION in api/_lib/pay.py
 *  and WITHDRAWAL_CONSENT_VERSION in src/shared/legal.ts, and its fingerprint here (the check prints it). */
export const CONSENT_FINGERPRINTS = {
  '2026-09-30.2': '1323e13de556f0533c0d3891789e3d49da9bc7cf15a506fc33cffddb97eee7b7',
};

/** The withdrawal waiver the checkbox shows and the server records (src/shared/legal.ts CHECKOUT_LEGAL, api/_lib/pay.py
 *  CONSENT_TEXT) and the statement the order page sends with the withdrawal and the server stores (src/order/copy.ts
 *  withdraw.statement, api/_lib/withdraw.py STATEMENT), word for word in every language. A customer's consent is recorded
 *  with a fingerprint of the server's text: a page that showed other words would record consent to words it never showed. */
export function checkServerTexts(root, legal, orderCopy) {
  const out = [];
  const read = (rel) => { try { return readFileSync(join(root, rel), 'utf8').replace(/\r\n/g, '\n'); } catch { return null; } };
  const pay = read('api/_lib/pay.py'), withdraw = read('api/_lib/withdraw.py');
  const files = { payLt: read('api/_lib/pay_lt.py'), payHu: read('api/_lib/pay_hu.py'), wLt: read('api/_lib/withdraw_lt.py'), wHu: read('api/_lib/withdraw_hu.py') };
  if (pay === null || withdraw === null || Object.values(files).some((f) => f === null)) return ['api/_lib/pay.py, withdraw.py, pay_lt.py, pay_hu.py, withdraw_lt.py or withdraw_hu.py not found (the text check reads them)'];
  const base = pay.indexOf('CONSENT_TEXT_EN_DE = {');
  const consent = {
    en: pyValue(pay, '"en":', base), de: pyValue(pay, '"de":', base),
    lt: pyValue(files.payLt, '\nCONSENT_TEXT_LT ='), hu: pyValue(files.payHu, '\nCONSENT_TEXT_HU ='),
  };
  const wbase = withdraw.indexOf('STATEMENT = {');
  const statement = {
    en: pyValue(withdraw, '"en":', wbase), de: pyValue(withdraw, '"de":', wbase),
    lt: pyValue(files.wLt, '\nSTATEMENT_LT ='), hu: pyValue(files.wHu, '\nSTATEMENT_HU ='),
  };
  for (const l of LANGS) {
    if (consent[l] === null) out.push(`the ${l} withdrawal waiver was not found in the server files (the text check reads it)`);
    else if (consent[l] !== legal.CHECKOUT_LEGAL[l].withdrawalConsent) {
      out.push(`the ${l} withdrawal waiver differs between the page (src/shared/legal.ts CHECKOUT_LEGAL.${l}.withdrawalConsent) and the server (api/_lib/pay.py CONSENT_TEXT): it must be the same words`);
    }
    if (statement[l] === null) out.push(`the ${l} withdrawal statement was not found in the server files (the text check reads it)`);
    else if (statement[l] !== orderCopy.ORDER_COPY[l].withdraw.statement('{order}')) {
      out.push(`the ${l} withdrawal statement differs between the order page (src/order/copy.ts withdraw.statement) and the server (api/_lib/withdraw.py STATEMENT): it must be the same words`);
    }
  }
  // the consent texts belong to their version: the fingerprint of the current version's texts is the one on record
  const auBase = pay.indexOf('CONSENT_TEXT_AU = {');
  const au = auBase < 0 ? { en: null, de: null } : { en: pyValue(pay, '"en":', auBase), de: pyValue(pay, '"de":', auBase) };
  const texts = [consent.en, consent.de, consent.lt, consent.hu, au.en, au.de];
  if (texts.some((t) => t === null)) out.push('a consent text was not found in api/_lib/pay.py, pay_lt.py or pay_hu.py (the text check reads them for its fingerprint)');
  else {
    const version = legal.WITHDRAWAL_CONSENT_VERSION;
    const print = createHash('sha256').update(JSON.stringify(texts)).digest('hex');
    if (!(version in CONSENT_FINGERPRINTS)) {
      out.push(`consent version "${version}" has no fingerprint in scripts/check_texts.mjs CONSENT_FINGERPRINTS: add  '${version}': '${print}'`);
    } else if (CONSENT_FINGERPRINTS[version] !== print) {
      out.push(`a consent text changed under the same version "${version}" (fingerprint now ${print}, on record ${CONSENT_FINGERPRINTS[version]}): a new text needs a new CONSENT_VERSION in api/_lib/pay.py and WITHDRAWAL_CONSENT_VERSION in src/shared/legal.ts together, and its fingerprint in CONSENT_FINGERPRINTS`);
    }
  }
  return out;
}

// ------------------------------------------------------------------------------------------ the new landing's copy
const COPY_DIR = 'src/landing/copy';
// a spaced hyphen (a hyphen between two spaces) is a dash in disguise (owner rule: no dash anywhere)
const SPACED_HYPHEN = /(^|[  ])-([  ]|$)/;
// claims the page must never make (hard rule of the landing v2 port): phrases, in the languages the copy is checked in
const BANNED_CLAIMS = /ready to print|print[- ]ready|druckfertig|druckbereit|100 ?(percent|%|prozent)|museum[- ]?glass|museumsglas/i;
// Lines that must stay where the prototype has them, per language: the words of the line in that language, and the copy
// paths (keys) that hold it. Lithuanian hero.caption says "neįskaičiuotas" (not included, as hero.lead and hero.chipBody do in
// every language) where the others say "not part of your order": the same promise in a shorter caption, so `alt` names the
// strings that must hold the other wording instead.
// The strings that say "Printing is not part of your order", and no others do: the hero caption, the sentence under the wall title, the
// pricing block, the FAQ answer about printing, the closing scene, and (fix round: a price or a picture of a printed piece must not
// stand without it) the line under a tile that is shown on a wall (styles.wallFile) and the caption of the polished edge.
const PRINTING_KEYS = ['hero.caption', 'wall.intro', 'pricing.notIncludes', 'faq.items.1.a', 'final.small', 'styles.wallFile', 'closeups.edgeCaption'];
const HONESTY = {
  en: {
    chips: { 'example.chip': 'Example', 'example.vis': 'AI visualisation' },
    printing: { re: /Printing is not part of your order/i, keys: PRINTING_KEYS },
    soon: { re: /Ordering opens soon/i, keys: ['bar.soon', 'pricing.notice', 'faq.items.14.a'] },
  },
  de: {
    chips: { 'example.chip': 'Beispiel', 'example.vis': 'KI-Visualisierung' },
    printing: { re: /Der Druck gehört nicht zur Bestellung/i, keys: PRINTING_KEYS },
    soon: { re: /Bestellungen sind bald möglich/i, keys: ['bar.soon', 'pricing.notice', 'faq.items.14.a'] },
  },
  lt: {
    chips: { 'example.chip': 'Pavyzdys', 'example.vis': 'DI vizualizacija' },
    printing: { re: /Spausdinimas nėra Jūsų užsakymo dalis/i, keys: PRINTING_KEYS.filter((k) => k !== 'hero.caption'), alt: { 'hero.caption': /Spausdinimas neįskaičiuotas/i } },
    soon: { re: /Užsakymus pradėsime priimti netrukus/i, keys: ['bar.soon', 'pricing.notice', 'faq.items.14.a'] },
  },
  hu: {
    chips: { 'example.chip': 'Példa', 'example.vis': 'MI-vizualizáció' },
    printing: { re: /A nyomtatás nem része a rendelésnek/i, keys: PRINTING_KEYS },
    soon: { re: /A rendelés hamarosan indul/i, keys: ['bar.soon', 'pricing.notice', 'faq.items.14.a'] },
  },
};
// the question of the FAQ item "withdraw" is pinned to the words of src/landing/copy.ts WITHDRAW_Q (the old landing keyed its
// Australian override on them; the landing replaces by id now, but the words are not to drift)

// copy paths whose value is an identifier or a file name, not a sentence: the FAQ item ids (faq.items.N.id), the demo file name
const NOT_PROSE = /(^|\.)id$|^how\.fileName$/;

const tokensOf = (s) => [...String(s).matchAll(/\{([a-zA-Z0-9]+)\}/g)].map((m) => m[1]);
const blankTokens = (s) => s.replace(/\{[a-zA-Z0-9]+\}/g, '0');
const dig = (o, path) => path.split('.').reduce((v, k) => (v == null ? v : v[k]), o);

function leafPaths(o, path = '', out = []) {
  if (Array.isArray(o)) o.forEach((v, i) => leafPaths(v, path ? `${path}.${i}` : String(i), out));
  else if (o && typeof o === 'object') for (const [k, v] of Object.entries(o)) leafPaths(v, path ? `${path}.${k}` : k, out);
  else out.push([path, o]);
  return out;
}

/** Compare a language file with en.json: same keys, same kinds, same list lengths, same numbers, same {tokens} in every string. */
function walkCopyJson(en, x, path, at, out) {
  const tag = `${at}${path ? `.${path}` : ''}`;
  const kind = (v) => (v === null ? 'null' : Array.isArray(v) ? 'list' : typeof v);
  if (kind(en) !== kind(x)) { out.push(`${tag}: a ${kind(x)} where en.json has a ${kind(en)}`); return; }
  if (typeof en === 'string') {
    const a = tokensOf(en).sort(), b = tokensOf(x).sort();
    if (a.join() !== b.join()) out.push(`${tag}: the tokens are {${b.join('}, {')}}, en.json has {${a.join('}, {')}}: ${x.slice(0, 90)}`);
    return;
  }
  if (Array.isArray(en)) {
    if (en.length !== x.length) out.push(`${tag}: ${x.length} items, en.json has ${en.length}`);
    en.forEach((v, i) => { if (i < x.length) walkCopyJson(v, x[i], path ? `${path}.${i}` : String(i), at, out); });
    return;
  }
  if (en && typeof en === 'object') {
    const a = Object.keys(en), b = Object.keys(x);
    const missing = a.filter((k) => !b.includes(k)), extra = b.filter((k) => !a.includes(k));
    if (missing.length) out.push(`${tag}: lacks ${missing.join(', ')} (en.json has it)`);
    if (extra.length) out.push(`${tag}: has ${extra.join(', ')}, which en.json lacks`);
    for (const k of a) if (k in x) walkCopyJson(en[k], x[k], path ? `${path}.${k}` : k, at, out);
    return;
  }
  if (en !== x) out.push(`${tag}: ${String(x)} where en.json has ${String(en)}`);
}

/** The copy files of the new landing: every problem as a sentence. strings: the per language lists of the lint (every
 *  string of en, de and of every translated lt or hu file joins them, so the dash, the typography, the untranslated English
 *  and the word for word checks treat them like every other dictionary). */
function checkLandingCopy(root, mods, strings, out) {
  const { lang, legal, config, format, oldCopy } = mods;
  const WITHDRAW_Q = oldCopy.WITHDRAW_Q;
  const read = (rel) => { try { return readFileSync(join(root, rel), 'utf8').replace(/^﻿/, ''); } catch { return null; } };
  const files = {};
  for (const l of lang.LANGS) {
    const rel = `${COPY_DIR}/${l}.json`;
    const text = read(rel);
    if (text === null) {
      out.push(`${rel}: missing. ${l} is a language of the site (src/shared/lang.ts LANGS), so the new landing needs its copy: drop the translation here with the keys and {tokens} of en.json`);
      continue;
    }
    try { files[l] = JSON.parse(text); } catch (e) { out.push(`${rel}: not valid JSON (${e instanceof Error ? e.message : String(e)})`); }
  }
  const en = files.en;
  if (!en) return;
  for (const l of lang.LANGS) {
    const x = files[l];
    if (!x) continue;
    const rel = `${COPY_DIR}/${l}.json`;
    if (l !== 'en') {
      // the offer of Australian dollars (marketHint.aud) belongs to the languages of the Australian edition (English and German) and to
      // no other: a Lithuanian or Hungarian visitor who took it would land on a page in English (src/landing/MarketHint.tsx offers a
      // market only in a language its edition has, and this keeps the words from existing where they could never be shown)
      const auOk = lang.langAllowed(l, 'au');
      const hasAud = x.marketHint && 'aud' in x.marketHint;
      if (hasAud && !auOk) out.push(`${rel}: marketHint.aud must not exist: the Australian edition has no texts in ${l} (src/shared/legal.ts EDITION_LANGS), so a visitor could never be offered it in ${l}`);
      const without = (o) => (o.marketHint ? { ...o, marketHint: Object.fromEntries(Object.entries(o.marketHint).filter(([k]) => k !== 'aud')) } : o);
      walkCopyJson(auOk ? en : without(en), auOk ? x : without(x), '', rel, out);
    }
    const leaves = leafPaths(x);
    // every string of every language: the tokens exist, no spaced hyphen, none of the banned claims
    for (const [p, v] of leaves) {
      if (typeof v !== 'string') continue;
      for (const k of tokensOf(v)) if (!format.TOKENS.includes(k)) out.push(`${rel}: ${p} holds the token {${k}}, which the page does not know (src/landing/copy/format.ts TOKENS)`);
      if (SPACED_HYPHEN.test(v)) out.push(`${rel}: ${p} holds a spaced hyphen (a dash in disguise; owner rule: none): ${v.slice(0, 90)}`);
      if (BANNED_CLAIMS.test(v)) out.push(`${rel}: ${p} makes a claim the page must not make ("${BANNED_CLAIMS.exec(v)[0]}"): ${v.slice(0, 90)}`);
    }
    // what a language says about itself, and the facts, against the single sources
    if (x.meta?.locale !== lang.LOCALES[l].og) out.push(`${rel}: meta.locale is "${x.meta?.locale}", src/shared/lang.ts LOCALES.${l}.og is "${lang.LOCALES[l].og}"`);
    if (x.langName !== lang.LANG_NAMES[l]) out.push(`${rel}: langName is "${x.langName}", src/shared/lang.ts LANG_NAMES.${l} is "${lang.LANG_NAMES[l]}"`);
    if (x.facts?.email !== config.CONTACT_EMAIL) out.push(`${rel}: facts.email is "${x.facts?.email}", src/landing/config.ts CONTACT_EMAIL is "${config.CONTACT_EMAIL}"`);
    if (x.facts?.hours !== String(config.DELIVERY_MAX_HOURS)) out.push(`${rel}: facts.hours is "${x.facts?.hours}", the delivery promise DELIVERY_MAX_HOURS (src/landing/config.ts) is ${config.DELIVERY_MAX_HOURS}`);
    // the faq: the same ids in the same order, and the Australian answers belong to ids that exist
    const ids = (f) => (f?.faq?.items ?? []).map((it) => it.id);
    if (ids(x).join() !== ids(en).join()) out.push(`${rel}: faq.items has the ids ${ids(x).join(', ')}, en.json has ${ids(en).join(', ')} (same ids, same order)`);
    for (const k of Object.keys(x.faqAu ?? {})) if (!ids(x).includes(k)) out.push(`${rel}: faqAu.${k} replaces no faq item (no item has that id)`);
    // the statutory words of the legal links, and the online withdrawal button inside the withdrawal answers
    const labels = legal.LEGAL_LABELS[l], online = legal.WITHDRAWAL_ONLINE[l];
    for (const d of ['privacy', 'terms', 'withdrawal', 'imprint']) if (x.footer?.legal?.[d] !== labels[d]) out.push(`${rel}: footer.legal.${d} is "${x.footer?.legal?.[d]}", src/shared/legal.ts LEGAL_LABELS.${l}.${d} is "${labels[d]}"`);
    if (x.footer?.legalNav !== labels.nav) out.push(`${rel}: footer.legalNav is "${x.footer?.legalNav}", LEGAL_LABELS.${l}.nav is "${labels.nav}"`);
    if (x.footer?.legal?.withdrawFn !== online.button) out.push(`${rel}: footer.legal.withdrawFn is "${x.footer?.legal?.withdrawFn}", WITHDRAWAL_ONLINE.${l}.button is "${online.button}"`);
    const w = (x.faq?.items ?? []).find((it) => it.id === 'withdraw');
    if (w && !w.a.includes(online.button)) out.push(`${rel}: the faq answer "withdraw" does not name the online withdrawal button "${online.button}" (src/shared/legal.ts WITHDRAWAL_ONLINE.${l}.button)`);
    // the button of the phone picture in step 2 (shown once ordering is open) is the real checkout button of /try: its statutory label
    // (in Hungary the one that says the order carries an obligation to pay), not a friendlier one
    if (x.how?.previewButton !== legal.CHECKOUT_LEGAL[l].continueButton) out.push(`${rel}: how.previewButton is "${x.how?.previewButton}", the checkout button of /try says "${legal.CHECKOUT_LEGAL[l].continueButton}" (src/shared/legal.ts CHECKOUT_LEGAL.${l}.continueButton)`);
    if (x.faqAu?.withdraw && !x.faqAu.withdraw.a.includes(online.button)) out.push(`${rel}: faqAu.withdraw.a does not name the online withdrawal button "${online.button}"`);
    if (WITHDRAW_Q[l] !== undefined && w?.q !== WITHDRAW_Q[l]) out.push(`${rel}: the faq question "withdraw" is "${w?.q}", it must stay "${WITHDRAW_Q[l]}" word for word`);
    // the honesty lines, where the prototype has them
    const h = HONESTY[l];
    if (h) {
      for (const [p, want] of Object.entries(h.chips)) if (dig(x, p) !== want) out.push(`${rel}: ${p} is "${dig(x, p)}", the label must read "${want}" word for word`);
      for (const p of ['hero.chipTitle', 'final.chip']) if (dig(x, p) !== x.example?.vis) out.push(`${rel}: ${p} ("${dig(x, p)}") must be the same label as example.vis ("${x.example?.vis}")`);
      for (const [p, re] of Object.entries(h.printing.alt ?? {})) if (!re.test(dig(x, p) ?? '')) out.push(`${rel}: ${p} must say that printing is not part of the order in the words ${re} (the caption's own wording)`);
      for (const [what, rule] of Object.entries({ 'the line "printing is not part of your order"': h.printing, 'the line "ordering opens soon"': h.soon })) {
        const where = leaves.filter(([, v]) => typeof v === 'string' && rule.re.test(v)).map(([p]) => p).sort();
        if (where.join() !== [...rule.keys].sort().join()) out.push(`${rel}: ${what} must be in exactly ${rule.keys.join(', ')}; it is in ${where.join(', ') || 'no string'}`);
      }
    }
    // the words join the lint lists of every other dictionary (dash, typography, untranslated English, word for word);
    // not the values that are no prose: the FAQ ids (anchors and keys, English in every language) and the demo file name
    for (const [p, v] of leaves) if (typeof v === 'string' && v !== '' && !NOT_PROSE.test(p)) strings[l].push([`landing copy ${l}.${p}`, blankTokens(v)]);
  }
}

/** Every problem found, as sentences ([] when the texts are sound). load(path): a module of src/ through Vite's module
 *  runner (vite.config.ts); root: the repository. */
export async function checkTexts(load, root) {
  const out = [];
  const [lang, legal, landing, tryCopy, orderCopy, editions, plain, markets, layouts, aiMaterial, config, format] = await Promise.all([
    load('./src/shared/lang.ts'), load('./src/shared/legal.ts'), load('./src/landing/copy.ts'), load('./src/try/copy.ts'),
    load('./src/order/copy.ts'), load('./src/legal/editions.ts'), load('./src/legal/plain.ts'), load('./src/shared/markets.ts'),
    load('./src/shared/layouts.ts'), load('./src/shared/aiMaterial.ts'), load('./src/landing/config.ts'), load('./src/landing/copy/format.ts'),
  ]);
  if (lang.LANGS.join() !== LANGS.join()) out.push(`src/shared/lang.ts LANGS is ${lang.LANGS.join()}, this check knows ${LANGS.join()}: update scripts/check_texts.mjs`);

  // 1 + 2. the dictionaries
  const strings = { en: [], de: [], lt: [], hu: [] };
  const surfaces = [['landing', landing.COPY], ['try', tryCopy.COPY], ['order', orderCopy.ORDER_COPY]];
  for (const [name, dict] of surfaces) {
    for (const l of LANGS) {
      const list = strings[l];
      if (!dict[l]) { out.push(`${name}: no ${l} dictionary`); continue; }
      if (NEW_LANGS.includes(l)) walk(dict.en, dict[l], '', l, name, out, list);
      else walk(dict.en, dict[l], '', l, name, [], list);   // English and German: their strings only, for the dash lint
    }
  }
  // the layout words (api/_lib/layout_names.py through src/shared/layouts.ts): every layout has a word in every language, and each word is
  // linted as a string of its language (no en or em dash, no untranslated English or German in a Lithuanian or Hungarian one)
  for (const [id, row] of Object.entries(layouts.LAYOUT_NAMES)) {
    for (const l of LANGS) {
      if (typeof row[l] !== 'string' || !row[l].trim()) out.push(`layout words: "${id}" has no ${l} word (api/_lib/layout_names.py)`);
      else strings[l].push([`layout words.${id}`, row[l]]);
    }
  }
  // the sentence about AI-made material (src/shared/aiMaterial.ts), published or not: linted and compared like any dictionary string, in every language
  for (const l of LANGS) if (typeof aiMaterial.AI_MATERIAL?.[l] === 'string') strings[l].push([`aiMaterial.${l}`, aiMaterial.AI_MATERIAL[l]]);
  // the refusals of the compose API (api/compose.py WORDS): the same checks as any dictionary string
  for (const [l, p, s] of composeWords(root, out)) strings[l].push([p, s]);
  for (const l of LANGS) {
    const shared = {
      LEGAL_LABELS: legal.LEGAL_LABELS[l], WITHDRAWAL_ONLINE: legal.WITHDRAWAL_ONLINE[l], CHECKOUT_LEGAL: legal.CHECKOUT_LEGAL[l],
    };
    walk({ LEGAL_LABELS: legal.LEGAL_LABELS.en, WITHDRAWAL_ONLINE: legal.WITHDRAWAL_ONLINE.en, CHECKOUT_LEGAL: legal.CHECKOUT_LEGAL.en },
      shared, '', l, 'legal.shared', NEW_LANGS.includes(l) ? out : [], strings[l]);
  }

  // 10. the copy of the new landing (src/landing/copy/*.json)
  checkLandingCopy(root, { lang, legal, config, format, oldCopy: landing }, strings, out);

  // 3. the legal pages of every edition, in every language the edition has
  for (const [edition, langs] of Object.entries(legal.EDITION_LANGS)) {
    for (const id of ['terms', 'privacy', 'withdrawal', 'imprint']) {
      const docs = editions.EDITIONS[edition][id];
      for (const l of LANGS) {
        const listed = langs.includes(l);
        if (!listed && docs[l]) out.push(`legal ${edition}.${id}: has ${l} texts, but src/shared/legal.ts EDITION_LANGS does not list ${l} for the ${edition} edition`);
        // the Australian edition adds sections of its own: only its strings are linted, the others are compared with the English text
        if (listed) checkDoc(id, edition, l, editions.EDITIONS.eu[id].en, docs[l], edition === 'au' ? [] : out, strings[l]);
      }
    }
  }
  for (const l of LANGS) for (const [p, s] of strings[l]) lint(p, s, l, out);
  identical(strings, out);

  // the head of index.html (search and share copy: English only): the same claims, the same dashes
  try {
    const html = readFileSync(join(root, 'index.html'), 'utf8');
    for (const m of html.matchAll(/<(?:title>([^<]*)<\/title>|meta\s+(?:name|property)="([^"]+)"\s+content="([^"]*)")/g)) lint(`index.html ${m[2] ?? 'title'}`, m[1] ?? m[3], 'en', out);
  } catch { out.push('index.html not found (the text check reads its head)'); }

  // the sentence about AI-made material (owner decision 10): written in the four languages, linted like any string while it is unpublished, and present in
  // every terms text once published and in none before (it is published by the cutover deploy, src/shared/aiMaterial.ts)
  for (const l of LANGS) {
    const sentence = aiMaterial.AI_MATERIAL?.[l];
    if (typeof sentence !== 'string' || sentence.length < 80) { out.push(`src/shared/aiMaterial.ts: no ${l} sentence about AI-made material`); continue; }
    for (const [edition, langs] of Object.entries(legal.EDITION_LANGS)) {
      if (!langs.includes(l)) continue;
      const text = JSON.stringify(editions.EDITIONS[edition].terms[l].sections);
      const has = text.includes(JSON.stringify(sentence).slice(1, -1));
      if (aiMaterial.AI_MATERIAL_PUBLISHED && !has) out.push(`legal ${edition}.terms (${l}): the sentence about AI-made material is published (src/shared/aiMaterial.ts) but not in the terms`);
      if (!aiMaterial.AI_MATERIAL_PUBLISHED && has) out.push(`legal ${edition}.terms (${l}): holds the sentence about AI-made material before the cutover publishes it (AI_MATERIAL_PUBLISHED is false)`);
    }
  }

  // the customer sentences of the server's Lithuanian and Hungarian files
  checkPyTexts(root, out);

  // the legal pack the email carries (the same function lints the file the build writes: vite.config.ts legalMail)
  out.push(...checkPack(plain.legalMailPack(), legal, markets));

  // the server's own customer sentences (api/analyze.py): the same keys in every language, one per block reason
  out.push(...checkAnalyzeTexts(root));

  // the two sentences a customer agrees to: the same words on the page and on the server
  out.push(...checkServerTexts(root, legal, orderCopy));

  // 4. the consent version and the date of the legal texts
  const v = legal.WITHDRAWAL_CONSENT_VERSION;
  const today = latestToday();
  if (!/^\d{4}-\d{2}-\d{2}\.\d+$/.test(v)) out.push(`src/shared/legal.ts WITHDRAWAL_CONSENT_VERSION "${v}" is not a date and a counter ("2026-09-30.1")`);
  else if (v.slice(0, 10) > today) out.push(`src/shared/legal.ts WITHDRAWAL_CONSENT_VERSION "${v}" is a date in the future (today is ${today})`);
  if (!isoDay(legal.LEGAL_UPDATED)) out.push(`src/shared/legal.ts LEGAL_UPDATED "${legal.LEGAL_UPDATED}" is not a date`);
  else if (legal.LEGAL_UPDATED > today) out.push(`src/shared/legal.ts LEGAL_UPDATED "${legal.LEGAL_UPDATED}" is a date in the future (today is ${today})`);
  let payPy = '';
  try { payPy = readFileSync(join(root, 'api/_lib/pay.py'), 'utf8'); } catch { /* checked below */ }
  const pv = /^CONSENT_VERSION = "([^"]+)"/m.exec(payPy)?.[1];
  if (!pv) out.push('api/_lib/pay.py: CONSENT_VERSION not found (the text check reads it)');
  else if (pv !== v) out.push(`api/_lib/pay.py CONSENT_VERSION "${pv}" and src/shared/legal.ts WITHDRAWAL_CONSENT_VERSION "${v}" must be the same`);

  // 5. no en or em dash in any source file
  for (const dir of ['src', 'api', 'scripts', 'public']) {
    for (const rel of sourceFiles(root, dir, [])) {
      const t = readFileSync(join(root, rel), 'utf8');
      const i = t.search(DASH);
      if (i >= 0) out.push(`${rel}: an en or em dash (line ${t.slice(0, i).split('\n').length}); the owner's rule: none, anywhere`);
    }
  }
  for (const rel of readdirSync(root).filter((n) => /\.(html|md|json)$/.test(n) && n !== 'package-lock.json')) {
    const t = readFileSync(join(root, rel), 'utf8');
    if (DASH.test(t)) out.push(`${rel}: an en or em dash; the owner's rule: none, anywhere`);
  }
  return [...new Set(out)];
}

// `node scripts/check_texts.mjs` (npm run check:texts): loads src/ through Vite's module runner, exit code 1 on any problem
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const root = join(fileURLToPath(new URL('.', import.meta.url)), '..');
  const require = createRequire(join(root, 'package.json'));
  const { runnerImport } = await import(pathToFileURL(require.resolve('vite')).href);
  const load = async (p) => (await runnerImport(p, { configFile: false, logLevel: 'silent', root })).module;
  const problems = await checkTexts(load, root);
  if (problems.length) {
    console.error(`text check FAILED (${problems.length}):\n  ${problems.join('\n  ')}`);
    process.exit(1);
  }
  console.log('text check ok: lt and hu dictionaries and legal texts match the English ones, every edition complete, no en or em dash');
}
