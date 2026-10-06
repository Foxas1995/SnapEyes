// What the Stiliai page asks the server for, and which answers it may use (no React: the page test drives this with a fake `call` whose answers it holds back and releases in any order).
//
// Two rules live here because both were once broken:
//  1. A SLOW ANSWER TO AN OLDER QUESTION MUST NOT OVERWRITE A NEWER ONE. Every request takes a number when it is sent; its answer is used only while that number is still the newest of its
//     kind (the numbers, the opening basis, the catalogue). The owner who clicks "7 d." and then "90 d." must never see 7 day numbers under the pressed 90 d. button.
//  2. THE OPENING CRITERION BESIDE A SWITCH HAS ITS OWN, FIXED BASIS: the whole market over the last 30 days (stylesView OPENING_DAYS), which is what the audit entry of a change keeps
//     (api/_lib/ops.py _flip_numbers). It is not the period or the filter picked for the numbers below. When the numbers happen to be asked for exactly that basis, the one answer serves
//     both; otherwise the basis is a second question of its own.
import type { Call } from './AdminApp';
import type { FunnelLine, Reply, StyleAuditEntry, StyleCatalogue, StylesStats } from './api';
import { filterBody, isOpeningBasis, OPENING_DAYS } from './stylesView';

/** The numbers behind the opening line beside a switch. null: not read yet; 'failed': the reading failed and no older one is kept. */
export type OpeningBasis = { opening: Record<string, FunnelLine>; partial: boolean } | 'failed' | null;
export type ProblemKey = 'cat' | 'stats' | 'audit' | 'basis';

/** Where the answers go: the page's state setters (the page test passes recorders). `problem` gets a failed reply, or null for "no problem now". */
export interface LoadSinks {
  cat: (c: StyleCatalogue) => void;
  stats: (s: StylesStats) => void;
  basis: (update: (cur: OpeningBasis) => OpeningBasis) => void;
  audit: (entries: StyleAuditEntry[]) => void;
  busy: (b: boolean) => void;
  problem: (key: ProblemKey, r: Reply<unknown> | null) => void;
}

const isGood = (r: Reply<unknown>): boolean => !!(r.ok && r.data);

export function createStylesLoader(call: Call, out: LoadSinks) {
  let statsSeq = 0;
  let basisSeq = 0;
  let catSeq = 0;

  const statsCall = (days: number, filter: string) => call<StylesStats>('styles_stats', { days, ...filterBody(filter) }, 90_000);

  /** The answer of the numbers' request number `mine`; nothing is shown or said when a newer question has been asked since. */
  const putStats = (mine: number, r: Reply<StylesStats>): void => {
    if (mine !== statsSeq) return;
    if (isGood(r) && r.data) out.stats(r.data);
    out.problem('stats', isGood(r) ? null : r);
    out.busy(false);
  };

  /** The answer of the opening basis' request number `mine`. A failed reading keeps an older good one (and says so); with none, the line says it could not be read. */
  const putBasis = (mine: number, r: Reply<StylesStats>): void => {
    if (mine !== basisSeq) return;
    const d = r.data;
    out.basis((cur) => (isGood(r) && d ? { opening: d.opening, partial: d.partial } : cur && cur !== 'failed' ? cur : 'failed'));
    out.problem('basis', isGood(r) ? null : r);
  };

  /** Everything, for the period and filter given (the first load, and the Refresh button). */
  const loadAll = async (days: number, filter: string): Promise<void> => {
    out.busy(true);
    const mineStats = ++statsSeq, mineBasis = ++basisSeq, mineCat = catSeq;
    const own = isOpeningBasis(days, filter);
    const [c, s, a, b] = await Promise.all([
      call<StyleCatalogue>('styles_catalogue'), statsCall(days, filter), call<{ entries: StyleAuditEntry[] }>('styles_audit', { limit: 60 }),
      own ? Promise.resolve(null) : statsCall(OPENING_DAYS, ''),
    ]);
    if (mineCat === catSeq) {                          // a change the owner made while this was on its way is newer than the catalogue it brought
      if (isGood(c) && c.data) out.cat(c.data);
      out.problem('cat', isGood(c) ? null : c);
    }
    if (isGood(a) && a.data) out.audit(a.data.entries);
    out.problem('audit', isGood(a) ? null : a);
    putBasis(mineBasis, b || s);
    putStats(mineStats, s);
  };

  /** The numbers only (a period or filter was picked). Asked for exactly the opening basis, the answer also becomes the basis; asked for anything else, the basis is left alone. */
  const loadStats = async (days: number, filter: string): Promise<void> => {
    const mine = ++statsSeq;
    const mineBasis = isOpeningBasis(days, filter) ? ++basisSeq : 0;
    out.busy(true);
    const r = await statsCall(days, filter);
    if (mineBasis) putBasis(mineBasis, r);
    putStats(mine, r);
  };

  /** The owner changed the switch: a catalogue read that began before it is older than what the page holds now. */
  const changed = (): void => { catSeq += 1; };

  return { loadAll, loadStats, changed };
}
