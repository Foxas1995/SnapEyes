// Orders, paid orders and revenue by style and by group (spec PR 6.1, row "Orders, paid and revenue by style and group"). The usage events carry no amount and no order id on purpose, so
// the one place that can say what a style earned is the order records: the order list the Užsakymai page already reads. Two shapes of the same tables: inside the order list
// (SalesDetails, from the rows already loaded) and on the Stiliai page (SalesLoader, which asks for the orders of the chosen period when the owner presses the button: reading the
// order folders is the heaviest read of the admin, so the page does not do it unasked). Counting rules and money are in stylesView.ts (styleSales); the page test calls them.
import { useRef, useState } from 'react';
import type React from 'react';
import type { OrderRow, Orders } from './api';
import type { Call } from './AdminApp';
import { explain } from './format';
import { periodWords, salesMoney, styleSales } from './stylesView';
import { BTN, CARD, MUTED, Notice, Spinner, Tbl } from './ui';

/** The two tables (by group, by style) and the sentence that says what each column is. `more`: the list was cut short. */
export const SalesTables: React.FC<{ rows: OrderRow[]; more: boolean; days: number }> = ({ rows, more, days }) => {
  const { byStyle, byGroup, total } = styleSales(rows);
  return (
    <div className="flex flex-col gap-3">
      <p className={`text-xs ${MUTED}`}>
        Užsakymai ({periodWords(days)}): visi užsakymų aplankai su tuo stiliumi, apmokėti ar ne. Apmokėta: tikri mokėjimai. Pajamos: tik tikri mokėjimai, kiekviena valiuta atskirai, grąžinimai neatimami
        (užsakymų sąrašas jų nežino; atsisakymo pareiškimų tarp apmokėtų: {total.withdrawn}). Testiniai mokėjimai skaičiuojami atskirai ir į pajamas neįeina.
        {more ? ' Rodoma ne viskas: pasirink trumpesnį laikotarpį.' : ''}
      </p>
      <p className="text-sm">Iš viso: užsakymų <b>{total.orders}</b>, apmokėta <b>{total.paid}</b>, pajamos <b>{salesMoney(total.revenue)}</b></p>
      <h4 className="text-xs font-bold text-white/80">Pagal grupę</h4>
      <Tbl label="Užsakymai ir pajamos pagal grupę" head={['Grupė', 'Užsakymai', 'Apmokėta', 'Pajamos', 'Testiniai mokėjimai']} empty="Užsakymų šiame laikotarpyje nėra."
        rows={byGroup.map((r) => [r.name, String(r.orders), String(r.paid), salesMoney(r.revenue), String(r.test)])} />
      <h4 className="text-xs font-bold text-white/80">Pagal stilių</h4>
      <Tbl label="Užsakymai ir pajamos pagal stilių" head={['Stilius', 'Grupė', 'Užsakymai', 'Apmokėta', 'Pajamos', 'Testiniai mokėjimai']} empty="Užsakymų šiame laikotarpyje nėra."
        rows={byStyle.map((r) => [r.name, byGroup.find((g) => g.group === r.group)?.name || '-', String(r.orders), String(r.paid), salesMoney(r.revenue), String(r.test)])} />
    </div>
  );
};

/** In the order list: a fold under the filters, closed so that the list stays where the owner looks for it; its heading carries the totals. */
export const SalesDetails: React.FC<{ rows: OrderRow[]; more: boolean; days: number }> = ({ rows, more, days }) => {
  const { total } = styleSales(rows);
  return (
    <details className="rounded-xl border border-white/10 bg-black/20">
      <summary className="cursor-pointer select-none px-3 py-2 text-sm font-semibold">
        Užsakymai ir pajamos pagal stilių ir grupę: apmokėta {total.paid}, pajamos {salesMoney(total.revenue)}
      </summary>
      <div className="p-3"><SalesTables rows={rows} more={more} days={days} /></div>
    </details>
  );
};

/** On the Stiliai page: a card that asks for the orders of the period the numbers show when the owner presses the button, and says when what it shows is another period. */
export const SalesLoader: React.FC<{ call: Call; days: number }> = ({ call, days }) => {
  const [res, setRes] = useState<{ days: number; data: Orders } | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const seq = useRef(0);
  const load = async () => {
    const mine = ++seq.current;
    setBusy(true);
    const r = await call<Orders>('orders', { days }, 90_000);
    if (mine !== seq.current) return;                       // a newer press has its own answer
    setBusy(false);
    if (r.ok && r.data) { setRes({ days, data: r.data }); setErr(''); } else setErr(explain(r));
  };
  return (
    <section className={`${CARD} flex flex-col gap-3`} aria-label="Užsakymai ir pajamos pagal stilių ir grupę">
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <h3 className="text-sm font-bold">Užsakymai ir pajamos pagal stilių ir grupę</h3>
        <span className="text-[11px] text-white/45">iš užsakymų įrašų, ne iš įvykių; filtras netaikomas</span>
      </div>
      <p className={`text-xs ${MUTED}`}>Įvykiuose sumų nėra, todėl pajamos skaičiuojamos iš užsakymų aplankų. Tai sunkiausias skaitymas, todėl užkraunama tik paspaudus.</p>
      <div><button type="button" className={BTN} onClick={() => void load()} disabled={busy}>{busy && <Spinner />}{res ? 'Atnaujinti' : 'Rodyti'} (paskutinės {days} d.)</button></div>
      {err && <Notice>{err}</Notice>}
      {res && res.days !== days && <p className={`text-xs ${MUTED}`}>Rodoma paskutinių {res.days} d., o skaičiams pasirinkta {days} d.: paspausk, kad atnaujintum.</p>}
      {res && <SalesTables rows={res.data.orders} more={res.data.more} days={res.days} />}
    </section>
  );
};
