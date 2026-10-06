// The landing page as the build's gate sees it: the WHOLE styles chapter (every group of the gallery with its tiles, its line and its combo card), the price table, the hero and the FAQ
// rendered, in Node, by the SAME components the live page uses (StyleGallery, PriceTable, HeroSection, Faq), for each state of the run-time catalogue a visitor can meet (nothing
// ticked, ordering open with nothing ticked, one style ticked, every live ceiling ticked, more than the ceilings allow today, the server not reachable).
// scripts/check_landing_assets.mjs loads this file through Vite's module runner (as vite.config.ts does for src/landing/shell/render.tsx) and reads the markup; nothing here runs in the browser.
//
// Why render and read the markup instead of reading the source: the promise the page makes is what a visitor SEES. A tile that prints a price for a style the catalogue does not sell,
// a tile of a style that is not live without its Soon chip, a name that is not the registry's, a picture that is not there, a hero line, a group line, a combo card or an FAQ answer
// that says more than the engine sells, are all visible in the markup whichever file caused them (a component, the wiring that hands it the catalogue, the tile table, the copy, the
// manifest), and a build that reads the markup cannot be fooled by a change that keeps the source looking right.
//
// What is rendered is the WIRED page, not views handed what the gate chose: the components read the catalogue through the hooks of the live page (src/landing/ordering.ts), and the
// gate gives them a store of its own (OrderingContext) that asks a stand-in server with the answer of the state; so the asking code (health, checkout, the rule that turns an answer
// into what can be bought) runs here too. The prices come from the visitor's own ladder as on the live page (the default market's: src/landing/prices.ts), the language from LangProvider.
//
// The answers (what GET /api/checkout says) are made by the caller from the registry (scripts/lib/stubapi.mjs); the prices the markup must print are worked out by the caller too,
// from the server's own price rule (scripts/check_landing_assets.mjs renderLanding), so this file knows no style id and no price.
import type { ReactNode } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import en from '../copy/en.json';
import de from '../copy/de.json';
import lt from '../copy/lt.json';
import hu from '../copy/hu.json';
import type { LandingCopy } from '../copy/types';
import { CopyContext } from '../copy/useCopy';
import { makeApi } from '../copy/makeApi';
import { LangProvider } from '../lang';
import { GALLERY } from '../assets.data';
import { GROUPS, artPicture, hasEyeSwitch, tileKey, tilesOf, type EyeId, type GalleryGroup } from '../gallery';
import { OrderingContext, createOrdering, type Ask } from '../ordering';
import { StyleGallery } from '../StyleGallery';
import { PriceTable } from '../PriceTable';
import { HeroSection } from '../Hero';
import { Faq } from '../Faq';
import { SiteTop } from '../SiteTop';
import { Pricing } from '../Pricing';
import { HowItWorks } from '../HowItWorks';
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
  /** The tile's markup, cut out of its group's (the own eye of the visitor's choice of eye colours). */
  html: string;
}

/** The words of the page the markup is read against: what a chip, a line and a card must say in this language. */
export interface GateWords {
  /** The Soon chip (styles.soonTag): what every tile and price row that cannot be bought must carry. */
  soon: string;
  /** The line under a group's intro when only some of its tiles can be bought (styles.moreSoon), and when none can (pricing.severalSoon). */
  moreSoon: string;
  severalSoon: string;
  /** The combo card of the pairs and the families: its title with the number of eyes ({max}), and the title and nothing else when no count of eyes can be sold. */
  comboTitle: string;
  comboTitleSoon: string;
  /** What the places that say whether ordering is open say in each state: the notice bar, the pricing notice and its payment line, the third step of how it works. */
  barSoon: string;
  barOpen: string;
  notice: string;
  noticeOpen: string;
  payOpen: string;
  step3: string;
  step3Open?: string;
}

/** One question of the FAQ as the copy holds it (the plain wording and the one for an open deployment): the gate works out which one the visitor must read. */
export interface GateFaqItem {
  id: string;
  q: string;
  a: string;
  qOpen?: string;
  aOpen?: string;
}

export interface GateLang {
  words: GateWords;
  /** The words of the Soon chip in this language (styles.soonTag): what every tile that cannot be bought must carry. Same as words.soon. */
  soon: string;
  /** Every tile of the gallery, cut out of the markup of its group. */
  tiles: GateTile[];
  /** The markup of the styles chapter of each group (the intro, the group's line, the tiles, the combo card). */
  groups: Record<string, string>;
  /** The price table's markup. */
  table: string;
  /** The hero's markup (its "Digital file from" line is held back, inert and invisible, while nothing can be bought for one eye). */
  hero: string;
  /** The FAQ's markup. */
  faq: string;
  /** The notice bar and the header, the pricing block (its notice and its payment line) and the three steps: the other places of the page that say whether ordering is open. */
  top: string;
  pricing: string;
  how: string;
  /** The copy's items the FAQ is made from (the gate checks the answer the markup holds against the wording the state calls for). */
  faqItems: GateFaqItem[];
}

