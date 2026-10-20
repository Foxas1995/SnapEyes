// The owner's visitor pages (Saltiniai, Piltuvas, Kodel nepavyksta, Nuotrauku kokybe, Reklamos): the shapes of what api/_lib/traffic.py and ads.py answer, the Lithuanian words, and the small
// calculations behind the pages, as pure functions without React so that suites/ts/admin_traffic.test.ts reads every sentence and every number. Every share is printed with the count behind it
// (stylesView.shareText: "12 iš 40 (30 %)"), a share with nothing under it says so. Money is euro cents (Ads Manager's figures have no VAT; the card is charged 21 percent more: ads.py).
import { dec, fmtPct, shareText } from './stylesView';
import { BLOCK_LT, DEVICE_LT, ENDPOINT_LT, KIND_LT, REASON_LT, SOURCE_LT, STYLE_LT, VERDICT_LT, fmtMoney } from './format';

export type Steps = Record<string, number>;
export type Group = 'src' | 'cmp' | 'trm' | 'cnt';
export interface CampKey { src: string; med: string; cmp: string; trm: string; cnt: string }
export interface SrcRow { key: CampKey; steps: Steps; orders?: number; revenue?: Record<string, number> }
export interface Filters { market?: string; lang?: string; dev?: string; br?: string; src?: string; cmp?: string }
export interface Available { market: string[]; lang: string[]; dev: string[]; br: string[]; src: string[]; cmp: string[] }
export interface Base { ok: boolean; days: number; filters: Filters; available: Available; partial: boolean; recording: boolean }
export interface SourcesReply extends Base {
  group: Group; rows: SrcRow[]; totals: Steps; other: number; orders?: number; revenue?: Record<string, number>; orders_comparable: boolean; orders_more: boolean;
}
export interface Pct { ms: number | null; over: boolean; n: number }
export interface Pcts { p50: Pct; p95: Pct }
export interface FunnelReply extends Base {
  steps: Steps; by_dev: Record<string, Steps>; by_br: Record<string, Steps>; other: number;
  ttp: { all: Pcts; by_dev: Record<string, Pcts>; by_br: Record<string, Pcts> }; cc: Record<string, Record<string, number>>;
}
export type Fx = Record<string, Record<string, Record<string, number>>>;
export interface MsReport { all: Pcts; by_dev: Record<string, Pcts>; by_br: Record<string, Pcts> }
// "times", not "ms": every admin reply carries the milliseconds the call took under that name (api/_lib/iris.py run)
export interface FxReply extends Base { fx: Fx; times: Record<string, MsReport>; by: string | null }
export interface AdRow { id: string; day: string; src: string; cmp: string; trm?: string; cnt?: string; amount: number; vat: boolean; impr?: number; clicks?: number }
export interface AdsReply extends Base {
  rows: AdRow[]; rev: number; groups: SrcRow[]; totals: Steps; orders: number; revenue: Record<string, number>; orders_more: boolean; vat: number;
}

