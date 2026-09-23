import type { ReactNode } from 'react';
import { Check } from 'lucide-react';
import { useLang } from './lang';
import { MAX_EYES, PRICE_CENTS, TRY_URL, centsForEyes } from './config';
import { formatEuro } from './copy';
import { SectionHead } from './ui';

function Card({ title, children, accent = false, className = '' }: { title: string; children: ReactNode; accent?: boolean; className?: string }) {
  return (
    <div className={`flex flex-col rounded-2xl border p-6 sm:p-7 ${accent ? 'border-[#f5c542]/35 bg-[#f5c542]/[0.04]' : 'border-white/[0.07] bg-white/[0.02]'} ${className}`}>
      <h3 className="font-body text-[11px] font-semibold uppercase tracking-[0.22em] text-zinc-400">{title}</h3>
      {children}
    </div>
  );
}

function Row({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="border-t border-white/[0.06] py-3 first:border-t-0 first:pt-0">
      <div className="flex items-baseline justify-between gap-4">
        <span className="text-sm text-zinc-300">{label}</span>
        <span className="shrink-0 font-luxury text-lg font-semibold text-white">{value}</span>
      </div>
      {note && <p className="mt-1 text-xs leading-relaxed text-zinc-400">{note}</p>}
    </div>
  );
}

// No purchase buttons: ordering is not open yet (no checkout). The only action is the free preview.
export function Pricing() {
  const { t, lang } = useLang();
  const p = t.pricing;
  const eur = (c: number) => formatEuro(c, lang);
  return (
    <section id="pricing" className="scroll-mt-16 border-t border-white/[0.06] py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <SectionHead eyebrow={p.eyebrow} title={p.title} />

        <p role="note" className="mt-8 inline-flex items-start gap-3 rounded-2xl border border-[#f5c542]/30 bg-[#f5c542]/[0.06] px-5 py-3.5 text-[15px] font-medium text-[#f7d77a]">
          <span aria-hidden="true" className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[#f5c542]" />
          <span>{p.notice}</span>
        </p>

        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Card title={p.previewTitle} accent>
            <p className="mt-4 font-luxury text-[32px] font-semibold leading-none text-white">{p.previewPrice}</p>
            <ul className="mt-5 grid gap-2.5 text-sm text-zinc-300">
              {p.previewItems.map((it) => (
                <li key={it} className="flex items-center gap-2.5">
                  <Check aria-hidden="true" className="h-4 w-4 shrink-0 text-[#f5c542]" />
                  {it}
                </li>
              ))}
            </ul>
            <a
              href={TRY_URL}
              className="mt-7 inline-flex min-h-11 items-center justify-center rounded-full border border-[#f5c542]/60 px-5 py-2.5 text-center text-sm font-semibold text-[#f5c542] transition-colors hover:bg-[#f5c542] hover:text-[#030408] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#f5c542] sm:mt-auto"
            >
              {t.cta}
            </a>
          </Card>

          <Card title={p.oneEyeTitle}>
            <p className="mt-3 text-sm leading-relaxed text-zinc-400">{p.oneEyeNote}</p>
            <div className="mt-5">
              <Row label={p.studioBlack} value={eur(PRICE_CENTS.studioBlack)} />
              <Row label={p.artBackground} value={eur(PRICE_CENTS.artBackground)} note={p.artBackgroundNote} />
            </div>
          </Card>

          <Card title={p.severalTitle} className="sm:col-span-2 lg:col-span-1">
            <p className="mt-3 text-sm leading-relaxed text-zinc-400">{p.severalNote}</p>
            <div className="mt-5">
              <Row label={p.duoLabel} value={eur(PRICE_CENTS.coupleDuo)} />
              {[3, 4, 5].map((n) => (
                <Row key={n} label={p.eyes(n)} value={eur(centsForEyes(n))} />
              ))}
            </div>
            <p className="mt-1 text-xs leading-relaxed text-zinc-400">{p.perEye(eur(PRICE_CENTS.extraEye), MAX_EYES)}</p>
          </Card>
        </div>

        <p className="mt-6 text-sm leading-relaxed text-zinc-400">{p.footnote}</p>
      </div>
    </section>
  );
}
