// The admin panel's shared pieces: cards, buttons, state chips, the confirmation dialog, a JSON view. Text only
// through React text nodes (escaped); links and images only through safeUrl.
import { useEffect, useRef, useState } from 'react';
import type React from 'react';
import { safeUrl, trimJson } from './format';

export const CARD = 'bg-[#0b0e17] border border-white/10 rounded-2xl p-4 sm:p-5 min-w-0';
export const BTN = 'min-h-[40px] px-3.5 py-2 rounded-xl bg-white/5 border border-white/10 text-sm font-semibold inline-flex items-center justify-center gap-2 text-center hover:bg-white/10 disabled:opacity-40 disabled:cursor-not-allowed';
export const GOLD = 'min-h-[40px] px-4 py-2 rounded-xl bg-gradient-to-r from-[#f5c542] to-[#d4af37] text-black text-sm font-bold inline-flex items-center justify-center gap-2 text-center disabled:opacity-40 disabled:cursor-not-allowed';
export const DANGER = 'min-h-[40px] px-3.5 py-2 rounded-xl bg-red-500/15 border border-red-400/40 text-red-200 text-sm font-semibold inline-flex items-center justify-center gap-2 text-center hover:bg-red-500/25 disabled:opacity-40 disabled:cursor-not-allowed';
export const INPUT = 'w-full min-h-[40px] px-3 py-2 rounded-xl bg-black/40 border border-white/15 text-sm text-white placeholder:text-white/35 focus:outline-none focus:border-[#f5c542]/70';
export const MUTED = 'text-white/55';

const TONES = {
  good: 'bg-emerald-400/15 text-emerald-200 border-emerald-300/30',
  warn: 'bg-amber-400/15 text-amber-100 border-amber-300/35',
  bad: 'bg-red-500/15 text-red-200 border-red-400/35',
  info: 'bg-sky-400/15 text-sky-100 border-sky-300/30',
  muted: 'bg-white/5 text-white/70 border-white/15',
} as const;
export type Tone = keyof typeof TONES;