// ------------------------------------------------------------------------------------------------ words
export const GROUP_LT: Record<Group, string> = { src: 'Šaltinis', cmp: 'Kampanija', trm: 'Reklamų rinkinys', cnt: 'Reklama' };
export const STEP_LT: Record<string, string> = {
  landing: 'Nusileidimai', try: 'Atidarė /try', photo: 'Pasirinko nuotrauką', result: 'Peržiūra parodyta', soon: 'Pirkimo kortelė uždaryta', buy: 'Paspaudė pirkti', order: 'Atidarė užsakymo puslapį',
  an: 'Nuotraukų patikros', anok: 'Tinkamos nuotraukos', en: 'Pradėtos peržiūros', rs: 'Užbaigtos peržiūros', sv: 'Stiliaus peržiūros', co: 'Mokėjimo puslapis', pd: 'Apmokėta', help: 'Rašė el. paštu',
};
export const SRC_LT: Record<string, string> = {
  fb: 'Facebook (reklama)', ig: 'Instagram (reklama)', msg: 'Messenger (reklama)', an: 'Audience Network (reklama)', facebook: 'Facebook (nuoroda)', instagram: 'Instagram (nuoroda)', tiktok: 'TikTok',
  google: 'Google', direct: 'Tiesiogiai', other: 'Kita svetainė', '-': 'Be šaltinio', meta: 'Meta',
};
export const BR_LT: Record<string, string> = {
  fb: 'Facebook programa', ig: 'Instagram programa', tt: 'TikTok programa', wv: 'Kita programa (web view)', samsung: 'Samsung naršyklė', edge: 'Edge', opera: 'Opera', firefox: 'Firefox', chrome: 'Chrome', safari: 'Safari',
  other: 'Kita', '-': 'Nežinoma',
};
export const DEV_LT: Record<string, string> = { ...DEVICE_LT, '-': 'Nežinoma' };
export const MARKET_LT: Record<string, string> = { eu: 'ES (EUR)', lt: 'Lietuva', hu: 'Vengrija', au: 'Australija', '-': 'Nežinoma' };
export const LANG_LT: Record<string, string> = { en: 'Anglų', de: 'Vokiečių', lt: 'Lietuvių', hu: 'Vengrų', '-': 'Nežinoma' };
export const MED_LT: Record<string, string> = { paid: 'mokama', org: 'organika', bio: 'bio nuoroda', story: 'stories', '': '', '-': '' };

const IN_APP = new Set(['fb', 'ig', 'tt', 'wv']);
/** Is this browser family another app's in-app browser (the ads plan's gate G4)? */
export const inApp = (br: string): boolean => IN_APP.has(br);

export const label = (map: Record<string, string>, k: string): string => map[k] ?? (k || '-');

/** A campaign key in words: "Facebook (reklama) / mokama / se-p0-test / lt-a1-eye / a1-lt-s1" down to the part the group has. */
export function keyText(k: CampKey, group: Group): string {
  const parts: string[] = [label(SRC_LT, k.src || '-')];
  if (k.med) parts.push(label(MED_LT, k.med));
  if (group !== 'src') parts.push(k.cmp || 'be kampanijos');
  if (group === 'trm' || group === 'cnt') parts.push(k.trm || 'be rinkinio');
  if (group === 'cnt') parts.push(k.cnt || 'be reklamos');
  return parts.filter(Boolean).join(' / ');
}

// ------------------------------------------------------------------------------------------------ numbers
const n0 = (v: number | undefined): number => (typeof v === 'number' && Number.isFinite(v) ? v : 0);
export const num = n0;

/** num / den, or null when there is no denominator. */
export const rate = (num_: number, den: number): number | null => (den > 0 ? num_ / den : null);

/** "63 % (45 iš 71)" or "nėra duomenų (0)": a share with its count. */
export const share = (k: number, n: number): string => (n > 0 ? shareText(k, n) : 'nėra duomenų (0)');

/** The steps of a row with the share each step is of the one before it: [{step, n, of, share}] in the order given (steps with no count at all are kept: a zero is data). */
export function chain(steps: Steps, order: readonly string[]): { step: string; n: number; prev: number | null; share: number | null }[] {
  return order.map((s, i) => {
    const prev = i === 0 ? null : n0(steps[order[i - 1]]);
    return { step: s, n: n0(steps[s]), prev, share: prev === null ? null : rate(n0(steps[s]), prev) };
  });
}

/** The funnel bars: each step as a share of the first and of the step before it. */
export function bars(steps: Steps, order: readonly string[]): { step: string; n: number; ofTop: number | null; ofPrev: number | null; lost: number | null }[] {
  const top = n0(steps[order[0]]);
  return order.map((s, i) => {
    const n = n0(steps[s]);
    const prev = i === 0 ? null : n0(steps[order[i - 1]]);
    return { step: s, n, ofTop: rate(n, top), ofPrev: prev === null ? null : rate(n, prev), lost: prev === null || prev === 0 ? null : Math.max(0, prev - n) / prev };
  });
}

