// The Reveal's public surface (work package WP9), for the pages that show it: /try (src/try/ResultView.tsx) today, the landing page (WP14: its own branch,
// interface names only) tomorrow. A page gives the components plain props (the customer's frame or a pre-made example, the restored iris, the geometry) and
// the words of its own language (src/try/copy.ts T.result.reveal is the model); nothing here knows where its pictures come from, and nothing here stores
// or uploads a picture (decision C10).
export { Reveal, RestoredDisc, usePrefersReducedMotion, type RevealLabels } from './Reveal';
export { RevealStrip } from './RevealStrip';
export { useRevealFrame, type FrameEye, type RevealState } from './useRevealFrame';
export { wideFrame, drawFrame, type WideFrame } from './wideFrame';
export { parseReveal, revealView, revealGeometry, tightFit, withheldByColour, type Fit, type Geometry, type RevealParams, type RevealView } from './revealMath';
