// The page's line icons (the lean pass of 2026-10-22, the owner: "fewer words, more pictures"): a short list of facts is a row of icons with two to four
// words each. Drawn here as plain paths on a 24 px grid (no icon library: the page already carries lucide-react for three glyphs, and these few paths
// are smaller than the components would be). A stroke of 1.6 px in currentColor with round ends; the colour is the stylesheet's (css/base.css .lp-ic:
// the palette's gold). Decoration only: every icon stands beside the words that say the same, so a screen reader skips it (aria-hidden).
import type { CSSProperties } from 'react';

// a diagonal stroke across an icon: "not", "without"
const SLASH = 'M4 4l16 16';
const EYE = 'M2.5 12s3.6-6.5 9.5-6.5 9.5 6.5 9.5 6.5-3.6 6.5-9.5 6.5S2.5 12 2.5 12zM12 9.2a2.8 2.8 0 1 0 0 5.6 2.8 2.8 0 0 0 0-5.6z';
const SUN = 'M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7zM12 3v2.2M12 18.8V21M3 12h2.2M18.8 12H21M5.6 5.6l1.6 1.6M16.8 16.8l1.6 1.6M5.6 18.4l1.6-1.6M16.8 7.2l1.6-1.6';
const FRAME = 'M4 4h16v16H4zM8 8h8v8H8z';

/** Each icon: the stroked path, and an optional filled one (the dark half of the contrast disc). */
const ICONS = {
  eye: [EYE],
  clock: ['M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 7.5V12l3 2'],
  noUser: ['M12 4.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7zM5.5 20c1.1-3.4 3.6-5.2 6.5-5.2s5.4 1.8 6.5 5.2' + SLASH],
  camera: ['M4 8.5h3.2L9 6h6l1.8 2.5H20a1 1 0 0 1 1 1V18a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9.5a1 1 0 0 1 1-1zM12 10.4a3.3 3.3 0 1 0 0 6.6 3.3 3.3 0 0 0 0-6.6z'],
  file: ['M14 3H7a1.5 1.5 0 0 0-1.5 1.5v15A1.5 1.5 0 0 0 7 21h10a1.5 1.5 0 0 0 1.5-1.5V7.5zM14 3v4.5h4.5M12 10.5v6.5M9.3 14.3 12 17l2.7-2.7'],
  layers: ['M12 4 3 8.5l9 4.5 9-4.5zM3 12.5l9 4.5 9-4.5M3 16.5l9 4.5 9-4.5'],
  float: ['M4 3v18M10 6h10v12H10zM4 9h6M4 15h6'],
  wall: ['M4 3v18M6.5 6h12v12h-12z'],
  contrast: ['M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z', 'M12 3a9 9 0 0 0 0 18z'],
  shine: [SUN],
  noGlare: [SUN + SLASH],
  noFrame: [FRAME + SLASH],
  frame: [FRAME],
  ruler: ['M3 16.5 16.5 3 21 7.5 7.5 21zM7.2 12.3l2 2M10.2 9.3l2 2M13.2 6.3l2 2'],
  hang: ['M12 3v3M12 6 6 11h12zM6 11h12v10H6z'],
  cube: ['M12 3l8 4.5v9L12 21l-8-4.5v-9zM4 7.5l8 4.5 8-4.5M12 12v9'],
  stand: ['M7 4h10v13H7zM3.5 20.5h17'],
  phone: ['M8 2.5h8A1.5 1.5 0 0 1 17.5 4v16a1.5 1.5 0 0 1-1.5 1.5H8A1.5 1.5 0 0 1 6.5 20V4A1.5 1.5 0 0 1 8 2.5zM10.5 18.5h3'],
  expand: ['M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5M9 9h6v6H9z'],
  check: ['M4.5 12.5l4.5 4.5 10.5-10.5'],
  image: ['M4 5h16v14H4zM4 15.5l4.5-4.5 4 4 2.5-2.5 5 5M15.5 7.8a1.2 1.2 0 1 0 0 2.4 1.2 1.2 0 0 0 0-2.4z'],
  download: ['M12 4v11M7.5 10.5 12 15l4.5-4.5M4 19.5h16'],
  badge: ['M12 3a6 6 0 1 0 0 12 6 6 0 0 0 0-12zM8.6 14 7 21l5-2.5 5 2.5-1.6-7'],
  noPrint: ['M7 9V3.5h10V9M7 17H5a1.5 1.5 0 0 1-1.5-1.5v-5A1.5 1.5 0 0 1 5 9h14a1.5 1.5 0 0 1 1.5 1.5v5A1.5 1.5 0 0 1 19 17h-2M7 14h10v6.5H7z' + 'M3 3l18 18'],
  pen: ['M4 20l1.2-4.8L16 4.4 19.6 8 8.8 18.8zM13.8 6.6l3.6 3.6'],
  tag: ['M3.5 12.6V4.5a1 1 0 0 1 1-1h8.1l8 8-9.1 9.1zM8.2 6.9a1.3 1.3 0 1 0 0 2.6 1.3 1.3 0 0 0 0-2.6z'],
  noEye: [EYE + SLASH],
  hourglass: ['M6 3h12M6 21h12M7 3c0 5 10 5 10 9s-10 4-10 9M17 3c0 5-10 5-10 9s10 4 10 9'],
} as const;

export type IconName = keyof typeof ICONS;

export function Icon({ name, className = 'lp-ic', style }: { name: IconName; className?: string; style?: CSSProperties }) {
  const [line, fill] = ICONS[name] as readonly [string, string?];
  return (
    <svg className={className} style={style} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      <path d={line} />
      {fill && <path d={fill} fill="currentColor" stroke="none" />}
    </svg>
  );
}
