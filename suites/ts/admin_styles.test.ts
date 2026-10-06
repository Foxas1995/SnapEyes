// WP13b (I16, I17, I22): the Stiliai page of the admin panel as it is printed and as it decides, with the real components rendered on the server (react-dom/server) and the pure functions of
// src/admin/stylesView.ts called as the page calls them: the request a panel makes (the ticks that changed, the score with its bar, the waiver, the in flight choice, the price test line, the
// revision), the sentences of the dialog, what an answer says (the orders held, a hold that stopped half way and its retry), the opening criterion with the n behind it, the tables on a phone
// and on a wide screen, the order detail's style block, and the Lithuanian rules of scripts/check_texts.mjs over every sentence the page prints (no dash, no double space, no space before a
// full stop, no straight double quote, no lower case "jus" form, no flagged wording, no English word, no written price). Pure page code, loaded through Vite's module runner by
// scripts/run_ts_tests.mjs; returns its results.
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import type { FunnelLine, FunnelRow, OrderDetail, Reply, StepsView, StyleCatalogue, StyleChange, StyleRange, StyleRow, StylesStats } from '../../src/admin/api';
import { ArtworkFacts } from '../../src/admin/ArtworkFacts';
import { OrderStyle } from '../../src/admin/OrderStyle';
import { ChosenBlock, DemandBlock, FunnelBlock, GateBlock, TimesBlock } from '../../src/admin/StyleNumbers';
import { RangePanel, StyleCard, type SwitchCtx } from '../../src/admin/StyleSwitch';
import { StylesPage } from '../../src/admin/Styles';
import { isFirstN } from '../../src/admin/groupEyes';
import { Tbl } from '../../src/admin/ui';
import {
  allowedStages, allWords, attentionText, auditNumbers, auditText, buildChange, changeNote, changeSummary, edgeText, eyesRangeText, eyesText, failText, filterBody, fixedIds, fmtPct, gateGroups,
  groupedStyles, heldText, initialPanel, missingAfter, openingView, optionsText, rateText, relPath, selfcheckRows, shareText, stageAfter, tickGroups, type PanelState,
} from '../../src/admin/stylesView';

type Row = [string, boolean, string?];

const range = (o: Partial<StyleRange> = {}): StyleRange => ({
  eyes: [1, 1], ceiling: 'live', override: null, effective: 'live', orderable: true, switchable: true, checklist: {}, waiver: null, missing_for_live: [], l0: null, ...o,
});
const row = (id: string, name: string, o: Partial<StyleRow> = {}): StyleRow => ({
  id, name, group: 'solo', legacy: false, eyes: [1, 1], gate: 'advisory', price_class: 'art', built: true, ranges: [range()], last: null, ...o,
});
const CHECKS = Array.from({ length: 12 }, (_, i) => `L${i}`);
const cat = (rows: StyleRow[], o: Partial<StyleCatalogue> = {}): StyleCatalogue => ({
  rev: 7, at: null, checks: CHECKS, limits: { min_n: 20, error_rate: 0.05, review_rate: 0.1, gate_fail_rate: 0.6 }, l0_bar: { mean: 3.96, min_axis: 3.8 }, default_effective: null,
  fallback_stage: 'preview', registry_hash: 'abc123', ordering_open: false, price_test: [], orderable_max_eyes: 3, styles: rows, ...o,
});
const line = (o: Partial<FunnelLine> = {}): FunnelLine => ({ ok: true, n: 41, need_n: 30, first: 0.65, need_first: 0.5, retake: 0.95, need_retake: 0.75, why: [], ...o });
const frow = (eyes: number, o: Partial<FunnelRow> = {}): FunnelRow => ({
  eyes, cls: null, first: 40, first_pass: 26, unknown: 0, retake1: 20, retake1_pass: 12, retake2: 0, retake2_pass: 0, fails: { lid_sectors_outer: 14 }, rate_first: 0.65, rate_retake: 0.95,
  line: eyes >= 2 ? line({ n: 40 }) : null, ...o,
});
const stats = (o: Partial<StylesStats> = {}): StylesStats => ({
  days: 30, partial: false, recording: true, market: null, lang: null, limits: { min_n: 20, error_rate: 0.05, review_rate: 0.1, gate_fail_rate: 0.6 }, health: { styles: true, plates_4k: false },
  requests: { total: 120, drew_nothing: 40 }, funnel: [frow(1), frow(2), frow(3, { first: 12, first_pass: 3, rate_first: 0.25, rate_retake: 0.25, line: line({ ok: false, n: 12, first: 0.25, retake: 0.25, why: ['n_low', 'first_low', 'retake_low'] }) })],
  funnel_by_class: [frow(2, { cls: 'grey' })], opening: { '2': line({ n: 40 }) },
  demand: [{ style: 'solo.radiance', name: 'Radiance', eyes: 1, stage: 'preview', tiles: 4, large: 2, soon: 3, blocked: 1 }], chosen: { pick: 3, other: 5, share: 0.375 },
  chosen_by_class: [{ cls: 'grey', pick: 1, other: 3, n: 4, share: 0.25 }], previews: [{ style: 'solo.gold', name: 'Celestial Gold', previews: 9, tiles: 20 }],
  conversion: { recorded: false, rows: [{ style: 'solo.gold', name: 'Celestial Gold', eyes: 1, previews: 20, started: 0, paid: 0, rate_started: 0, rate_paid: null }] },
  after_failure: [{ eyes: 1, started: 5, paid: 2, started_failed: 1, paid_failed: 0, by_code: {}, share_paid_failed: 0 }],
  fallbacks: [{ style: 'duo.collision_infinity', name: 'Collision Infinity', fallback: 'stack_contrast', count: 4, of: 30, share: 0.1333 }],
  times: [{ what: 'art', style: 'solo.gold', name: 'Celestial Gold', eyes: 1, n: 8, p50_ms: 12000, p95_ms: 32000, over: 0, need_s: 26.1 }],
  busy_retry: [], errors: [{ style: 'solo.gold', name: 'Celestial Gold', errors: 2, asked: 40, rate: 0.05 }], qa: [], review: [{ style: 'solo.gold', name: 'Celestial Gold', review: 1, made: 8, rate: 0.125 }],
  gate: { codes: { ok: 20, lid: 4 }, reasons: { lid_sectors_outer: 4 }, classes: { own: 10, grey: 14 }, pupils: { round: 20, bar: 4 }, by_style: [
    { style: 'solo.clean', name: 'Clean Iris', policy: 'advisory', rule: 'lid', seen: 24, failed: 4, rate: 0.1667 }, { style: 'solo.gold', name: 'Celestial Gold', policy: 'advisory', rule: 'lid', seen: 24, failed: 4, rate: 0.1667 },
    { style: 'duo.universe', name: 'Universe Duo', policy: 'hard', rule: 'fill', seen: 24, failed: 2, rate: 0.0833 }] },
  holds: { style_step_too_big: 1 }, master: { made_by_style: {}, fallback: {} }, help: { routes: { manual: 2, soon: 3 }, why: { bar_pupil: 2 }, eyes: { '2': 2 } },
  reveal: { codes: { ok: 6, colour: 2 }, n: 8, ok_share: 0.75, ms: 140.5 }, attention: [], memory: { peak_mb_avg: 481.6, n: 20, peak_mb_is: 'vmrss_increase_over_the_step', hwm_is: 'x' },
  filter: { slice: null, sliced: [], whole: [] }, ...o,
});

