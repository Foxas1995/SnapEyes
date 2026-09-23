import { useEffect, useState } from 'react';
import { useLang } from './lang';
import { TRY_URL } from './config';
import { Logo } from './ui';
import type { Lang } from './copy';

export function LangSwitch() {
  const { lang, setLang, t } = useLang();
  const options: Lang[] = ['en', 'de'];
  return (
    <div role="group" aria-label={t.switchLabel} className="flex items-center rounded-full border border-white/10 p-0.5 text-[11px] font-semibold tracking-[0.12em]">
      {options.map((l) => (
        <button
          key={l}
          type="button"
          onClick={() => setLang(l)}
          aria-pressed={lang === l}
          lang={l}
          title={l === 'en' ? 'English' : 'Deutsch'}
          className={`min-w-[40px] rounded-full px-2.5 py-1.5 uppercase transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#f5c542] ${
            lang === l ? 'bg-white/10 text-white' : 'text-zinc-400 hover:text-white'
          }`}
        >
          {l}
        </button>
      ))}
    </div>
  );
}

export function Header() {
  const { t } = useLang();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const links: Array<[string, string]> = [
    ['#before-after', t.nav.beforeAfter],
    ['#how', t.nav.how],
    ['#styles', t.nav.styles],
    ['#pricing', t.nav.pricing],
    ['#faq', t.nav.faq],
  ];

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-colors duration-300 ${
        scrolled ? 'border-b border-white/[0.06] bg-[#030408]/85 backdrop-blur-xl' : 'border-b border-transparent bg-transparent'
      }`}
    >
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Logo tag={t.brandTag} />
        <nav aria-label={t.navLabels.main} className="hidden items-center gap-7 text-[13px] text-zinc-400 lg:flex">
          {links.map(([href, label]) => (
            <a key={href} href={href} className="transition-colors hover:text-white">
              {label}
            </a>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          <LangSwitch />
          <a
            href={TRY_URL}
            className="hidden h-9 items-center rounded-full border border-[#f5c542]/50 px-4 text-[13px] font-semibold text-[#f5c542] transition-colors hover:bg-[#f5c542] hover:text-[#030408] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#f5c542] sm:inline-flex"
          >
            {t.ctaShort}
          </a>
        </div>
      </div>
    </header>
  );
}