export const FUNNEL_STEPS = ['landing', 'try', 'photo', 'result', 'buy', 'order'] as const;
export const SOURCE_STEPS = ['landing', 'try', 'photo', 'result', 'sv', 'buy', 'co', 'pd'] as const;
/** The step each column of the Saltiniai table is the share of: the style previews are a count of requests (one visitor asks for several), so they have no share; the buy card follows the preview shown. */
export const SOURCE_PREV: Record<string, string | null> = { landing: null, try: 'landing', photo: 'try', result: 'photo', sv: null, buy: 'result', co: 'buy', pd: 'co' };
export const SERVER_STEPS = ['an', 'anok', 'en', 'rs', 'sv', 'co', 'pd', 'help'] as const;

/** A time bound the percentile gives: "12 s" or "virš 300 s" for a bucket above the last bound, "-" for none. */
export function pctText(p: Pct | undefined): string {
  if (!p || p.n <= 0 || (p.ms === null && !p.over)) return 'nėra duomenų';
  if (p.over) return 'virš ribos';
  return `${dec(Math.round((p.ms as number) / 100) / 10)} s`;
}

export const eur = (cents: number): string => fmtMoney(cents, 'eur');

/** Money per currency as the page prints it: "79,94 €; 10 000 Ft"; "-" for none. */
export function moneyText(m: Record<string, number> | undefined): string {
  const keys = Object.keys(m ?? {}).sort((a, b) => (a === 'eur' ? -1 : b === 'eur' ? 1 : a.localeCompare(b)));
  return keys.length ? keys.map((c) => fmtMoney((m as Record<string, number>)[c], c)).join('; ') : '-';
}

// ------------------------------------------------------------------------------------------------ the fx tables (Kodel nepavyksta, Nuotrauku kokybe)
export interface FxLine { value: string; total: number; by: Record<string, number> }

/** The lines of one metric, largest first: each value with its count in the whole and in every group. */
export function fxLines(fx: Fx | undefined, metric: string): FxLine[] {
  const t = fx?.[metric] ?? {};
  return Object.entries(t).map(([value, by]) => ({ value, total: n0(by.all ?? Object.values(by).reduce((a, b) => a + b, 0)), by })).sort((a, b) => b.total - a.total || a.value.localeCompare(b.value));
}

export const fxTotal = (fx: Fx | undefined, metric: string): number => fxLines(fx, metric).reduce((s, l) => s + l.total, 0);

/** The groups that appear in a split, largest first (all is not one of them). */
export function groupsOf(fx: Fx | undefined, metrics: readonly string[], max = 6): string[] {
  const t: Record<string, number> = {};
  for (const m of metrics) for (const by of Object.values(fx?.[m] ?? {})) for (const [g, n] of Object.entries(by)) if (g !== 'all') t[g] = (t[g] ?? 0) + n;
  return Object.entries(t).sort((a, b) => b[1] - a[1]).slice(0, max).map(([g]) => g);
}

const GATE_LT: Record<string, string> = { ok: 'Praėjo', lid: 'Voko taisyklė', fill: 'Užpildymo taisyklė', both: 'Abi taisyklės', unknown: 'Nežinoma' };
const RETRY_LT: Record<string, string> = { none: 'Nereikėjo', kept2: 'Antra restauracija išlaikyta', kept1: 'Antra padaryta, pirma išlaikyta', time: 'Nebuvo laiko', error: 'Antra nepavyko' };
const RES_LT: Record<string, string> = { mp_lt1: 'iki 1 MP', mp_1_3: '1-3 MP', mp_3_8: '3-8 MP', mp_8_16: '8-16 MP', mp_16_40: '16-40 MP', mp_40p: 'virš 40 MP' };
const ORI_LT: Record<string, string> = { portrait: 'Stačia', landscape: 'Gulsčia', square: 'Kvadratinė' };
const IRIS_LT: Record<string, string> = { d_lt280: 'rainelė iki 280 px', d_280_420: 'rainelė 280-420 px', d_420_600: 'rainelė 420-600 px', d_600p: 'rainelė virš 600 px' };
const CLS_LT: Record<string, string> = { own: 'Savo spalva', dark_brown: 'Tamsiai ruda', grey: 'Pilka' };
const PUPIL_LT: Record<string, string> = { round: 'Apvalus', slit: 'Plyšinis', bar: 'Juostelė' };
const RETAKE_LT: Record<string, string> = { '0': 'Pirma nuotrauka', '1': 'Po vieno pakartojimo', '2': 'Po dviejų ar daugiau' };
const LOCK_LT: Record<string, string> = { locked: 'Rainelė užfiksuota', unlocked: 'Nepavyko užfiksuoti' };

