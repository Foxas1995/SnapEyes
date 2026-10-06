// The words and the small calculations of the Stiliai page of the admin panel (work package WP13b): pure functions and Lithuanian dictionaries, no React, so that a page
// test (suites/ts/admin_styles.test.ts) can read every sentence and every number the page prints. The numbers come from the server (api/_lib/style_stats.py, the actions
// styles_catalogue, styles_stats, styles_override and styles_audit); this file only writes them down: every rate with the n behind it, never a bare percentage.
import type {
  AttentionItem, FunnelLine, L0State, Reply, StageCode, StyleAuditEntry, StyleCatalogue, StyleChange, StyleHeld, StyleRange, StyleRow,
} from './api';
import { AKYS, explain, ltCount } from './format';

export type ViewTone = 'good' | 'warn' | 'bad' | 'info' | 'muted';

// ------------------------------------------------------------------------------------------------ words
export const STAGE_LT: Record<string, string> = {
  planned: 'Suplanuotas', lab: 'Laboratorija', preview: 'Greitai (peržiūra)', live: 'Parduodamas', retired: 'Išjungtas',
};
export const STAGE_ABOUT_LT: Record<string, string> = {
  lab: 'matomas tik šiame administravimo puslapyje',
  preview: 'pirkėjas mato paveikslėlį ir nemokamą peržiūrą, bet užsisakyti negali (rodoma „Greitai“)',
  live: 'pirkėjas gali užsisakyti (jei užsakymų priėmimas atidarytas)',
  restore: 'pašalinama tavo riba: galioja registro riba',
};
export const STAGE_TONE: Record<string, ViewTone> = { live: 'good', preview: 'info', lab: 'muted', planned: 'muted', retired: 'bad' };
export const stageLt = (s: string | null | undefined): string => (s ? STAGE_LT[s] || s : 'nėra');
/** The rank of a stage: a change may not go above the ceiling (api/_lib/catalogue.py STAGE_RANK). */
export const STAGE_RANK: Record<string, number> = { planned: 0, retired: 0, lab: 1, preview: 2, live: 3 };

export const GROUP_LT: Record<string, string> = { solo: 'Viena akis', duo: 'Dvi akys', grp: 'Trys ir daugiau akių', pet: 'Augintiniai' };
export const GROUP_ORDER = ['solo', 'duo', 'grp', 'pet'];
export const GATE_POLICY_LT: Record<string, string> = { none: 'be vartų', advisory: 'vartai tik perspėja', hard: 'vartai privalomi' };
export const PRICE_CLASS_LT: Record<string, string> = { black: 'juodoji kaina', art: 'meninė kaina' };

export const CLASS_LT: Record<string, string> = { own: 'kitos spalvos', dark_brown: 'tamsiai rudos', grey: 'pilkos' };
export const PUPIL_LT: Record<string, string> = { round: 'apvalus', slit: 'vertikalus plyšys', bar: 'horizontali juosta' };

/** Eye counts and sets as the panel counts them (Lithuanian noun forms: 1, 21 "rinkinys"; 2 to 9 "rinkiniai"; 0, 10 to 20 "rinkinių"). */
export const RINKINIAI: [string, string, string] = ['rinkinys', 'rinkiniai', 'rinkinių'];

/** The checks of a style going live (spec 4.1, L0 to L11): a name for the owner and one sentence of what it asks for. */
export const CHECK_LT: Record<string, { name: string; hint: string }> = {
  L0: { name: 'Nepriklausomas vertinimas (L0)', hint: 'Meno vadovo aklas vertinimas ant tikrų 4096 px akių (4K failų), 100 % didinime: vidurkis bent 3,96 ir nė viena ašis ne žemiau 3,8; arba tavo rašytinis atsisakymas jo.' },
  L1: { name: 'Tavo žvilgsnis į galutinius kūrinius (L1)', hint: 'Tikra grandinė, 4096 px, JPEG kaip pristatomas, bent trys tavo akių rinkiniai, tarp jų silpniausia šio stiliaus klasė.' },
  L2: { name: 'Automatiniai testai praėjo (L2)', hint: 'Testai T1 iki T7, T9, T10 iki T14, T18 ir T19 praėjo veikiančioje funkcijoje.' },
  L3: { name: '4K gamyba telpa į laiką ir atmintį (L3)', hint: 'Vienos, dviejų ir trijų akių 4K kūrinys veikiančiame serveryje telpa į biudžetą, be pakartojimų ciklo.' },
  L4: { name: 'Peržiūra sutampa su failu (L4)', hint: 'Bent 5 akys kiekvienoje grupėje per tikrą grandinę: T9a bent 0,97, T9b ribose.' },
  L5: { name: 'Vartų nesėkmių dažnis perskaitytas (L5)', hint: 'Pirmos 50 tikrų peržiūrų; dviem ir daugiau akių tai rinkinių piltuvas ir atidarymo kriterijus.' },
  L6: { name: 'Vandens ženklas išmatuotas (L6)', hint: 'Kiekvienoje stiliaus drobėje ir visomis keturiomis kalbomis.' },
  L7: { name: 'Pradžios puslapis rodo tik šiuos stilius (L7)', hint: 'Tie patys vardai, tame pačiame leidime.' },
  L8: { name: 'Tekstus perskaitė gimtakalbiai (L8)', hint: 'Lietuvių ir vengrų kalbomis; teisinius tekstus patikrino ir teisininkas.' },
  L9: { name: 'Pavadinimas patikrintas (L9)', hint: 'Prekių ženklų paieška: EUIPO TMview ir IP Australia.' },
  L10: { name: 'Sveikata ir plokštelės (L10)', hint: '/api/health rodo, kad styles ir plates_4k teisingi; stiliaus plokštelės yra pakete ir, kur reikia, saugykloje.' },
  L11: { name: 'Kainų testas (L11)', hint: 'Joks kainų testas neveikia, arba perskaitei eilutę, kad šis pakeitimas keičia jo imtį.' },
};
export const checkName = (c: string): string => CHECK_LT[c]?.name || c;

