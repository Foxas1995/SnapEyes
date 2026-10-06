// The four wall materials side by side, in a closed disclosure under the material list. The table scrolls sideways on a phone,
// so its wrapper is a named region with a tab stop (the keyboard can scroll it); the corner header cell is there for screen
// readers only. The note under it says what the table is: a general guide to what print shops offer, not our products.
import { Disclosure } from './ui';
import { useCopy } from './copy/useCopy';

export function CompareTable() {
  const { c } = useCopy();
  const cmp = c.wall.compare;
  return (
    <Disclosure className="lp-compare" summary={<span>{c.wall.compareTitle}</span>}>
      <div className="lp-tbl-wrap" id="tblWrap" tabIndex={0} role="group" aria-label={c.wall.compareTitle}>
        <table className="lp-tbl" id="cmpTbl">
          <thead>
            <tr>
              <th scope="col"><span className="lp-sr">{c.wall.compareCorner}</span></th>
              {cmp.cols.map((col) => (
                <th key={col} scope="col">{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {cmp.rows.map((row) => (
              <tr key={row.h}>
                <th scope="row">{row.h}</th>
                {row.v.map((cell, i) => (
                  <td key={i}>{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="lp-tbl-note" id="cmpNoteTbl">{cmp.note}</p>
    </Disclosure>
  );
}
