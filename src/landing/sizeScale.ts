// The size guide's numbers, without React. A drawing TO SCALE: a 220 cm sofa, a 175 cm person and the four print sizes on the
// wall, all in one unit (K units per centimetre), so the squares, the sofa and the person keep their real proportions. And
// the one honest number of the chapter: the pixels per inch of the 4096 px file at each size (ppi = 4096 / (cm / 2.54)),
// which the page puts next to what print shops usually ask for. The words are the copy's; this file holds geometry only.

/** The longest side of the delivered file, in pixels (the copy's {px} fact says the same in words). */
export const FILE_PX = 4096;

/** The four sizes of the drawing and of the chips, in centimetres. The largest is the one the page suggests. */
export const SIZES = [20, 30, 40, 50] as const;
export type SizeCm = (typeof SIZES)[number];
export const DEFAULT_SIZE: SizeCm = 50;

/** Pixels per inch of the file printed cm wide: 4096 / (cm / 2.54), rounded (520, 347, 260, 208). */
export function ppi(cm: number): number {
  return Math.round(FILE_PX / (cm / 2.54));
}

/** Drawing units per centimetre. */
export const K = 2.8;
/** Where each square sits: its centre on the x axis, and the one height they share. */
export const SQX: Readonly<Record<SizeCm, number>> = { 20: 201, 30: 305, 40: 437, 50: 597 };
export const CY = 154;
/** The floor line (y). */
export const FLOOR = 556;
/** The whole drawing is 1000 by 600 units. */
export const SCENE = { w: 1000, h: 600 } as const;

/** The sofa: 220 cm wide and 85 cm high, its left edge at x. */
export const SOFA = { x: 112, w: 220 * K, h: 85 * K } as const;
/** The person: 175 cm, centred on x. */
export const PERSON = { x: 868, h: 175 * K } as const;

/** What the viewer sees of the drawing: all of it, or on a phone a crop that leaves out the empty margins, so the pieces stay
 *  large enough to read. [x, y, width, height] of the view box. */
export type ViewBox = readonly [number, number, number, number];
export function viewBoxFor(narrow: boolean): ViewBox {
  return narrow ? [60, 40, 940, 560] : [0, 0, SCENE.w, SCENE.h];
}

export interface Square { cm: SizeCm; side: number; x: number; y: number }
/** The four squares: side in units, and the top left corner. */
export function squares(): Square[] {
  return SIZES.map((cm) => {
    const side = cm * K;
    return { cm, side, x: SQX[cm] - side / 2, y: CY - side / 2 };
  });
}

/** A point of the drawing as a position in percent of the view box, for the text labels laid over the picture (HTML text, so it
 *  stays crisp, wraps never and can be styled): "left:12.30%;top:45.00%". */
export function pct(vb: ViewBox, x: number, y: number): { left: string; top: string } {
  const [vx, vy, vw, vh] = vb;
  return { left: `${(((x - vx) / vw) * 100).toFixed(2)}%`, top: `${(((y - vy) / vh) * 100).toFixed(2)}%` };
}

export interface LabelSpots {
  squares: Readonly<Record<SizeCm, { left: string; top: string }>>;
  sofa: { left: string; top: string };
  person: { left: string; top: string };
}

/** Where every label sits: the size labels under their squares, the sofa label under the sofa, the person label under the
 *  person (shifted left on a phone, where the crop would cut it). */
export function labelSpots(narrow: boolean): LabelSpots {
  const vb = viewBoxFor(narrow);
  const sq = {} as Record<SizeCm, { left: string; top: string }>;
  for (const s of squares()) sq[s.cm] = pct(vb, SQX[s.cm], CY + s.side / 2 + 10);
  return {
    squares: sq,
    sofa: pct(vb, SOFA.x + SOFA.w / 2, FLOOR + 6),
    person: pct(vb, narrow ? PERSON.x - 46 : PERSON.x, FLOOR + 6),
  };
}

export interface Rect { x: number; y: number; width: number; height: number; rx?: number }

/** The sofa as six rounded rectangles: back, two arms, seat cushion, two legs. */
export function sofaRects(): Rect[] {
  const { x: sx, w: sw, h: sh } = SOFA;
  return [
    { x: sx + 30, y: FLOOR - sh, width: sw - 60, height: sh * 0.6, rx: 22 },
    { x: sx, y: FLOOR - sh * 0.78, width: 50, height: sh * 0.56, rx: 16 },
    { x: sx + sw - 50, y: FLOOR - sh * 0.78, width: 50, height: sh * 0.56, rx: 16 },
    { x: sx + 34, y: FLOOR - sh * 0.62, width: sw - 68, height: sh * 0.4, rx: 14 },
    { x: sx + 30, y: FLOOR - sh * 0.22, width: 10, height: sh * 0.22 },
    { x: sx + sw - 40, y: FLOOR - sh * 0.22, width: 10, height: sh * 0.22 },
  ];
}

/** The person: one filled silhouette (a path for the body, a circle for the head), 175 cm tall, feet on the floor. */
export function person(): { body: string; head: { cx: number; cy: number; r: number } } {
  const { x, h } = PERSON;
  const top = FLOOR - h;
  const f = FLOOR;
  const body =
    `M${x - 62} ${top + 92} Q${x} ${top + 66} ${x + 62} ${top + 92} L${x + 70} ${top + 232} Q${x + 72} ${top + 246} ${x + 58} ${top + 246} ` +
    `L${x + 50} ${top + 246} L${x + 34} ${top + 244} L${x + 34} ${f} L${x + 4} ${f} L${x + 3} ${top + 252} L${x - 3} ${top + 252} L${x - 4} ${f} ` +
    `L${x - 34} ${f} L${x - 34} ${top + 244} L${x - 50} ${top + 246} L${x - 58} ${top + 246} Q${x - 72} ${top + 246} ${x - 70} ${top + 232} Z`;
  return { body, head: { cx: x, cy: top + 31, r: 30 } };
}
