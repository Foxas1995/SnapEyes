// The landing's lines about printing follow the server's print state (2026-11-21: a print is ordered from the order page after the artwork is delivered, so
// "No ... we do not print or ship" would be false once the owner turns the print switch on). The page learns the state the way it learns that ordering is open:
// from GET /api/checkout (src/landing/ordering.ts: its `prints`, api/_lib/prints.py public_info). While no print is sold in the page's market every line is the
// line of before; while one is, the two FAQ answers about printing and the pricing line take their prints wording (faq aPrints, pricing.notIncludesPrints).
// Pure page code, loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results, prints nothing. The build's gate renders the same states
// (scripts/landing_gate.mjs) and check:landing reads them in a browser.
import en from '../../src/landing/copy/en.json';
import de from '../../src/landing/copy/de.json';
import lt from '../../src/landing/copy/lt.json';
import hu from '../../src/landing/copy/hu.json';
import hr from '../../src/landing/copy/hr.json';
import fi from '../../src/landing/copy/fi.json';
import et from '../../src/landing/copy/et.json';
import lv from '../../src/landing/copy/lv.json';
import { copyForMarket, faqEntries } from '../../src/landing/copy/index';
import type { LandingCopy } from '../../src/landing/copy/types';
import { createOrdering, printMarketsOf, type Ask } from '../../src/landing/ordering';
import { PRINT_OFFER } from '../../src/shared/prints';