export const L0_STATE_LT: Record<string, string> = {
  pass: 'įvykdytas: vertinimas praėjo kartelę',
  below_bar: 'vertinimas žemiau kartelės: įrašytas, bet neįskaitomas',
  incomplete: 'neišsamus: trūksta vieno skaičiaus arba vertintojo vardo',
  waiver: 'atsisakyta raštu',
};
export const l0Text = (s: L0State | undefined): string => (s ? L0_STATE_LT[s] || s : 'dar nėra');
export const L0_TONE: Record<string, ViewTone> = { pass: 'good', waiver: 'warn', below_bar: 'bad', incomplete: 'warn' };

export const REASON_KIND_LT: Record<string, string> = { quality: 'kokybė', capacity: 'pajėgumas', soon: 'dar ne laikas', other: 'kita' };

/** The reason codes of the restoration gate (api/_lib/styles/gate.py) and the codes of the enhance event. */
export const GATE_CODE_LT: Record<string, string> = {
  ok: 'praėjo', unknown: 'nežinoma (nėra užantspauduoto profilio)', lid: 'nepraėjo voko taisyklė', fill: 'nepraėjo užpildymo taisyklė', both: 'nepraėjo abi taisyklės',
  lid_sectors_inner: 'voko ar blakstienų sektoriai viduje', lid_sectors_outer: 'voko ar blakstienų sektoriai išorėje', lid_ring_outliers: 'žiede yra nukrypusių spalvų',
  lid_outliers_and_sectors: 'nukrypusios spalvos ir sektoriai kartu', lid_deviation: 'per didelis žiedo spalvų nukrypimas',
  fill_lid_margin: 'užpildymas: voko paraštė', fill_rim_sector: 'užpildymas: krašto sektorius', fill_hard_edges: 'užpildymas: aštrūs kraštai', fill_catchlight: 'užpildymas: atspindys akyje',
  bar_pupil: 'horizontalus vyzdys', reseal: 'reikia iš naujo padaryti peržiūrą', gate: 'vartai',
};
export const gateCodeLt = (c: string): string => GATE_CODE_LT[c] || c;

export const FALLBACK_LT: Record<string, string> = {
  overlap_fallback: 'persidengimo atsarginis variantas (Kiss geometrija)', stack_contrast: 'sudėta viena ant kitos (stipriai skirtingos spalvos)', kiss: 'Kiss geometrija',
};
export const fallbackLt = (c: string | null | undefined): string => (c ? FALLBACK_LT[c] || c : 'nėra');

export const WHAT_LT: Record<string, string> = { compose: 'peržiūra 1024 px', tile: 'paveikslėlis 480 px', art: '4K kūrinys' };

export const TILE_WHY_LT: Record<string, string> = {
  gate: 'nepraėjo vartai', reseal: 'reikia iš naujo padaryti peržiūrą', stage: 'šio stiliaus serveris nepiešia', eyes: 'netinka tokiam akių skaičiui', unknown: 'nežinomas stilius',
  bar_pupil: 'horizontalus vyzdys', no_time: 'pritrūko laiko', plate_unavailable: 'trūksta plokštelės', error: 'klaida piešiant',
};
export const tileWhyLt = (c: string | null | undefined): string => (c ? TILE_WHY_LT[c] || c : '');

/** The checks that run on every delivered artwork (api/_lib/styles/selfcheck.py): the number is the brief's. */
export const SELFCHECK_LT: Record<string, string> = {
  t1: 'T1 rainelė nepaliesta', t2: 'T2 vyzdys neuždengtas', t3: 'T3 matoma rainelės dalis', t4: 'T4 juodo dalis', t6: 'T6 nieko ant rainelės', t7: 'T7 tekstas tik kliento', t12: 'T12 jokių širdžių',
  t18: 'T18 rainelė pakankamai didelė', t19: 'T19 jokia rainelė ne apačioje daugiau nei dviejuose sąlytyse', seam: 'siūlė tarp rainelių',
};
export const selfcheckLt = (c: string): string => SELFCHECK_LT[c] || c.toUpperCase();

