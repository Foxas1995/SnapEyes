// The static first screens, made at build time. vite.config.ts (the heroShell plugin) loads this file through Vite's module runner in
// Node and writes what it returns into index.html. Nothing here runs in the browser.
//
// A first screen is the notice bar, the header, the hero with the LCP picture, the lead and the call to action, of the DEFAULT market,
// in one language. The English one is the markup of index.html; the German, Lithuanian and Hungarian ones are <template>s next to it
// (an inert element: its content has no ids in the document, loads nothing and costs no layout), and a small inline script
// (scripts.ts swapScript) puts the visitor's own language in place before the first paint. So a Lithuanian or a Hungarian visitor
// sees their own words and the LCP picture at once, as an English one does, instead of a blank page until React's first render.
// All four are rendered by the SAME components as the live first screen (src/landing/SiteTopView.tsx and HeroView.tsx), so the shell
// and the page cannot drift apart in markup; scripts/check_shell.mjs measures that they also occupy the same boxes, in every language,
// at 375, 768 and 1280 px.
//
// The price of the micro line is held back in the markup like every price of the page until the server has answered (HeroView), and a held line
// carries no price at all (src/landing/heroPrice.ts HELD_PRICE): this file never reads a price.
import { renderToStaticMarkup } from 'react-dom/server';
import en from '../copy/en.json';
import de from '../copy/de.json';
import lt from '../copy/lt.json';
import hu from '../copy/hu.json';
import type { LandingCopy } from '../copy/types';
import { fill } from '../copy/format';
import { tryUrl } from '../config';
import { HERO_SIZES, heroPicture } from './hero';
import { HeroView } from '../HeroView';
import { HELD_PRICE } from '../heroPrice';
import { SiteTopView } from '../SiteTopView';
import type { Lang } from '../../shared/lang';

const COPIES: Record<Lang, LandingCopy> = { en, de, lt, hu };

export interface ShellInput {
  /** The language buttons of the shells: the languages the default market can be read in. */
  langs: Lang[];
}

export interface ShellOutput {
  /** The markup that goes into <div id="shell"> (English). */
  html: string;
  /** The other languages' markup, each for a <template id="tpl-<lang>"> (the same content as html, in that language). */
  templates: Partial<Record<Lang, string>>;
  /** <link rel="preload"> for the LCP picture, with the same srcset and sizes as the image in the shell. */
  preload: string;
  /** The head's texts from the English copy (title, description, share texts). */
  meta: { title: string; description: string; shareDescription: string; locale: string };
  lang: Lang;
}

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

function renderOne(lang: Lang, langs: Lang[]): string {
  const copy = COPIES[lang];
  const tryHref = tryUrl(lang);
  const html = renderToStaticMarkup(
    <>
      <SiteTopView copy={copy} lang={lang} langs={langs} barText={copy.bar.soon} tryHref={tryHref} />
      <main id="main">
        <HeroView copy={copy} tryHref={tryHref} priceLine={fill(copy.hero.fromPrice, copy.facts, { from: HELD_PRICE })} pricePending />
      </main>
    </>,
  );
  // React 19 writes a preload hint for an image with fetchPriority high in front of the markup; the head already has the
  // preload, so this copy would only be a second request hint inside the body
  return html.replace(/^<link rel="preload" as="image"[^>]*\/>/, '');
}

export function renderShell({ langs }: ShellInput): ShellOutput {
  const templates: Partial<Record<Lang, string>> = {};
  for (const lang of Object.keys(COPIES) as Lang[]) if (lang !== 'en') templates[lang] = renderOne(lang, langs);
  const pic = heroPicture();
  const preload = `<link rel="preload" as="image" type="image/webp" fetchpriority="high" imagesrcset="${esc(pic.srcset ?? pic.src)}" imagesizes="${esc(HERO_SIZES)}" href="${esc(pic.src)}" />`;
  return { html: renderOne('en', langs), templates, preload, meta: COPIES.en.meta, lang: 'en' };
}
