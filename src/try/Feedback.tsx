import React, { useEffect, useId, useState } from 'react';
import { T } from './copy';
import { CHIPS, TEXT_MAX, feedbackAsked, markAnswered, sendFeedback, wasAnswered, type Outcome, type Place } from '../shared/feedback';
import { LEGAL_LABELS, legalHref } from '../shared/legal';
import { currentMarket } from '../shared/markets';

/** The anonymous feedback box (api/_lib/feedback.py): six chips and, once one is chosen, an optional text of up to 300 characters and a Send button. It is quiet: a small card at the end of the
 *  screen, no pop-up, no focus taken, nothing sent until Send, and not shown at all until /api/health says the server keeps the answers (src/shared/feedback.ts), nor again in one visit once
 *  that place has been answered. The chips are native radio buttons (keyboard and screen reader work as in any form), the text a labelled field with its limit and a plain-words hint. There is
 *  no e-mail field and no name: the hint asks the visitor not to write any, and the server drops a text that holds contact details or a link. `ctx` is the style on screen (result) or the
 *  block reason (retake), a short code; `on` shows the box without waiting for the server (tests); `send` is the sender (tests). */
export const FeedbackBox: React.FC<{ where: Place; ctx?: string; eyes?: number; on?: boolean; send?: typeof sendFeedback }> = ({ where, ctx, eyes, on: forced, send = sendFeedback }) => {
  const F = T.feedback;
  const id = useId();
  const [on, setOn] = useState(forced === true);
  const [chip, setChip] = useState('');
  const [text, setText] = useState('');
  const [hp, setHp] = useState('');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<Outcome | ''>('');
  useEffect(() => {
    let alive = true;
    void feedbackAsked().then((v) => { if (alive && v) setOn(true); });
    return () => { alive = false; };
  }, []);
  if (!on || (wasAnswered(where) && !result)) return null;
  const done = result !== '' && result !== 'failed';

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chip || busy) return;
    setBusy(true); setResult('');
    const out = await send({ w: where, c: chip, ...(ctx ? { x: ctx } : {}), ...(eyes ? { eyes } : {}), t: text, hp }, T.lang, currentMarket());
    setBusy(false);
    if (out !== 'failed') markAnswered(where);
    setResult(out);
  };

  const message = result === 'dropped' ? F.textDropped : result === 'lost' ? F.textLost : F.thanks;
  return (
    <section aria-labelledby={`${id}-t`} data-testid={`feedback-${where}`} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-xs text-zinc-300">
      <h2 id={`${id}-t`} className="text-[10px] uppercase tracking-widest text-zinc-300">{F.title[where]}</h2>
      {done ? (
        <p role="status" data-testid="feedback-thanks" className="mt-2 text-[12px] text-zinc-200">{message}</p>
      ) : (
        <form onSubmit={(e) => void submit(e)} className="mt-1.5 flex flex-col gap-2" noValidate>
          <p className="text-[11px] text-zinc-400">{F.hint[where]}</p>
          <fieldset className="contents">
            <legend className="sr-only">{F.title[where]}</legend>
            <div className="flex flex-wrap gap-1.5">
              {CHIPS[where].map((c) => (
                <label key={c} className="relative">
                  <input type="radio" name={`${id}-chip`} value={c} checked={chip === c} onChange={() => setChip(c)} data-testid={`feedback-chip-${c}`} className="peer sr-only" />
                  <span className="inline-flex min-h-[44px] items-center rounded-full border border-white/15 bg-white/5 px-3 text-[12px] font-semibold text-zinc-200 peer-checked:border-gold peer-checked:bg-gold/10 peer-checked:text-gold peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-gold">
                    {(F.chips[where] as Record<string, string>)[c]}
                  </span>
                </label>
              ))}
            </div>
          </fieldset>
          {chip && (
            <>
              <label className="flex flex-col gap-1">
                <span className="text-[11px] text-zinc-300">{F.textLabel}</span>
                <textarea value={text} onChange={(e) => setText(e.target.value.slice(0, TEXT_MAX))} maxLength={TEXT_MAX} rows={3} aria-describedby={`${id}-h`} data-testid="feedback-text"
                  className="w-full rounded-xl border border-white/15 bg-black/40 px-3 py-2 text-[13px] text-zinc-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold" />
              </label>
              <p id={`${id}-h`} className="text-[11px] text-zinc-400">{F.textHint} <span aria-hidden="true">{F.count(text.length, TEXT_MAX)}</span></p>
              {/* the honeypot: a person never sees it, never reaches it with the keyboard and a screen reader skips it; a robot that fills every field gives itself away */}
              <input type="text" name="company_site" value={hp} onChange={(e) => setHp(e.target.value)} tabIndex={-1} autoComplete="off" aria-hidden="true" data-testid="feedback-hp"
                className="absolute left-[-9999px] h-0 w-0 opacity-0" />
              <div className="flex items-center gap-3">
                <button type="submit" disabled={busy} data-testid="feedback-send"
                  className="min-h-[44px] rounded-xl border border-white/15 bg-white/10 px-4 text-sm font-semibold text-zinc-100 disabled:opacity-60 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold">
                  {busy ? F.sending : F.send}
                </button>
                {result === 'failed' && <p role="alert" data-testid="feedback-failed" className="text-[11px] text-rose-200">{F.failed}</p>}
              </div>
            </>
          )}
        </form>
      )}
      <p className="mt-2 text-[10px] text-zinc-400">
        {F.privacy}{' '}
        <a href={legalHref('privacy', T.lang)} target="_blank" rel="noopener" className="underline underline-offset-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold rounded-sm">{LEGAL_LABELS[T.lang].privacy}</a>
      </p>
    </section>
  );
};