/** The words of a value of a metric (the code itself where no word is known). */
export function valueLt(metric: string, value: string, gateCode: (c: string) => string = (c) => c): string {
  switch (metric) {
    case 'an_verdict': return VERDICT_LT[value] ?? value;
    case 'an_block': return BLOCK_LT[value] ?? value;
    case 'an_res': return RES_LT[value] ?? value;
    case 'an_ori': return ORI_LT[value] ?? value;
    case 'an_iris': return IRIS_LT[value] ?? value;
    case 'an_source': return SOURCE_LT[value] ?? value;
    case 'an_lock': return LOCK_LT[value] ?? value;
    case 'en_gate': return GATE_LT[value] ?? value;
    case 'en_reason': case 'set_gate': return value === 'ok' || GATE_LT[value] ? (GATE_LT[value] ?? value) : gateCode(value);
    case 'en_cls': return CLS_LT[value] ?? value;
    case 'en_pupil': return PUPIL_LT[value] ?? value;
    case 'en_retry': return RETRY_LT[value] ?? value;
    case 'en_qa': return value === 'ok' ? 'Spalvų patikra praėjo' : 'Spalvų patikra nepraėjo';
    case 'en_reveal': return value;
    case 'set_retake': return RETAKE_LT[value] ?? value;
    case 'set_eyes': return `${value} ${Number(value) === 1 ? 'akis' : 'akys'}`;
    case 'sv_style': return STYLE_LT[value] ?? value;
    case 'err_ep': return ENDPOINT_LT[value] ?? value;
    case 'err_cls': return KIND_LT[value] ?? value;
    case 'err_reason': return REASON_LT[value] ? `${value}` : value;
    default: return value;
  }
}

/** A group of a split in words: a device class, a browser family or a campaign ("fb / se-p0-test"). */
export function groupLt(by: string | null, g: string): string {
  if (g === 'all') return 'Viso';
  if (by === 'dev') return label(DEV_LT, g);
  if (by === 'br') return label(BR_LT, g);
  if (by === 'cmp') { const [s, c] = g.split(' / '); return `${label(SRC_LT, s ?? '-')} / ${c && c !== '-' ? c : 'be kampanijos'}`; }
  return g;
}

// ------------------------------------------------------------------------------------------------ the spend (Reklamos)
export interface AdTotals { spend: number; card: number; impr: number; clicks: number; hasClicks: boolean; hasImpr: boolean; rows: number }

/** The Ads Manager figure of a ledger row in euro cents (a typed card amount has Meta's VAT in it) and what the card paid. */
export const netOf = (r: AdRow, vat = 1.21): number => (r.vat ? Math.round(r.amount / vat) : r.amount);
export const cardOf = (r: AdRow, vat = 1.21): number => (r.vat ? r.amount : Math.round(r.amount * vat));

/** The ledger rows that belong to a campaign key at a level: a row with only a campaign belongs to the campaign, one with an ad set also to that ad set, one with an advertisement to it too. */
export function rowsFor(ledger: AdRow[], k: Pick<CampKey, 'cmp' | 'trm' | 'cnt'>, group: Group, from: string): AdRow[] {
  return ledger.filter((r) => r.day >= from && r.cmp === k.cmp && (group === 'cmp' || group === 'src' || ((r.trm ?? '') === k.trm && (group === 'trm' || (r.cnt ?? '') === k.cnt))));
}

