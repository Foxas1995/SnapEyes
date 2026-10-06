import { useId, type CSSProperties } from 'react';

// The capture guide as a drawing (motion spec 7.2): a phone on the left, an iris on the right, the distance between them, and the light from one side.
// The four strokes draw in one after the other (CSS, ./flow.css: pathLength 1, stroke-dashoffset), then the ring around the eye settles once and rests.
// Decorative: the guide's own four steps stand beside it as text in the page's language, so a screen reader loses nothing. The drawing holds no words of
// its own except "10 cm", which reads the same in all four languages; the number and its unit never separate (U+00A0).

export const CaptureDiagram = () => {
  const mask = useId();
  return (
    <svg aria-hidden="true" focusable="false" viewBox="0 0 240 140" className="fx-diagram" data-testid="capture-diagram">
      <defs>
        {/* the dashed distance line is revealed by a solid line that draws in over it (a dashed stroke cannot be drawn in by its own offset) */}
        <mask id={mask} maskUnits="userSpaceOnUse" x="0" y="0" width="240" height="140">
          <path d="M74 66H142" stroke="#fff" strokeWidth="6" fill="none" pathLength="1" className="dr" style={{ '--i': 2 } as CSSProperties} />
        </mask>
      </defs>
      {/* the phone, its back camera at the top left */}
      <path className="st dr" style={{ '--i': 0 } as CSSProperties} pathLength="1" d="M31 22h26a9 9 0 0 1 9 9v70a9 9 0 0 1-9 9H31a9 9 0 0 1-9-9V31a9 9 0 0 1 9-9z" />
      <circle className="st dr" style={{ '--i': 0 } as CSSProperties} pathLength="1" cx="33" cy="33" r="3.4" />
      {/* the eye: the iris ring and the pupil, and the ring that focus settles on */}
      <circle className="st au dr" style={{ '--i': 1 } as CSSProperties} pathLength="1" cx="186" cy="68" r="32" />
      <circle className="st dr" style={{ '--i': 1 } as CSSProperties} pathLength="1" cx="186" cy="68" r="10" />
      <circle className="st au rest" cx="186" cy="68" r="40" strokeOpacity=".55" />
      {/* the distance: a dashed line with its two ends marked, and its figure above it */}
      <path className="st" d="M74 66H142" strokeDasharray="3 4" mask={`url(#${mask})`} />
      <path className="st dr" style={{ '--i': 2 } as CSSProperties} pathLength="1" d="M74 59v14M142 59v14" />
      <text className="nm" x="108" y="52">10{'\u00a0'}cm</text>
      {/* the light: an arrow from the side (a window), not from in front */}
      <path className="st dr" style={{ '--i': 3 } as CSSProperties} pathLength="1" d="M232 14 210 36M210 26v10h10M232 30l-14 14" />
    </svg>
  );
};
