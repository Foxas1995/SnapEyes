// LAB: what the front artwork says, the same in both prototypes: the style's name and whose eye it is (the small honest label); the globe adds one
// button under the artwork it opens (the ring leaves the button to the hero, so the page never shows two gold buttons for one thing).
import type { ReactNode } from 'react';
import type { Art } from './art';
import type { Words } from './words';

export function Info({ art, words, tryHref, arrow }: { art: Art | null; words: Words; tryHref?: string; arrow?: ReactNode }) {
  return (
    <>
      <p className="sx-name" aria-live="polite">{art ? art.name : ' '}</p>
      <p className="sx-prov">{art ? words.prov[art.prov] : ' '}</p>
      {tryHref && (
        <a className="lp-btn lp-btn-gold gold-metal sx-cta" href={tryHref}>
          <span>{words.cta}</span>
          {arrow}
        </a>
      )}
    </>
  );
}