export const EDGE_LT: Record<string, string> = { dark: 'tamsus kraštas', hairline: 'plona linija' };
export const PLAN8_NOTE_LT: Record<string, string> = {
  pixel_choices: 'serverio planas liko galioti: skyrėsi tik tai, ką nulėmė pikseliai (pasirinkta iš 1024 px, puslapis rodė iš mažesnės kopijos)',
};

export const HOLD_LT: Record<string, string> = {
  style_step_too_big: 'gamybos žingsnis per didelis šiam serveriui', style_not_priced: 'kainų lentelėje nėra eilutės', engine_skew: 'pasikeitė variklio versija po apmokėjimo',
  class_changed: '4K akies spalvų klasė kita nei peržiūros', pupil_changed: '4K akies vyzdys kitoks nei peržiūros', style_step_failed: 'žingsnis žuvo tris kartus arba du kartus tą pačią klaidą',
  plate_unavailable: 'trūksta plokštelės saugykloje', eye_changed: '4K akis padaryta iš kitos peržiūros', picture_drift: 'paveikslėlis nesutampa su planu',
  design_changed: '4K akys prieštarauja planui', plan_mismatch: 'planas kito stiliaus ar akių skaičiaus', no_engine: 'šiame serveryje nėra variklio', style_rolled_back: 'stilius atšauktas ir užsakymas sulaikytas tavo peržiūrai',
};
export const holdLt = (c: string): string => HOLD_LT[c] || c;

export const HEALTH_LT: Record<string, string> = { styles: 'stilių registras ir plokštelės pakete', plates_4k: '4K plokštelės saugykloje' };
export const ROUTE_LT: Record<string, string> = { manual: 'rankinis kelias (pirkėjas rašo tau)', soon: 'paspaudė „Greitai“ stiliaus pirkimą', blocked: 'pirkimas atmestas (stilius neparduodamas)' };
export const ERROR_ENDPOINT_LT: Record<string, string> = { compose: 'peržiūra', master_compose: '4K kūrinys', order: 'užsakymas', checkout: 'mokėjimas', unknown: 'nežinoma' };
export const REVEAL_LT: Record<string, string> = { ok: 'rodoma', colour: 'nerodoma: spalva pasikeitė', registration: 'nerodoma: nesutapo vaizdai', none: 'nėra', error: 'klaida' };
export const SLICE_MARKET_LT: Record<string, string> = { eu: 'Europos Sąjunga', lt: 'Lietuva', au: 'Australija', hu: 'Vengrija' };
export const SLICE_LANG_LT: Record<string, string> = { en: 'anglų', de: 'vokiečių', lt: 'lietuvių', hu: 'vengrų' };

// ------------------------------------------------------------------------------------------------ numbers (always with n)
const finite = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v);

/** 0.65 -> "65 %", 0.653 -> "65,3 %" (a Lithuanian decimal comma). */
export function fmtPct(rate: number | null | undefined): string {
  if (!finite(rate)) return '-';
  const v = Math.round(rate * 1000) / 10;
  return `${String(v).replace('.', ',')} %`;
}

/** A rate with the count behind it: "65 % (iš 40)". A rate that has no denominator says so instead of "0 %". */
export function rateText(rate: number | null | undefined, n: number | null | undefined, what = 'iš'): string {
  const k = finite(n) ? n : 0;
  if (!finite(rate) || k <= 0) return `nėra duomenų (n 0)`;
  return `${fmtPct(rate)} (${what} ${k})`;
}

/** "12 iš 40 (30 %)". */
export function shareText(k: number, n: number): string {
  return n > 0 ? `${k} iš ${n} (${fmtPct(k / n)})` : `${k} iš 0`;
}

/** A score or a measure with a Lithuanian decimal comma: 4.1 as "4,1". */
export const dec = (v: number | null | undefined): string => (finite(v) ? String(v).replace('.', ',') : '-');

export const msText = (ms: number | null | undefined): string => (finite(ms) ? `${(ms / 1000).toFixed(ms < 10_000 ? 1 : 0).replace('.', ',')} s` : '-');

/** The count of eyes of a range of a style: "1 akis", "3 akys", "4 iki 8 akių". */
export function eyesRangeText(r: readonly [number, number]): string {
  const [a, b] = r;
  return a === b ? ltCount(a, AKYS) : `${a} iki ${b} akių`;
}
export const rangeCounts = (r: readonly [number, number]): number[] => Array.from({ length: Math.max(0, r[1] - r[0] + 1) }, (_, i) => r[0] + i);

// ------------------------------------------------------------------------------------------------ the opening criterion
const WHY_LINE_LT: Record<string, (l: FunnelLine) => string> = {
  n_low: (l) => `per mažai rinkinių (${l.n} iš ${l.need_n} reikalingų)`,
  first_low: (l) => `pirmos nuotraukos praėjimas ${l.first === null ? 'nežinomas' : fmtPct(l.first)}, reikia bent ${fmtPct(l.need_first)}`,
  retake_low: (l) => `su vienu pakartojimu ${l.retake === null ? 'nežinoma' : fmtPct(l.retake)}, reikia bent ${fmtPct(l.need_retake)}`,
};

