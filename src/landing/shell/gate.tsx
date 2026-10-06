// The style gallery as the build's gate sees it: every tile and the price table rendered, in Node, by the SAME components the live page uses, for each state
// of the run-time catalogue a visitor can meet (nothing ticked, ordering open with nothing ticked, one style ticked, every live ceiling ticked, the server
// not reachable). scripts/check_landing_assets.mjs loads this file through Vite's module runner (as vite.config.ts does for src/landing/shell/render.tsx) and
// reads the markup; nothing here runs in the browser.
//
// Why render and read the markup instead of reading the source: the promise the page makes is what a visitor SEES. A tile that prints a price for a style the
// catalogue does not sell, a tile of a style that is not live without its Soon chip, a name that is not the registry's, or a picture that is not there, are
// all visible in the markup whichever file caused them (a component, the tile table, the copy, the manifest), and a build that reads the markup cannot be
// fooled by a change that keeps the source looking right.
//
// The answers (what GET /api/checkout says) are made by the caller from the registry (scripts/lib/stubapi.mjs) and so are the price texts of each language (the
// caller reads the price ladder, as vite.config.ts does for the first screen: no file of the landing reads it), so this file knows no style id and no price.
import type { ReactNode } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import en from '../copy/en.json';
import de from '../copy/de.json';
import lt from '../copy/lt.json';
import hu from '../copy/hu.json';
import type { LandingCopy } from '../copy/types';
import { CopyContext } from '../copy/useCopy';
import { makeApi } from '../copy/makeApi';
import { GALLERY } from '../assets.data';
import { GROUPS, artPicture, hasEyeSwitch, tilesOf, type EyeId } from '../gallery';
import { StyleTile } from '../StyleTile';
import { PriceTableView } from '../PriceTable';
import { HeroView } from '../HeroView';
import { heroPrice } from '../heroPrice';
import { groupLine } from '../tileState';
import type { LandingPrices } from '../priceText';
import type { LandingPricesState } from '../prices';
import { fallbackCatalogue, ordersOpen, readCatalogue, saleCatalogue } from '../../shared/catalogue';
import { LANGS, type Lang } from '../../shared/lang';

const COPIES: Record<Lang, LandingCopy> = { en, de, lt, hu };

/** One state of the catalogue to render: what GET /api/checkout answered (null: the server could not be read, the page keeps the build's fallback). */
export interface GateInput {
  name: string;
  answer: unknown;
}

export interface GateTile {
  id: string;
  group: string;
  /** The tile's markup (the own eye of the visitor's choice of eye colours). */
  html: string;
}

export interface GateLang {
  /** The words of the Soon chip in this language (styles.soonTag): what every tile that cannot be bought must carry. */
  soon: string;
  tiles: GateTile[];
  /** The price table's markup. */
  table: string;
  /** The hero's markup (its "Digital file from" line is held back, inert and invisible, while nothing can be bought for one eye). */
  hero: string;
}

export interface GateScenario {
  name: string;
  /** Whether the page treats ordering as open (the deployment takes orders AND some style can be ordered now). */
  open: boolean;
  /** What the page can sell in this state (the sale catalogue). */
  sale: { max: number; eyes: number[]; one: string[]; by: Record<string, number[]> };
  /** The line each group adds under its intro (soon, more or none). */
  lines: Record<string, 'soon' | 'more' | null>;
  langs: Partial<Record<Lang, GateLang>>;
}

export interface GateOutput {
  scenarios: GateScenario[];
  /** What could not be rendered at all (a component that throws for some state): "<what> (<state>, <language>): <why>". Empty when the page renders in every state. */
  errors: string[];
  /** The tile pictures that could not be made (a family that is not in the manifest): "<tile> in <eye colour>: <why>". Empty when every tile of every eye colour has its picture. */
  pictures: string[];
}

const noop = () => undefined;

/** What the build's gate needs to read, for each state of the catalogue and each language. */
export function renderGate(inputs: readonly GateInput[], pricesFor: (lang: Lang) => LandingPrices): GateOutput {
  const eyes: EyeId[] = GALLERY.eyes.map((e) => e.id);
  const pictures: string[] = [];
  const errors: string[] = [];
  for (const g of GROUPS) {
    for (const tile of tilesOf(g)) {
      for (const eye of hasEyeSwitch(g) ? eyes : (['own'] as EyeId[])) {
        try {
          const a = artPicture(tile, eye);
          if (!a.src || !a.w || !a.h) pictures.push(`${tile.id} in ${eye}: the picture has no file or no size`);
          if (!a.srcset || !/ 480w(,|$)/.test(a.srcset) || !/ 900w(,|$)/.test(a.srcset)) pictures.push(`${tile.id} in ${eye}: the picture does not offer its 480 and its 900 px files`);
        } catch (e) {
          pictures.push(`${tile.id} in ${eye}: ${e instanceof Error ? e.message : String(e)}`);
        }
      }
    }
  }
  const scenarios: GateScenario[] = inputs.map((input) => {
    const readable = readCatalogue(input.answer);
    const deploymentOpen = !!input.answer && typeof input.answer === 'object' && (input.answer as Record<string, unknown>).open === true && (input.answer as Record<string, unknown>).ok !== false;
    const catalogue = readable ?? fallbackCatalogue();
    const sale = saleCatalogue(deploymentOpen, catalogue);
    const lines: Record<string, 'soon' | 'more' | null> = {};
    for (const g of GROUPS) lines[g] = groupLine(tilesOf(g).map((t) => t.id), sale);
    const langs: Partial<Record<Lang, GateLang>> = {};
    for (const lang of LANGS) {
      const copy = COPIES[lang];
      const p: LandingPricesState = { ...pricesFor(lang), ready: true, pending: false, open: ordersOpen(deploymentOpen, catalogue) };
      const api = makeApi(copy, lang);
      const wrap = (node: ReactNode) => <CopyContext.Provider value={api}>{node}</CopyContext.Provider>;
      const tiles: GateTile[] = [];
      for (const g of GROUPS) {
        tilesOf(g).forEach((tile, index) => {
          let html = '';
          try {
            html = renderToStaticMarkup(
              wrap(<StyleTile tile={tile} group={g} eye="own" wallOn={false} wallAsked={false} onWall={noop} prices={p} sale={sale} enter="reveal" index={index} />),
            );
          } catch (e) {
            errors.push(`the tile ${tile.id} (${input.name}, ${lang}): ${e instanceof Error ? e.message : String(e)}`);
          }
          tiles.push({ id: tile.id, group: g, html });
        });
      }
      let table = '';
      let hero = '';
      try {
        table = renderToStaticMarkup(wrap(<PriceTableView p={p} sale={sale} />));
        const hp = heroPrice(p, p.pending, sale);
        hero = renderToStaticMarkup(<HeroView copy={copy} tryHref="/try" priceLine={api.t('hero.fromPrice', { from: hp.from })} pricePending={hp.held} />);
      } catch (e) {
        errors.push(`the price table or the hero (${input.name}, ${lang}): ${e instanceof Error ? e.message : String(e)}`);
      }
      langs[lang] = { soon: copy.styles.soonTag, tiles, table, hero };
    }
    return { name: input.name, open: ordersOpen(deploymentOpen, catalogue), sale: { max: sale.max, eyes: sale.eyes, one: sale.one, by: sale.by }, lines, langs };
  });
  return { scenarios, errors, pictures };
}
