// The price table of the pricing block: a free preview row first, then the four prices the page sells by. Every price is the
// visitor's own (src/landing/prices.ts: their variant's ladder while a price experiment runs for them) and is held back
// (PriceGate) until the server's first answer about the prices has arrived, so nobody sees the standard price for a moment
// and nothing moves when the price appears. No price is written here: the texts come from the hook, the words from the copy.
// Motion (motion spec 6.12): a row's own hairline draws when the table comes into view (data-reveal="rule", one row after the other,
// .12 s apart, css/pricing.css); the words and the price in the row never move, fade or change: nothing animates on a price.
import type { ReactNode } from 'react';
import { useCopy } from './copy/useCopy';
import { useLandingPrices, type LandingPricesState } from './prices';
import { useSaleCatalogue } from './ordering';
import { PriceGate } from './ui';
import { GALLERY } from './assets.data';
import { severalMax, type RunCatalogue } from '../shared/catalogue';
import { classStyle, priceClass, styleName } from '../shared/styles';
import { saleTiles } from './tileState';

// WHAT IS PRICED. While nothing can be bought (ordering is closed: the sale catalogue is empty) the table is the shop's price list (the owner, 2026-10-22:
// "why is everything soon?"): every row prints the server's price for its class or count of eyes (one eye on black, one eye in an art style, two eyes, three
// eyes with the sentence of each further eye), no row says Soon and no row names a style, and the ONE line above the table (Pricing.tsx, pricing.notice) says
// that ordering opens soon. Once ordering is open, a row prints a price only for what the run-time catalogue (src/shared/catalogue.ts, through
// src/landing/ordering.ts useSaleCatalogue: what can be bought NOW) says can be bought; every other row says Soon. The rows name
// price CLASSES and counts of eyes; the styles a row names are the REGISTRY's names of the gallery's tiles that can be bought now, and "More styles soon." follows
// when some tile of the row cannot, so the rows and the tiles can never disagree about what costs that. With none for sale the row names no style and says
// "More styles soon." The number of eyes is what every smaller count can be ordered for (severalMax). The Trio alone
// (three eyes, no pair) prints the price of three eyes and no sentence about two.

const ART_TILES: readonly string[] = GALLERY.one.filter((tile) => tile.price === 'art').map((tile) => tile.id);
const PAIR_TILES: readonly string[] = GALLERY.two.map((tile) => tile.id);

interface RowProps {
  title: string;
  note: ReactNode;
  value: ReactNode;
  free?: boolean;
}

function Row({ title, note, value, free = false }: RowProps) {
  return (
    <div className={free ? 'lp-prow lp-free' : 'lp-prow'} data-reveal="rule">
      <div>
        <b>{title}</b>
        {/* a row of the closed price list may have no line under its title (nothing for sale yet: no style to name); the element stays, empty, for the readers of the table */}
        <small>{note}</small>
      </div>
      <div className="lp-pv">{value}</div>
    </div>
  );
}

export interface PriceTableViewProps {
  /** The visitor's prices (src/landing/prices.ts). */
  p: LandingPricesState;
  /** What can be bought now (src/shared/catalogue.ts saleCatalogue). */
  sale: RunCatalogue;
}

/** The table for a given state of prices and sale: the hook-free half, rendered by the page and by the build's gate (src/landing/shell/gate.tsx). */
export function PriceTableView({ p, sale: cat }: PriceTableViewProps) {
  const { c, t, fmt } = useCopy();
  const rows = c.pricing.rows;
  const soon = <span className="lp-soon">{c.styles.soonTag}</span>;
  const gate = (text: ReactNode) => <PriceGate pending={p.pending}>{text}</PriceGate>;
  // nothing can be bought yet (the page says that ordering opens soon: the same flag as the notice above the table, ordersOpen): the whole price list, no Soon in
  // any row, no style named (see WHAT IS PRICED)
  const closed = !p.open;
  const classLive = (cls: 'black' | 'art') => closed || cat.one.some((id) => priceClass(id) === cls);
  // the several-eyes ladder: two eyes, then each further eye, up to the count every smaller count of which can be ordered too (the Trio alone is none); while
  // closed the ladder up to the most eyes one artwork holds
  const several = closed ? p.max : severalMax(cat);
  const three = closed || cat.eyes.includes(3);
  const tokens = { ...p.tokens, max: several };
  // a row that lists styles: the registry's names of the tiles that can be bought now, then "More styles soon." when some tile of the row cannot; nothing for sale: "More styles soon." alone.
  // While closed no row names a style (none can be bought yet, and the notice above already says ordering opens soon)
  const list = (text: string, ids: readonly string[], fallback: readonly string[]): ReactNode => {
    if (closed) return null;
    const s = saleTiles(ids, cat);
    const names = s.names.length ? s.names : fallback;
    if (!names.length) return c.styles.moreSoon;
    return (
      <>
        {fmt(text, { ...tokens, styles: names.join(', ') })}
        {s.sale < s.total && ` ${c.styles.moreSoon}`}
      </>
    );
  };
  // the "three eyes" row: the full ladder sentence while the pairs and the three are all for sale, the Trio's own line when only the three is, else the group's own line
  const moreNote = several >= 3 ? fmt(rows.more.b, tokens) : three ? c.styles.items.fam_trio.d : t('pricing.severalSoon');
  return (
    <div className="lp-ptable" data-stagger>
      <Row free title={rows.free.t} note={fmt(rows.free.b)} value={c.pricing.free} />
      <Row title={rows.black.t} note={fmt(rows.black.b, { name: styleName(classStyle('black')) })} value={classLive('black') ? gate(p.black) : soon} />
      <Row title={rows.art.t} note={list(rows.art.b, ART_TILES, classLive('art') ? cat.styles : [])} value={classLive('art') ? gate(p.art) : soon} />
      <Row title={rows.two.t} note={list(rows.two.b, PAIR_TILES, [])} value={closed || cat.eyes.includes(2) ? gate(p.price2) : soon} />
      {/* three eyes: a sentence that names the two-eye price and the price of each further eye waits for the ladder too */}
      <Row title={rows.more.t} note={several >= 3 ? gate(moreNote) : moreNote} value={several >= 3 || three ? gate(p.eyes(3)) : soon} />
    </div>
  );
}

export function PriceTable() {
  const p = useLandingPrices();
  const sale = useSaleCatalogue();
  return <PriceTableView p={p} sale={sale} />;
}

export default PriceTable;
