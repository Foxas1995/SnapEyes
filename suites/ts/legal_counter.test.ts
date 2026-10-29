// The privacy policy says what the anonymous counter keeps (2026-10-20): the same paragraphs, in the same places, in English, German, Lithuanian, Hungarian and Croatian (2026-10-28),
// in the four editions (the euro texts, the Australian and the US edition made from them by patchDoc, and the Hungarian edition, which is the euro text with the forint prices and has no
// Croatian text), and nothing the policy says contradicts
// the counter (api/_lib/counter.py): no cookie, no visitor number, no IP address, no user agent stored; the country is stored as two letters. Pure page code, loaded through Vite's
// module runner by scripts/run_ts_tests.mjs; returns its results.
import { EDITIONS } from '../../src/legal/editions';
import { PRIVACY } from '../../src/legal/docs/privacy';
import { withPrintsPrivacy } from '../../src/legal/docs/prints';
import { LEGAL_UPDATED } from '../../src/shared/legal';
import type { Block, LegalDoc } from '../../src/legal/types';

type Row = [string, boolean, string?];
const LANGS = ['en', 'de', 'lt', 'hu', 'hr'] as const;
const blockText = (b: Block): string => (typeof b === 'string' ? b : 'ul' in b ? b.ul.join('\n') : 'dl' in b ? b.dl.map((r) => r.join(': ')).join('\n') : b.box.join('\n'));
const section = (d: LegalDoc, id: string) => d.sections.find((s) => s.id === id);
const sectionText = (d: LegalDoc, id: string) => (section(d, id)?.blocks ?? []).map(blockText).join('\n');

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);

  const ids = (d: LegalDoc) => d.sections.map((s) => s.id).join();
  check('the five languages of the privacy policy have the same sections in the same order', LANGS.every((l) => ids(PRIVACY[l]) === ids(PRIVACY.en)), LANGS.map((l) => ids(PRIVACY[l])).join(' | '));
  const nOps = LANGS.map((l) => section(PRIVACY[l], 'operations')?.blocks.length ?? -1);
  check('the "operations" section (service statistics) has the same number of paragraphs in every language: the counter, the campaign code and the feedback box are three more than before (eight)', nOps.every((n) => n === 8), nOps.join());

  const KEY: Record<(typeof LANGS)[number], RegExp> = {
    en: /counts the steps a page reaches/, de: /zählt unser Server außerdem die Schritte, die eine Seite erreicht/, lt: /serveris taip pat skaičiuoja žingsnius, kuriuos pasiekia puslapis/, hu: /a szerverünk azt is megszámolja, mely lépéseket éri el egy oldal/,
    hr: /naš poslužitelj broji i korake do kojih stranica stigne/,
  };
  check('the counter paragraph is in the operations section of every language', LANGS.every((l) => KEY[l].test(sectionText(PRIVACY[l], 'operations'))), LANGS.filter((l) => !KEY[l].test(sectionText(PRIVACY[l], 'operations'))).join());

  const NO_COOKIE: Record<(typeof LANGS)[number], RegExp> = { en: /use no cookie and no visitor number/, de: /keinen Cookie und keine Besuchernummer/, lt: /nenaudojamas slapukas ar lankytojo numeris/, hu: /nem használnak sütit és látogatószámot/, hr: /ne koriste kolačić ni broj posjetitelja/ };
  check('and says that the counts use no cookie and no visitor number', LANGS.every((l) => NO_COOKIE[l].test(sectionText(PRIVACY[l], 'operations'))), LANGS.filter((l) => !NO_COOKIE[l].test(sectionText(PRIVACY[l], 'operations'))).join());
  const IP: Record<(typeof LANGS)[number], RegExp> = { en: /hold no IP address, no browser identification/, de: /keine IP-Adresse, keine Browserkennung/, lt: /nėra IP adreso, naršyklės identifikatoriaus/, hu: /nem tartalmaznak IP-címet, böngészőazonosítót/, hr: /ne sadrže IP adresu, identifikator preglednika/ };
  check('and that they hold no IP address and no browser identification', LANGS.every((l) => IP[l].test(sectionText(PRIVACY[l], 'operations'))), LANGS.filter((l) => !IP[l].test(sectionText(PRIVACY[l], 'operations'))).join());
  const COUNTRY: Record<(typeof LANGS)[number], RegExp> = { en: /two letters, which Vercel derives from your IP address/, de: /zwei Buchstaben, die Vercel aus Ihrer IP-Adresse ableitet/, lt: /dvi raidės, kurias Vercel nustato pagal Jūsų IP adresą/, hu: /két betű, amelyet a Vercel az IP-címéből származtat/, hr: /dva slova koja Vercel izvodi iz vaše IP adrese/ };
  check('and that the country is kept as two letters', LANGS.every((l) => COUNTRY[l].test(sectionText(PRIVACY[l], 'operations'))), LANGS.filter((l) => !COUNTRY[l].test(sectionText(PRIVACY[l], 'operations'))).join());

  const NOT_STORED: Record<(typeof LANGS)[number], RegExp> = { en: /and is not stored\./, de: /und wird nicht gespeichert\./, lt: /nėra saugoma\./, hu: /és nem tároljuk\./, hr: /i ne pohranjuje se\./ };
  check('the website paragraph about the country no longer says it is not stored at all: it names the two letters in the anonymous counts, in every language',
    LANGS.every((l) => !NOT_STORED[l].test(sectionText(PRIVACY[l], 'website')) && /#operations/.test(sectionText(PRIVACY[l], 'website'))), LANGS.map((l) => NOT_STORED[l].test(sectionText(PRIVACY[l], 'website'))).join());

  const doc = (e: keyof typeof EDITIONS, l: (typeof LANGS)[number]) => EDITIONS[e].privacy[l];
  // 2026-10-28: the euro edition's policy is the raw text with the print paragraphs (src/legal/docs/prints.ts withPrintsPrivacy), and the Hungarian edition reads that very one
  check('the Hungarian edition reads the same privacy texts as the euro one (the forint prices are in the terms, not here), in all four of its languages, and has no Croatian text (Croatian is in the euro edition only)',
    LANGS.every((l) => JSON.stringify(doc('eu', l)) === JSON.stringify(withPrintsPrivacy(PRIVACY[l], l)) && (l === 'hr' ? doc('hu', l) === undefined : doc('hu', l) === doc('eu', l))));
  const au = EDITIONS.au.privacy;
  check('the Australian edition has English and German only, made from the euro texts: its operations section is the same paragraphs',
    !!au.en && !!au.de && !au.lt && !au.hu && !au.hr && (['en', 'de'] as const).every((l) => sectionText(au[l]!, 'operations') === sectionText(PRIVACY[l], 'operations') && sectionText(au[l]!, 'website') === sectionText(PRIVACY[l], 'website')));
  check('the Australian edition keeps its own section on top of them, after the rights section', (['en', 'de'] as const).every((l) => section(au[l]!, 'australia') !== undefined));
  // 2026-10-28: the US edition (English only), made the same way
  const us = EDITIONS.us.privacy;
  check('the US edition has English only, made from the euro texts: its operations and website sections are the same paragraphs',
    !!us.en && !us.de && !us.lt && !us.hu && !us.hr && sectionText(us.en!, 'operations') === sectionText(PRIVACY.en, 'operations') && sectionText(us.en!, 'website') === sectionText(PRIVACY.en, 'website'));
  check('the US edition keeps its own section on top of them, right after the rights section',
    !!us.en && us.en.sections[us.en.sections.findIndex((s) => s.id === 'rights') + 1]?.id === 'united-states');

  // the campaign code (item 2): the key in the storage section, the operations paragraph, the order section and the retention row, in every language
  const KEYS: Record<(typeof LANGS)[number], RegExp> = { en: /key "snapeyes\.c"/, de: /Schlüssel „snapeyes\.c“/, lt: /raktu „snapeyes\.c“/, hu: /„snapeyes\.c” kulcs alatt/, hr: /ključem „snapeyes\.c“/ };
  check('the storage section names the session storage key snapeyes.c and what it holds, in every language', LANGS.every((l) => KEYS[l].test(sectionText(PRIVACY[l], 'storage'))), LANGS.filter((l) => !KEYS[l].test(sectionText(PRIVACY[l], 'storage'))).join());
  const FB: Record<(typeof LANGS)[number], RegExp> = { en: /"fbclid" or similar number in the address is never read/, de: /„fbclid“ oder ähnliche Nummer in der Adresse wird nie gelesen/, lt: /„fbclid“ ar panašus numeris adrese niekada neskaitomas/, hu: /„fbclid” vagy hasonló számot soha nem olvassuk/, hr: /„fbclid“ ili sličan broj u adresi nikada se ne čita/ };
  check('and says that a click number (fbclid) is never read', LANGS.every((l) => FB[l].test(sectionText(PRIVACY[l], 'storage'))), LANGS.filter((l) => !FB[l].test(sectionText(PRIVACY[l], 'storage'))).join());
  const CAMP: Record<(typeof LANGS)[number], RegExp> = { en: /which advertisement led to which step/, de: /welche Anzeige zu welchem Schritt geführt hat/, lt: /kuri reklama atvedė iki kurio žingsnio/, hu: /melyik hirdetés melyik lépéshez vezetett/, hr: /koji je oglas doveo do kojeg koraka/ };
  check('the operations section says what the code is for', LANGS.every((l) => CAMP[l].test(sectionText(PRIVACY[l], 'operations'))), LANGS.filter((l) => !CAMP[l].test(sectionText(PRIVACY[l], 'operations'))).join());
  const ORD: Record<(typeof LANGS)[number], RegExp> = { en: /its campaign code/, de: /deren Kampagnencode/, lt: /jos kampanijos kodą/, hu: /annak kampánykódját/, hr: /njegov kod kampanje/ };
  check('the order section says the Stripe payment receives the code, in every language', LANGS.every((l) => ORD[l].test(sectionText(PRIVACY[l], 'orders'))), LANGS.filter((l) => !ORD[l].test(sectionText(PRIVACY[l], 'orders'))).join());
  const REC: Record<(typeof LANGS)[number], RegExp> = { en: /campaign code of the advertisement you came from \(if any\)/, de: /Kampagnencode der Anzeige, über die Sie kamen \(falls vorhanden\)/, lt: /kampanijos kodą \(jei yra\)/, hu: /kampánykódja, amelyen keresztül érkezett \(ha van\)/, hr: /kod kampanje oglasa putem kojeg ste došli \(ako postoji\)/ };
  check('and the retention row of the order records lists it', LANGS.every((l) => REC[l].test(sectionText(PRIVACY[l], 'retention'))), LANGS.filter((l) => !REC[l].test(sectionText(PRIVACY[l], 'retention'))).join());
  check('the Australian edition carries the same storage and order paragraphs', (['en', 'de'] as const).every((l) => sectionText(au[l]!, 'storage') === sectionText(PRIVACY[l], 'storage') && sectionText(au[l]!, 'orders') === sectionText(PRIVACY[l], 'orders')));
  check('the US edition carries the same storage and order paragraphs', !!us.en && sectionText(us.en, 'storage') === sectionText(PRIVACY.en, 'storage') && sectionText(us.en, 'orders') === sectionText(PRIVACY.en, 'orders'));

  const dash = new RegExp('[' + [0x2012, 0x2013, 0x2014, 0x2015].map((c) => String.fromCharCode(c)).join('') + ']');
  check('no paragraph of the policy holds an en or em dash', LANGS.every((l) => !dash.test(PRIVACY[l].sections.map((s) => sectionText(PRIVACY[l], s.id)).join('\n'))));
  // 2026-10-28: the date moved on with the Croatian texts of the EU edition (src/shared/legal.ts LEGAL_UPDATED); the counter paragraphs above are those of 2026-10-20
  check('one date versions the legal pages and it is the day of the last change (2026-10-28, the Croatian texts; the counter paragraphs came on 2026-10-20)', LEGAL_UPDATED === '2026-10-28', LEGAL_UPDATED);
  check('the retention row of the service statistics still says twelve months in every language', LANGS.every((l) => /12/.test(sectionText(PRIVACY[l], 'retention').split('\n').filter((x) => /operations/.test(x)).join('\n'))));
  return out;
}