/** The opening criterion of a count of two or more eyes as a green or red line (spec 1.6.2 rule 2): the numbers with n, and what is not met. A count with no
 *  sets yet is red for n. The line the page shows is the one the server's opening_line makes: this only words it. */
export function openingView(eyes: number, line: FunnelLine | null | undefined): { tone: ViewTone; text: string } {
  if (eyes < 2) return { tone: 'muted', text: 'Vienos akies rinkinys visada turi stilių su perspėjimu, todėl atidarymo kriterijaus nėra.' };
  if (!line) return { tone: 'bad', text: 'Atidarymo kriterijus neįvykdytas: tokių rinkinių dar nebuvo (n 0).' };
  const have = `${ltCount(line.n, RINKINIAI)}, pirmą kartą ${line.first === null ? '-' : fmtPct(line.first)}, ` +
    `su vienu pakartojimu ${line.retake === null ? '-' : fmtPct(line.retake)}`;
  if (line.ok) return { tone: 'good', text: `Atidarymo kriterijus įvykdytas: ${have}.` };
  return { tone: 'bad', text: `Atidarymo kriterijus neįvykdytas: ${have}. Trūksta: ${line.why.map((w) => (WHY_LINE_LT[w] ? WHY_LINE_LT[w](line) : w)).join('; ')}.` };
}

// ------------------------------------------------------------------------------------------------ the switch
/** A row's range of counts in which stages are what the owner can still change. */
export function allowedStages(range: StyleRange): string[] {
  if (!range.switchable || !range.ceiling) return [];
  const top = STAGE_RANK[range.ceiling] ?? 0;
  return ['lab', 'preview', 'live'].filter((s) => (STAGE_RANK[s] ?? 0) <= top);
}

export interface PanelState {
  counts: number[];
  stage: '' | 'lab' | 'preview' | 'live' | 'restore';
  ticks: Record<string, boolean>;          // L1 to L11 as the owner wants them (checked)
  l0: { mean: string; axis: string; by: string };
  waiver: string;
  removeWaiver: boolean;
  reason: string;
  reasonKind: string;
  inFlight: '' | 'finish' | 'hold';
}

export function initialPanel(range: StyleRange): PanelState {
  const ticks: Record<string, boolean> = {};
  for (let i = 1; i <= 11; i++) ticks[`L${i}`] = !!range.checklist[`L${i}`];
  return {
    counts: rangeCounts(range.eyes), stage: '', ticks,
    l0: { mean: '', axis: '', by: '' }, waiver: '', removeWaiver: false, reason: '', reasonKind: 'other', inFlight: '',
  };
}

const num = (t: string): number | null => {
  const s = t.trim().replace(',', '.');
  if (s === '') return null;
  const v = Number(s);
  return Number.isFinite(v) ? v : NaN;
};

/** The effective stage each count would have after the change, for the dialog's sentences: the stage asked for (never above the ceiling); restore removes the
 *  owner's own limit, so the stage is the lower of the ceiling and the catalogue's default (api/_lib/catalogue.py stage_with: preview after the cutover). */
export function stageAfter(range: StyleRange, stage: PanelState['stage'], defaultEffective: string | null = null): StageCode | null {
  if (stage === '') return range.effective;
  if (stage === 'restore') {
    const c = range.ceiling;
    if (!c || !defaultEffective || (STAGE_RANK[c] ?? 0) <= (STAGE_RANK[defaultEffective] ?? 0)) return c;
    return defaultEffective as StageCode;
  }
  return stage;
}

export interface BuiltChange { body: Record<string, unknown> | null; problems: string[]; flips: boolean; lowersOrderable: boolean; empty: boolean; inFlight: 'finish' | 'hold' | null }

/** The request of styles_override a panel makes (api/_lib/stage_overrides.py parse says what it accepts), or the sentences of what is wrong with it. rev is the
 *  revision the page was drawn from; priceTest the running price tests (the dialog then says so and price_test_seen is sent). */
