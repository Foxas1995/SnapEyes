import { defineConfig, runnerImport, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { checkPrices, type ClientMarkets, type LandingPriceModule } from './scripts/check_prices.mjs'
import { checkPack, checkTexts } from './scripts/check_texts.mjs'
import { checkLandingAssets } from './scripts/check_landing_assets.mjs'

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
// own, and the new landing prints only the visitor's own ladder (scripts/check_prices.mjs; `npm run check:prices` runs the
// same checks alone). Any problem stops the build.
function priceCheck(): Plugin {
  return {
    name: 'snapeyes-price-check',
    apply: 'build',
    async buildStart() {
      const { module } = await runnerImport<ClientMarkets>('./src/shared/markets.ts', { configFile: false, logLevel: 'silent' })
      // the new landing's price texts (src/landing/priceText.ts) are run against every price ladder, variants included
      const landing = (await runnerImport<LandingPriceModule>('./src/landing/priceText.ts', { configFile: false, logLevel: 'silent' })).module
      const problems = checkPrices(process.cwd(), module, landing)
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

// The landing page's pictures (public/assets/landing, written by scripts/build_landing_assets.py) against their manifest
// (src/landing/assets.ts): content hashes, sizes, nothing unused or missing, the byte budgets, the immutable cache headers of
// vercel.json (scripts/check_landing_assets.mjs; `npm run check:assets` runs it alone). The release gate (which tiles of the
// style gallery the engine can make today) is a notice, an error only with LANDING_GATE=strict. Any problem stops the build.
function assetCheck(): Plugin {
  return {
    name: 'snapeyes-landing-assets-check',
    apply: 'build',
    async buildStart() {
      const load = async (p: string) => (await runnerImport<any>(p, { configFile: false, logLevel: 'silent' })).module
      const { problems, notices } = checkLandingAssets(process.cwd(), await load('./src/landing/assets.ts'), await load('./src/landing/assets.data.ts'))
      for (const n of notices) this.warn(n)
      if (problems.length) this.error(`landing assets check failed (${problems.length}):\n  ${problems.join('\n  ')}`)
    },
  }
}

// The landing page's first screen, prerendered into index.html (BUILD_PLAN section 4, step 1). Without it the first paint waits for
// the whole React bundle (about 2 s of LCP on a phone over slow 4G instead of about 1.3 s): with it the browser paints the notice
// bar, the header and the hero, with the LCP picture already preloaded, before a line of script has run.
//   * lp:shell (body): the English first screen of the default market, rendered by the very components the live page uses
//     (src/landing/shell: parts.tsx, render.tsx), inside <div id="shell">. src/main.tsx takes it away the moment React has put the
//     page in its place (createRoot, not hydrateRoot: the live page renders more than the first screen, and another language or
//     market renders other words, so there is nothing to hydrate against). The prices in it are held back (invisible) like every
//     price of the page until the server has answered.
//   * lp:head: (1) the decision script (src/landing/shell/scripts.ts): a visitor who will read another language or market than the
//     shell's must never see the English shell flash up, so it is hidden for them; written from the tables of src/shared/lang.ts,
//     src/shared/markets.ts and src/landing/gate.ts, and proven equal to detectLang and detectMarket by scripts/check_shell.mjs.
//     A visitor the new landing does not serve (Lithuanian, Hungarian, forint while those have no copy) gets the preload of today's
//     first picture from that script. (2) The preload of the new hero picture.
//   * the title, description and share texts come from the English copy (src/landing/copy/en.json meta), as they do at run time.
// Loaded through Vite's module runner, like the other build steps, so this file imports no app code itself.
function heroShell(): Plugin {
  type Parts = { html: string; preload: string; decision: string; bar: string; meta: { title: string; description: string; shareDescription: string } }
  let built: Promise<Parts> | null = null
  const load = async (p: string) => (await runnerImport<any>(p, { configFile: false, logLevel: 'silent' })).module
  async function make(): Promise<Parts> {
    const markets = await load('./src/shared/markets.ts')
    const lang = await load('./src/shared/lang.ts')
    const priceText = await load('./src/landing/priceText.ts')
    const gate = await load('./src/landing/gate.ts')
    const config = await load('./src/landing/config.ts')
    const shell = await load('./src/landing/shell/render.tsx')
    const scripts = await load('./src/landing/shell/scripts.ts')
    const market: string = markets.DEFAULT_MARKET
    const all = Object.keys(markets.MARKETS)
    const rule = {
      defaultMarket: market,
      lang: 'en',
      selectable: markets.SELECTABLE,
      allowed: Object.fromEntries(all.map((m) => [m, lang.marketLangs(m)])),
      own: Object.fromEntries(all.map((m) => [m, lang.marketDefaultLang(m)])),
      newLangs: gate.NEW_LANDING_LANGS,
      legacyMarkets: all.filter((m) => markets.currencyOf(m) === 'huf'),
      legacy: { href: config.styleSrc('celestial-gold', 800), srcset: config.styleSrcSet('celestial-gold'), sizes: '(min-width: 640px) 520px, calc(100vw - 32px)' },
    }
    // the price of the micro line: the ladder the shell is made from (held back in the markup, see src/landing/shell/parts.tsx)
    const fromPrice: string = priceText.landingPrices(markets.priceList(market), market, 'en').from
    const langs = lang.LANGS.filter((l: string) => gate.NEW_LANDING_LANGS.includes(l) && lang.langAllowed(l, market))
    const out = shell.renderShell({ fromPrice, langs })
    return {
      html: out.html,
      preload: out.preload,
      decision: scripts.decisionScript(rule),
      bar: scripts.barScript,
      meta: out.meta,
    }
  }
  const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  return {
    name: 'snapeyes-hero-shell',
    configureServer(server) {
      // the shell follows the files it is made from while the dev server runs
      server.watcher.on('change', (f) => {
        if (/\/src\/(landing|shared)\/|markets\.py$/.test(f.split('\\').join('/'))) built = null
      })
    },
    async transformIndexHtml(html, ctx) {
      if (ctx.path !== '/index.html') return html
      built ??= make()
      const p = await built.catch((e) => {
        built = null
        throw e
      })
      if (!html.includes('<!-- lp:head -->') || !html.includes('<!-- lp:shell -->')) throw new Error('index.html lost its lp:head or lp:shell marker')
      return html
        .replace(/<title>[\s\S]*?<\/title>/, () => `<title>${esc(p.meta.title)}</title>`)
        .replace(/(<meta name="description" content=")[^"]*(")/, (_, a, b) => `${a}${esc(p.meta.description)}${b}`)
        .replace(/(<meta property="og:title" content=")[^"]*(")/, (_, a, b) => `${a}${esc(p.meta.title)}${b}`)
        .replace(/(<meta property="og:description" content=")[^"]*(")/, (_, a, b) => `${a}${esc(p.meta.shareDescription)}${b}`)
        .replace(/(<meta name="twitter:title" content=")[^"]*(")/, (_, a, b) => `${a}${esc(p.meta.title)}${b}`)
        .replace(/(<meta name="twitter:description" content=")[^"]*(")/, (_, a, b) => `${a}${esc(p.meta.shareDescription)}${b}`)
        .replace('<!-- lp:head -->', () => `<script>${p.decision}</script>\n    ${p.preload}`)
        .replace('<!-- lp:shell -->', () => `<div id="shell" class="lp-shell">${p.html}</div>\n    <script>${p.bar}</script>`)
    },
  }
}

// The page's own script starts after the LCP picture (build only, BUILD_PLAN section 5). Left in the head, the module script and its 8
// modulepreload links (React, the old sections: about 120 kB on the wire) compete with the picture for the phone's 1.6 Mbit/s: measured
// over slow 4G the picture arrived at about 1.5 s with them and about 0.9 s without. The first screen is static and needs no script, so
// this takes them out of the final HTML and adds an inline loader (src/landing/shell/scripts.ts loaderScript) that starts them as soon as
// the hero picture has loaded. A visitor the shell is not for loads them at once.
function lateMainScript(): Plugin {
  return {
    name: 'snapeyes-late-main-script',
    apply: 'build',
    transformIndexHtml: {
      order: 'post',
      async handler(html, ctx) {
        if (ctx.path !== '/index.html' || !ctx.bundle) return html
        const main = /<script type="module"[^>]*\ssrc="([^"]+)"[^>]*><\/script>\s*/.exec(html)
        if (!main) throw new Error('dist index.html: the module script was not found')
        const preloads = [...html.matchAll(/<link rel="modulepreload"[^>]*\shref="([^"]+)"[^>]*>\s*/g)].map((m) => m[1])
        const scripts = await runnerImport<any>('./src/landing/shell/scripts.ts', { configFile: false, logLevel: 'silent' })
        return html
          .replace(main[0], '')
          .replace(/<link rel="modulepreload"[^>]*>\s*/g, '')
          .replace('<div id="root"></div>', () => `<div id="root"></div>\n    <script>${scripts.module.loaderScript(main[1], preloads)}</script>`)
      },
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
    assetCheck(),
    legalMail(),
    heroShell(),
    lateMainScript(),
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
