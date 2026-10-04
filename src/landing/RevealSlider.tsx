// The Reveal's frame: a phone photo on the left and the same iris restored on the right, cut through the pupil. Two registered
// layers (same crop, same size) sit on top of each other; the photo is clipped at the cut. The cut is ONE number (--pos, in
// percent of the frame), and a native <input type="range"> carries it for the keyboard and for screen readers, so Home, End,
// PageUp, PageDown and the arrows work as on any slider. The cut and the grip move with transform (see css/reveal.css).
//
// Hands: a mouse moves the cut at once; a finger only after about 8 px of mostly sideways travel, so a vertical swipe that
// starts on the picture scrolls the page instead (touch-action: pan-y); a tap puts the cut where it landed. On arrival the
// cut sweeps once from the photo side to the pupil, unless the visitor has already touched it or prefers reduced motion.
import { useCallback, useEffect, useLayoutEffect, useRef, useState, type CSSProperties, type PointerEvent } from 'react';
import { useCopy } from './copy/useCopy';
import { REVEAL_SIZES, type RevealEye } from './revealEyes';

const SIDEWAYS_PX = 8; // a finger has to travel this far, mostly sideways, before it moves the cut
const SIDEWAYS_RATIO = 1.4; // "mostly": sideways travel over upward or downward travel
const LABEL_LEFT_HIDDEN = 18; // "Phone photo" fades out when the cut is nearer the left edge than this many percent
const LABEL_RIGHT_HIDDEN = 82; // "Restored iris" fades out when the cut is nearer the right edge than this
const SWEEP_MS = 950;
const SWEEP_DELAY_MS = 420;

const clamp = (p: number) => Math.max(0, Math.min(100, p));
const easeOut = (t: number) => 1 - Math.pow(1 - t, 3);

interface Touch {
  x: number;
  y: number;
  id: number;
}

export interface RevealSliderProps {
  eye: RevealEye;
}

