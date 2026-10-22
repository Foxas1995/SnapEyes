import { useEffect, useRef, useState, type CSSProperties } from 'react';

// The guide to photographing an eye (2026-10-22, the owner: "our explanation is not good ... the clearer the better"): our own animated video, no voice,
// its words burnt in, one square file per language (public/assets/howto), on the capture screen of /try and in the landing's first step of "How it works".
// It costs nothing until it is on screen. The poster (the video's own first frame, so nothing jumps when it starts) is a plain lazy picture in the flow,
// and it holds the box: the video arrives without moving anything, and until it has a frame it is transparent (a video with no poster of its own and no
// data yet shows nothing, HTML's rule), so the picture under it is what shows; nothing is hidden by a style. The video gets its file when it starts to come
// on screen and plays by itself, muted, inline and in a loop, only while at least half of it is on screen and the tab is visible; it stops when it leaves.
// Under prefers-reduced-motion, with a data saver, without IntersectionObserver, or in a browser that refuses to play by itself it never starts by itself:
// the poster stays with a play button, and a press plays it (once, under reduced motion or a data saver). While it plays, a pause button is always there
// (WCAG 2.2.2). The video is decorative (aria-hidden): the steps beside it say the same in words. Styles are inline: the landing and the tools share no
// stylesheet, and their CSS budgets are spent.
const BTN: CSSProperties = { position: 'absolute', display: 'grid', placeItems: 'center', borderRadius: '50%', padding: 0, cursor: 'pointer' };
const PLAY: CSSProperties = { ...BTN, left: '50%', top: '50%', width: 64, height: 64, margin: -32, background: 'rgb(7 9 14/.74)', border: '1px solid rgb(var(--gold-rgb) / .6)', color: 'var(--gold-primary)' };
const PAUSE: CSSProperties = { ...BTN, right: 4, bottom: 4, width: 44, height: 44, background: 'rgb(7 9 14/.5)', border: 0, color: '#f0f3fa' };

/** True when the video must wait for a press: reduced motion, a data saver, no IntersectionObserver (and on the server). */
export function guideStill(): boolean {
  if (typeof window === 'undefined' || !('IntersectionObserver' in window)) return true;
  return matchMedia('(prefers-reduced-motion: reduce)').matches || !!(navigator as Navigator & { connection?: { saveData?: boolean } }).connection?.saveData;
}

export function GuideVideo({ src, poster, w, h, play, pause, className, style }: {
  src: string; poster: string; w: number; h: number; play: string; pause: string; className?: string; style?: CSSProperties;
}) {
  const box = useRef<HTMLDivElement>(null);
  const vid = useRef<HTMLVideoElement>(null);
  // held: it waits for a press (reduced motion, a data saver, the visitor paused it, or the browser refused to play by itself)
  const [held, setHeld] = useState(guideStill);
  const heldRef = useRef(held);
  heldRef.current = held;
  const run = useRef(() => {});
  useEffect(() => {
    const v = vid.current, b = box.current;
    if (!v || !b) return;
    v.muted = true;
    v.loop = !guideStill();
    let seen = !('IntersectionObserver' in window);
    run.current = () => {
      if (!heldRef.current && seen && !document.hidden) {
        if (v.getAttribute('src') !== src) v.src = src;
        // a browser that refuses to play by itself (iOS in low power mode) gets the play button instead of a pause button on a still poster
        v.play().catch((e: Error) => { if (e.name === 'NotAllowedError') setHeld(true); });
      } else v.pause();
    };
    const end = () => setHeld(true);
    v.addEventListener('ended', end);
    // the file is asked for as the video comes on screen (when it may play by itself); it plays while half of it is on screen
    const io = seen ? null : new IntersectionObserver(([e]) => {
      if (e.isIntersecting && !heldRef.current && v.getAttribute('src') !== src) { v.preload = 'auto'; v.src = src; }
      seen = e.intersectionRatio > 0.45;
      run.current();
    }, { threshold: [0, 0.5] });
    io?.observe(b);
    const vis = () => run.current();
    document.addEventListener('visibilitychange', vis);
    return () => {
      io?.disconnect();
      document.removeEventListener('visibilitychange', vis);
      v.removeEventListener('ended', end);
      v.pause();
    };
  }, [src]);
  useEffect(() => run.current(), [held]);
  return (
    <div ref={box} className={className} style={{ position: 'relative', ...style }} data-guide={held ? 'held' : 'auto'}>
      <img src={poster} width={w} height={h} alt="" loading="lazy" decoding="async" style={{ display: 'block', width: '100%', height: 'auto' }} />
      <video key={src} ref={vid} muted playsInline preload="none" aria-hidden="true" tabIndex={-1}
        style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }} />
      <button type="button" onClick={() => setHeld((x) => !x)} aria-label={held ? play : pause} style={held ? PLAY : PAUSE}>
        <svg viewBox="0 0 24 24" width={held ? 26 : 18} height={held ? 26 : 18} fill="currentColor" aria-hidden="true">
          <path d={held ? 'M8 5.5v13l10.5-6.5z' : 'M7 5h3.5v14H7zm6.5 0H17v14h-3.5z'} />
        </svg>
      </button>
    </div>
  );
}