export const Chip: React.FC<{ tone?: Tone; children: React.ReactNode }> = ({ tone = 'muted', children }) => (
  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-semibold whitespace-nowrap ${TONES[tone]}`}>{children}</span>
);

/** A chip whose words may be long (a check's name with its numbers): it wraps and stays inside its box on a phone. */
export const WrapChip: React.FC<{ tone?: Tone; children: React.ReactNode }> = ({ tone = 'muted', children }) => (
  <span className={`inline-flex items-start gap-1 px-2 py-0.5 rounded-xl border text-xs font-semibold text-left break-words max-w-full ${TONES[tone]}`}>{children}</span>
);

/** A yes/no flag: a dot plus the word, never colour alone. */
export const Flag: React.FC<{ on: boolean | undefined | null; label: string; bad?: boolean }> = ({ on, label, bad = true }) => (
  <span className="inline-flex items-center gap-2 text-sm min-w-0">
    <span aria-hidden className={`w-2.5 h-2.5 rounded-full shrink-0 ${on ? 'bg-emerald-400' : bad ? 'bg-red-400' : 'bg-white/30'}`} />
    <span className="min-w-0 break-words">{label}: <b>{on === undefined || on === null ? 'nežinoma' : on ? 'taip' : 'ne'}</b></span>
  </span>
);

export const Spinner: React.FC = () => (
  <span aria-hidden className="inline-block w-4 h-4 shrink-0 border-2 border-[#f5c542]/30 border-t-[#f5c542] rounded-full animate-spin" />
);

export const H2: React.FC<{ children: React.ReactNode; right?: React.ReactNode }> = ({ children, right }) => (
  <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
    <h2 className="text-base sm:text-lg font-bold tracking-wide text-white" style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}>{children}</h2>
    {right}
  </div>
);

export const Notice: React.FC<{ tone?: Tone; children: React.ReactNode }> = ({ tone = 'bad', children }) => (
  <div role={tone === 'bad' ? 'alert' : 'status'} className={`rounded-xl border px-3 py-2 text-sm break-words ${TONES[tone]}`}>{children}</div>
);

/** A short statement in a tone, in the page's own flow (a green or a red line: the words say the same as the colour). */
export const ToneLine: React.FC<{ tone?: Tone; children: React.ReactNode }> = ({ tone = 'muted', children }) => (
  <p className={`rounded-lg border px-2.5 py-1.5 text-xs break-words ${TONES[tone]}`}>{children}</p>
);

/** A small table: a table on a wide screen (it scrolls inside itself if it must), one block per row on a phone, where the numbers of a table of many columns would be hidden
 *  behind sideways scrolling. The page itself never scrolls sideways. */
export const Tbl: React.FC<{ head: string[]; rows: React.ReactNode[][]; label: string; empty?: string }> = ({ head, rows, label, empty = 'Nėra duomenų.' }) => {
  if (!rows.length) return <p className="text-xs text-white/55">{empty}</p>;
  return (
    <>
      <ul className="md:hidden flex flex-col gap-2" aria-label={label}>
        {rows.map((r, i) => (
          <li key={i}>
            <dl className="rounded-lg border border-white/10 bg-black/20 p-2.5 grid grid-cols-[minmax(0,8.5rem)_minmax(0,1fr)] gap-x-3 gap-y-1 text-xs">
              {head.map((h, j) => (
                <div key={`${j}-${h}`} className="contents">
                  <dt className="text-white/55">{h}</dt>
                  <dd className="min-w-0 break-words">{r[j]}</dd>
                </div>
              ))}
            </dl>
          </li>
        ))}
      </ul>
      <div className="hidden md:block overflow-x-auto" role="region" aria-label={label} tabIndex={0}>
        <table className="w-full text-xs text-left border-collapse">
          <caption className="sr-only">{label}</caption>
          <thead className="text-white/55">
            <tr>{head.map((h, j) => <th key={`${j}-${h}`} scope="col" className="py-1 pr-3 font-semibold whitespace-nowrap">{h}</th>)}</tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} className="border-t border-white/5 align-top">
                {r.map((c, j) => <td key={j} className="py-1.5 pr-3 break-words">{c}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
};

/** An action's result, pinned to the bottom of the screen: the button that started it may be far down a long page,
 *  so a notice at the top would not be seen. Opaque (it lies over the page), scrolls inside itself when long. */
export const Toast: React.FC<{ tone?: Tone; onClose?: () => void; children: React.ReactNode }> = ({ tone = 'bad', onClose, children }) => (
  <div className="fixed inset-x-0 bottom-0 z-[45] p-3 pointer-events-none">
    <div className="pointer-events-auto mx-auto w-full max-w-3xl rounded-xl bg-[#0b0e17] shadow-2xl shadow-black/70">
      <div role={tone === 'bad' ? 'alert' : 'status'} className={`rounded-xl border px-3 py-2 text-sm break-words max-h-[45vh] overflow-y-auto flex items-start gap-2 ${TONES[tone]}`}>
        <div className="min-w-0 flex-1">{children}</div>
        {onClose && (
          <button type="button" onClick={onClose} aria-label="Uždaryti pranešimą"
            className="shrink-0 -mr-1 w-8 h-8 rounded-lg inline-flex items-center justify-center text-lg leading-none text-white/70 hover:bg-white/10">×</button>
        )}
      </div>
    </div>
  </div>
);

/** A link shown as text to copy, never as a clickable link (opening it would start something). */
export const CopyField: React.FC<{ value: string; label: string }> = ({ value, label }) => {
  const [done, setDone] = useState(false);
  const field = useRef<HTMLInputElement>(null);
  const copy = async () => {
    let ok = false;
    try { await navigator.clipboard.writeText(value); ok = true; } catch { /* no clipboard here: select the text */ }
    if (!ok) { field.current?.focus(); field.current?.select(); }
    setDone(ok);
  };
  return (
    <div className="flex gap-2 mt-1 min-w-0">
      <input ref={field} readOnly value={value} aria-label={label} spellCheck={false} onFocus={(e) => e.currentTarget.select()}
        className={`${INPUT} !min-h-[36px] min-w-0 text-xs font-mono`} />
      <button type="button" className={`${BTN} !min-h-[36px] shrink-0`} onClick={() => void copy()}>{done ? 'Nukopijuota' : 'Kopijuoti'}</button>
    </div>
  );
};

/** label: value lines that wrap at any width. */
export const Rows: React.FC<{ rows: [string, React.ReactNode][] }> = ({ rows }) => (
  <dl className="grid grid-cols-1 sm:grid-cols-[minmax(0,12rem)_minmax(0,1fr)] gap-x-4 gap-y-1 text-sm">
    {rows.map(([k, v], i) => (
      <div key={i} className="contents">
        <dt className={`${MUTED} pt-1 sm:pt-0`}>{k}</dt>
        <dd className="min-w-0 break-words">{v}</dd>
      </div>
    ))}
  </dl>
);

/** A folded JSON view (long base64 strings shortened). */
export const JsonView: React.FC<{ value: unknown; label?: string; open?: boolean }> = ({ value, label = 'JSON', open = false }) => (
  <details className="rounded-xl border border-white/10 bg-black/30 min-w-0" open={open}>
    <summary className="cursor-pointer select-none px-3 py-2 text-xs font-semibold text-white/70 break-all">{label}</summary>
    <pre className="px-3 pb-3 text-[11px] leading-snug text-white/80 whitespace-pre-wrap break-all overflow-x-auto max-h-[420px]">
      {JSON.stringify(trimJson(value), null, 2)}
    </pre>
  </details>
);

export const ExtLink: React.FC<{ href: unknown; children: React.ReactNode }> = ({ href, children }) => {
  const u = safeUrl(href);
  if (!u) return <span className={MUTED}>{children}</span>;
  return <a href={u} target="_blank" rel="noopener noreferrer" className="underline underline-offset-4 decoration-white/30 hover:text-white text-[#f5c542] break-all">{children}</a>;
};

/** A thumbnail of a signed image link (only http(s)); a 4K file is loaded only on request. */
export const Thumb: React.FC<{ src: unknown; alt: string; heavy?: boolean; size?: number }> = ({ src, alt, heavy = false, size = 140 }) => {
  const [show, setShow] = useState(!heavy);
  const u = safeUrl(src);
  if (!u) return null;
  return (
    <figure className="flex flex-col gap-1 min-w-0" style={{ width: size }}>
      {show ? (
        <a href={u} target="_blank" rel="noopener noreferrer">
          <img src={u} alt={alt} loading="lazy" width={size} height={size} className="rounded-lg border border-white/10 bg-black object-contain" style={{ width: size, height: size }} />
        </a>
      ) : (
        <button type="button" className={`${BTN} !min-h-0`} style={{ width: size, height: size }} onClick={() => setShow(true)}>Rodyti 4K</button>
      )}
      <figcaption className="text-[11px] text-white/60 break-words">{alt}</figcaption>
    </figure>
  );
};

export interface ConfirmSpec {
  title: string;
  text: string;
  confirmLabel: string;
  danger?: boolean;
  typeToConfirm?: string;           // the order number the owner must type
  option?: { label: string; value: boolean };
  run: (option: boolean) => Promise<void> | void;
}

/** The confirmation step every admin action goes through (a fresh dialog for every request). */
export const ConfirmDialog: React.FC<{ spec: ConfirmSpec | null; onClose: () => void }> = ({ spec, onClose }) =>
  spec ? <Confirm key={`${spec.title}|${spec.text}`} spec={spec} onClose={onClose} /> : null;

const Confirm: React.FC<{ spec: ConfirmSpec; onClose: () => void }> = ({ spec, onClose }) => {
  const [typed, setTyped] = useState('');
  const [opt, setOpt] = useState(spec.option?.value ?? false);
  const [busy, setBusy] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const t = setTimeout(() => box.current?.querySelector<HTMLElement>('input,button')?.focus(), 0);
    return () => clearTimeout(t);
  }, []);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape' && !busy) onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [busy, onClose]);
  const ok = !spec.typeToConfirm || typed.trim() === spec.typeToConfirm;
  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/70 p-3" role="dialog" aria-modal="true" aria-label={spec.title}>
      <div ref={box} className={`${CARD} w-full max-w-md flex flex-col gap-3`}>
        <h3 className="text-base font-bold" style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}>{spec.title}</h3>
        <p className="text-sm text-white/80 whitespace-pre-line break-words">{spec.text}</p>
        {spec.option && (
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={opt} onChange={(e) => setOpt(e.target.checked)} className="w-4 h-4 accent-[#f5c542]" />
            {spec.option.label}
          </label>
        )}
        {spec.typeToConfirm && (
          <label className="flex flex-col gap-1 text-sm">
            <span className={MUTED}>Patvirtinimui įrašyk užsakymo numerį: <b className="text-white break-all">{spec.typeToConfirm}</b></span>
            <input className={INPUT} value={typed} onChange={(e) => setTyped(e.target.value)} autoComplete="off" spellCheck={false} aria-label="Užsakymo numeris" />
          </label>
        )}
        <div className="flex flex-wrap gap-2 justify-end">
          <button type="button" className={BTN} onClick={onClose} disabled={busy}>Atšaukti</button>
          <button type="button" className={spec.danger ? DANGER : GOLD} disabled={!ok || busy}
            onClick={async () => { setBusy(true); try { await spec.run(opt); } finally { setBusy(false); onClose(); } }}>
            {busy && <Spinner />}{spec.confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
};
