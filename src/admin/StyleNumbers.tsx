// The numbers of the Stiliai page (api/_lib/style_stats.py through the action styles_stats): the set level gate funnel and the opening criterion of every eye count, the demand for
// styles that cannot be bought yet, the recommended tile against the others, previews and tiles, the funnel after the preview, the restoration gate, the stack and Kiss fallbacks, render
// times against the estimate, errors and review by style, the Reveal. Every share is printed with the count behind it (rateText), a count that is small looks small, and the tables a
// filter does not slice are marked as whole. Lithuanian only; nothing here is typed text of a customer or an image: codes and counts.
import type React from 'react';
import type { StyleCatalogue, StylesStats } from './api';
import { AKYS, ltCount } from './format';
import {
  CLASS_LT, dec, ERROR_ENDPOINT_LT, fallbackLt, gateCodeLt, gateGroups, GROUP_LT, holdLt, msText, openingView, PUPIL_LT, rateText, RINKINIAI, REVEAL_LT, ROUTE_LT, shareText, WHAT_LT,
} from './stylesView';
import { CARD, MUTED, Tbl, ToneLine, WrapChip } from './ui';

const Block: React.FC<{ title: string; hint?: React.ReactNode; whole?: boolean; children: React.ReactNode }> = ({ title, hint, whole, children }) => (
  <section className={`${CARD} flex flex-col gap-3`} aria-label={title}>
    <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
      <h3 className="text-sm font-bold">{title}</h3>
      {whole && <span className="text-[11px] text-white/45">visi duomenys, filtras netaikomas</span>}
    </div>
    {hint && <p className={`text-xs ${MUTED}`}>{hint}</p>}
    {children}
  </section>
);

const codes = (t: Record<string, number>, name: (c: string) => string): string =>
  Object.entries(t).sort((a, b) => b[1] - a[1]).map(([c, n]) => `${name(c)}: ${n}`).join(', ') || '-';

const nameOf = (id: string, name: string | null | undefined): string => name || id;

/** The set level funnel (spec 1.6.2): per eye count and per colour class, with n, and the opening criterion of every count of two or more eyes. */
export const FunnelBlock: React.FC<{ s: StylesStats }> = ({ s }) => (
  <Block
    title="Rinkinių piltuvas: ar rinkinys praeina vartus"
    hint={`Rinkinys skaičiuojamas vieną kartą, pagal pirmą užklausą. „Su vienu pakartojimu“ yra viršutinė riba: puslapis nesieja vieno rinkinio dviejų užklausų, todėl pakartojimas rinkinio, kuris jau buvo praėjęs, taip pat įskaitomas, ne daugiau nei nepraėjusių. Užklausų iš viso: ${s.requests.total}, iš jų nieko nepiešusių: ${s.requests.drew_nothing}.`}
  >
    <Tbl label="Rinkinių piltuvas pagal akių skaičių"
      head={['Akys', 'Pirmos nuotraukos rinkiniai', 'Pirmą kartą praėjo', 'Su vienu pakartojimu (riba)', 'Pakartota po vieną kartą', 'Be profilio', 'Kodėl nepraėjo', 'Atidarymo kriterijus']}
      empty="Rinkinių dar nebuvo šiame laikotarpyje."
      rows={s.funnel.map((r) => {
        const v = openingView(r.eyes, r.line);
        return [
          ltCount(r.eyes, AKYS), ltCount(r.first, RINKINIAI), shareText(r.first_pass, r.first), rateText(r.rate_retake, r.first), shareText(r.retake1_pass, r.retake1),
          String(r.unknown), codes(r.fails, gateCodeLt), r.eyes >= 2 ? <ToneLine key="o" tone={v.tone}>{v.text}</ToneLine> : <span key="o" className={MUTED}>nereikia</span>,
        ];
      })} />
    <h4 className="text-xs font-bold text-white/80">Pagal rinkinio akių klasę</h4>
    <Tbl label="Rinkinių piltuvas pagal akių klasę"
      head={['Akys', 'Klasė', 'Pirmos nuotraukos rinkiniai', 'Pirmą kartą praėjo', 'Su vienu pakartojimu (riba)', 'Kodėl nepraėjo']}
      empty="Pagal klasę rinkinių dar nebuvo."
      rows={s.funnel_by_class.map((r) => [ltCount(r.eyes, AKYS), CLASS_LT[r.cls || ''] || r.cls || '-', ltCount(r.first, RINKINIAI), shareText(r.first_pass, r.first),
        rateText(r.rate_retake, r.first), codes(r.fails, gateCodeLt)])} />
  </Block>
);

