// Lithuanian number agreement and formats, shared by every Lithuanian copy file (landing, /try, /order, the legal
// pages). English and German need no plural classes, Lithuanian needs three. Prices are written by
// src/shared/markets.ts money() ("19,97 €").
//
// A Lithuanian noun after a number takes one of three forms:
//   one   1, 21, 31, 101 ... (n % 10 = 1, but not 11)          1 akis, 21 akis
//   few   2-9, 22-29 ... (n % 10 = 2..9, but not 12-19)          2 akys, 8 akys
//   many  0, 10-20, 30, 40 ... (n % 10 = 0, or 11-19)            10 akių, 11 akių
// Numbers come from the page (eyes 1-8, shots 1-5, photos up to 8) but every helper handles any whole number.

export function ltForm(n: number, one: string, few: string, many: string): string {
  const a = Math.abs(Math.trunc(n));
  const d = a % 10;
  const h = a % 100;
  if (d === 1 && h !== 11) return one;
  if (d >= 2 && d <= 9 && (h < 12 || h > 19)) return few;
  return many;
}

/** "1 akis", "2 akys", "10 akių" (nominative: the subject of a sentence, a label). */
export const akys = (n: number) => `${n} ${ltForm(n, 'akis', 'akys', 'akių')}`;
/** the noun alone, nominative */
export const akysWord = (n: number) => ltForm(n, 'akis', 'akys', 'akių');
/** the noun alone, genitive ("iki 8 akių", "iki 1 akies") */
export const akiuWord = (n: number) => ltForm(n, 'akies', 'akių', 'akių');
/** "1 nuotrauką", "3 nuotraukas", "10 nuotraukų" (accusative: "palyginome ...") */
export const nuotraukasAcc = (n: number) => `${n} ${ltForm(n, 'nuotrauką', 'nuotraukas', 'nuotraukų')}`;
/** "1 kadras", "5 kadrai", "10 kadrų" (nominative) */
export const kadrai = (n: number) => `${n} ${ltForm(n, 'kadras', 'kadrai', 'kadrų')}`;
/** the noun alone, genitive ("iki 1 kadro", "iki 4 kadrų") */
export const kadruWord = (n: number) => ltForm(n, 'kadro', 'kadrų', 'kadrų');
/** "1 valandą", "48 valandas", "12 valandų" (accusative: "per ... valandas") */
export const valandasAcc = (n: number) => `${n} ${ltForm(n, 'valandą', 'valandas', 'valandų')}`;

/** One decimal with a decimal comma: "3,7". */
export const dec1Lt = (v: number) =>
  new Intl.NumberFormat('lt-LT', { minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(v);

/** A day in words: "2026 m. spalio 13 d." (Intl lt-LT, month in the genitive as Lithuanian writes dates). */
export const dateLt = (unixSeconds: number) =>
  new Intl.DateTimeFormat('lt-LT', { year: 'numeric', month: 'long', day: 'numeric' }).format(new Date(unixSeconds * 1000));

/** A moment with its time zone: "2026 m. rugsėjo 29 d. 13:15 (GMT+3)". Intl lt-LT alone prints "13:15; GMT+3" with a
 *  semicolon, which reads like a typo in a sentence, so the parts are put together here. */
export function whenLt(unixSeconds: number): string {
  const parts = new Intl.DateTimeFormat('lt-LT', {
    year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZoneName: 'short',
  }).formatToParts(new Date(unixSeconds * 1000));
  const get = (t: Intl.DateTimeFormatPartTypes) => parts.find((p) => p.type === t)?.value ?? '';
  const day = new Intl.DateTimeFormat('lt-LT', { year: 'numeric', month: 'long', day: 'numeric' }).format(new Date(unixSeconds * 1000));
  const zone = get('timeZoneName');
  return `${day} ${get('hour')}:${get('minute')}${zone ? ` (${zone})` : ''}`;
}

/** Megabytes with one decimal: "4,2". */
export const mbLt = (bytes: number) => dec1Lt(bytes / 1_000_000);
