import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './landing/css/index.css'
import './motion/motion.css'
import App from './App.tsx'
import { detectLang } from './shared/lang'
import { currentMarket } from './shared/markets'
import { preloadCopy } from './landing/copy/index'
import { startOrdering } from './landing/ordering'
import { watchPreloadErrors } from './landing/lazy'
import { boot, reveals } from './motion/motion'
import { adoptIntro } from './motion/handoff'

// The landing entry. index.html already holds the first screen as static HTML (<div id="shell">, written at build time by the
// heroShell plugin of vite.config.ts from src/landing/SiteTopView.tsx and HeroView.tsx, in the visitor's language: English in the
// markup, the others swapped in by an inline script), so the visitor sees the bar, the header and the hero, LCP picture included,
// before this script has run. React renders into the empty #root next to it: createRoot, never hydrateRoot, because the live page
// is more than the first screen. The shell goes away in the same frame in which React puts something on the page: a
// MutationObserver runs as a microtask right after the commit, before the browser paints. While the language file of a
// non-English visitor is still coming, React commits nothing and the shell stays; if React never commits (a script error), the
// static first screen stays as the fallback.
// Motion (src/motion): html.mo switches the hidden-until-revealed states on when motion is allowed, with a failsafe that lifts them
// after 3.5 s if no observer ever reports; reveals() then watches every [data-reveal] node, present or mounted later by the lazy
// sections. Nothing is hidden before this runs: the first screen's entrance is pure CSS and plays from the prerendered markup.
boot()
reveals()

const root = document.getElementById('root')!
const shell = document.getElementById('shell')
if (shell) {
  const handoff = new MutationObserver(() => {
    if (root.childElementCount > 0) {
      handoff.disconnect()
      // the entrance of the first screen is under way on the shell: the live hero continues it where it has got to instead of starting again
      adoptIntro(shell, root)
      shell.remove()
      // the other languages' first screens (src/landing/shell/render.tsx) have done their job too
      document.querySelectorAll('template[id^="tpl-"]').forEach((t) => t.remove())
    }
  })
  handoff.observe(root, { childList: true })
}

// a section's chunk or stylesheet that cannot be fetched (a flaky network, a new deploy): src/landing/lazy.ts
watchPreloadErrors()

// a visitor who reads another language than English: its file travels while React boots
preloadCopy(detectLang(currentMarket()))

// The page's two API answers (is ordering open, which currency does the visitor's country suggest) were asked for from the head of
// index.html. React starts once they are in, for at most MAX_HOLD_MS: the static first screen stays on screen meanwhile, and an offer
// of another currency (src/landing/MarketHint.tsx) is part of the first render that replaces it, so it is not added above the hero a
// moment after the visitor has seen the page (a layout shift of 0.12 on a phone). Where the answers are slower than that, React starts
// without them and the offer appears when they come, as it always did.
const MAX_HOLD_MS = 350
void Promise.race([startOrdering(), new Promise<void>((done) => setTimeout(done, MAX_HOLD_MS))]).then(() => {
  createRoot(root).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
})
