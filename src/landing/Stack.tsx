import type { ReactNode } from 'react';

/** Several versions of one thing in the same grid cell, one of them showing. A change of `index` cross-fades them (opacity only, the
 *  CSS of src/landing/css/sizes.css, .lp-stack): the old one fades out while the new one fades in, and because every version is
 *  always there the cell has the height and the width of the largest, so nothing around it ever moves and no number is tweened through
 *  a false in-between value. The versions that are not showing are out of the accessibility tree and cannot take the focus (aria-hidden
 *  and inert), so a screen reader meets exactly one of them. */
export function Stack({ index, items, className = '' }: { index: number; items: readonly ReactNode[]; className?: string }) {
  return (
    <div className={`lp-stack ${className}`.trim()}>
      {items.map((node, i) => {
        const on = i === index;
        return (
          <div key={i} className="lp-stack-i" data-on={on || undefined} aria-hidden={on ? undefined : true} inert={!on}>
            {node}
          </div>
        );
      })}
    </div>
  );
}
