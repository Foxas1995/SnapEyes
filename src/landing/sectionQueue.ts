// When each lazy section of the page is mounted (src/App.tsx Slot).
//
// The chunks of all nine sections are fetched at once, right after the first render (the network works in parallel), but a section
// is MOUNTED only when its code is here and the main thread has an idle slice (requestIdleCallback, at most 250 ms of waiting), one
// section at a time in page order. Left to React.lazy and Suspense the chunks arrive within a few milliseconds of each other and React
// reveals them together (it holds every Suspense reveal back for up to 300 ms after the fallback appeared): clusters of five sections
// in one task of 160 to 320 ms on a phone at CPU x4, during which the language buttons and the page's own links do not answer.
// A section the visitor comes near is let in at once, whatever its turn (the slot watches the screen with an IntersectionObserver,
// 1500 px ahead), so a fast scroller never waits for the queue. Until a section is mounted a slot, an empty section of the section's
// height and id (src/landing/slots.ts), holds its place; a section whose code cannot be fetched (after one more try, see lazy.ts)
// is left out and the page stays.
import { useSyncExternalStore, type ComponentType } from 'react';
import { loadRetry } from './lazy';
import { SECTION_LOADERS, type SectionName } from './sectionLoaders';

/** The sections in the order of the page, the first one to be let in first. */
export const SECTION_ORDER: readonly SectionName[] = ['reveal', 'wall', 'styles', 'how', 'pricing', 'closeups', 'trust', 'faq', 'final'];

const IDLE_TIMEOUT_MS = 250;
const NEAR_PX = 1500;

const opened = new Set<SectionName>();
const components = new Map<SectionName, ComponentType>();
const failed = new Set<SectionName>();
const loading = new Map<SectionName, Promise<void>>();
const listeners = new Set<() => void>();
let started = false;

function emit(): void {
  listeners.forEach((l) => l());
}

/** Fetch a section's code (once; a failed fetch is tried once more, see ./lazy.ts loadRetry). */
export function loadSection(name: SectionName): Promise<void> {
  let p = loading.get(name);
  if (!p) {
    p = loadRetry(SECTION_LOADERS[name]).then(
      (component) => {
        // an import that "succeeds" with nothing in it (Vite's preload helper does that when a failure event is cancelled) is a failure
        if (component == null) {
          failed.add(name);
        } else {
          components.set(name, component);
        }
        emit();
      },
      () => {
        failed.add(name);
        emit();
      },
    );
    loading.set(name, p);
  }
  return p;
}

/** Let a section in: it mounts as soon as its code is here (at once when it is). */
export function openSection(name: SectionName): void {
  if (opened.has(name)) return;
  opened.add(name);
  void loadSection(name);
  emit();
}

function idle(): Promise<void> {
  return new Promise((done) => {
    if (typeof window.requestIdleCallback === 'function') window.requestIdleCallback(() => done(), { timeout: IDLE_TIMEOUT_MS });
    else window.setTimeout(done, 60);
  });
}

/** Start the queue: fetch every section's code now, let the sections in one per idle slice in page order once their code is here.
 *  Call once, after the first render. */
export function startSections(): void {
  if (started) return;
  started = true;
  const loads = SECTION_ORDER.map((n) => loadSection(n));
  void (async () => {
    for (let i = 0; i < SECTION_ORDER.length; i++) {
      const name = SECTION_ORDER[i];
      if (opened.has(name)) continue;
      await loads[i];
      await idle();
      openSection(name);
    }
  })();
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** What a slot shows: 'failed' (nothing: the section could not be fetched), 'waiting' (the place holder: its turn has not come, or its
 *  code is not here yet), or the section's component. */
export function useSection(name: SectionName): ComponentType | 'waiting' | 'failed' {
  return useSyncExternalStore(
    subscribe,
    () => (failed.has(name) ? 'failed' : opened.has(name) ? (components.get(name) ?? 'waiting') : 'waiting'),
    () => 'waiting',
  );
}

/** The IntersectionObserver options of a slot: the section is let in when it is within NEAR_PX of the screen. */
export const NEAR_OPTIONS: IntersectionObserverInit = { rootMargin: `${NEAR_PX}px 0px` };