/** Demand for the styles that cannot be bought yet (spec 1.8 rule 6) and the clicks on the manual route. */
export const DemandBlock: React.FC<{ s: StylesStats }> = ({ s }) => (
  <Block title="Paklausa stiliams, kurių dar negalima pirkti" hint="Matyti paveikslėliai, padarytos didelės peržiūros ir bandymai pirkti stilių, kuris buvo „Greitai“. Skaičiuojamas etapas, kuris stiliui buvo tada, kai jo paprašė.">
    <Tbl label="Paklausa pagal stilių ir akių skaičių"
      head={['Stilius', 'Akys', 'Etapas', 'Paveikslėliai', 'Didelės peržiūros', 'Paspaudė pirkti „Greitai“', 'Pirkimas atmestas']}
      empty="Paklausos dar nėra."
      rows={s.demand.map((r) => [nameOf(r.style, r.name), ltCount(r.eyes, AKYS), r.stage === 'live' ? 'parduodamas' : 'Greitai', String(r.tiles), String(r.large), String(r.soon), String(r.blocked)])} />
    <h4 className="text-xs font-bold text-white/80">Rankinis kelias (pirkėjas parašė tau)</h4>
    <div className="flex flex-wrap gap-1.5">
      {Object.keys(s.help.routes).length === 0 && <span className={`text-xs ${MUTED}`}>Paspaudimų nėra.</span>}
      {Object.entries(s.help.routes).map(([k, n]) => <WrapChip key={k}>{ROUTE_LT[k] || k}: {n}</WrapChip>)}
    </div>
    {Object.keys(s.help.why).length > 0 && <p className="text-xs">Priežastys: {codes(s.help.why, gateCodeLt)}</p>}
    {Object.keys(s.help.eyes).length > 0 && <p className="text-xs">Pagal akių skaičių: {codes(s.help.eyes, (c) => ltCount(Number(c), AKYS))}</p>}
  </Block>
);

/** Previews by style (tiles counted apart from the large previews), the recommended tile against the others, and by colour class. */
export const ChosenBlock: React.FC<{ s: StylesStats; cat?: StyleCatalogue | null }> = ({ s, cat }) => (
  <Block title="Peržiūros pagal stilių ir rekomendacija" hint="Paveikslėliai (480 px) skaičiuojami atskirai nuo didelių peržiūrų (1024 px), nes vienas rinkinys piešia kelis paveikslėlius.">
    <Tbl label="Peržiūros pagal stilių" head={['Stilius', 'Grupė', 'Didelės peržiūros', 'Paveikslėliai']} empty="Peržiūrų dar nebuvo."
      rows={s.previews.map((r) => {
        const g = cat?.styles.find((x) => x.id === r.style)?.group;
        return [nameOf(r.style, r.name), g ? GROUP_LT[g] || g : '-', String(r.previews), String(r.tiles)];
      })} />
    <p className="text-sm">
      Pasirinko rekomenduojamą paveikslėlį: <b>{rateText(s.chosen.share, s.chosen.pick + s.chosen.other)}</b>
      <span className={MUTED}> (rekomenduotą {s.chosen.pick}, kitą {s.chosen.other})</span>
    </p>
    <Tbl label="Rekomendacija pagal akių klasę" head={['Klasė', 'Rekomenduotą', 'Kitą', 'Dalis']} empty="Pagal klasę duomenų nėra."
      rows={s.chosen_by_class.map((r) => [CLASS_LT[r.cls] || r.cls, String(r.pick), String(r.other), rateText(r.share, r.n)])} />
  </Block>
);

