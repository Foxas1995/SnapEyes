import { useCopy } from './copy/useCopy';
import { GROUPS, type GalleryGroup } from './gallery';
import { useRoving } from './ui';

/** The group tabs of the style gallery ("Just you", "Two of you", "Family"): a tablist with roving tabindex. The selected tab
 *  is the one tab stop; the arrow keys, Home and End move to a tab and pick it (selection follows focus, as in the
 *  prototype). The tabs keep their keys, so a pick never remounts a button and the focus stays where it was. */
export function StyleTabs({ group, onPick }: { group: GalleryGroup; onPick: (group: GalleryGroup) => void }) {
  const { c } = useCopy();
  const { ref, onKeyDown } = useRoving<HTMLDivElement>((el) => onPick(el.dataset.g as GalleryGroup));
  return (
    <div className="lp-tabs" id="gTabs" role="tablist" aria-label={c.styles.tabsLabel} ref={ref} onKeyDown={onKeyDown}>
      {GROUPS.map((g) => (
        <button
          key={g}
          type="button"
          className="lp-tab"
          role="tab"
          id={`gtab-${g}`}
          aria-selected={g === group}
          aria-controls="gPanel"
          tabIndex={g === group ? 0 : -1}
          data-g={g}
          onClick={() => onPick(g)}
        >
          {c.styles.groups[g]}
        </button>
      ))}
    </div>
  );
}
