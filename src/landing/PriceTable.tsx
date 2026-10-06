// The price table of the pricing block: a free preview row first, then the four prices the page sells by. Every price is the
// visitor's own (src/landing/prices.ts: their variant's ladder while a price experiment runs for them) and is held back
// (PriceGate) until the server's first answer about the prices has arrived, so nobody sees the standard price for a moment
// and nothing moves when the price appears. No price is written here: the texts come from the hook, the words from the copy.
// Motion (motion spec 6.12): a row's own hairline draws when the table comes into view (data-reveal="rule", one row after the other,
// .12 s apart, css/pricing.css); the words and the price in the row never move, fade or change: nothing animates on a price.
import type { ReactNode } from 'react';
import { useCopy } from './copy/useCopy';
import type { LandingCopy } from './copy/index';
import { useLandingPrices } from './prices';
import { useSaleCatalogue } from './ordering';
import { PriceGate } from './ui';
import { GALLERY } from './assets.data';
import { liveFor, severalMax, type RunCatalogue } from '../shared/catalogue';
import { priceClass } from '../shared/styles';
import { tileStyle } from './tileStyle';

// WHAT IS PRICED. A row prints a price only for what the run-time catalogue (src/shared/catalogue.ts, through src/landing/ordering.ts
// useSaleCatalogue: what can be bought NOW, nothing while ordering is closed) says can be bought; every other row says Soon and keeps its words. The rows name
// price CLASSES and counts of eyes, never a list of styles written here: the black class by what the catalogue lists in it, the art class by the names of the
// gallery's tiles whose style is live now, the number of eyes by what every smaller count can be ordered for (severalMax). The Trio alone (three eyes, no pair)
// prints the price of three eyes and no sentence about two.

/** The names of the one-eye tiles of the art class that can be bought now ("Powder Burst, Splash, ..."), taken from the style gallery's own tiles, so the price row
 *  and the tiles can never disagree about which styles cost that. With none live the row says Soon and lists every art tile (it names nothing as sold). */
function artStyleNames(c: LandingCopy, cat: RunCatalogue): string {
  const items = c.styles.items as Readonly<Record<string, { n: string } | undefined>>;
  const art = GALLERY.one.filter((tile) => tile.price === 'art');
  const live = art.filter((tile) => {
    const target = tileStyle(tile);
    return target !== null && liveFor(cat, target.id, 1);
  });
  return (live.length ? live : art)
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
    <div className={free ? 'lp-prow lp-free' : 'lp-prow'} data-reveal="rule">
      <div>
        <b>{title}</b>
        <small>{note}</small>
      </div>
      <div className="lp-pv">{value}</div>
    </div>
  );
}

export function PriceTable() {
  const { c, t, fmt } = useCopy();
  const p = useLandingPrices();
  const cat = useSaleCatalogue();
  const rows = c.pricing.rows;
  const soon = <span className="lp-soon">{c.styles.soonTag}</span>;
  const gate = (text: ReactNode) => <PriceGate pending={p.pending}>{text}</PriceGate>;
  const classLive = (cls: 'black' | 'art') => cat.one.some((id) => priceClass(id) === cls);
  // the several-eyes ladder: two eyes, then each further eye, up to the count every smaller count of which can be ordered too (the Trio alone is none)
  const several = severalMax(cat);
  const three = cat.eyes.includes(3);
  const tokens = { ...p.tokens, styles: artStyleNames(c, cat), max: several };
  // the "three eyes" row: the full ladder sentence while the pairs and the three are all for sale, the Trio's own line when only the three is, else Soon
  const moreNote = several >= 3 ? fmt(rows.more.b, tokens) : three ? c.styles.items.fam_trio.d : t('pricing.severalSoon');
  return (
    <div className="lp-ptable" data-stagger>
      <Row free title={rows.free.t} note={fmt(rows.free.b)} value={c.pricing.free} />
      <Row title={rows.black.t} note={fmt(rows.black.b)} value={classLive('black') ? gate(p.black) : soon} />
      <Row title={rows.art.t} note={fmt(rows.art.b, tokens)} value={classLive('art') ? gate(p.art) : soon} />
      <Row title={rows.two.t} note={fmt(rows.two.b)} value={cat.eyes.includes(2) ? gate(p.price2) : soon} />
      {/* three eyes: a sentence that names the two-eye price and the price of each further eye waits for the ladder too */}
      <Row title={rows.more.t} note={several >= 3 ? gate(moreNote) : moreNote} value={several >= 3 || three ? gate(p.eyes(3)) : soon} />
    </div>
  );
}

export default PriceTable;
