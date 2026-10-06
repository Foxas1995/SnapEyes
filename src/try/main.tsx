import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '../index.css'
import '../motion/transition.css'
import '../motion/flow.css'
import { watchAway } from '../motion/flow'
import { TryApp } from './TryApp'

// the waiting arc and the hairline pause while the tab is hidden (src/motion/flow.css)
watchAway()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <TryApp />
  </StrictMode>,
)
