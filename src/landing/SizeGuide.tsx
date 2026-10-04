// The size guide (#sizes): a drawing to scale of four print sizes on a wall next to a sofa and a person, four size chips, and a
// card with the one number that matters, the pixels per inch of the 4096 px file at that size, with the plain statement of
// what print shops usually ask for. Pick a size with a chip or by clicking the square in the drawing. The drawing is an SVG
// (the pieces are the owner's Radiance artwork); its text labels are HTML laid over it by percent, so they stay crisp.
// On a phone the view box is cropped so the four squares stay large, and only the picked size keeps its label.
import { useState } from 'react';
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
  const rung = s.rungs.find((r) => r.cm === size) ?? s.rungs[s.rungs.length - 1];

  return (
    <div className="lp-sizes-blk" id="sizes">
      <div className="lp-sec-head">
        <p className="lp-eyebrow">{s.eyebrow}</p>
        <h2>{t('sizes.title')}</h2>
        <p className="lp-intro">{t('sizes.intro')}</p>
      </div>
      <div className="lp-size-grid">
        <figure className="lp-ruler" id="ruler" role="img" aria-label={s.svgLabel}>
          <svg viewBox={vb.join(' ')} xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">
            <rect x="0" y="0" width={SCENE.w} height={SCENE.h} fill="#0b0e16" />
            <line x1="0" x2={SCENE.w} y1={FLOOR} y2={FLOOR} stroke="rgba(255,255,255,.2)" />
            <g fill="#141925" stroke="rgba(255,255,255,.24)" strokeWidth="1.5">
              {sofaRects().map((r) => (
                <rect key={`${r.x}-${r.y}`} x={r.x} y={r.y} width={r.width} height={r.height} rx={r.rx} />
              ))}
            </g>
            <g fill="#1b1f2a" stroke="rgba(255,255,255,.14)" strokeWidth="1.2">
              <path d={body.body} />
              <circle cx={body.head.cx} cy={body.head.cy} r={body.head.r} />
            </g>
            {squares().map((q) => {
              const on = q.cm === size;
              return (
                <g key={q.cm} className="lp-sqg" data-cm={q.cm} onClick={() => pick(q.cm)}>
                  <image href={ART} x={q.x} y={q.y} width={q.side} height={q.side} preserveAspectRatio="xMidYMid slice" opacity={on ? 1 : 0.72} />
                  <rect
                    className="lp-sq"
                    x={q.x}
                    y={q.y}
                    width={q.side}
                    height={q.side}
                    fill={on ? 'rgba(245,197,66,.06)' : 'none'}
                    stroke={on ? '#f5c542' : 'rgba(255,255,255,.5)'}
                    strokeWidth={on ? 3 : 1.5}
                  />
                  <rect className="lp-hit" x={q.x - 18} y={q.y - 18} width={q.side + 36} height={q.side + 36} />
                </g>
              );
            })}
          </svg>
          {SIZES.map((cm) => (
            <span key={cm} className={`lp-lbl${cm === size ? ' lp-on' : ''}`} style={spots.squares[cm]}>{t('sizes.cm', { n: cm })}</span>
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
              <b>{ppi(size)}</b>
              <span>{s.ppi}</span>
            </div>
            <h3>{rung.t}</h3>
            <p>{rung.b}</p>
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
