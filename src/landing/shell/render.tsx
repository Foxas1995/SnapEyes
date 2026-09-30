// The static first screen, made at build time. vite.config.ts (the heroShell plugin) loads this file through Vite's module
// runner in Node and writes what it returns into index.html. Nothing here runs in the browser.
//
// The shell is the English first screen of the default market: notice bar, header, hero with the LCP picture, the lead, the
// call to action. It is rendered by the SAME components as the live first screen (./parts.tsx), so the two cannot drift
// apart in markup; scripts/check_shell.mjs measures that they also occupy the same boxes at 375, 768 and 1280 px.
//
// The price of the micro line is a build-time input (fromPrice), held back in the markup like every price of the page until
// the server has answered (./parts.tsx): the plugin takes it from the price modules, this file never reads a price.
import { renderToStaticMarkup } from 'react-dom/server';
import { COPY_EN } from '../copy/index';
import { fill } from '../copy/format';
import { tryUrl } from '../config';
import { HERO_SIZES, heroPicture } from './hero';
import { ShellHero, ShellTop } from './parts';
import type { Lang } from '../../shared/lang';

export interface ShellInput {
  /** The lowest one-eye price as the page writes it in the shell's language and currency ("€19.97"). */
  fromPrice: string;
  /** The language buttons of the shell: the languages the new landing speaks. */
  langs: Lang[];
}

export interface ShellOutput {
  /** The markup that goes into <div id="shell">. */
  html: string;
  /** <link rel="preload"> for the LCP picture, with the same srcset and sizes as the image in the shell. */
  preload: string;
  /** The head's texts from the copy (title, description, share texts). */
  meta: { title: string; description: string; shareDescription: string; locale: string };
  lang: Lang;
}

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

export function renderShell({ fromPrice, langs }: ShellInput): ShellOutput {
  const copy = COPY_EN;
  const lang: Lang = 'en';
  const tryHref = tryUrl(lang);
  const html = renderToStaticMarkup(
    <>
      <ShellTop copy={copy} lang={lang} langs={langs} barText={copy.bar.soon} tryHref={tryHref} />
      <main id="main">
        <ShellHero copy={copy} tryHref={tryHref} priceLine={fill(copy.hero.fromPrice, copy.facts, { from: fromPrice })} pricePending />
      </main>
    </>,
  );
  const pic = heroPicture();
  const preload = `<link rel="preload" as="image" type="image/webp" fetchpriority="high" imagesrcset="${esc(pic.srcset ?? pic.src)}" imagesizes="${esc(HERO_SIZES)}" href="${esc(pic.src)}" />`;
  // React 19 writes a preload hint for an image with fetchPriority high in front of the markup; the head already has the
  // preload (above), so this copy would only be a second request hint inside the body
  return { html: html.replace(/^<link rel="preload" as="image"[^>]*\/>/, ''), preload, meta: copy.meta, lang };
}
