// The closing scene of the new landing (prototype: section.final): the last section of <main>, a dark study with Mantas's iris on
// acrylic, the headline, the gold button, and the line that the file is digital and printing is not part of the order.
//
//   <ClosingScene ctaRef={...} />     needs <LangProvider> and <CopyProvider> above it
//
// The closing picture is an AI visualisation and says so in its corner (the "AI visualisation" chip, the words of final.chip).
// Importing this file brings its own stylesheet, so it is loaded lazily with its section.
import type { Ref } from 'react';
import { useCopy } from './copy/useCopy';
import { useTryHref } from './links';
import { asset } from './assets';
import { ExampleChip } from './ui';
import './css/final.css';

export function ClosingScene({ ctaRef }: { ctaRef?: Ref<HTMLAnchorElement> }) {
  const { c } = useCopy();
  const tryHref = useTryHref();
  const pic = asset('m/study_acrylic_3x2__eye__wide', { pick: 2000 });
  return (
    <section className="lp-final" id="final" aria-labelledby="finalH">
      <div className="lp-bg">
        <img src={pic.src} srcSet={pic.srcset} sizes="(min-width: 960px) 1800px, 1200px" width={pic.w} height={pic.h} loading="lazy" decoding="async" alt={c.final.imageAlt} />
      </div>
      <ExampleChip variant="vis" label={c.final.chip} className="lp-final-chip" />
      <div className="lp-wrap">
        <h2 id="finalH">{c.final.title}</h2>
        <p className="lp-lede">{c.final.body}</p>
        <a className="lp-btn lp-btn-gold" id="ctaFinal" href={tryHref} ref={ctaRef}>
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
