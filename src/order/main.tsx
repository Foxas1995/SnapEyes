import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import '../index.css';
import { OrderApp } from './OrderApp';
import { adoptLinkedEdition } from '../shared/legal';

// a link that names a market with its own legal texts (m=au, the withdrawal link of the Australian pages) keeps them,
// even while that market is paused for new orders; the order's own market (its status) follows once the server names it
adoptLinkedEdition();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <OrderApp />
  </StrictMode>,
);
