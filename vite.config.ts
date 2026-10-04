import { defineConfig, runnerImport, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { checkPrices, type ClientMarkets } from './scripts/check_prices.mjs'
import { checkPack, checkTexts } from './scripts/check_texts.mjs'
import { checkStyles, describeRegistry } from './scripts/check_styles.mjs'

// The legal texts for the order confirmation email (src/legal/plain.ts legalMailPack: the terms of sale and the
// withdrawal information with the model form, per language, plus the seller's contact facts). Built from the same
// constants the legal pages print and written to /legal/order-mail.json, where api/_lib/pay.py can read them from its
// own deployment. Loaded through Vite's module runner, so this file never imports app code itself
// (tsconfig.node.json checks only this file, with Node's module rules).
function legalMail(): Plugin {
  return {
    name: 'snapeyes-legal-mail',
    apply: 'build',
    async generateBundle() {
      const load = async (p: string) => (await runnerImport<any>(p, { configFile: false, logLevel: 'silent' })).module
      const source = JSON.stringify((await load('./src/legal/plain.ts')).legalMailPack())
      // the file itself is checked before it is written: every edition complete, and no dash, slip or untranslated English
      // in a Lithuanian or Hungarian text (scripts/check_texts.mjs checkPack)
      const problems = checkPack(JSON.parse(source), await load('./src/shared/legal.ts'), await load('./src/shared/markets.ts'))
      if (problems.length) this.error(`legal pack check failed (${problems.length}):\n  ${problems.join('\n  ')}`)
      this.emitFile({ type: 'asset', fileName: 'legal/order-mail.json', source })
    },
  }
}

// Every price lives in api/_lib/markets.py (the server charges from it; src/shared/markets.ts reads it for every page).
// Before a build: that file is sound, the site's own reading of it (loaded through Vite's module runner, as the legal
// pack is) gives the server's prices for every market, eye count and style, and no other file holds a price of its
// own (scripts/check_prices.mjs; `npm run check:prices` runs the file checks alone). Any problem stops the build.
function priceCheck(): Plugin {
  return {
    name: 'snapeyes-price-check',
    apply: 'build',
    async buildStart() {
      const { module } = await runnerImport<ClientMarkets>('./src/shared/markets.ts', { configFile: false, logLevel: 'silent' })
      const problems = checkPrices(process.cwd(), module)
      if (problems.length) this.error(`price check failed (${problems.length}):\n  ${problems.join('\n  ')}`)
    },
  }
}

// The texts: the Lithuanian and Hungarian dictionaries and legal texts have the shape of the English ones, no string holds
// an en or em dash or untranslated English, every edition of the legal texts is complete (its languages, its prices in
// its currency, its contract languages), the consent version is a real date and the server's (scripts/check_texts.mjs;
// `npm run check:texts` runs it alone). Any problem stops the build.
function textCheck(): Plugin {
  return {
    name: 'snapeyes-text-check',
    apply: 'build',
    async buildStart() {
      const load = async (p: string) => (await runnerImport<any>(p, { configFile: false, logLevel: 'silent' })).module
      const problems = await checkTexts(load, process.cwd())
      if (problems.length) this.error(`text check failed (${problems.length}):\n  ${problems.join('\n  ')}`)
    },
  }
}

// Every style id, name, layout and the price class lives in api/_lib/styles_registry.py (src/shared/styles.ts reads it for every page;
// api/_lib/catalogue.py for the server). Before a build: both literals are sound, no other file writes a style id, the copy
// dictionaries keyed by style id and the layout names match it, the site's price rule agrees with the registry's price classes, and the
// terms of sale name the price classes (scripts/check_styles.mjs; `npm run check:styles` runs it alone). The registry hash is printed.
function styleCheck(): Plugin {
  return {
    name: 'snapeyes-style-check',
    apply: 'build',
    async buildStart() {
      const load = async (p: string) => (await runnerImport<any>(p, { configFile: false, logLevel: 'silent' })).module
      const problems = await checkStyles(process.cwd(), load)
      if (problems.length) this.error(`style check failed (${problems.length}):\n  ${problems.join('\n  ')}`)
      console.log(describeRegistry(process.cwd()))
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    priceCheck(),
    textCheck(),
    styleCheck(),
    legalMail(),
  ],
  build: {
    rollupOptions: {
      input: {
        main: 'index.html',
        try: 'try.html',
        // the legal pages (one entry, src/legal/main.tsx; vercel.json cleanUrls serves them at /privacy etc.)
        privacy: 'privacy.html',
        terms: 'terms.html',
        withdrawal: 'withdrawal.html',
        imprint: 'imprint.html',
        // the order page (src/order/main.tsx): /order?o=&k=[&s=] from the Stripe success page and the emails
        order: 'order.html',
        // the owner's admin panel (src/admin/main.tsx): /admin, noindex, not linked from the public site
        admin: 'admin.html',
      },
    },
  },
  server: {
    proxy: {
      // local Python stand-in for the Vercel functions: python scripts/dev_api.py. The source files the site itself
      // imports from api/ (src/shared/markets.ts reads api/_lib/markets.py, src/shared/styles.ts reads
      // api/_lib/styles_registry.py and src/shared/layouts.ts reads api/_lib/layout_names.py, all as text) are served by Vite, not proxied
      '/api': {
        target: 'http://localhost:5050',
        bypass: (req) => (req.url && /^\/api\/_lib\/(markets|styles_registry|layout_names)\.py\?/.test(req.url) ? req.url : undefined),
      },
    },
  },
})
