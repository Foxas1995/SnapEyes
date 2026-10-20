// The owner's visitor pages (2026-10-20): the words, the shares, the funnel bars, the cross tab cards, the traffic lights of the ads plan, the CSV and the Lithuanian text of the pages. Pure page
// code (src/admin/traffic.ts) and the pieces rendered on the server (TrafficUi.tsx, Ads.tsx ReportCard), loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results.
import { readFileSync } from 'node:fs';
import { createElement as h } from 'react';
import { fmtMoney } from '../../src/admin/format';
import { renderToStaticMarkup } from 'react-dom/server';
import {
  adRows, bars, campText, centsOf, chain, eur, fromDay, fxLines, groupLt, groupsOf, inApp, keyText, marketOfTerm, moneyText, netOf, cardOf, pctText, phase0, phase0Decision, phase1, rate, rollup, rowsFor,
  share, sourcesCsv, toCsv, totalsOf, valueLt, type AdRow, type Fx, type SrcRow,
} from '../../src/admin/traffic';
import { FilterBar, FunnelBars, FxCard, Light } from '../../src/admin/TrafficUi';
import { ReportCard } from '../../src/admin/Ads';
import { ordersOf } from '../../src/admin/DailyCard';

type Row = [string, boolean, string?];
const read = (p: string) => readFileSync(new URL(`../../${p}`, import.meta.url), 'utf8');
const html = (el: Parameters<typeof renderToStaticMarkup>[0]) => renderToStaticMarkup(el);

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);

  check('rate: a share needs a denominator; share() prints the count behind it, and says so when there is none', rate(1, 4) === 0.25 && rate(1, 0) === null && share(12, 40) === '12 iš 40 (30 %)' && share(0, 0) === 'nėra duomenų (0)', share(12, 40));
  const steps = { landing: 100, try: 60, photo: 30, result: 24, buy: 6, order: 3 };
  const b = bars(steps, ['landing', 'try', 'photo', 'result', 'buy', 'order']);
  check('the funnel bars: each step as a share of the first and of the step before it, and what was lost', b[0].ofTop === 1 && b[1].ofPrev === 0.6 && b[2].ofPrev === 0.5 && b[5].ofTop === 0.03 && Math.abs((b[2].lost ?? 0) - 0.5) < 1e-9 && b[0].lost === null);
  check('a step with nothing before it has no share (no division by zero)', bars({ landing: 0, try: 3 }, ['landing', 'try'])[1].ofPrev === null && chain({ a: 0, b: 5 }, ['a', 'b'])[1].share === null);
  check('pctText: a bound of the histogram in seconds, "virš ribos" above the last one, nothing when empty', pctText({ ms: 12000, over: false, n: 5 }) === '12 s' && pctText({ ms: null, over: true, n: 3 }) === 'virš ribos' && pctText({ ms: null, over: false, n: 0 }) === 'nėra duomenų' && pctText(undefined) === 'nėra duomenų');
  check('money is printed per currency and never added across them: euros first, forints whole', moneyText({ huf: 699000, eur: 7491 }) === `${fmtMoney(7491, 'eur')}; ${fmtMoney(699000, 'huf')}` && moneyText({}) === '-' && moneyText(undefined) === '-', moneyText({ huf: 699000, eur: 7491 }));
  check('keyText: a source, its medium and as much of the campaign as the level has; empty parts are named', keyText({ src: 'fb', med: 'paid', cmp: 'se-p0-test', trm: 'lt-a1-eye', cnt: 'a1-lt-s1' }, 'cnt') === 'Facebook (reklama) / mokama / se-p0-test / lt-a1-eye / a1-lt-s1'
    && keyText({ src: 'direct', med: '', cmp: '', trm: '', cnt: '' }, 'cmp') === 'Tiesiogiai / be kampanijos' && keyText({ src: '', med: '', cmp: '', trm: '', cnt: '' }, 'src') === 'Be šaltinio');
  check('campText: an order\'s packed code in words, empty parts left out', campText('fb|paid|se-p0-test|lt-a1-eye|a1-lt-s1') === 'Facebook (reklama) / mokama / se-p0-test / lt-a1-eye / a1-lt-s1' && campText('tiktok|org|o-plan||') === 'TikTok / organika / o-plan' && campText(null) === '');
  check('the Facebook and Instagram apps\' browsers are marked as in-app (the ads plan\'s gate G4), Chrome and Safari are not', inApp('fb') && inApp('ig') && inApp('tt') && inApp('wv') && !inApp('chrome') && !inApp('safari'));

  const fx: Fx = { en_gate: { ok: { all: 30, fb: 12, ig: 18 }, lid: { all: 6, fb: 6 } }, en_reason: { lid_colour_wedge: { all: 5, fb: 5 }, fill_void: { all: 1, fb: 1 } }, set_retake: { '0': { all: 24 }, '1': { all: 12 } } };
  check('fxLines: a metric\'s values, largest first, each with its total and its groups', fxLines(fx, 'en_gate').map((l) => `${l.value}:${l.total}`).join() === 'ok:30,lid:6' && fxLines(fx, 'nothing').length === 0);
  check('groupsOf: the groups of a split, largest first, without "all", at most the number asked', groupsOf(fx, ['en_gate', 'en_reason']).join() === 'fb,ig' && groupsOf(fx, ['en_gate'], 1).join() === 'fb');
  check('valueLt: the words of a value (verdict, block reason, gate, retry, resolution, orientation, retakes), and the code itself when no word is known',
    valueLt('an_verdict', 'weak') === 'Silpna' && valueLt('an_block', 'too_blurry') === 'Per neryški' && valueLt('en_gate', 'lid') === 'Voko taisyklė' && valueLt('en_retry', 'kept2') === 'Antra restauracija išlaikyta'
    && valueLt('an_res', 'mp_8_16') === '8-16 MP' && valueLt('an_ori', 'square') === 'Kvadratinė' && valueLt('set_retake', '1') === 'Po vieno pakartojimo' && valueLt('en_cls', 'dark_brown') === 'Tamsiai ruda' && valueLt('xyz', 'abc') === 'abc');
  check('groupLt: a device, a browser or a campaign in words', groupLt('dev', 'ios') === 'iPhone / iPad' && groupLt('br', 'fb') === 'Facebook programa' && groupLt('cmp', 'fb / se-p0-test') === 'Facebook (reklama) / se-p0-test' && groupLt('cmp', 'fb / -') === 'Facebook (reklama) / be kampanijos' && groupLt(null, 'all') === 'Viso');

  const md = html(h(FxCard, { title: 'Atkūrimo vartai', fx, metric: 'en_gate', by: 'br', groups: ['fb', 'ig'] }));
  check('the cross tab card prints every share with its n (12 iš 18 (67 %) of the Facebook app\'s eyes), names the groups and the values in words', md.includes('Facebook programa') && md.includes('Instagram programa') && md.includes('30 iš 36 (83,3 %)') && md.includes('Voko taisyklė') && md.includes('6 iš 18 (33,3 %)'), md.slice(0, 400));
  check('a card with no data says so', html(h(FxCard, { title: 'Tuščia', fx: {}, metric: 'x', by: null, groups: [] })).includes('Dar nėra duomenų'));
  const fb = html(h(FunnelBars, { steps, order: ['landing', 'try', 'photo', 'result', 'buy', 'order'], title: 'Piltuvas' }));
  check('the funnel bars render the steps in order with their counts, the share of the first step and what was lost since the step before', fb.indexOf('Nusileidimai') < fb.indexOf('Atidarė /try') && fb.indexOf('Atidarė /try') < fb.indexOf('Paspaudė pirkti') && fb.includes('Atkrito 50 % nuo ankstesnio žingsnio') && fb.includes('(60 % nuo pirmo)'));
  const lt = html(h(Light, { tone: 'bad', label: 'Kaina už užbaigtą peržiūrą', text: '5,00 €' }));
  check('a traffic light is a word and a number, never a colour alone', lt.includes('bloga') && lt.includes('5,00') && html(h(Light, { tone: 'muted', label: 'x', text: 'nėra duomenų' })).includes('nėra duomenų'));
  const fbar = html(h(FilterBar, { days: 30, setDays: () => undefined, filters: { dev: 'ios' }, setFilters: () => undefined, available: { market: ['eu', 'lt'], lang: ['lt'], dev: ['ios', 'android'], br: ['fb'], src: [], cmp: [] } }));
  check('the filter bar: the periods with the chosen one pressed, the menus with what the counts hold, the chosen value selected', fbar.includes('aria-pressed="true"') && fbar.includes('Viskas (90 d.)') && fbar.includes('Lietuva') && fbar.includes('Facebook programa') && /<option value="ios" selected/.test(fbar) || fbar.includes('selected=""'), fbar.slice(0, 300));
  check('and shows only the filters the page can answer', !html(h(FilterBar, { days: 7, setDays: () => undefined, filters: {}, setFilters: () => undefined, available: undefined, only: ['dev'] })).includes('Rinka'));

  // the spend and the lights
  const ledger: AdRow[] = [
    { id: 'a1a1a1a1', day: '2026-10-21', src: 'meta', cmp: 'se-p0-test', trm: 'lt-a1-eye', cnt: 'a1-lt-s1', amount: 250, vat: false, impr: 1200, clicks: 18 },
    { id: 'b2b2b2b2', day: '2026-10-22', src: 'meta', cmp: 'se-p0-test', trm: 'lt-a1-eye', cnt: 'a1-lt-s1', amount: 363, vat: true },
    { id: 'c3c3c3c3', day: '2026-10-22', src: 'meta', cmp: 'se-p0-test', trm: 'de-win', amount: 400, vat: false },
    { id: 'd4d4d4d4', day: '2026-09-01', src: 'meta', cmp: 'old', amount: 999, vat: false },
  ];
  check('Ads Manager\'s figure has no VAT, the card pays 21 percent more: a typed card amount is divided, an Ads Manager amount multiplied (rounded to the cent)', netOf(ledger[1]) === 300 && cardOf(ledger[1]) === 363 && netOf(ledger[0]) === 250 && cardOf(ledger[0]) === 303 && eur(300).startsWith('3,00'));
  check('rowsFor: a row with only a campaign belongs to the campaign alone, one with an ad set also to the ad set, one with an advertisement to it too; the window starts at its day',
    rowsFor(ledger, { cmp: 'se-p0-test', trm: '', cnt: '' }, 'cmp', '2026-10-01').length === 3 && rowsFor(ledger, { cmp: 'se-p0-test', trm: 'lt-a1-eye', cnt: '' }, 'trm', '2026-10-01').length === 2
    && rowsFor(ledger, { cmp: 'se-p0-test', trm: 'lt-a1-eye', cnt: 'a1-lt-s1' }, 'cnt', '2026-10-01').length === 2 && rowsFor(ledger, { cmp: 'se-p0-test', trm: 'de-win', cnt: 'a1-lt-s1' }, 'cnt', '2026-10-01').length === 0
    && rowsFor(ledger, { cmp: 'old', trm: '', cnt: '' }, 'cmp', '2026-10-01').length === 0);
  const t = totalsOf(ledger.slice(0, 2));
  check('totalsOf: the spend in Ads Manager euros, the card total, the impressions and clicks, and whether they were typed at all', t.spend === 550 && t.card === 666 && t.impr === 1200 && t.clicks === 18 && t.hasClicks && t.hasImpr && !totalsOf([ledger[1]]).hasClicks);

  const healthy = phase0({ spend: 400, card: 484, impr: 10000, clicks: 130, hasClicks: true, hasImpr: true, rows: 3 }, { landing: 110, en: 20, rs: 14 }, 'lt');
  const byKey = (ls: ReturnType<typeof phase0>) => Object.fromEntries(ls.map((l) => [l.key, l.tone]));
  check('phase 0, a healthy LT campaign: CTR 1,3 %, CPC 3,08 euros, 85 % landing, 18 % started, 70 % completed, 28,57 euros... the cost of a completed preview is judged in euros: 4 euros / 14 = 0,29 is green',
    JSON.stringify(byKey(healthy)) === JSON.stringify({ ctr: 'good', cpc: 'good', landing: 'good', started: 'good', done: 'good', perdone: 'good' }), JSON.stringify(byKey(healthy)));
  const poor = phase0({ spend: 3000, card: 3630, impr: 10000, clicks: 40, hasClicks: true, hasImpr: true, rows: 3 }, { landing: 18, en: 100, rs: 30 }, 'lt');
  check('phase 0, a poor campaign: CTR 0,4 % bad, CPC 0,75 euros amber, landing 45 % bad, started 556 % (more starts than visits is a counting difference, green), completed 30 % bad, 1,00 euro per completed preview green',
    byKey(poor).ctr === 'bad' && byKey(poor).cpc === 'warn' && byKey(poor).landing === 'bad' && byKey(poor).done === 'bad' && byKey(poor).perdone === 'good', JSON.stringify(byKey(poor)));
  const none = phase0({ spend: 0, card: 0, impr: 0, clicks: 0, hasClicks: false, hasImpr: false, rows: 0 }, {}, null);
  check('phase 0 with nothing typed and nothing counted: every light is grey and says there is no data (a light is never green or red on nothing)', none.every((l) => l.tone === 'muted' && l.text === 'nėra duomenų'), JSON.stringify(none));
  check('the cost of a completed preview in LT: up to 2 euros green, up to 4 amber, above red; other markets by the ratio to LT\'s (DE up to 2,5 times, HU up to 1,2 times green; DE above 3 times red)',
    phase0({ spend: 600, card: 0, impr: 0, clicks: 0, hasClicks: false, hasImpr: false, rows: 1 }, { rs: 3 }, 'lt').find((l) => l.key === 'perdone')?.tone === 'good'
    && phase0({ spend: 900, card: 0, impr: 0, clicks: 0, hasClicks: false, hasImpr: false, rows: 1 }, { rs: 3 }, 'lt').find((l) => l.key === 'perdone')?.tone === 'warn'
    && phase0({ spend: 1500, card: 0, impr: 0, clicks: 0, hasClicks: false, hasImpr: false, rows: 1 }, { rs: 3 }, 'lt').find((l) => l.key === 'perdone')?.tone === 'bad'
    && phase0({ spend: 1000, card: 0, impr: 0, clicks: 0, hasClicks: false, hasImpr: false, rows: 1 }, { rs: 2 }, 'de', 200).find((l) => l.key === 'perdone')?.tone === 'good'
    && phase0({ spend: 1800, card: 0, impr: 0, clicks: 0, hasClicks: false, hasImpr: false, rows: 1 }, { rs: 2 }, 'de', 200).find((l) => l.key === 'perdone')?.tone === 'bad'
    && phase0({ spend: 220, card: 0, impr: 0, clicks: 0, hasClicks: false, hasImpr: false, rows: 1 }, { rs: 1 }, 'hu', 200).find((l) => l.key === 'perdone')?.tone === 'good'
    && phase0({ spend: 500, card: 0, impr: 0, clicks: 0, hasClicks: false, hasImpr: false, rows: 1 }, { rs: 1 }, 'hu', 200).find((l) => l.key === 'perdone')?.tone === 'warn');
  check('phase 1: CPA up to 12 euros and ROAS from 1,8 are green, CPA up to 15 and ROAS from 1,5 amber, worse red, no orders grey',
    JSON.stringify(phase1(2400, 2, 4500).map((l) => l.tone)) === JSON.stringify(['good', 'good']) && JSON.stringify(phase1(3000, 2, 4800).map((l) => l.tone)) === JSON.stringify(['warn', 'warn'])
    && JSON.stringify(phase1(6000, 2, 4000).map((l) => l.tone)) === JSON.stringify(['bad', 'bad']) && phase1(500, 0, 0)[0].tone === 'muted');
  const dec1 = phase0Decision(12, 7, 300, 60, 100);
  const dec2 = phase0Decision(12, 7, 500, 60, 100);
  const dec3 = phase0Decision(12, 7, null, 0, 0);
  check('the decision at the end of phase 0: all numbers met is a yes, one missed a no, unknown inputs are not a no (the owner is asked for the clicks)', dec1.ok === true && dec2.ok === false && dec3.ok === null && dec2.lines[2].ok === false, JSON.stringify([dec1.ok, dec2.ok, dec3.ok]));

  const card = html(h(ReportCard, {
    row: { key: { src: '', med: '', cmp: 'se-p0-test', trm: 'lt-a1-eye', cnt: '' }, steps: { landing: 110, try: 70, en: 20, rs: 14, buy: 2, soon: 3 }, orders: 2, revenue: { eur: 4494 } },
    level: 'trm', ledger, from: '2026-10-01', vat: 1.21, ltCost: null,
  }));
  const want = [eur(550), eur(666), 'Kaina už užsakymą', eur(275), 'Grąža (ROAS)', 'Kaina už užbaigtą', 'Kaina už užsakymą (CPA)'];
  check('the campaign card: spend in Ads Manager euros and from the card, the costs per step, the lights of phase 0 and phase 1 (there are orders)', want.every((x) => card.includes(x)), `missing: ${want.filter((x) => !card.includes(x)).join(' | ')}`);

  const r1: SrcRow[] = [{ key: { src: 'fb', med: 'paid', cmp: 'c', trm: 't1', cnt: 'a' }, steps: { landing: 5 }, orders: 1, revenue: { eur: 100 } }, { key: { src: 'ig', med: 'paid', cmp: 'c', trm: 't1', cnt: 'a' }, steps: { landing: 3, try: 2 }, orders: 0, revenue: {} },
    { key: { src: 'fb', med: 'paid', cmp: 'c', trm: 't2', cnt: 'b' }, steps: { landing: 1 }, orders: 0, revenue: {} }];
  const ro = rollup(r1, 'trm');
  check('rollup: the same advertisement on Facebook and Instagram is one row (Meta bills a campaign, not a placement), the steps and the revenue added', ro.length === 2 && ro[0].key.trm === 't1' && ro[0].steps.landing === 8 && ro[0].steps.try === 2 && ro[0].orders === 1 && ro[0].revenue?.eur === 100 && rollup(r1, 'cmp').length === 1);
  // the Reklamos page is about advertising: the counter's rows of utm_medium paid and the campaigns with spend, plus the spend that has no visit counted
  const mixed: SrcRow[] = [{ key: { src: 'fb', med: 'paid', cmp: 'c1', trm: 'lt-a', cnt: 'x' }, steps: { landing: 5, rs: 2 }, orders: 0, revenue: {} }, { key: { src: 'ig', med: 'bio', cmp: 'o-plan', trm: '', cnt: '' }, steps: { landing: 9 }, orders: 1, revenue: { eur: 1997 } },
    { key: { src: 'direct', med: '', cmp: '', trm: '', cnt: '' }, steps: { landing: 3 }, orders: 0, revenue: {} }, { key: { src: 'tiktok', med: 'org', cmp: 'c3', trm: '', cnt: '' }, steps: { landing: 2 }, orders: 0, revenue: {} }];
  const led2: AdRow[] = [{ id: 'a0000001', day: '2026-10-10', src: 'meta', cmp: 'c3', amount: 100, vat: false }, { id: 'a0000002', day: '2026-10-10', src: 'meta', cmp: 'only-spend', trm: 'lt-b', cnt: 'y', amount: 200, vat: false },
    { id: 'a0000003', day: '2026-09-01', src: 'meta', cmp: 'old', amount: 300, vat: false }];
  const ac = adRows(mixed, led2, 'cmp', '2026-10-01').map((r) => r.key.cmp).sort();
  check('adRows: the paid rows and the campaigns with spend in the window are advertising; organic links, visits without a code and spend before the window are not; spend with no visit counted gets a row of nothing',
    JSON.stringify(ac) === JSON.stringify(['c1', 'c3', 'only-spend']), JSON.stringify(ac));
  const at = adRows(mixed, led2, 'trm', '2026-10-01');
  const ai = adRows(mixed, led2, 'cnt', '2026-10-01');
  check('adRows at the ad set and the advertisement level keep the names down to that level, and the row of nothing carries its ad set and advertisement',
    at.some((r) => r.key.cmp === 'only-spend' && r.key.trm === 'lt-b' && r.key.cnt === '' && r.steps.landing === undefined) && ai.some((r) => r.key.cmp === 'only-spend' && r.key.trm === 'lt-b' && r.key.cnt === 'y') && at.filter((r) => r.key.cmp === 'c1').length === 1);
  check('a ledger row without an ad set belongs to a card whose ad set is empty (undefined and empty are the same)', rowsFor([{ id: 'a0000004', day: '2026-10-10', src: 'meta', cmp: 'k', amount: 5, vat: false }], { cmp: 'k', trm: '', cnt: '' }, 'trm', '2026-10-01').length === 1
    && rowsFor([{ id: 'a0000004', day: '2026-10-10', src: 'meta', cmp: 'k', amount: 5, vat: false }], { cmp: 'k', trm: '', cnt: '' }, 'cnt', '2026-10-01').length === 1);
  const unspent = phase0({ spend: 0, card: 0, impr: 0, clicks: 0, hasClicks: false, hasImpr: false, rows: 0 }, { landing: 40, en: 10, rs: 6 }, 'lt');
  check('with no spend typed the cost lights are grey ("nėra duomenų"), never a green 0,00 euros', unspent.filter((l) => l.key === 'perdone' || l.key === 'cpc').every((l) => l.tone === 'muted' && l.text === 'nėra duomenų'), JSON.stringify(unspent));
  const bare = html(h(ReportCard, { row: { key: { src: 'fb', med: 'paid', cmp: 'no-spend', trm: '', cnt: '' }, steps: { landing: 40, en: 10, rs: 6 }, orders: 1, revenue: { eur: 1997 } }, level: 'cmp', ledger: [], from: '2026-10-01', vat: 1.21, ltCost: null }));
  check('a card of a campaign with no spend typed says "nėra įrašų" and has no cost per step and no phase 1 lights', bare.includes('nėra įrašų') && !bare.includes('Kaina už užsakymą (CPA)') && !bare.includes(eur(0)), bare.slice(0, 300));
  check('marketOfTerm follows the plan\'s names; centsOf reads a euro amount typed with a comma or a point; fromDay starts the window', marketOfTerm('lt-a1-eye') === 'lt' && marketOfTerm('de-win') === 'de' && marketOfTerm('hu-win') === 'hu' && marketOfTerm('x-win') === null
    && centsOf('2,50') === 250 && centsOf(' 12 ') === 1200 && centsOf('2.5') === 250 && centsOf('2,555') === null && centsOf('') === null && centsOf('abc') === null && centsOf('10001') === null && centsOf('10000') === 1000000
    && fromDay(1, Date.UTC(2026, 9, 21, 12)) === '2026-10-21' && fromDay(7, Date.UTC(2026, 9, 21, 12)) === '2026-10-15');
  check('ordersOf: the paid, live orders of the given UTC days, per currency; a test payment, a withdrawn order and an unpaid one count for nothing',
    JSON.stringify(ordersOf([
      { order: 'a', state: 'ready', paid: true, live: true, amount: 1997, currency: 'EUR', paid_at: Date.UTC(2026, 9, 20, 10) / 1000 }, { order: 'b', state: 'ready', paid: true, live: false, amount: 1997, currency: 'EUR', paid_at: Date.UTC(2026, 9, 20, 10) / 1000 },
      { order: 'c', state: 'withdrawn', paid: true, live: true, amount: 1997, currency: 'EUR', paid_at: Date.UTC(2026, 9, 20, 10) / 1000 }, { order: 'd', state: 'unpaid', paid: false, live: null, amount: 1997, currency: 'EUR', paid_at: null },
      { order: 'e', state: 'ready', paid: true, live: true, amount: 699000, currency: 'HUF', paid_at: Date.UTC(2026, 9, 20, 23) / 1000 }, { order: 'f', state: 'ready', paid: true, live: true, amount: 1997, currency: 'EUR', paid_at: Date.UTC(2026, 9, 19, 23) / 1000 },
    ] as never, ['2026-10-20'])) === JSON.stringify({ n: 2, revenue: { eur: 1997, huf: 699000 } }));

  check('CSV: a semicolon, a decimal comma, quotes around a text with a semicolon or a quote, and a cell that starts like a formula is quoted', toCsv(['a', 'b'], [['x;y', 1.5], ['=SUM(A1)', null], ['q"q', 2]]) === 'a;b\r\n"x;y";1,5\r\n"=SUM(A1)";\r\nq"q;2\r\n'.replace('q"q', '"q""q"'), JSON.stringify(toCsv(['a', 'b'], [['x;y', 1.5], ['=SUM(A1)', null], ['q"q', 2]])));
  const csv = sourcesCsv({ group: 'cmp', rows: [{ key: { src: 'fb', med: 'paid', cmp: 'se-p0-test', trm: '', cnt: '' }, steps: { landing: 5, try: 3 }, orders: 1, revenue: { eur: 1997 } }] });
  const csvLines = csv.split('\r\n');
  check('the sources CSV has the columns of the page (five codes, eight steps, orders, revenue) and one line per row, revenue in words', csvLines[0].split(';').length === 15 && csvLines[1].split(';').length === 15 && csvLines[0].split(';')[0].normalize('NFC') === 'Šaltinis'.normalize('NFC')
    && csvLines[1].startsWith('fb;paid;se-p0-test;;;5;3;') && csvLines[1].endsWith(`;1;${eur(1997)}`) && csvLines.length === 3, csv);

  // the pages: wiring and words
  const app = read('src/admin/AdminApp.tsx');
  check('the admin app has the five pages and groups its tabs in three rows (day to day, visitors and advertising, tools)', ['sources', 'funnel', 'why', 'photos', 'ads'].every((p) => app.includes(`'${p}'`) && app.includes(`route.page === '${p}'`)) && /Lankytojai ir reklama/.test(app) && /TAB_GROUPS/.test(app));
  const orders = read('src/admin/Orders.tsx');
  check('the orders list shows the source of an order and filters by it', /šaltinis: \$\{campText\(r\.camp\)\}/.test(orders) && /aria-label="Šaltinis"/.test(orders));
  check('the order detail names the source', /Šaltinis \(reklama\)/.test(read('src/admin/OrderDetail.tsx')) && /DailyCard/.test(read('src/admin/Summary.tsx')));
  const files = ['traffic.ts', 'TrafficUi.tsx', 'Sources.tsx', 'Funnel.tsx', 'Why.tsx', 'Photos.tsx', 'Ads.tsx', 'DailyCard.tsx'].map((f) => [f, read(`src/admin/${f}`)] as const);
  const dash = new RegExp('[' + [0x2012, 0x2013, 0x2014, 0x2015].map((c) => String.fromCharCode(c)).join('') + ']');
  check('no page of the visitor pages holds an en or em dash, and none sends a request but through the call it is given (no fetch, no localStorage)', files.every(([, t]) => !dash.test(t) && !/\bfetch\(|localStorage/.test(t.replace(/[/][/].*$/gm, ''))), files.filter(([, t]) => dash.test(t)).map(([f]) => f).join());
  check('the pages read nothing but what the admin actions answer: the actions they call exist on the server', ['sources', 'funnel', 'why', 'photos', 'ads', 'ads_put', 'ads_delete', 'daily'].every((a) => /ACTIONS = \{[\s\S]*\}/.test(read('api/_lib/ops.py')) && read('api/_lib/ops.py').includes(`"${a}":`)));
  return out;
}
