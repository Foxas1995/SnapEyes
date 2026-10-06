import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import '../index.css';
import '../motion/transition.css';
import '../motion/flow.css';
import { watchAway } from '../motion/flow';
import { OrderApp } from './OrderApp';
import { adoptLinkedEdition } from '../shared/legal';

// a link that names a market with its own legal texts (m=au, the withdrawal link of the Australian pages) keeps them,
// even while that market is paused for new orders; the order's own market (its status) follows once the server names it
adoptLinkedEdition();

// the waiting arcs and the hairlines pause while the tab is hidden (src/motion/flow.css)
watchAway();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <OrderApp />
  </StrictMode>,
);
