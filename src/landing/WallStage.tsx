// The stage of the wall chapter: one big AI visualisation of the visitor's file in a room, in the material and artwork the
// visitor picked. Two stacked pictures cross-fade (the CSS does the fade, .lp-stage img / .lp-on in css/wall.css): the new
// picture is put into the layer that is not in front, loaded and decoded there, and only then does the front change, so the
// stage never shows a half-loaded picture or an empty frame. The pictures are fetched when the stage comes near the screen,
// not when the page loads (the section sits far below the first screen).
//
// The glint (motion spec 6.7, charter AC-6): on the polished face of an acrylic plate, and only there, a soft band of light, 30 percent
// of the print's width and at most 10 percent white, moves across it as the visitor scrolls past (from 768 px, motion allowed): it is
// placed by the progress of the wall chapter through the screen, so it moves the way a reflection does when you walk by, and never
// follows the pointer. It is clipped to the print face (the span's box), decorative (aria-hidden) and exists only while the acrylic
// picture is the one on screen. On a phone the same band follows the scroll of the plate across the screen (the effect below, the owner's request of 2026-10-17); it
// replaces the single sweep that a phone used to get when the visitor picked acrylic (a phone with reduced motion or without the engine has no band at all).
import { useEffect, useLayoutEffect, useRef, useState, type RefObject } from 'react';
import { traverse, whenPinned } from '../motion/motion';
import { put, whenPhone } from '../motion/phone';
import { ExampleChip, type PictureAsset } from './ui';
import { STAGE_SIZES, type GlintBox, type StagePicture } from './wallScenes';

interface Slot { key: string; asset: PictureAsset }
type Slots = readonly [Slot | null, Slot | null];
interface Layers { front: 0 | 1; slots: Slots }

/** True from the moment the element has been within `margin` of the viewport (and stays true): the stage asks for its pictures
 *  900 px ahead of the screen. Without IntersectionObserver the answer is yes at once. */
function useNearViewport(ref: RefObject<Element | null>, margin: string): boolean {
  const [near, setNear] = useState(() => typeof IntersectionObserver === 'undefined');
  useEffect(() => {
    const el = ref.current;
    if (near || !el) return;
    const io = new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting)) {
        setNear(true);
        io.disconnect();
      }
    }, { rootMargin: margin });
    io.observe(el);
    return () => io.disconnect();
  }, [ref, margin, near]);
  return near;
}

export interface WallStageProps {
  /** The picture that should be on the stage now (null: the material has none for this artwork). */
  picture: StagePicture | null;
  /** The words of the picture for a screen reader ("Visualisation. On aluminium, about 50 cm. One eye."). */
  alt: string;
  /** The sweep of light on a polished surface (acrylic), or null: the box of the print's face, in percent of the stage. The span is
   *  always in the markup and gets the box only while the picture it belongs to is the one in front. */
  glint: GlintBox | null;
  /** The group's name (wall.stageLabel). */
  label: string;
  /** The line under the stage, in a live region. */
  caption: string;
  /** The second line under it, for the artworks with other people's eyes (wall.eyesNote), or undefined. */
  eyesNote?: string;
}