export function buildChange(style: string, range: StyleRange, p: PanelState, rev: number, priceTest: string[], defaultEffective: string | null = null): BuiltChange {
  const problems: string[] = [];
  const body: Record<string, unknown> = { style, eyes: p.counts.length === 1 ? p.counts[0] : p.counts, rev };
  if (!p.counts.length) problems.push('Pasirink bent vieną akių skaičių.');
  if (p.stage) body.stage = p.stage;
  const tick: Record<string, boolean> = {};
  for (let i = 1; i <= 11; i++) {
    const c = `L${i}`;
    if (p.ticks[c] !== !!range.checklist[c]) tick[c] = p.ticks[c];
  }
  if (Object.keys(tick).length) body.tick = tick;
  const mean = num(p.l0.mean), axis = num(p.l0.axis), by = p.l0.by.trim();
  if (mean !== null || axis !== null || by) {
    const ev: Record<string, unknown> = {};
    for (const [k, v, label] of [['mean', mean, 'vidurkis'], ['min_axis', axis, 'silpniausia ašis']] as const) {
      if (v === null) continue;
      if (Number.isNaN(v) || v < 0 || v > 5) problems.push(`L0 ${label}: skaičius nuo 0 iki 5.`);
      else ev[k] = v;
    }
    if (by) ev.by = by;
    if (Object.keys(ev).length) body.evidence = { L0: ev };
  }
  const w = p.waiver.trim();
  if (w) {
    if (w.length < 8 || w.length > 300) problems.push('Rašytinis atsisakymas L0: tavo žodžiais, nuo 8 iki 300 ženklų.');
    else body.waiver = { text: w };
  } else if (p.removeWaiver) body.waiver = false;
  if (p.reason.trim()) body.reason = p.reason.trim().slice(0, 200);
  body.reason_kind = p.reasonKind || 'other';
  const after = stageAfter(range, p.stage, defaultEffective);
  const wasLive = range.effective === 'live';
  const flips = p.stage !== '' && (after === 'live') !== wasLive;
  const lowersOrderable = range.orderable && p.stage !== '' && after !== 'live';
  if (p.stage) body.confirm = true;
  if (flips && priceTest.length) body.price_test_seen = true;
  if (lowersOrderable && p.inFlight) body.in_flight = p.inFlight;
  const empty = !body.stage && !body.tick && !body.evidence && body.waiver === undefined;
  if (empty && !problems.length) problems.push('Nieko nekeičiama: pasirink etapą, pažymėk patikrą, įrašyk vertinimą arba atsisakymą.');
  // what the server does with the paid orders in flight when nothing is chosen: hold when the reason is quality, else let them finish (api/_lib/ops.py act_styles_override)
  const inFlight = lowersOrderable ? (p.inFlight || (p.reasonKind === 'quality' ? 'hold' : 'finish')) : null;
  return { body: problems.length ? null : body, problems, flips, lowersOrderable, empty, inFlight };
}

/** What `live` still lacks once this request is applied: the server's list for the range, less what the request itself supplies (L1 ticked now; L0 by a score that reaches the bar,
 *  with the scorer's name, or by a written waiver). The server decides in the end (409 needs_ticks); this is only so that the dialog does not say "still missing" about what the
 *  same request provides. */
export function missingAfter(range: StyleRange, p: PanelState, bar = { mean: 3.96, min_axis: 3.8 }): string[] {
  const out = range.missing_for_live.filter((c) => {
    if (c === 'L1') return !p.ticks.L1;
    if (c === 'L0') {
      if (p.waiver.trim().length >= 8) return false;
      const old = range.checklist.L0;
      const mean = num(p.l0.mean) ?? old?.score?.mean ?? null;
      const axis = num(p.l0.axis) ?? old?.score?.min_axis ?? null;
      const by = p.l0.by.trim() || old?.director || '';
      return !(mean !== null && axis !== null && !Number.isNaN(mean) && !Number.isNaN(axis) && mean >= bar.mean && axis >= bar.min_axis && by);
    }
    return true;
  });
  return out;
}

/** The dialog's sentences for a change (what the owner reads before he confirms). */
export function changeSummary(row: StyleRow, range: StyleRange, p: PanelState, b: BuiltChange, priceTest: string[], defaultEffective: string | null = null, bar = { mean: 3.96, min_axis: 3.8 }): string {
  const lines: string[] = [];
  const who = `${row.name}, ${eyesText(p.counts)}`;
  if (p.stage) {
    const after = stageAfter(range, p.stage, defaultEffective);
    lines.push(`${who}: dabar galioja „${stageLt(range.effective)}“, po pakeitimo galios „${stageLt(after)}“.`);
    if (after === 'live') lines.push('Pirkėjas galės užsisakyti šį stilių, kai tik bus atidarytas užsakymų priėmimas (jis atidaromas atskirai).');
  } else lines.push(`${who}: etapas nesikeičia.`);
  const body = b.body || {};
  const tick = (body.tick || {}) as Record<string, boolean>;
  const on = Object.keys(tick).filter((c) => tick[c]).map(checkName);
  const off = Object.keys(tick).filter((c) => !tick[c]).map(checkName);
  if (on.length) lines.push(`Pažymima: ${on.join('; ')}.`);
  if (off.length) lines.push(`Nuimama žyma: ${off.join('; ')}.`);
  if (body.evidence) lines.push('Įrašomas nepriklausomo vertinimo (L0) rezultatas.');
  if (body.waiver && body.waiver !== false) lines.push('Įrašomas tavo rašytinis L0 atsisakymas.');
  if (body.waiver === false) lines.push('Šalinamas L0 atsisakymas.');
  if (b.flips && priceTest.length) lines.push('Veikia kainų testas: šis pakeitimas keičia jo imtį. Pakeitimas bus įrašytas ir to testo puslapyje.');
  if (b.lowersOrderable) {
    lines.push(b.inFlight === 'hold'
      ? 'Jau apmokėti užsakymai, kurie dar gaminami šiuo stiliumi, bus sulaikyti tavo peržiūrai.'
      : 'Jau apmokėti užsakymai, kurie dar gaminami šiuo stiliumi, bus baigti kaip įprasta.');
  }
  const lacking = missingAfter(range, p, bar);
  if (range.effective !== 'live' && stageAfter(range, p.stage, defaultEffective) === 'live' && lacking.length) {
    lines.push(`Dar trūksta, serveris tokio pakeitimo nepriims: ${lacking.map(checkName).join('; ')}.`);
  }
  return lines.join('\n');
}

