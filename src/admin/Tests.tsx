// Kainų testai: every price experiment of api/_lib/experiments.py with its state, its full price ladders, what each
// variant did (visitors, previews, payment pages opened, paid orders, conversion, revenue and average order in the
// experiment's own currency), an honest significance note, the warnings (a variant that would sell at a loss, ladders far
// apart, numbers that disagree) and the start and stop buttons, each behind a confirmation and written to the audit log.
// Nothing runs until the owner starts it here. All numbers come from the server (api/_lib/abtest.py admin_view); the
// ladders are the server's, never typed here. Tables on a wide screen, one card per variant on a phone (a table of
// four or five columns does not fit 375 px, and sideways scrolling hides exactly the numbers that matter).
import { useCallback, useEffect, useState } from 'react';
import type React from 'react';
import type { ExpCompare, ExpLadder, Experiment, ExpStats, ExpWarning, Experiments, Reply } from './api';
import type { Call } from './AdminApp';
import { actionLt, AKYS, explain, fmtMoney, fmtTime, logResultLt, ltCount, STYLE_LT } from './format';
import { BTN, CARD, Chip, ConfirmDialog, DANGER, GOLD, H2, MUTED, Notice, Rows, Spinner, Toast } from './ui';
import type { ConfirmSpec, Tone } from './ui';
import { priceMinor } from '../shared/markets';
import { classStyle } from '../shared/styles';

interface Note { tone: Tone; text: string; busy?: boolean }

const pct = (v: number | null | undefined, digits = 2): string => (typeof v === 'number' && Number.isFinite(v) ? `${(v * 100).toFixed(digits).replace('.', ',')} %` : '-');
const num = (v: number | null | undefined): string => (typeof v === 'number' ? String(Math.round(v)).replace(/\B(?=(\d{3})+(?!\d))/g, ' ') : '-');
const dec = (v: number, digits = 2): string => v.toFixed(digits).replace('.', ',');

const MARKET_LT: Record<string, string> = { eu: 'eu (euras, anglų ir vokiečių kalbos)', lt: 'lt (euras, Lietuva)', au: 'au (Australijos doleriai)', hu: 'hu (forintai)' };
const KEY_LT: Record<keyof ExpLadder, string> = {
  one_eye_studio_black: '1 akis, juodas fonas', one_eye_art: '1 akis, meninis fonas', two_eyes: '2 akys', each_further_eye: 'kiekviena kita akis',
};
const ATVEJIS: [string, string, string] = ['atvejis', 'atvejai', 'atvejų'];

/** The ladder's example totals for this many eyes (a style of the black class), by the very rule the pages use (src/shared/markets.ts). */
const total = (market: string, ladder: ExpLadder, eyes: number, style = classStyle('black')): number => priceMinor(eyes, style, market, ladder);

/** How long ago, in words: "15 min.", "3 val.", "12 d." */
const elapsed = (from: number | null | undefined, now: number): string => {
  if (!from) return '-';
  const s = Math.max(0, now - from);
  if (s < 3600) return `${Math.max(1, Math.round(s / 60))} min.`;
  if (s < 86400) return `${Math.round(s / 3600)} val.`;
  return `${Math.floor(s / 86400)} d.`;
};

/** The server's warnings as sentences (the loss check, the spread of the ladders, events that disagree with the orders). */
function warningLines(ex: Experiment, unitUsd: number): { tone: Tone; text: string }[] {
  const w = ex.warnings;
  const label = (v?: string) => ex.variants.find((x) => x.variant === v)?.label || v || '';
  const out: { tone: Tone; text: string }[] = [];
  const loss = w.filter((x) => x.code === 'loss');
  if (loss.length) {
    // one line per variant, number of eyes and style, with the markets it concerns (the same price in eu and lt is one case)
    const groups = new Map<string, { w: ExpWarning; markets: string[] }>();
    for (const x of loss) {
      const k = `${x.variant}|${x.eyes}|${x.style}|${x.price}`;
      const g = groups.get(k);
      if (g) { if (x.market && !g.markets.includes(x.market)) g.markets.push(x.market); } else groups.set(k, { w: x, markets: x.market ? [x.market] : [] });
    }
    const list = [...groups.values()];
    const first = list.slice(0, 3).map(({ w: x, markets }) => `${ltCount(x.eyes ?? 0, AKYS)}, ${STYLE_LT[x.style ?? ''] || x.style}, rinkose ${markets.join(' ir ')}: kaina ${fmtMoney(x.price, ex.currency)}, po mokesčių ir darbo lieka ${fmtMoney(x.net, ex.currency)}`).join('; ');
    out.push({ tone: 'bad', text: `Nuostolis: kainynas „${label(list[0].w.variant)}“ kai kuriems užsakymams parduodamas pigiau, nei kainuoja (${ltCount(list.length, ATVEJIS)}). Pavyzdžiai: ${first}. Skaičiuota su Stripe mokesčiu ir apie ${String(unitUsd).replace('.', ',')} USD už akį.` });
  }
  const spread = w.filter((x) => x.code === 'spread');
  if (spread.length) {
    const worst = [...spread].sort((a, b) => (b.ratio ?? 0) - (a.ratio ?? 0))[0];
    out.push({ tone: 'warn', text: `Kainynai labai skiriasi: ${ltCount(worst.eyes ?? 0, AKYS)} rinkoje ${worst.market} vieno varianto kaina yra ${dec(worst.ratio ?? 0)} karto didesnė už kito. Lankytojai tai gali pastebėti, o vienas kainynas gali būti toli nuo tinkamos kainos.` });
  }
  for (const x of w.filter((y) => y.code === 'events_differ')) {
    out.push({ tone: 'warn', text: `Varianto „${label(x.variant)}“ apmokėjimų įvykių skaičius (${x.events}) nesutampa su užsakymų įrašais (${x.orders}). Rodomi užsakymų įrašų skaičiai; anoniminiai įvykiai saugomi tik pagal galimybes ir gali pritrūkti.` });
  }
  return out;
}

