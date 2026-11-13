// The language menu of /try, /order, /gift and the legal pages when the page's market reads more than five languages (the euro
// market since Finnish, Estonian and Latvian, 2026-11-13: eight buttons in a row no longer fit beside the logo on a phone). A pill
// with the page's language opens a short list that names each language in itself. The landing page has the same menu in its own
// stylesheet (src/landing/Header.tsx, css/header.css). A market with five languages or fewer keeps the row of buttons each page had.
import { useEffect, useRef } from 'react';
import { LANG_NAMES, type Lang } from './lang';

export interface LangMenuProps {
  /** The group's name for a screen reader (the page's "Language"). */
  label: string;
  lang: Lang;
  langs: readonly Lang[];
  onSwitch: (l: Lang) => void;
}

/** More languages than a row of buttons can hold beside the logo on a phone. */
export const wantsLangMenu = (langs: readonly Lang[]): boolean => langs.length > 5;

export function LangMenu({ label, lang, langs, onSwitch }: LangMenuProps) {
  const ref = useRef<HTMLDetailsElement>(null);
  useEffect(() => {
    // a click outside the open menu or Escape closes it (Escape gives the focus back to the pill)
    const onClick = (e: MouseEvent) => {
      const d = ref.current;
      if (d?.open && !(e.target instanceof Node && d.contains(e.target))) d.open = false;
    };
    const onKey = (e: KeyboardEvent) => {
      const d = ref.current;
      if (e.key === 'Escape' && d?.open) {
        d.open = false;
        d.querySelector('summary')?.focus();
      }
    };
    document.addEventListener('click', onClick);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('click', onClick);
      document.removeEventListener('keydown', onKey);
    };
  }, []);
  return (
    <details ref={ref} data-testid="lang-menu" className="relative shrink-0">
      {/* the summary is the 44 px touch area; the pill inside it is what is seen (36 px) */}
      <summary
        aria-label={`${label}: ${LANG_NAMES[lang]}`}
        className="group flex h-11 cursor-pointer list-none select-none items-center rounded-full focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold [&::-webkit-details-marker]:hidden"
      >
        <span aria-hidden="true" className="flex h-9 items-center gap-1.5 rounded-full border border-white/10 px-3 text-[11px] font-semibold tracking-[0.12em] text-zinc-300 transition-colors group-hover:text-white">
          {lang.toUpperCase()}
          <svg viewBox="0 0 10 6" className="h-1.5 w-2.5 opacity-70" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M1 1l4 4 4-4" />
          </svg>
        </span>
      </summary>
      <div role="group" aria-label={label} className="absolute right-0 top-full z-30 mt-1 grid min-w-[168px] rounded-[14px] border border-white/10 bg-[#0b0e15] p-1.5 shadow-[0_18px_40px_rgba(0,0,0,0.55)]">
        {langs.map((l) => (
          <button
            key={l}
            type="button"
            lang={l}
            aria-pressed={lang === l}
            title={LANG_NAMES[l]}
            onClick={() => {
              if (ref.current) {
                ref.current.open = false;
                ref.current.querySelector('summary')?.focus();   // the chosen button is hidden again: the focus goes back to the pill
              }
              onSwitch(l);
            }}
            className={`h-11 rounded-[9px] px-3 text-left text-sm transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold ${
              lang === l ? 'bg-white/10 text-white shadow-[inset_0_0_0_1px_var(--gold-primary)]' : 'text-zinc-300 hover:bg-white/5 hover:text-white'
            }`}
          >
            {LANG_NAMES[l]}
          </button>
        ))}
      </div>
    </details>
  );
}
