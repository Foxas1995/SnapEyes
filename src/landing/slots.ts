import type { CSSProperties } from 'react';
import type { Lang } from '../shared/lang';

// The height of each lazy section of the page, so that the empty slot that holds its place until the section is mounted is as tall as the
// section will be (src/App.tsx Slot). Written by `node scripts/measure_slots.mjs --write` from the built page in real Chrome: [phone, tablet,
// desktop] per language, where phone is the layout below 640 px (measured at 375 px), tablet from 640 px (768 px) and desktop from 960 px
// (1280 px), ordering closed, EU market, details closed. The words differ in length between the languages, so each language has its own
// numbers: with one mean for all four a slot was up to 190 px off and the page jumped by that much when a section arrived above the
// reader (a browser without scroll anchoring, Safari, shows it). The numbers only have to be near: a slot is replaced within a moment, and
// a section's real height also depends on the market and on whether ordering is open (`--check` fails above 12 percent). The
// ids are the sections' own: a link to #pricing has its target while the section is on its way.
export const SLOT_HEIGHTS = {
  reveal: { id: 'reveal', h: { en: [1787, 3677, 3483], de: [1946, 3677, 3483], lt: [1887, 3700, 3483], hu: [1897, 3679, 3483] } },
  wall: { id: 'wall', h: { en: [2715, 2834, 2733], de: [2876, 2876, 2779], lt: [2809, 2954, 2853], hu: [2852, 2898, 2779] } },
  styles: { id: 'styles', h: { en: [947, 1925, 1543], de: [988, 1966, 1584], lt: [1015, 1994, 1612], hu: [968, 1945, 1563] } },
  how: { id: 'how', h: { en: [884, 1132, 1054], de: [939, 1181, 1103], lt: [939, 1181, 1103], hu: [939, 1132, 1054] } },
  pricing: { id: 'pricing', h: { en: [1552, 1324, 968], de: [1702, 1371, 990], lt: [1691, 1371, 990], hu: [1640, 1347, 1013] } },
  closeups: { id: 'closeups', h: { en: [829, 1801, 990], de: [856, 1851, 1039], lt: [824, 1801, 990], hu: [856, 1879, 1067] } },
  trust: { id: 'trust', h: { en: [1912, 1430, 1206], de: [2117, 1501, 1403], lt: [1996, 1501, 1343], hu: [2109, 1494, 1311] } },
  faq: { id: 'faq', h: { en: [1247, 1242, 1193], de: [1290, 1242, 1193], lt: [1276, 1242, 1193], hu: [1290, 1242, 1193] } },
  final: { id: 'final', h: { en: [660, 660, 600], de: [689, 722, 600], lt: [689, 694, 600], hu: [689, 722, 600] } },
  sizes: { id: 'sizes', h: { en: [876, 998, 648], de: [971, 1020, 672], lt: [944, 1069, 718], hu: [944, 1042, 672] } },
  more: { id: 'more', h: { en: [115, 94, 494], de: [115, 94, 494], lt: [115, 94, 494], hu: [115, 94, 494] } },
} as const;

export type SlotName = keyof typeof SLOT_HEIGHTS;

/** The style that gives the empty slot (class lp-slot, src/landing/css/base.css) its three heights, in the page's language. */
export function slotStyle(name: SlotName, lang: Lang): CSSProperties {
  const [phone, tablet, desktop] = SLOT_HEIGHTS[name].h[lang];
  return { '--slot-p': `${phone}px`, '--slot-t': `${tablet}px`, '--slot-d': `${desktop}px` } as CSSProperties;
}