export function totalsOf(rows: AdRow[], vat = 1.21): AdTotals {
  return {
    spend: rows.reduce((s, r) => s + netOf(r, vat), 0), card: rows.reduce((s, r) => s + cardOf(r, vat), 0),
    impr: rows.reduce((s, r) => s + n0(r.impr), 0), clicks: rows.reduce((s, r) => s + n0(r.clicks), 0),
    hasImpr: rows.some((r) => typeof r.impr === 'number'), hasClicks: rows.some((r) => typeof r.clicks === 'number'), rows: rows.length,
  };
}

export type Tone = 'good' | 'warn' | 'bad' | 'muted';
export interface Light { key: string; label: string; tone: Tone; text: string }

const tone3 = (v: number | null, good: (x: number) => boolean, warn: (x: number) => boolean): Tone => (v === null ? 'muted' : good(v) ? 'good' : warn(v) ? 'warn' : 'bad');
const pc = (v: number | null): string => (v === null ? 'nėra duomenų' : fmtPct(v));
const cost = (cents: number, k: number): number | null => (k > 0 ? Math.round(cents / k) : null);
const costText = (c: number | null): string => (c === null ? 'nėra duomenų' : eur(c));

/** The traffic lights of the ads plan's phase 0 (section 2.3) for one campaign, from its spend and the counter's steps. Missing inputs are grey with the words "nėra duomenų": a light is never
 *  green or red on nothing. market lt is the plan's best market: the cost of a completed preview is judged on its own (2 and 4 euros), the other markets by their ratio to LT's when it is known. */
export function phase0(t: AdTotals, steps: Steps, market: string | null, ltCost: number | null = null): Light[] {
  const landing = n0(steps.landing), started = n0(steps.en), done = n0(steps.rs);
  const spent = t.rows > 0;      // no ledger row: the cost of anything is not known (nothing typed is not a cost of nothing)
  const ctr = t.hasImpr && t.impr > 0 && t.hasClicks ? t.clicks / t.impr : null;
  const cpc = spent && t.hasClicks && t.clicks > 0 ? Math.round(t.spend / t.clicks) : null;
  const land = t.hasClicks && t.clicks > 0 ? landing / t.clicks : null;
  const start = rate(started, landing);
  const fin = rate(done, started);
  const perDone = spent ? cost(t.spend, done) : null;
  const lights: Light[] = [
    { key: 'ctr', label: 'Paspaudimų dalis (link CTR)', tone: tone3(ctr, (x) => x >= 0.012, (x) => x >= 0.006), text: pc(ctr) },
    { key: 'cpc', label: 'Kaina už paspaudimą (LT)', tone: tone3(cpc, (x) => x <= 40, (x) => x <= 80), text: costText(cpc) },
    { key: 'landing', label: 'Nusileidimai / paspaudimai', tone: tone3(land, (x) => x >= 0.75, (x) => x >= 0.55), text: pc(land) },
    { key: 'started', label: 'Pradėta / nusileidimai', tone: tone3(start, (x) => x >= 0.12, (x) => x >= 0.06), text: pc(start) },
    { key: 'done', label: 'Užbaigta / pradėta', tone: tone3(fin, (x) => x >= 0.6, (x) => x >= 0.4), text: pc(fin) },
  ];
  let tone: Tone;
  if (market === 'lt' || market === null) tone = tone3(perDone, (x) => x <= 200, (x) => x <= 400);
  else if (perDone === null) tone = 'muted';
  else if (ltCost && market === 'de') tone = perDone > ltCost * 3 ? 'bad' : perDone <= ltCost * 2.5 ? 'good' : 'warn';
  else if (ltCost && market === 'hu') tone = perDone <= ltCost * 1.2 ? 'good' : perDone <= ltCost * 3 ? 'warn' : 'bad';
  else tone = 'muted';
  lights.push({ key: 'perdone', label: 'Kaina už užbaigtą peržiūrą', tone, text: costText(perDone) });
  return lights;
}

