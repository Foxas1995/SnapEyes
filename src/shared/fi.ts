// Finnish number agreement and formats, shared by every Finnish copy file (/try, /order, and whichever landing or
// legal file wants them). English and German need no plural classes, Finnish needs two forms. Prices are written by
// src/shared/markets.ts money() ("24,97 €").
//
// A Finnish noun after a number is in the singular, in one of two forms (when the phrase is a subject, a label or
// the object of an imperative):
//   one   1 only                                    1 silmä, 1 kuva, 1 otos        (nominative)
//   many  0, 2, 3 ... 21, 101 ... (everything else)  2 silmää, 21 kuvaa, 5 otosta   (partitive)
// The object of a statement takes the genitive after 1 ("tarkistimme 1 kuvan") and the same partitive after any other
// number ("tarkistimme 3 kuvaa"): the "Acc" helpers below. In the other cases one form serves every number
// ("2 silmälle", "1 silmälle", "48 tunnin kuluessa"), so the copy writes those by hand.
// Numbers come from the page (eyes 1-8, shots 1-5, photos up to 8) but every helper handles any whole number.
// Eyes are numbered "silmä 3" and shots "otos 2", as English does.

export function fiForm(n: number, one: string, many: string): string {
  return Math.abs(Math.trunc(n)) === 1 ? one : many;
}

/** "1 silmä", "2 silmää", "5 silmää" (a subject, a label, the object of an imperative) */
export const silmat = (n: number) => `${n} ${fiForm(n, 'silmä', 'silmää')}`;
/** the noun alone */
export const silmatWord = (n: number) => fiForm(n, 'silmä', 'silmää');
/** "1 kuva", "3 kuvaa" (nominative) */
export const kuvat = (n: number) => `${n} ${fiForm(n, 'kuva', 'kuvaa')}`;
/** "1 kuvan", "3 kuvaa" (the object of a statement: "tarkistimme ...") */
export const kuvatAcc = (n: number) => `${n} ${fiForm(n, 'kuvan', 'kuvaa')}`;
/** "1 otos", "3 otosta" (nominative) */
export const otokset = (n: number) => `${n} ${fiForm(n, 'otos', 'otosta')}`;
/** "1 otoksen", "3 otosta" (the object of a statement: "voit ottaa vielä ...") */
export const otoksetAcc = (n: number) => `${n} ${fiForm(n, 'otoksen', 'otosta')}`;
/** the noun alone, as an object */
export const otoksetAccWord = (n: number) => fiForm(n, 'otoksen', 'otosta');
/** "1 kirjain", "3 kirjainta" */
export const kirjaimet = (n: number) => `${n} ${fiForm(n, 'kirjain', 'kirjainta')}`;
/** "1 merkki", "3 merkkiä" */
export const merkit = (n: number) => `${n} ${fiForm(n, 'merkki', 'merkkiä')}`;

/** A whole or one-decimal number as Finnish writes it: decimal comma, thousands with a non-breaking space
 *  ("3,7", "12 345,6"). Written by hand so that every runtime prints the same (Intl fi-FI uses a real minus sign). */
function groupFi(intPart: string): string {
  return intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

/** One decimal with a decimal comma: "3,7". */
export const dec1Fi = (v: number) => {
  const s = Math.abs(v).toFixed(1);
  const [i, f] = s.split('.');
  return `${v < 0 ? '-' : ''}${groupFi(i ?? '0')},${f ?? '0'}`;
};

/** A day as Finns write it: "28.10.2026" (day.month.year without leading zeros and without a final dot; Intl fi-FI numeric). */
export const dateFi = (unixSeconds: number) =>
  new Intl.DateTimeFormat('fi-FI', { year: 'numeric', month: 'numeric', day: 'numeric' }).format(new Date(unixSeconds * 1000));

/** A moment with its time zone: "28.10.2026 klo 14.05 (UTC+2)". Finnish writes the time with a full stop and "klo"
 *  before it, the hour without a leading zero; Intl fi-FI alone prints "28.10.2026 klo 14.05 UTC+2" or leaves "klo"
 *  out, depending on the runtime, so the parts are put together here. */
export function whenFi(unixSeconds: number): string {
  const at = new Date(unixSeconds * 1000);
  const parts = new Intl.DateTimeFormat('fi-FI', {
    year: 'numeric', month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZoneName: 'short',
  }).formatToParts(at);
  const get = (t: Intl.DateTimeFormatPartTypes) => parts.find((p) => p.type === t)?.value ?? '';
  const zone = get('timeZoneName');
  const hour = String(Number(get('hour')));
  return `${dateFi(unixSeconds)} klo ${hour}.${get('minute')}${zone ? ` (${zone})` : ''}`;
}

/** Megabytes with one decimal: "4,2". */
export const mbFi = (bytes: number) => dec1Fi(bytes / 1_000_000);
