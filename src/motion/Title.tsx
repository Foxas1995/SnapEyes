// A title with masked phrase reveals (motion spec 5.4): ONE source string drives the typography.
//   "\n"     a phrase break. Each phrase is one masked block that rises as a unit (never per character, so it cannot break in any
//            language). A string without "\n" is one phrase.
//   *word*   the accent word: gold, same weight (no italic, no second typeface). Chosen by hand per language, because Lithuanian
//            and Hungarian inflect the word. A string without markers has no accent word.
//   final .  a closing full stop is wrapped in .lp-dot (gold) by the renderer: nothing to mark.
// The words of the heading stay real text for crawlers and assistive technology: the phrases are separated by a real space, so
// textContent reads "Your real iris, made into art." and no markup is a letter wide.
//
// The heading is revealed by [data-reveal="mask"] (src/motion/motion.ts reveals(), once, when it comes into view), or, with
// intro, by the CSS entrance of the first screen (which has no JavaScript to wait for: the phrases rise from the already painted
// page). A pure component: no hook and no window, so the prerendered first screen can render it at build time.
import { Fragment, type CSSProperties, type ElementType } from 'react';

const accent = (s: string) => s.split(/(\*[^*]+\*)/g).map((p, i) => (p.startsWith('*') ? <span key={i} className="lp-acc">{p.slice(1, -1)}</span> : p));

export interface TitleProps {
  text: string;
  as?: ElementType;
  /** The first screen: the phrases enter by the CSS intro (delays .15 s, .25 s, ...) instead of by scrolling into view. */
  intro?: boolean;
  /** Type scale class: lp-t-title for a section, lp-t-display for the hero. */
  className?: string;
  id?: string;
}

export function Title({ text, as: Tag = 'h2', intro = false, className = 'lp-t-title', id }: TitleProps) {
  const phrases = text.split('\n');
  const last = phrases.length - 1;
  return (
    <Tag id={id} className={`${className} lp-phrased`} {...(intro ? {} : { 'data-reveal': 'mask' })}>
      {phrases.map((ph, k) => {
        const dot = k === last && ph.endsWith('.');
        return (
          <Fragment key={k}>
            <span className="lp-line-mask" style={{ '--k': k } as CSSProperties}>
              <span className={intro ? 'lp-rise-line' : undefined} style={intro ? ({ '--d': `${0.15 + 0.1 * k}s` } as CSSProperties) : undefined}>
                {accent(dot ? ph.slice(0, -1) : ph)}
                {dot && <span className="lp-dot">.</span>}
              </span>
            </span>
            {k < last && ' '}
          </Fragment>
        );
      })}
    </Tag>
  );
}
