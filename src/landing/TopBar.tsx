// The slim notice bar above the header (prototype: #topbar). A PURE component: props in, markup out, no hook and no window, so the
// same markup can be rendered to static HTML at build time (src/landing/shell) and live (./SiteTop.tsx).
//
// The bar keeps its row in both states: bar.soon ("Ordering opens soon. The free preview is available now.") and bar.open say
// about the same amount, so the flip when the deployment starts taking orders (src/landing/ordering.ts) moves nothing. The
// notice bar is the first of the three places that say "Ordering opens soon" (the other two: the pricing notice and the FAQ).
// Its height is what the fixed header sits under: ./SiteTop.tsx measures it into --bar-h (src/landing/shell/chrome.ts).
import type { Ref } from 'react';

export interface TopBarViewProps {
  /** The region's name for screen readers (bar.label, "Notice"). */
  label: string;
  /** The sentence: bar.soon, or bar.open once ordering is open. */
  text: string;
  barRef?: Ref<HTMLDivElement>;
}

export function TopBarView({ label, text, barRef }: TopBarViewProps) {
  return (
    <div className="lp-topbar" id="topbar" ref={barRef} role="region" aria-label={label}>
      <span id="barText">{text}</span>
    </div>
  );
}
