import type { CSSProperties } from 'react';

// The height of each lazy section of the page, so that the empty slot that holds its place while its chunk is on the way is about as
// tall as the section will be (src/App.tsx Slot). Measured on the integrated page, the mean of English, German, Lithuanian and
// Hungarian: phone is the layout below 640 px (measured at 375 px), tablet from 640 px (measured at 768 px, the sections are tallest
// there), desktop from 960 px (measured at 1280 px). A slot is below the first screen and is replaced within a moment, so the numbers
// only have to be near; they are not a promise. The ids are the sections' own: a link to #pricing has its target while the chunk loads.
export const SLOT_HEIGHTS = {
  reveal: { id: 'reveal', phone: 1910, tablet: 1930, desktop: 1566 },
  // the wall chapter holds the size guide and "More ways to see it": its slot is their sum, theirs are below
  wall: { id: 'wall', phone: 2813, tablet: 2891, desktop: 2796 },
  styles: { id: 'styles', phone: 980, tablet: 1958, desktop: 1576 },
  how: { id: 'how', phone: 925, tablet: 1157, desktop: 1079 },
  pricing: { id: 'pricing', phone: 1646, tablet: 1353, desktop: 990 },
  closeups: { id: 'closeups', phone: 822, tablet: 1833, desktop: 1022 },
  trust: { id: 'trust', phone: 2007, tablet: 1462, desktop: 1308 },
  faq: { id: 'faq', phone: 1277, tablet: 1237, desktop: 1179 },
  final: { id: 'final', phone: 682, tablet: 700, desktop: 600 },
  // the two blocks at the foot of the wall chapter, chunks of their own (src/landing/Wall.tsx)
  sizes: { id: 'sizes', phone: 934, tablet: 1032, desktop: 678 },
  more: { id: 'more', phone: 115, tablet: 94, desktop: 503 },
} as const;

export type SlotName = keyof typeof SLOT_HEIGHTS;

/** The style that gives the empty slot (class lp-slot, src/landing/css/base.css) its three heights. */
export function slotStyle(name: SlotName): CSSProperties {
  const h = SLOT_HEIGHTS[name];
  return { '--slot-p': `${h.phone}px`, '--slot-t': `${h.tablet}px`, '--slot-d': `${h.desktop}px` } as CSSProperties;
}
