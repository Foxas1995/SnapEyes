import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import '../index.css';
import '../motion/transition.css';
import '../motion/flow.css';
import { watchAway } from '../motion/flow';
import { GiftApp } from './GiftApp';

// the waiting arcs and the hairlines pause while the tab is hidden (src/motion/flow.css)
watchAway();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <GiftApp />
  </StrictMode>,
);