/** The prices that differ between the variants, as a sentence for the start dialog: what a visitor will see. */
function differingPrices(ex: Experiment): string {
  const parts: string[] = [];
  for (const m of ex.markets) {
    for (const k of ex.changes as (keyof ExpLadder)[]) {
      const vals = ex.variants.filter((v) => v.prices[m]).map((v) => `${v.variant} ${fmtMoney(v.prices[m][k], ex.currency)}`);
      if (vals.length) parts.push(`${ex.markets.length > 1 ? `${m}: ` : ''}${KEY_LT[k] || k}: ${vals.join(' prieš ')}`);
    }
  }
  return parts.join('; ');
}

// ------------------------------------------------------------------------------------------------ the ladders

const LADDER_ROWS: [string, (l: ExpLadder, m: string) => number, keyof ExpLadder | null][] = [
  ['1 akis, juodas fonas', (l) => l.one_eye_studio_black, 'one_eye_studio_black'],
  ['1 akis, meninis fonas', (l) => l.one_eye_art, 'one_eye_art'],
  ['2 akys', (l) => l.two_eyes, 'two_eyes'],
  ['Kiekviena kita akis', (l) => l.each_further_eye, 'each_further_eye'],
  ['3 akys iš viso', (l, m) => total(m, l, 3), null],
  ['4 akys iš viso', (l, m) => total(m, l, 4), null],
  ['8 akys iš viso', (l, m) => total(m, l, 8), null],
];

/** The markets of a test grouped by identical ladders (eu and lt often carry the very same ones): [[markets...], ...]. */
const ladderGroups = (ex: Experiment): string[][] => {
  const by = new Map<string, string[]>();
  for (const m of ex.markets) {
    const k = JSON.stringify(ex.variants.map((v) => v.prices[m] ?? null));
    by.set(k, [...(by.get(k) ?? []), m]);
  }
  return [...by.values()];
};

