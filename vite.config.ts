import { defineConfig, runnerImport, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { checkPrices, type ClientMarkets } from './scripts/check_prices.mjs'

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
      const { module } = await runnerImport<{ legalMailPack: () => unknown }>('./src/legal/plain.ts', {
        configFile: false,
        logLevel: 'silent',
      })
      this.emitFile({ type: 'asset', fileName: 'legal/order-mail.json', source: JSON.stringify(module.legalMailPack()) })
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

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    priceCheck(),
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
      // local Python stand-in for the Vercel functions: python scripts/dev_api.py. The one source file the site itself
      // imports from api/ (src/shared/markets.ts reads api/_lib/markets.py as text) is served by Vite, not proxied
      '/api': {
        target: 'http://localhost:5050',
        bypass: (req) => (req.url && req.url.startsWith('/api/_lib/markets.py?') ? req.url : undefined),
      },
    },
  },
})
