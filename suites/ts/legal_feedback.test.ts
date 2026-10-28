// The privacy policy says what the feedback box keeps (2026-10-20): the same paragraph, in the same place, in English, German, Lithuanian and Hungarian, in the three editions (the euro texts, the
// Australian edition made from them by patchDoc, and the Hungarian edition), and nothing it says contradicts the box (api/_lib/feedback.py, src/try/Feedback.tsx): six answers, a text of up to
// 300 characters, nothing sent until Send, no field for a name or an e-mail address, a text with contact details or a link not kept, texts deleted after 90 days, nothing written to the browser.
// The words the policy quotes (the button, two chips) are the words the page shows. Pure page code, loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results.
import { EDITIONS } from '../../src/legal/editions';
import { PRIVACY } from '../../src/legal/docs/privacy';
import { COPY } from '../../src/try/copy';
import type { Block, LegalDoc } from '../../src/legal/types';

type Row = [string, boolean, string?];
const LANGS = ['en', 'de', 'lt', 'hu'] as const;
type Lang = (typeof LANGS)[number];
const blockText = (b: Block): string => (typeof b === 'string' ? b : 'ul' in b ? b.ul.join('\n') : 'dl' in b ? b.dl.map((r) => r.join(': ')).join('\n') : b.box.join('\n'));
const section = (d: LegalDoc, id: string) => d.sections.find((s) => s.id === id);
const sectionText = (d: LegalDoc, id: string) => (section(d, id)?.blocks ?? []).map(blockText).join('\n');

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);
  const every = (re: Record<Lang, RegExp>, id: string) => LANGS.every((l) => re[l].test(sectionText(PRIVACY[l], id)));
  const missing = (re: Record<Lang, RegExp>, id: string) => LANGS.filter((l) => !re[l].test(sectionText(PRIVACY[l], id))).join();

  const BOX: Record<Lang, RegExp> = {
    en: /a small feedback box offers six answers/, de: /bietet ein kleines Feedback-Feld sechs Antworten/, lt: /nedidelė atsiliepimų dėžutė siūlo šešis atsakymus/, hu: /egy kis visszajelzés doboz hat választ kínál/,
  };
  check('the operations section has the feedback paragraph in every language', every(BOX, 'operations'), missing(BOX, 'operations'));
  const LIMIT: Record<Lang, RegExp> = { en: /up to 300 characters/, de: /bis zu 300 Zeichen/, lt: /iki 300 simbolių/, hu: /legfeljebb 300 karakteres/ };
  check('and says the text is at most 300 characters (the limit of the box and of the server)', every(LIMIT, 'operations'), missing(LIMIT, 'operations'));
  const SEND: Record<Lang, RegExp> = { en: /Nothing is sent until you press Send/, de: /Es wird nichts gesendet, bis Sie auf „Senden“ drücken/, lt: /Nieko nesiunčiama, kol nepaspaudžiate „Siųsti“/, hu: /Addig semmi nem kerül elküldésre, amíg a „Küldés” gombra nem nyom/ };
  check('and that nothing is sent until the visitor presses Send', every(SEND, 'operations'), missing(SEND, 'operations'));
  const NOFIELD: Record<Lang, RegExp> = {
    en: /no field for your name or email address: please do not write any, nor telephone numbers or links/, de: /kein Eingabefeld für Ihren Namen oder Ihre E-Mail-Adresse: Bitte schreiben Sie keine, auch keine Telefonnummern oder Links/,
    lt: /nėra lauko Jūsų vardui ar el\. pašto adresui: prašome jų nerašyti, taip pat telefono numerių ar nuorodų/, hu: /nincs mező a nevének vagy e-mail-címének: kérjük, ne írjon ilyet, telefonszámot vagy linket sem/,
  };
  check('and that the box has no field for a name or an e-mail address and asks the visitor to write none, nor a telephone number or a link', every(NOFIELD, 'operations'), missing(NOFIELD, 'operations'));
  const DROP: Record<Lang, RegExp> = {
    en: /a text that contains an at sign, a telephone number, a link or what looks like spam is not kept \(your answer is still counted\)/, de: /Ein Text mit einem At-Zeichen, einer Telefonnummer, einem Link oder mit dem Anschein von Spam wird nicht gespeichert \(Ihre Antwort wird trotzdem gezählt\)/,
    lt: /tekstas, kuriame yra ženklas „@“, telefono numeris, nuoroda arba kuris atrodo kaip šlamštas, nesaugomas \(Jūsų atsakymas vis tiek skaičiuojamas\)/, hu: /az a szöveg, amely „@” jelet, telefonszámot vagy linket tartalmaz, illetve kéretlen üzenetnek látszik, nem kerül megőrzésre \(a válaszát ettől még megszámoljuk\)/,
  };
  check('and that a text with an at sign, a telephone number, a link or spam is not kept while the answer is still counted (what the server\'s filter does)', every(DROP, 'operations'), missing(DROP, 'operations'));
  const DAYS: Record<Lang, RegExp> = { en: /Every text is deleted automatically after 90 days, and we can delete one earlier/, de: /Jeder Text wird nach 90 Tagen automatisch gelöscht, und wir können ihn auch früher löschen/, lt: /Kiekvienas tekstas automatiškai ištrinamas po 90 dienų, o anksčiau jį galime ištrinti ir patys/, hu: /Minden szöveget 90 nap után automatikusan törlünk, és korábban is törölhetjük/ };
  check('and that every text is deleted after 90 days (and earlier by hand): the days of the server\'s clean-up', every(DAYS, 'operations'), missing(DAYS, 'operations'));
  const NOREPLY: Record<Lang, RegExp> = { en: /we cannot reply, because we do not know who wrote them/, de: /antworten können wir nicht, weil wir nicht wissen, wer sie geschrieben hat/, lt: /atsakyti negalime, nes nežinome, kas juos parašė/, hu: /válaszolni nem tudunk, mert nem tudjuk, ki írta őket/ };
  check('and that nobody can be answered, and that the text of a visitor is found later only if the visitor tells us what it said', every(NOREPLY, 'operations') && LANGS.every((l) => /(tell us what it said|sagen, was darin stand|pasakytumėte, kas jame|elmondaná, mi állt benne)/.test(sectionText(PRIVACY[l], 'operations'))));
  const BROWSER: Record<Lang, RegExp> = { en: /The box writes nothing to your browser/, de: /Das Feld schreibt nichts in Ihren Browser/, lt: /Dėžutė nieko neįrašo į Jūsų naršyklę/, hu: /A doboz semmit nem ír a böngészőjébe/ };
  check('and that the box writes nothing to the browser', every(BROWSER, 'operations'), missing(BROWSER, 'operations'));
  const CODES: Record<Lang, RegExp> = { en: /the same details as in the step counts above/, de: /dieselben Angaben wie bei den Schrittzählungen oben/, lt: /tos pačios detalės kaip aukščiau aprašytuose žingsnių skaičiavimuose/, hu: /ugyanazok az adatok, mint a fenti lépésszámlálásnál/ };
  check('and that the answer carries the same codes as a step count, never the text (the text is stored apart from the event)', every(CODES, 'operations') && LANGS.every((l) => /(stored apart from them|getrennt davon gespeichert|saugomas atskirai, kaip aprašyta aukščiau|ettől külön tároljuk)/.test(sectionText(PRIVACY[l], 'operations'))));

  // the words the policy quotes are the words of the page
  check('the policy quotes the button and two chips in the words the page shows, in every language', LANGS.every((l) => {
    const f = COPY[l].feedback;
    const t = sectionText(PRIVACY[l], 'operations');
    return t.includes(f.send) && t.includes(f.chips.result.love) && t.includes(f.chips.result.colour);
  }), LANGS.filter((l) => { const f = COPY[l].feedback; const t = sectionText(PRIVACY[l], 'operations'); return !(t.includes(f.send) && t.includes(f.chips.result.love) && t.includes(f.chips.result.colour)); }).join());

  // the retention row, the legal basis, the paragraph about events
  const ROW: Record<Lang, RegExp> = { en: /Feedback texts: [^\n]*after 90 days/, de: /Feedback-Texte: [^\n]*nach 90 Tagen/, lt: /Atsiliepimų tekstai: [^\n]*po 90 dienų/, hu: /Visszajelzések szövegei: [^\n]*90 nap után/ };
  check('the retention section has a row for the feedback texts with the 90 days, in every language', every(ROW, 'retention'), missing(ROW, 'retention'));
  const BASIS: Record<Lang, RegExp> = { en: /the texts of the feedback box after 90 days/, de: /die Texte des Feedback-Felds nach 90 Tagen/, lt: /atsiliepimų dėžutės tekstai po 90 dienų/, hu: /a visszajelzés doboz szövegeit 90 nap után/ };
  check('the legal basis paragraph names the feedback box and its 90 days', every(BASIS, 'operations'), missing(BASIS, 'operations'));
  const CONTENT: Record<Lang, RegExp> = {
    en: /no text you typed \(a text written in the feedback box is stored apart from them, as described above\)/, de: /keinen von Ihnen eingegebenen Text \(ein Text aus dem Feedback-Feld wird getrennt davon gespeichert, wie oben beschrieben\)/,
    lt: /Jūsų įvesto teksto \(atsiliepimų dėžutėje parašytas tekstas saugomas atskirai, kaip aprašyta aukščiau\)/, hu: /Ön által beírt szöveget \(a visszajelzés dobozba írt szöveget ettől külön tároljuk, a fentiek szerint\)/,
  };
  check('the sentence that says the events hold no typed text points to the feedback texts as the one exception, stored apart', every(CONTENT, 'operations'), missing(CONTENT, 'operations'));

  // structure: the paragraph sits between the campaign code and the "these events hold no" sentence in every language
  const order = (l: Lang) => {
    const t = sectionText(PRIVACY[l], 'operations');
    return [CONTENT[l], BOX[l]].map((re) => t.search(re));
  };
  check('and sits before the sentence about what the events hold, after the campaign code paragraph', LANGS.every((l) => { const [c, b] = order(l); return b >= 0 && c > b; }), LANGS.map((l) => order(l).join('<')).join(' | '));

  // editions
  const doc = (e: keyof typeof EDITIONS, l: Lang) => EDITIONS[e].privacy[l];
  check('the Hungarian and the euro editions read the same privacy texts in all four languages', LANGS.every((l) => doc('hu', l) === PRIVACY[l] && doc('eu', l) === PRIVACY[l]));
  const au = EDITIONS.au.privacy;
  check('the Australian edition (English and German) has the same operations and retention sections, so the same feedback paragraph, basis and row',
    !!au.en && !!au.de && (['en', 'de'] as const).every((l) => sectionText(au[l]!, 'operations') === sectionText(PRIVACY[l], 'operations') && sectionText(au[l]!, 'retention') === sectionText(PRIVACY[l], 'retention')));
  const us = EDITIONS.us.privacy;
  check('the US edition (English only) has the same operations and retention sections, so the same feedback paragraph, basis and row',
    !!us.en && !us.de && sectionText(us.en, 'operations') === sectionText(PRIVACY.en, 'operations') && sectionText(us.en, 'retention') === sectionText(PRIVACY.en, 'retention'));
  const dash = new RegExp('[' + [0x2012, 0x2013, 0x2014, 0x2015].map((c) => String.fromCharCode(c)).join('') + ']');
  check('no paragraph of the feedback text holds an en or em dash', LANGS.every((l) => !dash.test(sectionText(PRIVACY[l], 'operations') + sectionText(PRIVACY[l], 'retention'))));
  return out;
}
