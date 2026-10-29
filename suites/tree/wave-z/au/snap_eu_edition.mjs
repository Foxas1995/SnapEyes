// Snapshot of the EU edition of the legal pages AS THE SITE SHOWS THEM (src/legal/editions.ts EDITIONS.eu: terms, withdrawal, privacy, imprint; every
// language), the checkout legal wording and the built pack, in the layout of snap_eu.mjs. Since the prints (2026-10-28, src/legal/docs/prints.ts) the EU
// edition is the raw docs with the print sections applied, so its pin is taken from the editions, not from the raw docs. Run with the repo as cwd:
//   node suites/tree/wave-z/au/snap_eu_edition.mjs suites/tree/wave-z/au/eu_prints.json
import { createRequire } from 'node:module';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { writeFileSync } from 'node:fs';
const req = createRequire(join(process.cwd(), 'package.json'));
const { runnerImport } = await import(pathToFileURL(req.resolve('vite')).href);
const opt = { configFile: false, logLevel: 'silent' };
const { module: ED } = await runnerImport('./src/legal/editions.ts', opt);
const out = { terms: ED.EDITIONS.eu.terms, withdrawal: ED.EDITIONS.eu.withdrawal, privacy: ED.EDITIONS.eu.privacy, imprint: ED.EDITIONS.eu.imprint };
const { module: L } = await runnerImport('./src/shared/legal.ts', opt);
out.checkout = L.CHECKOUT_LEGAL;
const { module: P } = await runnerImport('./src/legal/plain.ts', opt);
out.pack = P.legalMailPack();
writeFileSync(process.argv[2], JSON.stringify(out, null, 1));
console.log('ok');
