// Croatian number agreement and formats, shared by every Croatian copy file (/try, /order, and whichever landing or
// legal file wants them). English and German need no plural classes, Croatian needs three. Prices are written by
// src/shared/markets.ts money() ("24,97 €").
//
// A Croatian noun after a number takes one of three forms (nominative and accusative; the number governs the noun):
//   one   1, 21, 31, 101 ... (n % 10 = 1, but not 11)           1 oko, 21 fotografija, 1 snimka
//   few   2-4, 22-24 ... (n % 10 = 2..4, but not 12-14)          2 oka, 3 fotografije, 4 snimke
//   many  0, 5-20, 25-30 ... (everything else)                   5 očiju, 11 fotografija, 12 snimaka
// Numbers come from the page (eyes 1-8, shots 1-5, photos up to 8) but every helper handles any whole number.
// Eyes are numbered with an ordinal ("3. oko"), never "oko 3": "oko" is also the word for "about".

export function hrForm(n: number, one: string, few: string, many: string): string {
  const a = Math.abs(Math.trunc(n));
  const d = a % 10;
  const h = a % 100;
  if (d === 1 && h !== 11) return one;
  if (d >= 2 && d <= 4 && (h < 12 || h > 14)) return few;
  return many;
}

/** "1 oko", "2 oka", "5 očiju" (nominative and accusative are the same: "za još 2 oka"). */
export const oci = (n: number) => `${n} ${hrForm(n, 'oko', 'oka', 'očiju')}`;
/** the noun alone */
export const ociWord = (n: number) => hrForm(n, 'oko', 'oka', 'očiju');
/** "1 fotografija", "3 fotografije", "5 fotografija" (nominative) */
export const fotografije = (n: number) => `${n} ${hrForm(n, 'fotografija', 'fotografije', 'fotografija')}`;
/** "1 fotografiju", "3 fotografije", "5 fotografija" (accusative: "provjerili smo ...") */
export const fotografijeAcc = (n: number) => `${n} ${hrForm(n, 'fotografiju', 'fotografije', 'fotografija')}`;
/** "1 snimka", "3 snimke", "5 snimaka" (nominative) */
export const snimke = (n: number) => `${n} ${hrForm(n, 'snimka', 'snimke', 'snimaka')}`;
/** "1 snimku", "3 snimke", "5 snimaka" (accusative: "snimite još ...") */
export const snimkeAcc = (n: number) => `${n} ${hrForm(n, 'snimku', 'snimke', 'snimaka')}`;
/** the noun alone, accusative */
export const snimkeAccWord = (n: number) => hrForm(n, 'snimku', 'snimke', 'snimaka');
/** "1 slovo", "3 slova", "5 slova" */
export const slova = (n: number) => `${n} ${hrForm(n, 'slovo', 'slova', 'slova')}`;
/** "1 znak", "3 znaka", "5 znakova" */
export const znakova = (n: number) => `${n} ${hrForm(n, 'znak', 'znaka', 'znakova')}`;

/** A whole or one-decimal number as Croatian writes it: decimal comma, thousands with a non-breaking space
 *  ("3,7", "12 345,6"). Intl hr-HR groups thousands with a dot, which the site's Croatian style does not use. */
function groupHr(intPart: string): string {
  return intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

/** One decimal with a decimal comma: "3,7". */
export const dec1Hr = (v: number) => {
  const s = Math.abs(v).toFixed(1);
  const [i, f] = s.split('.');
  return `${v < 0 ? '-' : ''}${groupHr(i ?? '0')},${f ?? '0'}`;
};

/** A day as Croatians write it: "28. 10. 2026." (day. month. year. with a final dot; Intl hr-HR numeric). */
export const dateHr = (unixSeconds: number) =>
  new Intl.DateTimeFormat('hr-HR', { year: 'numeric', month: 'numeric', day: 'numeric' }).format(new Date(unixSeconds * 1000));

/** A moment with its time zone: "28. 10. 2026. u 14:05 (CET)". Intl hr-HR alone prints "28. 10. 2026. 14:05 CET",
 *  which runs the date into the time, so the parts are put together here. */
export function whenHr(unixSeconds: number): string {
  const at = new Date(unixSeconds * 1000);
  const parts = new Intl.DateTimeFormat('hr-HR', {
    year: 'numeric', month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZoneName: 'short',
  }).formatToParts(at);
  const get = (t: Intl.DateTimeFormatPartTypes) => parts.find((p) => p.type === t)?.value ?? '';
  const zone = get('timeZoneName');
  return `${dateHr(unixSeconds)} u ${get('hour')}:${get('minute')}${zone ? ` (${zone})` : ''}`;
}

/** Megabytes with one decimal: "4,2". */
export const mbHr = (bytes: number) => dec1Hr(bytes / 1_000_000);
