import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import '../index.css';
import './legal.css';
import { LegalApp } from './LegalApp';
import { LEGAL_DOCS, adoptLinkedEdition, type LegalDocId } from '../shared/legal';
import { startPixel } from '../shared/metaPixel';

// privacy.html, terms.html, withdrawal.html and imprint.html all load this entry; data-doc says which text to show.
const root = document.getElementById('root')!;
const asked = root.dataset.doc ?? '';
const doc: LegalDocId = (LEGAL_DOCS as readonly string[]).includes(asked) ? (asked as LegalDocId) : 'imprint';

// a link to the Australian texts (m=au) keeps showing them, and keeps m=au in every link, even while that market is
// paused for new orders: the texts an order was made under stay readable
adoptLinkedEdition();

// the Meta pixel (src/shared/metaPixel.ts): PageView only, once the page has loaded and the browser is idle
startPixel('script');

createRoot(root).render(
  <StrictMode>
    <LegalApp doc={doc} />
  </StrictMode>,
);
