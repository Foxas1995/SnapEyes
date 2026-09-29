import { defineConfig, runnerImport, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

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

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
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
      },
    },
  },
  server: {
    proxy: {
      // local Python stand-in for the Vercel functions: python scripts/dev_api.py
      '/api': 'http://localhost:5050',
    },
  },
})