/** Phase 1 (the plan's section 6): the cost of an order and the return on the spend. CPA (Ads Manager figures) up to 12 euros and ROAS from 1,8 are green, CPA up to 15 euros and ROAS from 1,5 amber. */
export function phase1(spendNet: number, orders: number, revenueEur: number): Light[] {
  const cpa = cost(spendNet, orders);
  const roas = spendNet > 0 ? revenueEur / spendNet : null;
  return [
    { key: 'cpa', label: 'Kaina už užsakymą (CPA)', tone: tone3(cpa, (x) => x <= 1200, (x) => x <= 1500), text: costText(cpa) },
    { key: 'roas', label: 'Grąža (ROAS)', tone: tone3(roas, (x) => x >= 1.8, (x) => x >= 1.5), text: roas === null ? 'nėra duomenų' : dec(Math.round(roas * 100) / 100) },
  ];
}

/** The decision at the end of phase 0 (the plan's section 2.4) from what is counted: the first three conditions are numbers, the fourth (no unresolved ad rejection) is the owner's. */
export function phase0Decision(done: number, bestMarketDone: number, bestCost: number | null, landing: number, clicks: number): { ok: boolean | null; lines: { text: string; ok: boolean | null }[] } {
  const lines = [
    { text: `Užbaigta bent 10 peržiūrų iš reklamos: ${done}`, ok: done >= 10 },
    { text: `Iš jų bent 6 geriausioje rinkoje: ${bestMarketDone}`, ok: bestMarketDone >= 6 },
    { text: `Kaina už užbaigtą peržiūrą geriausioje rinkoje ne didesnė kaip 4 €: ${costText(bestCost)}`, ok: bestCost === null ? null : bestCost <= 400 },
    { text: `Nusileidimai / paspaudimai ne mažiau kaip 55 %: ${clicks > 0 ? fmtPct(landing / clicks) : 'įrašyk paspaudimus (Reklamos)'}`, ok: clicks > 0 ? landing / clicks >= 0.55 : null },
  ];
  const known = lines.every((l) => l.ok !== null);
  return { ok: known ? lines.every((l) => l.ok) : lines.some((l) => l.ok === false) ? false : null, lines };
}

