// Lithuanian words and number formats of the admin panel. Every value shown comes through React text nodes, so a
// customer's name or title is always escaped; safeUrl keeps anything but an http(s) link out of href and src.

import type { Counts, Prices, Reply } from './api';
import { STYLE_NAMES } from '../shared/styles';

export function safeUrl(u: unknown): string | undefined {
  return typeof u === 'string' && /^https?:\/\//i.test(u) ? u : undefined;
}

const pad2 = (n: number) => String(n).padStart(2, '0');

/** 2026-09-29 14:05 (the browser's own time zone). */
export function fmtTime(t: number | null | undefined, seconds = false): string {
  if (typeof t !== 'number' || !Number.isFinite(t) || t <= 0) return '-';
  const d = new Date(t * 1000);
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())} ${pad2(d.getHours())}:${pad2(d.getMinutes())}` +
    (seconds ? `:${pad2(d.getSeconds())}` : '');
}

export function fmtDate(t: number | null | undefined): string {
  return fmtTime(t).slice(0, 10);
}

/** An amount in Stripe's smallest unit, in its currency, as the panel writes it (Lithuanian style): "39,97 €",
 *  "79,00 A$", "13 990 Ft" (forints whole: Stripe's HUF amount is the forint x 100). No currency named: euros (every
 *  order before markets existed). */
export function fmtMoney(cents: number | null | undefined, currency?: string | null): string {
  if (typeof cents !== 'number' || !Number.isFinite(cents)) return '-';
  const cur = (currency || 'eur').toLowerCase();
  if (cur === 'huf') return `${String(Math.round(cents / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, '\u00a0')}\u00a0Ft`;
  const sign = cur === 'aud' ? 'A$' : cur === 'eur' ? '€' : cur.toUpperCase();
  return `${(cents / 100).toFixed(2).replace('.', ',')} ${sign}`;
}

/** 39,97 € (fmtMoney in euros) */
export const fmtEur = (cents: number | null | undefined): string => fmtMoney(cents, 'eur');

/** $0,22 */
export function fmtUsd(v: number): string {
  return `$${v.toFixed(v >= 10 ? 0 : v > 0 && v < 0.1 ? 3 : 2).replace('.', ',')}`;
}

export function fmtSec(ms: number | null | undefined): string {
  if (typeof ms !== 'number' || !Number.isFinite(ms)) return '-';
  return `${(ms / 1000).toFixed(ms < 10_000 ? 1 : 0).replace('.', ',')} s`;
}

export function fmtNum(n: number | null | undefined): string {
  return typeof n === 'number' && Number.isFinite(n) ? String(Math.round(n * 100) / 100).replace('.', ',') : '-';
}

/** A count with the Lithuanian noun form it takes: 1, 21, 31 "kartas"; 2-9, 22-29 "kartai"; 0, 10-20, 30 "kartų". */
export function ltCount(n: number, forms: [one: string, few: string, many: string]): string {
  const a = Math.abs(Math.trunc(n)), d = a % 10, h = a % 100;
  const w = d === 1 && h !== 11 ? forms[0] : d >= 2 && (h < 12 || h > 19) ? forms[1] : forms[2];
  return `${n} ${w}`;
}
export const AKYS: [string, string, string] = ['akis', 'akys', 'akių'];
export const KARTAI: [string, string, string] = ['kartas', 'kartai', 'kartų'];

export function fmtBytes(b: number | null | undefined): string {
  if (typeof b !== 'number' || !Number.isFinite(b)) return '-';
  return b > 1 << 20 ? `${(b / (1 << 20)).toFixed(1).replace('.', ',')} MB` : `${Math.round(b / 1024)} kB`;
}

export const STATE_LT: Record<string, string> = {
  unpaid: 'Neapmokėtas', checkout: 'Atidarytas mokėjimas', expired: 'Neapmokėtas, pasibaigęs', broken: 'Be įrašo',
  pending: 'Laukia patvirtinimo laiško', paid: 'Apmokėtas', making: 'Gaminamas', review: 'Laukia peržiūros',
  ready: 'Paruoštas', withdrawn: 'Atsisakyta', deleted: 'Failai ištrinti', test_payment: 'Testo mokėjimas', lab: 'Laboratorijos testas',
};

export const STATE_TONE: Record<string, 'good' | 'warn' | 'bad' | 'muted' | 'info'> = {
  unpaid: 'muted', checkout: 'info', expired: 'muted', broken: 'bad', pending: 'warn', paid: 'info', making: 'info',
  review: 'warn', ready: 'good', withdrawn: 'bad', deleted: 'muted', test_payment: 'muted', lab: 'info',
};

/** The brand name of every style id, generated from the registry (api/_lib/styles_registry.py): never typed here. */
export const STYLE_LT: Record<string, string> = { ...STYLE_NAMES };

export const VERDICT_LT: Record<string, string> = { good: 'Gera', ok: 'Tinkama', weak: 'Silpna', no_eye: 'Akies nerasta' };

export const BLOCK_LT: Record<string, string> = {
  too_blurry: 'Per neryški', too_dark: 'Per tamsi', pupil_too_large: 'Per didelis vyzdys', too_small: 'Per maža rainelė', eyelid: 'Vokas dengia rainelę', unknown: 'Nežinoma',
};

export const DEVICE_LT: Record<string, string> = {
  ios: 'iPhone / iPad', android: 'Android', desktop: 'Kompiuteris', other: 'Kita', unknown: 'Nežinoma',
};

export const SOURCE_LT: Record<string, string> = {
  camera: 'Kamera', gallery: 'Galerija', live: 'Gyva kamera', sample: 'Pavyzdys', lab: 'Laboratorija', other: 'Kita', unknown: 'Nežinoma',
};

export const STEP_LT: Record<string, string> = {
  analyze: 'Analizė', deglare: 'Atspindžiai', enhance: 'Restauravimas', compose: 'Kompozicija',
  master_eye: '4K akis', master_compose: '4K kūrinys',
};

export const KIND_LT: Record<string, string> = {
  busy: 'Gemini užimtas', '400': 'Bloga užklausa', '403': 'Atmesta (403)', '429': 'Per daug (429)', '500': 'Serverio klaida',
  '502': 'Atmetė paslauga (502)', '503': 'Neprieinama (503)',
};

/** An error event's kind in words, with its HTTP status once (a label such as "Atmesta (403)" names it already). */
export function kindLabel(kind: string | null | undefined, status?: number | null): string {
  const k = kind || '';
  const label = KIND_LT[k] || k;
  return status && !label.includes(`(${status})`) ? `${label} (${status})` : label;
}

export const ENDPOINT_LT: Record<string, string> = {
  analyze: 'Analizė', deglare: 'Atspindžiai', enhance: 'Restauravimas', compose: 'Kompozicija', master_eye: '4K akis',
  master_compose: '4K kūrinys', order: 'Užsakymas', checkout: 'Mokėjimas', admin: 'Administravimas',
  stripe_webhook: 'Stripe webhook', other: 'Kita',
};

export const RESULT_LT: Record<string, string> = {
  sent: 'išsiųsta', off: 'el. paštas neįjungtas', bad_address: 'blogas adresas', transient: 'laikinai nepavyko, bandyk vėliau',
  failed: 'Resend atmetė', done: 'jau siunčiama arba išsiųsta', no_address: 'nėra adreso', no_consent: 'neužfiksuotas sutikimas',
  withdrawn: 'užsakymo atsisakyta', legal_unavailable: 'nepavyko nuskaityti teisinių tekstų', link_unavailable: 'nuorodos atkurti negalima',
  not_held: 'nesiųstas: kūrinys nebuvo sulaikytas, laiškas „paruošta“ išėjo, kai jis buvo pagamintas',
};

// the admin audit log's actions (api/_lib/ops.py ACTIONS), named as the buttons that run them
export const ACTION_LT: Record<string, string> = {
  link: 'Pirkėjo nuoroda', resend_confirmation: 'Siųsti patvirtinimą', resend_ready: 'Siųsti „paruošta“',
  release: 'Išleisti kūrinį', clear_review: 'Nuimti peržiūros žymą', mailed_by_hand: 'Išsiunčiau ranka',
  render: 'Pagaminti 4K', recompose: 'Sudėti kūrinį iš naujo', rerun_step: 'Perpiešti kūrinio žingsnį', lab_steps: 'Laboratorijos gamybos žingsniai',
  refund: 'Grąžinti pinigus',
  mark_refunded: 'Grąžinau Stripe svetainėje', delete_files: 'Ištrinti failus', lab_start: 'Laboratorijos testas',
  lab_delete: 'Ištrinti laboratorijos testą', exp_start: 'Paleisti kainų testą', exp_stop: 'Sustabdyti kainų testą',
  styles_override: 'Pakeisti stiliaus būseną', styles_limits: 'Pakeisti dėmesio ribas',
};

// an audit entry's result code in words (RESULT_LT for the email words, then these), else the code itself
const LOG_RESULT_LT: Record<string, string> = {
  started: 'pradėta', deleted: 'ištrinta', released: 'išleista', removed: 'nuimta', none: 'nebuvo ko nuimti',
  marked: 'pažymėta', made: 'padaryta', stored: 'jau buvo padaryta', rerendered: 'perpiešta', composed: 'sudėta', rerun: 'perpiešta', dry: 'tik planas',
  step_held: 'žingsnis sulaikytas', rerun_not_available: 'perpiešti negalima',
  same: 'nepasikeitė', shown: 'parodyta', by_hand: 'pažymėta ranka', refunded: 'grąžinta', succeeded: 'grąžinta',
  pending: 'laukia Stripe', bad_request: 'bloga užklausa', not_found: 'nerasta', stopped: 'sustabdyta',
  already_running: 'jau veikė', not_running: 'neveikė', market_taken: 'rinkoje veikia kitas testas', sells_at_loss: 'atmesta: nuostolis',
  stats_not_collected: 'atmesta: statistika nerenkama', retired: 'atmesta: testas užbaigtas',
  changed: 'pakeista', ticked: 'žymos pakeistos', above_ceiling: 'atmesta: virš registro ribos', needs_ticks: 'atmesta: trūksta žymų',
  not_switchable: 'atmesta: perjungti negalima', stale_view: 'atmesta: puslapis pasenęs', price_test_running: 'atmesta: veikia kainų testas',
  no_engine: 'atmesta: nėra variklio',
};

export const actionLt = (a: unknown): string => ACTION_LT[String(a ?? '')] || String(a ?? '');
export const logResultLt = (r: unknown): string => {
  const k = String(r ?? '');
  return RESULT_LT[k] || LOG_RESULT_LT[k] || k;
};

export const REASON_LT: Record<string, string> = {
  admin_denied: 'Raktas netinka (pasibaigęs, atšauktas arba kitam serveriui).',
  admin_not_configured: "Administravimas šiame serveryje neįjungtas: Vercel'e nustatyk SNAPEYES_ADMIN_SECRET (bent 32 simboliai, python scripts/mint_admin.py --new-secret), SNAPEYES_ADMIN_EPOCH palik tuščią arba tik skaičių, ir paleisk iš naujo.",
  making_not_started: 'Gamyba dar neprasidėjo: ją pradeda pirkėjo užsakymo puslapis. Pradėjus čia pirkėjas netektų teisės atsisakyti, o paskelbtos sąlygos to nenumato.',
  too_many_attempts: 'Per daug nesėkmingų bandymų. Palauk ir bandyk vėliau.',
  storage_not_configured: 'Saugykla (Supabase) šiame serveryje nenustatyta.',
  storage_busy: 'Saugykla neatsakė. Pabandyk po akimirkos.',
  payments_not_configured: 'Stripe nenustatytas arba raktas neturi teisės.',
  payments_busy: 'Stripe neatsakė. Pabandyk po akimirkos.',
  payments_error: 'Stripe atmetė užklausą.',
  not_found: 'Tokio užsakymo nėra.',
  not_paid: 'Užsakymas neapmokėtas.',
  withdrawn: 'Užsakymo atsisakyta: jam nieko negaminama.',
  deleted: 'Šio užsakymo failai ištrinti.',
  link_unavailable: 'Nuorodos atkurti negalima: pasikeitė bilietų paslaptis.',
  email_off: 'Šiame serveryje el. paštas (Resend) neįjungtas.',
  no_address: 'Užsakymui neužfiksuotas el. pašto adresas.',
  no_consent: 'Neužfiksuotas pirkėjo sutikimas, patvirtinimo siųsti nėra ko.',
  legal_unavailable: 'Nepavyko nuskaityti teisinių tekstų. Pabandyk po akimirkos.',
  mail_in_progress: 'Laiškas kaip tik siunčiamas. Pažiūrėk po minutės.',
  no_artwork: 'Kūrinys dar nepagamintas.',
  held: 'Kūrinys laukia tavo peržiūros: pirma jį išleisk (tai išsiunčia ir laišką).',
  test_payment: 'Apmokėta Stripe testo režimu: čia nieko negaminama.',
  rerender_not_allowed: 'master_eye taisyklė: akis perpiešiama tik jei jos 4K nepraėjo patikros ir dar nebuvo perpiešta.',
  draft_missing: 'Trūksta įkelto akies iškarpos ar peržiūros failo.',
  draft_changed: 'Įkelta akies iškarpa ar peržiūra dingo arba pasikeitė.',
  eyes_not_ready: 'Ne visos akys pagamintos.',
  stripe_off: 'Stripe šiame serveryje nenustatytas.',
  unknown_payment: 'Toks mokėjimas šiam užsakymui neužfiksuotas.',
  already_refunded: 'Šis mokėjimas jau grąžintas.',
  in_review: 'Užsakymas pažymėtas peržiūrai: pirma nuimk peržiūros žymą.',
  confirming: 'Patvirtinimo laiškas dar neišsiųstas: nieko negaminama, kol jis neišeis.',
  rendering: 'Ši akis kaip tik piešiama. Pabandyk po minutės.',
  model_busy: 'Gemini šiuo metu užimtas. Pabandyk po minutės.',
  busy_retry: 'Nepakako laiko šiame iškvietime. Pabandyk dar kartą.',
  render_rejected: 'Gemini negrąžino tinkamo 4K vaizdo.',
  bad_link: 'Užsakymo raktas nesutampa.',
  already_running: 'Šis kainų testas jau veikia.',
  not_running: 'Šis kainų testas neveikia.',
  market_taken: 'Šioje rinkoje jau veikia kitas kainų testas: pirma sustabdyk jį.',
  sells_at_loss: 'Kainynas kai kuriems užsakymams parduodamas nuostoliu: paleidimui reikia aiškaus patvirtinimo.',
  stats_not_collected: 'Šiame serveryje nenustatytas CRON_SECRET, todėl lankytojų ir peržiūrų skaičiai nebūtų renkami: paleidimui reikia aiškaus patvirtinimo.',
  retired: 'Šis kainų testas užbaigtas ir daugiau nepaleidžiamas.',
  payment_processing: 'Mokėjimas dar tvirtinamas.',
  step_held: 'Gamybos žingsnis sulaikytas (priežastis ir ką daryti: pranešime ir užsakymo peržiūros žymoje).',
  rerun_not_available: 'Šio užsakymo kūrinį piešia senasis variklis: perpiešk akį ir sudėk kūrinį iš naujo.',
  plate_retry: 'Stiliui reikalingas failas dar neparuoštas. Pabandyk po akimirkos.',
  room_retry: 'Serveris kaip tik piešia kitą užsakymą. Pabandyk po kelių sekundžių.',
  not_lab: 'Tik laboratorijos testinis užsakymas (lab-...) paleidžiamas šitaip.',
  above_ceiling: 'Registro riba žemesnė: aukščiau stilių gali pakelti tik peržiūrėtas kodo pakeitimas.',
  not_switchable: 'Šio stiliaus perjungti negalima: jis dar neturi variklio arba jau išimtas. Tai registro, o ne šio puslapio pakeitimas.',
  needs_ticks: 'Kad stilius taptų užsakomas, reikia tavo žymų: savo žvilgsnio į galutinius kūrinius (L1) ir nepriklausomo vertinimo (L0) arba tavo rašytinio atsisakymo jo. Vertinimas, žemesnis už kartelę (vidurkis bent 3,96, nė viena ašis ne žemiau 3,8), neužtenka: tada padeda tik tavo rašytinis atsisakymas.',
  no_engine: 'Šiame serveryje šio stiliaus variklio nėra.',
  stale_view: 'Perjungiklis pakeistas po to, kai šis puslapis buvo nupieštas: perkrauk puslapį.',
  price_test_running: 'Veikia kainų testas: šis pakeitimas keičia jo imtį. Patvirtink, kad tai perskaitei, ir tęsk.',
};

/** One sentence for a failed reply: our own words for a known reason, else the server's sentence, else the status. */
export function explain(r: Reply<unknown>): string {
  if (r.status === 0) return 'Serveris neatsakė (nėra ryšio arba baigėsi laikas).';
  const lt = REASON_LT[r.reason];
  const detail = r.data && typeof (r.data as Record<string, unknown>).detail === 'string' ? ` (${(r.data as Record<string, unknown>).detail as string})` : '';
  if (lt) return lt + detail;
  if (r.error) return r.error + detail;
  return `Klaida, HTTP ${r.status}.`;
}

/** Estimated Gemini spend (USD) of a period's call counts. */
export function spend(c: Pick<Counts, 'gemini'>, p: Prices): number {
  return c.gemini.vision * p.vision + c.gemini.image_1k * p.image_1k + c.gemini.image_4k * p.image_4k;
}

export const DEFAULT_PRICES: Prices = { vision: 0.003, image_1k: 0.067, image_4k: 0.153 };

/** Long base64 strings in a reply are replaced by their length, so a JSON view stays readable and light. */
export function trimJson(v: unknown, depth = 0): unknown {
  if (typeof v === 'string') return v.length > 300 ? `<${v.length} simbolių>` : v;
  if (Array.isArray(v)) return depth > 6 ? '[...]' : v.slice(0, 50).map((x) => trimJson(x, depth + 1));
  if (v && typeof v === 'object') {
    if (depth > 6) return '{...}';
    return Object.fromEntries(Object.entries(v as Record<string, unknown>).map(([k, x]) => [k, trimJson(x, depth + 1)]));
  }
  return v;
}
