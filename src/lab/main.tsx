// LAB (2026-10-22): the page of the two centrepiece prototypes, src/lab/sphere.html. Not an entry of the site's build (vite.config.ts lists its pages),
// so it never ships; it runs on the dev server (npm run dev, then /src/lab/sphere.html) or from its own build (scripts/lab/sphere/vite.lab.config.mjs).
//
// It plays the landing's first screen the way the centrepiece would sit in it: the header's logo, the piece, the hero's title and button (the landing's
// own words, src/landing/copy). The piece arrives the way it would on the landing: a still poster of its first view is painted at once (an image the
// size of the stage, so nothing moves), and the interactive code is its own chunk, fetched once the poster is in and the browser is idle; it takes
// the poster's place when the pictures of its first view are decoded.
//
//   ?p=globe | ring     which prototype (globe by default)
//   ?lang=lt | en | de | hu
//   ?ui=0               no lab switch (the recordings)
//   ?rec                the recorder's virtual clock (src/lab/sphere/motion.ts)
//   ?shot               only the stage, for the poster (scripts/lab/sphere/poster.mjs)
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import '../index.css';
import '../landing/css/index.css';
import '../motion/tokens.css';
import './lab.css';
import Lab from './Lab';

const q = new URLSearchParams(location.search);
document.documentElement.lang = q.get('lang') ?? 'lt';
document.body.classList.add('lp');
if (q.has('shot')) document.body.classList.add('lab-shot');
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Lab />
  </StrictMode>,
);
