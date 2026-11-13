// Latvian number agreement and formats, shared by every Latvian copy file (/try, /order, and whichever landing or
// legal file wants them). English and German need no plural classes, Latvian needs three. Prices are written by
// src/shared/markets.ts money() ("24,97 €").
//
// A Latvian noun after a number takes one of three forms:
//   one   1, 21, 31, 101 ... (n % 10 = 1, but not 11)           1 acs, 21 fotogrāfija, 1 kadrs       (singular)
//   few   2-9, 22-29 ... (n % 10 = 2..9, but not 12-19)         2 acis, 3 fotogrāfijas, 4 kadri      (plural)
//   many  0, 10-20, 30, 40 ... (n % 10 = 0, or 11-19)           10 acu, 11 fotogrāfiju, 12 kadru     (genitive plural)
// The singular and the plural are declined by the sentence (nominative "1 acs", accusative "1 aci", dative "1 acij"),
// so a noun has one helper per case the copy needs; the genitive plural after 0, 10-20 and the round tens stays as it
// is in the nominative and the accusative. Numbers come from the page (eyes 1-8, shots 1-5, photos up to 8) but every
// helper handles any whole number. Eyes are numbered with an ordinal ("3. acs"), as Latvian reads "the third eye".

export function lvForm(n: number, one: string, few: string, many: string): string {
  const a = Math.abs(Math.trunc(n));
  const d = a % 10;
  const h = a % 100;
  if (d === 1 && h !== 11) return one;
  if (d >= 2 && d <= 9 && (h < 12 || h > 19)) return few;
  return many;
}

/** "1 acs", "2 acis", "10 acu" (nominative: a label, the subject of a sentence). */
export const acis = (n: number) => `${n} ${lvForm(n, 'acs', 'acis', 'acu')}`;
/** the noun alone, nominative */
export const acisWord = (n: number) => lvForm(n, 'acs', 'acis', 'acu');
/** "1 acij", "2 acīm", "10 acīm" (dative: "vieta vēl 2 acīm", "līdz 8 acīm", "nav pieejams 3 acīm") */
export const acisDat = (n: number) => `${n} ${lvForm(n, 'acij', 'acīm', 'acīm')}`;
/** "1 fotogrāfija", "3 fotogrāfijas", "10 fotogrāfiju" (nominative) */
export const fotografijas = (n: number) => `${n} ${lvForm(n, 'fotogrāfija', 'fotogrāfijas', 'fotogrāfiju')}`;
/** "1 fotogrāfiju", "3 fotogrāfijas", "10 fotogrāfiju" (accusative: "pārbaudījām ...") */
export const fotografijasAcc = (n: number) => `${n} ${lvForm(n, 'fotogrāfiju', 'fotogrāfijas', 'fotogrāfiju')}`;
/** "1 kadrs", "3 kadri", "10 kadru" (nominative) */
export const kadri = (n: number) => `${n} ${lvForm(n, 'kadrs', 'kadri', 'kadru')}`;
/** "1 kadru", "3 kadrus", "10 kadru" (accusative: "uzņemiet vēl ...") */
export const kadriAcc = (n: number) => `${n} ${lvForm(n, 'kadru', 'kadrus', 'kadru')}`;
/** the noun alone, accusative */
export const kadriAccWord = (n: number) => lvForm(n, 'kadru', 'kadrus', 'kadru');
/** "1 burts", "3 burti", "10 burtu" */
export const burti = (n: number) => `${n} ${lvForm(n, 'burts', 'burti', 'burtu')}`;
/** "1 rakstzīme", "3 rakstzīmes", "10 rakstzīmju" */
export const zimes = (n: number) => `${n} ${lvForm(n, 'rakstzīme', 'rakstzīmes', 'rakstzīmju')}`;

/** A whole or one-decimal number as Latvian writes it: decimal comma, thousands with a non-breaking space
 *  ("3,7", "12 345,6"). Written by hand, so every browser prints the same. */
function groupLv(intPart: string): string {
  return intPart.replace(/\B(?=(\d{3})+(?!\d))/g, '\u00a0');
}

/** One decimal with a decimal comma: "3,7". */
export const dec1Lv = (v: number) => {
  const s = Math.abs(v).toFixed(1);
  const [i, f] = s.split('.');
  return `${v < 0 ? '-' : ''}${groupLv(i ?? '0')},${f ?? '0'}`;
};

/** The parts of a moment in the visitor's own time zone, as Intl lv-LV gives them (two-digit day and month). */
function partsLv(unixSeconds: number): (t: Intl.DateTimeFormatPartTypes) => string {
  const parts = new Intl.DateTimeFormat('lv-LV', {
    year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', timeZoneName: 'short',
  }).formatToParts(new Date(unixSeconds * 1000));
  return (t) => parts.find((p) => p.type === t)?.value ?? '';
}

/** A day as Latvians write it in numbers: "28.10.2026." (day.month.year. with a final dot, the year being an ordinal).
 *  Put together from the parts: Intl lv-LV alone prints "5.01.2026." for a one-digit day. */
export const dateLv = (unixSeconds: number) => {
  const get = partsLv(unixSeconds);
  return `${get('day')}.${get('month')}.${get('year')}.`;
};

/** A moment with its time zone: "28.10.2026. plkst. 14:05 (EET)". Intl lv-LV alone prints "28.10.2026. 14:05 EET",
 *  which runs the date into the time, so the parts are put together here. */
export function whenLv(unixSeconds: number): string {
  const get = partsLv(unixSeconds);
  const zone = get('timeZoneName');
  return `${dateLv(unixSeconds)} plkst. ${get('hour')}:${get('minute')}${zone ? ` (${zone})` : ''}`;
}

/** Megabytes with one decimal: "4,2". */
export const mbLv = (bytes: number) => dec1Lv(bytes / 1_000_000);
