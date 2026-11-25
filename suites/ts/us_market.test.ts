// The US market, its legal edition and the two other markets of 2026-10-28 (the owner's decisions: us in US dollars with the US
// edition, English only, and the consent to the use of the eye photos in its checkbox; uk in pounds behind the switch, selectable 0;
// hr in euros, its own key, the EU edition, Croatian as its page language), as the page code reads them: the prices, the money
// format, the edition and its languages, the checkout wording, the four legal pages and the pack the confirmation email quotes.
// Pure page code, loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results.
import { MARKETS, SELECTABLE, currencyOf, isSelectable, money, priceList, priceMinor, withMarket } from '../../src/shared/markets';
import {
  CHECKOUT_LEGAL, CHECKOUT_LEGAL_US, EDITION_LANGS, EDITION_MARKETS, checkoutLegal, editionLang, legalEdition, legalHref, ownConsent,
} from '../../src/shared/legal';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { LANGS, LANG_NAMES, langFor, marketDefaultLang, marketLangs } from '../../src/shared/lang';
import { LangMenu, wantsLangMenu } from '../../src/shared/LangMenu';
import { EDITIONS } from '../../src/legal/editions';
import { PRIVACY } from '../../src/legal/docs/privacy';
import { legalMailPack } from '../../src/legal/plain';
import type { Block, LegalDoc } from '../../src/legal/types';

