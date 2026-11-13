// Estonian number agreement and formats, shared by every Estonian copy file (/try, /order, and whichever landing or
// legal file wants them). English and German need no plural classes; Estonian needs two forms, but not the English two.
// Prices are written by src/shared/markets.ts money() ("24,97 €").
//
// An Estonian noun after a number takes one of two forms:
//   one    1 only                                     1 silm, 1 foto, 1 võte (nominative singular)
//   other  0, 2, 3 ... 21, 101 (every other number)   2 silma, 21 fotot, 5 võtet (partitive singular)
// (21 and 101 take the partitive too: no Slavic or Baltic "ends in 1" rule.) When the whole phrase stands in another case
// the noun follows it in the singular ("2 silma jaoks", "neist 5 võttest"): the copy files write those few forms inline.
// Numbers come from the page (eyes 1-8, shots 1-5, photos up to 8) but every helper handles any whole number.
// An eye is numbered after the noun, as in English ("silm 3").

export function etForm(n: number, one: string, other: string): string {
  return Math.abs(Math.trunc(n)) === 1 ? one : other;
}

/** "1 silm", "2 silma", "8 silma" (the subject of a sentence, a label, an object after a number) */
export const silmad = (n: number) => `${n} ${etForm(n, 'silm', 'silma')}`;
/** the noun alone */
export const silmWord = (n: number) => etForm(n, 'silm', 'silma');
/** "1 silma", "2 silma": the genitive phrase, before a postposition or a noun ("3 silma jaoks", "2 silma hind") */
export const silmaGen = (n: number) => `${n} silma`;
/** "1 foto", "3 fotot" */
export const fotod = (n: number) => `${n} ${etForm(n, 'foto', 'fotot')}`;
/** "1 võte", "3 võtet" (nominative and partitive; also the object of an imperative: "tee veel 1 võte") */
export const votted = (n: number) => `${n} ${etForm(n, 'võte', 'võtet')}`;
/** the noun alone */
export const voteWord = (n: number) => etForm(n, 'võte', 'võtet');
/** "1 võttest", "5 võttest": the elative phrase ("ühtki neist 5 võttest"); the noun stays singular */
export const vottedEla = (n: number) => `${n} võttest`;
/** "1 täht", "3 tähte" */
export const tahed = (n: number) => `${n} ${etForm(n, 'täht', 'tähte')}`;
/** "1 märk", "3 märki" */
export const margid = (n: number) => `${n} ${etForm(n, 'märk', 'märki')}`;

/** A whole or one-decimal number as Estonian writes it: decimal comma, thousands with a non-breaking space
 *  ("3,7", "12 345,6"). Written by hand so that it does not depend on the Intl data of the browser. */
function groupEt(intPart: string): string {
  return intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

/** One decimal with a decimal comma: "3,7". */
export const dec1Et = (v: number) => {
  const s = Math.abs(v).toFixed(1);
  const [i, f] = s.split('.');
  return `${v < 0 ? '-' : ''}${groupEt(i ?? '0')},${f ?? '0'}`;
};

/** A day as Estonians write it: "28.10.2026" (day.month.year, two digits each, no spaces, no final dot). */
export const dateEt = (unixSeconds: number) =>
  new Intl.DateTimeFormat('et-EE', { year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(unixSeconds * 1000));

/** A moment with its time zone: "28.10.2026 kell 14:05 (EET)". Intl et-EE alone prints "28.10.2026, 14:05 EET",
 *  which reads like a list in a sentence, so the parts are put together here. */
export function whenEt(unixSeconds: number): string {
  const at = new Date(unixSeconds * 1000);
  const parts = new Intl.DateTimeFormat('et-EE', {
    year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', timeZoneName: 'short',
  }).formatToParts(at);
  const get = (t: Intl.DateTimeFormatPartTypes) => parts.find((p) => p.type === t)?.value ?? '';
  const zone = get('timeZoneName');
  return `${dateEt(unixSeconds)} kell ${get('hour')}:${get('minute')}${zone ? ` (${zone})` : ''}`;
}

/** Megabytes with one decimal: "4,2". */
export const mbEt = (bytes: number) => dec1Et(bytes / 1_000_000);