export const eyesText = (counts: number[]): string => {
  if (!counts.length) return 'jokio akių skaičiaus';
  const first = counts[0], last = counts[counts.length - 1];
  const contiguous = counts.every((n, i) => n === first + i);
  if (counts.length === 1) return eyesRangeText([first, first]);
  return contiguous ? eyesRangeText([first, last]) : counts.join(', ') + ' akys';
};

/** What an answer of the switch says about the paid orders that were in flight (spec DE1, WP13a). */
export function heldText(h: StyleHeld | null | undefined): string {
  if (!h) return '';
  const parts = [`Sulaikyta užsakymų: ${h.count}`];
  if (h.checked) parts.push(`patikrinta ${h.checked}`);
  if (h.unread) parts.push(`neperskaityta ${h.unread}`);
  if (h.failed.length) parts.push(`nepavyko sulaikyti ${h.failed.length}`);
  if (h.more) parts.push('pritrūko laiko');
  if (h.error) parts.push(`sustojo dėl klaidos (${h.error})`);
  return parts.join(', ') + '.';
}

// ------------------------------------------------------------------------------------------------ the attention card
export function attentionText(a: AttentionItem, nameOf: (id: string) => string): string {
  const who = a.style ? nameOf(a.style) : '';
  if (a.kind === 'error') return `${who}: klaidų dalis ${rateText(a.rate, a.n)} viršija ribą ${fmtPct(a.limit)}.`;
  if (a.kind === 'review') return `${who}: kūrinių, laukiančių tavo peržiūros, dalis ${rateText(a.rate, a.n)} viršija ribą ${fmtPct(a.limit)}.`;
  if (a.kind === 'gate') return `${who}: akių, nepraėjusių vartų, dalis ${rateText(a.rate, a.n)} viršija ribą ${fmtPct(a.limit)}.`;
  if (a.kind === 'health') return `Sveikatos patikra nepraėjo: ${HEALTH_LT[a.key || ''] || a.key || '?'}.`;
  return `Užsakymų, sulaikytų dėl gamybos žingsnio (${holdLt(a.code || '')}): ${a.n ?? 0}.`;
}

// ------------------------------------------------------------------------------------------------ the audit log
/** "L2@4", "L2@5", "L1@4" as "L1 (4 akys), L2 (4 iki 5 akių)": the ticks of one change grouped by check. */
export function tickGroups(list: string[]): string {
  const by = new Map<string, number[]>();
  for (const t of list) {
    const [code, n] = t.split('@');
    const k = Number(n);
    if (code && Number.isInteger(k)) by.set(code, [...(by.get(code) || []), k]);
  }
  return [...by.entries()].sort((a, b) => Number(a[0].slice(1)) - Number(b[0].slice(1))).map(([c, ns]) => `${c} (${eyesText(ns.sort((a, b) => a - b))})`).join(', ');
}

export function auditText(e: StyleAuditEntry): string {
  if (e.kind === 'limits') return 'Pakeistos dėmesio kortelės ribos.';
  const eyes = e.eyes && e.eyes.length ? eyesText(e.eyes) : '';
  const after = e.effective_after ? Array.from(new Set(Object.values(e.effective_after))).map(stageLt).join(', ') : '';
  const base = `${e.name || e.style || '?'}, ${eyes}`;
  if (e.kind === 'hold') return `${base}: ta pati užklausa pakartota, kad būtų baigtas užsakymų sulaikymas. ${heldText(e.held)}`;
  const bits: string[] = [];
  if (e.stage) bits.push(`etapas ${e.stage === 'restore' ? 'atstatytas iki registro ribos' : `„${stageLt(e.stage)}“`}${after ? ` (galioja: ${after})` : ''}`);
  if (e.ticked && e.ticked.length) bits.push(`pažymėta ${tickGroups(e.ticked)}`);
  if (e.unticked && e.unticked.length) bits.push(`žyma nuimta ${tickGroups(e.unticked)}`);
  if (e.waiver) bits.push(e.waiver === 'set' ? 'įrašytas L0 atsisakymas' : 'L0 atsisakymas pašalintas');
  return `${base}: ${bits.join('; ') || 'pakeitimas'}.`;
}

