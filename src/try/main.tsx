import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '../index.css'
import '../motion/transition.css'
import '../motion/flow.css'
import { watchAway } from '../motion/flow'
import { TryApp } from './TryApp'
import { startPixel } from '../shared/metaPixel'

// the waiting arc and the hairline pause while the tab is hidden (src/motion/flow.css)
watchAway()

// the Meta pixel (src/shared/metaPixel.ts): Meta's script once the page has loaded and the browser is idle, PageView, then what the page reported
startPixel('script')

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <TryApp />
  </StrictMode>,
)
