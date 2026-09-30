import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './landing/css/index.css'
import App from './App.tsx'
import { detectLang } from './shared/lang'
import { currentMarket } from './shared/markets'
import { preloadCopy } from './landing/copy/index'
import { newLandingFor } from './landing/gate'

// The landing entry. index.html already holds the first screen as static HTML (<div id="shell">, written at build time by the
// heroShell plugin of vite.config.ts from src/landing/shell), so the visitor sees the bar, the header and the hero, LCP picture
// included, before this script has run. React renders into the empty #root next to it: createRoot, never hydrateRoot, because
// the live page is more than the first screen and, for another language or market, other words (a German visitor's shell is
// hidden by the decision script in the head, so there is nothing to hydrate and nothing English to flash). The shell goes away
// in the same frame in which React puts something on the page: a MutationObserver runs as a microtask right after the commit,
// before the browser paints. While the language file of a non-English visitor is still coming, React commits nothing and the
// shell stays; if React never commits (a script error), the static first screen stays as the fallback.
const root = document.getElementById('root')!
const shell = document.getElementById('shell')
if (shell) {
  const handoff = new MutationObserver(() => {
    if (root.childElementCount > 0) {
      handoff.disconnect()
      shell.remove()
    }
  })
  handoff.observe(root, { childList: true })
}

// a visitor who reads another language than English: its file travels while React boots
const lang = detectLang(currentMarket())
if (newLandingFor(lang, currentMarket())) preloadCopy(lang)

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