/** The numbers an audit entry kept of each eye count at the moment of the change, each with its n. */
export function auditNumbers(e: StyleAuditEntry): string[] {
  const out: string[] = [];
  for (const [k, v] of Object.entries(e.numbers || {})) {
    out.push(`${eyesRangeText([Number(k), Number(k)])}: ${ltCount(v.n, RINKINIAI)}, ` +
      `pirmą kartą ${fmtPct(v.first_pass)}, su pakartojimu ${fmtPct(v.with_retake)}${v.partial ? ' (dalis dienų neperskaityta)' : ''}${v.line_ok === null ? '' : v.line_ok ? ', kriterijus įvykdytas' : ', kriterijus neįvykdytas'}`);
  }
  return out;
}

// ------------------------------------------------------------------------------------------------ the catalogue as a list
/** The styles of the catalogue the owner can switch, grouped as the picker groups them; the six legacy ones apart (they are retired and final). */
export function groupedStyles(cat: StyleCatalogue | null): { group: string; label: string; rows: StyleRow[]; fixed: StyleRow[] }[] {
  const rows = (cat?.styles || []).filter((s) => !s.legacy);
  const live = (s: StyleRow) => s.ranges.some((r) => r.switchable);
  return GROUP_ORDER.map((g) => ({ group: g, label: GROUP_LT[g] || g, rows: rows.filter((s) => s.group === g && live(s)), fixed: rows.filter((s) => s.group === g && !live(s)) }))
    .filter((g) => g.rows.length > 0 || g.fixed.length > 0);
}

/** The ids of the styles that have no engine to switch (planned or retired at every count): the gate numbers leave them out. */
export function fixedIds(cat: StyleCatalogue | null): Set<string> {
  return new Set((cat?.styles || []).filter((s) => !s.ranges.some((r) => r.switchable)).map((s) => s.id));
}

/** The per style gate rows grouped by what they have in common (the rule, the policy and the numbers): [{rule, policy, seen, failed, rate, styles: [names]}]. A style the registry only
 *  plans (no engine) is left out when `skip` names it. */
export function gateGroups(rows: { style: string; name: string; policy: string; rule: string; seen: number; failed: number; rate: number | null }[], skip: Set<string> = new Set()) {
  const out = new Map<string, { rule: string; policy: string; seen: number; failed: number; rate: number | null; styles: string[] }>();
  for (const r of rows) {
    if (skip.has(r.style)) continue;
    const k = `${r.rule}|${r.policy}|${r.seen}|${r.failed}`;
    const g = out.get(k) || { rule: r.rule, policy: r.policy, seen: r.seen, failed: r.failed, rate: r.rate, styles: [] };
    if (!g.styles.includes(r.name)) g.styles.push(r.name);
    out.set(k, g);
  }
  return [...out.values()];
}

// ------------------------------------------------------------------------------------------------ what an answer says
export interface Note { tone: ViewTone; text: string; retry?: Record<string, unknown> }

/** The sentence of a refused or failed change: the reason in the owner's words and the facts the server sent with it. */
export function failText(r: Reply<unknown>): string {
  const d = (r.data || {}) as Record<string, unknown>;
  let more = '';
  if (r.reason === 'needs_ticks' && d.missing && typeof d.missing === 'object') {
    more = ' Trūksta: ' + Object.entries(d.missing as Record<string, string[]>).map(([n, c]) => `${eyesText([Number(n)])}: ${c.map((x) => checkName(x)).join(', ')}`).join('; ') + '.';
  } else if (r.reason === 'above_ceiling' && d.ceiling && typeof d.ceiling === 'object') {
    more = ' Registro riba: ' + Object.entries(d.ceiling as Record<string, string>).map(([n, c]) => `${eyesText([Number(n)])} ${stageLt(c)}`).join(', ') + '.';
  } else if (r.reason === 'price_test_running' && Array.isArray(d.keys)) {
    more = ` Veikia testas: ${(d.keys as string[]).join(', ')}.`;
  }
  return explain(r) + more;
}

/** What the answer of a change tells the owner: what holds now, the orders held, a hold that stopped half way (with the request that finishes it: the same one again, in_flight hold,
 *  the NEW revision, because the old one is stale after the owner's own change), a log line that was not written. */
export function changeNote(c: StyleChange, sent: Record<string, unknown>): Note {
  const stages = Array.from(new Set(Object.values(c.effective))).map(stageLt).join(', ');
  const parts: string[] = [];
  if (c.result === 'changed') parts.push(`Pakeista: ${c.view.name}, ${eyesText(c.eyes)}: dabar galioja „${stages}“.`);
  else if (c.result === 'ticked') parts.push(`Įrašyta: ${c.view.name}, ${eyesText(c.eyes)}. Etapas nesikeitė: galioja „${stages}“.`);
  else parts.push(`Nieko nepasikeitė: ${c.view.name}, ${eyesText(c.eyes)} (galioja „${stages}“).`);
  if (c.held) parts.push(heldText(c.held));
  else if (c.in_flight === 'finish') parts.push('Jau apmokėti užsakymai baigiami kaip įprasta.');
  if (c.price_test && c.price_test.length) parts.push(`Pakeitimas įrašytas ir kainų testo puslapyje (${c.price_test.join(', ')}).`);
  let tone: ViewTone = 'good';
  let retry: Record<string, unknown> | undefined;
  if (c.held && c.held.incomplete) {
    tone = 'warn';
    parts.push('Sulaikymas nebaigtas: pakartok tą pačią užklausą, ir bus sulaikyti likę užsakymai (jau sulaikytų nelies).');
    retry = { ...sent, in_flight: 'hold', confirm: true, rev: c.rev };
  }
  if (c.audit_written === false) {
    tone = 'warn';
    parts.push('Pakeitimas išsaugotas, bet žurnalo įrašas neįrašytas.');
  }
  return { tone, text: parts.join(' '), retry };
}

