// The closing scene of the new landing (prototype: section.final): the last section of <main>, a dark study with Mantas's iris on
// acrylic, the headline, the gold button, and the line that the file is digital and printing is not part of the order.
//
//   <ClosingScene ctaRef={...} />     needs <LangProvider> and <CopyProvider> above it
//
// The closing picture is an AI visualisation and says so in its corner (the "AI visualisation" chip, the words of final.chip).
// Importing this file brings its own stylesheet, so it is loaded lazily with its section.
// Motion (motion spec 6.14): when the scene is well in view the large picture opens from a frame, a mat opening: it starts inset by 7 percent
// with rounded corners (86 percent of it is on screen from the first frame), and opens to the full band in 1.3 s while the picture inside
// settles from 1.03 to 1 (src/landing/css/final.css). The headline rises out of its mask, the sentence and the button rise after it. The
// "AI visualisation" label and the line that the file is digital and printing is not part of the order never move and never fade.
import type { CSSProperties, Ref } from 'react';
import { useCopy } from './copy/useCopy';
import { useTryHref } from './links';
import { asset } from './assets';
import { ExampleChip } from './ui';
import { Title } from '../motion/Title';
import './css/final.css';

/** a reveal that starts after this many stagger steps (80 ms each): the headline first, then the sentence, then the button */
const after = (steps: number) => ({ '--i': steps }) as CSSProperties;

export function ClosingScene({ ctaRef }: { ctaRef?: Ref<HTMLAnchorElement> }) {
  const { c } = useCopy();
  const tryHref = useTryHref();
  const pic = asset('m/study_acrylic_3x2__eye__wide', { pick: 2000 });
  return (
    <section className="lp-final" id="final" aria-labelledby="finalH">
      {/* the cue: a one pixel mark at a third of the scene's height, observed by the engine like any reveal; the picture opens when it is on
          screen, so that the visitor sees the opening and not a sliver of the band coming over the edge */}
      <span className="lp-open-cue" data-reveal="cue" aria-hidden="true" />
      <div className="lp-bg">
        <img src={pic.src} srcSet={pic.srcset} sizes="(min-width: 960px) 1800px, 1200px" width={pic.w} height={pic.h} loading="lazy" decoding="async" alt={c.final.imageAlt} />
      </div>
      <ExampleChip variant="vis" label={c.final.chip} className="lp-final-chip" />
      <div className="lp-wrap">
        <Title id="finalH" text={c.final.title} />
        <p className="lp-lede" data-reveal="fade" style={after(2.5)}>{c.final.body}</p>
        <a className="lp-btn lp-btn-gold" id="ctaFinal" href={tryHref} ref={ctaRef} data-reveal="fade" style={after(4)}>
          <span>{c.cta}</span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M5 12h14M13 6l6 6-6 6" />
          </svg>
        </a>
        <p className="lp-fine">{c.final.small}</p>
      </div>
    </section>
  );
}

export default ClosingScene;