export function WallStage({ picture, alt, glint, label, caption, eyesNote }: WallStageProps) {
  const frame = useRef<HTMLDivElement>(null);
  const near = useNearViewport(frame, '900px 0px');
  const want = near ? picture : null;

  const [layers, setLayers] = useState<Layers>({ front: 0, slots: [null, null] });
  const { front, slots } = layers;
  const back = front === 0 ? 1 : 0;
  const imgs = useRef<(HTMLImageElement | null)[]>([null, null]);
  // the load handlers run later than the render that made them: they read what is current now
  const latest = useRef({ want, layers });
  useLayoutEffect(() => {
    latest.current = { want, layers };
  });

  // the wanted picture goes into the layer that is not in front (unless a layer holds it already). Adjusting state while
  // rendering is the documented way to derive it from props; the guard ends after one round.
  if (want && slots[front]?.key !== want.key && slots[back]?.key !== want.key) {
    const next: [Slot | null, Slot | null] = [slots[0], slots[1]];
    next[back] = { key: want.key, asset: want.asset };
    setLayers({ front, slots: next });
  }

  // bring a loaded and decoded layer to the front, if it still is the picture that is wanted
  const flip = (i: 0 | 1) => {
    const now = latest.current;
    if (!now.want || i === now.layers.front || now.layers.slots[i]?.key !== now.want.key) return;
    const go = () =>
      setLayers((s) => (i !== s.front && s.slots[i]?.key === latest.current.want?.key ? { front: i, slots: s.slots } : s));
    const img = imgs.current[i];
    if (img?.decode) img.decode().catch(() => undefined).then(go);
    else go();
  };

  // a layer that already holds the wanted picture (the visitor went back to one seen before) has nothing left to load
  const wantKey = want?.key;
  useEffect(() => {
    const img = imgs.current[back];
    if (wantKey && slots[back]?.key === wantKey && img && img.complete && img.naturalWidth > 0) flip(back);
    // flip reads the current values through the ref, so it is not a dependency
  }, [wantKey, slots, back]);

  // the glint belongs to the acrylic picture: it is there only once that picture is in front (never over the picture it is replacing)
  const polished = glint && !!want && slots[front]?.key === want.key ? glint : null;
  const shine = polished !== null;
  const glintEl = useRef<HTMLSpanElement>(null);

  // from 768 px, with motion: the band follows the scroll progress of the wall chapter (listeners only while the chapter is near the screen)
  useEffect(() => {
    const el = glintEl.current;
    const chapter = frame.current?.closest<HTMLElement>('.lp-wall-grid');
    if (!el || !chapter || !shine) return;
    return whenPinned(() => traverse(chapter, (p) => el.style.setProperty('--gx', `${(p * 80 - 40).toFixed(2)}%`), { start: 0.9, end: 0.1 }));
  }, [shine]);

  // on a phone with the engine running (the owner's request of 2026-10-17): the plate opens like a mat and settles from a scale of 1.03 to exactly 1 while it arrives
  // (over the first 45 percent of its crossing of the screen), and the light on a polished face passes over the print with the scroll, as it does from 768 px (the
  // stylesheet shows both only once data-scrub is on the frame: css/wall.css). Both values are written on the frame (--ps, --gx); the glint inherits --gx.
  useEffect(() => {
    const el = frame.current;
    return el ? whenPhone(() => traverse(el, (p) => { const ps = Math.min(1, p / 0.45); put(el, { '--ps': ps.toFixed(3), '--gx': `${(p * 80 - 40).toFixed(3)}%` }, ps); }, { start: 1, end: 0 })) : undefined;
  }, []);

  return (
    <figure>
      <div ref={frame} className="lp-stage" id="stage" role="group" aria-label={label} data-chip-area="vis">
        {([0, 1] as const).map((i) => {
          const slot = slots[i];
          const shown = i === front && !!slot;
          return (
            <img
              key={i}
              ref={(el) => {
                imgs.current[i] = el;
              }}
              id={i === 0 ? 'stA' : 'stB'}
              className={`${i === 0 ? 'lp-a' : 'lp-b'}${shown ? ' lp-on' : ''}`}
              src={slot?.asset.src}
              srcSet={slot?.asset.srcset}
              sizes={slot?.asset.srcset ? STAGE_SIZES : undefined}
              width={slot?.asset.w ?? 1200}
              height={slot?.asset.h ?? 1500}
              alt={shown ? alt : ''}
              aria-hidden={shown ? undefined : true}
              decoding="async"
              onLoad={() => flip(i)}
            />
          );
        })}
        <span
          ref={glintEl}
          className="lp-glint"
          id="stGlint"
          aria-hidden="true"
          data-shine={shine || undefined}
          style={polished ? { left: `${polished[0]}%`, top: `${polished[1]}%`, width: `${polished[2]}%`, height: `${polished[3]}%` } : undefined}
        />
        <ExampleChip variant="vis" />
      </div>
      <figcaption className="lp-stage-cap">
        <span id="stageCap" aria-live="polite">{caption}</span>
        <span className="lp-eyes-note" id="stageEyes" hidden={!eyesNote}>{eyesNote}</span>
      </figcaption>
    </figure>
  );
}
