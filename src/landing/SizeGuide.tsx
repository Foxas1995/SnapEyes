// The size guide (#sizes): a drawing to scale of four print sizes on a wall next to a sofa and a person, four size chips, and a
// card with the one number that matters, the pixels per inch of the 4096 px file at that size, with the plain statement of
// what print shops usually ask for. Pick a size with a chip or by clicking the square in the drawing. The drawing is an SVG
// (the pieces are the owner's Radiance artwork); its text labels are HTML laid over it by percent, so they stay crisp.
// On a phone the view box is cropped so the four squares stay large, and only the picked size keeps its label.
//
// Motion (motion spec 6.8, the third of the page's signature moments): when most of the drawing is on screen the sofa and the person
// draw themselves, outline by outline (stroke-dashoffset on pathLength 1: 1.5 s, 100 ms apart), and then the four squares fade in with
// their labels. A pick of a size draws the chosen square's gold outline (.6 s), the others keep a dimmer stroke, and the number of pixels
// per inch and the two lines under it CROSS-FADE (.3 s and .42 s): all four versions are in the page, stacked in one cell (Stack.tsx), so
// no figure is ever tweened through a false in-between value and nothing moves when the text changes. Every number is real text.
import { Fragment, useState, type CSSProperties } from 'react';
import { Title } from '../motion/Title';
import { Stack } from './Stack';
import { useInViewOnce } from './useInView';
import { assetUrl } from './assets';
import { useCopy } from './copy/useCopy';
import { DEFAULT_SIZE, FLOOR, SCENE, SIZES, labelSpots, person, ppi, sofaRects, squares, viewBoxFor, type SizeCm } from './sizeScale';
import { Pill, useKeepFocus, useMediaQuery, useRoving } from './ui';
import './css/sizes.css';

const ART = assetUrl('art/radiance_own_480');

export function SizeGuide() {
  const { c, t } = useCopy();
  const s = c.sizes;
  const narrow = useMediaQuery('(max-width: 639px)');
  const [size, setSize] = useState<SizeCm>(DEFAULT_SIZE);
  const roving = useRoving<HTMLDivElement>((el) => pick(Number(el.dataset.cm) as SizeCm));
  const keepFocus = useKeepFocus(roving.ref);
  function pick(cm: SizeCm) {
    keepFocus(() => setSize(cm), `[data-cm="${cm}"]`);
  }

  const vb = viewBoxFor(narrow);
  const spots = labelSpots(narrow);
  const body = person();
  const picked = SIZES.indexOf(size);
  const rungs = SIZES.map((cm) => s.rungs.find((r) => r.cm === cm) ?? s.rungs[s.rungs.length - 1]);
  const drawn = useInViewOnce<HTMLElement>(0.4);

  return (
    <div className="lp-sizes-blk" id="sizes">
      <div className="lp-sec-head">
        <p className="lp-eyebrow">{s.eyebrow}</p>
        <Title id="sizesH" text={t('sizes.title')} />
        <p className="lp-intro">{t('sizes.intro')}</p>
      </div>
      <div className="lp-size-grid">
        <figure className="lp-ruler" id="ruler" role="img" aria-label={s.svgLabel} data-draw ref={drawn}>
          <svg viewBox={vb.join(' ')} xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">
            <rect x="0" y="0" width={SCENE.w} height={SCENE.h} fill="#0b0e16" />
            <line x1="0" x2={SCENE.w} y1={FLOOR} y2={FLOOR} stroke="rgba(255,255,255,.2)" />
            <g fill="#141925" stroke="rgba(255,255,255,.24)" strokeWidth="1.5">
              {sofaRects().map((r, i) => (
                <rect key={`${r.x}-${r.y}`} className="lp-dr" pathLength={1} style={{ '--k': i } as CSSProperties} x={r.x} y={r.y} width={r.width} height={r.height} rx={r.rx} />
              ))}
            </g>
            <g fill="#1b1f2a" stroke="rgba(255,255,255,.14)" strokeWidth="1.2">
              <path className="lp-dr" pathLength={1} style={{ '--k': 6 } as CSSProperties} d={body.body} />
              <circle className="lp-dr" pathLength={1} style={{ '--k': 7 } as CSSProperties} cx={body.head.cx} cy={body.head.cy} r={body.head.r} />
            </g>
            {squares().map((q, i) => {
              const on = q.cm === size;
              return (
                <g key={q.cm} className="lp-sqg" data-cm={q.cm} style={{ '--k': i } as CSSProperties} onClick={() => pick(q.cm)}>
                  <image href={ART} x={q.x} y={q.y} width={q.side} height={q.side} preserveAspectRatio="xMidYMid slice" opacity={on ? 1 : 0.72} />
                  <rect
                    className="lp-sq"
                    x={q.x}
                    y={q.y}
                    width={q.side}
                    height={q.side}
                    fill={on ? 'rgba(245,197,66,.06)' : 'none'}
                    stroke="rgba(255,255,255,.34)"
                    strokeWidth={1.5}
                  />
                  {/* the chosen square's gold outline: drawn when it is picked, undrawn when another is */}
                  <rect className="lp-sq-on" pathLength={1} data-on={on || undefined} x={q.x} y={q.y} width={q.side} height={q.side} />
                  <rect className="lp-hit" x={q.x - 18} y={q.y - 18} width={q.side + 36} height={q.side + 36} />
                </g>
              );
            })}
          </svg>
          {SIZES.map((cm, i) => (
            <span key={cm} className={`lp-lbl${cm === size ? ' lp-on' : ''}`} style={{ ...spots.squares[cm], '--k': i } as CSSProperties}>{t('sizes.cm', { n: cm })}</span>
          ))}
          <span className="lp-lbl lp-note" style={spots.sofa}>{s.sofa}</span>
          <span className="lp-lbl lp-note" style={spots.person}>{s.person}</span>
        </figure>
        <div className="lp-size-side">
          <div ref={roving.ref} onKeyDown={roving.onKeyDown} className="lp-pills" id="sizeChips" role="radiogroup" aria-label={s.chips}>
            {SIZES.map((cm) => (
              <Pill key={cm} role="radio" on={cm === size} data-cm={cm} onClick={() => pick(cm)}>
                {t('sizes.cm', { n: cm })}
              </Pill>
            ))}
          </div>
          <div className="lp-size-card" id="sizeCard" aria-live="polite">
            <div className="lp-big">
              <Stack className="lp-stack-fig" index={picked} items={SIZES.map((cm) => <b key={cm}>{ppi(cm)}</b>)} />
              <span>{s.ppi}</span>
            </div>
            <Stack
              className="lp-stack-txt"
              index={picked}
              items={rungs.map((r) => (
                <Fragment key={r.cm}>
                  <h3>{r.t}</h3>
                  <p>{r.b}</p>
                </Fragment>
              ))}
            />
          </div>
          <div className="lp-size-notes" id="sizeNotes">
            {(['several', 'above', 'rule'] as const).map((k) => (
              <p key={k}>{t(`sizes.${k}`)}</p>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
