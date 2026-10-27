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
  reveal: { id: 'reveal', h: { en: [1012, 3141, 3234], de: [1043, 3141, 3234], lt: [1063, 3141, 3234], hu: [1043, 3141, 3234] } },
  wall: { id: 'wall', h: { en: [1981, 2382, 2480], de: [2039, 2382, 2431], lt: [2012, 2422, 2480], hu: [1981, 2382, 2480] } },
  styles: { id: 'styles', h: { en: [722, 2912, 2214], de: [722, 2912, 2214], lt: [753, 2912, 2214], hu: [753, 2912, 2214] } },
  how: { id: 'how', h: { en: [692, 980, 862], de: [723, 980, 935], lt: [723, 980, 912], hu: [723, 980, 862] } },
  pricing: { id: 'pricing', h: { en: [1159, 1096, 884], de: [1200, 1157, 884], lt: [1212, 1157, 905], hu: [1180, 1157, 905] } },
  closeups: { id: 'closeups', h: { en: [621, 1625, 983], de: [621, 1625, 983], lt: [589, 1625, 934], hu: [621, 1625, 983] } },
  trust: { id: 'trust', h: { en: [1235, 968, 832], de: [1367, 968, 940], lt: [1294, 968, 902], hu: [1363, 1010, 891] } },
  faq: { id: 'faq', h: { en: [1247, 1242, 1193], de: [1290, 1242, 1193], lt: [1276, 1242, 1193], hu: [1290, 1242, 1193] } },
  final: { id: 'final', h: { en: [660, 660, 600], de: [660, 684, 600], lt: [660, 660, 600], hu: [660, 684, 600] } },
  sizes: { id: 'sizes', h: { en: [605, 829, 629], de: [631, 829, 580], lt: [605, 870, 629], hu: [605, 829, 629] } },
  more: { id: 'more', h: { en: [70, 70, 509], de: [70, 70, 509], lt: [70, 70, 509], hu: [70, 70, 509] } },
} as const;

export type SlotName = keyof typeof SLOT_HEIGHTS;

/** The style that gives the empty slot (class lp-slot, src/landing/css/base.css) its three heights, in the page's language. */
export function slotStyle(name: SlotName, lang: Lang): CSSProperties {
  const [phone, tablet, desktop] = SLOT_HEIGHTS[name].h[lang];
  return { '--slot-p': `${phone}px`, '--slot-t': `${tablet}px`, '--slot-d': `${desktop}px` } as CSSProperties;
}
