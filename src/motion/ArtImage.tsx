import { useCallback, useEffect, useRef, useState, type ImgHTMLAttributes } from 'react';
import { stillMotion, whenDecoded } from './flow';

// The picture of an artwork frame that arrives (motion spec 7.5 and 8). Three things can happen to it, and each is the picture's own, drawn by the server:
//   the first one of a real arrival (`arrive`): it opens like a diaphragm, 1.3 s, a clip and nothing else (the CSS class fx-open, no fill), started when
//     the picture has decoded and never before: the picture is not in the page until then, so there is no flash of the whole picture before the
//     clip, and a delay of 3.5 s at most (src/motion/flow.ts whenDecoded) puts it in anyway without the opening, so a decode that never comes never
//     holds a picture back;
//   a later one (another style, layout, eye): the new picture decodes first, then fades in over the old one, opacity only, no scale (AC-4); the old one
//     is gone when it ends;
//   one that was there at the start (a restored session, a picture shown before): it is simply there, in the first render.
// Under reduced motion all three are the same: the picture is there. The picture is always the one it is given: this component never draws, filters or
// layers anything of its own over it (AC-2), and the watermark and the labels are in the picture or beside it, not part of the motion (AC-7, AC-8).

type Layer = { id: number; src: string; mode: 'plain' | 'open' | 'fade' };
let seq = 0;

type Props = Omit<ImgHTMLAttributes<HTMLImageElement>, 'src' | 'alt'> & {
  src: string;
  alt: string;
  /** this display is the first of a real arrival: open it (ignored while there is a picture already) */
  arrive?: boolean;
  /** the opening has ended (or could not run): the arrival is spent */
  onOpened?: () => void;
};

export const ArtImage = ({ src, alt, arrive = false, onOpened, className = '', ...rest }: Props) => {
  const [layers, setLayers] = useState<Layer[]>(() => (arrive ? [] : [{ id: seq++, src, mode: 'plain' }]));
  const last = layers.length ? layers[layers.length - 1] : null;
  const top = last ? last.src : null;
  const opened = useRef(onOpened);
  useEffect(() => { opened.current = onOpened; });

  // a picture that is not on screen yet: decode it, then put it in
  useEffect(() => {
    if (src === top) return;
    let alive = true;
    const mode = stillMotion() ? 'plain' : top === null ? (arrive ? 'open' : 'plain') : 'fade';
    void whenDecoded(src).then((r) => {
      if (alive) setLayers((ls) => [...ls.slice(-1), { id: seq++, src, mode: r === 'decoded' ? mode : 'plain' }]);
    });
    return () => { alive = false; };
  }, [src, top, arrive]);

  // the picture that has just come in is the one on top: when its motion is over (or after a failsafe, if the event never comes) it is plain and the one
  // below is not drawn any more
  const settle = useCallback((id: number, wasOpen: boolean) => {
    setLayers((ls) => (ls.length && ls[ls.length - 1].id === id ? [{ ...ls[ls.length - 1], mode: 'plain' }] : ls));
    if (wasOpen) opened.current?.();
  }, []);
  const id = last ? last.id : -1;
  const mode = last ? last.mode : 'plain';
  useEffect(() => {
    if (id < 0 || mode === 'plain') return;
    const t = setTimeout(() => settle(id, mode === 'open'), mode === 'open' ? 2200 : 1000);
    return () => clearTimeout(t);
  }, [id, mode, settle]);

  // a plain picture on top is the whole picture: whatever is below it is not drawn
  const drawn = last && last.mode === 'plain' ? [last] : layers;
  return (
    <>
      {drawn.map((l, i) => (
        <img key={l.id} {...rest} src={l.src} alt={i === drawn.length - 1 ? alt : ''} aria-hidden={i < drawn.length - 1 ? true : undefined}
          className={`${className} ${l.mode === 'open' ? 'fx-open' : l.mode === 'fade' ? 'fx-xfade' : ''}`.trim()}
          onAnimationEnd={(e) => { if (e.target === e.currentTarget && l.id === id && l.mode !== 'plain') settle(l.id, l.mode === 'open'); }} />
      ))}
    </>
  );
};
