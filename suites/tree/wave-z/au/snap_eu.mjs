// Snapshot of the EU legal docs (terms, withdrawal, privacy, imprint; en, de) and the checkout legal wording, as the
// site builds them, BEFORE the AU work: the AU tests compare the EU edition against it. Run with the repo as cwd.
import { createRequire } from 'node:module';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { writeFileSync } from 'node:fs';
const req = createRequire(join(process.cwd(), 'package.json'));
const { runnerImport } = await import(pathToFileURL(req.resolve('vite')).href);
const opt = { configFile: false, logLevel: 'silent' };
const out = {};
for (const [id, file, name] of [['terms', 'terms', 'TERMS'], ['withdrawal', 'withdrawal', 'WITHDRAWAL'], ['privacy', 'privacy', 'PRIVACY'], ['imprint', 'imprint', 'IMPRINT']]) {
  const { module } = await runnerImport(`./src/legal/docs/${file}.ts`, opt);
  out[id] = module[name];
}
const { module: L } = await runnerImport('./src/shared/legal.ts', opt);
out.checkout = L.CHECKOUT_LEGAL;
const { module: P } = await runnerImport('./src/legal/plain.ts', opt);
out.pack = P.legalMailPack();
writeFileSync(process.argv[2], JSON.stringify(out, null, 1));
console.log('ok');
