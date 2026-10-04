// The price table of the pricing block: a free preview row first, then the four prices the page sells by. Every price is the
// visitor's own (src/landing/prices.ts: their variant's ladder while a price experiment runs for them) and is held back
// (PriceGate) until the server's first answer about the prices has arrived, so nobody sees the standard price for a moment
// and nothing moves when the price appears. No price is written here: the texts come from the hook, the words from the copy.
import type { ReactNode } from 'react';
import { useCopy } from './copy/useCopy';
import type { LandingCopy } from './copy/index';
import { useLandingPrices } from './prices';
import { PriceGate } from './ui';
import { GALLERY } from './assets.data';

/** The names of the art styles that share the one-eye art price ("Radiance, Powder Burst, ..."), taken from the style gallery's
 *  own list, so the price row and the tiles can never disagree about which styles cost that. */
function artStyleNames(c: LandingCopy): string {
  const items = c.styles.items as Readonly<Record<string, { n: string } | undefined>>;
  return GALLERY.one
    .filter((tile) => tile.price === 'art')
    .map((tile) => items[tile.id]?.n ?? '')
    .filter((name) => name !== '')
    .join(', ');
}

interface RowProps {
  title: string;
  note: ReactNode;
  value: ReactNode;
  free?: boolean;
}

function Row({ title, note, value, free = false }: RowProps) {
  return (
    <div className={free ? 'lp-prow lp-free' : 'lp-prow'}>
      <div>
        <b>{title}</b>
        <small>{note}</small>
      </div>
      <div className="lp-pv">{value}</div>
    </div>
  );
}

export function PriceTable() {
  const { c, fmt } = useCopy();
  const p = useLandingPrices();
  const rows = c.pricing.rows;
  const tokens = { ...p.tokens, styles: artStyleNames(c) };
  const gate = (text: string) => <PriceGate pending={p.pending}>{text}</PriceGate>;
  return (
    <div className="lp-ptable">
      <Row free title={rows.free.t} note={fmt(rows.free.b)} value={c.pricing.free} />
      <Row title={rows.black.t} note={fmt(rows.black.b)} value={gate(p.black)} />
      <Row title={rows.art.t} note={fmt(rows.art.b, tokens)} value={gate(p.art)} />
      <Row title={rows.two.t} note={fmt(rows.two.b)} value={gate(p.price2)} />
      {/* three eyes: the sentence names the two-eye price and the price of each further eye, so it waits for the ladder too */}
      <Row title={rows.more.t} note={gate(fmt(rows.more.b, tokens))} value={gate(p.eyes(3))} />
    </div>
  );
}

export default PriceTable;
