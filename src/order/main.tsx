import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import '../index.css';
import { OrderApp } from './OrderApp';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <OrderApp />
  </StrictMode>,
);
