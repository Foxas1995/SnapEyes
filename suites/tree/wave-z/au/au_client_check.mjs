// The site's Australian edition as the build makes it (loaded through Vite's module runner, like the build's legal
// pack), for test_au.py: every legal page of both editions, the checkout wording, the landing copy per market, the
// order page's ACL line, and the facts test_au.py compares with the server and with the EU snapshot taken before the
// AU work (eu_before.json). Prints JSON. Run with the repo as the working directory: node <this file>
import { createRequire } from 'node:module';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { readFileSync } from 'node:fs';

const req = createRequire(join(process.cwd(), 'package.json'));
const { runnerImport } = await import(pathToFileURL(req.resolve('vite')).href);
const opt = { configFile: false, logLevel: 'silent' };

const { module: ED } = await runnerImport('./src/legal/editions.ts', opt);
const { module: L } = await runnerImport('./src/shared/legal.ts', opt);
const { module: M } = await runnerImport('./src/shared/markets.ts', opt);
const { module: C } = await runnerImport('./src/landing/copy/index.ts', opt);
const DE = JSON.parse(readFileSync('./src/landing/copy/de.json', 'utf8'));
const { module: P } = await runnerImport('./src/legal/plain.ts', opt);
const { module: O } = await runnerImport('./src/order/copy.ts', opt);

const out = {
  editions: ED.EDITIONS,
  legalUpdated: L.LEGAL_UPDATED,
  consentVersion: L.WITHDRAWAL_CONSENT_VERSION,
  editionMarkets: L.EDITION_MARKETS,
  edition: Object.fromEntries(['eu', 'lt', 'au', 'hu', 'zz'].map((m) => [m, L.legalEdition(m)])),
  checkoutEu: L.CHECKOUT_LEGAL,
  checkoutAu: L.CHECKOUT_LEGAL_AU,
  checkoutFor: {
    en_au: L.checkoutLegal('en', 'au'), de_au: L.checkoutLegal('de', 'au'),
    en_eu: L.checkoutLegal('en', 'eu'), en_lt: L.checkoutLegal('en', 'lt'),
  },
  hrefs: {
    auSection: L.legalHref('terms', 'en', 'australia', 'au'),
    euSection: L.legalHref('terms', 'en', 'australia', 'eu'),
    plain: L.legalHref('privacy', 'de'),
  },
  auPrices: M.priceList('au'),
  money: { a39: M.money(M.priceList('au').one_eye_studio_black, 'aud', 'en') },
  copy: { eu: C.copyForMarket(C.COPY_EN, 'eu'), lt: C.copyForMarket(DE, 'lt'), auEn: C.copyForMarket(C.COPY_EN, 'au'), auDe: C.copyForMarket(DE, 'au') },
  copySame: { euEn: C.copyForMarket(C.COPY_EN, 'eu') === C.COPY_EN, euDe: C.copyForMarket(DE, 'eu') === DE, ltEn: C.copyForMarket(C.COPY_EN, 'lt') === C.COPY_EN },
  plainAuTerms: P.legalPlainText('terms', ED.EDITIONS.au.terms.en, 'en', 'au'),
  pack: P.legalMailPack(),
  orderAcl: null,
};
// the order page copy's export name differs between versions: find the object with withdraw.acl
for (const [k, v] of Object.entries(O)) {
  if (v && typeof v === 'object' && v.en && v.en.withdraw && v.de && v.de.withdraw) out.orderAcl = { name: k, en: v.en.withdraw.acl, de: v.de.withdraw.acl };
}
console.log(JSON.stringify(out));