type Row = [string, boolean, string?];
const blockText = (b: Block): string => (typeof b === 'string' ? b : 'ul' in b ? b.ul.join('\n') : 'dl' in b ? b.dl.map((r) => r.join(': ')).join('\n') : b.box.join('\n'));
const section = (d: LegalDoc, id: string) => d.sections.find((s) => s.id === id);
const sectionText = (d: LegalDoc, id: string) => (section(d, id)?.blocks ?? []).map(blockText).join('\n');
const DASH = new RegExp('[' + [0x2012, 0x2013, 0x2014, 0x2015].map((c) => String.fromCharCode(c)).join('') + ']');

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);

  // the three new markets (api/_lib/markets.py, read by src/shared/markets.ts)
  const p = (m: string) => Object.values(priceList(m)).join(',');
  check('us: US dollars, 2197 / 2797 / 4497 / +1600, selectable, English, no Stripe locale of its own, the United States',
    currencyOf('us') === 'usd' && p('us') === '2197,2797,4497,1600' && MARKETS.us.selectable === 1 && MARKETS.us.lang === 'en'
      && JSON.stringify(MARKETS.us.stripe_locale) === '{}' && JSON.stringify(MARKETS.us.countries) === '["US"]', JSON.stringify(MARKETS.us));
  check('uk: pounds, 1797 / 2197 / 3497 / +1300, behind the switch (selectable 0), en-GB on Stripe, Great Britain',
    currencyOf('uk') === 'gbp' && p('uk') === '1797,2197,3497,1300' && MARKETS.uk.selectable === 0 && MARKETS.uk.lang === 'en'
      && MARKETS.uk.stripe_locale.en === 'en-GB' && JSON.stringify(MARKETS.uk.countries) === '["GB"]', JSON.stringify(MARKETS.uk));
  check('hr: euros, the same prices as eu, selectable, Croatian, Croatia', currencyOf('hr') === 'eur' && p('hr') === p('eu')
    && MARKETS.hr.selectable === 1 && MARKETS.hr.lang === 'hr' && JSON.stringify(MARKETS.hr.countries) === '["HR"]', JSON.stringify(MARKETS.hr));
  check('the site sells in us and hr, not in uk; a link that names uk is ignored (no m=uk in the links)',
    SELECTABLE.includes('us') && SELECTABLE.includes('hr') && !SELECTABLE.includes('uk') && isSelectable('us') && !isSelectable('uk')
      && withMarket('/try', 'uk') === '/try' && withMarket('/try', 'us') === '/try?m=us' && withMarket('/try#a', 'hr') === '/try?m=hr#a');
  check('priceMinor on the US market: one eye by its price class, two eyes $44.97, eight eyes $140.97',
    priceMinor(1, 'solo.clean', 'us') === 2197 && priceMinor(2, 'solo.clean', 'us') === 4497 && priceMinor(8, 'solo.clean', 'us') === 4497 + 6 * 1600);

  // money: "$21.97" in English, always with the cents; pounds the same; never an en or em dash
  check('money: US dollars and pounds in English with the cents ($21.97, +$16.00, £17.97, £13.00, $1,234.50)',
    money(2197, 'usd', 'en') === '$21.97' && money(1600, 'usd', 'en') === '$16.00' && money(1797, 'gbp', 'en') === '£17.97'
      && money(1300, 'gbp', 'en') === '£13.00' && money(123450, 'usd', 'en') === '$1,234.50' && money(2197, 'USD', 'en') === '$21.97',
    [money(2197, 'usd', 'en'), money(1600, 'usd', 'en'), money(1797, 'gbp', 'en'), money(123450, 'usd', 'en')].join(' '));
  check('money: in the other languages a decimal comma and the sign after a no-break space (21,97 $, 17,97 £), Finnish, Estonian and Latvian among them (2026-11-13)',
    money(2197, 'usd', 'de') === '21,97 $' && money(1797, 'gbp', 'lt') === '17,97 £' && money(123450, 'usd', 'de') === '1.234,50 $'
      && (['fi', 'et', 'lv'] as const).every((l) => money(2197, 'usd', l) === '21,97 $' && money(1797, 'gbp', l) === '17,97 £' && money(2497, 'eur', l) === '24,97 €'),
    [money(2197, 'usd', 'de'), money(1797, 'gbp', 'lt')].join(' '));
  check('money: the old currencies write as before (euros, A$, forints)', money(1997, 'eur', 'en') === '€19.97' && money(3900, 'aud', 'en') === 'A$39'
    && money(699000, 'huf', 'en') === '6 990 Ft');

  // the edition and its languages
  check('legalEdition: us reads the US edition; eu, lt, hr and uk the EU one; au and hu their own', legalEdition('us') === 'us'
    && legalEdition('eu') === 'eu' && legalEdition('lt') === 'eu' && legalEdition('hr') === 'eu' && legalEdition('uk') === 'eu'
    && legalEdition('au') === 'au' && legalEdition('hu') === 'hu' && EDITION_MARKETS.us === 'us');
  check('the US edition is English only: every language reads English on a US page, and the US market has no default language of its own',
    JSON.stringify(EDITION_LANGS.us) === '["en"]' && JSON.stringify(marketLangs('us')) === '["en"]' && (['en', 'de', 'lt', 'hu', 'hr', 'fi', 'et', 'lv'] as const).every((l) => langFor(l, 'us') === 'en' && editionLang(l, 'us') === 'en')
      && marketDefaultLang('us') === null);
  check('the Croatian market opens in Croatian and can be read in every language of the EU edition', marketDefaultLang('hr') === 'hr'
    && JSON.stringify(marketLangs('hr')) === JSON.stringify(EDITION_LANGS.eu) && langFor('de', 'hr') === 'de');
  // 2026-11-13: Finnish, Estonian and Latvian are texts of the EU edition only (src/shared/legal.ts EDITION_LANGS), so the euro markets read eight languages and the
  // Hungarian (forint), the Australian and the US market the ones they had: a page of those three never shows one of the new languages
  check('the EU edition reads eight languages since 2026-11-13 (Finnish, Estonian and Latvian came); the Hungarian edition keeps its four, the Australian its two, the US its one, and a page of those markets asked for a new language shows its own (hu) or English (au, us)',
    JSON.stringify(EDITION_LANGS.eu) === '["en","de","lt","hu","hr","fi","et","lv"]' && JSON.stringify(EDITION_LANGS.hu) === '["en","de","lt","hu"]' && JSON.stringify(EDITION_LANGS.au) === '["en","de"]'
      && (['eu', 'lt', 'hr'] as const).every((m) => (['fi', 'et', 'lv'] as const).every((l) => langFor(l, m) === l && editionLang(l, m) === l && marketLangs(m).length === 8))
      && (['fi', 'et', 'lv'] as const).every((l) => langFor(l, 'hu') === 'hu' && editionLang(l, 'hu') === 'en' && langFor(l, 'au') === 'en' && editionLang(l, 'au') === 'en' && langFor(l, 'us') === 'en')
      && (['fi', 'et', 'lv'] as const).every((l) => !EDITIONS.hu.terms[l] && !EDITIONS.hu.privacy[l] && !EDITIONS.hu.withdrawal[l] && !EDITIONS.hu.imprint[l] && !EDITIONS.au.terms[l] && !EDITIONS.au.privacy[l]
        && !!EDITIONS.eu.terms[l] && !!EDITIONS.eu.privacy[l] && !!EDITIONS.eu.withdrawal[l] && !!EDITIONS.eu.imprint[l]),
    JSON.stringify(EDITION_LANGS));
  // 2026-11-13: with eight languages the switch of /try, /order, /gift and the legal pages is a menu on the euro markets (src/shared/LangMenu.tsx); a market that reads five
  // languages or fewer keeps its row of buttons
  check('the language switch is a menu where a market reads more than five languages (eu, lt, hr: eight) and the row of buttons elsewhere (hu: four, au: two, us: one)',
    (['eu', 'lt', 'hr'] as const).every((m) => wantsLangMenu(marketLangs(m))) && (['hu', 'au', 'us'] as const).every((m) => !wantsLangMenu(marketLangs(m)))
      && wantsLangMenu(['en', 'de', 'lt', 'hu', 'hr', 'fi']) && !wantsLangMenu(['en', 'de', 'lt', 'hu', 'hr']));
  const menu = (lang: (typeof LANGS)[number]) => renderToStaticMarkup(createElement(LangMenu, { label: 'Language', lang, langs: marketLangs('eu'), onSwitch: () => undefined }));
  const offered = (h: string) => [...h.matchAll(/<button[^>]*\slang="([a-z]{2})"[^>]*aria-pressed="(true|false)"[^>]*>([^<]*)<\/button>/g)].map((m) => ({ lang: m[1], pressed: m[2] === 'true', name: m[3] }));
  check('the menu of a euro page: a closed <details data-testid="lang-menu"> whose summary shows the page\'s language code, and one button per language of the EU edition, in the site\'s order, named in its own language, only the page\'s own pressed',
    (['fi', 'et', 'lv', 'en'] as const).every((l) => {
      const h = menu(l), b = offered(h);
      return /<details data-testid="lang-menu"/.test(h) && !/<details[^>]*\sopen/.test(h) && new RegExp(`<summary[^>]*aria-label="Language: ${LANG_NAMES[l]}"[^>]*><span aria-hidden="true"[^>]*>${l.toUpperCase()}<svg `).test(h)
        && b.map((x) => x.lang).join() === EDITION_LANGS.eu.join() && b.length === 8 && b.every((x) => x.name === LANG_NAMES[x.lang as keyof typeof LANG_NAMES] && x.pressed === (x.lang === l));
    }) && LANG_NAMES.fi === 'Suomi' && LANG_NAMES.et === 'Eesti' && LANG_NAMES.lv === 'Latviešu', menu('fi').replace(/ class="[^"]*"/g, '').slice(0, 400));

  // the checkout wording
  const us = checkoutLegal('de', 'us');
  check('the US checkout: its own checkbox (both EU elements, no cancelling for a change of mind, faulty file rights kept, the eye photos), in English whatever the page asked',
    us.withdrawalConsent === CHECKOUT_LEGAL_US.en.withdrawalConsent && /^I expressly agree that SnapEyes starts making my personalised digital artwork right away, before the withdrawal period ends\./.test(us.withdrawalConsent)
      && us.withdrawalConsent.includes('I lose my right of withdrawal') && us.withdrawalConsent.includes("can't cancel for a change of mind")
      && us.withdrawalConsent.includes('my rights if the file is faulty are not affected') && us.withdrawalConsent.includes('photos of my eyes only to make my preview and my artwork, never to identify anyone')
      && us.continueButton === CHECKOUT_LEGAL.en.continueButton && us.withdrawalConsentMissing === CHECKOUT_LEGAL.en.withdrawalConsentMissing, us.withdrawalConsent);
  check('the line under it names the terms\' "Your rights in the United States"', us.acceptance.some((x) => x.doc === 'terms' && x.section === 'united-states'));
  check('own checkbox texts (GET /api/checkout consent.markets): au and us; eu and hu read the EU text', ownConsent('au') && ownConsent('us') && !ownConsent('eu') && !ownConsent('hu')
    && checkoutLegal('en', 'hr').withdrawalConsent === CHECKOUT_LEGAL.en.withdrawalConsent);
  check('no word of the US checkbox reads as "no refunds", and no dash', !/no refund/i.test(us.withdrawalConsent) && !DASH.test(us.withdrawalConsent));

  // the four legal pages of the US edition
  const ed = EDITIONS.us;
  const terms = ed.terms.en!, privacy = ed.privacy.en!, wd = ed.withdrawal.en!, imprint = ed.imprint.en!;
  check('the US edition has the four pages in English and in no other language', !!terms && !!privacy && !!wd && !!imprint
    && (['de', 'lt', 'hu', 'hr', 'fi', 'et', 'lv'] as const).every((l) => !ed.terms[l] && !ed.privacy[l] && !ed.withdrawal[l] && !ed.imprint[l]));
  const prices = sectionText(terms, 'prices');
  check('the US terms print the four US prices and no euro or A$ price, and say no sales tax is charged',
    ['One eye, Clean Iris: $21.97', 'One eye, any other style: $27.97', 'Two eyes, any style: $44.97', 'Each further eye: +$16.00'].every((x) => prices.includes(x))
      && !/€|A\$|Ft\b/.test(prices) && prices.includes('are not registered to collect sales tax in any US state, so no sales tax is charged'), prices.slice(0, 300));
  const ids = terms.sections.map((s) => s.id);
  check('the US terms have "Your rights in the United States" right after the complaints, and the contract language is English',
    ids[ids.indexOf('defects') + 1] === 'united-states' && sectionText(terms, 'contract').includes('The contract language is English.')
      && !sectionText(terms, 'contract').includes('German'), ids.join(','));
  const rights = sectionText(terms, 'united-states');
  check('the US rights: a faulty file made again free of charge or refunded in full, the change of mind, the eye photos, the law of the state kept',
    rights.includes('We make the file again free of charge, or refund you in full if that does not fix the problem.') && rights.includes('within 48 hours of your payment')
      && rights.includes('never create, keep or compare an iris template') && rights.includes('doc:privacy#united-states') && rights.includes('law of your state that cannot be excluded or limited by contract'));
  check('the US disputes name the state consumer protection office and the FTC, and keep the EU route', sectionText(terms, 'disputes').includes('reportfraud.ftc.gov')
    && sectionText(terms, 'disputes').includes('vvtat.lt') && sectionText(terms, 'disputes').includes('the consumer protection law of your state'));
  check('the US withdrawal: cancelling for a change of mind only, framed as EU law, with a link to the US rights', section(terms, 'withdrawal')?.title === 'Cancelling for a change of mind (right of withdrawal)'
    && sectionText(terms, 'withdrawal').includes('[Your rights in the United States](#united-states)')
    // 2026-11-25 (the owner's decision): the US checkout keeps its consent box, so its section still says the right ends once making starts; the Australian one has no box and says the 14 days stay
    && sectionText(terms, 'withdrawal').includes('we ask you to agree that we start making your file straight away') && sectionText(EDITIONS.au.terms.en!, 'withdrawal').includes('this does not end your right to cancel'));
  const pus = sectionText(privacy, 'united-states');
  const pids = privacy.sections.map((s) => s.id);
  check('the US privacy policy: its own section after the rights section, with the state laws, the retention schedule and no sale for advertising',
    pids[pids.indexOf('rights') + 1] === 'united-states' && pus.includes('Illinois, Texas and Washington') && pus.includes('within 30 days at the latest')
      && pus.includes('12 months after your payment') && pus.includes('14 days after the withdrawal') && pus.includes('targeted advertising') && pus.includes('within one month'), pids.join(','));
  // 2026-10-28: the US edition is made from the euro text before the prints (src/legal/docs/prints.ts patches the euro edition only: the US market sells no print)
  check('the US privacy policy keeps every other section of the euro text word for word', pids.filter((x) => x !== 'united-states').every((x) => sectionText(privacy, x) === sectionText(PRIVACY.en, x))
    && !pids.includes('prints'));
  check('the US withdrawal page shows the US checkbox in its box and links the US rights', JSON.stringify(wd).includes(JSON.stringify(CHECKOUT_LEGAL_US.en.withdrawalConsent).slice(1, -1))
    && (wd.lead ?? '').includes('doc:terms#united-states') && sectionText(wd, 'expiry').includes('doc:terms#united-states'));
  check('the US legal notice says no sales tax is charged', sectionText(imprint, 'provider').includes('Sales tax (United States): Not registered to collect sales tax in any US state'));
  check('no paragraph of the US edition holds an en or em dash', !DASH.test(JSON.stringify(ed)));

  // the pack of the confirmation email and the links of the US texts
  const pack = legalMailPack();
  const pu = pack.editions.us;
  check('the legal pack carries the US edition apart, English only, with links that carry m=us', !!pu?.en && !pu.de && !pu.lt && !pu.hu && !pu.hr && !pu.fi && !pu.et && !pu.lv
    && pu.en.terms.url === 'https://snapeyes.com/terms?lang=en&m=us' && pu.en.withdrawal.url === 'https://snapeyes.com/withdrawal?lang=en&m=us'
    && pu.en.terms.text.includes('https://snapeyes.com/terms?lang=en&m=us#united-states') && pu.en.terms.text.includes('$21.97'), JSON.stringify(pu?.en?.terms.url));
  check('a legal link of the US market always carries m=us', legalHref('terms', 'en', 'united-states', 'us') === '/terms?lang=en&m=us#united-states'
    && legalHref('privacy', 'de', '', 'us') === '/privacy?lang=de&m=us');
  check('the EU, Australian and Hungarian packs print no US price', !pack.docs.en.terms.text.includes('$21.97') && !pack.editions.au.en!.terms.text.includes('$21.97')
    && !pack.editions.hu.en!.terms.text.includes('$21.97'));
  return out;
}