export function RevealSlider({ eye }: RevealSliderProps) {
  const { c, t } = useCopy();
  const frame = useRef<HTMLDivElement>(null);
  const photo = useRef<HTMLImageElement>(null);
  const [pos, setPos] = useState(50);
  const [show, setShow] = useState(false); // the line and the grip stay visible for a moment after the visitor lets go
  // what the pointer and the arrival sweep share without a render: whether the visitor (or the sweep) has had its turn, a
  // counter that any input bumps to call the sweep off, the drag in progress and the timer of the handle
  const hand = useRef({ swept: false, gen: 0, dragging: false, down: null as Touch | null, timer: 0 });
  const posNow = useRef(pos);
  useLayoutEffect(() => {
    posNow.current = pos;
  });

  // another eye: the cut goes back to the middle (the language changing keeps it where it is)
  const [eyeSeen, setEyeSeen] = useState(eye.id);
  if (eyeSeen !== eye.id) {
    setEyeSeen(eye.id);
    setPos(50);
  }

  const move = useCallback((p: number, quiet = false) => {
    setPos(clamp(p));
    if (!quiet) setShow(true);
  }, []);
  const flash = useCallback((ms: number) => {
    const h = hand.current;
    setShow(true);
    window.clearTimeout(h.timer);
    h.timer = window.setTimeout(() => setShow(false), ms);
  }, []);
  useEffect(() => () => window.clearTimeout(hand.current.timer), []);

  const fromX = (x: number) => {
    const r = frame.current?.getBoundingClientRect();
    if (r && r.width > 0) move(((x - r.left) / r.width) * 100);
  };

  const onPointerDown = (e: PointerEvent<HTMLDivElement>) => {
    const h = hand.current;
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    h.gen++;
    if (e.pointerType === 'mouse') {
      h.dragging = true;
      e.currentTarget.setPointerCapture(e.pointerId);
      fromX(e.clientX);
      h.swept = true;
    } else {
      h.down = { x: e.clientX, y: e.clientY, id: e.pointerId };
    }
  };
  const onPointerMove = (e: PointerEvent<HTMLDivElement>) => {
    const h = hand.current;
    if (h.dragging) {
      fromX(e.clientX);
      return;
    }
    if (h.down && e.pointerId === h.down.id) {
      const dx = e.clientX - h.down.x;
      const dy = e.clientY - h.down.y;
      if (Math.abs(dx) > SIDEWAYS_PX && Math.abs(dx) > Math.abs(dy) * SIDEWAYS_RATIO) {
        h.dragging = true;
        h.swept = true;
        e.currentTarget.setPointerCapture(e.pointerId);
        fromX(e.clientX);
      }
    }
  };
  const onPointerEnd = (e: PointerEvent<HTMLDivElement>) => {
    const h = hand.current;
    if (h.dragging) {
      h.dragging = false;
      flash(1800);
    } else if (h.down && e.type === 'pointerup' && Math.abs(e.clientX - h.down.x) < SIDEWAYS_PX && Math.abs(e.clientY - h.down.y) < SIDEWAYS_PX) {
      fromX(e.clientX);
      h.swept = true;
      flash(1800);
    }
    h.down = null;
  };

  // the arrival: the cut waits at the photo side until the frame is near, then sweeps to the pupil, once
  useEffect(() => {
    const el = frame.current;
    if (!el || !('IntersectionObserver' in window) || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const h = hand.current;
    let delay = 0;
    let raf = 0;
    const near = new IntersectionObserver(
      (es) => {
        if (es[0].isIntersecting && !h.swept) {
          move(100, true);
          near.disconnect();
        }
      },
      { rootMargin: '700px 0px' },
    );
    const inView = new IntersectionObserver(
      (es) => {
        if (!es[0].isIntersecting || h.swept) return;
        inView.disconnect();
        h.swept = true;
        const go = () => {
          delay = window.setTimeout(() => {
            const t0 = performance.now();
            const from = posNow.current;
            const g0 = h.gen;
            setShow(true);
            const tick = (now: number) => {
              if (g0 !== h.gen) return; // the visitor took over
              const k = Math.min(1, (now - t0) / SWEEP_MS);
              move(from + (50 - from) * easeOut(k), true);
              if (k < 1) raf = requestAnimationFrame(tick);
              else flash(2200);
            };
            raf = requestAnimationFrame(tick);
          }, SWEEP_DELAY_MS);
        };
        const img = photo.current;
        if (!img || img.complete) go();
        else img.addEventListener('load', go, { once: true });
      },
      { threshold: 0.55 },
    );
    near.observe(el);
    inView.observe(el);
    return () => {
      near.disconnect();
      inView.disconnect();
      window.clearTimeout(delay);
      cancelAnimationFrame(raf);
    };
  }, [move, flash]);

  const r = c.reveal;
  const whole = Math.round(pos);
  return (
    <figure>
      <div
        ref={frame}
        className={show ? 'lp-cmp lp-show' : 'lp-cmp'}
        style={{ '--pos': pos.toFixed(2) } as CSSProperties}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerEnd}
        onPointerCancel={onPointerEnd}
      >
        <img className="lp-cmp-iris" src={eye.iris.src} srcSet={eye.iris.srcset} sizes={REVEAL_SIZES} width={eye.iris.w} height={eye.iris.h} loading="lazy" decoding="async" alt={eye.irisAlt} />
        <img ref={photo} className="lp-cmp-photo" src={eye.photo.src} srcSet={eye.photo.srcset} sizes={REVEAL_SIZES} width={eye.photo.w} height={eye.photo.h} loading="lazy" decoding="async" alt={eye.photoAlt} />
        <span className="lp-cmp-lab lp-l" style={{ opacity: pos > LABEL_LEFT_HIDDEN ? 1 : 0 }}>{r.before}</span>
        <span className="lp-cmp-lab lp-r" style={{ opacity: pos < LABEL_RIGHT_HIDDEN ? 1 : 0 }}>{r.after}</span>
        <span className="lp-cmp-line" aria-hidden="true" />
        <span className="lp-cmp-grip" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 7l-5 5 5 5M15 7l5 5-5 5" />
          </svg>
        </span>
        <input
          className="lp-cmp-range"
          type="range"
          min={0}
          max={100}
          step={1}
          value={whole}
          aria-label={r.sliderLabel}
          aria-valuetext={t('reveal.valueText', { n: whole })}
          onChange={(e) => {
            const h = hand.current;
            h.swept = true;
            h.gen++;
            move(+e.currentTarget.value);
          }}
          onKeyDown={() => {
            const h = hand.current;
            h.swept = true;
            h.gen++;
          }}
        />
        <span className="lp-cmp-ring" aria-hidden="true" />
      </div>
      <figcaption className="lp-cmp-meta">
        <span>{eye.note}</span>
        <span className="lp-hint">{r.hint}</span>
      </figcaption>
      <p className="lp-cmp-scale">{t('reveal.scale', { n: eye.n })}</p>
    </figure>
  );
}
