// The scroll-lit sentence (motion spec 5.4): renders a sentence as word spans that lit() (./motion.ts) brings from the dim floor
// to full opacity in sequence while the visitor scrolls. At most ONE accent word: mark it in the copy as *word* (chosen by hand per
// language, like the title accent); punctuation may follow the closing star. The words are display: inline spans (never
// inline-block), so hyphenation keeps working in German and Hungarian. 25 to 40 words, one sentence per page. Without the engine
// (reduced motion, no script, the failsafe) every word is at full opacity: the dim state exists only under html.mo.
//
//   const ref = useRef<HTMLParagraphElement>(null);
//   useEffect(() => (ref.current ? lit(ref.current) : undefined), []);
//   <Lit text={...} ref={ref} />
import type { Ref } from 'react';

export function Lit({ text, ref }: { text: string; ref?: Ref<HTMLParagraphElement> }) {
  const w = text.split(' ');
  return (
    <p className="lp-lit lp-t-lead" ref={ref}>
      {w.map((x, i) => {
        const m = /^\*([^*]+)\*(.*)$/.exec(x);
        return (
          <span key={i}>
            <span data-w className={m ? 'lp-g' : undefined}>{m ? m[1] + m[2] : x}</span>
            {i < w.length - 1 ? ' ' : ''}
          </span>
        );
      })}
    </p>
  );
}
