// Suvestinė: the deployment (health flags and commit), whether it takes orders and why not, and the counts of today,
// 7 and 30 days: analyses, blocked photos by reason, verdicts, previews, masters, orders by state, paid revenue, the
// estimated Gemini spend and the busy and error counts.
import { useCallback, useEffect, useState } from 'react';
import type React from 'react';
import { getHealth } from './api';
import type { Counts, Health, OrderRow, Orders, Stats, Summary } from './api';
import type { Call } from './AdminApp';
import { countBy, lastDays, ordersSince, revenue, sumTable } from './agg';
import { BLOCK_LT, DEFAULT_PRICES, explain, fmtEur, fmtMoney, fmtTime, fmtUsd, KIND_LT, spend, STATE_LT, VERDICT_LT } from './format';
import { BTN, CARD, Flag, H2, MUTED, Notice, Spinner } from './ui';

const WINDOWS: [number, string][] = [[1, 'Šiandien'], [7, '7 d.'], [30, '30 d.']];

type Line = [string, (c: Counts, rows: OrderRow[], n: number) => React.ReactNode];

export const SummaryPage: React.FC<{ call: Call }> = ({ call }) => {
  const [health, setHealth] = useState<Health | null>(null);
  const [sum, setSum] = useState<Summary | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [orders, setOrders] = useState<Orders | null>(null);
  const [err, setErr] = useState<string[]>([]);
  const [busy, setBusy] = useState(true);
  const [loadedAt, setLoadedAt] = useState(0);

  const fetchAll = useCallback(() => Promise.all([getHealth(), call<Summary>('summary'), call<Stats>('stats', { days: 30 }),
    call<Orders>('orders', { days: 30 })]), [call]);

  const apply = useCallback(([h, s, st, o]: Awaited<ReturnType<typeof fetchAll>>) => {
    const e: string[] = [];
    if (h.ok && h.data) setHealth(h.data); else e.push(`/api/health: ${explain(h)}`);
    if (s.ok && s.data) setSum(s.data); else e.push(`Nustatymai: ${explain(s)}`);
    if (st.ok && st.data) setStats(st.data); else e.push(`Statistika: ${explain(st)}`);
    if (o.ok && o.data) setOrders(o.data); else e.push(`Užsakymai: ${explain(o)}`);
    setErr(e); setBusy(false); setLoadedAt(Math.floor(Date.now() / 1000));
  }, []);

  useEffect(() => {
    let live = true;
    void fetchAll().then((x) => { if (live) apply(x); });
    return () => { live = false; };
  }, [fetchAll, apply]);

  const load = async () => { setBusy(true); apply(await fetchAll()); };

  const now = loadedAt;
  const prices = stats?.prices_usd || sum?.prices_usd || DEFAULT_PRICES;
  const rows = orders?.orders || [];
  const days = stats?.days || [];

  const lines: Line[] = [
    ['Analizės (nuotraukos)', (c) => c.kinds.analyze || 0],
    ['Užblokuotos nuotraukos', (c) => `${c.blocked}${c.blocked ? ` (${Object.entries(c.block_reason).map(([k, v]) => `${BLOCK_LT[k] || k} ${v}`).join(', ')})` : ''}`],
    ['Vertinimai', (c) => Object.keys(c.verdict).length ? ['good', 'ok', 'weak', 'no_eye'].filter((k) => c.verdict[k]).map((k) => `${VERDICT_LT[k]} ${c.verdict[k]}`).join(', ') : '0'],
    ['Peržiūros (restauruotos akys)', (c) => c.kinds.enhance || 0],
    ['Kompozicijos (/api/compose)', (c) => c.kinds.compose || 0],
    ['4K akys / 4K kūriniai', (c) => `${c.master_eye} / ${c.master_compose}${c.master_lab ? ` (iš jų testų ${c.master_lab})` : ''}`],
    ['Užsakymai pagal būseną', (_c, r, n) => {
      const t = countBy(ordersSince(r, n, now), (x) => x.state);
      const keys = Object.keys(t);
      return keys.length ? keys.map((k) => `${STATE_LT[k] || k} ${t[k]}`).join(', ') : '0';
    }],
    ['Apmokėta (tikri mokėjimai)', (_c, r, n) => {
      // one line part per currency: euros, dollars and forints are never added together
      const by = revenue(r, n, now);
      const curs = Object.keys(by).sort((a, b) => (a === 'eur' ? -1 : b === 'eur' ? 1 : a.localeCompare(b)));
      if (!curs.length) return `${fmtEur(0)} (0)`;
      return curs.map((c) => `${fmtMoney(by[c].live, c)} (${by[c].n})${by[c].test ? `, testo ${fmtMoney(by[c].test, c)}` : ''}`).join('; ');
    }],
    ['Gemini užklausos', (c) => `vaizdo analizė ${c.gemini.vision}, 1K ${c.gemini.image_1k}, 4K ${c.gemini.image_4k}`],
    ['Gemini išlaidos (įvertis)', (c) => fmtUsd(spend(c, prices))],
    ['Gemini užimtas', (c) => c.busy],
    ['Klaidos', (c) => { const n = sumTable(c.errors); return n ? `${n} (${Object.entries(c.errors).map(([k, v]) => `${KIND_LT[k] || k} ${v}`).join(', ')})` : '0'; }],
  ];

  return (
    <div className="flex flex-col gap-4">
      <H2 right={<button type="button" className={BTN} onClick={() => void load()} disabled={busy}>{busy && <Spinner />}Atnaujinti</button>}>
        Suvestinė
      </H2>
      {err.map((e, i) => <Notice key={i}>{e}</Notice>)}
      {sum?.retention && !sum.retention.cron && <Notice tone="warn">Statistika nerenkama: šiame serveryje nenustatytas CRON_SECRET (bent 16 simbolių). Privatumo politika žada įvykius ištrinti po 12 mėnesių, o nesėkmingų prisijungimų žymas po 2 dienų, bet juos ištrina tik kasdienis valymas, kuriam reikia CRON_SECRET. Kol jo nėra, niekas nerašoma.</Notice>}
      <div className="grid gap-4 md:grid-cols-2">
        <section className={CARD}>
          <h3 className="text-sm font-bold mb-3">Užsakymų priėmimas</h3>
          {sum ? (
            <div className="flex flex-col gap-2">
              <p className="text-lg font-bold">{sum.ordering.open ? <span className="text-emerald-300">Atidarytas</span> : <span className="text-amber-200">Uždarytas</span>}</p>
              {!sum.ordering.open && <p className="text-sm break-words"><span className={MUTED}>Kodėl: </span>{sum.ordering.problem || 'nežinoma'}</p>}
              <Flag on={sum.payments.stripe} label="Stripe" />
              <Flag on={sum.payments.live} label="Stripe tikras (live) raktas" bad={false} />
              <Flag on={sum.payments.email} label="El. paštas (Resend)" />
              <Flag on={sum.storage.configured} label="Saugykla (Supabase)" />
              <Flag on={sum.payments.test_orders} label="Testo užsakymai čia galioja" bad={false} />
              {sum.storage.problem && <p className="text-xs text-red-200 break-words">{sum.storage.problem}</p>}
            </div>
          ) : busy ? <Spinner /> : null}
        </section>
        <section className={CARD}>
          <h3 className="text-sm font-bold mb-3">Serveris (/api/health)</h3>
          {health ? (
            <div className="flex flex-col gap-2">
              <p className="text-sm"><span className={MUTED}>Versija (commit): </span><code>{health.commit || 'nežinoma (vietinis paleidimas)'}</code></p>
              <Flag on={health.gemini_key} label="Gemini raktas" />
              <Flag on={health.master_store} label="Privati saugykla" />
              <Flag on={health.ordering} label="Priima užsakymus" />
              <Flag on={health.cron} label="Kasdienis valymas (CRON_SECRET)" />
              {sum?.admin.secret && (
                <p className="text-xs break-words">
                  <span className={MUTED}>Administratoriaus raktai pasirašomi: </span><code>{sum.admin.secret}</code>
                  {sum.admin.secret !== 'SNAPEYES_ADMIN_SECRET' && <span className="text-amber-200"> (saugiau atskira SNAPEYES_ADMIN_SECRET)</span>}
                </p>
              )}
              <Flag on={health.sr_model} label="Real-ESRGAN modelis" />
              <Flag on={health.deglare_model} label="Atspindžių Gemini kvietimas" bad={false} />
            </div>
          ) : busy ? <Spinner /> : null}
        </section>
      </div>
      <section className={CARD}>
        <h3 className="text-sm font-bold mb-1">Skaičiai</h3>
        <p className={`text-xs mb-3 ${MUTED}`}>
          Dienos skaičiuojamos pagal UTC. Gemini išlaidos yra įvertis: užklausų skaičius padaugintas iš kainų
          (analizė {fmtUsd(prices.vision)}, 1K {fmtUsd(prices.image_1k)}, 4K {fmtUsd(prices.image_4k)} už kvietimą).
          {stats?.partial ? ' Dalis dienų dar skaičiuojama: atnaujink po minutės.' : ''}
          {orders?.more ? ' Užsakymų daugiau nei parodyta.' : ''}
          {loadedAt ? ` Atnaujinta ${fmtTime(loadedAt, true)}.` : ''}
        </p>
        {/* a table on wide screens, one block per line on a phone */}
        <div className="hidden md:block">
          <table className="w-full text-sm table-fixed">
            <thead>
              <tr className="text-left text-white/60">
                <th className="py-1 pr-3 font-semibold w-[28%]">&nbsp;</th>
                {WINDOWS.map(([, l]) => <th key={l} className="py-1 pr-3 font-semibold">{l}</th>)}
              </tr>
            </thead>
            <tbody>
              {lines.map(([label, f]) => (
                <tr key={label} className="border-t border-white/5 align-top">
                  <th scope="row" className="py-1.5 pr-3 text-left font-normal text-white/70">{label}</th>
                  {WINDOWS.map(([n]) => <td key={n} className="py-1.5 pr-3 break-words">{f(lastDays(days, n), rows, n)}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="md:hidden flex flex-col gap-3">
          {lines.map(([label, f]) => (
            <div key={label} className="border-t border-white/5 pt-2">
              <p className="text-xs text-white/60 mb-1">{label}</p>
              {WINDOWS.map(([n, l]) => (
                <p key={n} className="text-sm break-words"><span className="text-white/50">{l}: </span>{f(lastDays(days, n), rows, n)}</p>
              ))}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
