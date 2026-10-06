// The Reveal scene's script (motion spec 6.4), as numbers: scroll progress p (0 at the start of the pin, 1 at its end) in, what the frame shows
// out. Pure functions, no DOM, so the table below is the one place that says what happens when, and the scene (RevealScene.tsx) only applies it.
//
//   p 0 to .06     the phone photo alone (the honest "before"); no line
//   p .06 to .50   the cut travels right to left through the pupil (--pos 100 to 0, linear in p); a 1 px gold line with a soft glow rides on it
//   p .50 to .56   the restored iris on black; the line fades out
//   p .56 to .94   the aperture: a circle centred on the pupil opens (--r 0 to 72 percent of the frame, which covers the corners) and shows
//                  the artwork; a 1 px gold ring at .6 alpha follows its edge (no glow)
//   p .94 to 1     the artwork whole
//   steps          01 your photo, 02 your iris from p .34, 03 your art from p .72
//   chips          "phone photo" while the cut is right of 18 percent, "restored iris" while it is left of 82 percent (the slider's own rule),
//                  "your art" once the aperture covers about a third of the frame (radius 34 percent, p .74): a label that says art over a frame
//                  that is still the restored iris is not exact

const clamp01 = (x: number) => (x < 0 ? 0 : x > 1 ? 1 : x);
const ramp = (p: number, from: number, to: number) => clamp01((p - from) / (to - from));

export const CUT_START = 0.06;
export const CUT_END = 0.5;
export const APERTURE_START = 0.56;
export const APERTURE_END = 0.94;
/** The aperture's radius at the end, in percent of the frame: 72 covers the corners (the half diagonal is 70.7). */
export const APERTURE_R = 72;
export const STEP_AT = [0, 0.34, 0.72] as const;
/** The aperture radius, in percent of the frame, from which the chip says "your art" (about 36 percent of the frame's area is the artwork). */
export const ART_CHIP_R = 34;
/** Where a click on a step row takes the scroll: inside the step's stretch, away from the thresholds. */
export const STEP_GOTO = [0, 0.53, 0.97] as const;

export type Chip = 'photo' | 'iris' | 'art';

export interface SceneState {
  /** The cut, in percent of the frame from the left: the photo shows to the left of it. */
  pos: number;
  /** The aperture's radius, in percent of the frame. */
  r: number;
  /** Opacity of the cut line and of the aperture's ring, 0 to 1. */
  line: number;
  ring: number;
  /** The active step, 0 to 2. */
  step: 0 | 1 | 2;
  /** The chips that are showing. */
  chips: readonly Chip[];
}

export function sceneState(p: number): SceneState {
  const pos = 100 * (1 - ramp(p, CUT_START, CUT_END));
  const r = APERTURE_R * ramp(p, APERTURE_START, APERTURE_END);
  const art = r >= ART_CHIP_R;
  const chips: Chip[] = [];
  if (!art && pos > 18) chips.push('photo');
  if (!art && pos < 82) chips.push('iris');
  if (art) chips.push('art');
  return {
    pos,
    r,
    line: ramp(p, CUT_START, CUT_START + 0.03) * (1 - ramp(p, CUT_END, APERTURE_START)),
    // the ring is visible while the circle is inside the frame or crossing its corners; it is gone by the time the circle has left the frame
    ring: ramp(p, APERTURE_START, APERTURE_START + 0.03) * (1 - ramp(p, 0.86, APERTURE_END)),
    step: p >= STEP_AT[2] ? 2 : p >= STEP_AT[1] ? 1 : 0,
    chips,
  };
}
