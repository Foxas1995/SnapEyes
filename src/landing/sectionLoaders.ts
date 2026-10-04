// The nine lazy sections of the page, one import each, each resolving to the section's component. src/landing/sectionQueue.ts calls them
// all right after the first render (the chunks travel in parallel) and mounts each section when its turn has come.
import type { ComponentType } from 'react';

type Loader = () => Promise<ComponentType>;

export const SECTION_LOADERS = {
  reveal: (() => import('./Reveal').then((m) => m.default)) as Loader,
  wall: (() => import('./Wall').then((m) => m.default)) as Loader,
  styles: (() => import('./StyleGallery').then((m) => m.StyleGallery)) as Loader,
  how: (() => import('./HowItWorks').then((m) => m.HowItWorks)) as Loader,
  pricing: (() => import('./Pricing').then((m) => m.default)) as Loader,
  closeups: (() => import('./CloseUps').then((m) => m.default)) as Loader,
  trust: (() => import('./Trust').then((m) => m.default)) as Loader,
  faq: (() => import('./Faq').then((m) => m.default)) as Loader,
  final: (() => import('./ClosingScene').then((m) => m.default)) as Loader,
} as const;

/** The lazy sections of the page (the ids of their slots, src/landing/slots.ts). */
export type SectionName = keyof typeof SECTION_LOADERS;
