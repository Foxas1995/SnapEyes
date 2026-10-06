// The language switch of the legal pages (privacy, terms, withdrawal, imprint): one button per language the visitor's market can be
// read in. It was the landing page's switch before landing v2 (src/landing/Header.tsx); the landing has its own now (the header
// of src/landing/Header.tsx, in the page's own classes), and the legal pages keep this one exactly as it was.
import { useLang } from '../landing/lang';
import { LANG_NAMES, marketLangs } from '../shared/lang';
import { useMarket } from '../shared/useMarket';

/** One button per language the visitor's market can be read in (English, German, Lithuanian and Hungarian; the
 *  Australian market: English and German, src/shared/legal.ts EDITION_LANGS). Below 340 px wide (the smallest phones)
 *  the buttons are narrower, so four of them still fit beside the logo and none is pushed off the screen. */
export function LangSwitch() {
  const { lang, setLang, t } = useLang();
  const options = marketLangs(useMarket());
  return (
    <div role="group" aria-label={t.switchLabel} className="flex items-center rounded-full border border-white/10 p-0.5 text-[11px] font-semibold tracking-[0.12em]">
      {options.map((l) => (
        <button
          key={l}
          type="button"
          onClick={() => setLang(l)}
          aria-pressed={lang === l}
          lang={l}
          title={LANG_NAMES[l]}
          className={`min-w-[40px] rounded-full px-2.5 py-1.5 max-[340px]:min-w-[28px] max-[340px]:px-1.5 uppercase transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#f5c542] ${
            lang === l ? 'bg-white/10 text-white' : 'text-zinc-400 hover:text-white'
          }`}
        >
          {l}
        </button>
      ))}
    </div>
  );
}