/** The funnel after the preview: previews while the style was live, sessions started, paid; and the orders made on a set that failed the gate. */
export const ConversionBlock: React.FC<{ s: StylesStats }> = ({ s }) => (
  <Block title="Nuo peržiūros iki apmokėjimo pagal stilių" whole
    hint="Peržiūros: didelės peržiūros, kol stilius buvo parduodamas. Pradėta: sukurtas Stripe puslapis. Apmokėta: užfiksuotas mokėjimas. Kiekviena dalis su n.">
    {!s.conversion.recorded && <ToneLine tone="warn">Šiuo laikotarpiu mokėjimo įvykių dar neužfiksuota, todėl „pradėta“ ir „apmokėta“ rodo nulį ir nieko nesako.</ToneLine>}
    <Tbl label="Nuo peržiūros iki apmokėjimo" head={['Stilius', 'Akys', 'Peržiūros', 'Pradėta', 'Pradėta nuo peržiūrų', 'Apmokėta', 'Apmokėta nuo pradėtų']} empty="Duomenų dar nėra."
      rows={s.conversion.rows.map((r) => [nameOf(r.style, r.name), ltCount(r.eyes, AKYS), String(r.previews), String(r.started), rateText(r.rate_started, r.previews),
        String(r.paid), rateText(r.rate_paid, r.started)])} />
    <h4 className="text-xs font-bold text-white/80">Užsakyta po vartų nesėkmės (stilius, kurio vartai tik perspėja, perkamas ir ant nepraėjusio rinkinio)</h4>
    <Tbl label="Užsakyta po vartų nesėkmės" head={['Akys', 'Pradėta', 'Pradėta, nepraėjo vartai', 'Apmokėta', 'Apmokėta, nepraėjo vartai', 'Dalis apmokėtų', 'Kodai']} empty="Duomenų dar nėra."
      rows={s.after_failure.map((r) => [ltCount(r.eyes, AKYS), String(r.started), String(r.started_failed), String(r.paid), String(r.paid_failed),
        rateText(r.share_paid_failed, r.paid), codes(r.by_code, gateCodeLt)])} />
  </Block>
);

/** The restoration gate: failures per eye by reason code, class and pupil, and per style under its own rule. */
export const GateBlock: React.FC<{ s: StylesStats; skip?: Set<string> }> = ({ s, skip }) => (
  <Block title="Restauravimo vartai pagal akį" whole hint="Matuojama kiekvienai akiai kuriant peržiūrą, todėl nėra atrankos poveikio: akis, kurios stilius nepiešė, vis tiek skaičiuojama.">
    <p className="text-sm">Rezultatai: {codes(s.gate.codes, gateCodeLt)}</p>
    <p className="text-xs">Priežastys: {codes(s.gate.reasons, gateCodeLt)}</p>
    <p className="text-xs">Akių klasės: {codes(s.gate.classes, (c) => CLASS_LT[c] || c)}</p>
    <p className="text-xs">Vyzdžio klasės: {codes(s.gate.pupils, (c) => PUPIL_LT[c] || c)}</p>
    <Tbl label="Vartai pagal stilių" head={['Taisyklė', 'Vartai', 'Akių', 'Nepraėjo', 'Stiliai']} empty="Duomenų nėra."
      rows={gateGroups(s.gate.by_style, skip).map((g) => [g.rule, g.policy === 'hard' ? 'privalomi' : 'tik perspėja', String(g.seen), rateText(g.rate, g.seen), g.styles.join(', ')])} />
  </Block>
);

/** How often a style's picture fell back (Kiss for a wide pupil, one iris in front of the other for pairs of strongly different colours). */
export const FallbackBlock: React.FC<{ s: StylesStats }> = ({ s }) => (
  <Block title="Atsarginiai variantai" hint="Dalis to stiliaus paveikslėlių, kurie buvo nupiešti atsarginiu variantu (poroms: viena akis priekyje, kai spalvos stipriai skiriasi).">
    <Tbl label="Atsarginiai variantai pagal stilių" head={['Stilius', 'Variantas', 'Kartų', 'Dalis']} empty="Atsarginio varianto dar nereikėjo."
      rows={s.fallbacks.map((r) => [nameOf(r.style, r.name), fallbackLt(r.fallback), String(r.count), rateText(r.share, r.of)])} />
  </Block>
);