const Ladders: React.FC<{ ex: Experiment }> = ({ ex }) => (
  <div className="flex flex-col gap-4">
    {ladderGroups(ex).map((group) => {
      const m = group[0];
      const differs = (k: keyof ExpLadder | null, v: Experiment['variants'][number]) => !!k && ex.variants.some((o) => o.prices[m] && v.prices[m] && o.prices[m][k] !== v.prices[m][k]);
      return (
        <div key={group.join(',')} className="min-w-0">
          <p className="text-xs text-white/70 mb-1">{group.length > 1 ? `Rinkos ${group.join(' ir ')} (tie patys kainynai)` : `Rinka ${MARKET_LT[m] || m}`}</p>
          {/* wide screens: one table, a row per price */}
          <div className="hidden sm:block overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-white/60 text-xs">
                  <th className="py-1 pr-3 font-semibold">&nbsp;</th>
                  {ex.variants.map((v) => <th key={v.variant} className="py-1 pr-3 font-semibold"><code>{v.variant}</code><span className={`block font-normal ${MUTED}`}>{v.label} ({v.split} %)</span></th>)}
                </tr>
              </thead>
              <tbody>
                {LADDER_ROWS.map(([label, f, k]) => (
                  <tr key={label} className="border-t border-white/5 align-top">
                    <th scope="row" className="py-1.5 pr-3 text-left font-normal text-white/70">{label}</th>
                    {ex.variants.map((v) => v.prices[m]
                      ? <td key={v.variant} className={`py-1.5 pr-3 ${differs(k, v) ? 'font-bold text-[#f5c542]' : ''}`}>{fmtMoney(f(v.prices[m], m), ex.currency)}</td>
                      : <td key={v.variant} className="py-1.5 pr-3">-</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {/* phones: a card per variant */}
          <div className="sm:hidden flex flex-col gap-2">
            {ex.variants.map((v) => v.prices[m] && (
              <div key={v.variant} className="rounded-xl border border-white/10 bg-black/20 p-3 min-w-0">
                <p className="text-sm break-words"><b><code>{v.variant}</code></b> <span className={MUTED}>{v.label}, dalis {v.split} %</span></p>
                <dl className="mt-1.5 grid grid-cols-[minmax(0,1fr)_auto] gap-x-3 gap-y-0.5 text-sm">
                  {LADDER_ROWS.map(([label, f, k]) => (
                    <div key={label} className="contents">
                      <dt className="text-white/70">{label}</dt>
                      <dd className={`text-right ${differs(k, v) ? 'font-bold text-[#f5c542]' : ''}`}>{fmtMoney(f(v.prices[m], m), ex.currency)}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            ))}
          </div>
        </div>
      );
    })}
    <p className={`text-xs ${MUTED}`}>Aukso spalva paryškintos kainos, kuriomis variantai skiriasi. Kiekvienas variantas turi pilną savo kainyną: lankytojui niekada netaikomas koks nors skirtumas, tik čia surašyta kaina.</p>
  </div>
);

// ------------------------------------------------------------------------------------------------ what happened

const statRows = (ex: Experiment): [string, (s: ExpStats) => React.ReactNode][] => {
  const rows: [string, (s: ExpStats) => React.ReactNode][] = [
    ['Lankytojai (naršyklės, kurioms parodytas variantas)', (s) => num(s.visitors)],
    ['Padarė peržiūrą', (s) => `${num(s.previews)}${s.rate_preview === null ? '' : ` (${pct(s.rate_preview, 1)} lankytojų)`}`],
    ['Atidarė mokėjimo puslapį', (s) => `${num(s.checkouts)}${s.rate_checkout === null ? '' : ` (${pct(s.rate_checkout, 1)} lankytojų)`}`],
    ['Apmokėti užsakymai', (s) => `${num(s.paid)}${s.paid_test ? `, testinių ${num(s.paid_test)}` : ''}${s.returned ? `, grąžinta ${num(s.returned)}` : ''}`],
    ['Apmokėta iš lankytojų', (s) => pct(s.rate_paid)],
    ['Apmokėta iš atidarytų mokėjimų', (s) => pct(s.rate_paid_of_checkout, 1)],
    ['Pajamos (be grąžintų)', (s) => fmtMoney(s.revenue, ex.currency)],
    ['Vidutinis užsakymas', (s) => (s.avg_order === null ? '-' : fmtMoney(s.avg_order, ex.currency))],
    ['Pajamos vienam lankytojui', (s) => (s.revenue_per_visitor === null ? '-' : fmtMoney(s.revenue_per_visitor, ex.currency))],
  ];
  if (ex.partial) {
    rows.push(
      [`Paveikti užsakymai (${ex.hit_label}): apmokėta`, (s) => num(s.hit_paid)],
      ['Paveikti užsakymai: pajamos', (s) => fmtMoney(s.revenue_hit, ex.currency)],
      ['Paveikti užsakymai: vidutinis užsakymas', (s) => (s.avg_order_hit === null ? '-' : fmtMoney(s.avg_order_hit, ex.currency))],
    );
  }
  return rows;
};

const StatsView: React.FC<{ ex: Experiment }> = ({ ex }) => {
  const rows = statRows(ex);
  const label = (v: string) => ex.variants.find((x) => x.variant === v)?.label || '';
  return (
    <>
      {/* wide screens: one table */}
      <div className="hidden sm:block overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-white/60 text-xs">
              <th className="py-1 pr-3 font-semibold">&nbsp;</th>
              {ex.stats.map((s) => <th key={s.variant} className="py-1 pr-3 font-semibold"><code>{s.variant}</code><span className={`block font-normal ${MUTED}`}>{label(s.variant)}</span></th>)}
            </tr>
          </thead>
          <tbody>
            {rows.map(([l, f]) => (
              <tr key={l} className="border-t border-white/5 align-top">
                <th scope="row" className="py-1.5 pr-3 text-left font-normal text-white/70">{l}</th>
                {ex.stats.map((s) => <td key={s.variant} className="py-1.5 pr-3">{f(s)}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {/* phones: a card per variant, label and value on each line */}
      <div className="sm:hidden flex flex-col gap-2">
        {ex.stats.map((s) => (
          <div key={s.variant} className="rounded-xl border border-white/10 bg-black/20 p-3 min-w-0">
            <p className="text-sm break-words"><b><code>{s.variant}</code></b> <span className={MUTED}>{label(s.variant)}</span></p>
            <dl className="mt-1.5 flex flex-col gap-1 text-sm">
              {rows.map(([l, f]) => (
                <div key={l} className="flex flex-col border-t border-white/5 pt-1 first:border-t-0 first:pt-0">
                  <dt className="text-xs text-white/60 break-words">{l}</dt>
                  <dd className="break-words">{f(s)}</dd>
                </div>
              ))}
            </dl>
          </div>
        ))}
      </div>
    </>
  );
};

// ------------------------------------------------------------------------------------------------ does the difference mean anything

const whyLt = (why: string | null, rules: Experiments['rules']): string => {
  const base = `p nerodomas, kol kiekvienas variantas neturi bent ${rules.min_arm_visitors} lankytojų ir ${rules.min_arm_paid} apmokėtų užsakymų`;
  if (why === 'few_paid') return `${base}; apmokėtų dar per mažai`;
  if (why === 'few_visitors') return `${base}; lankytojų dar per mažai`;
  if (why === 'paid_exceeds_visitors') return 'p nerodomas: apmokėtų užsakymų yra daugiau nei užfiksuotų lankytojų (lankytojų skaičius neišsamus, pavyzdžiui po pakartotinio paleidimo)';
  return base;
};

/** One test of a difference, in words. planned: every arm reached the planned size (only then a verdict is allowed). */
function testWords(t: { p: number | null; enough: boolean; why: string | null }, rules: Experiments['rules'], planned: boolean, what: string): React.ReactNode {
  if (!t.enough || t.p === null) return <><b className="text-amber-200">per mažai duomenų</b><span className={MUTED}> ({whyLt(t.why, rules)}.)</span></>;
  const p = `p = ${String(t.p).replace('.', ',')}`;
  if (!planned) {
    return <>{p} ({what}). <b className="text-amber-200">Dar per anksti sprendimui:</b> planuotas dydis nepasiektas. Ankstyvų dienų p reikšmių nevertink: žiūrint rezultatus per anksti, atsitiktinis skirtumas gana dažnai atrodo reikšmingas.</>;
  }
  return <>{p} ({what}). {t.p < 0.05 ? 'Planuotas dydis pasiektas ir skirtumas reikšmingas: šis rodiklis tikrai skiriasi.' : 'Planuotas dydis pasiektas, bet šio rodiklio skirtumo nepastebėta.'}</>;
}

const Significance: React.FC<{ ex: Experiment; rules: Experiments['rules'] }> = ({ ex, rules }) => {
  const need = ex.need;
  const control = ex.stats.find((x) => x.variant === 'control');
  const money = (v: number) => fmtMoney(v, ex.currency);
  const ranked = ex.stats.filter((s) => s.revenue_per_visitor !== null && s.visitors > 0).sort((a, b) => (b.revenue_per_visitor ?? 0) - (a.revenue_per_visitor ?? 0));
  const allPlanned = ex.compare.length > 0 && ex.compare.every((c) => c.planned);
  const diff = (c: ExpCompare) => (typeof c.diff === 'number' ? ` (skirtumas ${c.diff >= 0 ? '+' : '-'}${dec(Math.abs(c.diff) * 100)} procentinio punkto)` : '');
  return (
    <div className="flex flex-col gap-3 text-sm">
      {ranked.length > 0 && (
        <p className="break-words rounded-xl border border-white/10 bg-black/20 px-3 py-2">
          <b>Pajamos vienam lankytojui:</b> {ranked.map((s) => `${s.variant} ${money(s.revenue_per_visitor as number)}`).join(', ')}.{' '}
          {allPlanned ? 'Planuotas dydis pasiektas.' : <b className="text-amber-200">Tai dar tik stebėjimas, sprendimui per mažai duomenų.</b>}
        </p>
      )}
      {ex.compare.map((c) => {
        const s = ex.stats.find((x) => x.variant === c.variant);
        const hasData = !!s && !!control && s.visitors > 0 && control.visitors > 0;
        return (
          <div key={c.variant} className="flex flex-col gap-1.5 break-words">
            <p><b><code>{c.variant}</code></b> prieš <code>control</code>:</p>
            <p>
              <b>Apmokėjimo dažnis</b> (kiek lankytojų nupirko): {hasData && s && control ? `${pct(s.rate_paid)} prieš ${pct(control.rate_paid)}${diff(c)}` : 'dar nėra lankytojų palyginimui'}.{' '}
              {hasData ? testWords(c, rules, c.planned, 'tik dažnio palyginimas, ne pajamos') : null}
            </p>
            {ex.partial && c.hit && (
              <p>
                <b>Tik paveikti užsakymai</b> ({ex.hit_label}; kiek lankytojų nupirko būtent tokį): {hasData && s && control ? `${pct(s.rate_hit_paid)} prieš ${pct(control.rate_hit_paid)}` : 'dar nėra duomenų'}.{' '}
                {hasData ? testWords(c.hit, rules, c.planned, 'pagrindinis šio testo rodiklis') : null}
              </p>
            )}
            <p>
              <b>Pajamos vienam lankytojui</b> (pagal šį rodiklį sprendžiama dėl kainos): {hasData && s && control && s.revenue_per_visitor !== null && control.revenue_per_visitor !== null ? `${money(s.revenue_per_visitor)} prieš ${money(control.revenue_per_visitor)}` : 'dar nėra duomenų'}.{' '}
              {c.rpv
                ? <>Skirtumas {c.rpv.diff >= 0 ? '+' : '-'}{money(Math.abs(Math.round(c.rpv.diff)))}, p = {String(c.rpv.p).replace('.', ',')}.{c.planned ? '' : ' Dar per anksti sprendimui.'}</>
                : <b className="text-amber-200">per mažai duomenų</b>}
            </p>
          </div>
        );
      })}
      {need && (
        <p className="break-words">
          {ex.partial && ex.need_hit
            ? <>Šio testo kainos keičia tik dalį užsakymų ({ex.hit_label}), todėl sprendimui reikia maždaug <b>{num(ex.need_hit.paid)} paveiktų apmokėtų užsakymų kiekvienam variantui</b> (apie {num(ex.need_hit.visitors)} lankytojų kiekvienam), kad būtų galima patikimai pastebėti {Math.round(ex.need_hit.rel * 100)} % skirtumą (95 % pasikliovimas, 80 % galia).
              {ex.need_hit.assumed ? ` Tai prielaida: paveiktų užsakymų dažnis ${pct(ex.need_hit.rate, 2)} lankytojų, kol nėra savo duomenų.` : ` Skaičiuota pagal dabartinį kontrolinio varianto paveiktų užsakymų dažnį ${pct(ex.need_hit.rate)}.`}{' '}</>
            : <>Kad būtų galima patikimai pastebėti {Math.round(need.rel * 100)} % santykinį skirtumą apmokėjimo dažnyje (95 % pasikliovimas, 80 % galia), reikia maždaug <b>{num(need.paid)} apmokėtų užsakymų kiekvienam variantui</b> (apie {num(need.visitors)} lankytojų kiekvienam).
              {need.assumed ? ` Tai prielaida: skaičiuota su ${pct(need.rate, 0)} apmokėjimo dažniu, kol nėra savo duomenų.` : ` Skaičiuota pagal dabartinį kontrolinio varianto ${pct(need.rate)} apmokėjimo dažnį.`}{' '}</>}
          Kol tiek nėra, skirtumai gali būti atsitiktiniai.
        </p>
      )}
      {ex.untokened && (ex.untokened.orders > 0 || ex.stats.some((s) => s.paid > 0)) && (
        <p className={`break-words text-xs ${MUTED}`}>
          Užsakymai be varianto per testo laiką (išjungta naršyklės saugykla, pasirinktas nedalyvavimas ar apeitas testas): {ex.untokened.orders}, iš jų apmokėta {ex.untokened.paid}.
          Jie neturi varianto ir į skaičius aukščiau neįtraukti. Jei jų daug, palyginimas gali būti iškreiptas.
        </p>
      )}
      <p className={`text-xs ${MUTED}`}>
        Lankytojas yra naršyklė: išvalius svetainės duomenis ji tampa nauju lankytoju ir gauna naują atsitiktinį variantą. Lankytojų ir peržiūrų
        skaičius skaičiuojamas vieną kartą kiekvienai naršyklei ir kiekvienam testo paleidimui, mokėjimo puslapiai skaičiuojami kiekvienam atidarytam
        mokėjimui. Apmokėti užsakymai ir pajamos imami iš užsakymų įrašų (gyvi mokėjimai, be grąžintų ir be atsisakytų), lankytojai, peržiūros ir
        mokėjimo puslapiai iš anoniminių įvykių. Skaičiai rodomi tik nuo pirmo testo paleidimo.
      </p>
    </div>
  );
};

// ------------------------------------------------------------------------------------------------ one experiment

const logDetail = (d: string | undefined): string => {
  if (!d) return '';
  const [key, ...flags] = d.split(' ');
  const words = flags.map((f) => (f === 'accept_loss' ? 'nuostolis priimtas' : f === 'accept_no_stats' ? 'be statistikos' : f));
  return ` (${key}${words.length ? `, ${words.join(', ')}` : ''})`;
};

const ExperimentCard: React.FC<{ ex: Experiment; data: Experiments; call: Call; onChanged: () => void; setNote: (n: Note | null) => void; setConfirm: (c: ConfirmSpec | null) => void }> = ({ ex, data, call, onChanged, setNote, setConfirm }) => {
  const running = ex.state.running;
  const lines = warningLines(ex, data.costs.unit_usd_per_eye);
  const loss = ex.warnings.some((w) => w.code === 'loss');
  const noStats = data.collecting === false;
  const act = async (action: 'exp_start' | 'exp_stop', extra: Record<string, unknown>, ok: string) => {
    setNote({ tone: 'info', text: 'Vykdoma...', busy: true });
    const r: Reply<Record<string, unknown>> = await call<Record<string, unknown>>(action, { key: ex.key, ...extra });
    setNote(r.ok ? { tone: 'good', text: ok } : { tone: 'bad', text: explainExp(r) });
    onChanged();
  };
  const risks = [loss ? 'kai kurie variantai parduodami nuostoliu' : '', noStats ? 'lankytojų, peržiūrų ir atidarytų mokėjimų skaičiai nebus renkami' : ''].filter(Boolean);
  const start = () => setConfirm({
    title: `Paleisti testą „${ex.title}“`, confirmLabel: 'Paleisti testą',
    text: `Nuo šios akimirkos ${ex.markets.length > 1 ? `${ex.markets.join(' ir ')} rinkų` : `${ex.markets[0]} rinkos`} lankytojai atsitiktinai gaus vieną iš ${ex.variants.length} kainynų (${ex.variants.map((v) => `${v.variant} ${v.split} %`).join(', ')}) ir jį išlaikys. `
      + `Kainos, kurios skiriasi: ${differingPrices(ex)}. `
      + 'Puslapiai rodys tik to varianto kainas, Stripe nuskaitys lygiai tą sumą, o užsakymas, laiškai ir kvitas fiksuos varianto pavadinimą ir kainyną. '
      + 'Kol testas veikia, tų rinkų lankytojų naršyklėje sukuriamas atsitiktinis anoniminis numeris (aprašyta privatumo politikoje, su nuoroda, kaip nedalyvauti). Sustabdyti galėsi bet kada.'
      + `${data.ordering_open === false ? '\n\nDabar užsakymai uždaryti, todėl testas pradės veikti tik atidarius užsakymus.' : ''}`
      + `${lines.length ? `\n\nDĖMESIO:\n${lines.map((l) => l.text).join('\n')}` : ''}`
      + `${noStats ? '\n\nDĖMESIO:\nŠiame serveryje nenustatytas CRON_SECRET, todėl lankytojų, peržiūrų ir atidarytų mokėjimų skaičiai liks nuliniai (apmokėti užsakymai ir pajamos rodomi pagal užsakymus ir veikia).' : ''}`,
    danger: loss || noStats,
    option: risks.length ? { label: `Suprantu: ${risks.join('; ')}, ir vis tiek noriu paleisti`, value: false } : undefined,
    run: async (accepted) => {
      if (risks.length && !accepted) { setNote({ tone: 'bad', text: 'Testas nepaleistas: pirma pažymėk, kad supranti pirmiau nurodytą riziką.' }); return; }
      await act('exp_start', { accept_loss: loss && accepted, accept_no_stats: noStats && accepted }, `Testas „${ex.title}“ paleistas.`);
    },
  });
  const stop = () => setConfirm({
    title: `Sustabdyti testą „${ex.title}“`, confirmLabel: 'Sustabdyti', danger: true,
    text: 'Sustabdžius nauji lankytojai vėl mato ir moka įprastas kainas. Jau atidaryti Stripe mokėjimo puslapiai (jie galioja iki 24 val.) išlaiko savo varianto kainą ir apmokėti bus užfiksuoti kaip įprasta. Skaičiai lieka šiame puslapyje. Prieš keisdamas kainas ar testų apibrėžimus, palauk 24 val.',
    run: () => act('exp_stop', {}, `Testas „${ex.title}“ sustabdytas.`),
  });
  const s0 = ex.state;
  return (
    <section className={`${CARD} flex flex-col gap-4`} aria-label={ex.title}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="text-base font-bold break-words">{ex.title}</h3>
          <p className={`text-xs mt-0.5 break-words ${MUTED}`}>raktas <code>{ex.key}</code> · rinkos: {ex.markets.join(', ')} · valiuta {ex.currency}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Chip tone={running ? 'good' : 'muted'}>{ex.retired ? 'Užbaigtas' : running ? 'Veikia' : 'Išjungtas'}</Chip>
          {running
            ? <button type="button" className={DANGER} onClick={stop}>Sustabdyti testą</button>
            : !ex.retired && <button type="button" className={GOLD} onClick={start} disabled={!!ex.conflict}>Paleisti testą</button>}
        </div>
      </div>
      <p className="text-sm text-white/80 break-words">{ex.about}</p>
      {ex.conflict && <Notice tone="warn">Šioje rinkoje jau veikia kitas testas (<code>{ex.conflict}</code>). Vienu metu vienoje rinkoje gali veikti tik vienas: pirma sustabdyk jį.</Notice>}
      {ex.stats_error && <Notice tone="warn">Šio testo skaičių apskaičiuoti nepavyko. Būsena, kainynai ir mygtukai veikia; bandyk atnaujinti po minutės.</Notice>}
      {lines.map((l, i) => <Notice key={i} tone={l.tone}>{l.text}</Notice>)}
      <Rows rows={[
        ['Būsena', running ? `veikia nuo ${s0.started_at ? fmtTime(s0.started_at) : '-'} (jau ${elapsed(s0.started_at, data.now)})` : s0.stopped_at ? `išjungtas ${fmtTime(s0.stopped_at)}` : 'dar niekada nepaleistas'],
        ['Paleidimų', String(s0.runs.length)],
        ['Skaičiai', s0.since ? `skaičiuojami nuo pirmo paleidimo (${fmtTime(s0.since)}, prieš ${elapsed(s0.since, data.now)})` : 'nėra ko skaičiuoti'],
      ]} />
      <div>
        <h4 className="text-sm font-bold mb-2">Kainynai</h4>
        <Ladders ex={ex} />
      </div>
      {!ex.stats_error && (
        <>
          <div>
            <h4 className="text-sm font-bold mb-2">Kas įvyko</h4>
            <StatsView ex={ex} />
          </div>
          <div>
            <h4 className="text-sm font-bold mb-2">Ar skirtumas ką nors reiškia</h4>
            <Significance ex={ex} rules={data.rules} />
          </div>
        </>
      )}
      {s0.runs.length > 0 && (
        <details className="text-sm">
          <summary className="cursor-pointer text-white/70">Paleidimai ir sustabdymai</summary>
          <ul className="mt-2 list-disc pl-5 text-white/80">
            {[...s0.runs].reverse().map((r, i) => <li key={i}>nuo {fmtTime(r.start)}{r.stop ? ` iki ${fmtTime(r.stop)}` : ' (veikia)'}</li>)}
          </ul>
        </details>
      )}
    </section>
  );
};

const explainExp = (r: Reply<Record<string, unknown>>): string => {
  const extra: Record<string, string> = {
    already_running: 'Šis testas jau veikia.', not_running: 'Šis testas neveikia.',
    market_taken: 'Šioje rinkoje jau veikia kitas testas: pirma sustabdyk jį.',
    sells_at_loss: 'Kainynas kai kuriems užsakymams parduodamas nuostoliu: paleidimui reikia aiškaus patvirtinimo.',
    stats_not_collected: 'Šiame serveryje nenustatytas CRON_SECRET, todėl lankytojų ir peržiūrų skaičiai nebūtų renkami: paleidimui reikia aiškaus patvirtinimo.',
    retired: 'Šis testas užbaigtas ir daugiau nepaleidžiamas.',
  };
  return extra[r.reason] || explain(r);
};

export const TestsPage: React.FC<{ call: Call }> = ({ call }) => {
  const [data, setData] = useState<Experiments | null>(null);
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(true);
  const [note, setNote] = useState<Note | null>(null);
  const [confirm, setConfirm] = useState<ConfirmSpec | null>(null);

  const apply = useCallback((r: Reply<Experiments>) => {
    setBusy(false);
    if (r.ok && r.data) { setData(r.data); setErr(''); } else setErr(explain(r));
  }, []);

  useEffect(() => {
    let live = true;
    void call<Experiments>('experiments', {}, 60_000).then((r) => { if (live) apply(r); });
    return () => { live = false; };
  }, [call, apply]);

  useEffect(() => {
    if (!note || note.tone !== 'good') return;
    const t = setTimeout(() => setNote((cur) => (cur === note ? null : cur)), 9000);
    return () => clearTimeout(t);
  }, [note]);

  const load = async () => { setBusy(true); apply(await call<Experiments>('experiments', {}, 60_000)); };
  const hasLog = !!data && (data.log.length > 0 || data.runs.length > 0);

  return (
    <div className="flex flex-col gap-4">
      {note && (
        <Toast tone={note.tone} onClose={note.busy ? undefined : () => setNote(null)}>
          <span className="inline-flex items-center gap-2">{note.busy && <Spinner />}{note.text}</span>
        </Toast>
      )}
      <ConfirmDialog spec={confirm} onClose={() => setConfirm(null)} />
      <H2 right={<button type="button" className={BTN} onClick={() => void load()} disabled={busy}>{busy && <Spinner />}Atnaujinti</button>}>
        Kainų testai
      </H2>
      <p className={`text-sm ${MUTED}`}>
        Čia paleidžiami ir stebimi kainų testai. Kol testas neįjungtas, visi lankytojai mato ir moka įprastas kainas ir jų naršyklėje nieko nekuriama.
        Įjungus, kiekviena naršyklė tos rinkos, kurioje vyksta testas, atsitiktinai gauna vieną kainyną ir jį išlaiko. Serveris pats skaičiuoja kainą
        iš savo pasirašyto priskyrimo, todėl lankytojas negali pasirinkti pigesnio varianto, o puslapis rodo lygiai tą kainą, kuri bus nuskaityta.
        Kiekvienas paleidimas ir sustabdymas įrašomas į veiksmų žurnalą. Pakeitus serverio paslaptį SNAPEYES_TICKET_SECRET, visi lankytojai gautų
        naują atsitiktinį variantą, todėl jos testo metu nekeisk.
      </p>
      {err && <Notice>{err}</Notice>}
      {data && data.collecting === false && <Notice tone="bad">Statistika nerenkama: šiame serveryje nenustatytas CRON_SECRET (bent 16 simbolių), todėl lankytojų, peržiūrų ir atidarytų mokėjimų skaičiai liks nuliniai. Apmokėti užsakymai ir pajamos rodomi pagal užsakymų įrašus ir veikia be jo.</Notice>}
      {data && data.ordering_open === false && <Notice tone="warn">Užsakymai šiame serveryje dabar uždaryti: testas gali būti įjungtas, bet lankytojų ir užsakymų jame nebus, kol užsakymai neatidaryti.</Notice>}
      {data && data.orders_source !== 'orders' && data.experiments.some((e) => e.state.since) && (
        <Notice tone="warn">{data.orders_source === 'events_cut' ? 'Užsakymų per daug, kad visi būtų perskaityti' : 'Užsakymų įrašų perskaityti nepavyko'}, todėl apmokėti užsakymai ir pajamos skaičiuojami iš anoniminių įvykių ir gali būti netikslūs.</Notice>
      )}
      {data?.partial && <Notice tone="info">Dalis dienų dar skaičiuojama: atnaujink po minutės.</Notice>}
      {!data && busy && <p className="flex items-center gap-2 text-sm"><Spinner />Kraunama...</p>}
      {data?.experiments.map((ex) => (
        <ExperimentCard key={ex.key} ex={ex} data={data} call={call} onChanged={() => void load()} setNote={setNote} setConfirm={setConfirm} />
      ))}
      {data && (
        <section className={CARD}>
          <h3 className="text-sm font-bold mb-2">Paleidimai ir veiksmų žurnalas</h3>
          {!hasLog ? <p className={`text-sm ${MUTED}`}>Dar nieko nepaleista.</p> : (
            <div className="flex flex-col gap-3">
              {data.runs.length > 0 && (
                <div>
                  <p className={`text-xs mb-1 ${MUTED}`}>Visi paleidimai (iš testų būsenos, nesikeičia nuo kitų veiksmų):</p>
                  <ul className="text-sm flex flex-col gap-1">
                    {data.runs.map((r, i) => <li key={i} className="break-words">{r.title}: nuo {fmtTime(r.start, true)}{r.stop ? ` iki ${fmtTime(r.stop, true)}` : ' (veikia)'}</li>)}
                  </ul>
                </div>
              )}
              {data.log.length > 0 && (
                <div>
                  <p className={`text-xs mb-1 ${MUTED}`}>Veiksmų žurnalas (paskutinės 14 dienų, taip pat atmesti bandymai):</p>
                  <ul className="text-sm flex flex-col gap-1">
                    {data.log.map((l, i) => (
                      <li key={i} className="break-words">
                        {fmtTime(l.t, true)} · {actionLt(l.action)}{logDetail(l.detail)} · {l.ok ? 'ok' : 'nepavyko'}{l.result ? `: ${logResultLt(l.result)}` : ''}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </section>
      )}
    </div>
  );
};
