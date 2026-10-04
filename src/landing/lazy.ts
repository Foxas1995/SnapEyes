// Lazy sections that survive a bad network and a new deploy.
//
// Every section below the first screen is a chunk of its own (src/landing/sectionLoaders.ts, mounted by src/landing/sectionQueue.ts; the
// size guide and "More ways to see it" inside the wall are React.lazy, src/landing/Wall.tsx). A chunk can fail to load: a phone on a
// flaky connection, a content blocker, a CDN hiccup, and above all a deploy while the page is open (the chunk names are hashed and
// served immutable, so an old name is a 404 on the new deployment). Without care a rejected import throws during render, and with no
// error boundary React 19 unmounts the whole root: a blank page. So:
//   loadRetry   asks once more after a short wait (a transient failure then costs nothing; lazyRetry is the React.lazy of it);
//   skew        when the retry fails too, the page asks the server for a fresh index.html: if that no longer names the script this
//               page runs on, a new deploy is live and the old chunks are gone, so the page reloads itself (at most once a minute);
//   boundary    (./SectionBoundary.tsx) a section that cannot be loaded is missing, the rest of the page stays.
import { lazy, type ComponentType, type LazyExoticComponent } from 'react';

const RETRY_MS = 800;
const RELOAD_KEY = 'snapeyes.skewReload';
const RELOAD_GAP_MS = 60_000;

/** The file name of the script this page runs on (the loader of index.html adds it as the one module script of /assets/), or '' (dev server). */
function runningScript(): string {
  const s = document.querySelector<HTMLScriptElement>('script[type="module"][src*="/assets/"]');
  return s ? new URL(s.src, window.location.href).pathname : '';
}

let asked = false;

/** A chunk failed twice: if the server's index.html is another deploy's, reload once; if it is still ours, the network was the problem
 *  and the visitor keeps the page without that section. */
export function checkDeploySkew(): void {
  if (asked || !import.meta.env.PROD) return;
  asked = true;
  const mine = runningScript();
  if (!mine) return;
  void fetch('/', { cache: 'no-store', credentials: 'same-origin' })
    .then((r) => (r.ok ? r.text() : ''))
    .then((html) => {
      if (!html || html.includes(mine)) return;
      try {
        const last = Number(window.sessionStorage.getItem(RELOAD_KEY) ?? '0');
        if (Date.now() - last < RELOAD_GAP_MS) return;
        window.sessionStorage.setItem(RELOAD_KEY, String(Date.now()));
      } catch {
        return;
      }
      window.location.reload();
    })
    .catch(() => undefined);
}

/** An import that asks again once after a failure, and looks for a new deploy when the second try fails too. */
export function loadRetry<M>(load: () => Promise<M>): Promise<M> {
  return load()
    .catch(() => new Promise<void>((done) => setTimeout(done, RETRY_MS)).then(load))
    .catch((e: unknown) => {
      checkDeploySkew();
      throw e;
    });
}

/** React.lazy with loadRetry (for the blocks inside a section that are chunks of their own). */
export function lazyRetry<T extends ComponentType<any>>(load: () => Promise<{ default: T }>): LazyExoticComponent<T> {
  return lazy(() => loadRetry(load));
}

/** Vite's own signal for a failed preload or import (a stylesheet or a script a chunk depends on, or the chunk itself): look for a new
 *  deploy. The event is NOT cancelled on purpose: Vite swallows the error of a cancelled event and the import then "succeeds" with
 *  nothing in it, a section that waits for ever. Left alone the import rejects, and loadRetry above is the one that decides. Call once at start. */
export function watchPreloadErrors(): void {
  window.addEventListener('vite:preloadError', () => {
    checkDeploySkew();
  });
}