/** The filter select's value ("market:au", "lang:lt" or "") as the request's one filter. */
export function filterBody(v: string): Record<string, string> {
  const [k, x] = v.split(':');
  return (k === 'market' || k === 'lang') && x ? { [k]: x } : {};
}

// ------------------------------------------------------------------------------------------------ the order detail
type J = Record<string, unknown>;
const rec = (v: unknown): J => (v && typeof v === 'object' && !Array.isArray(v) ? (v as J) : {});
const asText = (v: unknown): string => (typeof v === 'string' ? v : typeof v === 'number' || typeof v === 'boolean' ? String(v) : '');
const asNum = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null);
const pct1 = (v: number): string => `${String(Math.round(v * 1000) / 10).replace('.', ',')} %`;

/** The part of a stored path that is relative to the order's folder, or null when it is not inside it (orders/<order>/draft/eye_1_preview.jpg gives draft/eye_1_preview.jpg). */
export function relPath(order: string, p: unknown): string | null {
  const pre = `orders/${order}/`;
  return typeof p === 'string' && p.startsWith(pre) && p.length > pre.length ? p.slice(pre.length) : null;
}

/** The options of the style as the plan recorded them: the look, swap (two eyes) and rotate (three or more). */
export function optionsText(plan: J): string {
  const o = rec(plan.opts);
  const n = typeof plan.eyes === 'number' ? plan.eyes : 0;
  const parts: string[] = [];
  if (o.look) parts.push(`vaizdas (look): ${asText(o.look)}`);
  if (n === 2) parts.push(`akys sukeistos vietomis (swap): ${o.swap === true ? 'taip' : 'ne'}`);
  if (n >= 3) parts.push(`pasukimas (rotate): ${typeof o.rotate === 'number' ? o.rotate : 0}`);
  return parts.join('; ') || 'nėra (stiliaus pagrindinės)';
}

/** The checks of an artwork record's selfcheck as [code, ok, short detail]. */
export function selfcheckRows(art: J | null): [string, boolean, string][] {
  const checks = rec(rec(art?.selfcheck).checks);
  return Object.entries(checks).map(([k, c]) => {
    const o = rec(c);
    const bits: string[] = [];
    if (asNum(o.bad) !== null) bits.push(`netinkamų taškų ${o.bad}`);
    if (asNum(o.violations) !== null) bits.push(`pažeidimų ${o.violations}`);
    if (asNum(o.count) !== null) bits.push(`${o.count}`);
    if (asNum(o.share) !== null) bits.push(`dalis ${pct1(o.share as number)}`);
    if (Array.isArray(o.shares)) bits.push(`dalys ${(o.shares as unknown[]).map((v) => (asNum(v) === null ? '-' : pct1(v as number))).join(', ')}`);
    return [k, o.ok === true, bits.join(', ')];
  });
}

/** The edge mode of every contact (the collision family: a dark edge, or a hairline for dark eyes), from the facts the picture recorded. */
export function edgeText(art: J | null): string {
  const em = rec(rec(art?.facts).edge_modes);
  const keys = Object.keys(em);
  return keys.length ? keys.map((k) => `sąlytis ${k}: ${EDGE_LT[asText(em[k])] || asText(em[k])}`).join('; ') : '-';
}

/** Every text this module holds that the page prints, for the page test's scan (the Lithuanian rules of scripts/check_texts.mjs). */
export function allWords(): string[] {
  const out: string[] = [];
  const add = (o: Record<string, unknown>) => { for (const v of Object.values(o)) if (typeof v === 'string') out.push(v); else if (v && typeof v === 'object') add(v as Record<string, unknown>); };
  [SELFCHECK_LT, EDGE_LT, PLAN8_NOTE_LT, STAGE_LT, STAGE_ABOUT_LT, GROUP_LT, GATE_POLICY_LT, PRICE_CLASS_LT, CLASS_LT, PUPIL_LT, CHECK_LT, L0_STATE_LT, REASON_KIND_LT, GATE_CODE_LT, FALLBACK_LT, WHAT_LT, TILE_WHY_LT,
    HOLD_LT, HEALTH_LT, ROUTE_LT, ERROR_ENDPOINT_LT, REVEAL_LT, SLICE_MARKET_LT, SLICE_LANG_LT].forEach(add);
  return out;
}
