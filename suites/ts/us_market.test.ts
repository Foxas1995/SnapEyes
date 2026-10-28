// The US market, its legal edition and the two other markets of 2026-10-28 (the owner's decisions: us in US dollars with the US
// edition, English only, and the consent to the use of the eye photos in its checkbox; uk in pounds behind the switch, selectable 0;
// hr in euros, its own key, the EU edition, Croatian as its page language), as the page code reads them: the prices, the money
// format, the edition and its languages, the checkout wording, the four legal pages and the pack the confirmation email quotes.
// Pure page code, loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results.
import { MARKETS, SELECTABLE, currencyOf, isSelectable, money, priceList, priceMinor, withMarket } from '../../src/shared/markets';
import {
  CHECKOUT_LEGAL, CHECKOUT_LEGAL_US, EDITION_LANGS, EDITION_MARKETS, checkoutLegal, editionLang, legalEdition, legalHref, ownConsent,
} from '../../src/shared/legal';
import { langFor, marketDefaultLang, marketLangs } from '../../src/shared/lang';
import { EDITIONS } from '../../src/legal/editions';
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
  check('money: in the other languages a decimal comma and the sign after a no-break space (21,97 $, 17,97 £)',
    money(2197, 'usd', 'de') === '21,97 $' && money(1797, 'gbp', 'lt') === '17,97 £' && money(123450, 'usd', 'de') === '1.234,50 $',
    [money(2197, 'usd', 'de'), money(1797, 'gbp', 'lt')].join(' '));
  check('money: the old currencies write as before (euros, A$, forints)', money(1997, 'eur', 'en') === '€19.97' && money(3900, 'aud', 'en') === 'A$39'
    && money(699000, 'huf', 'en') === '6 990 Ft');

  // the edition and its languages
  check('legalEdition: us reads the US edition; eu, lt, hr and uk the EU one; au and hu their own', legalEdition('us') === 'us'
    && legalEdition('eu') === 'eu' && legalEdition('lt') === 'eu' && legalEdition('hr') === 'eu' && legalEdition('uk') === 'eu'
    && legalEdition('au') === 'au' && legalEdition('hu') === 'hu' && EDITION_MARKETS.us === 'us');
  check('the US edition is English only: every language reads English on a US page, and the US market has no default language of its own',
    JSON.stringify(EDITION_LANGS.us) === '["en"]' && JSON.stringify(marketLangs('us')) === '["en"]' && (['en', 'de', 'lt', 'hu', 'hr'] as const).every((l) => langFor(l, 'us') === 'en' && editionLang(l, 'us') === 'en')
      && marketDefaultLang('us') === null);
  check('the Croatian market opens in Croatian and can be read in every language of the EU edition', marketDefaultLang('hr') === 'hr'
    && JSON.stringify(marketLangs('hr')) === JSON.stringify(EDITION_LANGS.eu) && langFor('de', 'hr') === 'de');

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
    && (['de', 'lt', 'hu', 'hr'] as const).every((l) => !ed.terms[l] && !ed.privacy[l] && !ed.withdrawal[l] && !ed.imprint[l]));
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
    && sectionText(terms, 'withdrawal').includes('[Your rights in the United States](#united-states)') && sectionText(terms, 'withdrawal') === sectionText(EDITIONS.au.terms.en!, 'withdrawal').replace('[Your rights in Australia](#australia)', '[Your rights in the United States](#united-states)'));
  const pus = sectionText(privacy, 'united-states');
  const pids = privacy.sections.map((s) => s.id);
  check('the US privacy policy: its own section after the rights section, with the state laws, the retention schedule and no sale for advertising',
    pids[pids.indexOf('rights') + 1] === 'united-states' && pus.includes('Illinois, Texas and Washington') && pus.includes('within 30 days at the latest')
      && pus.includes('12 months after your payment') && pus.includes('14 days after the withdrawal') && pus.includes('targeted advertising') && pus.includes('within one month'), pids.join(','));
  check('the US privacy policy keeps every other section of the euro text word for word', pids.filter((x) => x !== 'united-states').every((x) => sectionText(privacy, x) === sectionText(EDITIONS.eu.privacy.en!, x)));
  check('the US withdrawal page shows the US checkbox in its box and links the US rights', JSON.stringify(wd).includes(JSON.stringify(CHECKOUT_LEGAL_US.en.withdrawalConsent).slice(1, -1))
    && (wd.lead ?? '').includes('doc:terms#united-states') && sectionText(wd, 'expiry').includes('doc:terms#united-states'));
  check('the US legal notice says no sales tax is charged', sectionText(imprint, 'provider').includes('Sales tax (United States): Not registered to collect sales tax in any US state'));
  check('no paragraph of the US edition holds an en or em dash', !DASH.test(JSON.stringify(ed)));

  // the pack of the confirmation email and the links of the US texts
  const pack = legalMailPack();
  const pu = pack.editions.us;
  check('the legal pack carries the US edition apart, English only, with links that carry m=us', !!pu?.en && !pu.de && !pu.lt && !pu.hu && !pu.hr
    && pu.en.terms.url === 'https://snapeyes.com/terms?lang=en&m=us' && pu.en.withdrawal.url === 'https://snapeyes.com/withdrawal?lang=en&m=us'
    && pu.en.terms.text.includes('https://snapeyes.com/terms?lang=en&m=us#united-states') && pu.en.terms.text.includes('$21.97'), JSON.stringify(pu?.en?.terms.url));
  check('a legal link of the US market always carries m=us', legalHref('terms', 'en', 'united-states', 'us') === '/terms?lang=en&m=us#united-states'
    && legalHref('privacy', 'de', '', 'us') === '/privacy?lang=de&m=us');
  check('the EU, Australian and Hungarian packs print no US price', !pack.docs.en.terms.text.includes('$21.97') && !pack.editions.au.en!.terms.text.includes('$21.97')
    && !pack.editions.hu.en!.terms.text.includes('$21.97'));
  return out;
}
