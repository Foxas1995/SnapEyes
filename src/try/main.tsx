import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '../index.css'
import { TryApp } from './TryApp'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <TryApp />
  </StrictMode>,
)
