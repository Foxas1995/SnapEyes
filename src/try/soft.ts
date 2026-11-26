// A soft photo the customer may go on with (the owner, 2026-11-26). api/analyze.py refuses a photo as too blurry exactly as before, and when that photo is
// otherwise usable (SOFT_BY: its circle locked, no other reason, the iris large enough, Detail at least SOFT_DETAIL) it also sends a second work ticket,
// soft_ticket, and quality.soft. The page counts the visit's blur refusals in memory (nothing is stored) and from the SECOND one on, when a refused photo
// of this visit carried a soft ticket, offers a quiet second button under the retake. It goes on with the best such photo (the highest Detail) as if it
// had been accepted as a weak one. No React and no DOM here.
import { num, type Analysis } from './shots';

/** The blur refusals a visit needs before the soft photo is offered: after the first one nothing new is shown. */
export const SOFT_AFTER = 2;

/** A refusal for blur (the reason the server gave, whatever line raised it). */
export const isBlur = (a: Analysis | null | undefined): boolean =>
  !!a?.ok && a.quality?.blocked === true && a.quality.block_reason === 'too_blurry';

/** A blur refusal the server says may be gone on with: it carries a soft ticket. */
export const isSoft = (a: Analysis | null | undefined): boolean =>
  isBlur(a) && a!.quality!.soft === true && typeof a!.soft_ticket === 'string' && !!a!.soft_ticket && !!a!.iris;

export interface SoftPick<F> { a: Analysis; file: F; at: number }

/** The best soft photo so far: a new one replaces the one held only when its Detail is higher. */
export function keepSoft<F>(cur: SoftPick<F> | null, a: Analysis, file: F, at: number): SoftPick<F> | null {
  if (!isSoft(a)) return cur;
  if (cur && (num(cur.a.quality?.detail) ?? -1) >= (num(a.quality?.detail) ?? -1)) return cur;
  return { a, file, at };
}

/** Whether the refusal screen offers the soft photo: from the second blur refusal of the visit on, with a soft photo whose ticket is still good. */
export const offerSoft = <F>(blurs: number, pick: SoftPick<F> | null, now: number, ttlMs: number): boolean =>
  blurs >= SOFT_AFTER && !!pick && now - pick.at < ttlMs;

/** The analysis the restoration is run with: the soft photo as an accepted weak one, its soft ticket the work ticket. The numbers stay as measured. */
export function softAnalysis(a: Analysis): Analysis {
  const q = a.quality!;
  return { ...a, ticket: a.soft_ticket, quality: { ...q, blocked: false, block_reason: null, verdict: 'weak', soft: true } };
}