/** Render times against the cost table's estimate. */
export const TimesBlock: React.FC<{ s: StylesStats }> = ({ s }) => (
  <Block title="Piešimo laikai pagal stilių ir akių skaičių" whole
    hint={`p50 ir p95 yra intervalo viršutinė riba (ne daugiau kaip vienu intervalu per aukštai). „Planas“ yra kainų lentelės įvertis esamu lėtėjimo koeficientu. Atminties prieaugis yra proceso VmRSS padidėjimas per žingsnį${s.memory.peak_mb_avg !== null ? `: vidutiniškai ${dec(s.memory.peak_mb_avg)} MB (n ${s.memory.n})` : ''}; instancijos aukščiausią reikšmę (VmHWM) rodo užsakymo informacija.`}>
    <Tbl label="Piešimo laikai" head={['Kas', 'Stilius', 'Akys', 'n', 'p50', 'p95', 'Planas', 'Virš 64 s']} empty="Laikų dar nėra."
      rows={s.times.map((r) => {
        const over = r.need_s !== null && r.p95_ms !== null && r.p95_ms / 1000 > r.need_s;
        return [WHAT_LT[r.what] || r.what, nameOf(r.style, r.name), ltCount(r.eyes, AKYS), String(r.n), msText(r.p50_ms), over ? <WrapChip key="p" tone="bad">{msText(r.p95_ms)}, viršija planą</WrapChip> : msText(r.p95_ms),
          r.need_s !== null ? `${dec(r.need_s)} s` : 'nėra eilutės', r.over ? String(r.over) : '0'];
      })} />
  </Block>
);

/** Errors, held artworks and orders, failed colour checks and busy answers by style. */
export const ErrorsBlock: React.FC<{ s: StylesStats }> = ({ s }) => (
  <Block title="Klaidos ir peržiūra pagal stilių" whole>
    <Tbl label="Klaidos pagal stilių" head={['Stilius', 'Klaidų', 'Užklausų', 'Dalis']} empty="Klaidų su stiliumi nebuvo."
      rows={s.errors.map((r) => [nameOf(r.style, r.name), String(r.errors), String(r.asked), rateText(r.rate, r.asked)])} />
    <h4 className="text-xs font-bold text-white/80">Kūriniai, laukiantys tavo peržiūros</h4>
    <Tbl label="Peržiūros žymos pagal stilių" head={['Stilius', 'Sulaikyta', 'Pagaminta', 'Dalis']} empty="Duomenų nėra."
      rows={s.review.map((r) => [nameOf(r.style, r.name), String(r.review), String(r.made), rateText(r.rate, r.made)])} />
    <h4 className="text-xs font-bold text-white/80">Nepraėjusi spalvų patikra</h4>
    <Tbl label="Spalvų patikra pagal stilių" head={['Stilius', 'Nepraėjo', 'Paveikslėlių', 'Dalis']} empty="Nepraėjusių nebuvo."
      rows={s.qa.map((r) => [nameOf(r.style, r.name), String(r.qa_fail), String(r.of), rateText(r.rate, r.of)])} />
    <h4 className="text-xs font-bold text-white/80">Atsakymai „užimta, bandyk dar kartą“</h4>
    <Tbl label="Užimtumo atsakymai" head={['Kur', 'Stilius', 'Kartų']} empty="Nebuvo."
      rows={s.busy_retry.map((r) => [ERROR_ENDPOINT_LT[r.endpoint] || r.endpoint, r.name || (r.style === 'unknown' ? 'nenurodytas' : r.style), String(r.count)])} />
    <h4 className="text-xs font-bold text-white/80">Užsakymai, sulaikyti dėl gamybos žingsnio</h4>
    <p className="text-xs">{codes(s.holds, holdLt)}</p>
  </Block>
);

/** Reveal availability (the cut between the photo and the restored iris). */
export const RevealBlock: React.FC<{ s: StylesStats }> = ({ s }) => (
  <Block title="Atidengimas (Reveal): ar buvo ką parodyti" whole hint="Kiekvienai akiai kuriant peržiūrą: ar buvo galima parodyti nuotraukos ir atkurtos rainelės perėjimą.">
    <p className="text-sm">
      Rodoma: <b>{rateText(s.reveal.ok_share, s.reveal.n)}</b>
      {s.reveal.ms !== null && <span className={MUTED}> · vidutiniškai {dec(s.reveal.ms)} ms vienai akiai</span>}
    </p>
    <p className="text-xs">{codes(s.reveal.codes, (c) => REVEAL_LT[c] || c)}</p>
  </Block>
);
