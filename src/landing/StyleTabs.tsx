import { useCallback, useEffect, useLayoutEffect, useRef } from 'react';
import { useCopy } from './copy/useCopy';
import { GROUPS, type GalleryGroup } from './gallery';
import { useRoving } from './ui';

/** The group tabs of the style gallery ("Just you", "Two of you", "Family"): a tablist with roving tabindex. The selected tab
 *  is the one tab stop; the arrow keys, Home and End move to a tab and pick it (selection follows focus, as in the
 *  prototype). The tabs keep their keys, so a pick never remounts a button and the focus stays where it was.
 *
 *  The underline is one gold line of 1 px that slides to the selected tab (motion spec 6.6): it is placed by `translate` and `scale`
 *  from the tab's measured box, in the tab list's own coordinates, so it scrolls with the tabs when the list is swiped on a phone. It is
 *  measured again whenever the box could have changed (another language, the web font arriving, the window resized) and then it snaps
 *  instead of sliding. While it has not been measured (a list that is not displayed) the CSS keeps the plain underline of the selected
 *  tab, so the selection is always marked. */
export function StyleTabs({ group, onPick }: { group: GalleryGroup; onPick: (group: GalleryGroup) => void }) {
  const { c, lang } = useCopy();
  const { ref, onKeyDown } = useRoving<HTMLDivElement>((el) => onPick(el.dataset.g as GalleryGroup));
  const bar = useRef<HTMLSpanElement>(null);
  const placed = useRef<GalleryGroup | null>(null);

  const place = useCallback(
    (slide: boolean) => {
      const list = ref.current;
      const line = bar.current;
      const tab = list?.querySelector<HTMLElement>('[aria-selected="true"]');
      if (!list || !line || !tab || !tab.offsetWidth) return;
      // the line is inset like the underline it replaces: 14 px from each side of the tab
      const x = tab.offsetLeft + 14;
      const w = Math.max(0, tab.offsetWidth - 28);
      line.style.transition = slide ? '' : 'none';
      line.style.translate = `${x}px 0`;
      line.style.scale = `${w} 1`;
      list.dataset.bar = '';
    },
    [ref],
  );

  // the selected tab changed: slide; the language changed: snap. The very first placement is the ResizeObserver's below (it reports once as soon
  // as it starts observing, after the browser has laid the list out): no read of a box during the commit, which would force the layout of the
  // whole page inside React's own task.
  useLayoutEffect(() => {
    if (placed.current !== null && placed.current !== group) place(true);
    placed.current = group;
  }, [group, place]);
  const first = useRef(true);
  useLayoutEffect(() => {
    if (first.current) first.current = false;
    else place(false);
  }, [lang, place]);

  // the box changed under us (the list resized, the web font arrived): snap
  useEffect(() => {
    const list = ref.current;
    if (!list) return;
    const ro = new ResizeObserver(() => place(false));
    ro.observe(list);
    void document.fonts?.ready.then(() => place(false));
    return () => ro.disconnect();
  }, [ref, place]);

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
      <span className="lp-tabs-bar" ref={bar} aria-hidden="true" />
    </div>
  );
}
