import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import '../index.css';
import '../landing/landing.css';
import './legal.css';
import { LegalApp } from './LegalApp';
import { LEGAL_DOCS, type LegalDocId } from '../shared/legal';

// privacy.html, terms.html, withdrawal.html and imprint.html all load this entry; data-doc says which text to show.
const root = document.getElementById('root')!;
const asked = root.dataset.doc ?? '';
const doc: LegalDocId = (LEGAL_DOCS as readonly string[]).includes(asked) ? (asked as LegalDocId) : 'imprint';

createRoot(root).render(
  <StrictMode>
    <LegalApp doc={doc} />
  </StrictMode>,
);