const reply = (status: number, reason: string, data: Record<string, unknown> = {}): Reply<unknown> => ({ ok: false, status, data, reason, error: '', ms: 1 });
const noop = () => undefined;
const text = (h: string) => h.replace(/<pre[\s\S]*?<\/pre>/g, ' ').replace(/<[^>]*>/g, ' ').replace(/&amp;/g, '&').replace(/&#x27;/g, "'").replace(/&quot;/g, '"').replace(/\s+/g, ' ').trim();

// the Lithuanian rules of scripts/check_texts.mjs (lint, LT_LOWER_JUS, LT_FLAGGED), the dash rule, and the words that mean a sentence was never translated
const D = (cs: number[]) => new RegExp('[' + String.fromCharCode(...cs) + ']');
const DASH = D([0x2012, 0x2013, 0x2014, 0x2015]);
const LT = 'A-Za-zĄČĘĖĮŠŲŪŽąčęėįšųūž';
const LOWER_JUS = new RegExp(`(^|[^${LT}])(j${String.fromCharCode(0x16b)}s|j${String.fromCharCode(0x16b, 0x173)}|jums|jus|jumis)(?![${LT}])`, 'u');
const FLAGGED = new RegExp(`(^|[^${LT}])(matosi|matyt${String.fromCharCode(0x173)}si|mat${String.fromCharCode(0x117)}si|ilgojoje kraštinėje|niekas nekuriama|privalomas pasiūlymas|iš principo|pilno dydžio|pilnai|priklausomai nuo|pagal ką|įtakoja|Gerb\\.)(?![${LT}])`, 'iu');
const ENGLISH = /\b(the|and|with|for|are|not|price|test|style|stage|live|ceiling|override|tick|admin|retake|click|button|save|cancel|error)\b/i;
const INVISIBLE = new RegExp('[' + [[0x200b, 0x200f], [0x2028, 0x202e], [0x2060, 0x2064], [0xfeff, 0xfeff]].map(([a, b]) => String.fromCharCode(a) + '-' + String.fromCharCode(b)).join('') + ']');
const PRICE = /\d+[.,]\d\d\s?(EUR|eur|A\$|Ft)|A\$\s?\d|\d\s?Ft\b|€/;
const lint = (raw: string): string[] => {
  const s = raw.replace(/admin-v\d+/g, 'raktas');     // the attribution of a tick is the admin key's kind, a code and not a sentence
  const bad: string[] = [];
  if (DASH.test(s)) bad.push('dash');
  if (INVISIBLE.test(s)) bad.push('invisible');
  if (/ {2}/.test(s)) bad.push('double space');
  if (/ \./.test(s)) bad.push('space before full stop');
  if (s.includes('"')) bad.push('straight quote');
  if (LOWER_JUS.test(s)) bad.push('lower case jus');
  if (FLAGGED.test(s)) bad.push('flagged wording');
  const en = ENGLISH.exec(s);
  if (en) bad.push(`English word "${en[0]}"`);
  if (PRICE.test(s)) bad.push('written price');
  return bad;
};

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);

  // ------------------------------------------------------------------------------------------------ numbers always come with their n
  check('fmtPct: a Lithuanian decimal comma, whole percents without one, nothing is "-"', fmtPct(0.65) === '65 %' && fmtPct(0.653) === '65,3 %' && fmtPct(1) === '100 %' && fmtPct(null) === '-' && fmtPct(NaN) === '-');
  check('rateText: a rate is printed with the count behind it, and a rate with no denominator says so instead of "0 %"',
    rateText(0.65, 40) === '65 % (iš 40)' && rateText(0.5, 0) === 'nėra duomenų (n 0)' && rateText(null, 40) === 'nėra duomenų (n 0)' && rateText(0, 12) === '0 % (iš 12)', rateText(0.65, 40));
  check('shareText: "26 iš 40 (65 %)" and "0 iš 0"', shareText(26, 40) === '26 iš 40 (65 %)' && shareText(0, 0) === '0 iš 0');
  check('eye counts take the Lithuanian forms: 1 akis, 2 akys, 10 akių, 21 akis, 12 akių, and a range',
    eyesRangeText([1, 1]) === '1 akis' && eyesRangeText([2, 2]) === '2 akys' && eyesRangeText([10, 10]) === '10 akių' && eyesRangeText([21, 21]) === '21 akis' && eyesRangeText([12, 12]) === '12 akių'
    && eyesRangeText([4, 8]) === '4 iki 8 akių' && eyesText([3]) === '3 akys' && eyesText([4, 5, 6]) === '4 iki 6 akių' && eyesText([3, 5]) === '3, 5 akys', `${eyesText([3, 5])}`);

  // ------------------------------------------------------------------------------------------------ the opening criterion (spec 1.6.2 rule 2)
  const ok = openingView(2, line());
  const red = openingView(3, line({ ok: false, n: 12, first: 0.4, retake: 0.9, why: ['n_low', 'first_low'] }));
  check('the opening line is green and says the numbers with n when the criterion is met', ok.tone === 'good' && ok.text === 'Atidarymo kriterijus įvykdytas: 41 rinkinys, pirmą kartą 65 %, su vienu pakartojimu 95 %.', ok.text);
  check('it is red and says what is not met, each with its number and its bar (n low, first photo low)',
    red.tone === 'bad' && red.text.includes('12 rinkinių') && red.text.includes('per mažai rinkinių (12 iš 30 reikalingų)') && red.text.includes('pirmos nuotraukos praėjimas 40 %, reikia bent 50 %') && !red.text.includes('su vienu pakartojimu 90 %, reikia'), red.text);
  check('a count with no sets yet is red for n; one eye has no criterion (a one eye set always has a style to buy)',
    openingView(2, null).tone === 'bad' && openingView(2, null).text.includes('n 0') && openingView(1, null).tone === 'muted' && openingView(1, line()).tone === 'muted');

  // ------------------------------------------------------------------------------------------------ the request a panel makes
  const r3 = range({ eyes: [3, 3], ceiling: 'live', effective: 'preview', override: 'preview', orderable: false, missing_for_live: ['L1', 'L0'] });
  const mk = (r: StyleRange, patch: Partial<PanelState> = {}): PanelState => ({ ...initialPanel(r), ...patch });
  let p = mk(r3, { stage: 'live', ticks: { ...initialPanel(r3).ticks, L1: true }, waiver: 'Nepriklausomo vertinimo nelauksiu' });
  let b = buildChange('x', r3, p, 7, []);
  check('buildChange: a stage and the ticks that CHANGED and the waiver, the revision the page saw, confirm only because a stage changes, the reason kind; one count is a number',
    JSON.stringify(b.body) === JSON.stringify({ style: 'x', eyes: 3, rev: 7, stage: 'live', tick: { L1: true }, waiver: { text: 'Nepriklausomo vertinimo nelauksiu' }, reason_kind: 'other', confirm: true }) && b.flips && !b.lowersOrderable && b.inFlight === null, JSON.stringify(b.body));
  p = mk(r3, { l0: { mean: '4,1', axis: '3.9', by: ' Vera ' } });
  b = buildChange('x', r3, p, 7, []);
  check('buildChange: the score of L0 takes a Lithuanian comma, is sent as evidence with the scorer, and no stage means no confirm',
    JSON.stringify((b.body || {}).evidence) === JSON.stringify({ L0: { mean: 4.1, min_axis: 3.9, by: 'Vera' } }) && !('confirm' in (b.body || {})) && !('stage' in (b.body || {})), JSON.stringify(b.body));
  check('buildChange: a score outside 0 to 5 or not a number is a sentence, not a request; one number alone is accepted (the server merges)',
    buildChange('x', r3, mk(r3, { l0: { mean: '6', axis: '', by: '' } }), 7, []).body === null && buildChange('x', r3, mk(r3, { l0: { mean: 'abc', axis: '', by: '' } }), 7, []).problems[0].includes('L0')
    && JSON.stringify(buildChange('x', r3, mk(r3, { l0: { mean: '4', axis: '', by: '' } }), 7, []).body?.evidence) === JSON.stringify({ L0: { mean: 4 } }));
  check('buildChange: a waiver of fewer than 8 or more than 300 characters is a sentence; removing the existing one sends false',
    buildChange('x', r3, mk(r3, { waiver: 'abc' }), 7, []).problems.length === 1 && buildChange('x', r3, mk(r3, { waiver: 'a'.repeat(301) }), 7, []).problems.length === 1
    && (buildChange('x', range({ waiver: { at: 'a', by: 'b', text: 'texttext' } }), mk(r3, { removeWaiver: true }), 7, []).body || {}).waiver === false);
  b = buildChange('x', r3, mk(r3), 7, []);
  check('buildChange: nothing to change is a sentence (no request is sent), and no counts chosen is one too', b.body === null && b.empty && b.problems[0].startsWith('Nieko nekeičiama') && buildChange('x', r3, mk(r3, { counts: [], stage: 'lab' }), 7, []).problems.length === 1);
  const live1 = range({ checklist: { L1: { ticked_at: 'a', by: 'b' } } });
  check('buildChange: unticking a check sends false; an unchanged tick is not sent; counts of a range may be narrowed',
    JSON.stringify((buildChange('x', live1, mk(live1, { ticks: { ...initialPanel(live1).ticks, L1: false } }), 7, []).body || {}).tick) === JSON.stringify({ L1: false })
    && !('tick' in (buildChange('x', live1, mk(live1, { stage: 'lab' }), 7, []).body || {}))
    && JSON.stringify((buildChange('x', range({ eyes: [4, 8] }), mk(range({ eyes: [4, 8] }), { counts: [4, 5], stage: 'lab' }), 7, []).body || {}).eyes) === '[4,5]');
  const orderable = range({ ceiling: 'live', effective: 'live', orderable: true });
  const lowQ = buildChange('x', orderable, mk(orderable, { stage: 'preview', reasonKind: 'quality' }), 7, ['extra_eye_eur']);
  const lowO = buildChange('x', orderable, mk(orderable, { stage: 'preview', reasonKind: 'other' }), 7, []);
  const lowC = buildChange('x', orderable, mk(orderable, { stage: 'preview', reasonKind: 'quality', inFlight: 'finish' }), 7, []);
  check('taking an orderable style back: the quality reason holds the paid orders in flight, any other lets them finish, the owner may choose either; only the choice he made is sent',
    lowQ.lowersOrderable && lowQ.inFlight === 'hold' && lowO.inFlight === 'finish' && lowC.inFlight === 'finish' && !('in_flight' in (lowQ.body || {})) && (lowC.body || {}).in_flight === 'finish');
  check('a running price test: a flip sends price_test_seen (the dialog said so), a change that flips nothing does not',
    (lowQ.body || {}).price_test_seen === true && lowQ.flips && !('price_test_seen' in (buildChange('x', orderable, mk(orderable, { ticks: { ...initialPanel(orderable).ticks, L2: true } }), 7, ['extra_eye_eur']).body || {})));
  check('restore removes the owner\'s limit: with a default stage of preview a live style comes back as preview (a flip, a lowering); with no default it is the ceiling',
    stageAfter(orderable, 'restore', 'preview') === 'preview' && stageAfter(orderable, 'restore', null) === 'live' && stageAfter(range({ ceiling: 'lab' }), 'restore', 'preview') === 'lab'
    && buildChange('x', orderable, mk(orderable, { stage: 'restore' }), 7, [], 'preview').lowersOrderable && !buildChange('x', orderable, mk(orderable, { stage: 'restore' }), 7, [], null).flips);
  check('allowedStages: nothing above the ceiling is offered, and a planned or retired style offers nothing',
    JSON.stringify(allowedStages(range({ ceiling: 'preview' }))) === '["lab","preview"]' && JSON.stringify(allowedStages(range({ ceiling: 'live' }))) === '["lab","preview","live"]'
    && allowedStages(range({ ceiling: 'planned', switchable: false })).length === 0 && JSON.stringify(allowedStages(range({ ceiling: 'lab' }))) === '["lab"]');

  // ------------------------------------------------------------------------------------------------ the sentences
  const rowX = row('solo.clean', 'Clean Iris');
  const sumLive = changeSummary(rowX, r3, mk(r3, { stage: 'live' }), buildChange('x', r3, mk(r3, { stage: 'live' }), 7, ['extra_eye_eur']), ['extra_eye_eur']);
  check('the dialog says what changes, that a price test is running and what it still lacks (the server would refuse)',
    sumLive.includes('dabar galioja „Greitai (peržiūra)“, po pakeitimo galios „Parduodamas“') && sumLive.includes('Veikia kainų testas: šis pakeitimas keičia jo imtį') && sumLive.includes('Dar trūksta, serveris tokio pakeitimo nepriims: Tavo žvilgsnis')
    && sumLive.includes('(L1)') && sumLive.includes('(L0)'), sumLive);
  const sup = mk(r3, { stage: 'live', ticks: { ...initialPanel(r3).ticks, L1: true }, waiver: 'Nepriklausomo vertinimo nelauksiu' });
  const sumOk = changeSummary(rowX, r3, sup, buildChange('x', r3, sup, 7, []), []);
  check('...and does not say "still lacks" about what the same request supplies (L1 ticked now, L0 waived in words)', !sumOk.includes('Dar trūksta') && sumOk.includes('Pažymima:') && sumOk.includes('rašytinis L0 atsisakymas'), sumOk);
  const lowText = changeSummary(rowX, orderable, mk(orderable, { stage: 'preview', reasonKind: 'quality' }), lowQ, ['extra_eye_eur']);
  check('taking a style back says what happens to the paid orders in flight (held for quality)', lowText.includes('bus sulaikyti tavo peržiūrai') && changeSummary(rowX, orderable, mk(orderable, { stage: 'preview' }), lowO, []).includes('bus baigti kaip įprasta'), lowText);
  check('missingAfter: L1 ticked and L0 waived, or L0 scored over the bar with a name, supply what live lacks; a score under the bar or without a name does not',
    missingAfter(r3, sup).length === 0 && missingAfter(r3, mk(r3, { ticks: { ...initialPanel(r3).ticks, L1: true }, l0: { mean: '4', axis: '3.9', by: 'Vera' } })).length === 0
    && JSON.stringify(missingAfter(r3, mk(r3, { ticks: { ...initialPanel(r3).ticks, L1: true }, l0: { mean: '3.5', axis: '3.9', by: 'Vera' } }))) === '["L0"]'
    && JSON.stringify(missingAfter(r3, mk(r3, { l0: { mean: '4', axis: '3.9', by: '' } }))) === '["L1","L0"]');
  check('failText: a refusal carries the facts the server sent (what is missing per count, the ceiling, the running test), in the owner\'s words',
    failText(reply(409, 'needs_ticks', { missing: { '3': ['L1', 'L0'] } })).includes('Trūksta: 3 akys: Tavo žvilgsnis') && failText(reply(409, 'above_ceiling', { ceiling: { '1': 'preview' } })).includes('Registro riba: 1 akis Greitai (peržiūra).')
    && failText(reply(409, 'price_test_running', { keys: ['extra_eye_eur'] })).includes('extra_eye_eur') && failText(reply(409, 'stale_view')).includes('perkrauk puslapį') && failText({ ...reply(0, ''), data: null }).includes('Serveris neatsakė'));
  const held = { count: 2, orders: ['a', 'b'], checked: 14, more: false, failed: [], unread: 0, error: null, incomplete: false };
  const view = row('solo.clean', 'Clean Iris');
  const chg = (o: Partial<StyleChange> = {}): StyleChange => ({ result: 'changed', style: 'solo.clean', eyes: [1], rev: 9, before: { '1': null }, after: { '1': 'preview' }, effective: { '1': 'preview' }, ceiling: { '1': 'live' }, l0: { '1': null },
    in_flight: 'hold', held, audit_written: true, view, ...o });
  const n1 = changeNote(chg(), { style: 'solo.clean', eyes: 1, stage: 'preview', rev: 8 });
  check('changeNote: what holds now, the orders held, and a plain success is green with nothing to retry', n1.tone === 'good' && n1.text.includes('dabar galioja „Greitai (peržiūra)“') && n1.text.includes('Sulaikyta užsakymų: 2, patikrinta 14') && n1.retry === undefined, n1.text);
  const n2 = changeNote(chg({ held: { ...held, count: 1, failed: ['c'], incomplete: true } }), { style: 'solo.clean', eyes: 1, stage: 'preview', rev: 8 });
  check('changeNote: a hold that stopped half way is a warning with the retry (the same request again, in_flight hold, the NEW revision: the old one is stale after our own change)',
    n2.tone === 'warn' && n2.text.includes('nepavyko sulaikyti 1') && n2.text.includes('Sulaikymas nebaigtas') && n2.retry?.in_flight === 'hold' && n2.retry?.rev === 9 && n2.retry?.confirm === true && n2.retry?.stage === 'preview', JSON.stringify(n2.retry));
  const n3 = changeNote(chg({ audit_written: false, held: null, in_flight: null, result: 'ticked' }), { style: 'solo.clean', eyes: 1, tick: { L1: true }, rev: 8 });
  check('changeNote: a log line that could not be written is a warning that says the change stands; a tick says the stage did not change', n3.tone === 'warn' && n3.text.includes('žurnalo įrašas neįrašytas') && n3.text.includes('Etapas nesikeitė'), n3.text);
  check('heldText: counts and what went wrong (unread, failed, out of time, an exception) and nothing for no hold',
    heldText(null) === '' && heldText({ ...held, unread: 3, failed: ['c', 'd'], more: true, error: 'OSError', incomplete: true }) === 'Sulaikyta užsakymų: 2, patikrinta 14, neperskaityta 3, nepavyko sulaikyti 2, pritrūko laiko, sustojo dėl klaidos (OSError).');
  const nameOf = (id: string) => ({ 'solo.gold': 'Celestial Gold' } as Record<string, string>)[id] || id;
  check('attentionText: an error, a review and a gate rate over its limit (with n), a failing health boolean, orders held for a step',
    attentionText({ kind: 'error', style: 'solo.gold', rate: 0.1, n: 40, limit: 0.05 }, nameOf) === 'Celestial Gold: klaidų dalis 10 % (iš 40) viršija ribą 5 %.'
    && attentionText({ kind: 'review', style: 'solo.gold', rate: 0.2, n: 10, limit: 0.1 }, nameOf).includes('laukiančių tavo peržiūros') && attentionText({ kind: 'gate', style: 'solo.gold', rate: 0.7, n: 30, limit: 0.6 }, nameOf).includes('nepraėjusių vartų')
    && attentionText({ kind: 'health', key: 'plates_4k' }, nameOf) === 'Sveikatos patikra nepraėjo: 4K plokštelės saugykloje.' && attentionText({ kind: 'hold', code: 'style_step_too_big', n: 2 }, nameOf).includes('gamybos žingsnis per didelis'));
  const ent = { kind: 'override' as const, name: 'Family Colours', style: 'grp.collision', eyes: [4, 5, 6], stage: 'live', effective_after: { '4': 'live', '5': 'live', '6': 'live' }, ticked: ['L2@4', 'L2@5', 'L1@4'], unticked: [],
    numbers: { '4': { n: 24, first_pass: 1, with_retake: 1, unknown: 0, line_ok: false, why: ['n_low'] }, '5': { n: 1, first_pass: null, with_retake: null, unknown: 0, line_ok: null, why: [], partial: true } } };
  check('tickGroups and auditText: the ticks of one change grouped by check; the stage and what held after it; auditNumbers keep each count with its n (a partial reading says so)',
    tickGroups(['L2@4', 'L2@5', 'L1@4']) === 'L1 (4 akys), L2 (4 iki 5 akių)' && auditText(ent).includes('etapas „Parduodamas“ (galioja: Parduodamas)') && auditText(ent).includes('pažymėta L1 (4 akys), L2 (4 iki 5 akių)')
    && auditNumbers(ent)[0].startsWith('4 akys: 24 rinkiniai, pirmą kartą 100 %') && auditNumbers(ent)[0].endsWith('kriterijus neįvykdytas') && auditNumbers(ent)[1].includes('dalis dienų neperskaityta') && auditText({ kind: 'limits' }) === 'Pakeistos dėmesio kortelės ribos.');

  // ------------------------------------------------------------------------------------------------ catalogue helpers
  const fixedRow = row('duo.reflection', 'Reflection', { group: 'duo', eyes: [2, 2], ranges: [range({ eyes: [2, 2], ceiling: 'planned', effective: 'planned', orderable: false, switchable: false })] });
  const c2 = cat([row('solo.clean', 'Clean Iris'), fixedRow, row('celestial_gold', 'Celestial Gold', { legacy: true })]);
  const gr = groupedStyles(c2);
  check('groupedStyles: the switchable styles by group in the picker\'s order, a planned one in the group\'s fixed list, the legacy six not at all; fixedIds names the planned',
    gr.length === 2 && gr[0].group === 'solo' && gr[0].rows.length === 1 && gr[0].fixed.length === 0 && gr[1].group === 'duo' && gr[1].rows.length === 0 && gr[1].fixed[0].id === 'duo.reflection'
    && fixedIds(c2).has('duo.reflection') && !fixedIds(c2).has('solo.clean'));
  const gg = gateGroups(stats().gate.by_style, new Set(['duo.universe']));
  check('gateGroups: styles with the same rule, policy and numbers are one row, and a style the registry only plans is left out', gg.length === 1 && gg[0].styles.join() === 'Clean Iris,Celestial Gold' && gateGroups(stats().gate.by_style).length === 2);
  check('filterBody: one filter at a time, a market or a language, nothing for the empty one or a malformed one',
    JSON.stringify(filterBody('market:au')) === '{"market":"au"}' && JSON.stringify(filterBody('lang:en')) === '{"lang":"en"}' && JSON.stringify(filterBody('')) === '{}' && JSON.stringify(filterBody('moon:x')) === '{}');
  check('isFirstN: the stored masters of a lab order are eyes 1 to n with no gap', isFirstN([1, 2, 3]) && isFirstN([2, 1]) && !isFirstN([1, 3]) && !isFirstN([]) && !isFirstN([2]));

  // ------------------------------------------------------------------------------------------------ the page as printed
  const ctxOf = (c: StyleCatalogue, s: StylesStats | null): SwitchCtx => ({ call: (async () => reply(0, '')) as never, cat: c, stats: s, onChanged: noop, setConfirm: noop, report: noop, reload: noop });
  const withPair = row('duo.kiss_collision', 'Kiss Collision', { group: 'duo', eyes: [2, 2], gate: 'hard', ranges: [range({ eyes: [2, 2], ceiling: 'preview', effective: 'preview', orderable: false, missing_for_live: ['L1', 'L0'], l0: 'below_bar',
    checklist: { L0: { ticked_at: '2026-10-05T10:00:00Z', by: 'admin-v1', score: { mean: 3.5, min_axis: 3.2 }, director: 'Vera' } } })] });
  const multi = row('grp.collision', 'Family Colours', { group: 'grp', eyes: [3, 8], gate: 'hard', ranges: [range({ eyes: [3, 3] }), range({ eyes: [4, 8], ceiling: 'preview', effective: 'preview', orderable: false })] });
  const planned = row('grp.clean', 'Clean Family', { group: 'grp', eyes: [3, 8], ranges: [range({ eyes: [3, 8], ceiling: 'planned', effective: 'planned', orderable: false, switchable: false })] });
  const cc = cat([row('solo.clean', 'Clean Iris', { ranges: [range({ override: 'live', checklist: { L1: { ticked_at: '2026-10-05T10:00:00Z', by: 'admin-v1' } }, waiver: { at: '2026-10-05T10:00:00Z', by: 'admin-v1', text: 'Sprendžiu pats' }, l0: 'waiver' })],
    last: { by: 'admin-v1', at: '2026-10-05T10:00:00Z', reason: 'pirmasis', reason_kind: 'other' } }), withPair, multi, planned], { price_test: ['extra_eye_eur'] });
  const st = stats();
  const html = (e: Parameters<typeof renderToStaticMarkup>[0]) => renderToStaticMarkup(e);
  const hClean = html(createElement(StyleCard, { row: cc.styles[0], ctx: ctxOf(cc, st) }));
  check('a style card: name, id, eye range, gate policy and price class; the ceiling, the owner\'s own limit, what holds now and whether it can be bought; L0 and L1 with who and when; the last change',
    ['Clean Iris', 'solo.clean', 'vartai tik perspėja', 'meninė kaina', 'registro riba: Parduodamas', 'mano riba: Parduodamas', 'dabar galioja: Parduodamas', 'perkamas', 'atsisakyta raštu', 'Sprendžiu pats',
      'L1 tavo žvilgsnis į galutinius kūrinius', 'pažymėta', 'Paskutinis pakeitimas', 'pirmasis'].every((x) => text(hClean).includes(x)), text(hClean).slice(0, 700));
  const hPair = text(html(createElement(StyleCard, { row: withPair, ctx: ctxOf(cc, st) })));
  check('a pair\'s card: the score under the bar is shown as recorded and not counted (with the scorer and the numbers in a Lithuanian comma), what live still lacks, and the opening criterion beside the switch with its n',
    hPair.includes('vertinimas žemiau kartelės: įrašytas, bet neįskaitomas') && hPair.includes('vidurkis 3,5, silpniausia ašis 3,2, vertino Vera') && hPair.includes('Kad taptų „Parduodamas“, dar trūksta: Tavo žvilgsnis')
    && hPair.includes('2 akys: Atidarymo kriterijus įvykdytas: 40 rinkinių') && hPair.includes('neperkamas'), hPair.slice(0, 900));
  const hMulti = text(html(createElement(StyleCard, { row: multi, ctx: ctxOf(cc, st) })));
  check('a style with two ranges has a row for each; counts above the first hold the opening lines in one fold with how many are green', hMulti.includes('3 akys') && hMulti.includes('4 iki 8 akių') && hMulti.includes('Atidarymo kriterijus pagal akių skaičių: įvykdytas 0 iš 5'), hMulti.slice(0, 900));
  const hPlan = html(createElement(StyleCard, { row: planned, ctx: ctxOf(cc, st) }));
  check('a planned style cannot be switched: the button is disabled and the sentence says it is the registry\'s change', hPlan.includes('disabled=""') && text(hPlan).includes('Perjungti negalima: stilius suplanuotas arba išjungtas'));
  const noStats = text(html(createElement(StyleCard, { row: withPair, ctx: ctxOf(cc, null) })));
  check('before the numbers arrive the opening line says they are loading, it never shows a made up number', noStats.includes('Atidarymo kriterijaus skaičiai kraunami') && !noStats.includes('Atidarymo kriterijus įvykdytas'));
  const hPanel = html(createElement(RangePanel, { row: withPair, range: withPair.ranges[0], ctx: ctxOf(cc, st), onClose: noop }));
  const tp = text(hPanel);
  check('the panel: the stage choices up to the ceiling only (a note says why Parduodamas is missing), restore, L0 with its inputs and the waiver, L1 to L11 each with its hint, and the price test line is not there until a flip',
    tp.includes('Etapas (registro riba: Greitai (peržiūra))') && !tp.includes('Parduodamas: pirkėjas gali užsisakyti') && tp.includes('„Parduodamas“ pasirinkti negalima: registro riba žemesnė') && tp.includes('Atstatyti pradinę būseną')
    && tp.includes('Vidurkis (0 iki 5)') && tp.includes('Arba tavo rašytinis atsisakymas L0') && CHECKS.slice(1).every((c) => tp.includes(`(${c})`)) && !tp.includes('Veikia kainų testas'), tp.slice(0, 500));
  check('the panel names the range and has the two buttons; a range of several counts offers each count', tp.includes('Peržiūrėti ir patvirtinti') && html(createElement(RangePanel, { row: multi, range: multi.ranges[1], ctx: ctxOf(cc, st), onClose: noop })).includes('aria-pressed="true"'));

  // the numbers
  const fb = text(html(createElement(FunnelBlock, { s: st })));
  check('the funnel: per eye count the sets with n, the first photo pass as "k of n", the retake as an upper bound with n, the reasons, and the opening criterion green or red; the by-class table too',
    fb.includes('40 rinkinių') && fb.includes('26 iš 40 (65 %)') && fb.includes('95 % (iš 40)') && fb.includes('voko ar blakstienų sektoriai išorėje: 14') && fb.includes('Atidarymo kriterijus įvykdytas')
    && fb.includes('Atidarymo kriterijus neįvykdytas: 12 rinkinių') && fb.includes('pilkos') && fb.includes('viršutinė riba'), fb.slice(0, 600));
  const tbl = html(createElement(Tbl, { head: ['A', 'B'], rows: [['1', '2']], label: 'Bandymas' }));
  check('Tbl: a table on a wide screen (it scrolls inside itself) and one block per row on a phone, each value under its heading; no data is a sentence',
    tbl.includes('md:hidden') && tbl.includes('<table') && tbl.includes('overflow-x-auto') && tbl.includes('<dt class="text-white/55">A</dt>') && html(createElement(Tbl, { head: ['A'], rows: [], label: 'x' })).includes('Nėra duomenų.'));
  const dm = text(html(createElement(DemandBlock, { s: st })));
  check('demand for a style that cannot be bought yet: tiles, large previews, clicks on its buy button, refused checkouts; and the manual route clicks',
    dm.includes('Radiance') && dm.includes('Greitai') && dm.includes('rankinis kelias (pirkėjas rašo tau): 2') && dm.includes('paspaudė „Greitai“ stiliaus pirkimą: 3'), dm.slice(0, 500));
  const ch = text(html(createElement(ChosenBlock, { s: st, cat: cc })));
  check('previews by style with the group, tiles apart from large previews, and the recommended tile against the others with n', ch.includes('Celestial Gold') && ch.includes('Grupė') && ch.includes('37,5 % (iš 8)') && ch.includes('25 % (iš 4)'), ch.slice(0, 400));
  const tm = text(html(createElement(TimesBlock, { s: st })));
  check('render times: p50 and p95 against the estimate (a p95 over the plan is flagged), the memory is the INCREASE of VmRSS and says so', tm.includes('32 s, viršija planą') && tm.includes('26,1 s') && tm.includes('481,6 MB (n 20)') && tm.includes('VmRSS') && tm.includes('VmHWM'), tm.slice(0, 500));
  const gt = text(html(createElement(GateBlock, { s: st, skip: new Set(['duo.universe']) })));
  check('the gate by style groups the equal rows and leaves out a planned style', gt.includes('Clean Iris, Celestial Gold') && !gt.includes('Universe Duo') && gt.includes('Vyzdžio klasės'), gt.slice(0, 400));
  const page = text(html(createElement(StylesPage, { call: (async () => reply(0, '')) as never })));
  check('the page renders its frame before the numbers arrive (no effect has run): the title, how it works, the attention card and the catalogue, a loading line, and no number', page.includes('Stiliai') && page.includes('Kaip čia viskas veikia') && page.includes('Dėmesio kortelė')
    && page.includes('Katalogas ir perjungiklis') && page.includes('Kraunama'));

  // the order detail's style block
  const plan = { style: 'duo.kiss_collision', eyes: 2, opts: { swap: true }, fallback: 'overlap_fallback', plan8: 'b10f218e', plates_needed: [{ id: 'P-1', family: 'JET', bytes: 2_000_000, sha256: 'a'.repeat(64) }] };
  const art = { width: 4096, height: 2732, bytes: 1_600_000, design_used: 'kiss', seed: '6113', qa: { ok: true }, times: { total: 5.7 }, needs_review: false, rerun: 0, engine_v: 4, pv: 1, reg: 'abc',
    facts: { edge_modes: { '0': 'hairline' }, plates: ['P-1'] }, selfcheck: { ok: true, checks: { t1: { ok: true, bad: 0 }, t3: { ok: false, shares: [1, 0.8] }, seam: { ok: true }, t19: { ok: true } } } };
  const steps = { plan, steps: [{ name: 'art', kind: 'art', done: { step: 'art', ms: 7300, cpu_s: 7.1, peak_mb: 412, hwm_mb: 684, outputs: [{ path: 'orders/o/artwork_x.jpg', bytes: 1_600_000, sha12: 'abc' }] }, try: null }],
    rerun: 0, progress: { done: 1, of: 1, step: null }, locks: {}, capacity: null, factor: 1.6, registry_hash: 'abc', engine_v: 4,
    eyes: [{ eye: 1, eye_id: 'e1', cls: 'own', pupil: 'round', gate: { lid: false, fill: true }, gate_why: { lid: ['lid_sectors_outer'], fill: [] } }, { eye: 2, eye_id: 'e2', cls: 'grey', pupil: 'bar', gate: { lid: true, fill: null }, gate_why: { lid: [], fill: [] } }], artwork: art } as unknown as StepsView;
  const od = { order: 'o', state: 'ready', lab: false, paid: true, count: 2, email: null, consent: null, files: [{ path: 'style/plan.json' }, { path: 'style/done_art.json' }, { path: 'draft/eye_1_preview.jpg' }],
    records: { 'order.json': { checkout: { gate: 'lid_sectors_outer', plan8_shown: true, plan8_page: '0123abcd', plan8_note: 'pixel_choices', plan: { plan8: 'b10f218e' } } }, 'delivery.json': { key: 'orders/o/artwork_x.jpg' },
      'draft/eye_1.json': { preview: { path: 'orders/o/draft/eye_1_preview.jpg' } } }, eyes: [{ eye: 1, draft: {}, master: null }], artworks: [], payments: [], refunds: [], log: [], can: { email: false, stripe: false, link: false, counts: true } } as unknown as OrderDetail;
  const os = text(html(createElement(OrderStyle, { d: od, steps, call: (async () => reply(0, '')) as never })));
  check('the order detail\'s style block: the options (swap), the fallback, the gate at checkout and per eye with its reasons, the plan\'s identity at checkout against the one the page showed and the note, the checks T1 to T19 and the seam, the size, the time, the memory as an increase with the HWM beside it, the edge mode, the plates, the intermediates and the comparison button',
    os.includes('akys sukeistos vietomis (swap): taip') && os.includes('persidengimo atsarginis variantas') && os.includes('voko ar blakstienų sektoriai išorėje') && os.includes('Akis 2: klasė pilkos, vyzdys horizontali juosta')
    && os.includes('0123abcd') && os.includes('serverio planas liko galioti') && os.includes('T1 rainelė nepaliesta: gerai') && os.includes('T3 matoma rainelės dalis: nepraėjo (dalys 100 %, 80 %)') && os.includes('siūlė tarp rainelių: gerai')
    && os.includes('4096 x 2732 px, 1,5 MB') && os.includes('+412 MB (proceso VmRSS padidėjimas per žingsnį), instancijos aukščiausia reikšmė (VmHWM) 684 MB') && os.includes('sąlytis 0: plona linija') && os.includes('P-1')
    && os.includes('Tarpinių vaizdų (žingsnių rėmų) nėra') && os.includes('Parodyti peržiūrą ir failą'), os.slice(0, 900));
  check('relPath and optionsText: a path inside the order\'s folder is made relative (anything else is null); options print only the ones that apply to the eye count',
    relPath('o', 'orders/o/draft/x.jpg') === 'draft/x.jpg' && relPath('o', 'orders/p/draft/x.jpg') === null && relPath('o', 5) === null && relPath('o', 'orders/o/') === null
    && optionsText({ eyes: 2, opts: { swap: true } }) === 'akys sukeistos vietomis (swap): taip' && optionsText({ eyes: 4, opts: { rotate: 2, look: 'vortex' } }) === 'vaizdas (look): vortex; pasukimas (rotate): 2' && optionsText({ eyes: 1, opts: {} }) === 'nėra (stiliaus pagrindinės)');
  check('selfcheckRows and edgeText: every check of the record with its ok and short details; the edge mode of every contact; nothing is "-"',
    selfcheckRows(art).length === 4 && selfcheckRows(art)[1][1] === false && selfcheckRows(null).length === 0 && edgeText(art) === 'sąlytis 0: plona linija' && edgeText(null) === '-');
  check('ArtworkFacts without a record says so instead of an empty block', text(html(createElement(ArtworkFacts, { art: null }))).includes('Kūrinio įrašo nėra'));

  // ------------------------------------------------------------------------------------------------ Lithuanian
  const printed = [text(hClean), hPair, hMulti, text(hPlan), noStats, tp, fb, dm, ch, tm, gt, page, os, sumLive, sumOk, lowText, n1.text, n2.text, n3.text, failText(reply(409, 'needs_ticks', { missing: { '3': ['L1'] } })),
    ...allWords(), ...stats().attention.map((a) => attentionText(a, nameOf)), auditText(ent), ...auditNumbers(ent), openingView(2, line()).text, red.text, openingView(2, null).text];
  const problems = printed.map((s) => ({ s, bad: lint(s) })).filter((x) => x.bad.length).map((x) => `${x.bad.join('+')}: ${x.s.slice(0, 90)}`);
  check('every sentence the page prints (the dictionaries, the dialog, the answers, the rendered cards, tables and blocks) passes the Lithuanian rules of the text check and holds no dash, no written price, no English word', problems.length === 0, problems.slice(0, 5).join(' | '));
  check('the names of all twelve checks and every stage, class and hold code have a word in the dictionaries', CHECKS.every((c) => allWords().some((w) => w.includes(`(${c})`))) && Object.keys(stats().gate.codes).every((c) => attentionText({ kind: 'hold', code: c, n: 1 }, nameOf).length > 0));
  return out;
}