type Row = [string, boolean, string?];
const COPIES = { en, de, lt, hu, hr, fi, et, lv } as unknown as Record<string, LandingCopy>;
const LANGS = ['en', 'de', 'lt', 'hu', 'hr', 'fi', 'et', 'lv'] as const;
const DASH = new RegExp('[' + [0x2012, 0x2013, 0x2014, 0x2015].map((c) => String.fromCharCode(c)).join('') + ']');

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);

  // what the answer says
  check('printMarketsOf: the markets of an answer that says prints are on; none while it says nothing, says off, or names no market',
    printMarketsOf({ prints: { on: true, markets: ['eu', 'lt', 'hr'] } }).join() === 'eu,lt,hr' && printMarketsOf({}).length === 0 && printMarketsOf(null).length === 0
      && printMarketsOf({ prints: { on: false, markets: ['eu'] } }).length === 0 && printMarketsOf({ prints: { on: true } }).length === 0
      && printMarketsOf({ prints: { on: true, markets: [1, 'eu', null] } }).join() === 'eu' && printMarketsOf({ prints: 'yes' }).length === 0);

  // the store: the page's own asking code with a stand-in server
  const styles = [{ id: 'solo.powder', name: 'Powder Burst', slug: 'powder-burst', group: 'one', eyes: [1, 1], stages: { 1: 'live' } }];
  const ask = (answer: Record<string, unknown> | null): Ask => async (path) => {
    if (answer === null) throw new Error('unreachable');
    const body = path === '/api/health' ? { ok: true, stripe: true, stripe_live: false, email: true } : answer;
    return new Response(JSON.stringify(body), { status: 200, headers: { 'content-type': 'application/json' } });
  };
  const store = async (answer: Record<string, unknown> | null) => { const s = createOrdering(ask(answer), true); await s.start(); return s; };
  const prints = { on: true, currency: 'EUR', markets: [...PRINT_OFFER.markets] };
  const openOn = await store({ ok: true, open: true, styles, orderable_max_eyes: 1, prints });
  const openOff = await store({ ok: true, open: true, styles, orderable_max_eyes: 1 });
  const closedOn = await store({ ok: true, open: false, styles: [], orderable_max_eyes: 0, prints });
  const noStyle = await store({ ok: true, open: true, styles: [], orderable_max_eyes: 0, prints });
  const gone = await store(null);
  check('the store keeps the markets the server sells prints in only while orders can be placed: open with prints on (eu, lt, hr); none with prints off, while ordering is '
    + 'closed, while no style can be ordered, and when the server cannot be read',
    openOn.open() && openOn.printMarkets().join() === 'eu,lt,hr' && openOff.open() && openOff.printMarkets().length === 0 && !closedOn.open() && closedOn.printMarkets().length === 0
      && !noStyle.open() && noStyle.printMarkets().length === 0 && gone.printMarkets().length === 0,
    [openOn.printMarkets().join(), openOff.printMarkets().join(), closedOn.printMarkets().join(), noStyle.printMarkets().join()].join(' / '));
  check('the same array is handed out until an answer changes it (a stable snapshot for the components), and the markets without prints are not in it',
    openOn.printMarkets() === openOn.printMarkets() && openOff.printMarkets() === closedOn.printMarkets() && !openOn.printMarkets().includes('au') && !openOn.printMarkets().includes('hu')
      && !openOn.printMarkets().includes('us'));

  // the FAQ
  for (const l of LANGS) {
    const c = COPIES[l];
    const byId = (list: { id: string; q: string; a: string }[], id: string) => list.find((x) => x.id === id)!;
    const item = (id: string) => c.faq.items.find((i) => i.id === id) as { id: string; q: string; a: string; aPrints?: string };
    const closed = faqEntries(c, false, 0), open = faqEntries(c, true, 1), on = faqEntries(c, true, 1, true), closedOn2 = faqEntries(c, false, 0, true);
    const sentences = (t: string) => t.split(/(?<=[.!?]) /);
    const lost = sentences(item('printit').a).filter((x) => !sentences(item('printit').aPrints ?? '').includes(x));
    const gained = sentences(item('printit').aPrints ?? '').filter((x) => !sentences(item('printit').a).includes(x));
    check(`${l}: without prints the answers about printing are byte for byte the ones of before (closed, open, and closed with the switch on); with prints sold they are the `
      + 'prints wording, the questions the same, and no other item changes',
      byId(closed, 'print').a === item('print').a && byId(open, 'print').a === item('print').a && byId(closedOn2, 'print').a === item('print').a
        && byId(open, 'printit').a === item('printit').a && byId(on, 'print').a === item('print').aPrints && byId(on, 'printit').a === item('printit').aPrints
        && byId(on, 'print').q === item('print').q && on.length === open.length && on.every((e, i) => e.id === open[i].id && (e.id === 'print' || e.id === 'printit' || e.a === open[i].a) && e.q === open[i].q)
        && c.faq.items.filter((i) => 'aPrints' in i).map((i) => i.id).join() === 'print,printit');
    check(`${l}: the prints wording of "Can I print it?" is the old answer with ONE sentence replaced (the one that says we do not print or ship), its tokens kept; the answer `
      + '"Do you print or ship it?" and the pricing line name no price, hold no dash, and the pricing line keeps its sentence of before',
      lost.length === 1 && gained.length === 1 && (item('printit').aPrints ?? '').includes('{printMax}') && (item('printit').aPrints ?? '').includes('{printMaxCm}')
        && !/[0-9€$]/.test((item('print').aPrints ?? '') + gained[0]) && !DASH.test((item('print').aPrints ?? '') + gained[0] + c.pricing.notIncludesPrints)
        && c.pricing.notIncludesPrints.startsWith(`${c.pricing.notIncludes} `) && !/[0-9€$]/.test(c.pricing.notIncludesPrints)
        && (item('print').aPrints ?? '').length > 120 && item('print').aPrints !== item('print').a, `${lost.length} lost, ${gained.length} gained`);
  }
  check('eight different wordings (none is a copy of another language), and the English one says the three things: the order is the digital file, it can be printed anywhere, '
    + 'and a print can be ordered from us on the order page once the artwork is ready',
    new Set(LANGS.map((l) => (COPIES[l].faq.items.find((i) => i.id === 'print') as { aPrints?: string }).aPrints)).size === 8
      && new Set(LANGS.map((l) => COPIES[l].pricing.notIncludesPrints)).size === 8
      && /your order is the digital file/.test((en.faq.items.find((i) => i.id === 'print') as { aPrints: string }).aPrints)
      && /print it anywhere yourself/.test((en.faq.items.find((i) => i.id === 'print') as { aPrints: string }).aPrints)
      && /Once your artwork is ready, you can also order a print from us on your order page/.test((en.faq.items.find((i) => i.id === 'print') as { aPrints: string }).aPrints)
      // 2026-11-24: the list of that day (acrylic glass, glossy metal, canvas, poster, acrylic block); no digit in the answer (check:landing holds that)
      && /behind acrylic glass, on glossy metal, on canvas, as a poster or as an acrylic block, each made to order and shipped to you/.test((en.faq.items.find((i) => i.id === 'print') as { aPrints: string }).aPrints)
      && LANGS.every((l) => !/\d/.test((COPIES[l].faq.items.find((i) => i.id === 'print') as { aPrints: string }).aPrints)));
  // the Australian market replaces FAQ items by its own (no print is sold there, and the store names no such market): its copy keeps what it had
  const au = copyForMarket(COPIES.en, 'au' as never);
  check('the Australian edition\'s FAQ is untouched by the print state where its own answers stand, and the store never names the A$ market',
    faqEntries(au, true, 1).length === faqEntries(COPIES.en, true, 1).length && !PRINT_OFFER.markets.includes('au') && !PRINT_OFFER.markets.includes('us') && !PRINT_OFFER.markets.includes('hu'));
  return out;
}
