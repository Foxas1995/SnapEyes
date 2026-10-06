import { assetUrl } from './assets';
import { useCopy } from './copy/useCopy';
import { EYES, type EyeId } from './gallery';
import { useRoving } from './ui';

/** "Try another eye colour": one round dot per eye colour (Mantas's own, yellow green, brown, grey), a radiogroup with roving
 *  tabindex, then the line that says whose eye it is ("Mantas's own eye" or "Example photo, not a customer"). The two
 *  elements are siblings on purpose: on a phone the gallery's panel orders them around the tiles (css/styles.css). The dot
 *  shows its name only while it is the selected one on a phone; the other names are there for a screen reader. */
export function EyeChips({ eye, onPick, hidden }: { eye: EyeId; onPick: (eye: EyeId) => void; hidden: boolean }) {
  const { c } = useCopy();
  const { ref, onKeyDown } = useRoving<HTMLDivElement>((el) => onPick(el.dataset.e as EyeId));
  return (
    <>
      <div className="lp-eyepick" id="gEye" hidden={hidden}>
        <span className="lp-lab" id="gEyeLab">{c.styles.eyeLabel}</span>
        <div className="lp-eyechips" id="gEyeChips" role="radiogroup" aria-labelledby="gEyeLab" ref={ref} onKeyDown={onKeyDown}>
          {EYES.map((e) => (
            <button
              key={e.id}
              type="button"
              className="lp-eyechip"
              role="radio"
              aria-checked={e.id === eye}
              tabIndex={e.id === eye ? 0 : -1}
              data-e={e.id}
              onClick={() => onPick(e.id)}
            >
              <span className="lp-eyedot" style={{ background: `#000 url(${assetUrl(e.thumb)}) 50% 50%/cover no-repeat` }} />
              <span className="lp-en">{c.styles.eyes[e.id]}</span>
            </button>
          ))}
        </div>
      </div>
      <p className="lp-eyenote" id="gEyeNote" hidden={hidden}>{eye === 'own' ? c.styles.eyeNote.own : c.styles.eyeNote.other}</p>
    </>
  );
}
