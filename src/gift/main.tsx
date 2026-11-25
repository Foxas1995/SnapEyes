import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import '../index.css';
import '../motion/transition.css';
import '../motion/flow.css';
import { watchAway } from '../motion/flow';
import { GiftApp } from './GiftApp';
import { startPixel } from '../shared/metaPixel';

// the waiting arcs and the hairlines pause while the tab is hidden (src/motion/flow.css)
watchAway();

// the Meta pixel (src/shared/metaPixel.ts) WITHOUT Meta's script: after the payment the address names the voucher's session, which shows its code, so
// each event is one request that names the path alone
startPixel('image');

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <GiftApp />
  </StrictMode>,
);