export interface GateScenario {
  name: string;
  /** Whether the page treats ordering as open (the deployment takes orders AND some style can be ordered now): what the page's own store says after asking. */
  open: boolean;
  /** What the page can sell in this state (the sale catalogue the page's store holds). */
  sale: { max: number; eyes: number[]; one: string[]; by: Record<string, number[]> };
  langs: Partial<Record<Lang, GateLang>>;
}

export interface GateOutput {
  scenarios: GateScenario[];
  /** What could not be rendered at all (a component that throws for some state): "<what> (<state>, <language>): <why>". Empty when the page renders in every state. */
  errors: string[];
  /** The tile pictures that could not be made (a family that is not in the manifest): "<tile> in <eye colour>: <why>". Empty when every tile of every eye colour has its picture. */
  pictures: string[];
}

/** The stand-in server of a state: /api/health says Stripe is set up, /api/checkout answers what the state says; null is a server that cannot be reached. */
function askFor(answer: unknown): Ask {
  return async (path) => {
    if (answer === null) throw new Error('the server cannot be reached');
    const body = path === '/api/health' ? { ok: true, stripe: true, stripe_live: false, email: true } : answer;
    return new Response(JSON.stringify(body), { status: 200, headers: { 'content-type': 'application/json' } });
  };
}

/** The tiles of one group, cut out of its markup: a tile is a <figure data-k="<group><id>"> and nothing else in the chapter is. A tile that is not there is missing from the list. */
function tilesIn(group: GalleryGroup, html: string): GateTile[] {
  const byKey = new Map<string, string>();
  for (const piece of html.split('<figure ').slice(1)) {
    const end = piece.indexOf('</figure>');
    const key = /^[^>]*\sdata-k="([^"]*)"/.exec(piece)?.[1];
    if (key !== undefined && end >= 0) byKey.set(key, `<figure ${piece.slice(0, end + '</figure>'.length)}`);
  }
  const out: GateTile[] = [];
  for (const tile of tilesOf(group)) {
    const found = byKey.get(tileKey(group, tile));
    if (found !== undefined) out.push({ id: tile.id, group, html: found });
  }
  return out;
}

/** What the build's gate needs to read, for each state of the catalogue and each language. */
export async function renderGate(inputs: readonly GateInput[]): Promise<GateOutput> {
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
  const scenarios: GateScenario[] = [];
  for (const input of inputs) {
    // the page's own asking code, given the stand-in server of this state: it settles on what the page can sell
    const store = createOrdering(askFor(input.answer), true);
    await store.start();
    const sale = store.sale();
    const langs: Partial<Record<Lang, GateLang>> = {};
    for (const lang of LANGS) {
      const copy = COPIES[lang];
      const api = makeApi(copy, lang);
      const wrap = (node: ReactNode) => (
        <OrderingContext.Provider value={store}>
          <LangProvider initial={lang}>
            <CopyContext.Provider value={api}>{node}</CopyContext.Provider>
          </LangProvider>
        </OrderingContext.Provider>
      );
      const render = (what: string, node: ReactNode): string => {
        try {
          return renderToStaticMarkup(wrap(node));
        } catch (e) {
          errors.push(`${what} (${input.name}, ${lang}): ${e instanceof Error ? e.message : String(e)}`);
          return '';
        }
      };
      const groups: Record<string, string> = {};
      const tiles: GateTile[] = [];
      for (const g of GROUPS) {
        groups[g] = render(`the styles chapter, group ${g}`, <StyleGallery initialGroup={g} />);
        tiles.push(...tilesIn(g, groups[g]));
      }
      const table = render('the price table', <PriceTable />);
      const hero = render('the hero', <HeroSection />);
      const faq = render('the FAQ', <Faq />);
      const top = render('the notice bar', <SiteTop />);
      const pricing = render('the pricing block', <Pricing />);
      const how = render('the steps', <HowItWorks />);
      const step3 = copy.how.steps[2] as { b: string; bOpen?: string };
      langs[lang] = {
        words: {
          soon: copy.styles.soonTag, moreSoon: copy.styles.moreSoon, severalSoon: copy.pricing.severalSoon, comboTitle: copy.styles.comboTitle, comboTitleSoon: copy.styles.comboTitleSoon,
          barSoon: copy.bar.soon, barOpen: copy.bar.open, notice: copy.pricing.notice, noticeOpen: copy.pricing.noticeOpen, payOpen: copy.pricing.payOpen, step3: step3.b, step3Open: step3.bOpen,
        },
        soon: copy.styles.soonTag,
        tiles,
        groups,
        table,
        hero,
        faq,
        top,
        pricing,
        how,
        faqItems: copy.faq.items.map((it) => ({ id: it.id, q: it.q, a: it.a, qOpen: it.qOpen, aOpen: it.aOpen })),
      };
    }
    scenarios.push({ name: input.name, open: store.open(), sale: { max: sale.max, eyes: sale.eyes, one: sale.one, by: sale.by }, langs });
  }
  return { scenarios, errors, pictures };
}