// ------------------------------------------------------------------------------------------------ CSV
const cell = (v: string | number): string => {
  const s = String(v);
  return /[;"\n\r]/.test(s) || /^[=+@-]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
};
/** CSV with a semicolon (Excel in Lithuanian settings) and a decimal comma; a cell that starts like a formula is quoted. */
export function toCsv(head: string[], rows: (string | number | null)[][]): string {
  return [head, ...rows.map((r) => r.map((v) => (v === null ? '' : typeof v === 'number' ? String(v).replace('.', ',') : v)))].map((r) => r.map(cell).join(';')).join('\r\n') + '\r\n';
}

/** The rows of the Saltiniai table as CSV. */
export function sourcesCsv(rep: Pick<SourcesReply, 'rows' | 'group'>): string {
  const head = ['Šaltinis', 'Priemonė', 'Kampanija', 'Rinkinys', 'Reklama', ...SOURCE_STEPS.map((s) => STEP_LT[s]), 'Užsakymai', 'Pajamos'];
  return toCsv(head, rep.rows.map((r) => [r.key.src || '-', r.key.med, r.key.cmp, r.key.trm, r.key.cnt, ...SOURCE_STEPS.map((s) => n0(r.steps[s])), n0(r.orders), moneyText(r.revenue)]));
}

// ------------------------------------------------------------------------------------------------ the ads page: the counter's rows put together with the spend
/** The counter's rows summed by campaign, ad set or advertisement (the platform and the medium do not matter to the spend: Meta bills a campaign, not a placement). */
export function rollup(rows: SrcRow[], group: 'cmp' | 'trm' | 'cnt'): SrcRow[] {
  const by = new Map<string, SrcRow>();
  for (const r of rows) {
    const key: CampKey = { src: '', med: '', cmp: r.key.cmp, trm: group === 'cmp' ? '' : r.key.trm, cnt: group === 'cnt' ? r.key.cnt : '' };
    const id = [key.cmp, key.trm, key.cnt].join('|');
    const cur = by.get(id) ?? { key, steps: {}, orders: 0, revenue: {} };
    for (const [s, n] of Object.entries(r.steps)) cur.steps[s] = n0(cur.steps[s]) + n0(n);
    cur.orders = n0(cur.orders) + n0(r.orders);
    for (const [c, v] of Object.entries(r.revenue ?? {})) (cur.revenue as Record<string, number>)[c] = n0((cur.revenue as Record<string, number>)[c]) + n0(v);
    by.set(id, cur);
  }
  return [...by.values()].sort((a, b) => n0(b.steps.landing) - n0(a.steps.landing) || (a.key.cmp + a.key.trm + a.key.cnt).localeCompare(b.key.cmp + b.key.trm + b.key.cnt));
}

/** The rows of the Reklamos page at a level: the counter's rows of advertisements (utm_medium paid, or a campaign that has spend in the ledger in the window) rolled up to the level, and a row of nothing
 *  for every campaign, ad set or advertisement that only has spend in the ledger (money spent and no visit counted is what the owner most needs to see). Organic links and visits without a code are not advertising. */
export function adRows(groups: SrcRow[], ledger: AdRow[], level: 'cmp' | 'trm' | 'cnt', from: string): SrcRow[] {
  const inWindow = ledger.filter((r) => r.day >= from);
  const spent = new Set(inWindow.map((r) => r.cmp));
  const rows = rollup(groups.filter((g) => g.key.med === 'paid' || (g.key.cmp !== '' && spent.has(g.key.cmp))), level);
  const have = new Set(rows.map((r) => [r.key.cmp, r.key.trm, r.key.cnt].join('|')));
  for (const r of inWindow) {
    const key: CampKey = { src: '', med: '', cmp: r.cmp, trm: level === 'cmp' ? '' : r.trm ?? '', cnt: level === 'cnt' ? r.cnt ?? '' : '' };
    const id = [key.cmp, key.trm, key.cnt].join('|');
    if (!have.has(id)) { have.add(id); rows.push({ key, steps: {}, orders: 0, revenue: {} }); }
  }
  return rows;
}

/** The market an ad set is for, by the plan's naming (lt-a1-eye, lt-win, de-win, hu-win: the first part): lt, de or hu, else null. */
export const marketOfTerm = (trm: string): string | null => {
  const m = /^(lt|de|hu|at)-/.exec(trm);
  return m ? m[1] : null;
};

/** The euro cents of a euro amount a person typed ("2,50", "2.5", " 12 ") or null when it is not an amount from 0 to 10 000. */
export function centsOf(text: string): number | null {
  const t = text.trim().replace(/\s/g, '').replace(',', '.');
  if (!/^[0-9]+(\.[0-9]{1,2})?$/.test(t)) return null;
  const c = Math.round(Number(t) * 100);
  return c >= 0 && c <= 1_000_000 ? c : null;
}

/** The first day of the window of n days ending today (UTC), as YYYY-MM-DD: the spend of the ledger from there on is the spend of the counter's window. */
export function fromDay(n: number, now = Date.now()): string {
  return new Date(now - (n - 1) * 86_400_000).toISOString().slice(0, 10);
}

/** An order's packed campaign code ("fb|paid|se-p0-test|lt-a1-eye|a1-lt-s1") in words: "Facebook (reklama) / mokama / se-p0-test / lt-a1-eye / a1-lt-s1"; empty parts are left out. */
export function campText(camp: string | null | undefined): string {
  if (!camp) return '';
  const [src = '', med = '', cmp = '', trm = '', cnt = ''] = camp.split('|');
  return [src ? label(SRC_LT, src) : '', med ? label(MED_LT, med) : '', cmp, trm, cnt].filter(Boolean).join(' / ');
}
