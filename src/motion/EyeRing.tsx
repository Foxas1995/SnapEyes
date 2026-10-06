import { useState } from 'react';
import { Arc, Tick } from './Tick';

/** True from the moment `flag` turns on while this component is mounted; false for a flag that was on already when it mounted (a page opened in the
 *  middle of the work shows its finished eyes finished, it does not close their rings again). Derived while rendering, no effect. */
function useBecame(flag: boolean): boolean {
  const [prev, setPrev] = useState(flag);
  const [became, setBecame] = useState(false);
  if (flag !== prev) { setPrev(flag); setBecame(flag); }
  return became;
}

/** One eye of an order (spec 8): its thumbnail with a ring around it. Waiting: a dim still ring. Busy: the rotating gold arc on the ring. Made: the ring
 *  closes in the success colour and its check draws; a ring that was closed when the page opened is simply closed. The numbers behind it are the
 *  server's (`made`, and whether this page is making the eye now), nothing here counts or guesses. */
export const EyeRing = ({ made, busy, thumb }: { made: boolean; busy: boolean; thumb: string | null | undefined }) => {
  const fresh = useBecame(made);
  return (
    <span className={`wk-disc wk-eye${!made && !busy ? ' wk-waits' : ''}`}>
      <span className="crop">{thumb ? <img src={thumb} alt="" /> : null}</span>
      <svg aria-hidden="true" focusable="false" viewBox="0 0 172 172" className={`wk-ring${fresh ? ' fx-fresh' : ''}`}>
        <circle className="track" cx="86" cy="86" r="85" />
        {made ? <circle className="on" cx="86" cy="86" r="85" pathLength="1" /> : null}
      </svg>
      {busy && !made ? <Arc /> : null}
      {made ? <span className={`wk-badge${fresh ? ' wk-fresh' : ''}`}><Tick still={!fresh} /></span> : null}
    </span>
  );
};
